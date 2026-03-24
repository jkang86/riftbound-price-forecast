"""
Phase 3 — Feature Engineering.

Reads:  data/processed/master.csv
Writes: data/processed/features.csv

Feature set
-----------
Categorical (encoded):
  rarity_tier          ordinal 1-5 (see config.RARITY_TIER)
  type_*               one-hot for each card type (8 dummies)
  domain_primary_*     one-hot for primary domain (pipe-split, 7 dummies)

Temporal:
  set_release_flag     1 if week falls within ±2 weeks of any SET_RELEASE_DATES
  days_since_first_sale  days from card's first observed price to current week

Autoregressive price:
  price_lag_1w         market_price 1 week prior (per card)
  price_lag_2w         market_price 2 weeks prior (per card)
  price_rolling_mean_4w  4-week rolling mean (min_periods=2)
  price_pct_change_1w  (market_price - price_lag_1w) / price_lag_1w

Tournament:
  tournament_play_rate   renamed from legend_play_rate
  tournament_top8_rate   renamed from legend_top8_rate

Target:
  price_next_week      market_price shifted forward 1 week per card

Rows dropped:
  - First 2 rows per product_id (price_lag_2w unavailable)
  - Last 1 row per product_id (price_next_week unavailable)

Note: all time-series operations (lag, rolling, target) are grouped by product_id,
not card_name. Multiple rarities of the same card (e.g. Ahri Rare vs Ahri Showcase)
are separate product_ids and are modelled independently.
card_display = card_name + " (" + rarity + ")" for multi-rarity cards.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import PROCESSED_DIR, SET_RELEASE_DATES, RARITY_TIER, TARGET_COL

_RELEASE_DTS = [datetime.strptime(d, "%Y-%m-%d") for d in SET_RELEASE_DATES]
_RELEASE_WINDOW_WEEKS = 2  # ±2 weeks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _release_flag(week_str: str) -> int:
    week_dt = datetime.strptime(week_str, "%Y-%m-%d")
    for rd in _RELEASE_DTS:
        if abs((week_dt - rd).days) <= _RELEASE_WINDOW_WEEKS * 7:
            return 1
    return 0


def _safe_type_col(name: str) -> str:
    """'Champion Unit' -> 'type_champion_unit'"""
    return "type_" + name.lower().replace(" ", "_")


def _safe_domain_col(name: str) -> str:
    return "domain_primary_" + name.lower().replace("|", "_")


# ---------------------------------------------------------------------------
# Feature builders
# ---------------------------------------------------------------------------

def _add_rarity_tier(df: pd.DataFrame) -> pd.DataFrame:
    df["rarity_tier"] = df["rarity"].map(RARITY_TIER)
    unmapped = df["rarity_tier"].isna().sum()
    if unmapped:
        raise ValueError(
            f"[engineer] {unmapped} rows have unmapped rarity: "
            f"{df.loc[df['rarity_tier'].isna(), 'rarity'].unique()}"
        )
    return df


def _add_type_dummies(df: pd.DataFrame) -> pd.DataFrame:
    dummies = pd.get_dummies(df["type"], prefix="type", dtype=int)
    dummies.columns = [c.lower().replace(" ", "_") for c in dummies.columns]
    return pd.concat([df, dummies], axis=1)


def _add_domain_dummies(df: pd.DataFrame) -> pd.DataFrame:
    df["domain_primary"] = df["domain"].str.split("|").str[0]
    dummies = pd.get_dummies(df["domain_primary"], prefix="domain_primary", dtype=int)
    dummies.columns = [c.lower() for c in dummies.columns]
    return pd.concat([df, dummies], axis=1)


def _add_release_flag(df: pd.DataFrame) -> pd.DataFrame:
    df["set_release_flag"] = df["week"].apply(_release_flag)
    return df


def _add_card_display(df: pd.DataFrame) -> pd.DataFrame:
    """Create a display label that disambiguates multi-rarity cards."""
    counts = df.groupby("card_name")["product_id"].nunique()
    multi = set(counts[counts > 1].index)
    df["card_display"] = df.apply(
        lambda r: f"{r['card_name']} ({r['rarity']})" if r["card_name"] in multi else r["card_name"],
        axis=1,
    )
    return df


def _add_days_since_first_sale(df: pd.DataFrame) -> pd.DataFrame:
    first_sale = (
        df.groupby("product_id")["week"]
        .min()
        .rename("first_sale_week")
    )
    df = df.join(first_sale, on="product_id")
    df["days_since_first_sale"] = (
        pd.to_datetime(df["week"]) - pd.to_datetime(df["first_sale_week"])
    ).dt.days
    df = df.drop(columns=["first_sale_week"])
    return df


def _add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["product_id", "week"]).reset_index(drop=True)

    grp = df.groupby("product_id")["market_price"]

    df["price_lag_1w"] = grp.shift(1)
    df["price_lag_2w"] = grp.shift(2)
    df["price_rolling_mean_4w"] = (
        grp.transform(lambda s: s.rolling(4, min_periods=2).mean())
    )
    df["price_pct_change_1w"] = (
        (df["market_price"] - df["price_lag_1w"])
        / df["price_lag_1w"].replace(0, np.nan)
    ).round(4)

    return df


def _add_target(df: pd.DataFrame) -> pd.DataFrame:
    df[TARGET_COL] = df.groupby("product_id")["market_price"].shift(-1)
    return df


def _rename_tournament_cols(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "legend_play_rate": "tournament_play_rate",
        "legend_top8_rate": "tournament_top8_rate",
    })


# ---------------------------------------------------------------------------
# Leakage check
# ---------------------------------------------------------------------------

def _check_leakage(df: pd.DataFrame) -> None:
    id_cols = {"card_name", "card_display", "product_id", "week", TARGET_COL}
    forbidden = {"low_price", "high_price", "qty_sold", "transaction_count"}
    feature_cols = set(df.columns) - id_cols
    leakers = forbidden & feature_cols
    if leakers:
        raise AssertionError(f"[engineer] Leakage detected — drop these columns: {leakers}")
    if TARGET_COL not in df.columns:
        raise AssertionError(f"[engineer] Target column '{TARGET_COL}' is missing.")
    print(f"[engineer] Leakage check passed.")


# ---------------------------------------------------------------------------
# Column selection for final CSV
# ---------------------------------------------------------------------------

def _select_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    id_cols    = ["product_id", "card_name", "card_display", "week"]
    price_cols = ["market_price"]  # current-week price — kept for dashboard / ARIMA baseline
    feature_cols = [
        "rarity_tier",
        "days_since_first_sale",
        "set_release_flag",
        "tournament_play_rate",
        "tournament_top8_rate",
        "price_lag_1w",
        "price_lag_2w",
        "price_rolling_mean_4w",
        "price_pct_change_1w",
    ]
    type_cols   = sorted([c for c in df.columns if c.startswith("type_")])
    domain_cols = sorted([c for c in df.columns if c.startswith("domain_primary_")])
    target_col  = [TARGET_COL]

    ordered = id_cols + price_cols + feature_cols + type_cols + domain_cols + target_col
    return df[ordered]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_features() -> pd.DataFrame:
    master = pd.read_csv(PROCESSED_DIR / "master.csv")
    print(f"[engineer] Loaded master.csv — {master.shape[0]} rows, {master['card_name'].nunique()} cards")

    df = master.copy()
    df = _rename_tournament_cols(df)
    df = _add_card_display(df)
    df = _add_rarity_tier(df)
    df = _add_type_dummies(df)
    df = _add_domain_dummies(df)
    df = _add_release_flag(df)
    df = _add_days_since_first_sale(df)
    df = _add_price_features(df)
    df = _add_target(df)

    # Drop rows where lag or target is unavailable
    rows_before = len(df)
    df = df.dropna(subset=["price_lag_2w", TARGET_COL]).reset_index(drop=True)
    rows_after = len(df)
    print(f"[engineer] Dropped {rows_before - rows_after} rows (insufficient lag or no target)")

    df = _select_output_columns(df)

    # Round floats
    float_cols = df.select_dtypes(include="float64").columns
    df[float_cols] = df[float_cols].round(4)

    _check_leakage(df)

    return df


def save_features() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_features()

    out = PROCESSED_DIR / "features.csv"
    df.to_csv(out, index=False)

    print(f"\n[engineer] Saved {out.name}")
    print(f"[engineer] Shape: {df.shape}")
    print(f"[engineer] Columns ({len(df.columns)}):")
    for c in df.columns:
        print(f"  {c}")
    print(f"\n[engineer] Null counts:")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    print(nulls.to_string() if len(nulls) else "  none")
    print(f"\n[engineer] market_price stats:")
    print(df["market_price"].describe().round(4).to_string())
    print(f"\n[engineer] target ({TARGET_COL}) stats:")
    print(df[TARGET_COL].describe().round(4).to_string())

    return df


if __name__ == "__main__":
    save_features()
