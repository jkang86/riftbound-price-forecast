# Riftbound Price Forecasting — Project Log

_Last updated: 2026-03-23_

---

## Phase 1 — Data Collection

### Original Plan
Scrape three sources:
1. **TCGIndex** (`tcgindex.io/riftbound`) — daily price history per card
2. **RiftboundData** (`riftbounddata.com`) — secondary price validation
3. **RiftboundStats** (`riftboundstats.com`) — tournament decklists and event results

Use `requests` + `BeautifulSoup` or `selenium` for JS-rendered pages.

### What Actually Happened

**RiftboundStats** — Easiest win. Discovered a full undocumented public REST API at `https://www.riftboundstats.com/api`. No scraping needed:
- `/api/cards` → 101 cards with metadata (name, type, rarity, domain, market_price, tcgplayer_product_id)
- `/api/events` → 194 tournaments
- `/api/decks` → 22,807 decks (capped at 5,000 for server respect)
- `/api/decks/{id}/cards` → per-deck card list

Wrote `src/scrapers/riftboundstats_scraper.py` using pure `requests` pagination. Hit a 502 error on the decks endpoint mid-scrape — fixed with exponential backoff retry (3s→6s→12s→24s).

**TCGIndex** — Built a Selenium + CDP network interception scraper (`src/scrapers/tcgindex_scraper.py`) with multi-strategy extraction (NextData JSON → network interception → DOM fallback). The scraper ran and returned data, but only captured a current-snapshot overview (`2026-03-18_overview.json`), not historical price series. This was a dead end for price history.

**RiftboundData** — Site was completely inaccessible (connection refused). Stubbed out in `src/scrapers/riftbounddata_scraper.py`. Not usable.

### Pivot: TCGPlayer as Price Source
Since TCGIndex couldn't deliver history and RiftboundData was down, pivoted to **TCGPlayer Infinite** as the price data source. The RiftboundStats cards API conveniently includes `tcgplayer_product_id` for each card, enabling a direct lookup.

Discovered that `https://infinite-api.tcgplayer.com/price/history/{product_id}/detailed?range=quarter` returns 3-day bucket price history (marketPrice, lowSalePrice, highSalePrice, quantitySold, transactionCount) per SKU. Access requires a valid browser session cookie passed via `TCGPLAYER_COOKIE` env var.

Wrote `src/scrapers/tcgplayer_scraper.py`. Cookie was obtained from browser dev tools and scraper was run manually by the user. Result: `data/raw/tcgplayer/2026-03-19_price_history.json`.

### Deliverables (actual)
| File | Notes |
|---|---|
| `data/raw/riftboundstats/2026-03-14_cards.json` | 101 cards with metadata |
| `data/raw/riftboundstats/2026-03-14_decks.json` | ~5,000 decks (capped) |
| `data/raw/riftboundstats/2026-03-14_events.json` | 194 events |
| `data/raw/riftboundstats/2026-03-14_deck_cards.json` | Per-deck card lists |
| `data/raw/riftboundstats/2026-03-18_cards_full.json` | Full card catalog re-pull |
| `data/raw/riftboundstats/2026-03-18_legend_cards.json` | Legend-only cards for domain mapping |
| `data/raw/tcgindex/2026-03-18_overview.json` | Snapshot only — not used in pipeline |
| `data/raw/tcgplayer/2026-03-19_price_history.json` | **Primary price source** — 3-day buckets per card |

### Changes from Original Plan
| Original | Actual |
|---|---|
| TCGIndex as price source | Dropped — JS-rendered, only snapshot available |
| RiftboundData as secondary validation | Dropped — site inaccessible |
| Selenium-heavy scraping | Mostly unnecessary; REST API for tournament data |
| `data/raw/tcgindex/` and `data/raw/riftbounddata/` | Replaced by `data/raw/tcgplayer/` |

---

## Phase 2 — Cleaning & Merging

### Original Plan
- `cleaner.py`: standardize names, parse prices, normalize dates, deduplicate on `(card_name, source, date)`
- `merger.py`: join TCGIndex + RiftboundData prices on `card_name + date`, then join RiftboundStats tournament data on `card_name + week`
- Output: `data/processed/master.csv` — one row per `(card_name, week)`

### What Actually Happened

