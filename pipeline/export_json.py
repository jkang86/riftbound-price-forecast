"""
export_json.py — Bridge pipeline CSV exports to React frontend JSON.

Reads data/exports/*.csv  →  writes public/data/*.json

Run after run_phase4.py:
  python -m pipeline.export_json
"""
from __future__ import annotations

import json
import logging
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

BASE_DIR = Path(__file__).parent.parent
EXPORTS_DIR = BASE_DIR / "data" / "exports"
PUBLIC_DATA_DIR = BASE_DIR / "public" / "data"

FORECAST_TOP_N = 30      # cards to run Prophet on
SPARKLINE_WEEKS = 10     # weeks of price history in sparkline

# ── Signal thresholds ──────────────────────────────────────────────────────

def _signal(pct: float) -> str:
    if pct >= 0.20:  return "STRONG BUY"
    if pct >= 0.05:  return "BUY"
    if pct > -0.05:  return "HOLD"
    if pct > -0.20:  return "WATCH"
    return "SELL"


# ── Helpers ────────────────────────────────────────────────────────────────

def _safe(v):
    """Convert numpy/pandas scalars to plain Python types."""
    if pd.isna(v):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return round(float(v), 4)
    return v


def _round2(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), 2)


# ── cards.json ─────────────────────────────────────────────────────────────

def build_cards_json(df: pd.DataFrame) -> dict:
    """Build full card catalog from features.csv."""
    # Sort by week so groupby().last() gets the most recent row per card
    df = df.sort_values("week")

    # Sparkline: last SPARKLINE_WEEKS prices per card (oldest → newest)
    sparklines: dict[int, list[float]] = {}
    for pid, grp in df.groupby("product_id"):
        prices = grp.tail(SPARKLINE_WEEKS)["market_price"].tolist()
        sparklines[pid] = [_round2(p) for p in prices]

    latest = df.groupby("product_id").last().reset_index()

    cards = []
    for _, row in latest.iterrows():
        pid = int(row["product_id"])
        pct = float(row["price_pct_change_1w"]) if not pd.isna(row["price_pct_change_1w"]) else 0.0
        domain = str(row["domain"]) if not pd.isna(row["domain"]) else "Unknown"
        rarity = str(row["rarity"]) if not pd.isna(row["rarity"]) else "Common"
        card_type = str(row["card_type"]) if not pd.isna(row["card_type"]) else ""

        tags = [rarity.upper()]
        if card_type:
            tags.append(card_type.upper())

        cards.append({
            "id":            str(pid),
            "name":          str(row["card_display"]),
            "faction":       domain,
            "rarity":        rarity,
            "current_price": _round2(row["market_price"]),
            "price_7d_ago":  _round2(row["price_lag_1w"]),
            "delta_7d_pct":  round(pct * 100, 2),
            "signal":        _signal(pct),
            "sparkline":     sparklines.get(pid, [_round2(row["market_price"])]),
            "tags":          tags,
        })

    # Sort descending by price for default explorer order
    cards.sort(key=lambda c: c["current_price"] or 0, reverse=True)

    return {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "cards":      cards,
    }


# ── market.json ────────────────────────────────────────────────────────────

def build_market_json(df: pd.DataFrame) -> dict:
    """Market-level aggregates: history, volatility heatmap, gainer/loser counts."""
    # Weekly market history (average price + card count that week)
    weekly = (
        df.groupby("week")
        .agg(
            avg_price=("market_price", "mean"),
            card_count=("product_id", "nunique"),
            total_market_cap=("market_price", "sum"),
        )
        .reset_index()
        .sort_values("week")
    )
    history = [
        {
            "week":             row["week"],
            "avg_price":        _round2(row["avg_price"]),
            "card_count":       int(row["card_count"]),
            "total_market_cap": _round2(row["total_market_cap"]),
        }
        for _, row in weekly.iterrows()
    ]

    # Domain × rarity volatility (coefficient of variation per group)
    latest = df.sort_values("week").groupby("product_id").last().reset_index()
    latest_week = df["week"].max()
    prev_week = df[df["week"] < latest_week]["week"].max()

    domain_rarity_vol = []
    if prev_week:
        prev = df[df["week"] == prev_week][["product_id", "market_price"]].rename(columns={"market_price": "price_prev"})
        merged = latest.merge(prev, on="product_id", how="left")
        merged["vol_pct"] = ((merged["market_price"] - merged["price_prev"]) / merged["price_prev"].replace(0, np.nan)).abs() * 100
        for (domain, rarity), grp in merged.dropna(subset=["vol_pct"]).groupby(["domain", "rarity"]):
            domain_rarity_vol.append({
                "faction":    str(domain),
                "rarity":     str(rarity),
                "volatility": _round2(grp["vol_pct"].mean()),
                "count":      int(len(grp)),
            })

    # Gainer / loser counts from latest week
    latest_movers = df[df["week"] == df["week"].max()].copy()
    gainers = int((latest_movers["price_pct_change_1w"] > 0.02).sum())
    losers  = int((latest_movers["price_pct_change_1w"] < -0.02).sum())

    return {
        "updated_at":                datetime.utcnow().isoformat() + "Z",
        "market_history":            history,
        "faction_rarity_volatility": domain_rarity_vol,
        "gainers_count":             gainers,
        "losers_count":              losers,
    }


