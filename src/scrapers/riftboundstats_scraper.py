"""
RiftboundStats scraper — uses the public REST API.
Endpoints confirmed:
  GET /api/cards          → 101 cards with metadata + market_price + low_price
  GET /api/events         → 194 tournaments with dates/locations/formats
  GET /api/decks          → 22,807+ decks with timestamps + best_placement + legend
"""
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import RIFTBOUNDSTATS_API, RAW_DIR, SCRAPER_SLEEP

BASE = RIFTBOUNDSTATS_API
OUT_DIR = RAW_DIR / "riftboundstats"
TODAY = datetime.now().strftime("%Y-%m-%d")

# Deck fetching: only need a representative sample for play-rate computation.
# 5,000 decks spanning the full date range is more than sufficient.
DECK_PAGE_SIZE = 50
DECK_MAX_PAGES = 100  # 100 * 50 = 5,000 decks

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.riftboundstats.com/",
}


def _get(endpoint: str, params: dict | None = None, retries: int = 4) -> dict | list:
    url = f"{BASE}/{endpoint}"
    delay = 3.0
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
            if resp.status_code in (502, 503, 504):
                if attempt < retries - 1:
                    print(f"[riftboundstats] {resp.status_code} on {url} — retrying in {delay:.0f}s...")
                    time.sleep(delay)
                    delay *= 2
                    continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
            if attempt < retries - 1:
                print(f"[riftboundstats] Connection error on {url} — retrying in {delay:.0f}s...")
                time.sleep(delay)
                delay *= 2
    raise RuntimeError(f"Failed after {retries} attempts: {url}") from last_exc


def _paginate(
    endpoint: str,
    page_size: int = 100,
    max_pages: int | None = None,
) -> list[dict]:
    """Fetch pages from a paginated endpoint. Stops at max_pages if set."""
    page = 1
    all_records: list[dict] = []

    while True:
        data = _get(endpoint, params={"page": page, "page_size": page_size})

        if isinstance(data, list):
            all_records.extend(data)
            break

        records = data.get("data", [])
        all_records.extend(records)
        total_pages = data.get("total_pages", 1)

        if page >= total_pages or not records:
            break
        if max_pages is not None and page >= max_pages:
            print(f"[riftboundstats] Stopping {endpoint} at page {page} (max_pages={max_pages})")
            break

        page += 1
        time.sleep(SCRAPER_SLEEP)

    return all_records


def scrape_cards() -> list[dict]:
    print("[riftboundstats] Fetching cards...")
    cards = _paginate("cards", page_size=200)
    print(f"[riftboundstats] Cards fetched: {len(cards)}")
    return cards


def scrape_events() -> list[dict]:
    print("[riftboundstats] Fetching events...")
    events = _paginate("events", page_size=200)
    print(f"[riftboundstats] Events fetched: {len(events)}")
    return events


def scrape_decks() -> list[dict]:
    print(f"[riftboundstats] Fetching decks (up to {DECK_MAX_PAGES * DECK_PAGE_SIZE} records)...")
    decks = _paginate("decks", page_size=DECK_PAGE_SIZE, max_pages=DECK_MAX_PAGES)
    print(f"[riftboundstats] Decks fetched: {len(decks)}")
    return decks


def scrape_deck_cards(deck_id: int) -> list[dict]:
    """Fetch the card list for a single deck. Returns [] on any failure."""
    try:
        data = _get(f"decks/{deck_id}/cards")
        if isinstance(data, list):
            return data
        return data.get("data", [])
    except (requests.HTTPError, requests.exceptions.ConnectionError, RuntimeError):
        return []


def scrape_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cards = scrape_cards()
    events = scrape_events()
    decks = scrape_decks()

    _save(cards, "cards")
    _save(events, "events")
    _save(decks, "decks")

    # Fetch card compositions only for tournament decks (best_placement not null).
    # These drive tournament_play_rate and tournament_top8_rate features.
    tournament_decks = [d for d in decks if d.get("best_placement") is not None]
    print(f"[riftboundstats] Fetching card lists for {len(tournament_decks)} tournament decks...")

    deck_cards: dict[int, list[dict]] = {}
    for deck in tqdm(tournament_decks, desc="deck cards"):
        deck_id = deck["id"]
        deck_cards[deck_id] = scrape_deck_cards(deck_id)
        time.sleep(SCRAPER_SLEEP)

    _save(deck_cards, "deck_cards")
    print("[riftboundstats] Done. All files saved to data/raw/riftboundstats/")


def _save(data: dict | list, name: str) -> None:
    path = OUT_DIR / f"{TODAY}_{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[riftboundstats] Saved {path.name}")


if __name__ == "__main__":
    scrape_all()