**Cleaner (`src/processing/cleaner.py`):**
- Reads `data/raw/tcgplayer/*_price_history.json`
- Flattens nested bucket arrays into rows keyed by `(card_name, product_id, bucket_date)`
- Derives `week` by flooring each bucket_date to Monday of its ISO week
- Aggregates to weekly: mean market/low/high price, sum qty_sold + transaction_count
- Drops buckets with `market_price == 0` (no sales activity)
- Outputs `data/processed/prices_clean.csv`

**Tournament processor (`src/processing/tournament.py`)** — new file, not in original plan:
- The original plan assumed card-level play rates from deck card lists (`/api/decks/{id}/cards`)
- In practice, deck card compositions were noisy and unreliable for computing per-card rates
- Pivoted to **Option B**: compute per-legend-per-week play/top8 rates from deck metadata alone
- Legend names are mapped to domains using the `legend_cards` catalog (short-name normalization: strips champion prefix, e.g. `"Draven, Glorious Executioner"` → `"Glorious Executioner"`)
- Multi-domain legends (e.g. `"Fury|Chaos"`) are exploded so their play pressure is attributed to both domains
- When multiple legends share a domain in a week, we take the MAX rate (peak competitive pressure)
- Outputs `data/processed/tournament_features.csv` — columns: `domain, week, legend_play_rate, legend_top8_rate`

**Merger (`src/processing/merger.py`):**
- Left joins `prices_clean.csv` with `tournament_features.csv` on `(domain, week)`
- Tournament metrics fill to 0 where a domain has no recorded play that week (absence = archetype inactive)
- Output: `data/processed/master.csv`

**master.csv stats:**
- Shape: 1,036 rows × 16 columns
- Cards: varies by week coverage from TCGPlayer data
- Week range: 2025-12-15 to present (~13 weeks of price data from `range=quarter`)
- No nulls on price columns; tournament columns default to 0.0 for inactive weeks

### Changes from Original Plan
| Original | Actual |
|---|---|
| Deduplicate on `(card_name, source, date)` | Single source (TCGPlayer), dedup happens in weekly aggregation |
| Join two price sources on `card_name + date` | No secondary price source; direct weekly aggregation from one source |
| Join RiftboundStats on `card_name + week` | Joined on `domain + week` (card-level play rates not available; using legend/domain proxy) |
| `tournament_play_rate` / `tournament_top8_rate` per card | `legend_play_rate` / `legend_top8_rate` per domain — card inherits its domain's competitive pressure |
| New files: none | Added `src/processing/tournament.py` — domain-level tournament processor |

---

## Phase 2.5 — SQL Database Layer

**Status: COMPLETE** _(added between Phase 2 and Phase 3 to demonstrate SQL skills)_

### What Was Added

A SQLite database (`data/riftbound.db`) that serves as a queryable store of all raw + processed data, decoupled from the CSV pipeline.

**New module: `src/database/`**

| File | Purpose |
|---|---|
| `schema.py` | DDL — 4 tables: `cards`, `price_history`, `events`, `decks`. Indexes on card_name, week, product_id, legend, event_date. |
| `loader.py` | Idempotent ETL — reads raw JSON files and bulk-inserts via `INSERT OR IGNORE / INSERT OR REPLACE`. Handles the `_cards_full.json` having stray string entries at EOF (API error artifact). |
| `queries.py` | 6 analytical queries demonstrating: `LAG`, `RANK`, `AVG OVER (ROWS BETWEEN)`, CTEs, multi-table `JOIN`, `HAVING`, conditional `CASE` aggregation. |

**Runner: `run_db.py`** — `python run_db.py` creates schema → loads all data → runs all queries. Flags: `--load` (skip queries), `--query` (skip load).

**`config.py`** — added `DB_PATH = DATA_DIR / "riftbound.db"`.

### DB Stats (as of 2026-03-23)
- `cards`: 100 rows (102 in file; 2 trailing error strings filtered)
- `price_history`: 2,260 rows (3-day buckets, 100 cards, ~14 weeks)
- `events`: 50 rows
- `decks`: 2,000 rows

### Queries implemented
| # | Query | SQL features |
|---|---|---|
| 1 | Weekly price trend per card | `LAG` window, CTE |
| 2 | Most volatile cards by price stddev | stddev via `SQRT(AVG(x²) - AVG(x)²)`, `RANK`, `HAVING` |
| 3 | Top 5 legends per week by meta share + Top8 conversion | Multi-CTE, `RANK OVER PARTITION`, `CASE` |
| 4 | Biggest weekly price movers with card metadata | Two-stage CTE (LAG then RANK), `JOIN cards` |
| 5 | Tournament size trend with 4-event rolling average | `AVG OVER (ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)` |
| 6 | Price summary by rarity tier | Conditional `CASE` aggregation, `JOIN`, `GROUP BY` |

