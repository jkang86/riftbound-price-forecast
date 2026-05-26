import { Delta } from './Delta'
import { formatPrice } from '../lib/format'

/**
 * Infinite-scroll market tape. Duplicates items for a seamless loop.
 * Props: items ([{ name, price, delta }]), className
 */
export function BroadcastTicker({ items = [], className = '' }) {
  if (!items.length) return null

  const doubled = [...items, ...items]

  return (
    <div
      role="marquee"
      aria-live="polite"
      aria-label="Live market prices"
      className={`overflow-hidden flex items-center ${className}`}
      style={{
        height: 32,
        background: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
      }}
    >
      <div
        className="flex items-center whitespace-nowrap animate-ticker"
        style={{ width: 'max-content' }}
      >
        {doubled.map((item, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-2 px-4"
            style={{ height: 32 }}
          >
            <span className="font-ui font-semibold text-xs tracking-wider uppercase" style={{ color: 'var(--text-primary)' }}>
              {item.name}
            </span>
            <span className="font-mono text-xs" style={{ color: 'var(--text-primary)' }}>
              {formatPrice(item.price)}
            </span>
            <Delta value={item.delta} className="text-xs" />
            <span aria-hidden="true" style={{ color: 'var(--accent-gold)', opacity: 0.35 }}>·</span>
          </span>
        ))}
      </div>
    </div>
  )
}

export default BroadcastTicker
