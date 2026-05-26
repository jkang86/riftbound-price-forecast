# docs/design.md — Riftbound Market Intelligence Platform

## VISUAL DIRECTION

**Aesthetic:** Esports broadcast overlay — cinematic, score-bug energy.

The platform feels like the League of Legends World Championship production
team built a collectible market terminal. Every screen should feel like it
could be a live broadcast lower-third or analyst desk overlay.

**Three-word test:** Cinematic. Credible. Alive.

**NOT:**
- A generic analytics dashboard
- A crypto UI clone
- A neon cyberpunk aesthetic
- A fan site

---

## TAILWIND CONFIG

```js
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'rift-red':      '#E2012D',
        'rift-gold':     '#C9A84C',
        'rift-black':    '#0A0A0A',
        'rift-surface':  '#121212',
        'rift-elevated': '#1A1A1A',
        'rift-border':   'rgba(255,255,255,0.08)',
        'rift-success':  '#4CAF50',
        'rift-warning':  '#FFB020',
        'rift-danger':   '#FF5252',
        'rift-text':     '#F5F5F5',
        'rift-muted':    'rgba(255,255,255,0.65)',
      },
      fontFamily: {
        display:  ['Bebas Neue', 'sans-serif'],
        ui:       ['Rajdhani', 'sans-serif'],
        body:     ['Inter', 'sans-serif'],
        mono:     ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-red':     'pulseRed 2s ease-in-out infinite',
        'ticker':        'ticker 40s linear infinite',
        'lower-third':   'lowerThird 0.4s cubic-bezier(0.16,1,0.3,1) forwards',
        'score-reveal':  'scoreReveal 0.6s cubic-bezier(0.16,1,0.3,1) forwards',
        'fade-up':       'fadeUp 0.5s ease forwards',
        'shimmer':       'shimmer 1.6s ease-in-out infinite',
      },
      keyframes: {
        pulseRed: {
          '0%,100%': { opacity: 1, boxShadow: '0 0 0 0 rgba(226,1,45,0.4)' },
          '50%':     { opacity: 0.7, boxShadow: '0 0 0 6px rgba(226,1,45,0)' },
        },
        ticker: {
          '0%':   { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        lowerThird: {
          from: { transform: 'translateY(100%)', opacity: 0 },
          to:   { transform: 'translateY(0)',    opacity: 1 },
        },
        scoreReveal: {
          from: { transform: 'translateY(8px) scaleY(0.9)', opacity: 0 },
          to:   { transform: 'translateY(0) scaleY(1)',     opacity: 1 },
        },
        fadeUp: {
          from: { transform: 'translateY(16px)', opacity: 0 },
          to:   { transform: 'translateY(0)',    opacity: 1 },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backgroundImage: {
        'shimmer-gradient': 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 50%, transparent 100%)',
      },
    },
  },
  plugins: [],
}
```

---

## CSS VARIABLES (global.css)

```css
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg-primary:    #0A0A0A;
  --bg-surface:    #121212;
  --bg-elevated:   #1A1A1A;
  --accent-red:    #E2012D;
  --accent-gold:   #C9A84C;
  --text-primary:  #F5F5F5;
  --text-muted:    rgba(255,255,255,0.65);
  --border-subtle: rgba(255,255,255,0.08);
  --success:       #4CAF50;
  --warning:       #FFB020;
  --danger:        #FF5252;
}

* { box-sizing: border-box; }

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Utility classes */
.font-display  { font-family: 'Bebas Neue', sans-serif; letter-spacing: 0.04em; }
.font-ui       { font-family: 'Rajdhani', sans-serif; }
.font-mono     { font-family: 'JetBrains Mono', monospace; }
.eyebrow       { font-family: 'Rajdhani', sans-serif; font-weight: 600;
                 letter-spacing: 0.12em; text-transform: uppercase; font-size: 11px; }
```

---

## TYPOGRAPHY SYSTEM

### Bebas Neue — Display / Score-Bug Labels
- Hero headlines: `text-7xl md:text-9xl font-display`
- Section titles: `text-4xl md:text-6xl font-display`
- Score-bug stat values: `text-3xl font-display`
- Broadcast lower-thirds: `text-2xl font-display`
- **Never use for:** body text, paragraphs, descriptions

### Rajdhani — UI Chrome
- Navigation links: `font-ui font-600 text-sm tracking-widest uppercase`
- Filter labels: `font-ui font-600 text-xs tracking-wider uppercase`
- Buttons: `font-ui font-700 text-sm tracking-widest uppercase`
- Tab labels: `font-ui font-600 text-xs tracking-wider uppercase`
- Signal/rarity pills: `font-ui font-600 text-[10px] tracking-wider uppercase`

