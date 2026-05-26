import { Link } from 'react-router-dom'
import { Rarity } from './Rarity'
import { Signal } from './Signal'
import { Delta } from './Delta'
import { Sparkline } from './Sparkline'
import { formatPrice } from '../lib/format'

/**
 * Full market card — art placeholder, name, rarity, price, signal, sparkline.
 * Props: card ({ id, name, faction, rarity, current_price, delta_7d_pct, signal, sparkline }), className
 */
export function MarketCard({ card, className = '' }) {
  if (!card) return null

  return (
    <Link
      to={`/cards/${card.id}`}
      data-testid="market-card"
      className={`market-card block rounded overflow-hidden no-underline ${className}`}
      style={{ background: 'var(--bg-surface)' }}
    >
      {/* Art area */}
      <div
        className="relative flex items-center justify-center"
        style={{ height: 160, background: 'var(--bg-elevated)' }}
      >
        <span
          className="font-display text-4xl select-none"
          style={{ color: 'var(--border-subtle)', opacity: 0.4 }}
          aria-hidden="true"
        >
          ⚔
        </span>
        <div className="absolute top-2 right-2">
          <Rarity kind={card.rarity} />
        </div>
      </div>

      {/* Info */}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2 mb-0.5">
          <h3 className="font-ui font-semibold text-sm leading-tight" style={{ color: 'var(--text-primary)' }}>
            {card.name}
          </h3>
          <Signal kind={card.signal} className="flex-shrink-0" />
        </div>

        <p className="font-ui text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
          {card.faction}
          {card.rarity && ` · ${card.rarity}`}
        </p>

        <div className="flex items-end justify-between">
          <div>
            <p className="font-mono text-lg font-semibold leading-none" style={{ color: 'var(--text-primary)' }}>
              {formatPrice(card.current_price)}
            </p>
            <Delta value={card.delta_7d_pct} className="text-xs mt-1" />
          </div>
          <Sparkline data={card.sparkline} width={110} height={36} />
        </div>
      </div>
    </Link>
  )
}

export default MarketCard
