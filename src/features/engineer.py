"""
Phase 3 — Feature Engineering.

Reads:  SQLite master table  (data/riftbound.db)
Writes: SQLite features table  +  data/processed/features.csv

Autoregressive price features are computed via SQL window functions:
  LAG / LEAD over (PARTITION BY product_id ORDER BY week)
  Rolling 4-week average via ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  Days since first sale via MIN() OVER partition

Categorical features (one-hot, ordinal) are applied in pandas after the SQL query.

Feature set
-----------
Ordinal:
  rarity_tier              Common=1 … Showcase=5

Temporal:
  set_release_flag         1 if week within ±2 weeks of any set release
  days_since_first_sale    days from card's first observed price

Autoregressive (SQL window functions):
  price_lag_1w             LAG(market_price, 1) per card
  price_lag_2w             LAG(market_price, 2) per card
  price_rolling_mean_4w    4-week rolling mean per card
  price_pct_change_1w      (price - lag_1w) / lag_1w

Tournament:
  tournament_play_rate     domain-level legend play rate
  tournament_top8_rate     domain-level legend top-8 rate

Dummies:
  type_*                   one-hot per card_type
  domain_primary_*         one-hot per primary domain

Target:
  price_next_week          LEAD(market_price, 1) per card
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH, PROCESSED_DIR, SET_RELEASE_DATES, RARITY_TIER, TARGET_COL

_RELEASE_DTS = [datetime.strptime(d, "%Y-%m-%d") for d in SET_RELEASE_DATES]
_RELEASE_WINDOW_WEEKS = 2


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run the merger first."
        )
    return sqlite3.connect(DB_PATH)


def _init_features_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS features")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS features (
            product_id            INTEGER NOT NULL,
            card_name             TEXT    NOT NULL,
            card_display          TEXT,
            week                  TEXT    NOT NULL,
            market_price          REAL,
            rarity_tier           INTEGER,
            days_since_first_sale INTEGER,
            set_release_flag      INTEGER,
            tournament_play_rate  REAL,
            tournament_top8_rate  REAL,
            price_lag_1w          REAL,
            price_lag_2w          REAL,
            price_rolling_mean_4w REAL,
            price_pct_change_1w   REAL,
            price_next_week       REAL,
            PRIMARY KEY (product_id, week)
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# SQL — window functions for price features
# ---------------------------------------------------------------------------

_PRICE_FEATURES_SQL = """
    WITH windowed AS (
        SELECT
            product_id,
            card_name,
            week,
            rarity,
            set_name,
            card_type,
            domain,
            market_price,
            legend_play_rate,
            legend_top8_rate,

            LAG(market_price, 1) OVER w                           AS price_lag_1w,
            LAG(market_price, 2) OVER w                           AS price_lag_2w,

            AVG(market_price) OVER (
                PARTITION BY product_id ORDER BY week
                ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
            )                                                      AS price_rolling_mean_4w,

            CAST(
                julianday(week) - MIN(julianday(week)) OVER (PARTITION BY product_id)
                AS INTEGER
            )                                                      AS days_since_first_sale,

            LEAD(market_price, 1) OVER w                          AS price_next_week

        FROM master
        WINDOW w AS (PARTITION BY product_id ORDER BY week)
    )
    SELECT *
    FROM windowed
    WHERE price_lag_2w    IS NOT NULL
      AND price_next_week IS NOT NULL
    ORDER BY product_id, week
