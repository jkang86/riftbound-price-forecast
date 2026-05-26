import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Delta } from '../components/Delta'
import { Rarity } from '../components/Rarity'
import { Button } from '../components/Button'
import { useMeta } from '../hooks/useMeta'
import { usePageTitle } from '../hooks/usePageTitle'
import { staggerContainerVariants, cardRevealVariants } from '../lib/motionVariants'

const FACTION_COLORS = {
  Piltover: 'var(--accent-gold)',
  Ionia:    'var(--accent-red)',
  Noxus:    '#C84040',
  Demacia:  '#5DB7FF',
  Freljord: '#8FCFFF',
}

function DeckRow({ deck, index }) {
  return (
    <motion.tr
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: index * 0.05 }}
      style={{ background: index % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-elevated)' }}
    >
      <td className="py-3 pl-4 pr-6">
        <span
          className="font-display text-xl"
          style={{ color: deck.rank === 1 ? 'var(--accent-gold)' : 'var(--text-muted)', opacity: deck.rank === 1 ? 1 : 0.6 }}
        >
          #{deck.rank}
        </span>
      </td>
      <td className="py-3 pr-6">
        <p className="font-ui font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{deck.name}</p>
        <p className="font-mono text-xs mt-0.5" style={{ color: FACTION_COLORS[deck.faction] ?? 'var(--text-muted)', opacity: 0.8 }}>
          {deck.faction.toUpperCase()}
        </p>
      </td>
      <td className="py-3 pr-6">
        <span className="font-mono text-sm font-semibold" style={{ color: deck.win_rate >= 55 ? 'var(--success)' : 'var(--text-muted)' }}>
          {deck.win_rate.toFixed(1)}%
        </span>
      </td>
      <td className="py-3 pr-4">
        <span className="font-mono text-sm" style={{ color: 'var(--text-muted)', opacity: 0.7 }}>
          {deck.top8_appearances}
        </span>
      </td>
    </motion.tr>
  )
}

function InclusionBar({ pct }) {
  return (
    <div style={{ height: 4, background: 'var(--bg-elevated)', borderRadius: 2, marginTop: 6 }}>
      <motion.div
        initial={{ width: 0 }}
        whileInView={{ width: `${pct}%` }}
        viewport={{ once: true }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        style={{ height: '100%', background: 'var(--accent-gold)', borderRadius: 2 }}
      />
    </div>
  )
}

function TopCardTile({ card }) {
  return (
    <Link
      to={`/cards/${card.id}`}
      className="block p-4 no-underline"
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        transition: 'border-color 200ms, transform 200ms',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent-gold)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.transform = 'translateY(0)' }}
    >
      <div className="flex items-start justify-between mb-2">
        <Rarity rarity={card.rarity} />
        <span
          className="font-mono text-xs font-semibold"
          style={{ color: 'var(--accent-gold)' }}
        >
          {card.inclusion_pct.toFixed(0)}%
        </span>
      </div>
      <p className="font-ui font-semibold text-sm mb-0.5" style={{ color: 'var(--text-primary)', lineHeight: 1.3 }}>
        {card.name}
      </p>
      <p className="font-mono text-xs mb-2" style={{ color: FACTION_COLORS[card.faction] ?? 'var(--text-muted)', opacity: 0.8 }}>
        {card.faction.toUpperCase()}
      </p>
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs" style={{ color: 'var(--text-muted)', opacity: 0.55 }}>DECK INCLUSION</span>
        <Delta value={card.delta_7d} />
      </div>
      <InclusionBar pct={card.inclusion_pct} />
    </Link>
  )
}

function FactionBar({ faction, pct, total }) {
  const color = FACTION_COLORS[faction] ?? 'var(--accent-gold)'
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <span className="eyebrow" style={{ color }}>{faction.toUpperCase()}</span>
        <span className="font-mono text-xs font-semibold" style={{ color }}>
          {pct.toFixed(0)}%
        </span>
      </div>
      <div style={{ height: 6, background: 'var(--bg-elevated)', borderRadius: 2 }}>
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${pct}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          style={{ height: '100%', background: color, borderRadius: 2 }}
        />
      </div>
    </div>
  )
}

