"""
Database runner — Phase 1.5 (post-scrape, pre-cleaning).

Creates the SQLite schema, loads all raw JSON files, then runs the
full suite of analytical queries.

Usage:
  python run_db.py           # create schema + load + run all queries
  python run_db.py --load    # create schema + load only (skip queries)
  python run_db.py --query   # run queries only (DB must already exist)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database.loader import load_all
from src.database.queries import run_all
from config import DB_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description="Riftbound SQLite runner")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--load",  action="store_true", help="Load data only, skip queries")
    group.add_argument("--query", action="store_true", help="Run queries only, skip load")
    args = parser.parse_args()

    if args.query:
        run_all(DB_PATH)
    elif args.load:
        load_all(DB_PATH)
    else:
        load_all(DB_PATH)
        run_all(DB_PATH)


if __name__ == "__main__":
    main()
