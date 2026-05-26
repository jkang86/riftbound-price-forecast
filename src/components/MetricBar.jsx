import { motion } from 'framer-motion'
import { useIntersect } from '../hooks/useIntersect'

/**
 * Horizontal fill bar for a single metric (RMSE, MAE, R²).
 * Props: label, value (display string), pct (0–100 fill), color, sublabel
 */
export function MetricBar({ label, value, pct = 0, color = 'var(--accent-gold)', sublabel = '' }) {
  const [ref, visible] = useIntersect({ threshold: 0.3 })

  return (
    <div ref={ref} className="mb-5">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="eyebrow" style={{ color: 'var(--text-muted)', opacity: 0.7 }}>{label}</span>
        <div className="text-right">
          <span className="font-mono text-sm font-semibold" style={{ color }}>{value}</span>
          {sublabel && (
            <span className="font-mono text-xs ml-2" style={{ color: 'var(--text-muted)', opacity: 0.5 }}>
              {sublabel}
            </span>
          )}
        </div>
      </div>
      <div
        style={{
          height: 6,
          background: 'var(--bg-elevated)',
          borderRadius: 2,
          overflow: 'hidden',
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: visible ? `${pct}%` : 0 }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          style={{ height: '100%', background: color, borderRadius: 2 }}
        />
      </div>
    </div>
  )
}

export default MetricBar
