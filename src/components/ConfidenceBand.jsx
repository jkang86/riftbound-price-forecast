import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import { SkeletonChart } from './SkeletonChart'

function buildChartData(history = [], forecast = []) {
  const historyPts = history.map(d => ({ date: d.date, price: d.price }))
  const forecastPts = forecast.map(d => ({
    date: d.date,
    yhat: d.yhat,
    yhat_upper: d.yhat_upper,
    yhat_lower: d.yhat_lower,
  }))
  return [...historyPts, ...forecastPts]
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="font-mono text-xs p-2 rounded"
      style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}
    >
      <p style={{ color: 'var(--text-muted)' }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color ?? 'var(--text-primary)' }}>
          {p.name}: ${Number(p.value).toFixed(2)}
        </p>
      ))}
    </div>
  )
}

/**
 * Prophet confidence band chart — 90d history + 30d forecast.
 * Props: data ({ history, forecast }), height, className
 */
export function ConfidenceBand({ data, height = 280, className = '' }) {
  if (!data) return <SkeletonChart height={height} className={className} />

  const chartData = buildChartData(data.history, data.forecast)

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="bandFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#C9A84C" stopOpacity={0.18} />
              <stop offset="95%" stopColor="#C9A84C" stopOpacity={0.04} />
            </linearGradient>
          </defs>

          <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />

          <XAxis
            dataKey="date"
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={v => `$${v}`}
            width={44}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Confidence band — upper fill, then lower erases bottom */}
          <Area
            dataKey="yhat_upper"
            fill="url(#bandFill)"
            stroke="none"
            dot={false}
            activeDot={false}
            name="Upper"
            legendType="none"
            connectNulls
          />
          <Area
            dataKey="yhat_lower"
            fill="var(--bg-surface)"
            fillOpacity={1}
            stroke="none"
            dot={false}
            activeDot={false}
            name="Lower"
            legendType="none"
            connectNulls
          />

          {/* Actual price line — gold */}
          <Line
            dataKey="price"
            stroke="var(--accent-gold)"
            strokeWidth={2}
            dot={false}
            name="Actual"
            connectNulls={false}
            animationBegin={200}
            animationDuration={800}
          />

          {/* Forecast line — red dashed */}
          <Line
            dataKey="yhat"
            stroke="var(--accent-red)"
            strokeWidth={1.5}
            strokeDasharray="4 3"
            dot={false}
            name="Forecast"
            connectNulls
            animationBegin={600}
            animationDuration={800}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

export default ConfidenceBand
