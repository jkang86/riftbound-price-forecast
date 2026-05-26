import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { MetricBar } from '../components/MetricBar'
import { Button } from '../components/Button'
import { useMarketData } from '../hooks/useMarketData'
import { usePageTitle } from '../hooks/usePageTitle'
import { staggerContainerVariants, cardRevealVariants } from '../lib/motionVariants'

const MODEL_COMPARISON = [
  { name: 'ARIMA',         rmse: 1.80,  mae: 1.64, r2: 0.9986, highlight: false },
  { name: 'PROPHET',       rmse: 2.89,  mae: 2.74, r2: 0.9963, highlight: true  },
  { name: 'RIDGE',         rmse: 17.91, mae: 3.34, r2: 0.9964, highlight: false },
  { name: 'RANDOM FOREST', rmse: 19.07, mae: 2.98, r2: 0.9959, highlight: false },
  { name: 'LASSO',         rmse: 33.83, mae: 5.72, r2: 0.9871, highlight: false },
  { name: 'XGBOOST',       rmse: 37.53, mae: 5.55, r2: 0.9841, highlight: false },
]

const FEATURE_IMPORTANCE = [
  { feature: 'PRICE LAG 1W',       pct: 94 },
  { feature: 'PRICE LAG 2W',       pct: 68 },
  { feature: 'ROLLING MEAN 4W',    pct: 52 },
  { feature: 'TOURNAMENT PLAY %',  pct: 31 },
  { feature: 'RARITY TIER',        pct: 18 },
  { feature: 'FACTION VOLATILITY', pct: 12 },
]

const RMSE_MAX  = Math.max(...MODEL_COMPARISON.map(m => m.rmse))
const MAE_MAX   = Math.max(...MODEL_COMPARISON.map(m => m.mae))

