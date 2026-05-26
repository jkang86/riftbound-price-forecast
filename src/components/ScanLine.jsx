import { useReducedMotion } from '../hooks/useReducedMotion'

/**
 * Decorative horizontal scan line sweeping the hero background.
 * Hidden when prefers-reduced-motion is set.
 */
export function ScanLine() {
  const prefersReduced = useReducedMotion()
  if (prefersReduced) return null

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden"
      style={{ zIndex: 0 }}
    >
      <div
        className="absolute left-0 right-0 h-px animate-scan-line"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, var(--accent-red) 50%, transparent 100%)',
          opacity: 0.35,
        }}
      />
    </div>
  )
}

export default ScanLine
