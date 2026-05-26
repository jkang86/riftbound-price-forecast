const STYLES = {
  Mythic: { color: '#E2012D', bg: 'rgba(226,1,45,0.12)',    border: 'rgba(226,1,45,0.30)' },
  Legend: { color: '#C9A84C', bg: 'rgba(201,168,76,0.14)',  border: 'rgba(201,168,76,0.35)' },
  Epic:   { color: '#A98BFF', bg: 'rgba(169,139,255,0.12)', border: 'rgba(169,139,255,0.30)' },
  Rare:   { color: '#5DB7FF', bg: 'rgba(93,183,255,0.12)',  border: 'rgba(93,183,255,0.30)' },
  Common: { color: '#9aa3ad', bg: 'rgba(154,163,173,0.12)', border: 'rgba(154,163,173,0.25)' },
}

/**
 * Rarity tier pill badge.
 * Props: kind ("Mythic"|"Legend"|"Epic"|"Rare"|"Common"), className
 */
export function Rarity({ kind, className = '' }) {
  const s = STYLES[kind] ?? STYLES.Common

  return (
    <span
      className={`eyebrow px-2 py-0.5 rounded ${className}`}
      style={{ color: s.color, background: s.bg, border: `1px solid ${s.border}` }}
    >
      {kind}
    </span>
  )
}

export default Rarity
