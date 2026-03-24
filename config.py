from pathlib import Path

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"
FIGURES_DIR = BASE_DIR / "outputs" / "figures"
DB_PATH = DATA_DIR / "riftbound.db"

SOURCES = {
    "tcgindex": "https://tcgindex.io/riftbound",
    "riftbounddata": "https://riftbounddata.com",
    "riftboundstats": "https://www.riftboundstats.com",
}

RIFTBOUNDSTATS_API = "https://www.riftboundstats.com/api"

SET_RELEASE_DATES = [
    "2025-02-11",  # Origins — Riftbound launch
    "2025-08-01",  # Proving Grounds — estimated (pre-dates our price history window)
    "2026-01-20",  # Spiritforged — estimated from first observed price data (2026-01-26)
]

RARITY_TIER = {
    "Common": 1,
    "Uncommon": 2,
    "Rare": 3,
    "Promo": 3,   # promo prints are Rare-equivalent in market value
    "Epic": 4,
    "Showcase": 5,
}

MODEL_PARAMS = {
    "ridge_alphas": [0.01, 0.1, 1.0, 10.0, 100.0],
    "lasso_alphas": [0.001, 0.01, 0.1, 1.0],
    "rf_n_estimators": 200,
    "xgb_n_estimators": 300,
    "xgb_learning_rate": 0.05,
    "ts_test_weeks": 3,   # reduced from 8 — data window is only 11 weeks
    "ts_cv_splits": 5,
}

TARGET_COL = "price_next_week"
DATE_COL = "week"
CARD_COL = "card_name"

SCRAPER_SLEEP = 1.5  # seconds between requests
PAGE_SIZE = 100
