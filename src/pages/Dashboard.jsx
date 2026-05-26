import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { MarketOverviewChart } from '../components/MarketOverviewChart'
import { RarityDonut } from '../components/RarityDonut'
import { VolatilityHeatmap } from '../components/VolatilityHeatmap'
import { ScoreBug } from '../components/ScoreBug'
import { MarketCard } from '../components/MarketCard'
import { SkeletonCard } from '../components/SkeletonCard'
import { SkeletonChart } from '../components/SkeletonChart'
import { Button } from '../components/Button'
import { LiveDot } from '../components/LiveDot'
import { useMarketData } from '../hooks/useMarketData'
import { usePageTitle } from '../hooks/usePageTitle'
import { staggerContainerVariants, cardRevealVariants } from '../lib/motionVariants'
import { formatPrice } from '../lib/format'

const MOVERS_COUNT = 6

function topMovers(cards, n) {
  return [...cards]
    .sort((a, b) => Math.abs(b.delta_7d_pct ?? 0) - Math.abs(a.delta_7d_pct ?? 0))
    .slice(0, n)
}

function buildKPIs(market) {
  if (!market) return Array.from({ length: 5 }, (_, i) => ({ label: '—', value: '—' }))
  return [
    { label: 'MARKET CAP',    value: `$${Math.round(market.market_cap).toLocaleString()}` },
    { label: '24H VOLUME',    value: formatPrice(market.volume_24h) },
    { label: 'TOTAL CARDS',   value: market.total_cards, countUp: true },
    { label: 'GAINERS',       value: market.gainers_count ?? '—', highlight: true },
    { label: 'VOLATILITY IDX',value: market.volatility_index != null ? `${market.volatility_index.toFixed(1)}` : '—' },
  ]
}

/* ── Section: Market Overview ────────────────────────────────────────── */

function OverviewSection({ market }) {
  const kpis = buildKPIs(market)
  const history = market?.market_history ?? []

  return (
    <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-primary)' }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="flex items-center gap-4 mb-8"
        >
          <div>
            <p className="eyebrow mb-1" style={{ color: 'var(--accent-red)' }}>// MARKET OVERVIEW</p>
            <h1 className="font-display text-5xl leading-none" style={{ color: 'var(--text-primary)' }}>
              DASHBOARD
            </h1>
          </div>
          <LiveDot className="ml-2" />
          {market?.updated_at && (
            <span className="font-mono text-xs ml-auto" style={{ color: 'var(--text-muted)', opacity: 0.5 }}>
              UPDATED {new Date(market.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase()}
            </span>
          )}
        </motion.div>

        {/* Chart + KPI stack */}
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Area chart */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="flex-1 min-w-0 p-5"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <p className="eyebrow mb-1" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>90-DAY MARKET CAP</p>
            {history.length
              ? <MarketOverviewChart history={history} height={280} />
              : <SkeletonChart height={280} />
            }
          </motion.div>

          {/* KPI stack */}
          <motion.div
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-row lg:flex-col gap-px lg:w-56"
            style={{ background: 'var(--border-subtle)' }}
          >
            {kpis.map((kpi, i) => (
              <ScoreBug
                key={i}
                label={kpi.label}
                value={kpi.value}
                countUp={kpi.countUp}
                highlight={kpi.highlight}
                className="flex-1 lg:flex-none"
              />
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  )
}

/* ── Section: Top Movers ─────────────────────────────────────────────── */

function TopMoversSection({ cards, loading }) {
  return (
    <section
      className="px-8 md:px-16 py-12"
      style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)' }}
    >
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="flex items-end justify-between mb-6 flex-wrap gap-4"
        >
          <div>
            <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// TOP MOVERS</p>
            <h2 className="font-display text-4xl" style={{ color: 'var(--text-primary)' }}>
              WEEKLY LEADERS
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
            {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
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

/* ── Section: Analytics Row ──────────────────────────────────────────── */

function AnalyticsSection({ market }) {
  const distribution = market?.rarity_distribution ?? {}
  const heatmapData  = market?.faction_rarity_volatility ?? []

  return (
    <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-primary)' }}>
      <div className="max-w-7xl mx-auto">
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
          className="eyebrow mb-8"
          style={{ color: 'var(--accent-red)' }}
        >
          // MARKET ANALYTICS
        </motion.p>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Volatility heatmap */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-40px' }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="flex-1 min-w-0 p-5"
            style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
          >
            <p className="eyebrow mb-1" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>VOLATILITY INDEX</p>
            <h3 className="font-display text-2xl mb-4" style={{ color: 'var(--text-primary)' }}>
              FACTION × RARITY
            </h3>
            <VolatilityHeatmap data={heatmapData} />
          </motion.div>

          {/* Rarity donut */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-40px' }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
            className="p-5"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              width: '100%',
              maxWidth: 260,
              alignSelf: 'flex-start',
            }}
          >
            <p className="eyebrow mb-1" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>SUPPLY BREAKDOWN</p>
            <h3 className="font-display text-2xl mb-4" style={{ color: 'var(--text-primary)' }}>
              RARITY
            </h3>
            <RarityDonut distribution={distribution} size={180} />
          </motion.div>
        </div>
      </div>
    </section>
  )
}

/* ── Page ────────────────────────────────────────────────────────────── */

export default function Dashboard() {
  usePageTitle('Dashboard')
  const marketData = useMarketData()

  const allCards = marketData?.cards?.cards ?? []
  const market   = marketData?.market ?? null
  const movers   = topMovers(allCards, MOVERS_COUNT)
  const isLoading = !marketData

  return (
    <>
      <OverviewSection market={market} />
      <TopMoversSection cards={movers} loading={isLoading} />
      <AnalyticsSection market={market} />
    </>
  )
}
