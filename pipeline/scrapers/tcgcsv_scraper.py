"""
TCGCSV price history scraper for Riftbound.

TCGCSV (tcgcsv.com) mirrors TCGPlayer data daily, no auth required.

Two data sources:
  1. Live product metadata — https://tcgcsv.com/tcgplayer/89/{groupId}/products
     Fetched once; gives card names, rarity, type, domain.

  2. Daily price archives — https://tcgcsv.com/archive/tcgplayer/prices-YYYY-MM-DD.ppmd.7z
     One 7z archive per day (~3.6 MB compressed). Contains prices for all TCGs;
     we extract only Riftbound files: YYYY-MM-DD/89/{groupId}/prices (plain JSON).

Writes to SQLite (data/riftbound.db):
  cards       — card metadata (one row per product_id)
  prices_raw  — daily prices  (one row per product_id × date × sub_type_name)

Incremental: skips dates already present in prices_raw.
Weekly cadence: downloads every Monday between TCGCSV_START_DATE and today.

Usage:
    python src/scrapers/tcgcsv_scraper.py
"""
import io
import json
import sqlite3
import tempfile
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import py7zr
import requests
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import (
    DB_PATH,
    SCRAPER_SLEEP,
    TCGCSV_BASE,
    TCGCSV_CATEGORY_ID,
    TCGCSV_GROUPS,
    TCGCSV_START_DATE,
)

CAT = TCGCSV_CATEGORY_ID
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; riftbound-price-forecast/1.0)"}


