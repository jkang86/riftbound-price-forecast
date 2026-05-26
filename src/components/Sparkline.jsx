/**
 * Inline SVG mini price chart.
 * Props: data (number[]), width, height, className
 */
export function Sparkline({ data = [], width = 120, height = 36, className = '' }) {
  if (data.length < 2) {
    return <div style={{ width, height }} className={className} aria-hidden="true" />
  }

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const pad = 2

  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (width - pad * 2)
    const y = pad + (1 - (v - min) / range) * (height - pad * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const trending = data[data.length - 1] >= data[0]
  const stroke = trending ? 'var(--success)' : 'var(--danger)'

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      aria-hidden="true"
    >
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  )
}

export default Sparkline
