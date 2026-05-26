import { useState, useEffect } from 'react'

const BASE = import.meta.env.VITE_DATA_BASE_URL ?? '/data'

/**
 * Fetches cards.json + market.json. Returns null until both resolve.
 */
export function useMarketData() {
  const [data, setData] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch(`${BASE}/cards.json`).then(r => r.json()),
      fetch(`${BASE}/market.json`).then(r => r.json()),
    ])
      .then(([cards, market]) => setData({ cards, market }))
      .catch(console.error)
  }, [])

  return data
}
