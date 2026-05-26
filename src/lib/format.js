export const formatPrice = n =>
  typeof n === 'number' ? `$${n.toFixed(2)}` : '—'

export const formatDelta = n => {
  if (typeof n !== 'number') return '—'
  const sign = n >= 0 ? '+' : ''
  return `${sign}${n.toFixed(1)}%`
}

const RARITY_ORDER = { Mythic: 0, Legend: 1, Epic: 2, Rare: 3, Common: 4 }

export const raritySort = (a, b) =>
  (RARITY_ORDER[a.rarity] ?? 9) - (RARITY_ORDER[b.rarity] ?? 9)
