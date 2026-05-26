/**
 * Pulsing red dot with LIVE label.
 * Props: className
 */
export function LiveDot({ className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <span
        className="inline-block rounded-full animate-pulse-red"
        style={{ width: 7, height: 7, background: 'var(--accent-red)' }}
        aria-hidden="true"
      />
      <span
        className="font-ui font-bold text-xs tracking-widest uppercase"
        style={{ color: 'var(--accent-red)' }}
      >
        LIVE
      </span>
    </span>
  )
}

export default LiveDot
