"""
Phase 2 — Cleaning.

Reads:  SQLite prices_raw + cards tables (data/riftbound.db)
Writes: SQLite prices_weekly table  +  data/processed/prices_clean.csv

Logic:
  - Join prices_raw with cards to get metadata.
  - Prefer Normal SKU over Foil per product; drop rows with no market_price.
  - Aggregate daily snapshots to weekly (Monday of ISO week).
  - One row per (product_id, week).
"""
import sqlite3
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH, PROCESSED_DIR


def _get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run the TCGCSV scraper first."
        )
    return sqlite3.connect(DB_PATH)


def _init_prices_weekly(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS prices_weekly (
            product_id   INTEGER NOT NULL,
            card_name    TEXT    NOT NULL,
            week         TEXT    NOT NULL,
            rarity       TEXT,
            set_name     TEXT,
            card_type    TEXT,
            domain       TEXT,
            market_price REAL,
            low_price    REAL,
            high_price   REAL,
            PRIMARY KEY (product_id, week)
        );
    """)
    conn.commit()


def _load_raw(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Join prices_raw with cards. Prefer Normal SKU; fall back to Foil.
    Returns one row per (product_id, date) — the best available SKU.
    """
    query = """
        SELECT
            p.date,
            p.product_id,
            p.sub_type_name,
            p.market_price,
            p.low_price,
            p.high_price,
            c.name        AS card_name,
            c.rarity,
            c.set_name,
            c.card_type,
            c.domain
        FROM prices_raw p
        INNER JOIN cards c ON c.product_id = p.product_id
        WHERE p.market_price IS NOT NULL
          AND p.market_price > 0
        ORDER BY p.product_id, p.date,
                 -- Normal preferred (0) before Foil (1) and others (2)
                 CASE p.sub_type_name
                     WHEN 'Normal' THEN 0
                     WHEN 'Foil'   THEN 1
                     ELSE               2
                 END
    """
    df = pd.read_sql_query(query, conn)

    # Keep best SKU per (product_id, date)
    df = df.drop_duplicates(subset=["product_id", "date"], keep="first").copy()
    return df


def _to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Floor date to Monday of its ISO week, then aggregate to weekly means."""
    dates = pd.to_datetime(df["date"])
    df["week"] = (dates - pd.to_timedelta(dates.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")

    agg = (
        df.groupby(["product_id", "card_name", "week", "rarity", "set_name", "card_type", "domain"])
        .agg(
            market_price=("market_price", "mean"),
            low_price=("low_price",    "mean"),
            high_price=("high_price",  "mean"),
        )
        .reset_index()
    )
    agg[["market_price", "low_price", "high_price"]] = (
        agg[["market_price", "low_price", "high_price"]].round(4)
    )
    return agg.sort_values(["card_name", "week"]).reset_index(drop=True)


def clean_prices() -> pd.DataFrame:
    conn = _get_conn()
    df = _load_raw(conn)
    conn.close()

    print(f"[cleaner] Raw rows (daily, best SKU): {len(df)}")
    df = _to_weekly(df)
    print(f"[cleaner] After weekly aggregation: {df.shape[0]} rows")
    print(f"[cleaner] Cards: {df['card_name'].nunique()} | Weeks: {df['week'].nunique()}")
    print(f"[cleaner] Week range: {df['week'].min()} to {df['week'].max()}")
    return df


def save_clean_prices() -> pd.DataFrame:
    df = clean_prices()

    # Write to SQLite
    conn = _get_conn()
    _init_prices_weekly(conn)
    conn.execute("DELETE FROM prices_weekly")
    df.to_sql("prices_weekly", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    # Write CSV for backward compatibility
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "prices_clean.csv"
    df.to_csv(out, index=False)
    print(f"[cleaner] Saved prices_weekly -> DB + {out.name} — shape: {df.shape}")
    return df


if __name__ == "__main__":
    save_clean_prices()
