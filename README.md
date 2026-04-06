# Riftbound Card Price Forecasting Model

A data analytics portfolio project that scrapes card price and tournament data for the Riftbound TCG, engineers features, and trains multiple forecasting models to predict weekly card price movement. Framed as a financial/sports analytics crossover — think stock market meets competitive gaming.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live_Dashboard-FF4B4B?logo=streamlit)](https://riftbound-price-forecast.streamlit.app)
[![XGBoost](https://img.shields.io/badge/XGBoost-Model-orange)](https://xgboost.readthedocs.io)
[![Prophet](https://img.shields.io/badge/Prophet-Time--Series-blue)](https://facebook.github.io/prophet/)

**[Live Dashboard →](https://riftbound-price-forecast.streamlit.app)**

---

## What This Project Does

1. **Scrapes** card price history from TCGCSV (a daily TCGPlayer mirror, no auth required) and tournament data from the RiftboundStats REST API
2. **Stores** raw data in a SQLite database with analytical SQL queries (LAG, RANK, rolling averages, CTEs)
3. **Engineers** features: rarity tiers, lag prices, rolling means, tournament play rates, set release flags
4. **Trains** 6 forecasting models: Ridge, Lasso, Random Forest, XGBoost, ARIMA, Prophet
5. **Visualizes** everything in an interactive multi-page Streamlit dashboard

---

## Dashboard Pages

| Page | Description |
|---|---|
| 📈 Price Forecast | Actual vs predicted price per card, per model. Metrics: RMSE/MAE/R². |
| 🏆 Model Leaderboard | Side-by-side RMSE/MAE/R² comparison across all 6 models |
| 🔍 Card Explorer | Per-card price history with tournament play rate overlay |
| 🔥 Top Movers | Weekly biggest price movers — filterable by direction and top-N |
| 📊 Feature Analysis | Correlation heatmap, feature importances (XGBoost + RF), play rate vs price scatter |

---

## Model Results (test set: 3 weeks, 713 cards, 26 weeks of history)

| Model | RMSE | MAE | R² |
|---|---|---|---|
| **ARIMA** | $1.80 | $1.64 | 0.9986 |
| **Prophet** | $2.89 | $2.74 | 0.9963 |
| Ridge | $17.91 | $3.34 | 0.9964 |
| Random Forest | $19.07 | $2.98 | 0.9959 |
| Lasso | $33.83 | $5.72 | 0.9871 |
| XGBoost | $37.53 | $5.55 | 0.9841 |

> ARIMA/Prophet operate on per-product time series. Ridge and RF are cross-sectional models trained on lag + rolling + tournament features across all cards simultaneously.

---

## Tech Stack

- **Data collection:** `requests`, `py7zr` (TCGCSV archive scraper — no auth required; RiftboundStats REST API)
- **Database:** `sqlite3` — schema, ETL loader, 6 analytical SQL queries
- **Feature engineering:** `pandas`, `numpy`
- **Models:** `scikit-learn` (Ridge/Lasso/RF), `xgboost`, `statsmodels` (ARIMA), `prophet`
- **Dashboard:** `streamlit`, `plotly`

---

## Project Structure

```
riftbound-price-forecast/
├── config.py                       # All constants: paths, model params, rarity tiers
├── data/
│   └── exports/                    # CSVs consumed by the dashboard
│       ├── prices.csv              # Actual + predicted prices per card per model
│       ├── features.csv            # Feature matrix for correlation/scatter charts
│       ├── model_comparison.csv    # RMSE/MAE/R² per model
│       ├── top_movers.csv          # Weekly price movers with direction labels
│       └── feature_importances.csv # XGBoost + RF feature importance scores
├── src/
│   ├── scrapers/                   # TCGPlayer, RiftboundStats, RiftboundData scrapers
│   ├── database/                   # SQLite schema, ETL loader, analytical queries
│   ├── processing/                 # Cleaner, merger, tournament processor
│   ├── features/                   # Feature engineering pipeline
│   ├── models/                     # Ridge, Lasso, RF, XGBoost, ARIMA, Prophet + compare runner
│   └── dashboard/                  # Streamlit app — app.py + 5 pages + components
├── notebooks/                      # EDA + prototyping notebooks (phases 1–5)
└── PROJECT_LOG.md                  # Phase-by-phase log: original plan vs what actually happened
```

---

## Run Locally

```bash
pip install -r requirements.txt
streamlit run src/dashboard/app.py
```

The dashboard reads from `data/exports/` — all CSVs are committed, no pipeline re-run needed.

To re-run the full pipeline:

```bash
# Phase 1 — Scrape price history (no auth required)
python src/scrapers/tcgcsv_scraper.py

# Phase 2 — Clean + merge into master table
python -c "from src.processing.cleaner import save_clean_prices; save_clean_prices()"
python -c "from src.processing.merger import save_master; save_master()"

# Phase 3 — Feature engineering
python -c "from src.features.engineer import save_features; save_features()"

# Phase 4 — Train all models and export CSVs
python run_phase4.py
```

---

## Key Findings

- **Time-series models win**: ARIMA (RMSE $1.80) and Prophet (RMSE $2.89) outperform all cross-sectional models — per-card temporal modeling captures individual price dynamics that a shared feature matrix cannot
- **Ridge and RF are competitive** at $17.91 vs $19.07 RMSE — once `market_price` is excluded as a feature (it's `lag_0w` in disguise), RF learns meaningfully from rolling price features rather than trivially copying the current price
- **Autoregressive signal dominates**: `price_rolling_mean_4w` (73%) and `price_lag_1w` (25%) account for nearly all RF feature importance — card prices exhibit strong momentum/mean-reversion, consistent with thin secondary market behavior
- **Tournament features provide marginal signal**: domain-level legend play/top8 rates contribute <0.1% to tree model importance. Card-level deck composition rates would improve this; domain-level is a proxy
