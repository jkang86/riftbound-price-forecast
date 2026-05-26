# docs/animations.md — Riftbound Market Intelligence Platform

## ANIMATION PHILOSOPHY

**Aesthetic reference:** LoL Worlds broadcast production.
Motion should feel like a live esports production — purposeful, weighty,
cinematic. Not flashy. Not decorative. Every animation earns its place.

**Motion level:** MEDIUM
**Rule:** If you can remove an animation and the page still communicates
clearly, it shouldn't exist.

---

## TIMING CONSTANTS

Always import these — never hardcode duration values.

```js
// src/lib/motion.js
export const TIMING = {
  INSTANT:    0,
  FAST:       150,   // hover state changes
  STANDARD:   250,   // most transitions
  ENTER:      400,   // elements entering viewport
  BROADCAST:  600,   // score-bug and lower-third reveals
  PAGE:       350,   // page transitions
  CHART:      800,   // chart draw animations
  TICKER:     40000, // BroadcastTicker one full loop (ms)
  STAGGER:    50,    // delay between staggered children
  SKELETON:   1600,  // shimmer loop
}

export const EASING = {
  STANDARD:   'cubic-bezier(0.4, 0, 0.2, 1)',
  ENTER:      'cubic-bezier(0.16, 1, 0.3, 1)',  // spring-like, snappy
  EXIT:       'cubic-bezier(0.4, 0, 1, 1)',
  BROADCAST:  'cubic-bezier(0.16, 1, 0.3, 1)',  // same as ENTER
}
```

---

## CSS KEYFRAMES

All keyframes live in `src/styles/global.css`:

```css
/* —— Broadcast / Score-Bug Animations ————————————————————————————————— */

/* Score-bug stat reveal — used when KPIs mount or update */
@keyframes scoreReveal {
  from {
    transform: translateY(8px) scaleY(0.9);
    opacity: 0;
    filter: blur(2px);
  }
  to {
    transform: translateY(0) scaleY(1);
    opacity: 1;
    filter: blur(0);
  }
}

/* Lower-third slide-up — card name/faction reveal */
@keyframes lowerThird {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Scan line — hero background effect, horizontal sweep */
@keyframes scanLine {
  0% {
    transform: translateY(-100%);
    opacity: 0;
  }
  10% { opacity: 0.6; }
  90% { opacity: 0.6; }
  100% {
    transform: translateY(100vh);
    opacity: 0;
  }
}

/* —— Live Indicator ————————————————————————————————————————————————————— */

@keyframes pulseRed {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(226, 1, 45, 0.5);
  }
  50% {
    opacity: 0.7;
    box-shadow: 0 0 0 6px rgba(226, 1, 45, 0);
  }
}

/* —— Market Ticker —————————————————————————————————————————————————————— */

@keyframes ticker {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* —— Scroll Reveals ————————————————————————————————————————————————————— */

@keyframes fadeUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* Stagger children — applied via animation-delay on nth-child */
@keyframes cardReveal {
  from {
    transform: translateY(12px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* —— Skeleton / Loading ————————————————————————————————————————————————— */

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

/* —— Chart ————————————————————————————————————————————————————————————— */

/* Line chart draw — applied to SVG path via stroke-dashoffset */
@keyframes chartDraw {
  from { stroke-dashoffset: var(--path-length, 1000); }
  to   { stroke-dashoffset: 0; }
}

/* Area fill fade-in — confidence band */
@keyframes areaReveal {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* —— Number Count-Up ————————————————————————————————————————————————————*/
/* Implemented in JS (see useCountUp hook), not CSS */

/* —— Page Transition ————————————————————————————————————————————————————*/

@keyframes pageEnter {
  from {
    transform: translateY(6px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
```

---

## CSS ANIMATION UTILITY CLASSES

