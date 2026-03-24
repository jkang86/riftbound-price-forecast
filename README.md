# Riftbound Card Price Forecasting Model

A data analytics portfolio project that scrapes card price and tournament data for the Riftbound TCG, engineers features, and trains multiple forecasting models to predict weekly card price movement. Framed as a financial/sports analytics crossover — think stock market meets competitive gaming.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live_Dashboard-FF4B4B?logo=streamlit)](https://riftbound-price-forecast.streamlit.app)
[![XGBoost](https://img.shields.io/badge/XGBoost-Model-orange)](https://xgboost.readthedocs.io)
[![Prophet](https://img.shields.io/badge/Prophet-Time--Series-blue)](https://facebook.github.io/prophet/)

**[Live Dashboard →](https://riftbound-price-forecast.streamlit.app)**

---

## What This Project Does

1. **Scrapes** card price history from TCGPlayer Infinite API and tournament data from RiftboundStats REST API
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

## Model Results (test set: 3 weeks)

| Model | RMSE | MAE | R² |
|---|---|---|---|
| **Prophet** | $2.56 | $2.37 | 0.9976 |
| **ARIMA** | $2.67 | $2.29 | 0.9952 |
| Ridge | $13.20 | $2.86 | 0.9981 |
| Lasso | $28.47 | $5.45 | 0.9911 |
| XGBoost | $198.38 | $28.68 | 0.5681 |
| Random Forest | $237.55 | $32.44 | 0.3807 |

> ARIMA/Prophet operate on the 52 products with ≥6 weeks of history. Tree models are evaluated across all 100 products including high-volatility short-series cards.

---

## Tech Stack

- **Data collection:** `requests`, `BeautifulSoup`, `selenium` (TCGPlayer Infinite API, RiftboundStats REST API)
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
# Phase 1 — Scrape RiftboundStats
python run_phase1.py --riftboundstats

# Phase 1 — Scrape TCGPlayer (requires TCGPLAYER_COOKIE env var)
export TCGPLAYER_COOKIE="your_browser_cookie_here"
python run_phase1.py --tcgindex

# Phase 2.5 — Load SQLite database
python run_db.py

# Phase 4 — Train all models and export CSVs
python run_phase4.py
```

---

## Key Findings

- **Time-series models win** for short-window data: Prophet (RMSE $2.56) and ARIMA (RMSE $2.67) outperform all cross-sectional models by a large margin on a per-card basis
- **Ridge beats tree models** ($13.20 vs $198–237) — with only 11 weeks of data and a strong autoregressive price signal, regularized linear regression generalizes far better than trees
- **Top feature: `market_price` itself** (~41–83% importance in RF/XGB) — confirms strong mean-reversion / momentum signal in card prices; contextual features (play rate, rarity) will gain signal with longer price history
- **Tournament play rate proxy**: card-level play rates are unavailable without deck card composition data; legend/domain-level rates are used as a proxy — re-scraping with deck compositions would improve signal
