/**
 * Shimmer placeholder for chart components while data loads.
 * Props: height, className
 */
export function SkeletonChart({ height = 280, className = '' }) {
  return (
    <div
      className={`skeleton rounded ${className}`}
      style={{ height }}
      aria-hidden="true"
    />
  )
}

export default SkeletonChart
