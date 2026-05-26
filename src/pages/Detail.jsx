import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ConfidenceBand } from '../components/ConfidenceBand'
import { SkeletonChart } from '../components/SkeletonChart'
import { ScoreBugRow } from '../components/ScoreBugRow'
import { LowerThird } from '../components/LowerThird'
import { Rarity } from '../components/Rarity'
import { Signal } from '../components/Signal'
import { MarketCard } from '../components/MarketCard'
import { Button } from '../components/Button'
import { Delta } from '../components/Delta'
import { useMarketData } from '../hooks/useMarketData'
import { useCardForecast } from '../hooks/useCardForecast'
import { usePageTitle } from '../hooks/usePageTitle'
import { formatPrice } from '../lib/format'

const TOGGLE_OPTIONS = [
  { value: 'combined',  label: 'COMBINED' },
  { value: 'history',   label: 'HISTORY'  },
  { value: 'forecast',  label: 'FORECAST' },
]

const METRIC_EXPLANATIONS = [
  {
    key: 'rmse',
    label: 'PRICE ERROR',
    title: 'How close are the predictions?',
    body: 'The average dollar amount the forecast misses by. A price error of $1.80 means our model\'s guesses are usually within $1.80 of the real price — roughly the spread between a buylist and market price.',
  },
  {
    key: 'mae',
    label: 'TYPICAL MISS',
    title: 'What\'s the usual miss on any given week?',
    body: 'The middle-of-the-road prediction error. Half of forecasts beat this number, half are wider. Good to check if you\'re deciding whether to buy now or wait a week.',
  },
  {
    key: 'r2',
    label: 'CONFIDENCE',
    title: 'How well does the model track price movement?',
    body: 'Shown as a percentage. 99.86% means the model\'s price curve almost perfectly follows real historical prices. Anything above 95% is strong for a volatile TCG market.',
  },
]

function buildScoreBugs(card, forecast) {
  const forecastTarget = forecast?.forecast?.[0]?.yhat
  const hasMetrics = forecast != null && forecast.metrics != null
  return [
    { label: 'CURRENT PRICE',   value: card ? `$${formatPrice(card.current_price)}` : '—' },
    { label: '7D CHANGE',       value: card ? undefined : '—', delta: card?.delta_7d_pct },
    { label: 'NEXT WEEK TARGET',value: forecastTarget != null ? `$${forecastTarget.toFixed(2)}` : '—', highlight: true },
    { label: 'PRICE ERROR',     value: hasMetrics ? `$${forecast.metrics.rmse.toFixed(2)}` : '—' },
    { label: 'CONFIDENCE',      value: hasMetrics ? `${(forecast.metrics.r2 * 100).toFixed(1)}%` : '—' },
  ]
}

