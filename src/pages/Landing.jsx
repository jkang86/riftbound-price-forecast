import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ScanLine } from '../components/ScanLine'
import { ScoreBugRow } from '../components/ScoreBugRow'
import { LowerThird } from '../components/LowerThird'
import { ConfidenceBand } from '../components/ConfidenceBand'
import { MarketCard } from '../components/MarketCard'
import { MarketSentiment } from '../components/MarketSentiment'
import { Button } from '../components/Button'
import { SkeletonCard } from '../components/SkeletonCard'
import { SkeletonChart } from '../components/SkeletonChart'
import { useMarketData } from '../hooks/useMarketData'
import { useCardForecast } from '../hooks/useCardForecast'
import { staggerContainerVariants, cardRevealVariants } from '../lib/motionVariants'
import { formatPrice } from '../lib/format'
import { usePageTitle } from '../hooks/usePageTitle'

const FEATURED_ID = 'jinx-loose-cannon'
const TOP_MOVERS_COUNT = 6

/* ── Helpers ─────────────────────────────────────────────────────────── */

function topMovers(cards, n) {
  return [...cards]
    .sort((a, b) => Math.abs(b.delta_7d_pct ?? 0) - Math.abs(a.delta_7d_pct ?? 0))
    .slice(0, n)
}

function buildScoreBugs(market) {
  if (!market) return [
    { label: 'TOTAL CARDS',  value: '—' },
    { label: 'MARKET CAP',   value: '—' },
    { label: '24H VOLUME',   value: '—' },
    { label: 'TOP GAINER',   value: '—' },
  ]

  const gainerName = market.top_gainer?.name?.split(',')[0] ?? '—'

  return [
    {
      label: 'TOTAL CARDS',
      value: market.total_cards,
      countUp: true,
    },
    {
      label: 'MARKET CAP',
      value: `$${Math.round(market.market_cap).toLocaleString()}`,
    },
    {
      label: '24H VOLUME',
      value: formatPrice(market.volume_24h),
    },
    {
      label: 'TOP GAINER',
      value: gainerName,
      delta: market.top_gainer?.delta_7d_pct,
    },
  ]
}

/* ── Section: Hero ───────────────────────────────────────────────────── */

function HeroSection({ market }) {
  return (
    <section
      className="relative flex flex-col justify-center overflow-hidden px-8 md:px-16"
      style={{
        minHeight: 'calc(100vh - 88px)',
        background: 'var(--bg-primary)',
      }}
    >
      <ScanLine />

      {/* Decorative diagonal accent — top right */}
      <div
        aria-hidden="true"
        className="absolute right-0 top-0 bottom-0 pointer-events-none"
        style={{ width: '38%', overflow: 'hidden', opacity: 0.04 }}
      >
        <svg width="100%" height="100%" preserveAspectRatio="none">
          <line x1="100%" y1="0" x2="0" y2="100%" stroke="var(--accent-gold)" strokeWidth="120" />
        </svg>
      </div>

      <div className="relative max-w-5xl" style={{ zIndex: 1 }}>
        {/* Eyebrow */}
        <motion.p
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="eyebrow mb-5"
          style={{ color: 'var(--accent-red)' }}
        >
          // LIVE MARKET INTELLIGENCE
        </motion.p>

        {/* Headline */}
        <div className="overflow-hidden mb-2">
          <motion.h1
            initial={{ y: '110%' }}
            animate={{ y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.05 }}
            className="font-display leading-none"
            style={{ fontSize: 'clamp(3.5rem, 11vw, 9.5rem)', color: 'var(--text-primary)' }}
          >
            THE RIFTBOUND
          </motion.h1>
        </div>
        <div className="overflow-hidden mb-2">
          <motion.div
            initial={{ y: '110%' }}
            animate={{ y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.10 }}
          >
            <span
              className="font-display leading-none"
              style={{ fontSize: 'clamp(3.5rem, 11vw, 9.5rem)', color: 'var(--accent-gold)' }}
            >
              ECONOMY,
            </span>
          </motion.div>
        </div>
        <div className="overflow-hidden mb-8">
          <motion.div
            initial={{ y: '110%' }}
            animate={{ y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
          >
            <span
              className="font-display leading-none"
              style={{ fontSize: 'clamp(3.5rem, 11vw, 9.5rem)', color: 'var(--text-primary)' }}
            >
              LIVE.
            </span>
          </motion.div>
        </div>

        {/* Score-bug row */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: 0.25 }}
          className="mb-10"
        >
          <ScoreBugRow items={buildScoreBugs(market)} />
        </motion.div>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.35 }}
          className="flex gap-4 flex-wrap"
        >
          <Button as={Link} to="/dashboard" variant="primary">
            ENTER DASHBOARD
          </Button>
          <Button as={Link} to="/cards" variant="ghost">
            EXPLORE CARDS →
          </Button>
        </motion.div>
      </div>

      {/* Scroll hint */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.6 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        aria-hidden="true"
      >
        <span className="font-mono text-xs tracking-widest" style={{ color: 'var(--text-muted)', opacity: 0.4 }}>
          SCROLL
        </span>
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ repeat: Infinity, duration: 1.6, ease: 'easeInOut' }}
          style={{ width: 1, height: 28, background: 'linear-gradient(to bottom, var(--accent-gold), transparent)', opacity: 0.5 }}
        />
      </motion.div>
    </section>
  )
}

