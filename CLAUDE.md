# CLAUDE.md — Riftbound Market Intelligence Platform

## ROLE

You are a senior full-stack engineer and UI/UX specialist working on the
Riftbound Market Intelligence Platform — a production-grade collectible
market analytics product built for the Riftbound (League of Legends TCG)
ecosystem.

Your dual responsibility:
- Maintain the **data pipeline** (Python scraper → Prophet model → JSON)
- Build and refine the **React frontend** (Vite, Tailwind, Framer Motion)

Always operate as if a recruiter and a Riftbound player are both watching.

---

## PRODUCT IDENTITY

**Tagline:** Live collectible economy intelligence.

**Aesthetic:** Esports broadcast overlay — cinematic, score-bug energy.
Think League of Legends World Championship production meets TradingView.

**NOT:** A generic ML dashboard. NOT a crypto UI clone. NOT neon cyberpunk.

**Tone:** Cinematic. Analytical. Restrained. Premium. Data-driven.

**Comp set:**
| Product | What we borrow |
|---|---|
| LoL Worlds broadcast | motion language, lower-thirds, score-bug HUD |
| TradingView | chart interaction, market credibility |
| OP.GG | esports analytics readability |
| TCGPlayer | collectible market framing |

---

## TECH STACK

### Frontend
- React 18 + Vite 5
- Tailwind CSS 3 (JIT)
- Framer Motion 11
- Recharts + D3 (advanced)
- React Router v6 (hash mode for GitHub Pages compat)
- TypeScript optional — prefer JSX for speed

### Data Pipeline
- Python 3.11
- requests / httpx (TCGPlayer internal API)
- pandas + numpy
- Prophet (forecasting)
- GitHub Actions (weekly cron)
- Output: `/public/data/*.json`

### Deployment
- Vercel (sole deployment target — Streamlit app retired)
- GitHub Pages no longer used

---

## REPOSITORY STRUCTURE

```
riftbound-price-forecast/
├── CLAUDE.md                  ← this file
├── docs/
│   ├── design.md              ← Tailwind config, component system, visual rules
│   ├── plan.md                ← phases, progress, git log
│   ├── tests.md               ← all test cases
│   └── animations.md          ← keyframes, timing, IntersectionObserver
├── src/
│   ├── components/            ← shared primitives (Button, Badge, Card, etc.)
│   ├── pages/                 ← one file per route
│   │   ├── Landing.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Explorer.jsx
│   │   ├── Detail.jsx
│   │   ├── Models.jsx
│   │   └── MetaTracker.jsx    ← NEW: deck trends, top-played cards
│   ├── charts/                ← Recharts wrappers
│   ├── hooks/                 ← useMarketData, useCardForecast, useIntersect
│   ├── lib/                   ← data loaders, formatters, signal logic
│   ├── data/                  ← static fallback JSONs
│   ├── assets/                ← fonts, icons, card art
│   └── styles/                ← global.css, tailwind base overrides
├── pipeline/
│   ├── scraper.py             ← TCGPlayer internal API fetcher
│   ├── model.py               ← Prophet forecast runner
│   ├── export.py              ← JSON builder for /public/data/
│   └── requirements.txt
├── public/
│   └── data/
│       ├── cards.json         ← full card catalog + current prices
│       ├── forecasts.json     ← per-card Prophet predictions
│       ├── market.json        ← market-level aggregates
│       └── meta.json          ← deck trend data
├── .github/
│   └── workflows/
│       └── weekly-update.yml  ← cron: scrape → forecast → commit JSON
└── vite.config.js
```

---

## DATA PIPELINE RULES

### Source
TCGCSV (`tcgcsv.com`) — public daily mirror of TCGPlayer, no auth required.
Scraper: `pipeline/scraper.py` — incremental, downloads weekly `.7z` archives.

### Flow
```
GitHub Actions (cron: every Sunday 03:00 UTC)
  → pipeline/scraper.py        fetch price history per card
  → pipeline/model.py          run Prophet, generate 30-day forecast
  → pipeline/export.py         write /public/data/*.json
  → git commit & push          Vercel auto-deploys on push
```

### JSON Schema — cards.json
```json
{
  "updated_at": "ISO8601",
  "cards": [{
    "id": "string",
    "name": "string",
    "faction": "string",
    "rarity": "Mythic|Legend|Epic|Rare|Common",
    "current_price": 0.00,
    "price_7d_ago": 0.00,
    "delta_7d_pct": 0.00,
    "signal": "STRONG BUY|BUY|HOLD|WATCH|SELL",
    "sparkline": [0.00],
    "tags": ["string"]
  }]
}
```

