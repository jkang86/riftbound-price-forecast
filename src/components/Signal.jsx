const STYLES = {
  'STRONG BUY': { color: '#4CAF50', bg: 'rgba(76,175,80,0.14)' },
  'BUY':        { color: '#4CAF50', bg: 'rgba(76,175,80,0.08)' },
  'HOLD':       { color: '#FFB020', bg: 'rgba(255,176,32,0.10)' },
  'WATCH':      { color: '#FFB020', bg: 'rgba(255,176,32,0.08)' },
  'SELL':       { color: '#FF5252', bg: 'rgba(255,82,82,0.12)' },
}

/**
 * BUY / SELL / HOLD signal pill.
 * Props: kind ("STRONG BUY"|"BUY"|"HOLD"|"WATCH"|"SELL"), className
 */
export function Signal({ kind, className = '' }) {
  const s = STYLES[kind] ?? STYLES.HOLD

  return (
    <span
      className={`eyebrow px-2 py-0.5 rounded ${className}`}
      style={{ color: s.color, background: s.bg }}
    >
      {kind}
    </span>
  )
}

export default Signal
