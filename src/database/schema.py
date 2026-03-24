"""
SQLite schema for the Riftbound Price Forecasting project.

Tables:
  cards          — card metadata from RiftboundStats API
  price_history  — 3-day bucket price data from TCGPlayer Infinite API
  decks          — deck metadata from RiftboundStats API
  events         — tournament events from RiftboundStats API

Run standalone to (re)create the schema on an existing DB:
  python -m src.database.schema
"""
import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH

DDL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cards (
    id                    INTEGER PRIMARY KEY,
    name                  TEXT    NOT NULL,
    type                  TEXT,
    rarity                TEXT,
    domain                TEXT,
    energy                INTEGER,
    power                 INTEGER,
    might                 INTEGER,
    set_name              TEXT,
    card_number           TEXT,
    tcgplayer_product_id  INTEGER UNIQUE,
    market_price          REAL,
    low_price             REAL,
    created_at            TEXT
);

CREATE TABLE IF NOT EXISTS price_history (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id        INTEGER NOT NULL REFERENCES cards(tcgplayer_product_id),
    card_name         TEXT    NOT NULL,
    bucket_date       TEXT    NOT NULL,
    week              TEXT    NOT NULL,
    market_price      REAL    NOT NULL,
    low_price         REAL,
    high_price        REAL,
    qty_sold          INTEGER,
    transaction_count INTEGER,
    variant           TEXT,
    condition         TEXT,
    UNIQUE (product_id, bucket_date)
);

CREATE TABLE IF NOT EXISTS events (
    id                INTEGER PRIMARY KEY,
    name              TEXT    NOT NULL,
    location          TEXT,
    event_date        TEXT,
    format            TEXT,
    participant_count INTEGER,
    status            TEXT,
    event_type        TEXT,
    created_at        TEXT
);

CREATE TABLE IF NOT EXISTS decks (
    id                        INTEGER PRIMARY KEY,
    name                      TEXT,
    legend                    TEXT,
    format                    TEXT,
    best_placement            INTEGER,
    best_placement_event_id   INTEGER REFERENCES events(id),
    best_placement_event_name TEXT,
    created_at                TEXT
);

CREATE INDEX IF NOT EXISTS idx_price_history_card   ON price_history (card_name);
CREATE INDEX IF NOT EXISTS idx_price_history_week   ON price_history (week);
CREATE INDEX IF NOT EXISTS idx_price_history_pid    ON price_history (product_id);
CREATE INDEX IF NOT EXISTS idx_decks_legend         ON decks (legend);
CREATE INDEX IF NOT EXISTS idx_decks_created        ON decks (created_at);
CREATE INDEX IF NOT EXISTS idx_events_date          ON events (event_date);
"""


def create_schema(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(DDL)
    print(f"[schema] Schema created/verified at {db_path}")


if __name__ == "__main__":
    create_schema()
