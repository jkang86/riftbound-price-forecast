# docs/plan.md — Riftbound Market Intelligence Platform

## PROJECT GOAL

Build a production-grade collectible market intelligence platform for Riftbound
(League of Legends TCG) that demonstrates ML forecasting, data engineering,
frontend engineering, and UX systems thinking — targeted at data analytics
and data science recruiters.

---

## PROGRESS LEGEND

```
[ ] — not started
[~] — in progress
[x] — complete
[!] — blocked
```

---

## DATA PIPELINE ARCHITECTURE

### Overview

```
TCGPlayer Internal API
  → (weekly via GitHub Actions cron)
pipeline/scraper.py          → fetch price history per card ID
  →
pipeline/model.py            → run Prophet per card, generate 30d forecast
  →
pipeline/export.py           → serialize to /public/data/*.json
  →
git commit + push to main    → triggers Vercel auto-deploy
  →
React app fetches /data/*.json at runtime (no backend needed)
```

### Files Produced

| File | Contents | Updated |
|---|---|---|
| `public/data/cards.json` | Full card catalog, current prices, sparklines, signals | Weekly |
| `public/data/forecasts.json` | Per-card Prophet output: history, yhat, confidence bands, metrics | Weekly |
| `public/data/market.json` | Market-level aggregates: cap, volume, volatility, rarity distribution | Weekly |
| `public/data/meta.json` | Deck inclusion rates, top-played cards, faction breakdown | Weekly |

### Signal Logic (export.py)

```python
def compute_signal(delta_7d, delta_30d, forecast_slope):
    if delta_7d > 15 and forecast_slope > 0:  return "STRONG BUY"
    if delta_7d > 5  and forecast_slope > 0:  return "BUY"
    if delta_7d < -10:                         return "SELL"
    if abs(delta_7d) < 3:                      return "HOLD"
    return "WATCH"
```

### GitHub Actions Workflow

```yaml
# .github/workflows/weekly-update.yml
name: Weekly Market Update
on:
  schedule:
    - cron: '0 3 * * 0'   # Every Sunday 03:00 UTC
  workflow_dispatch:        # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r pipeline/requirements.txt
      - run: python pipeline/scraper.py
        env:
          TCGPLAYER_TOKEN: ${{ secrets.TCGPLAYER_TOKEN }}
      - run: python pipeline/model.py
      - run: python pipeline/export.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: 'data(pipeline): weekly market update'
          file_pattern: 'public/data/*.json'
```

### React Data Layer

```js
// src/hooks/useMarketData.js
export function useMarketData() {
  const [data, setData] = useState(null);
  useEffect(() => {
    Promise.all([
      fetch('/data/cards.json').then(r => r.json()),
      fetch('/data/market.json').then(r => r.json()),
    ]).then(([cards, market]) => setData({ cards, market }));
  }, []);
  return data;
}
```

---

## JS / REACT ARCHITECTURE

### Router
React Router v6, hash-based (`createHashRouter`) for GitHub Pages compatibility.

```
#/          → Landing
#/dashboard → Dashboard
#/cards     → Explorer
#/cards/:id → Detail
#/models    → Models
#/meta      → MetaTracker
```

### State Management
No Redux. Local state via `useState` + `useReducer` for filter state.
Data fetched once at hook level, passed via props. No context needed at current scale.

### Key Hooks

| Hook | Purpose |
|---|---|
| `useMarketData()` | Fetches cards.json + market.json, memoizes |
| `useCardForecast(id)` | Fetches forecasts.json, returns single card forecast |
| `useMetaData()` | Fetches meta.json |
| `useIntersect(ref, opts)` | IntersectionObserver wrapper for scroll animations |
| `useReducedMotion()` | Reads `prefers-reduced-motion` |

### Component Hierarchy

