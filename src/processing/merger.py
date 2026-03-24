"""
Phase 2 — Merging.

Reads:
  data/processed/prices_clean.csv
  data/processed/tournament_features.csv

Writes:
  data/processed/master.csv

Schema (one row per card_name × week):
  card_name, product_id, week, market_price, low_price, high_price,
  qty_sold, transaction_count, rarity, set, type, domain, variant,
  condition, legend_play_rate, legend_top8_rate
"""
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import PROCESSED_DIR


def _load(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    print(f"[merger] Loading {filename}")
    return pd.read_csv(path)


def merge() -> pd.DataFrame:
    prices = _load("prices_clean.csv")
    tournament = _load("tournament_features.csv")

    print(f"[merger] prices_clean: {prices.shape}")
    print(f"[merger] tournament_features: {tournament.shape}")

    # Left join: every price row gets tournament metrics for its domain+week.
    # Cards whose domain has no tournament data that week get 0 (not NaN) —
    # absence of play data is meaningful (archetype inactive that week).
    master = prices.merge(
        tournament[["domain", "week", "legend_play_rate", "legend_top8_rate"]],
        on=["domain", "week"],
        how="left",
    )

    master["legend_play_rate"] = master["legend_play_rate"].fillna(0)
    master["legend_top8_rate"] = master["legend_top8_rate"].fillna(0)

    # Canonical column order
    col_order = [
        "card_name", "product_id", "week",
        "market_price", "low_price", "high_price",
        "qty_sold", "transaction_count",
        "rarity", "set", "type", "domain", "variant", "condition",
        "legend_play_rate", "legend_top8_rate",
    ]
    master = master[col_order].sort_values(["card_name", "week"]).reset_index(drop=True)

    return master


def _report(df: pd.DataFrame) -> None:
    print(f"[merger] master.csv shape: {df.shape}")
    print(f"[merger] Cards: {df['card_name'].nunique()} | Weeks: {df['week'].nunique()}")
    print(f"[merger] Week range: {df['week'].min()} to {df['week'].max()}")
    print(f"[merger] Nulls:\n{df.isnull().sum()[df.isnull().sum() > 0].to_string() or '  none'}")
    print(f"\n[merger] market_price stats:")
    print(df["market_price"].describe().round(4).to_string())
    print(f"\n[merger] Sample rows:")
    print(df.head(6).to_string())


def save_master() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = merge()
    _report(df)
    out = PROCESSED_DIR / "master.csv"
    df.to_csv(out, index=False)
    print(f"\n[merger] Saved {out.name}")
    return df


if __name__ == "__main__":
    save_master()
