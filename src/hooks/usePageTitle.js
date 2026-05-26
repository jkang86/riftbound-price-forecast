import { useEffect } from 'react'

const BASE = 'Riftbound Market Intelligence'

export function usePageTitle(page) {
  useEffect(() => {
    document.title = page ? `${page} · ${BASE}` : BASE
    return () => { document.title = BASE }
  }, [page])
}
