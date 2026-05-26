import { useMemo } from 'react'

const RARITIES = ['Mythic', 'Legend', 'Epic', 'Rare', 'Common']

function volatilityColor(v, max) {
  const t = Math.min(v / max, 1)
  if (t >= 0.7) return 'var(--accent-red)'
  if (t >= 0.4) return 'var(--warning)'
  if (t >= 0.2) return 'var(--accent-gold)'
  return 'var(--success)'
}

function volatilityBg(v, max) {
  const t = Math.min(v / max, 1)
  if (t >= 0.7) return 'rgba(226,1,45,0.15)'
  if (t >= 0.4) return 'rgba(255,176,32,0.13)'
  if (t >= 0.2) return 'rgba(201,168,76,0.12)'
  return 'rgba(76,175,80,0.10)'
}

export function VolatilityHeatmap({ data = [] }) {
  const factions = useMemo(
    () => [...new Set(data.map(d => d.faction))].sort(),
    [data]
  )

  const lookup = useMemo(() => {
    const m = {}
    data.forEach(d => { m[`${d.faction}|${d.rarity}`] = d.volatility })
    return m
  }, [data])

  const max = useMemo(() => Math.max(...data.map(d => d.volatility), 1), [data])

  if (!data.length) return null

  return (
    <div style={{ overflowX: 'auto' }}>
      <table
        style={{ borderCollapse: 'separate', borderSpacing: 2, width: '100%', minWidth: 360 }}
        aria-label="Volatility by faction and rarity"
      >
        <thead>
          <tr>
            <th
              className="font-mono text-xs text-left pb-2 pr-3"
              style={{ color: 'var(--text-muted)', opacity: 0.6, fontWeight: 500 }}
            >
              FACTION
            </th>
            {RARITIES.map(r => (
              <th
                key={r}
                className="font-mono text-xs pb-2 text-center"
                style={{ color: 'var(--text-muted)', opacity: 0.6, fontWeight: 500, minWidth: 56 }}
              >
                {r.slice(0, 3).toUpperCase()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {factions.map(faction => (
            <tr key={faction}>
              <td
                className="font-mono text-xs pr-3 whitespace-nowrap"
                style={{ color: 'var(--text-muted)', paddingTop: 2, paddingBottom: 2 }}
              >
                {faction.toUpperCase()}
              </td>
              {RARITIES.map(rarity => {
                const v = lookup[`${faction}|${rarity}`]
                if (v == null) {
                  return (
                    <td key={rarity} style={{ padding: 2 }}>
                      <div
                        style={{
                          height: 36,
                          borderRadius: 2,
                          background: 'var(--bg-elevated)',
                        }}
                      />
                    </td>
                  )
                }
                return (
                  <td key={rarity} style={{ padding: 2 }}>
                    <div
                      style={{
                        height: 36,
                        borderRadius: 2,
                        background: volatilityBg(v, max),
                        border: `1px solid ${volatilityColor(v, max)}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                      title={`${faction} ${rarity}: ${v.toFixed(1)}% volatility`}
                    >
                      <span
                        className="font-mono text-xs font-semibold"
                        style={{ color: volatilityColor(v, max) }}
                      >
                        {v.toFixed(1)}
                      </span>
                    </div>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Legend */}
      <div className="flex gap-4 mt-3 flex-wrap">
        {[
          { label: 'LOW < 20%',   color: 'var(--success)' },
          { label: 'MED 20–40%',  color: 'var(--accent-gold)' },
          { label: 'HIGH 40–70%', color: 'var(--warning)' },
          { label: 'EXTREME 70%+',color: 'var(--accent-red)' },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1.5">
            <span
              className="inline-block rounded-sm"
              style={{ width: 8, height: 8, background: color }}
              aria-hidden="true"
            />
            <span className="font-mono text-xs" style={{ color: 'var(--text-muted)', opacity: 0.65 }}>
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default VolatilityHeatmap