"""


# ---------------------------------------------------------------------------
# Pandas feature builders (applied after SQL)
# ---------------------------------------------------------------------------

def _release_flag(week_str: str) -> int:
    dt = datetime.strptime(week_str, "%Y-%m-%d")
    return int(any(abs((dt - rd).days) <= _RELEASE_WINDOW_WEEKS * 7 for rd in _RELEASE_DTS))


def _add_rarity_tier(df: pd.DataFrame) -> pd.DataFrame:
    df["rarity_tier"] = df["rarity"].map(RARITY_TIER)
    unmapped = df["rarity_tier"].isna().sum()
    if unmapped:
        raise ValueError(
            f"[engineer] {unmapped} rows have unmapped rarity: "
            f"{df.loc[df['rarity_tier'].isna(), 'rarity'].unique()}"
        )
    return df


def _add_pct_change(df: pd.DataFrame) -> pd.DataFrame:
    df["price_pct_change_1w"] = (
        (df["market_price"] - df["price_lag_1w"])
        / df["price_lag_1w"].replace(0, np.nan)
    ).round(4)
    return df


def _add_release_flag(df: pd.DataFrame) -> pd.DataFrame:
    df["set_release_flag"] = df["week"].apply(_release_flag)
    return df


def _add_card_display(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.groupby("card_name")["product_id"].nunique()
    multi = set(counts[counts > 1].index)
    df["card_display"] = df.apply(
        lambda r: f"{r['card_name']} ({r['rarity']})" if r["card_name"] in multi else r["card_name"],
        axis=1,
    )
    return df


def _add_type_dummies(df: pd.DataFrame) -> pd.DataFrame:
    dummies = pd.get_dummies(df["card_type"], prefix="type", dtype=int)
    dummies.columns = [c.lower().replace(" ", "_") for c in dummies.columns]
    return pd.concat([df, dummies], axis=1)


def _add_domain_dummies(df: pd.DataFrame) -> pd.DataFrame:
    df["domain_primary"] = df["domain"].str.split("|").str[0]
    dummies = pd.get_dummies(df["domain_primary"], prefix="domain_primary", dtype=int)
    dummies.columns = [c.lower() for c in dummies.columns]
    return pd.concat([df, dummies], axis=1)


def _check_leakage(df: pd.DataFrame) -> None:
    id_cols  = {"card_name", "card_display", "product_id", "week", TARGET_COL}
    forbidden = {"low_price", "high_price"}
    leakers  = forbidden & (set(df.columns) - id_cols)
    if leakers:
        raise AssertionError(f"[engineer] Leakage detected — drop: {leakers}")
    if TARGET_COL not in df.columns:
        raise AssertionError(f"[engineer] Target column '{TARGET_COL}' missing.")
    print("[engineer] Leakage check passed.")


def _select_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    id_cols      = ["product_id", "card_name", "card_display", "week"]
    price_cols   = ["market_price"]
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
    type_cols   = sorted(c for c in df.columns if c.startswith("type_"))
    domain_cols = sorted(c for c in df.columns if c.startswith("domain_primary_"))
    target_col  = [TARGET_COL]

    ordered = id_cols + price_cols + feature_cols + type_cols + domain_cols + target_col
    return df[ordered]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_features() -> pd.DataFrame:
    conn = _get_conn()
    df = pd.read_sql_query(_PRICE_FEATURES_SQL, conn)
    conn.close()

    n_cards = df["card_name"].nunique()
    print(f"[engineer] Loaded master via SQL — {len(df)} rows, {n_cards} cards")

    # Rename tournament cols to match existing convention
    df = df.rename(columns={
        "legend_play_rate": "tournament_play_rate",
        "legend_top8_rate": "tournament_top8_rate",
    })

    df = _add_rarity_tier(df)
    df = _add_pct_change(df)
    df = _add_release_flag(df)
    df = _add_card_display(df)
    df = _add_type_dummies(df)
    df = _add_domain_dummies(df)

    df = _select_output_columns(df)

    float_cols = df.select_dtypes(include="float64").columns
    df[float_cols] = df[float_cols].round(4)

    _check_leakage(df)
    return df


def save_features() -> pd.DataFrame:
    df = build_features()

    conn = _get_conn()
    _init_features_table(conn)
    # Write base columns (no one-hot dummies — too dynamic for a fixed schema)
    base_cols = [
        "product_id", "card_name", "card_display", "week",
        "market_price", "rarity_tier", "days_since_first_sale",
        "set_release_flag", "tournament_play_rate", "tournament_top8_rate",
        "price_lag_1w", "price_lag_2w", "price_rolling_mean_4w",
        "price_pct_change_1w", TARGET_COL,
    ]
    df[base_cols].to_sql("features", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "features.csv"
    df.to_csv(out, index=False)

    print(f"\n[engineer] Saved features -> DB + {out.name}")
    print(f"[engineer] Shape: {df.shape}")
    print(f"[engineer] Columns ({len(df.columns)}):")
    for c in df.columns:
        print(f"  {c}")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    print(f"\n[engineer] Null counts:\n{nulls.to_string() if len(nulls) else '  none'}")
    print(f"\n[engineer] market_price stats:")
    print(df["market_price"].describe().round(4).to_string())
    print(f"\n[engineer] target ({TARGET_COL}) stats:")
    print(df[TARGET_COL].describe().round(4).to_string())

    return df


if __name__ == "__main__":
    save_features()