export default function MetaTracker() {
  usePageTitle('Meta Tracker')
  const meta = useMeta()

  const topDecks      = meta?.top_decks ?? []
  const topPlayed     = meta?.top_played_cards ?? []
  const factionBreak  = meta?.faction_breakdown ?? {}
  const factionTotal  = Object.values(factionBreak).reduce((s, n) => s + n, 0) || 1

  return (
    <div style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>

      {/* Header */}
      <section className="px-8 md:px-16 py-14" style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          >
            <p className="eyebrow mb-3" style={{ color: 'var(--accent-red)' }}>// DECK TRENDS</p>
            <h1 className="font-display text-5xl leading-none mb-3" style={{ color: 'var(--text-primary)' }}>
              META TRACKER
            </h1>
            <p className="font-body text-sm" style={{ color: 'var(--text-muted)', lineHeight: 1.7 }}>
              Weekly snapshot based on tournament results from RiftboundStats.
              {meta?.snapshot_week && (
                <span className="font-mono text-xs ml-2" style={{ color: 'var(--text-muted)', opacity: 0.5 }}>
                  WEEK OF {meta.snapshot_week.toUpperCase()}
                </span>
              )}
            </p>
          </motion.div>
        </div>
      </section>

      {/* Top Decks Table */}
      <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-primary)' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.4 }}
            className="mb-6"
          >
            <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// TOURNAMENT RESULTS</p>
            <h2 className="font-display text-3xl" style={{ color: 'var(--text-primary)' }}>TOP DECKS</h2>
          </motion.div>

          {!meta ? (
            <div className="flex flex-col gap-px">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 52, borderRadius: 2 }} />
              ))}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 2px' }}>
                <thead>
                  <tr>
                    {['RANK', 'DECK', 'WIN RATE', 'TOP 8'].map(h => (
                      <th key={h} className="eyebrow text-left pb-3 pr-6" style={{ color: 'var(--text-muted)', opacity: 0.55, fontWeight: 500 }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {topDecks.map((deck, i) => <DeckRow key={deck.rank} deck={deck} index={i} />)}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      {/* Top Played Cards */}
      <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.4 }}
            className="flex items-end justify-between mb-6 flex-wrap gap-4"
          >
            <div>
              <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// MOST PLAYED</p>
              <h2 className="font-display text-3xl" style={{ color: 'var(--text-primary)' }}>TOP INCLUDED CARDS</h2>
            </div>
            <span className="font-mono text-xs" style={{ color: 'var(--text-muted)', opacity: 0.5 }}>
              % OF DECKS INCLUDING CARD
            </span>
          </motion.div>

          {!meta ? (
            <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 140, borderRadius: 2 }} />
              ))}
            </div>
          ) : (
            <motion.div
              key="top-played-grid"
              variants={staggerContainerVariants}
              initial="initial"
              animate="enter"
              className="grid gap-4"
              style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}
            >
              {topPlayed.map(card => (
                <motion.div key={card.id} variants={cardRevealVariants}>
                  <TopCardTile card={card} />
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </section>

      {/* Faction Breakdown */}
      <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-primary)' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.4 }}
            className="mb-6"
          >
            <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// FACTION META</p>
            <h2 className="font-display text-3xl" style={{ color: 'var(--text-primary)' }}>REPRESENTATION</h2>
          </motion.div>

          <div className="max-w-lg">
            {Object.entries(factionBreak)
              .sort((a, b) => b[1] - a[1])
              .map(([faction, count]) => (
                <FactionBar
                  key={faction}
                  faction={faction}
                  pct={(count / factionTotal) * 100}
                  total={factionTotal}
                />
              ))
            }
          </div>

          <div className="mt-10 flex gap-4 flex-wrap">
            <Button as={Link} to="/cards" variant="ghost">EXPLORE CARDS →</Button>
            <Button as={Link} to="/dashboard" variant="ghost">MARKET DASHBOARD →</Button>
          </div>
        </div>
      </section>
    </div>
  )
}
