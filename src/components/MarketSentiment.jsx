import { motion } from 'framer-motion'
import { useIntersect } from '../hooks/useIntersect'

const SIGNAL_GROUPS = {
  bullish: ['STRONG BUY', 'BUY'],
  neutral: ['HOLD', 'WATCH'],
  bearish: ['SELL'],
}

/**
 * Horizontal bar showing the distribution of BUY / HOLD / SELL signals.
 * Animates widths on viewport entry.
 * Props: cards (array of card objects), className
 */
export function MarketSentiment({ cards = [], className = '' }) {
  const [ref, isVisible] = useIntersect({ threshold: 0.3 })

  const total = cards.length || 1
  const bullish = cards.filter(c => SIGNAL_GROUPS.bullish.includes(c.signal)).length
  const neutral = cards.filter(c => SIGNAL_GROUPS.neutral.includes(c.signal)).length
  const bearish = cards.filter(c => SIGNAL_GROUPS.bearish.includes(c.signal)).length

  const pctBullish = (bullish / total) * 100
  const pctNeutral = (neutral / total) * 100
  const pctBearish = (bearish / total) * 100

  const sentiment = pctBullish >= 50 ? 'BULLISH' : pctBearish >= 50 ? 'BEARISH' : 'NEUTRAL'
  const sentimentColor = sentiment === 'BULLISH' ? 'var(--success)' : sentiment === 'BEARISH' ? 'var(--danger)' : 'var(--warning)'

  const segments = [
    { label: 'BULLISH', pct: pctBullish, color: 'var(--success)',  count: bullish },
    { label: 'NEUTRAL', pct: pctNeutral, color: 'var(--warning)',  count: neutral },
    { label: 'BEARISH', pct: pctBearish, color: 'var(--danger)',   count: bearish },
  ]

  return (
    <div ref={ref} className={className}>
      {/* Header row */}
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <p className="eyebrow mb-1" style={{ color: 'var(--accent-red)' }}>// MARKET SENTIMENT</p>
          <h3 className="font-display text-3xl" style={{ color: 'var(--text-primary)' }}>
            SIGNAL DISTRIBUTION
          </h3>
        </div>
        <span className="font-display text-2xl" style={{ color: sentimentColor }}>
          {sentiment}
        </span>
      </div>

      {/* Bar */}
      <div
        className="flex rounded overflow-hidden mb-4"
        style={{ height: 10, background: 'var(--bg-elevated)', gap: 2 }}
        role="img"
        aria-label={`Market sentiment: ${pctBullish.toFixed(0)}% bullish, ${pctNeutral.toFixed(0)}% neutral, ${pctBearish.toFixed(0)}% bearish`}
      >
        {segments.map(seg => (
          <motion.div
            key={seg.label}
            initial={{ width: 0 }}
            animate={{ width: isVisible ? `${seg.pct}%` : 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
            style={{ background: seg.color, borderRadius: 2 }}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-6 flex-wrap">
        {segments.map(seg => (
          <div key={seg.label} className="flex items-center gap-2">
            <span
              className="inline-block rounded-sm"
              style={{ width: 10, height: 10, background: seg.color }}
              aria-hidden="true"
            />
            <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>
              {seg.label}
            </span>
            <span className="font-mono text-xs font-semibold" style={{ color: seg.color }}>
              {seg.pct.toFixed(0)}%
            </span>
            <span className="font-mono text-xs" style={{ color: 'var(--text-muted)', opacity: 0.5 }}>
              ({seg.count})
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MarketSentiment
