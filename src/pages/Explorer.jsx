import { useState, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FilterPill } from '../components/FilterPill'
import { MarketCard } from '../components/MarketCard'
import { SkeletonCard } from '../components/SkeletonCard'
import { Button } from '../components/Button'
import { useMarketData } from '../hooks/useMarketData'
import { useDebounce } from '../hooks/useDebounce'
import { usePageTitle } from '../hooks/usePageTitle'
import { staggerContainerVariants, cardRevealVariants } from '../lib/motionVariants'

const FACTIONS = ['Piltover', 'Demacia', 'Noxus', 'Freljord', 'Ionia']
const RARITIES = ['Mythic', 'Legend', 'Epic', 'Rare', 'Common']
const SIGNALS  = ['STRONG BUY', 'BUY', 'HOLD', 'WATCH', 'SELL']

const SORT_OPTIONS = [
  { value: 'delta_desc', label: 'Δ HIGH→LOW' },
  { value: 'delta_asc',  label: 'Δ LOW→HIGH' },
  { value: 'price_desc', label: '$ HIGH→LOW' },
  { value: 'price_asc',  label: '$ LOW→HIGH' },
  { value: 'name_asc',   label: 'A → Z' },
]

function applySort(cards, sort) {
  return [...cards].sort((a, b) => {
    switch (sort) {
      case 'delta_desc': return (b.delta_7d_pct ?? 0) - (a.delta_7d_pct ?? 0)
      case 'delta_asc':  return (a.delta_7d_pct ?? 0) - (b.delta_7d_pct ?? 0)
      case 'price_desc': return (b.current_price ?? 0) - (a.current_price ?? 0)
      case 'price_asc':  return (a.current_price ?? 0) - (b.current_price ?? 0)
      case 'name_asc':   return a.name.localeCompare(b.name)
      default:           return 0
    }
  })
}

function SidebarSection({ title, children }) {
  return (
    <div className="mb-6">
      <p className="eyebrow mb-3" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>{title}</p>
      {children}
    </div>
  )
}

