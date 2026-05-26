import { useState, useEffect } from 'react'

const BASE = import.meta.env.VITE_DATA_BASE_URL ?? '/data'

/**
 * Fetches meta.json — deck trends, top-played cards, faction breakdown.
 */
export function useMeta() {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch(`${BASE}/meta.json`)
      .then(r => r.json())
      .then(setData)
      .catch(console.error)
  }, [])

  return data
}