/* ── Section: Featured Prediction ────────────────────────────────────── */

function FeaturedPrediction({ forecastData, featuredCard }) {
  return (
    <section
      className="px-8 md:px-16 py-20"
      style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)' }}
    >
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8"
        >
          <div>
            <p className="eyebrow mb-3" style={{ color: 'var(--accent-red)' }}>// FEATURED PREDICTION</p>
            {featuredCard ? (
              <LowerThird
                title={featuredCard.name.toUpperCase()}
                subtitle={`${featuredCard.faction} · ${featuredCard.rarity} · Prophet RMSE $1.80 · R² 0.9986`}
                tag={featuredCard.signal}
              />
            ) : (
              <LowerThird
                title="JINX, LOOSE CANNON"
                subtitle="Piltover · Mythic · Prophet RMSE $1.80 · R² 0.9986"
                tag="STRONG BUY"
              />
            )}
          </div>
          <Button as={Link} to={`/cards/${FEATURED_ID}`} variant="ghost">
            FULL ANALYSIS →
          </Button>
        </motion.div>

        {/* Chart */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 }}
        >
          {forecastData
            ? <ConfidenceBand data={forecastData} height={340} />
            : <SkeletonChart height={340} />
          }
        </motion.div>

        {/* Metrics row */}
        {forecastData?.metrics && (
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="flex gap-8 mt-6 flex-wrap"
          >
            {[
              { label: 'MODEL',      value: 'PROPHET' },
              { label: 'RMSE',       value: `$${forecastData.metrics.rmse.toFixed(2)}` },
              { label: 'MAE',        value: `$${forecastData.metrics.mae.toFixed(2)}` },
              { label: 'R²',         value: forecastData.metrics.r2.toFixed(4) },
              { label: 'FORECAST',   value: '30 DAYS' },
            ].map(m => (
              <div key={m.label}>
                <p className="eyebrow mb-0.5" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>{m.label}</p>
                <p className="font-mono text-sm font-semibold" style={{ color: 'var(--accent-gold)' }}>{m.value}</p>
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </section>
  )
}

/* ── Section: Top Movers ─────────────────────────────────────────────── */

function TopMovers({ cards, loading }) {
  return (
    <section className="px-8 md:px-16 py-20" style={{ background: 'var(--bg-primary)' }}>
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="flex items-end justify-between mb-8 flex-wrap gap-4"
        >
          <div>
            <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// TOP MOVERS</p>
            <h2 className="font-display text-5xl" style={{ color: 'var(--text-primary)' }}>
              MARKET LEADERS
            </h2>
          </div>
          <Button as={Link} to="/cards" variant="ghost">
            ALL CARDS →
          </Button>
        </motion.div>

        {loading ? (
          <div
            className="grid gap-4"
            style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}
          >
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : (
          <motion.div
            variants={staggerContainerVariants}
            initial="initial"
            whileInView="enter"
            viewport={{ once: true, margin: '-60px' }}
            className="grid gap-4"
            style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}
          >
            {cards.map(card => (
              <motion.div key={card.id} variants={cardRevealVariants}>
                <MarketCard card={card} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </section>
  )
}

/* ── Section: Market Sentiment ───────────────────────────────────────── */

function SentimentSection({ allCards }) {
  return (
    <section
      className="px-8 md:px-16 py-20"
      style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)' }}
    >
      <div className="max-w-5xl mx-auto">
        <MarketSentiment cards={allCards} />

        <div className="mt-10 flex gap-4 flex-wrap">
          <Button as={Link} to="/models" variant="ghost">
            VIEW MODEL DETAILS →
          </Button>
          <Button as={Link} to="/dashboard" variant="ghost">
            MARKET DASHBOARD →
          </Button>
        </div>
      </div>
    </section>
  )
}

/* ── Page ────────────────────────────────────────────────────────────── */

export default function Landing() {
  usePageTitle(null)
  const marketData   = useMarketData()
  const forecastData = useCardForecast(FEATURED_ID)

  const allCards     = marketData?.cards?.cards ?? []
  const market       = marketData?.market ?? null
  const movers       = topMovers(allCards, TOP_MOVERS_COUNT)
  const featuredCard = allCards.find(c => c.id === FEATURED_ID) ?? null
  const isLoading    = !marketData

  return (
    <>
      <HeroSection market={market} />
      <FeaturedPrediction forecastData={forecastData} featuredCard={featuredCard} />
      <TopMovers cards={movers} loading={isLoading} />
      <SentimentSection allCards={allCards} />
    </>
  )
}