### Inter — Content
- Body paragraphs: `font-body text-sm leading-relaxed text-rift-muted`
- Card descriptions: `font-body text-sm`
- Insight panels: `font-body text-base`

### JetBrains Mono — Numbers Only
- Prices: `font-mono text-lg font-semibold`
- Percentages/deltas: `font-mono text-sm font-semibold`
- RMSE/R²/metrics: `font-mono text-xs`
- Card IDs: `font-mono text-xs text-rift-muted`
- All numbers in charts: applied via Recharts `tick` props

---

## COLOR RULES

| Color | Use | Never Use For |
|---|---|---|
| `#E2012D` Red | Primary CTA, live indicator, negative delta, nav active state | Positive market movement |
| `#C9A84C` Gold | Premium accent, positive signal, section headings, hover glow | Error states |
| `#4CAF50` Green | Positive delta ONLY | Decorative use |
| `#FF5252` Danger | Negative delta, sell signal | General accent |
| `#FFB020` Warning | WATCH/HOLD signal, caution states | Primary accent |
| `#F5F5F5` Text | Body copy | Large display text (use font-display instead) |
| `rgba(255,255,255,0.65)` Muted | Secondary labels, metadata | Primary content |

**Glow rules:**
- Red glow: `box-shadow: 0 0 20px rgba(226,1,45,0.15)` — live indicators, active nav
- Gold glow: `box-shadow: 0 0 20px rgba(201,168,76,0.12)` — hover on premium cards
- Never apply glow to more than one element per viewport simultaneously

---

## BROADCAST COMPONENT SYSTEM

### `<ScoreBug />`
The core broadcast primitive. Replicates LoL Worlds HUD stat blocks.

```jsx
// Props: label, value, delta?, highlight?
// Usage: <ScoreBug label="MARKET CAP" value="$42,813" delta={+2.4} />
```
Structure:
```
┌─────────────────┐
│ MARKET CAP      │  ← Rajdhani eyebrow, gold
│ $42,813         │  ← Bebas Neue 2xl, white
│ ▲ +2.4%         │  ← JetBrains Mono, green
└─────────────────┘
Border-left: 2px solid var(--accent-gold)
Background: var(--bg-elevated)
```

### `<LowerThird />`
Slide-up broadcast overlay. Used on hero and card detail pages.

```jsx
// Props: title, subtitle, tag?
// Animates: translateY(100%) → translateY(0) on mount
```

### `<BroadcastTicker />`
Horizontal scrolling market tape. Lives at top of Dashboard.

```jsx
// Props: items[] = [{ name, price, delta }]
// Infinite loop via CSS animation: ticker 40s linear infinite
// Duplicated content for seamless loop
```

### `<LiveDot />`
```jsx
// Pulsing red dot + "LIVE" label
// Uses: animate-pulse-red keyframe
// Position: fixed top-right on Dashboard, inline elsewhere
```

### `<ConfidenceBand />`
Recharts `<ComposedChart>` wrapper with Prophet output.

```jsx
// Props: history[], forecast[], card
// Layers: Area (yhat_upper - yhat_lower), Line (yhat), Line (actual)
// Colors: gold line (actual), red line (forecast), rgba gold fill (band)
```

### `<Rarity />`
```
Mythic  → Red   #E2012D bg rgba(226,1,45,0.12)
Legend  → Gold  #C9A84C bg rgba(201,168,76,0.14)
Epic    → Purple #A98BFF bg rgba(169,139,255,0.12)
Rare    → Blue  #5DB7FF bg rgba(93,183,255,0.12)
Common  → Grey  #9aa3ad bg rgba(154,163,173,0.12)
```

---

## PAGE-LEVEL DESIGN SPECS

### Landing (`/`)
**Goal:** Cinematic hook in under 3 seconds.

Layout:
```
[BROADCAST TICKER — fixed top]
[HERO — full viewport]
  → animated red scan line across background
  → Bebas Neue headline: "THE RIFTBOUND ECONOMY, LIVE"
  → score-bug row: Total Cards | Market Cap | 24h Volume | Top Gainer
  → LowerThird: featured card with signal badge
[FEATURED PREDICTION PANEL]
  → ConfidenceBand chart — the money shot
[TOP MOVERS — 3-column grid]
[MARKET SENTIMENT — horizontal bar]
```

**WOW moment:** The scan-line + score-bug row. Feels like tuning into a broadcast.

