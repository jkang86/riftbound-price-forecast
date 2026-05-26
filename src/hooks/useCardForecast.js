import { useState, useEffect } from 'react'

const BASE = import.meta.env.VITE_DATA_BASE_URL ?? '/data'

/**
 * Fetches forecasts.json and returns a single card's forecast by id.
 */
export function useCardForecast(id) {
  const [forecast, setForecast] = useState(null)

  useEffect(() => {
    if (!id) return
    fetch(`${BASE}/forecasts.json`)
      .then(r => r.json())
      .then(data => {
        const match = data.forecasts?.find(f => f.card_id === id) ?? null
        setForecast(match)
      })
      .catch(console.error)
  }, [id])

  return forecast
}
