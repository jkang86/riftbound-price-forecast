/**
 * ▲/▼ percentage with green/red color.
 * Props: value (number), className
 */
export function Delta({ value, className = '' }) {
  if (typeof value !== 'number') {
    return <span className={`font-mono ${className}`} style={{ color: 'var(--text-muted)' }}>—</span>
  }

  const isPos = value >= 0
  const color = isPos ? 'var(--success)' : 'var(--danger)'
  const arrow = isPos ? '▲' : '▼'
  const sign  = isPos ? '+' : ''

  return (
    <span className={`font-mono ${className}`} style={{ color }}>
      {arrow} {sign}{value.toFixed(1)}%
    </span>
  )
}

export default Delta
