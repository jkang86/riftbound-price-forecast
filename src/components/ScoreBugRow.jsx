import { ScoreBug } from './ScoreBug'

/**
 * Horizontal row of ScoreBug blocks separated by 1px gaps.
 * Props: items (array of ScoreBug props), className
 */
export function ScoreBugRow({ items = [], className = '' }) {
  return (
    <div
      role="list"
      aria-label="Market statistics"
      className={`flex overflow-x-auto ${className}`}
      style={{ gap: '1px', background: 'var(--border-subtle)' }}
    >
      {items.map((item, i) => (
        <ScoreBug key={i} {...item} />
      ))}
    </div>
  )
}

export default ScoreBugRow