function FilterSidebar({ factions, rarities, signals, priceMin, priceMax,
  setFactions, setRarities, setSignals, setPriceMin, setPriceMax, onReset, activeCount }) {
  const toggle = (arr, setArr, val) =>
    setArr(prev => prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val])

  return (
    <aside
      aria-label="Filter controls"
      className="p-5 h-fit"
      style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', minWidth: 200 }}
    >
      <div className="flex items-center justify-between mb-6">
        <p className="eyebrow" style={{ color: 'var(--text-primary)' }}>FILTERS</p>
        {activeCount > 0 && (
          <button
            onClick={onReset}
            className="font-mono text-xs"
            style={{ color: 'var(--accent-red)', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            RESET ({activeCount})
          </button>
        )}
      </div>

      <SidebarSection title="FACTION">
        <div className="flex flex-col gap-2">
          {FACTIONS.map(f => (
            <FilterPill key={f} label={f} active={factions.includes(f)} onClick={() => toggle(factions, setFactions, f)} />
          ))}
        </div>
      </SidebarSection>

      <SidebarSection title="RARITY">
        <div className="flex flex-col gap-2">
          {RARITIES.map(r => (
            <FilterPill key={r} label={r} active={rarities.includes(r)} onClick={() => toggle(rarities, setRarities, r)} />
          ))}
        </div>
      </SidebarSection>

      <SidebarSection title="SIGNAL">
        <div className="flex flex-col gap-2">
          {SIGNALS.map(s => (
            <FilterPill key={s} label={s} active={signals.includes(s)} onClick={() => toggle(signals, setSignals, s)} />
          ))}
        </div>
      </SidebarSection>

      <SidebarSection title="PRICE RANGE">
        <div className="flex gap-2 items-center">
          <div className="flex-1">
            <label className="font-mono text-xs mb-1 block" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>MIN $</label>
            <input
              type="number"
              min={0}
              value={priceMin}
              onChange={e => setPriceMin(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full font-mono text-xs px-2 py-1.5"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                outline: 'none',
                borderRadius: 2,
              }}
              placeholder="0"
            />
          </div>
          <span className="font-mono text-xs mt-4" style={{ color: 'var(--text-muted)' }}>–</span>
          <div className="flex-1">
            <label className="font-mono text-xs mb-1 block" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>MAX $</label>
            <input
              type="number"
              min={0}
              value={priceMax}
              onChange={e => setPriceMax(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full font-mono text-xs px-2 py-1.5"
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                outline: 'none',
                borderRadius: 2,
              }}
              placeholder="∞"
            />
          </div>
        </div>
      </SidebarSection>
    </aside>
  )
}

export default function Explorer() {
  usePageTitle('Explorer')
  const marketData = useMarketData()
  const allCards   = marketData?.cards?.cards ?? []
  const isLoading  = !marketData

  const [query,     setQuery]     = useState('')
  const [factions,  setFactions]  = useState([])
  const [rarities,  setRarities]  = useState([])
  const [signals,   setSignals]   = useState([])
  const [priceMin,  setPriceMin]  = useState('')
  const [priceMax,  setPriceMax]  = useState('')
  const [sortBy,    setSortBy]    = useState('delta_desc')
  const [drawerOpen, setDrawer]   = useState(false)

  const debouncedQuery = useDebounce(query, 300)

  const activeCount = useMemo(
    () => factions.length + rarities.length + signals.length + (priceMin !== '' ? 1 : 0) + (priceMax !== '' ? 1 : 0),
    [factions, rarities, signals, priceMin, priceMax]
  )

  const reset = useCallback(() => {
    setFactions([]); setRarities([]); setSignals([]); setPriceMin(''); setPriceMax(''); setQuery('')
  }, [])

  const filtered = useMemo(() => {
    let cards = allCards
    if (debouncedQuery) {
      const q = debouncedQuery.toLowerCase()
      cards = cards.filter(c => c.name.toLowerCase().includes(q) || c.faction?.toLowerCase().includes(q))
    }
    if (factions.length)  cards = cards.filter(c => factions.includes(c.faction))
    if (rarities.length)  cards = cards.filter(c => rarities.includes(c.rarity))
    if (signals.length)   cards = cards.filter(c => signals.includes(c.signal))
    if (priceMin !== '')  cards = cards.filter(c => (c.current_price ?? 0) >= Number(priceMin))
    if (priceMax !== '')  cards = cards.filter(c => (c.current_price ?? 0) <= Number(priceMax))
    return applySort(cards, sortBy)
  }, [allCards, debouncedQuery, factions, rarities, signals, priceMin, priceMax, sortBy])

  const sidebarProps = { factions, rarities, signals, priceMin, priceMax,
    setFactions, setRarities, setSignals, setPriceMin, setPriceMax, onReset: reset, activeCount }

  return (
    <div style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
      <div className="px-8 md:px-16 py-12 max-w-7xl mx-auto">

        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="mb-8"
        >
          <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// CARD CATALOG</p>
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <h1 className="font-display text-5xl leading-none" style={{ color: 'var(--text-primary)' }}>
              EXPLORER
            </h1>
            {!isLoading && (
              <span className="font-mono text-xs" style={{ color: 'var(--text-muted)', opacity: 0.55 }}>
                {filtered.length} / {allCards.length} CARDS
              </span>
            )}
          </div>
        </motion.div>

        {/* Search + Sort bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="flex gap-3 mb-6 flex-wrap items-center"
        >
          {/* Search */}
          <input
            type="search"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="SEARCH CARDS..."
            aria-label="Search cards by name or faction"
            className="flex-1 font-mono text-sm px-4 py-2.5"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              outline: 'none',
              minWidth: 200,
            }}
          />

          {/* Sort */}
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            aria-label="Sort cards"
            className="font-mono text-xs px-3 py-2.5 cursor-pointer"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              outline: 'none',
            }}
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          {/* Mobile filter button */}
          <button
            onClick={() => setDrawer(true)}
            className="flex md:hidden items-center gap-2 font-ui font-bold text-xs tracking-widest uppercase px-4 py-2.5 relative"
            aria-label="Open filters"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              cursor: 'pointer',
            }}
          >
            FILTERS
            {activeCount > 0 && (
              <span
                className="font-mono text-xs w-5 h-5 flex items-center justify-center rounded-full"
                style={{ background: 'var(--accent-red)', color: '#fff', fontSize: 10 }}
              >
                {activeCount}
              </span>
            )}
          </button>
        </motion.div>

        {/* Main layout: sidebar + grid */}
        <div className="flex gap-6">
          {/* Desktop sidebar */}
          <motion.div
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.15 }}
            className="hidden md:block w-52 flex-none"
          >
            <FilterSidebar {...sidebarProps} />
          </motion.div>

          {/* Card grid */}
          <div className="flex-1 min-w-0">
            {isLoading ? (
              <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
                {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
              </div>
            ) : filtered.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-24 text-center"
              >
                <p className="font-display text-4xl mb-3" style={{ color: 'var(--text-muted)', opacity: 0.4 }}>NO CARDS</p>
                <p className="font-mono text-sm mb-6" style={{ color: 'var(--text-muted)', opacity: 0.5 }}>
                  No cards match your filters.
                </p>
                <Button variant="ghost" onClick={reset}>RESET FILTERS</Button>
              </motion.div>
            ) : (
              <motion.div
                key={`${debouncedQuery}-${sortBy}-${factions.join()}-${rarities.join()}-${signals.join()}`}
                variants={staggerContainerVariants}
                initial="initial"
                animate="enter"
                className="grid gap-4"
                style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}
              >
                {filtered.map(card => (
                  <motion.div key={card.id} variants={cardRevealVariants}>
                    <MarketCard card={card} />
                  </motion.div>
                ))}
              </motion.div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile filter drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <>
            <motion.div
              key="overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setDrawer(false)}
              style={{
                position: 'fixed', inset: 0, zIndex: 300,
                background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
              }}
              aria-hidden="true"
            />
            <motion.div
              key="drawer"
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ ease: [0.16, 1, 0.3, 1], duration: 0.35 }}
              style={{
                position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 301,
                width: 280, overflowY: 'auto', background: 'var(--bg-primary)',
                borderRight: '1px solid var(--border-subtle)',
              }}
              role="dialog"
              aria-modal="true"
              aria-label="Filter drawer"
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <p className="eyebrow" style={{ color: 'var(--text-primary)' }}>FILTERS</p>
                  <button
                    onClick={() => setDrawer(false)}
                    className="font-mono text-sm"
                    style={{ color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}
                    aria-label="Close filters"
                  >
                    ✕
                  </button>
                </div>
                <FilterSidebar {...sidebarProps} />
                <Button variant="primary" className="w-full mt-4" onClick={() => setDrawer(false)}>
                  APPLY FILTERS
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
