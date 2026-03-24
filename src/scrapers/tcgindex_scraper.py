"""
TCGIndex scraper — uses Selenium + Chrome DevTools Protocol.

Strategy:
  1. Load the TCGIndex Riftbound overview page with performance logging enabled.
  2. Capture all XHR/Fetch network responses to discover internal API endpoints.
  3. If price-history JSON endpoints are found, hit them directly with requests.
  4. Fall back to DOM extraction if no clean API is discoverable.

Prerequisite: Chrome + ChromeDriver installed and on PATH.
Run: python src/scrapers/tcgindex_scraper.py
"""
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import SOURCES, RAW_DIR, SCRAPER_SLEEP

OUT_DIR = RAW_DIR / "tcgindex"
TODAY = datetime.now().strftime("%Y-%m-%d")
BASE_URL = SOURCES["tcgindex"]


def _build_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    # Enable performance logging to capture network requests
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    return webdriver.Chrome(options=opts)


def _drain_network_log(driver) -> list[dict]:
    """Return all captured XHR/Fetch responses from the performance log."""
    raw_logs = driver.get_log("performance")
    results = []
    for entry in raw_logs:
        try:
            msg = json.loads(entry["message"])["message"]
            if msg.get("method") == "Network.responseReceived":
                params = msg["params"]
                if params.get("type") in ("XHR", "Fetch"):
                    results.append(params)
        except (KeyError, json.JSONDecodeError):
            continue
    return results


def _find_price_api(driver) -> str | None:
    """
    Parse the network log to find an API endpoint that returns price/card data.
    Returns the base API URL if found.
    """
    log_entries = _drain_network_log(driver)
    for entry in log_entries:
        url = entry.get("response", {}).get("url", "")
        if any(kw in url.lower() for kw in ("price", "card", "market", "riftbound")):
            if "api" in url.lower() or url.endswith(".json"):
                print(f"[tcgindex] Discovered API endpoint: {url}")
                return url
    return None


def _extract_next_data(driver) -> dict | None:
    """Attempt to extract window.__NEXT_DATA__ — standard Next.js data payload."""
    try:
        data = driver.execute_script("return window.__NEXT_DATA__")
        if data:
            return data
    except Exception:
        pass
    return None


def _extract_dom_cards(driver) -> list[dict]:
    """
    Last-resort DOM extraction: find all card rows/cells visible after render.
    Returns a list of partial card dicts with whatever is parseable.
    """
    from selenium.webdriver.common.by import By
    cards = []
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "[data-card-name], [class*='card-row'], [class*='CardRow']")
        for row in rows:
            name = row.get_attribute("data-card-name") or row.get_attribute("data-name") or ""
            price_el = None
            for sel in ["[class*='price']", "[class*='Price']", "td:nth-child(3)"]:
                els = row.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    price_el = els[0]
                    break
            price_text = price_el.text.strip() if price_el else ""
            price_match = re.search(r"[\d.]+", price_text.replace(",", ""))
            cards.append({
                "name": name,
                "price_text": price_text,
                "price": float(price_match.group()) if price_match else None,
                "scraped_at": TODAY,
            })
    except Exception as e:
        print(f"[tcgindex] DOM extraction failed: {e}")
    return cards


def _wait_for_content(driver, timeout: int = 20) -> None:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # Give React/Next time to hydrate
        time.sleep(5)
    except Exception:
        pass


def scrape_overview(driver) -> dict[str, Any]:
    """Load the main Riftbound page and extract all discoverable data."""
    print(f"[tcgindex] Loading {BASE_URL} ...")
    driver.get(BASE_URL)
    _wait_for_content(driver)

    result: dict[str, Any] = {"scraped_at": TODAY, "source": BASE_URL}

    # Strategy 1: Next.js page data
    next_data = _extract_next_data(driver)
    if next_data:
        print("[tcgindex] Found __NEXT_DATA__ payload")
        result["next_data"] = next_data
        return result

    # Strategy 2: Discover API from network log
    api_url = _find_price_api(driver)
    if api_url:
        result["discovered_api"] = api_url
        try:
            resp = requests.get(api_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            result["api_data"] = resp.json()
            print(f"[tcgindex] API data fetched from {api_url}")
            return result
        except Exception as e:
            print(f"[tcgindex] API fetch failed: {e}")

    # Strategy 3: DOM extraction
    print("[tcgindex] Falling back to DOM extraction...")
    dom_cards = _extract_dom_cards(driver)
    result["dom_cards"] = dom_cards
    print(f"[tcgindex] DOM extraction found {len(dom_cards)} card entries")

    return result


def scrape_card_page(driver, card_name: str, card_url: str) -> dict[str, Any]:
    """Navigate to an individual card page and extract price history."""
    driver.get(card_url)
    _wait_for_content(driver)

    result: dict[str, Any] = {
        "card_name": card_name,
        "url": card_url,
        "scraped_at": TODAY,
    }

    next_data = _extract_next_data(driver)
    if next_data:
        result["next_data"] = next_data
        return result

    api_url = _find_price_api(driver)
    if api_url:
        result["discovered_api"] = api_url
        try:
            resp = requests.get(api_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            result["api_data"] = resp.json()
        except Exception as e:
            print(f"[tcgindex] Card API fetch failed for {card_name}: {e}")

    return result


def _save(data: Any, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{TODAY}_{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[tcgindex] Saved {path.name}")


def scrape_all() -> None:
    driver = _build_driver()
    try:
        overview = scrape_overview(driver)
        _save(overview, "overview")

        # If the overview revealed card links, attempt per-card history scraping
        card_links: list[tuple[str, str]] = []

        # Extract from Next.js data if available
        if "next_data" in overview:
            try:
                pages_props = overview["next_data"].get("props", {}).get("pageProps", {})
                cards = pages_props.get("cards", pages_props.get("data", []))
                for c in cards:
                    name = c.get("name", c.get("cardName", ""))
                    slug = c.get("slug", name.lower().replace(" ", "-"))
                    if name:
                        card_links.append((name, f"{BASE_URL}/cards/{slug}"))
            except Exception:
                pass

        if card_links:
            print(f"[tcgindex] Scraping price history for {len(card_links)} cards...")
            card_histories = []
            for name, url in tqdm(card_links, desc="card history"):
                history = scrape_card_page(driver, name, url)
                card_histories.append(history)
                time.sleep(SCRAPER_SLEEP)
            _save(card_histories, "card_histories")
        else:
            print(
                "[tcgindex] No card links discoverable from overview page.\n"
                "           The site may require authenticated sessions or\n"
                "           a different URL structure. Review the saved overview.json\n"
                "           and inspect the TCGIndex network tab in your browser to\n"
                "           find the correct card URL pattern, then update this scraper."
            )

    finally:
        driver.quit()

    print("[tcgindex] Done.")


if __name__ == "__main__":
    scrape_all()