### JSON Schema — forecasts.json
```json
{
  "updated_at": "ISO8601",
  "forecasts": [{
    "card_id": "string",
    "history": [{ "date": "YYYY-MM-DD", "price": 0.00 }],
    "forecast": [{ "date": "YYYY-MM-DD", "yhat": 0.00, "yhat_lower": 0.00, "yhat_upper": 0.00 }],
    "metrics": { "rmse": 0.00, "mae": 0.00, "r2": 0.00 },
    "model": "prophet"
  }]
}
```

---

## VISUAL RULES (enforced)

- `--accent-red: #E2012D` — primary CTA, live indicators, negative delta
- `--accent-gold: #C9A84C` — premium accent, positive signal, headings
- `--bg-primary: #0A0A0A` — page background
- `--bg-surface: #121212` — card/panel background
- `--bg-elevated: #1A1A1A` — hover/active state surfaces
- Green `#4CAF50` — positive delta ONLY (never decorative)
- Red movement = negative market. Gold = premium/positive.

**Fonts (loaded via Google Fonts):**
- `Bebas Neue` — hero headlines, score-bug stat labels
- `Rajdhani` — nav, tabs, filters, buttons, UI labels
- `Inter` — body copy, descriptions
- `JetBrains Mono` — all numbers, prices, metrics, percentages

**Never:** neon gradients, saturated blues, cyberpunk purple, system fonts.

---

## COMPONENT RULES

Every component must:
1. Accept a `className` prop for layout overrides
2. Use CSS variables for all colors (never hardcode hex in JSX)
3. Have a named export AND a default export
4. Include a brief JSDoc comment describing its props

Broadcast-style primitives to maintain:
- `<ScoreBug />` — HUD stat display with label + value + delta
- `<LiveDot />` — pulsing red dot with LIVE label
- `<LowerThird />` — slide-up name/stat overlay
- `<BroadcastTicker />` — horizontal scrolling market data
- `<ConfidenceBand />` — Recharts area with yhat_upper/lower shading
- `<Rarity />` — pill badge per rarity tier
- `<Signal />` — BUY/SELL/HOLD pill
- `<Delta />` — ▲/▼ percentage with color
- `<Sparkline />` — inline SVG mini chart

---

## PAGE RESPONSIBILITIES

| Route | Page | Primary Goal |
|---|---|---|
| `/` | Landing | Cinematic hook — establish platform identity |
| `/dashboard` | Dashboard | Market overview — top movers, sentiment |
| `/cards` | Explorer | Card search, filter, rarity browse |
| `/cards/:id` | Detail | Full forecast + historical chart |
| `/models` | Models | ML credibility — Prophet metrics |
| `/meta` | MetaTracker | Deck trends, top-played cards |

---

## GIT COMMIT CONVENTION

```
type(scope): message

Types: feat | fix | data | style | refactor | test | docs | chore
Scopes: phase0 | phase1 | ... | pipeline | design | deploy

Examples:
  feat(phase2): add ScoreBug and LowerThird broadcast primitives
  data(pipeline): add TCGPlayer scraper with retry logic
  fix(phase4): correct Prophet confidence band rendering on mobile
  docs(plan): mark Phase 1 complete, update git log
```

---

## SESSION STARTUP CHECKLIST

When beginning a new session:
1. Read `docs/plan.md` — find current phase and first incomplete task
2. Read `docs/design.md` — refresh component system and color rules
3. Read `docs/animations.md` — check timing constants before animating
4. Run `npm run dev` to verify baseline builds
5. Never modify `/public/data/*.json` manually — always via pipeline

---

## SUCCESS CRITERIA

Project is complete when:

- [ ] Vercel deployment is live and stable
- [ ] GitHub Actions pipeline runs weekly without failure
- [ ] All 6 pages are interactive with real data
- [ ] Forecast charts show confidence bands with real Prophet output
- [ ] Mobile experience passes QA on 375px viewport
- [ ] Lighthouse Accessibility ≥ 95
- [ ] Lighthouse Performance ≥ 85
- [ ] Recruiters can navigate without explanation
- [ ] Riftbound players find real card data useful
- [ ] The product feels indistinguishable from a funded startup
