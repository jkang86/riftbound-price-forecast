import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="px-3 py-2"
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        fontFamily: 'JetBrains Mono, monospace',
      }}
    >
      <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{formatDate(label)}</p>
      <p className="text-sm font-semibold" style={{ color: 'var(--accent-gold)' }}>
        ${Math.round(payload[0].value).toLocaleString()}
      </p>
    </div>
  )
}

export function MarketOverviewChart({ history = [], height = 280 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={history} margin={{ top: 8, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="capGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="var(--accent-gold)" stopOpacity={0.25} />
            <stop offset="100%" stopColor="var(--accent-gold)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="var(--border-subtle)"
          vertical={false}
        />
        <XAxis
          dataKey="week"
          tickFormatter={formatDate}
          tick={{ fill: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
          tick={{ fill: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          width={44}
          domain={['auto', 'auto']}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--accent-gold)', strokeWidth: 1, strokeDasharray: '4 4' }} />
        <Area
          type="monotone"
          dataKey="total_market_cap"
          stroke="var(--accent-gold)"
          strokeWidth={2}
          fill="url(#capGradient)"
          dot={false}
          activeDot={{ r: 4, fill: 'var(--accent-gold)', stroke: 'var(--bg-primary)', strokeWidth: 2 }}
          animationDuration={1200}
          animationEasing="ease-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default MarketOverviewChart
