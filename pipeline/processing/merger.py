"""
Phase 2 — Merging.

Reads:  SQLite prices_weekly table  +  data/processed/tournament_features.csv
Writes: SQLite master table         +  data/processed/master.csv

Joins weekly card prices with domain-level tournament metrics.
One row per (product_id, week).
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
            f"Database not found at {DB_PATH}. Run the cleaner first."
        )
    return sqlite3.connect(DB_PATH)


def _init_master(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS master (
            product_id        INTEGER NOT NULL,
            card_name         TEXT    NOT NULL,
            week              TEXT    NOT NULL,
            market_price      REAL,
            low_price         REAL,
            high_price        REAL,
            rarity            TEXT,
            set_name          TEXT,
            card_type         TEXT,
            domain            TEXT,
            legend_play_rate  REAL    NOT NULL DEFAULT 0,
            legend_top8_rate  REAL    NOT NULL DEFAULT 0,
            PRIMARY KEY (product_id, week)
        );
    """)
    conn.commit()


def merge() -> pd.DataFrame:
    conn = _get_conn()
    prices = pd.read_sql_query("SELECT * FROM prices_weekly", conn)
    conn.close()

    tournament_path = PROCESSED_DIR / "tournament_features.csv"
    tournament = pd.read_csv(tournament_path)

    print(f"[merger] prices_weekly: {prices.shape}")
    print(f"[merger] tournament_features: {tournament.shape}")

    master = prices.merge(
        tournament[["domain", "week", "legend_play_rate", "legend_top8_rate"]],
        on=["domain", "week"],
        how="left",
    )
    master["legend_play_rate"] = master["legend_play_rate"].fillna(0)
    master["legend_top8_rate"] = master["legend_top8_rate"].fillna(0)

    col_order = [
        "product_id", "card_name", "week",
        "market_price", "low_price", "high_price",
        "rarity", "set_name", "card_type", "domain",
        "legend_play_rate", "legend_top8_rate",
    ]
    master = master[col_order].sort_values(["card_name", "week"]).reset_index(drop=True)
    return master


def _report(df: pd.DataFrame) -> None:
    print(f"[merger] master shape: {df.shape}")
    print(f"[merger] Cards: {df['card_name'].nunique()} | Weeks: {df['week'].nunique()}")
    print(f"[merger] Week range: {df['week'].min()} to {df['week'].max()}")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    print(f"[merger] Nulls:\n{nulls.to_string() if len(nulls) else '  none'}")
    print(f"\n[merger] market_price stats:")
    print(df["market_price"].describe().round(4).to_string())


def save_master() -> pd.DataFrame:
    df = merge()
    _report(df)

    conn = _get_conn()
    _init_master(conn)
    conn.execute("DELETE FROM master")
    df.to_sql("master", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "master.csv"
    df.to_csv(out, index=False)
    print(f"\n[merger] Saved master -> DB + {out.name}")
    return df


if __name__ == "__main__":
    save_master()
