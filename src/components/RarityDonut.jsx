import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const RARITY_COLORS = {
  Showcase: '#E2012D',
  Promo:    '#C9A84C',
  Epic:     '#A98BFF',
  Rare:     '#5DB7FF',
  Uncommon: '#6dbf8a',
  Common:   '#9aa3ad',
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div
      className="px-3 py-2"
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        fontFamily: 'JetBrains Mono, monospace',
      }}
    >
      <p className="text-xs mb-0.5" style={{ color: 'var(--text-muted)' }}>{name}</p>
      <p className="text-sm font-semibold" style={{ color: RARITY_COLORS[name] ?? 'var(--accent-gold)' }}>
        {value} cards
      </p>
    </div>
  )
}

export function RarityDonut({ distribution = {}, size = 200 }) {
  const data = Object.entries(distribution).map(([name, value]) => ({ name, value }))
  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className="flex flex-col items-center gap-4">
      <div style={{ width: size, height: size, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius="58%"
              outerRadius="78%"
              dataKey="value"
              startAngle={90}
              endAngle={-270}
              strokeWidth={0}
              animationBegin={200}
              animationDuration={900}
            >
              {data.map(entry => (
                <Cell key={entry.name} fill={RARITY_COLORS[entry.name] ?? '#666'} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        {/* Center label */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
          }}
        >
          <span className="font-display text-2xl leading-none" style={{ color: 'var(--text-primary)' }}>
            {total}
          </span>
          <span className="font-mono text-xs mt-0.5" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>
            CARDS
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-col gap-1.5 w-full">
        {data.map(d => (
          <div key={d.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className="inline-block rounded-sm"
                style={{ width: 8, height: 8, background: RARITY_COLORS[d.name] ?? '#666' }}
                aria-hidden="true"
              />
              <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{d.name}</span>
            </div>
            <span className="font-mono text-xs font-semibold" style={{ color: RARITY_COLORS[d.name] ?? 'var(--accent-gold)' }}>
              {((d.value / total) * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RarityDonut
