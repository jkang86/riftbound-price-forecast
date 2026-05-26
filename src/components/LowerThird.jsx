import { motion } from 'framer-motion'

/**
 * Slide-up broadcast lower-third overlay.
 * Props: title, subtitle, tag (eyebrow label), delay (ms), className
 */
export function LowerThird({ title, subtitle, tag, delay = 0, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: '100%' }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: delay / 1000 }}
      className={`overflow-hidden ${className}`}
    >
      <div style={{ borderLeft: '3px solid var(--accent-gold)', paddingLeft: 12 }}>
        {tag && (
          <p className="eyebrow mb-1" style={{ color: 'var(--accent-gold)' }}>{tag}</p>
        )}
        <h2 className="font-display text-2xl leading-none" style={{ color: 'var(--text-primary)' }}>
          {title}
        </h2>
        {subtitle && (
          <p className="font-mono text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>
        )}
      </div>
    </motion.div>
  )
}

export default LowerThird
