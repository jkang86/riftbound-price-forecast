import { useState, useEffect } from 'react'

const BASE = import.meta.env.VITE_DATA_BASE_URL ?? '/data'

/**
 * Fetches forecasts.json and returns a single card's forecast by id.
 */
// Returns undefined while loading, null when loaded but no forecast exists, or the forecast object.
export function useCardForecast(id) {
  const [forecast, setForecast] = useState(undefined)

  useEffect(() => {
    if (!id) return
    setForecast(undefined)
    fetch(`${BASE}/forecasts.json`)
      .then(r => r.json())
      .then(data => {
        const match = data.forecasts?.find(f => f.card_id === id) ?? null
        setForecast(match)
      })
      .catch(() => setForecast(null))
  }, [id])

  return forecast
}
