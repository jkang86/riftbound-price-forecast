/**
 * Shimmer placeholder for MarketCard while data loads.
 * Props: className
 */
export function SkeletonCard({ className = '' }) {
  return (
    <div
      className={`rounded overflow-hidden ${className}`}
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}
      aria-hidden="true"
    >
      {/* Art area */}
      <div className="skeleton" style={{ height: 160 }} />

      <div className="p-3 flex flex-col gap-2">
        {/* Name + signal row */}
        <div className="flex justify-between items-center">
          <div className="skeleton rounded" style={{ height: 14, width: '55%' }} />
          <div className="skeleton rounded" style={{ height: 14, width: '22%' }} />
        </div>
        {/* Faction */}
        <div className="skeleton rounded" style={{ height: 10, width: '35%' }} />
        {/* Price + sparkline */}
        <div className="flex justify-between items-end mt-1">
          <div className="flex flex-col gap-1">
            <div className="skeleton rounded" style={{ height: 16, width: 60 }} />
            <div className="skeleton rounded" style={{ height: 10, width: 50 }} />
          </div>
          <div className="skeleton rounded" style={{ height: 36, width: 120 }} />
        </div>
      </div>
    </div>
  )
}

export default SkeletonCard