### Relationship to pipeline
The DB is additive — the CSV pipeline (`cleaner.py`, `merger.py`) is unchanged. The DB is an independent, queryable layer that recruiters can explore separately from the ML pipeline.

---

## Phase 3 — Feature Engineering

**Status: COMPLETE**

### Original Plan
Build `src/features/engineer.py` producing `data/processed/features.csv` with:

| Feature | Notes |
|---|---|
| `rarity_tier` | Ordinal: Common=1 … Legendary=5 |
| `card_type` | One-hot: unit, spell, landmark, equipment |
| `champion_affiliation` | One-hot or target-encode by avg price |
| `tournament_play_rate` | % of decks containing card (per week) |
| `tournament_top8_rate` | % of Top 8 decks containing card |
| `set_release_flag` | Binary: 1 within ±2 weeks of a set release date |
| `days_since_release` | Numeric from card release date |
| `price_lag_1w` | Price 1 week prior |
| `price_lag_2w` | Price 2 weeks prior |
| `price_rolling_mean_4w` | 4-week rolling average |
| `price_pct_change_1w` | Week-over-week % change |

Target: `price_next_week` (shift market_price forward 1 week per card)

### What Actually Happened

**`src/features/engineer.py`** — all features implemented as planned, with the following deviations:

| Original | Actual |
|---|---|
| `rarity_tier`: 5 tiers (Common→Legendary) | 6 values in data; added Showcase=5, Promo=3. Tier map moved to `config.RARITY_TIER`. |
| `card_type`: 4 types (unit, spell, landmark, equipment) | 8 types in data (Unit, Champion Unit, Spell, Basic Rune, Legend, Gear, Battlefield, Signature Spell). All one-hotted. |
| `champion_affiliation`: one-hot or target-encode | Replaced by `domain_primary_*` one-hot (7 single domains; pipe-split multi-domain cards use their first domain). |
| `tournament_play_rate` / `tournament_top8_rate` | Direct rename of `legend_play_rate` / `legend_top8_rate` from master.csv. |
| `days_since_release` using card release date | Replaced by `days_since_first_sale` — days from card's earliest observed price row. Card `created_at` in API reflects DB ingestion date, not actual release. |
| Set release dates: Origins only in config | Added Proving Grounds (2025-08-01, estimated) and Spiritforged (2026-01-20, inferred from first price data at 2026-01-26). |

**features.csv stats (2026-03-23):**
- Shape: 802 rows × 28 columns
- Cards: 78 | Weeks: up to 11 per card (after dropping 2 lag rows + 1 target row per card)
- Zero nulls
- Columns: card_name, week, market_price, rarity_tier, days_since_first_sale, set_release_flag, tournament_play_rate, tournament_top8_rate, price_lag_1w, price_lag_2w, price_rolling_mean_4w, price_pct_change_1w, type_* (8), domain_primary_* (7), price_next_week

---

## Phase 4 — Model Training & Comparison

**Status: COMPLETE**

### Changes from Original Plan

| Original | Actual |
|---|---|
| `ts_test_weeks=8` | Reduced to `3` — data window is only 11 weeks; 8 test weeks left only 3 for training |
| ARIMA auto-select via AIC (statsmodels) | Grid search over p∈{0,1,2}, d∈{0,1}, q∈{0,1,2} — trivial (0,0,0) excluded |
| ARIMA/Prophet predict per-card market_price | Predicts `price_next_week` directly — aligns with cross-sectional target, avoids 1-week offset |
| All 78 cards fitted for ARIMA/Prophet | 52/100 products fitted (48 skipped: < 6 rows after split) |
| Bug fix: engineer.py grouped by `card_name` | Fixed to group by `product_id` — multi-rarity cards (Ahri Rare vs Showcase) are separate series |

### Results (test set: 3 weeks, 299 rows)

| Model | RMSE | MAE | R² |
|---|---|---|---|
| Prophet | 2.5579 | 2.3738 | 0.9976 |
| ARIMA | 2.6707 | 2.2906 | 0.9952 |
| Ridge | 13.1963 | 2.8611 | 0.9981 |
| Lasso | 28.4729 | 5.4488 | 0.9911 |
| XGBoost | 198.3830 | 28.6794 | 0.5681 |
| Random Forest | 237.5485 | 32.4439 | 0.3807 |

