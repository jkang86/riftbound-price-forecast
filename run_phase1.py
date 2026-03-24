"""
Phase 1 — Data Collection runner.

Usage:
    python run_phase1.py                  # run both scrapers
    python run_phase1.py --riftboundstats # RiftboundStats API only (no Selenium)
    python run_phase1.py --tcgindex       # TCGIndex Selenium only
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.scrapers.riftboundstats_scraper import scrape_all as scrape_riftboundstats
from src.scrapers.tcgindex_scraper import scrape_all as scrape_tcgindex


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1: Data Collection")
    parser.add_argument("--riftboundstats", action="store_true")
    parser.add_argument("--tcgindex", action="store_true")
    args = parser.parse_args()

    run_all = not args.riftboundstats and not args.tcgindex

    if run_all or args.riftboundstats:
        print("=" * 60)
        print("RiftboundStats API scraper")
        print("=" * 60)
        scrape_riftboundstats()

    if run_all or args.tcgindex:
        print("=" * 60)
        print("TCGIndex Selenium scraper")
        print("=" * 60)
        scrape_tcgindex()

    print("\nPhase 1 complete. Check data/raw/ for output files.")
    print("Confirm row counts and date ranges before proceeding to Phase 2.")


if __name__ == "__main__":
    main()
