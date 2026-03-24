"""
ETL loader — raw JSON -> SQLite.

Reads the latest raw JSON dumps from data/raw/ and bulk-inserts into the
database. All inserts use INSERT OR IGNORE / INSERT OR REPLACE so the loader
is safe to re-run (idempotent).

Usage:
  from src.database.loader import load_all
  load_all()
"""
import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import RAW_DIR, DB_PATH
from src.database.schema import create_schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _latest(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern), reverse=True)
    if not matches:
        raise FileNotFoundError(f"No file matching {pattern} in {directory}")
    return matches[0]


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _to_monday(date_str: str) -> str:
    """Return the ISO-week Monday for a given YYYY-MM-DD string."""
    d = datetime.strptime(date_str[:10], "%Y-%m-%d")
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_cards(conn: sqlite3.Connection) -> int:
    # Prefer full card catalog if available, fall back to base cards file
    stats_dir = RAW_DIR / "riftboundstats"
    candidates = sorted(stats_dir.glob("*_cards_full.json"), reverse=True)
    if not candidates:
        candidates = sorted(
            [p for p in stats_dir.glob("*_cards.json")
             if re.match(r"^\d{4}-\d{2}-\d{2}_cards\.json$", p.name)],
            reverse=True,
        )
    if not candidates:
        raise FileNotFoundError("No cards JSON found in data/raw/riftboundstats/")
    path = candidates[0]
    print(f"[loader] cards  <- {path.name}")

    cards = [c for c in _load_json(path) if isinstance(c, dict)]
    rows = [
        (
            c.get("id"),
            c.get("name"),
            c.get("type"),
            c.get("rarity"),
            c.get("domain"),
            c.get("energy"),
            c.get("power"),
            c.get("might"),
            c.get("set"),
            c.get("card_number"),
            c.get("tcgplayer_product_id"),
            c.get("market_price"),
            c.get("low_price"),
            c.get("created_at"),
        )
        for c in cards
    ]

    conn.executemany(
        """
        INSERT OR REPLACE INTO cards
            (id, name, type, rarity, domain, energy, power, might,
             set_name, card_number, tcgplayer_product_id,
             market_price, low_price, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    print(f"[loader] cards  -> {len(rows)} rows inserted/replaced")
    return len(rows)


def load_events(conn: sqlite3.Connection) -> int:
    path = _latest(RAW_DIR / "riftboundstats", "*_events.json")
    print(f"[loader] events <- {path.name}")

    events = _load_json(path)
    rows = [
        (
            e["id"],
            e.get("name"),
            e.get("location"),
            e.get("event_date"),
            e.get("format"),
            e.get("participant_count"),
            e.get("status"),
            e.get("event_type"),
            e.get("created_at"),
        )
        for e in events
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO events
            (id, name, location, event_date, format, participant_count,
             status, event_type, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    print(f"[loader] events -> {len(rows)} rows inserted")
    return len(rows)


def load_decks(conn: sqlite3.Connection) -> int:
    path = _latest(RAW_DIR / "riftboundstats", "*_decks.json")
    print(f"[loader] decks  <- {path.name}")

    decks = _load_json(path)
    rows = [
        (
            d["id"],
            d.get("name"),
            d.get("legend"),
            d.get("format"),
            d.get("best_placement"),
            d.get("best_placement_event_id"),
            d.get("best_placement_event_name"),
            d.get("created_at"),
        )
        for d in decks
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO decks
            (id, name, legend, format, best_placement,
             best_placement_event_id, best_placement_event_name, created_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    print(f"[loader] decks  -> {len(rows)} rows inserted")
    return len(rows)


def load_price_history(conn: sqlite3.Connection) -> int:
    path = _latest(RAW_DIR / "tcgplayer", "*_price_history.json")
    print(f"[loader] prices <- {path.name}")

    raw = _load_json(path)

    rows = []
    for pid_str, card in raw.items():
        product_id = card["product_id"]
        card_name  = card["card_name"]
        variant    = card.get("selected_variant")
        condition  = card.get("selected_condition")

        for bucket in card.get("buckets", []):
            mkt = float(bucket.get("marketPrice") or 0)
            if mkt == 0:
                continue  # no sales activity — skip

            bucket_date = bucket["bucketStartDate"][:10]
            rows.append((
                product_id,
                card_name,
                bucket_date,
                _to_monday(bucket_date),
                mkt,
                float(bucket.get("lowSalePrice") or 0),
                float(bucket.get("highSalePrice") or 0),
                int(bucket.get("quantitySold") or 0),
                int(bucket.get("transactionCount") or 0),
                variant,
                condition,
            ))

    conn.executemany(
        """
        INSERT OR IGNORE INTO price_history
            (product_id, card_name, bucket_date, week,
             market_price, low_price, high_price,
             qty_sold, transaction_count, variant, condition)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    print(f"[loader] prices -> {len(rows)} rows inserted")
    return len(rows)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_all(db_path: Path = DB_PATH) -> None:
    create_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        load_cards(conn)
        load_events(conn)
        load_decks(conn)
        load_price_history(conn)
        conn.commit()
    print(f"\n[loader] Done — database: {db_path}")


if __name__ == "__main__":
    load_all()