Note: ARIMA/Prophet RMSE is lower because they operate on a filtered subset of 52 products with ≥6 weeks of data (skipping the high-volatility Showcase cards with short histories that inflate RMSE for the cross-sectional models).

Top feature (RF + XGB): `market_price` (~41–83% importance), confirming strong autoregressive signal. Price lags and rolling mean account for most of the remainder.

### New files
- `src/models/utils.py` — shared split, feature columns, log transform, metrics
- `src/models/linear.py` — Ridge + Lasso (GridSearchCV + StandardScaler)
- `src/models/tree.py` — Random Forest + XGBoost (with early stopping CV)
- `src/models/timeseries.py` — ARIMA + Prophet (per-product, price_next_week target)
- `src/models/compare.py` — orchestrator + all 4 export writers
- `run_phase4.py` — entry point (`--linear` / `--tree` / `--ts` flags)
- `outputs/figures/feature_importance_randomforest.png`
- `outputs/figures/feature_importance_xgboost.png`

### Exports written
- `data/exports/model_comparison.csv` — 6 models, ranked by RMSE
- `data/exports/prices.csv` — 4,040 rows (94 cards × 6 models × train+test predictions)
- `data/exports/features.csv` — 736 rows × 17 cols (dashboard-ready, one-hots dropped)
- `data/exports/top_movers.csv` — 736 rows with direction labels

---

## Phase 5 — Streamlit Dashboard

**Status: COMPLETE** _(local — deployment pending)_

### What Was Built

Multi-page Streamlit app running at `streamlit run src/dashboard/app.py`. All 5 pages render with real data.

**Theme:** Riftbound gold `#C89B3C` on dark navy `#0A1428` (`.streamlit/config.toml`)

**Files added:**
| File | Purpose |
|---|---|
| `src/dashboard/utils.py` | 5 `@st.cache_data` loaders: prices, features, model_comparison, top_movers, feature_importances |
| `src/dashboard/app.py` | Landing page — KPI metrics row (cards tracked, best RMSE, top mover, avg predicted Δ), data freshness caption |
| `src/dashboard/pages/1_📈_Price_Forecast.py` | Sidebar: card selectbox, model multiselect, week range slider. Chart: actual vs predicted per model. Metrics: RMSE/MAE/R² per model. |
| `src/dashboard/pages/2_🏆_Model_Leaderboard.py` | Grouped bar chart (RMSE/MAE/R²), styled table (best=green, worst=red), CSV download button |
| `src/dashboard/pages/3_🔍_Card_Explorer.py` | Metadata row, dual-axis price + play rate chart, price stats table |
| `src/dashboard/pages/4_🔥_Top_Movers.py` | Sidebar: week, direction, top-N. Horizontal bar chart + styled dataframe. |
| `src/dashboard/pages/5_📊_Feature_Analysis.py` | Correlation heatmap, XGBoost + RF feature importances side-by-side, play rate vs price scatter |
| `src/dashboard/components/price_chart.py` | Plotly dual line chart + test region shading |
| `src/dashboard/components/model_leaderboard.py` | Plotly grouped bar chart |
| `src/dashboard/components/feature_importance.py` | Plotly horizontal bar from feature_importances.csv |
| `src/dashboard/components/top_movers.py` | Plotly horizontal bar (green/red by direction) |
| `src/dashboard/components/card_explorer.py` | Plotly dual-axis: price line + play rate bars |

### Changes from Original Plan
| Original | Actual |
|---|---|
| Default card: "Blind Monk" | Changed to "Acceptable Losses" — "Blind Monk" stored as "Blind Monk (Rare)"/"Blind Monk (Showcase)" due to multi-rarity `card_display` format |
| `load_feature_importances()` not in original utils spec | Added — required by Feature Analysis page |
| `data/exports/feature_importances.csv` not in original export spec | Added in compare.py — 50 rows (25 features × 2 models) |
| Features.csv: full 30-col one-hot set | Dashboard-facing features.csv is 17-col (one-hots dropped; dashboard only needs raw metadata + key numeric features) |

### Known Limitation
11 weeks of price history → tree models (RF/XGB) show `market_price` dominating feature importance (~41–83%). Re-scraping TCGPlayer with `range=year` will give ~52 weeks, allowing contextual features (play rate, rarity, set release) to show signal. Planned post-Phase-5 task.

### Next Step
Deploy to Streamlit Community Cloud:
1. Push repo to GitHub (public)
2. Connect at share.streamlit.io → main file: `src/dashboard/app.py`
3. Add live URL badge to README.md