```
App (router)
└── Layout (nav, ticker, footer)
    ├── Landing
    │   ├── HeroSection
    │   │   ├── ScoreBugRow
    │   │   └── LowerThird (featured card)
    │   ├── FeaturedPrediction (ConfidenceBand)
    │   ├── TopMovers (3-col grid of MarketCard)
    │   └── MarketSentiment
    ├── Dashboard
    │   ├── BroadcastTicker
    │   ├── MarketOverviewChart
    │   ├── ScoreBugStack
    │   ├── TopMoversGrid
    │   └── VolatilityHeatmap
    ├── Explorer
    │   ├── FilterSidebar
    │   │   ├── FactionFilter
    │   │   ├── RarityFilter
    │   │   ├── SignalFilter
    │   │   └── PriceRangeSlider
    │   └── CardGrid → MarketCard[]
    ├── Detail
    │   ├── LowerThirdHero
    │   ├── ConfidenceBand (full chart)
    │   ├── ScoreBugStack
    │   └── RelatedCards
    ├── Models
    │   ├── ModelComparisonTable
    │   ├── MetricBars (RMSE, MAE, R²)
    │   ├── ConfidenceDistribution
    │   └── FeatureImportance
    └── MetaTracker
        ├── TopDecksTable
        ├── TopPlayedCards
        ├── InclusionTrendSparklines
        └── FactionHeatmap
```

---

## DEVELOPMENT PHASES

---

## PHASE 0 — VITE MIGRATION

Status: [x]
Git tag: `v0.1.0-vite`
Branch: `feat/phase0-vite-migration`

**Goal:** Retire the Streamlit app, migrate from bundleless HTML to Vite + npm,
and wire up Vercel as the sole deployment target.

### Context — Streamlit → Vercel
The original forecasting tool lived at `riftbound-price-forecast.streamlit.app`.
That app is being **retired and replaced** by this React platform. The Python
pipeline (scraper → Prophet → JSON export) is preserved and adapted; only the
Streamlit UI layer is dropped. Vercel serves the React build statically — no
Python server required at runtime.

### Tasks

#### Streamlit Retirement
- [x] Archive the Streamlit app (add deprecation notice to streamlit `app.py`)
- [ ] Confirm `riftbound-price-forecast.streamlit.app` can be taken offline after launch
- [ ] Migrate any pipeline code from `app.py` into `pipeline/model.py` and `pipeline/export.py`
- [x] Preserve all existing Prophet model logic — do not rewrite, just relocate
- [ ] Update repo README to point to new Vercel URL instead of Streamlit URL

#### Vite Setup
- [x] `npm create vite@latest . -- --template react`
- [x] Install dependencies: `tailwindcss`, `framer-motion`, `recharts`, `react-router-dom`, `d3`
- [x] Configure `tailwind.config.js` with full token set (see design.md)
- [x] Configure `vite.config.js` — base path `/` (Vercel handles routing natively)
- [x] Add `vercel.json` for SPA rewrite rule (see below)
- [ ] Port `src/data.jsx` — static fallback JSON at `src/data/fallback.json`
- [ ] Port all existing `.jsx` files into `src/pages/`
- [ ] Port `src/primitives.jsx` — `src/components/` (split per component)
- [ ] Port `src/layout.jsx` — `src/components/Layout.jsx`
- [x] Set up hash router with all 6 routes (including `/meta`)
- [x] Verify `npm run build` produces clean dist/
- [x] Verify `npm run dev` hot-reloads correctly

