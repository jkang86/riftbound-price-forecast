import { NavLink } from 'react-router-dom'

const FOOTER_LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/cards',     label: 'Explorer' },
  { to: '/models',    label: 'Models' },
  { to: '/meta',      label: 'Meta' },
]

/**
 * Site footer — logo mark, nav links, attribution, copyright.
 */
export function Footer() {
  return (
    <footer
      className="px-8 md:px-16 py-12"
      style={{
        background: 'var(--bg-surface)',
        borderTop: '1px solid var(--border-subtle)',
      }}
    >
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
        {/* Logo mark */}
        <div>
          <span
            className="font-display text-4xl leading-none"
            style={{ color: 'var(--accent-red)' }}
          >
            RM
          </span>
          <p className="font-mono text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
            RIFTBOUND MARKET INTELLIGENCE
          </p>
        </div>

        {/* Nav */}
        <nav aria-label="Footer navigation">
          <ul className="flex flex-wrap gap-6 list-none m-0 p-0">
            {FOOTER_LINKS.map(({ to, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  className="font-ui font-semibold text-xs tracking-widest uppercase no-underline"
                  style={({ isActive }) => ({
                    color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                  })}
                >
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* Attribution + copyright */}
        <div className="text-right">
          <p className="font-mono text-xs mb-1" style={{ color: 'var(--text-muted)', opacity: 0.55 }}>
            Data sourced from TCGCSV
          </p>
          <p className="font-mono text-xs" style={{ color: 'var(--text-muted)', opacity: 0.55 }}>
            Not affiliated with Riot Games or TCGPlayer
          </p>
          <p className="font-mono text-xs mt-2" style={{ color: 'var(--text-muted)', opacity: 0.35 }}>
            © 2026 Joseph Kang
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