function MetricsAccordion({ metrics }) {
  const [open, setOpen] = useState(null)
  const toggle = key => setOpen(prev => prev === key ? null : key)

  if (!metrics) return null
  return (
    <div className="mt-8">
      <p className="eyebrow mb-4" style={{ color: 'var(--accent-red)' }}>// MODEL METRICS</p>
      <div className="flex flex-col gap-px" style={{ background: 'var(--border-subtle)' }}>
        {METRIC_EXPLANATIONS.map(item => (
          <div key={item.key} style={{ background: 'var(--bg-surface)' }}>
            <button
              onClick={() => toggle(item.key)}
              aria-expanded={open === item.key}
              className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer"
              style={{ background: 'none', border: 'none', color: 'inherit' }}
            >
              <div className="flex items-center gap-4">
                <span className="eyebrow" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>{item.label}</span>
                <span className="font-mono text-sm font-semibold" style={{ color: 'var(--accent-gold)' }}>
                  {item.key === 'r2'
                    ? `${(metrics.r2 * 100).toFixed(1)}%`
                    : `$${metrics[item.key].toFixed(2)}`
                  }
                </span>
              </div>
              <span
                className="font-mono text-xs"
                style={{
                  color: 'var(--text-muted)',
                  transform: open === item.key ? 'rotate(180deg)' : 'none',
                  transition: 'transform 200ms ease',
                  display: 'inline-block',
                }}
              >
                ▼
              </span>
            </button>
            {open === item.key && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
                className="px-4 pb-4"
              >
                <p className="font-ui font-semibold text-sm mb-1" style={{ color: 'var(--text-primary)' }}>
                  {item.title}
                </p>
                <p className="font-body text-sm" style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>
                  {item.body}
                </p>
              </motion.div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function filterForecastData(forecast, view) {
  if (!forecast) return null
  if (view === 'history')  return { ...forecast, forecast: [] }
  if (view === 'forecast') return { ...forecast, history: [] }
  return forecast
}

export default function Detail() {
  const { id } = useParams()
  const marketData = useMarketData()
  const forecast   = useCardForecast(id)

  const allCards    = marketData?.cards?.cards ?? []
  const card        = allCards.find(c => c.id === id) ?? null

  usePageTitle(card ? card.name : 'Card Detail')
  const relatedCards = allCards
    .filter(c => c.id !== id && c.faction === card?.faction)
    .slice(0, 4)

  const [chartView, setChartView] = useState('combined')
  const [copied, setCopied] = useState(false)

  const handleShare = useCallback(() => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [])

  const scoreBugs = buildScoreBugs(card, forecast)
  const chartData = filterForecastData(forecast, chartView)

  return (
    <div style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>

      {/* Hero section */}
      <section
        className="px-8 md:px-16 py-14"
        style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-subtle)' }}
      >
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="flex items-center gap-3 mb-4 flex-wrap">
              <Link
                to="/cards"
                className="font-mono text-xs"
                style={{ color: 'var(--text-muted)', opacity: 0.5, textDecoration: 'none' }}
              >
                ← EXPLORER
              </Link>
              {card && <Rarity kind={card.rarity} />}
              {card && <Signal signal={card.signal} />}
            </div>

            <p className="eyebrow mb-3" style={{ color: 'var(--accent-red)' }}>// CARD ANALYSIS</p>

            {card ? (
              <LowerThird
                title={card.name.toUpperCase()}
                subtitle={`${card.faction} · ${card.rarity} · ${card.tags?.join(' · ')}`}
                tag={card.signal}
              />
            ) : (
              <div style={{ height: 72 }} className="skeleton rounded" />
            )}

            <div className="flex items-center gap-4 mt-5 flex-wrap">
              {card && (
                <div className="flex items-baseline gap-3">
                  <span className="font-display text-4xl" style={{ color: 'var(--text-primary)' }}>
                    ${formatPrice(card.current_price)}
                  </span>
                  <Delta value={card.delta_7d_pct} />
                </div>
              )}
              <button
                onClick={handleShare}
                className="font-mono text-xs px-3 py-1.5 ml-auto"
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: copied ? 'var(--success)' : 'var(--text-muted)',
                  cursor: 'pointer',
                  transition: 'color 200ms',
                }}
                aria-label="Copy page link"
              >
                {copied ? '✓ COPIED' : '⎘ SHARE'}
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Score-bug KPIs */}
      <section className="px-8 md:px-16 py-6" style={{ background: 'var(--bg-elevated)' }}>
        <div className="max-w-5xl mx-auto">
          <ScoreBugRow items={scoreBugs} />
        </div>
      </section>

      {/* Chart section */}
      <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-primary)' }}>
        <div className="max-w-5xl mx-auto">
          {/* Chart header + toggle */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="flex items-center justify-between mb-6 flex-wrap gap-4"
          >
            <div>
              <p className="eyebrow mb-1" style={{ color: 'var(--accent-red)' }}>// PROPHET FORECAST</p>
              <h2 className="font-display text-3xl" style={{ color: 'var(--text-primary)' }}>
                PRICE HISTORY + 30-DAY FORECAST
              </h2>
            </div>
            {/* Chart view toggle */}
            <div
              className="flex gap-px"
              role="group"
              aria-label="Chart view"
              style={{ background: 'var(--border-subtle)' }}
            >
              {TOGGLE_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setChartView(opt.value)}
                  aria-pressed={chartView === opt.value}
                  className="eyebrow px-3 py-1.5 cursor-pointer"
                  style={{
                    background: chartView === opt.value ? 'var(--accent-red)' : 'var(--bg-elevated)',
                    color: chartView === opt.value ? '#fff' : 'var(--text-muted)',
                    border: 'none',
                    transition: 'background 150ms, color 150ms',
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            {forecast === undefined ? (
              <SkeletonChart height={360} />
            ) : forecast === null ? (
              <div
                style={{ height: 360, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}
              >
                <p className="font-display text-2xl" style={{ color: 'var(--text-muted)', opacity: 0.4 }}>NO FORECAST</p>
                <p className="font-mono text-xs" style={{ color: 'var(--text-muted)', opacity: 0.3 }}>This card is not in the top 30 tracked by Prophet. Check back after the next weekly update.</p>
              </div>
            ) : (
              <ConfidenceBand data={chartData} height={360} />
            )}
          </motion.div>

          <MetricsAccordion metrics={forecast?.metrics} />
        </div>
      </section>

      {/* Related cards */}
      {relatedCards.length > 0 && (
        <section
          className="px-8 md:px-16 py-12"
          style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)' }}
        >
          <div className="max-w-5xl mx-auto">
            <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// RELATED</p>
            <h3 className="font-display text-3xl mb-6" style={{ color: 'var(--text-primary)' }}>
              {card?.faction?.toUpperCase()} CARDS
            </h3>
            <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
              {relatedCards.map(c => <MarketCard key={c.id} card={c} />)}
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