### Dashboard (`/dashboard`)
**Layout:** 12-col grid, asymmetric.
- Left 8 cols: market overview chart (area, 90-day)
- Right 4 cols: score-bug stack (5 KPIs)
- Full width: BroadcastTicker
- 3-col grid: Top Movers cards
- 2-col: Volatility heatmap + Rarity distribution donut

### Explorer (`/cards`)
**Layout:** Filter sidebar (left 3 cols) + card grid (right 9 cols)
- Filter sidebar: faction pills, rarity checkboxes, signal filter, price range slider
- Card grid: 3-col desktop, 2-col tablet, 1-col mobile
- Each card: art placeholder, name, price (mono), rarity badge, sparkline, signal

### Detail (`/cards/:id`)
**Layout:** Cinematic single-card presentation.
- Top: LowerThird hero with card name + faction
- Left 7 cols: ConfidenceBand chart (full 90d history + 30d forecast)
- Right 5 cols: score-bug stack (price, signal, RMSE, confidence)
- Bottom: Related cards row

### Models (`/models`)
**Goal:** Technical credibility without academic feel.
- Model comparison table (Prophet vs baseline)
- Per-metric bars: RMSE, MAE, R²
- Confidence interval distribution chart
- Feature importance visual (horizontal bars, gold fill)

### MetaTracker (`/meta`) — NEW
**Goal:** Deck-level market intelligence.
- Top decks by win-rate (weekly snapshot, manual or scraped)
- Top-played cards by deck inclusion rate
- Rising/falling inclusion trend sparklines
- Faction breakdown heatmap

---

## RESPONSIVE STRATEGY

| Breakpoint | Behavior |
|---|---|
| `sm` 640px | Single column, collapsed nav |
| `md` 768px | 2-col grids, filter drawer |
| `lg` 1024px | Full sidebar layout |
| `xl` 1280px | Cinematic spacing, wide charts |
| `2xl` 1536px | Max-width container (1400px) |

**Mobile priorities (< 640px):**
1. Score-bug row (horizontal scroll, no wrap)
2. Featured prediction (ConfidenceBand chart, no sidebar)
3. Card grid (1 col)
4. Nav collapses to hamburger with slide-in drawer

**Charts on mobile:**
- Remove grid labels, keep axis
- Reduce data points to last 30d
- Maintain touch-scroll interaction

---

## CARD COMPONENT ANATOMY

```
┌──────────────────────────────────────┐
│  [CARD ART AREA]          [RARITY]  │  ← 160px tall, bg-elevated
│                                      │
├──────────────────────────────────────┤
│  Card Name                [SIGNAL]  │  ← font-ui font-600
│  Faction · Epic                      │  ← text-rift-muted text-xs
├──────────────────────────────────────┤
│  $24.99              [SPARKLINE]    │  ← mono price + 120px sparkline
│  ▲ +8.2% (7d)                       │  ← delta tag
└──────────────────────────────────────┘
Border: 1px solid var(--border-subtle)
Hover: border-color → var(--accent-gold) + gold glow
Transition: 200ms ease
```

---

## LOADING & SKELETON STATES

```css
/* Shimmer skeleton */
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-elevated) 0%,
    rgba(255,255,255,0.04) 50%,
    var(--bg-elevated) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.6s ease-in-out infinite;
  border-radius: 4px;
}
```

Skeleton shapes per component:
- Card: full card shape (aspect-ratio 3/4)
- ScoreBug: 80px × 60px block
- Chart: full width × 240px rectangle
- Ticker: full width × 32px strip

**Empty states:** Never blank. Use: "No cards match your filters." with a
gold-accent CTA to reset filters.

---

## ACCESSIBILITY RULES

- All interactive elements: visible focus ring `ring-2 ring-rift-gold ring-offset-2 ring-offset-rift-black`
- Contrast ratio: ≥ 4.5:1 for all text (verified against bg-primary)
- `prefers-reduced-motion`: all animations must have a `@media` fallback
- Semantic HTML: `<nav>`, `<main>`, `<section aria-label>`, `<article>`
- ARIA: `aria-label` on all icon buttons, `aria-live="polite"` on ticker
- Keyboard: Tab order follows visual flow. Esc closes drawers/modals.

---

## WHAT MAKES THIS UNFORGETTABLE

The one thing a recruiter will remember: **the broadcast framing.**

Every other analytics portfolio has cards and charts. Ours has a score-bug
row, a live indicator, a scrolling ticker, and lower-third reveals. It feels
like tuning in to a live event, not opening a dashboard.

That's the differentiator. Protect it in every design decision.
