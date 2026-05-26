import { useEffect, useState } from 'react'
import { useReducedMotion } from './useReducedMotion'

/**
 * Animates a number from 0 to target on mount. Respects prefers-reduced-motion.
 * Returns the current animated value.
 */
export function useCountUp(target, duration = 1000) {
  const prefersReduced = useReducedMotion()
  const [value, setValue] = useState(prefersReduced ? target : 0)

  useEffect(() => {
    if (!target || prefersReduced) { setValue(target); return }

    const start = performance.now()
    let raf

    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * target))
      if (progress < 1) raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration, prefersReduced])

  return value
}