export default function Models() {
  usePageTitle('Model Intelligence')
  const marketData = useMarketData()
  const allCards   = marketData?.cards?.cards ?? []

  const sortedByR2 = [...allCards]
    .filter(c => c.signal)
    .sort((a, b) => (b.delta_7d_pct ?? 0) - (a.delta_7d_pct ?? 0))
    .slice(0, 5)

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
            <p className="eyebrow mb-3" style={{ color: 'var(--accent-red)' }}>// FORECAST MODELS</p>
            <h1 className="font-display text-5xl leading-none mb-3" style={{ color: 'var(--text-primary)' }}>
              MODEL INTELLIGENCE
            </h1>
            <p className="font-body text-sm max-w-lg" style={{ color: 'var(--text-muted)', lineHeight: 1.7 }}>
              Six models trained on 26 weeks of price history across 713 cards.
              Prophet is used for live forecasts. Median per-card RMSE and MAE reported.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Model Comparison Table */}
      <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-primary)' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="mb-8"
          >
            <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// COMPARISON</p>
            <h2 className="font-display text-3xl" style={{ color: 'var(--text-primary)' }}>
              MODEL LEADERBOARD
            </h2>
          </motion.div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 2px' }}>
              <thead>
                <tr>
                  {['MODEL', 'RMSE ↑ LOWER BETTER', 'MAE ↑ LOWER BETTER', 'R² ↑ HIGHER BETTER', 'ACTIVE'].map(h => (
                    <th
                      key={h}
                      className="eyebrow text-left pb-3 pr-6"
                      style={{ color: 'var(--text-muted)', opacity: 0.55, fontWeight: 500, whiteSpace: 'nowrap' }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MODEL_COMPARISON.map((m, i) => (
                  <motion.tr
                    key={m.name}
                    initial={{ opacity: 0, x: -8 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.35, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
                    style={{ background: m.highlight ? 'rgba(201,168,76,0.06)' : 'var(--bg-surface)' }}
                  >
                    <td
                      className="font-display text-lg py-3 pr-6 pl-4"
                      style={{
                        color: m.highlight ? 'var(--accent-gold)' : 'var(--text-primary)',
                        borderLeft: m.highlight ? '2px solid var(--accent-gold)' : '2px solid transparent',
                      }}
                    >
                      {m.name}
                    </td>
                    <td className="font-mono text-sm py-3 pr-6" style={{ color: i === 0 ? 'var(--success)' : 'var(--text-muted)' }}>
                      ${m.rmse.toFixed(2)}
                    </td>
                    <td className="font-mono text-sm py-3 pr-6" style={{ color: i === 0 ? 'var(--success)' : 'var(--text-muted)' }}>
                      ${m.mae.toFixed(2)}
                    </td>
                    <td className="font-mono text-sm py-3 pr-6" style={{ color: 'var(--accent-gold)' }}>
                      {m.r2.toFixed(4)}
                    </td>
                    <td className="py-3 pr-4">
                      {m.highlight && (
                        <span
                          className="eyebrow px-2 py-0.5"
                          style={{
                            background: 'rgba(201,168,76,0.15)',
                            color: 'var(--accent-gold)',
                            border: '1px solid rgba(201,168,76,0.3)',
                            borderRadius: 2,
                          }}
                        >
                          LIVE
                        </span>
                      )}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Metric Bars */}
      <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)' }}>
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col lg:flex-row gap-12">
            {/* RMSE bars */}
            <div className="flex-1">
              <p className="eyebrow mb-1" style={{ color: 'var(--accent-red)' }}>// RMSE BY MODEL</p>
              <h3 className="font-display text-2xl mb-6" style={{ color: 'var(--text-primary)' }}>
                PREDICTION ERROR
              </h3>
              {MODEL_COMPARISON.map(m => (
                <MetricBar
                  key={m.name}
                  label={m.name}
                  value={`$${m.rmse.toFixed(2)}`}
                  pct={(m.rmse / RMSE_MAX) * 100}
                  color={m.highlight ? 'var(--accent-gold)' : 'var(--accent-red)'}
                />
              ))}
              <p className="font-body text-xs mt-2" style={{ color: 'var(--text-muted)', opacity: 0.55, lineHeight: 1.6 }}>
                RMSE measures how far predictions deviate from actual prices.
                Bars show relative error — shorter is better.
              </p>
            </div>

            {/* R² bars */}
            <div className="flex-1">
              <p className="eyebrow mb-1" style={{ color: 'var(--accent-red)' }}>// R² BY MODEL</p>
              <h3 className="font-display text-2xl mb-6" style={{ color: 'var(--text-primary)' }}>
                EXPLANATORY POWER
              </h3>
              {MODEL_COMPARISON.map(m => (
                <MetricBar
                  key={m.name}
                  label={m.name}
                  value={m.r2.toFixed(4)}
                  pct={m.r2 * 100}
                  color={m.highlight ? 'var(--accent-gold)' : 'var(--success)'}
                />
              ))}
              <p className="font-body text-xs mt-2" style={{ color: 'var(--text-muted)', opacity: 0.55, lineHeight: 1.6 }}>
                R² of 0.9986 means the model explains 99.86% of price variance.
                All six models show strong fit on historical data.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Importance */}
      <section className="px-8 md:px-16 py-12" style={{ background: 'var(--bg-primary)' }}>
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.4 }}
            className="mb-8"
          >
            <p className="eyebrow mb-2" style={{ color: 'var(--accent-red)' }}>// RANDOM FOREST</p>
            <h2 className="font-display text-3xl" style={{ color: 'var(--text-primary)' }}>
              FEATURE IMPORTANCE
            </h2>
          </motion.div>

          <div className="max-w-lg">
            {FEATURE_IMPORTANCE.map(f => (
              <MetricBar
                key={f.feature}
                label={f.feature}
                value={`${f.pct}%`}
                pct={f.pct}
                color="var(--accent-gold)"
              />
            ))}
          </div>

          <div
            className="mt-8 p-4"
            style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', maxWidth: 520 }}
          >
            <p className="eyebrow mb-2" style={{ color: 'var(--text-muted)', opacity: 0.6 }}>NOTE</p>
            <p className="font-body text-sm" style={{ color: 'var(--text-muted)', lineHeight: 1.7 }}>
              <code style={{ color: 'var(--accent-gold)', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>market_price</code> was
              excluded from cross-sectional features — it's effectively lag_0w and dominated
              Random Forest importance at 97.7%, masking all other signals.
              Models use lag_1w, lag_2w, and rolling_mean_4w instead.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section
        className="px-8 md:px-16 py-12"
        style={{ background: 'var(--bg-surface)', borderTop: '1px solid var(--border-subtle)' }}
      >
        <div className="max-w-5xl mx-auto flex gap-4 flex-wrap">
          <Button as={Link} to="/cards" variant="ghost">EXPLORE CARDS →</Button>
          <Button as={Link} to="/dashboard" variant="ghost">MARKET DASHBOARD →</Button>
        </div>
      </section>
    </div>
  )
}