# ---------------------------------------------------------------------------
# DB setup
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        PRAGMA foreign_keys=OFF;
        DROP TABLE IF EXISTS features;
        DROP TABLE IF EXISTS master;
        DROP TABLE IF EXISTS prices_weekly;
        DROP TABLE IF EXISTS prices_raw;
        DROP TABLE IF EXISTS cards;
        PRAGMA foreign_keys=ON;

        CREATE TABLE cards (
            product_id   INTEGER PRIMARY KEY,
            name         TEXT    NOT NULL,
            clean_name   TEXT,
            rarity       TEXT,
            card_type    TEXT,
            domain       TEXT,
            set_name     TEXT,
            group_id     INTEGER
        );

        CREATE TABLE prices_raw (
            date             TEXT    NOT NULL,
            product_id       INTEGER NOT NULL,
            sub_type_name    TEXT,
            low_price        REAL,
            mid_price        REAL,
            high_price       REAL,
            market_price     REAL,
            direct_low_price REAL,
            PRIMARY KEY (date, product_id, sub_type_name)
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Metadata scrape (live endpoint)
# ---------------------------------------------------------------------------

def _parse_extended(extended_data: list[dict]) -> dict[str, str]:
    """Convert extendedData list to a flat {name: value} dict."""
    return {item["name"]: item["value"] for item in extended_data if "name" in item}


def scrape_metadata(conn: sqlite3.Connection) -> int:
    """
    Download card metadata from live TCGCSV product endpoints.
    Upserts into the cards table. Returns number of cards inserted/updated.
    """
    rows: list[tuple] = []

    for set_name, group_id in TCGCSV_GROUPS.items():
        url = f"{TCGCSV_BASE}/tcgplayer/{CAT}/{group_id}/products"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        products = resp.json().get("results", [])

        for p in products:
            ext = _parse_extended(p.get("extendedData", []))
            rarity    = ext.get("Rarity")
            card_type = ext.get("Card Type")
            # Filter to actual cards only (sealed product has no Rarity or Card Type)
            if not rarity or not card_type:
                continue
            rows.append((
                p["productId"],
                p.get("name", ""),
                p.get("cleanName", ""),
                rarity,
                card_type,
                ext.get("Domain"),
                set_name,
                group_id,
            ))
        time.sleep(SCRAPER_SLEEP)

    conn.executemany(
        """INSERT INTO cards (product_id, name, clean_name, rarity, card_type, domain, set_name, group_id)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(product_id) DO UPDATE SET
             name=excluded.name, clean_name=excluded.clean_name,
             rarity=excluded.rarity, card_type=excluded.card_type,
             domain=excluded.domain, set_name=excluded.set_name,
             group_id=excluded.group_id""",
        rows,
    )
    conn.commit()
    print(f"[tcgcsv] Metadata: {len(rows)} cards upserted across {len(TCGCSV_GROUPS)} sets")
    return len(rows)


# ---------------------------------------------------------------------------
# Archive price scrape (historical)
# ---------------------------------------------------------------------------

def _weekly_dates(start: str, end: date | None = None) -> list[str]:
    """Return every Monday from start to end (inclusive), as YYYY-MM-DD strings."""
    start_dt = datetime.strptime(start, "%Y-%m-%d").date()
    # Advance to next Monday if start isn't one
    days_ahead = (7 - start_dt.weekday()) % 7
    start_dt += timedelta(days=days_ahead)

    end_dt = end or date.today()
    dates = []
    current = start_dt
    while current <= end_dt:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(weeks=1)
    return dates


def _loaded_dates(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT DISTINCT date FROM prices_raw").fetchall()
    return {r[0] for r in rows}


def _fetch_archive_prices(date_str: str) -> dict[str, list[dict]]:
    """
    Download the daily 7z archive and extract Riftbound price files.
    Returns {date_str: [price_record, ...]} or empty dict on failure.
    """
    url = f"{TCGCSV_BASE}/archive/tcgplayer/prices-{date_str}.ppmd.7z"
    resp = requests.get(url, headers=HEADERS, timeout=60, stream=True)
    if resp.status_code == 404:
        return {}
    resp.raise_for_status()

    archive_bytes = io.BytesIO(resp.content)
    group_ids = set(TCGCSV_GROUPS.values())
    records: list[dict] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / f"prices-{date_str}.7z"
        tmp_path.write_bytes(archive_bytes.getvalue())

        with py7zr.SevenZipFile(tmp_path, mode="r") as zf:
            all_names = zf.getnames()
            # Target paths: YYYY-MM-DD/89/{groupId}/prices
            targets = [
                n for n in all_names
                if n.startswith(f"{date_str}/{CAT}/")
                and n.endswith("/prices")
                and int(n.split("/")[2]) in group_ids
            ]
            if not targets:
                return {}
            zf.extract(path=tmpdir, targets=targets)

        for target in targets:
            price_file = Path(tmpdir) / target
            if not price_file.exists():
                continue
            raw = json.loads(price_file.read_text(encoding="utf-8"))
            for entry in raw.get("results", []):
                records.append(entry)

    return {date_str: records}


def scrape_history(
    conn: sqlite3.Connection,
    start: str = TCGCSV_START_DATE,
) -> None:
    """
    Download weekly archive snapshots from start to today.
    Skips dates already present in the DB.
    """
    all_dates = _weekly_dates(start)
    already_loaded = _loaded_dates(conn)
    pending = [d for d in all_dates if d not in already_loaded]

    if not pending:
        print("[tcgcsv] Price history up to date — nothing to fetch")
        return

    print(f"[tcgcsv] Fetching {len(pending)} weekly snapshots "
          f"({pending[0]} -> {pending[-1]})...")

    total_rows = 0
    for date_str in tqdm(pending, desc="archives"):
        try:
            data = _fetch_archive_prices(date_str)
        except Exception as exc:
            print(f"\n[tcgcsv] WARNING: failed to fetch {date_str}: {exc}")
            time.sleep(SCRAPER_SLEEP)
            continue

        if not data:
            # Archive exists but no Riftbound data yet (pre-launch dates)
            time.sleep(SCRAPER_SLEEP)
            continue

        rows = [
            (
                date_str,
                entry["productId"],
                entry.get("subTypeName"),
                entry.get("lowPrice"),
                entry.get("midPrice"),
                entry.get("highPrice"),
                entry.get("marketPrice"),
                entry.get("directLowPrice"),
            )
            for entry in data[date_str]
            if entry.get("productId")
        ]

        conn.executemany(
            """INSERT OR IGNORE INTO prices_raw
               (date, product_id, sub_type_name, low_price, mid_price,
                high_price, market_price, direct_low_price)
               VALUES (?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()
        total_rows += len(rows)
        time.sleep(SCRAPER_SLEEP)

    print(f"[tcgcsv] Inserted {total_rows} price rows across {len(pending)} dates")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def scrape_all() -> None:
    conn = _get_conn()
    _init_db(conn)
    scrape_metadata(conn)
    scrape_history(conn)
    conn.close()

    # Report
    conn = sqlite3.connect(DB_PATH)
    n_cards = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    n_dates = conn.execute("SELECT COUNT(DISTINCT date) FROM prices_raw").fetchone()[0]
    n_rows  = conn.execute("SELECT COUNT(*) FROM prices_raw").fetchone()[0]
    conn.close()
    print(f"[tcgcsv] DB summary: {n_cards} cards | {n_dates} dates | {n_rows} price rows")


if __name__ == "__main__":
    scrape_all()
