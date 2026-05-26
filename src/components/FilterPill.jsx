/**
 * Toggle pill for faction / rarity / signal filters.
 * Props: label, active (bool), onClick, className
 */
export function FilterPill({ label, active = false, onClick, className = '' }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={`eyebrow px-3 py-1 rounded-full cursor-pointer transition-all duration-150 ${className}`}
      style={
        active
          ? { background: 'var(--accent-red)', color: '#fff', border: '1px solid var(--accent-red)' }
          : { background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border-subtle)' }
      }
    >
      {label}
    </button>
  )
}

export default FilterPill