#### Vercel Config
```json
// vercel.json — SPA fallback so all routes serve index.html
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### Decisions
- **Vercel is the only deployment target** — GitHub Pages is no longer used
- Use `createHashRouter` (still preferred) — works on Vercel and avoids 404 on deep links without needing server rewrites
- Tailwind JIT mode (default in v3) — no purge config needed
- Keep D3 lazy-imported to avoid bundle bloat on non-chart pages
- Streamlit app stays archived but accessible until Vercel URL is confirmed stable

### Git Commit Message
```
feat(phase0): retire streamlit, migrate to Vite 5 + Vercel, hash router
```

---

## PHASE 1 — DATA PIPELINE

Status: [ ]
Git tag: `v0.2.0-pipeline`
Branch: `feat/phase1-data-pipeline`

**Goal:** Real TCGPlayer price data flowing to `/public/data/*.json`.

### Tasks

#### Scraper (pipeline/scraper.py)
- [ ] Reverse-engineer TCGPlayer internal API endpoint for Riftbound category
- [ ] Implement card ID list fetch (all Riftbound cards)
- [ ] Implement price history fetch per card (90-day window)
- [ ] Add retry logic with exponential backoff
- [ ] Add rate limiting (0.5s between requests)
- [ ] Store raw responses to `pipeline/cache/` (avoid re-scraping)
- [ ] Output: `pipeline/output/raw_prices.csv`

#### Model (pipeline/model.py)
- [ ] Load `raw_prices.csv`
- [ ] Clean and impute missing price days
- [ ] Run Prophet per card: 30-day forecast, weekly seasonality
- [ ] Compute RMSE, MAE, R² on holdout last 14 days
- [ ] Compute signal via `compute_signal()` logic
- [ ] Output: `pipeline/output/forecasts.json`

#### Export (pipeline/export.py)
- [ ] Build `cards.json` — catalog + current prices + sparklines + signals
- [ ] Build `forecasts.json` — per-card history + forecast + metrics
- [ ] Build `market.json` — aggregates (cap, volume, volatility, rarity dist)
- [ ] Build `meta.json` — placeholder structure until meta data source added
- [ ] Copy all to `public/data/`

#### GitHub Actions
- [ ] Create `.github/workflows/weekly-update.yml`
- [ ] Add `TCGPLAYER_TOKEN` to repo secrets
- [ ] Test with `workflow_dispatch` before enabling schedule
- [ ] Verify Vercel auto-deploys on push to main

#### React Integration
- [ ] Implement `useMarketData()` hook
- [ ] Implement `useCardForecast(id)` hook
- [ ] Implement `useMetaData()` hook
- [ ] Add loading/skeleton states to all data-dependent components
- [ ] Add error boundaries with fallback to static data

### Decisions
- Keep `src/data/fallback.json` as static backup if pipeline fails
- Prophet runs per-card, not as a batch model — better per-card accuracy
- 90-day history minimum before forecasting (skip cards with < 90d data)

### Git Commit Message
```
data(phase1): add TCGPlayer scraper, Prophet model, GitHub Actions pipeline
```

---

## PHASE 2 — DESIGN SYSTEM

Status: [x]
Git tag: `v0.3.0-design-system`
Branch: `feat/phase2-design-system`

**Goal:** Build broadcast-style primitive component library.

### Tasks

#### Broadcast Primitives
- [x] `<ScoreBug />` — HUD stat block (label + value + delta)
- [x] `<ScoreBugRow />` — horizontal row of ScoreBugs
- [x] `<LowerThird />` — slide-up broadcast overlay
- [x] `<BroadcastTicker />` — infinite scroll market tape
- [x] `<LiveDot />` — pulsing red LIVE indicator
- [x] `<ScanLine />` — animated horizontal red scan line (hero bg effect)

#### Data Primitives
- [x] `<Rarity />` — pill badge (Mythic/Legend/Epic/Rare/Common)
- [x] `<Signal />` — BUY/SELL/HOLD/WATCH pill
- [x] `<Delta />` — ▲/▼ percentage with color
- [x] `<Sparkline />` — inline SVG mini chart
- [x] `<ConfidenceBand />` — Recharts ComposedChart with Prophet layers

#### UI Primitives
- [x] `<Button />` — variants: primary, ghost, destructive
- [x] `<MarketCard />` — full card component (art, name, price, signal, sparkline)
- [x] `<FilterPill />` — faction/rarity toggle pill
- [ ] `<PriceRangeSlider />` — dual-thumb slider (deferred to Phase 5 Explorer)
- [x] `<SkeletonCard />` — shimmer loading state
- [x] `<SkeletonChart />` — shimmer chart placeholder

#### Utilities
- [x] `useIntersect(ref, opts)` — IntersectionObserver hook
- [x] `useReducedMotion()` — prefers-reduced-motion hook
- [x] `useCountUp(target, duration)` — animated number count-up
- [x] `<PageTransition />` — Framer Motion page wrapper
- [x] `formatPrice(n)` — "$24.99" formatter
- [x] `formatDelta(n)` — "+8.2%" formatter
- [x] `raritySort(a, b)` — sort by rarity tier

### Git Commit Message
```
feat(phase2): add broadcast primitives and full design system component library
```

---

## PHASE 3 — LANDING PAGE

Status: [x]
Git tag: `v0.4.0-landing`
Branch: `feat/phase3-landing`

**Goal:** Cinematic hook — establish platform identity in < 3 seconds.

### Tasks
- [ ] Full-viewport hero with `<ScanLine />` bg effect
- [ ] Bebas Neue headline: "THE RIFTBOUND ECONOMY, LIVE"
- [ ] `<ScoreBugRow />` with live market stats
- [ ] `<LowerThird />` featuring top-signal card
- [ ] `<FeaturedPrediction />` — ConfidenceBand chart (the money shot)
- [ ] `<TopMovers />` — 3-col grid, staggered scroll reveal
- [ ] `<MarketSentiment />` — horizontal bar (bullish/bearish)
- [ ] Staggered mount animations (0ms → 100ms → 200ms delays)
- [ ] `<BroadcastTicker />` at page top (fixed position)
- [ ] CTA buttons to Dashboard and Explorer

### WOW Feature
The scan-line + score-bug row. The moment a recruiter hits the page it
should feel like turning on a broadcast, not opening a website.

### Git Commit Message
```
feat(phase3): landing page — broadcast hero, score-bug row, featured prediction
```

---

## PHASE 4 — DASHBOARD

Status: [x]
Git tag: `v0.5.0-dashboard`
Branch: `feat/phase4-dashboard`

**Goal:** Market overview — all key signals visible above the fold.

### Tasks
- [ ] `<BroadcastTicker />` fixed at top
- [ ] `<LiveDot />` in nav when dashboard is active
- [ ] 90-day market overview area chart (Recharts)
- [ ] Right-column score-bug stack (5 KPIs: cap, volume, gainers, losers, volatility)
- [ ] Top Movers 3-col grid (sorted by delta_7d_pct)
- [ ] Volatility heatmap (faction × rarity, D3 or Recharts)
- [ ] Rarity distribution donut chart
- [ ] Responsive: score-bug stack collapses below chart on mobile

### Git Commit Message
```
feat(phase4): dashboard — market overview, score-bug KPIs, top movers grid
```

---

## PHASE 5 — CARD EXPLORER

Status: [x]
Git tag: `v0.6.0-explorer`
Branch: `feat/phase5-explorer`

**Goal:** Interactive card search and discovery.

### Tasks
- [ ] Filter sidebar: faction pills, rarity checkboxes, signal filter, price range slider
- [ ] Search input with debounce (300ms)
- [ ] Card grid: 3-col desktop, 2-col tablet, 1-col mobile
- [ ] Sort controls: price ↕, delta ↕, name A-Z
- [ ] `<MarketCard />` grid rendering (virtualize if > 200 cards)
- [ ] Filter drawer on mobile (slide-in from left)
- [ ] Empty state with reset-filters CTA
- [ ] Active filter count badge on mobile filter button

### Git Commit Message
```
feat(phase5): card explorer — filter sidebar, search, responsive card grid
```

---

## PHASE 6 — CARD DETAIL

Status: [x]
Git tag: `v0.7.0-detail`
Branch: `feat/phase6-detail`

**Goal:** Full forecast presentation for a single card.

### Tasks
- [ ] `<LowerThirdHero />` — card name + faction + rarity (cinematic reveal)
- [ ] `<ConfidenceBand />` full chart — 90d history + 30d forecast + bands
- [ ] Chart toggle: history only / forecast only / combined
- [ ] Score-bug stack: current price, signal, forecast target, RMSE, R²
- [ ] Metrics explanation accordion (non-technical language)
- [ ] Related cards row (same faction, sorted by signal)
- [ ] Share button (copies URL to clipboard)

### Git Commit Message
```
feat(phase6): card detail — confidence band chart, score-bug metrics, related cards
```

---

## PHASE 7 — MODEL INTELLIGENCE

Status: [x]
Git tag: `v0.8.0-models`
Branch: `feat/phase7-models`

**Goal:** ML credibility — make the forecasting methodology legible.

### Tasks
- [ ] Model comparison table (Prophet vs naive baseline vs moving average)
- [ ] Per-metric horizontal bars: RMSE, MAE, R² — gold fill
- [ ] Confidence interval distribution chart (how wide are the bands?)
- [ ] Feature importance horizontal bars (seasonality, trend, recent vol)
- [ ] Forecast accuracy timeline (how has the model performed over time?)
- [ ] Plain-language explanations next to every metric
- [ ] Cards sorted by model confidence (highest R² first)

### Git Commit Message
```
feat(phase7): model intelligence — prophet metrics, comparison table, explainability
```

---

## PHASE 8 — META TRACKER

Status: [x]
Git tag: `v0.9.0-meta`
Branch: `feat/phase8-meta`

**Goal:** Deck-level market intelligence — top-played cards and deck trends.

### Tasks

#### Data Source Decision
- [ ] Evaluate Riftbound official tournament data availability
- [ ] Evaluate community-submitted deck data (r/Riftbound, Discord)
- [ ] If no API: build manual CSV upload flow for meta.json
- [ ] Document chosen approach in this file

#### UI
- [ ] Top decks table (name, win-rate, top-included cards)
- [ ] Top-played cards grid with inclusion % badge
- [ ] Inclusion trend sparklines (7d, 30d)
- [ ] Faction breakdown heatmap
- [ ] "Meta Impact" badge on MarketCard when card is in top deck
- [ ] Weekly meta snapshot with timestamp

### Git Commit Message
```
feat(phase8): meta tracker — deck trends, top-played cards, faction heatmap
```

---

## PHASE 9 — POLISH & IMMERSION

Status: [x]
Git tag: `v0.10.0-polish`
Branch: `feat/phase9-polish`

**Goal:** Riot-level motion and interaction polish.

### Tasks
- [ ] Page transitions: restrained fade + 8px translateY
- [ ] Staggered card grid reveals (IntersectionObserver, 50ms stagger)
- [ ] Chart progressive reveal (animate strokeDashoffset on line charts)
- [ ] Hover micro-interactions: card elevation + gold glow
- [ ] Skeleton → content transitions (opacity fade, no layout shift)
- [ ] BroadcastTicker smooth pause on hover
- [ ] ScoreBug number count-up animation on mount
- [ ] `prefers-reduced-motion` fallbacks for all animations
- [ ] Nav active indicator slide (2px underline, translateX transition)
- [ ] Focus ring polish: `ring-2 ring-rift-gold` on all interactive elements

### Git Commit Message
```
feat(phase9): motion polish — page transitions, staggered reveals, micro-interactions
```

---

## PHASE 10 — PERFORMANCE & ACCESSIBILITY

Status: [x]
Git tag: `v0.11.0-perf`
Branch: `feat/phase10-perf`

### Targets
- Lighthouse Performance ≥ 85
- Lighthouse Accessibility ≥ 95
- LCP < 2.5s
- CLS < 0.1

### Tasks
- [ ] Audit and fix all missing `aria-label` attributes
- [ ] Add `aria-live="polite"` to BroadcastTicker
- [ ] Semantic HTML audit: `<nav>`, `<main>`, `<section aria-label>`, `<article>`
- [ ] Keyboard navigation test: tab order, Esc closes drawers
- [ ] Image: add `width`/`height` to all `<img>` to prevent CLS
- [ ] Lazy-load below-fold charts with `React.lazy` + `Suspense`
- [ ] Code-split per route (Vite handles automatically with dynamic import)
- [ ] Font display: `font-display: swap` in Google Fonts URL
- [ ] Bundle analysis: `npx vite-bundle-visualizer`
- [ ] Remove unused D3 imports (import only needed submodules)

### Git Commit Message
```
feat(phase10): perf + a11y — lighthouse targets, semantic html, lazy loading
```

---

## PHASE 11 — DEPLOYMENT (VERCEL)

Status: [ ]
Git tag: `v1.0.0`
Branch: `main`

**Replacing:** `riftbound-price-forecast.streamlit.app`
**New URL:** `riftbound.vercel.app` (or custom domain)

### Vercel Project Setup
- [ ] Create Vercel account / confirm existing account at vercel.com
- [ ] Import GitHub repo `jkang84/riftbound-price-forecast` from Vercel dashboard
- [ ] Framework preset: **Vite** (auto-detected)
- [ ] Build command: `npm run build`
- [ ] Output directory: `dist`
- [ ] Install command: `npm install`
- [ ] Confirm `vercel.json` SPA rewrite is present (see Phase 0)
- [ ] Set environment variable in Vercel dashboard:
  - `VITE_DATA_BASE_URL` = `/data` (or absolute URL if serving from CDN)
- [ ] Trigger first manual deploy — confirm green build

### Domain & Identity
- [ ] Confirm Vercel subdomain: `riftbound-forecast.vercel.app` (or rename project)
- [ ] Optional: add custom domain in Vercel → Settings → Domains
- [ ] Update portfolio site link to new Vercel URL
- [ ] Update GitHub repo description + README with new URL
- [ ] **Take Streamlit app offline** (or leave archived — your call)

### Metadata & SEO
- [ ] OpenGraph tags on every page:
  - `og:title` — "Riftbound Market Intelligence"
  - `og:description` — "Live price forecasting and market analytics for Riftbound TCG"
  - `og:image` — 1200×630px screenshot of landing hero
  - `og:url` — Vercel URL
- [ ] Twitter card meta tags
- [ ] `<title>` tag per page (not just index.html)
- [ ] Favicon system: SVG favicon + 192px + 512px PNG (use Riftbound red/gold mark)
- [ ] `robots.txt` — allow all
- [ ] `sitemap.xml` — list all 6 routes

### GitHub Actions — Vercel Integration
- [ ] Confirm GitHub Actions pipeline pushes to `main`
- [ ] Verify Vercel auto-deploys within 60s of push
- [ ] Add Vercel deploy status badge to README
- [ ] Add pipeline run badge to README

### QA Checklist
- [ ] Mobile QA: iPhone Safari (375px), Android Chrome (360px)
- [ ] Tablet QA: iPad (768px)
- [ ] Desktop QA: 1280px, 1440px, 1920px
- [ ] Cross-browser: Chrome, Firefox, Safari, Edge
- [ ] Hash routing: deep link to `/cards/jinx-loose-cannon` — verify loads correctly
- [ ] Ticker pause on hover
- [ ] All 6 nav routes reachable from landing
- [ ] Pipeline JSON loads (check Network tab — no 404s on `/data/*.json`)
- [ ] Lighthouse audit: Performance ≥ 85, Accessibility ≥ 95

### Analytics
- [ ] Enable Vercel Analytics (free tier, privacy-friendly, no cookie banner needed)

### Git Commit Message
```
chore(deploy): production launch on Vercel — retire Streamlit, OG tags, favicon, analytics
```

---

## GIT VERSION HISTORY

_Updated as phases complete. Format: `vX.Y.Z — description — YYYY-MM-DD`_

| Version | Description | Date | Status |
|---|---|---|---|
| `v0.0.1` | Initial Python pipeline + Streamlit dashboard | — | shipped |
| `v0.1.0` | Vite migration + Streamlit retirement | 2026-05-25 | shipped |
| `v0.2.0` | TCGPlayer pipeline + Prophet | — | pending |
| `v0.3.0` | Design system + broadcast primitives | 2026-05-25 | shipped |
| `v0.4.0` | Landing page | 2026-05-25 | shipped |
| `v0.5.0` | Dashboard | 2026-05-25 | shipped |
| `v0.6.0` | Card Explorer | 2026-05-25 | shipped |
| `v0.7.0` | Card Detail | 2026-05-25 | shipped |
| `v0.8.0` | Model Intelligence | 2026-05-25 | shipped |
| `v0.9.0` | Meta Tracker | 2026-05-25 | shipped |
| `v0.10.0` | Polish & immersion | 2026-05-25 | shipped |
| `v0.11.0` | Performance & accessibility | 2026-05-25 | shipped |
| `v1.0.0` | Production launch on Vercel | — | pending |

---

## OPEN DECISIONS

| Decision | Options | Status |
|---|---|---|
| Meta data source | Tournament API vs community CSV | [ ] unresolved |
| Card art | Riot official assets vs placeholder | [ ] unresolved |
| Auth for TCGPlayer API | Rotate token via secret or use public endpoints | [ ] unresolved |
| TypeScript migration | Add TS in Phase 2 or stay JSX | [ ] unresolved |

---

## CURRENT FOCUS

**Active phase:** Phase 11 — Deployment (Vercel)
**Next unblocked task:** Import GitHub repo into Vercel, confirm build command `npm run build`, output `dist`, verify SPA rewrite, set VITE_DATA_BASE_URL=/data, trigger first deploy
**Blocked by:** User must complete Vercel account setup and GitHub import (manual step)

_Update this section at the start of every session._
