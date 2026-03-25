"""
Phase 1 — Data Collection runner.

Usage:
    python run_phase1.py                  # TCGCSV + RiftboundStats (default)
    python run_phase1.py --tcgcsv         # TCGCSV price history only
    python run_phase1.py --riftboundstats # RiftboundStats tournament data only
    python run_phase1.py --tcgplayer      # Legacy TCGPlayer cookie scraper
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1: Data Collection")
    parser.add_argument("--tcgcsv",         action="store_true")
    parser.add_argument("--riftboundstats", action="store_true")
    parser.add_argument("--tcgplayer",      action="store_true",
                        help="Legacy TCGPlayer cookie scraper (requires TCGPLAYER_COOKIE env var)")
    args = parser.parse_args()

    run_default = not (args.tcgcsv or args.riftboundstats or args.tcgplayer)

    if run_default or args.tcgcsv:
        print("=" * 60)
        print("TCGCSV scraper (price history + card metadata -> SQLite)")
        print("=" * 60)
        from src.scrapers.tcgcsv_scraper import scrape_all as scrape_tcgcsv
        scrape_tcgcsv()

    if run_default or args.riftboundstats:
        print("=" * 60)
        print("RiftboundStats API scraper (tournament data)")
        print("=" * 60)
        from src.scrapers.riftboundstats_scraper import scrape_all as scrape_riftboundstats
        scrape_riftboundstats()

    if args.tcgplayer:
        print("=" * 60)
        print("TCGPlayer cookie scraper (legacy)")
        print("=" * 60)
        import os
        cookie = os.environ.get("TCGPLAYER_COOKIE", "")
        if not cookie:
            raise RuntimeError("Set TCGPLAYER_COOKIE env var before running --tcgplayer.")
        from src.scrapers.tcgplayer_scraper import scrape_all as scrape_tcgplayer
        scrape_tcgplayer(cookie=cookie, range_="quarter")

    print("\nPhase 1 complete. Check data/ for output files.")


if __name__ == "__main__":
    main()