# ── forecasts.json ─────────────────────────────────────────────────────────

def _fit_prophet_forecast(grp: pd.DataFrame, weeks_ahead: int = 4) -> dict | None:
    """Fit Prophet on a single card's price history, return forecast dict."""
    try:
        from prophet import Prophet  # noqa: PLC0415
    except ImportError:
        return None

    ts = grp[["week", "market_price"]].rename(columns={"week": "ds", "market_price": "y"})
    ts["ds"] = pd.to_datetime(ts["ds"])
    ts = ts.dropna(subset=["y"]).sort_values("ds")

    if len(ts) < 4:  # need at least 4 data points
        return None

    try:
        m = Prophet(
            weekly_seasonality=False,
            daily_seasonality=False,
            yearly_seasonality=False,
            changepoint_prior_scale=0.3,
            interval_width=0.8,
        )
        m.fit(ts)

        last_date = ts["ds"].max()
        future_dates = pd.DataFrame({
            "ds": [last_date + timedelta(weeks=i) for i in range(1, weeks_ahead + 1)]
        })
        forecast = m.predict(future_dates)

        # Compute simple metrics on in-sample last 3 weeks
        test = ts.tail(3).copy()
        test_future = m.predict(test[["ds"]])
        y_true = test["y"].values
        y_pred = test_future["yhat"].values
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        mae  = float(np.mean(np.abs(y_true - y_pred)))
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 1.0

        history = [
            {"date": row["ds"].strftime("%Y-%m-%d"), "price": _round2(row["y"])}
            for _, row in ts.iterrows()
        ]
        future = [
            {
                "date":       row["ds"].strftime("%Y-%m-%d"),
                "yhat":       _round2(max(0, row["yhat"])),
                "yhat_lower": _round2(max(0, row["yhat_lower"])),
                "yhat_upper": _round2(max(0, row["yhat_upper"])),
            }
            for _, row in forecast.iterrows()
        ]

        return {"history": history, "forecast": future, "rmse": rmse, "mae": mae, "r2": r2}

    except Exception as exc:
        logging.warning("Prophet failed for card: %s", exc)
        return None


def build_forecasts_json(df: pd.DataFrame, top_n: int = FORECAST_TOP_N) -> dict:
    """Run Prophet on top_n cards by latest price, return forecasts dict."""
    latest = df.sort_values("week").groupby("product_id").last().reset_index()
    top_ids = (
        latest.sort_values("market_price", ascending=False)
        .head(top_n)["product_id"]
        .tolist()
    )

    forecasts = []
    total = len(top_ids)
    for i, pid in enumerate(top_ids, 1):
        card_row = latest[latest["product_id"] == pid].iloc[0]
        grp = df[df["product_id"] == pid].sort_values("week")
        print(f"  Prophet [{i}/{total}] {card_row['card_display'][:40]}")

        result = _fit_prophet_forecast(grp)
        if result is None:
            continue

        forecasts.append({
            "card_id":  str(pid),
            "history":  result["history"],
            "forecast": result["forecast"],
            "metrics":  {
                "rmse": round(result["rmse"], 4),
                "mae":  round(result["mae"],  4),
                "r2":   round(result["r2"],   6),
            },
            "model": "prophet",
        })

    return {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "forecasts":  forecasts,
    }


# ── Entry point ────────────────────────────────────────────────────────────

def run() -> None:
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading features.csv ...")
    df = pd.read_csv(EXPORTS_DIR / "features.csv")
    df["week"] = df["week"].astype(str)

    # ── cards.json
    print("Building cards.json …")
    cards_data = build_cards_json(df)
    out = PUBLIC_DATA_DIR / "cards.json"
    out.write_text(json.dumps(cards_data, ensure_ascii=False), encoding="utf-8")
    print(f"  OK: {len(cards_data['cards'])} cards -> {out}")

    # ── market.json
    print("Building market.json ...")
    market_data = build_market_json(df)
    out = PUBLIC_DATA_DIR / "market.json"
    out.write_text(json.dumps(market_data, ensure_ascii=False), encoding="utf-8")
    print(f"  OK: {len(market_data['market_history'])} weeks of history -> {out}")

    # ── forecasts.json
    print(f"Building forecasts.json (top {FORECAST_TOP_N} cards via Prophet) ...")
    forecasts_data = build_forecasts_json(df)
    out = PUBLIC_DATA_DIR / "forecasts.json"
    out.write_text(json.dumps(forecasts_data, ensure_ascii=False), encoding="utf-8")
    print(f"  OK: {len(forecasts_data['forecasts'])} forecasts -> {out}")

    print("\nDone. public/data/ updated.")


if __name__ == "__main__":
    run()
