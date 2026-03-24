"""
Phase 2 — Cleaning.

Reads:  data/raw/tcgplayer/YYYY-MM-DD_price_history.json
Writes: data/processed/prices_clean.csv

Schema:
  card_name, product_id, rarity, set, type, domain,
  variant, condition, week, market_price, low_price,
  high_price, qty_sold, transaction_count
"""
import json
import re
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import RAW_DIR, PROCESSED_DIR


def _latest_file(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern), reverse=True)
    if not matches:
        raise FileNotFoundError(f"No file matching {pattern} in {directory}")
    return matches[0]


def _load_price_history() -> pd.DataFrame:
    path = _latest_file(RAW_DIR / "tcgplayer", "*_price_history.json")
    print(f"[cleaner] Loading {path.name}")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    rows = []
    for pid, card in raw.items():
        for bucket in card.get("buckets", []):
            rows.append({
                "card_name": card["card_name"],
                "product_id": card["product_id"],
                "rarity": card.get("rarity"),
                "set": card.get("set"),
                "type": card.get("type"),
                "domain": card.get("domain"),
                "variant": card.get("selected_variant"),
                "condition": card.get("selected_condition"),
                "bucket_date": bucket["bucketStartDate"],
                "market_price": float(bucket["marketPrice"] or 0),
                "low_price": float(bucket.get("lowSalePrice") or 0),
                "high_price": float(bucket.get("highSalePrice") or 0),
                "qty_sold": int(bucket.get("quantitySold") or 0),
                "transaction_count": int(bucket.get("transactionCount") or 0),
            })

    return pd.DataFrame(rows)


def _derive_week(df: pd.DataFrame) -> pd.DataFrame:
    """Floor bucket_date to the Monday of its ISO week."""
    dates = pd.to_datetime(df["bucket_date"])
    df["week"] = (dates - pd.to_timedelta(dates.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")
    return df


def _aggregate_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Mean market/low/high price + sum qty per (card_name, week)."""
    # Drop buckets with no sales activity
    df = df[df["market_price"] > 0].copy()

    agg = (
        df.groupby(["card_name", "product_id", "rarity", "set", "type", "domain",
                    "variant", "condition", "week"])
        .agg(
            market_price=("market_price", "mean"),
            low_price=("low_price", "mean"),
            high_price=("high_price", "mean"),
            qty_sold=("qty_sold", "sum"),
            transaction_count=("transaction_count", "sum"),
        )
        .reset_index()
    )

    agg[["market_price", "low_price", "high_price"]] = (
        agg[["market_price", "low_price", "high_price"]].round(4)
    )

    return agg.sort_values(["card_name", "week"]).reset_index(drop=True)


def clean_prices() -> pd.DataFrame:
    df = _load_price_history()
    print(f"[cleaner] Raw rows (buckets): {len(df)}")

    df = _derive_week(df)
    df = _aggregate_to_weekly(df)

    print(f"[cleaner] After weekly aggregation: {df.shape[0]} rows")
    print(f"[cleaner] Cards: {df['card_name'].nunique()} | Weeks: {df['week'].nunique()}")
    print(f"[cleaner] Week range: {df['week'].min()} to {df['week'].max()}")

    null_counts = df.isnull().sum()
    if null_counts.any():
        print(f"[cleaner] Nulls:\n{null_counts[null_counts > 0]}")

    return df


def save_clean_prices() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = clean_prices()
    out = PROCESSED_DIR / "prices_clean.csv"
    df.to_csv(out, index=False)
    print(f"[cleaner] Saved {out.name} — shape: {df.shape}")
    return df


if __name__ == "__main__":
    save_clean_prices()
