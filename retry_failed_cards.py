"""
Retry scraper for TCGPlayer cards that returned 403 in the previous run.

Reads data/raw/tcgplayer/2026-03-24_failed.json, fetches price history for each,
and merges results into data/raw/tcgplayer/2026-03-24_price_history.json.

Uses 3s sleep between requests to avoid rate limiting.

Usage:
    set TCGPLAYER_COOKIE=<fresh_cookie>
    python retry_failed_cards.py
"""
import json
import os
import time
from pathlib import Path

import requests
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent))
from src.scrapers.tcgplayer_scraper import fetch_price_history, _best_sku

RAW_TCGPLAYER = Path("data/raw/tcgplayer")
FAILED_PATH = RAW_TCGPLAYER / "2026-03-24_failed.json"
HISTORY_PATH = RAW_TCGPLAYER / "2026-03-24_price_history.json"
SLEEP = 3.0


def main() -> None:
    cookie = os.environ.get("TCGPLAYER_COOKIE", "")
    if not cookie:
        raise RuntimeError("Set TCGPLAYER_COOKIE env var before running.")

    with open(FAILED_PATH, encoding="utf-8") as f:
        failed: list[dict] = json.load(f)

    with open(HISTORY_PATH, encoding="utf-8") as f:
        existing: dict[str, dict] = json.load(f)

    print(f"Retrying {len(failed)} failed cards (sleep={SLEEP}s)...")

    still_failed: list[dict] = []
    new_results: dict[str, dict] = {}

    for card in tqdm(failed, desc="retry"):
        pid = card["product_id"]
        name = card["name"]
        try:
            skus = fetch_price_history(pid, cookie=cookie, range_="quarter")
            best = _best_sku(skus)
            new_results[str(pid)] = {
                "card_name": name,
                "product_id": pid,
                "selected_variant": best.get("variant") if best else None,
                "selected_condition": best.get("condition") if best else None,
                "buckets": best.get("buckets", []) if best else [],
                "all_skus": skus,
            }
            if not best or not best.get("buckets"):
                print(f"\nWARNING: no bucket data for {name} (id={pid})")
        except requests.HTTPError as exc:
            print(f"\nHTTP {exc.response.status_code} for {name} (id={pid}) — skipping")
            still_failed.append(card)
        except Exception as exc:
            print(f"\nERROR for {name} (id={pid}): {exc}")
            still_failed.append(card)

        time.sleep(SLEEP)

    # Merge into existing
    merged = {**existing, **new_results}
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Total cards in history: {len(merged)}")
    print(f"New successes: {len(new_results)} | Still failed: {len(still_failed)}")

    if still_failed:
        with open(FAILED_PATH, "w", encoding="utf-8") as f:
            json.dump(still_failed, f, indent=2)
        print(f"Updated failed list: {FAILED_PATH.name}")
    else:
        FAILED_PATH.unlink()
        print("All cards recovered — deleted failed.json")


if __name__ == "__main__":
    main()
