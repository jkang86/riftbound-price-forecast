import { Delta } from './Delta'
import { useCountUp } from '../hooks/useCountUp'

/**
 * HUD stat block — label, numeric value with count-up, optional delta.
 * Props: label, value (number|string), delta (number?), highlight (bool — uses red instead of gold border), className
 */
export function ScoreBug({ label, value, delta, highlight = false, countUp = false, className = '' }) {
  const animated = useCountUp(countUp && typeof value === 'number' ? value : 0)
  const display = countUp && typeof value === 'number' ? animated : value

  return (
    <div
      className={`px-4 py-3 min-w-[100px] ${className}`}
      style={{
        background: 'var(--bg-elevated)',
        borderLeft: `2px solid ${highlight ? 'var(--accent-red)' : 'var(--accent-gold)'}`,
      }}
    >
      <p className="eyebrow mb-1" style={{ color: 'var(--accent-gold)' }}>{label}</p>
      <p className="font-display text-2xl leading-none" style={{ color: 'var(--text-primary)' }}>
        {display}
      </p>
      {delta !== undefined && (
        <Delta value={delta} className="text-xs mt-1" />
      )}
    </div>
  )
}

export default ScoreBug