```css
/* src/styles/global.css — animation utility classes */

.animate-score-reveal {
  animation: scoreReveal 600ms cubic-bezier(0.16,1,0.3,1) forwards;
}

.animate-lower-third {
  animation: lowerThird 400ms cubic-bezier(0.16,1,0.3,1) forwards;
}

.animate-scan-line {
  animation: scanLine 4s linear infinite;
}

.animate-pulse-red {
  animation: pulseRed 2s ease-in-out infinite;
}

.animate-ticker {
  animation: ticker 40s linear infinite;
}

.animate-ticker:hover {
  animation-play-state: paused;
}

.animate-fade-up {
  animation: fadeUp 500ms cubic-bezier(0.16,1,0.3,1) forwards;
}

.animate-card-reveal {
  opacity: 0; /* starts hidden, animation fills forward */
  animation: cardReveal 400ms cubic-bezier(0.16,1,0.3,1) forwards;
}

.animate-page-enter {
  animation: pageEnter 350ms cubic-bezier(0.16,1,0.3,1) forwards;
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-elevated) 0%,
    rgba(255,255,255,0.04) 50%,
    var(--bg-elevated) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1600ms ease-in-out infinite;
  border-radius: 4px;
}
```

---

## FRAMER MOTION VARIANTS

```js
// src/lib/motionVariants.js

export const pageVariants = {
  initial: { opacity: 0, y: 6 },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16,1,0.3,1] } },
  exit:    { opacity: 0, y: -4, transition: { duration: 0.2, ease: [0.4,0,1,1] } },
}

export const scoreRevealVariants = {
  initial: { opacity: 0, y: 8, scaleY: 0.9, filter: 'blur(2px)' },
  enter:   {
    opacity: 1, y: 0, scaleY: 1, filter: 'blur(0px)',
    transition: { duration: 0.6, ease: [0.16,1,0.3,1] }
  },
}

export const lowerThirdVariants = {
  initial: { opacity: 0, y: '100%' },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16,1,0.3,1] } },
}

export const staggerContainerVariants = {
  initial: {},
  enter: {
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  },
}

export const cardRevealVariants = {
  initial: { opacity: 0, y: 12 },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16,1,0.3,1] } },
}

export const chartRevealVariants = {
  initial: { opacity: 0 },
  enter:   { opacity: 1, transition: { duration: 0.8, ease: 'easeOut' } },
}

export const tickerVariants = {
  animate: {
    x: '-50%',
    transition: { duration: 40, ease: 'linear', repeat: Infinity }
  }
}
```

---

## INTERSECTIONOBSERVER PATTERNS

### `useIntersect` Hook

```js
// src/hooks/useIntersect.js
import { useEffect, useRef, useState } from 'react'

export function useIntersect(options = {}) {
  const ref = useRef(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true)
        observer.unobserve(el) // fire once
      }
    }, {
      threshold: options.threshold ?? 0.15,
      rootMargin: options.rootMargin ?? '0px 0px -60px 0px',
    })

    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return [ref, isVisible]
}
```

### Usage — Card Grid Stagger

```jsx
// In ExplorerPage or TopMovers
function CardGrid({ cards }) {
  const [ref, isVisible] = useIntersect({ threshold: 0.05 })

  return (
    <motion.div
      ref={ref}
      variants={staggerContainerVariants}
      initial="initial"
      animate={isVisible ? "enter" : "initial"}
      className="grid grid-cols-3 gap-4"
    >
      {cards.map(card => (
        <motion.div key={card.id} variants={cardRevealVariants}>
          <MarketCard card={card} />
        </motion.div>
      ))}
    </motion.div>
  )
}
```

### Usage — Section Reveal (fadeUp)

```jsx
function Section({ children, className }) {
  const [ref, isVisible] = useIntersect()

  return (
    <motion.section
      ref={ref}
      variants={{ initial: { opacity: 0, y: 20 }, enter: { opacity: 1, y: 0 } }}
      initial="initial"
      animate={isVisible ? "enter" : "initial"}
      transition={{ duration: 0.5, ease: [0.16,1,0.3,1] }}
      className={className}
    >
      {children}
    </motion.section>
  )
}
```

### Usage — Chart Progressive Reveal

```jsx
// In ConfidenceBand — fade in chart after entering viewport
function ConfidenceBand({ data }) {
  const [ref, isVisible] = useIntersect({ threshold: 0.3 })

  return (
    <motion.div
      ref={ref}
      variants={chartRevealVariants}
      initial="initial"
      animate={isVisible ? "enter" : "initial"}
    >
      <ComposedChart data={data}>...</ComposedChart>
    </motion.div>
  )
}
```

---

## COUNT-UP ANIMATION

Used for ScoreBug values on mount (market cap, total cards, etc.).

