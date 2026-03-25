"""
TCGPlayer Infinite price history scraper.

Endpoint (requires browser session cookie):
  GET https://infinite-api.tcgplayer.com/price/history/{product_id}/detailed?range=quarter

Fetches per-card price history for all cards in data/raw/riftboundstats/*_cards.json.
Saves to data/raw/tcgplayer/YYYY-MM-DD_price_history.json

Price data lives in the `buckets` array per SKU — 3-day windows with:
  bucketStartDate, marketPrice, lowSalePrice, highSalePrice, quantitySold, transactionCount

We extract Near Mint Normal (preferred) or Near Mint Foil per card.
"""
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import RAW_DIR, SCRAPER_SLEEP

OUT_DIR = RAW_DIR / "tcgplayer"
TODAY = datetime.now().strftime("%Y-%m-%d")

BASE_URL = "https://infinite-api.tcgplayer.com/price/history/{product_id}/detailed"

# Cookie must be passed in at runtime — do NOT hardcode here.
# Set via TCGPLAYER_COOKIE env var or pass to scrape_all().
HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.tcgplayer.com/",
}

CONDITION_PRIORITY = ["Near Mint", "Lightly Played", "Moderately Played", "Damaged"]
VARIANT_PRIORITY = ["Normal", "Foil"]


def _load_cards() -> list[dict]:
    stats_dir = RAW_DIR / "riftboundstats"
    # Prefer cards_full_v2 (full 529-card catalog), then any cards_full, then YYYY-MM-DD_cards.json
    import re as _re
    v2 = sorted(stats_dir.glob("*_cards_full_v2.json"), reverse=True)
    if v2:
        path = v2[0]
    else:
        full = sorted(stats_dir.glob("*_cards_full.json"), reverse=True)
        if full:
            path = full[0]
        else:
            candidates = sorted(
                [p for p in stats_dir.glob("*_cards.json")
                 if _re.match(r"^\d{4}-\d{2}-\d{2}_cards\.json$", p.name)],
                reverse=True,
            )
            if not candidates:
                raise FileNotFoundError(f"No cards JSON found in {stats_dir}")
            path = candidates[0]
    print(f"[tcgplayer] Loading cards from {path.name}")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [c for c in raw if isinstance(c, dict)]


def fetch_price_history(product_id: int | str, cookie: str, range_: str = "quarter") -> list[dict]:
    """Fetch price history for a single product. Returns list of SKU entries."""
    url = BASE_URL.format(product_id=product_id)
    headers = {**HEADERS_BASE, "Cookie": cookie}
    resp = requests.get(url, headers=headers, params={"range": range_}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        return data.get("result", [])
    return data


def _best_sku(skus: list[dict]) -> dict | None:
    """Pick the best SKU: prefer Near Mint Normal, fall back to Near Mint Foil."""
    for variant in VARIANT_PRIORITY:
        for condition in CONDITION_PRIORITY:
            for sku in skus:
                if sku.get("variant") == variant and sku.get("condition") == condition:
                    if sku.get("buckets"):
                        return sku
    # Last resort: first SKU with any buckets
    for sku in skus:
        if sku.get("buckets"):
            return sku
    return None


def scrape_all(cookie: str, range_: str = "quarter") -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    cards = _load_cards()

    # Deduplicate by product_id — cards.json has reprints with same product_id
    seen_ids: set[int] = set()
    unique_cards: list[dict] = []
    for c in cards:
        pid = c.get("tcgplayer_product_id")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique_cards.append(c)

    print(f"[tcgplayer] Fetching price history for {len(unique_cards)} unique cards (range={range_})...")

    results: dict[str, dict] = {}
    failed: list[dict] = []

    for card in tqdm(unique_cards, desc="price history"):
        pid = card["tcgplayer_product_id"]
        name = card["name"]
        try:
            skus = fetch_price_history(pid, cookie=cookie, range_=range_)
            best = _best_sku(skus)
            results[str(pid)] = {
                "card_name": name,
                "product_id": pid,
                "rarity": card.get("rarity"),
                "set": card.get("set"),
                "type": card.get("type"),
                "domain": card.get("domain"),
                "selected_variant": best.get("variant") if best else None,
                "selected_condition": best.get("condition") if best else None,
                "buckets": best.get("buckets", []) if best else [],
                "all_skus": skus,
            }
            if not best or not best.get("buckets"):
                print(f"\n[tcgplayer] WARNING: no bucket data for {name} (id={pid})")
        except requests.HTTPError as exc:
            print(f"\n[tcgplayer] HTTP {exc.response.status_code} for {name} (id={pid}) — skipping")
            failed.append({"name": name, "product_id": pid, "error": str(exc)})
        except Exception as exc:
            print(f"\n[tcgplayer] ERROR for {name} (id={pid}): {exc}")
            failed.append({"name": name, "product_id": pid, "error": str(exc)})

        time.sleep(SCRAPER_SLEEP)

    out_path = OUT_DIR / f"{TODAY}_price_history.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[tcgplayer] Saved {out_path.name}")
    print(f"[tcgplayer] Success: {len(results)} | Failed: {len(failed)}")

    if failed:
        fail_path = OUT_DIR / f"{TODAY}_failed.json"
        with open(fail_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, indent=2)
        print(f"[tcgplayer] Failed cards saved to {fail_path.name}")


if __name__ == "__main__":
    import os
    cookie = os.environ.get("TCGPLAYER_COOKIE", "")
    if not cookie:
        raise RuntimeError("Set TCGPLAYER_COOKIE env var before running.")
    scrape_all(cookie=cookie, range_="quarter")