```js
// src/hooks/useCountUp.js
import { useEffect, useState } from 'react'
import { useReducedMotion } from './useReducedMotion'

export function useCountUp(target, duration = 1000) {
  const prefersReduced = useReducedMotion()
  const [value, setValue] = useState(prefersReduced ? target : 0)

  useEffect(() => {
    if (prefersReduced) { setValue(target); return }

    const start = performance.now()
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
      setValue(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target, duration, prefersReduced])

  return value
}

// Usage:
// const displayValue = useCountUp(42813, 1200)
// <span>{formatPrice(displayValue)}</span>
```

---

## CHART LINE DRAW ANIMATION

For the main line on `ConfidenceBand` — progressive drawing effect.

```js
// Applied via Recharts' animationBegin + animationDuration props
<Line
  type="monotone"
  dataKey="price"
  stroke="var(--accent-gold)"
  strokeWidth={2}
  dot={false}
  animationBegin={200}
  animationDuration={800}
  animationEasing="ease-out"
/>

<Line
  dataKey="yhat"
  stroke="var(--accent-red)"
  strokeWidth={1.5}
  strokeDasharray="4 3"
  dot={false}
  animationBegin={600}
  animationDuration={800}
/>
```

---

## BROADCAST SCAN LINE (ScanLine component)

```jsx
// src/components/ScanLine.jsx
// Purely decorative — horizontal line sweeping down hero section.
// Skipped entirely when prefers-reduced-motion.

export function ScanLine() {
  const prefersReduced = useReducedMotion()
  if (prefersReduced) return null

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      <div
        className="absolute left-0 right-0 h-px"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, #E2012D 50%, transparent 100%)',
          opacity: 0.4,
          animation: 'scanLine 4s linear infinite',
        }}
      />
    </div>
  )
}
```

---

## HOVER INTERACTIONS

```css
/* Card hover — gold border + subtle glow */
.market-card {
  border: 1px solid var(--border-subtle);
  transition: border-color 200ms ease, box-shadow 200ms ease, transform 200ms ease;
}
.market-card:hover {
  border-color: var(--accent-gold);
  box-shadow: 0 0 20px rgba(201,168,76,0.12);
  transform: translateY(-2px);
}

/* Button hover — red fill on ghost buttons */
.btn-ghost {
  transition: background 150ms ease, color 150ms ease;
}
.btn-ghost:hover {
  background: rgba(226,1,45,0.08);
  color: var(--accent-red);
}

/* Nav link — underline slide */
.nav-link::after {
  content: '';
  display: block;
  height: 2px;
  background: var(--accent-red);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 200ms ease;
}
.nav-link:hover::after,
.nav-link[aria-current="page"]::after {
  transform: scaleX(1);
}
```

---

## PREFERS-REDUCED-MOTION

**Rule:** Every animation MUST have a reduced-motion fallback.

```css
/* global.css — override all animations when user prefers reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  /* Keep ticker static — show a simple overflow scroll */
  .animate-ticker {
    animation: none !important;
    overflow-x: auto;
  }
}
```

```js
// src/hooks/useReducedMotion.js
import { useEffect, useState } from 'react'

export function useReducedMotion() {
  const [prefersReduced, setPrefersReduced] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handler = (e) => setPrefersReduced(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return prefersReduced
}
```

---

## ANIMATION DO / DON'T

| DO | DON'T |
|---|---|
| Animate `transform` and `opacity` | Animate `width`, `height`, `top`, `left` |
| One entrance animation per viewport entry | Stack multiple animations on same element |
| Stagger children by 50ms | Stagger children > 100ms (feels slow) |
| Use `forwards` fill mode | Leave elements in initial (invisible) state |
| `animation-play-state: paused` on ticker hover | Auto-pause ticker aggressively |
| Test at 0.25x speed in DevTools | Ship without visual review at slow speed |
| Always provide `prefers-reduced-motion` fallback | Assume all users want motion |

---

## PAGE TRANSITION WRAPPER

```jsx
// src/components/PageTransition.jsx
import { motion } from 'framer-motion'
import { pageVariants } from '../lib/motionVariants'

export function PageTransition({ children }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
    >
      {children}
    </motion.div>
  )
}

// Usage in App.jsx — wrap each page:
// <PageTransition><LandingPage /></PageTransition>
```
