import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { BroadcastTicker } from './BroadcastTicker'
import { LiveDot } from './LiveDot'
import { Footer } from './Footer'

const TICKER_ITEMS = [
  { name: 'Ahri - Nine-Tailed Fox (Metal)',         price: 4999.99, delta:  0.0 },
  { name: 'Ahri - Inquisitive (Signature)',          price: 2717.05, delta: -0.5 },
  { name: "Kai'Sa - Daughter of the Void (Sig)",    price: 2360.00, delta:  1.4 },
  { name: 'Irelia - Fervent (Signature)',            price: 1653.22, delta: -0.2 },
  { name: 'Vayne - Hunter (Signature)',              price: 1217.01, delta:  0.0 },
  { name: 'Jinx - Loose Cannon (Signature)',         price:  960.52, delta:  0.0 },
  { name: 'Viktor - Herald of the Arcane (Sig)',    price:  778.85, delta:  0.0 },
  { name: 'Darius - Hand of Noxus (Signature)',     price:  744.55, delta:  0.0 },
]

const NAV_LINKS = [
  { to: '/',          label: 'HOME',      end: true },
  { to: '/dashboard', label: 'DASHBOARD', end: false },
  { to: '/cards',     label: 'EXPLORER',  end: false },
  { to: '/models',    label: 'MODELS',    end: false },
  { to: '/meta',      label: 'META',      end: false },
]

export default function Layout() {
  const location = useLocation()
  const isDashboard = location.pathname === '/dashboard'

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Ticker strip — fixed at very top */}
      <div className="fixed top-0 left-0 right-0" style={{ zIndex: 201 }}>
        <BroadcastTicker items={TICKER_ITEMS} />
      </div>

      {/* Nav — fixed below ticker */}
      <nav
        aria-label="Primary"
        className="fixed left-0 right-0 flex items-center justify-between px-6 h-14"
        style={{
          top: 32,
          zIndex: 200,
          background: 'rgba(10,10,10,0.90)',
          backdropFilter: 'blur(12px) saturate(140%)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        {/* Logo */}
        <NavLink
          to="/"
          className="flex items-center gap-2 no-underline"
          aria-label="Riftbound Market Intelligence — Home"
        >
          <span
            className="font-display text-lg leading-none px-2 py-0.5 rounded"
            style={{ background: 'var(--accent-red)', color: '#fff', letterSpacing: '0.05em' }}
            aria-hidden="true"
          >
            RM
          </span>
          <span className="font-display text-base tracking-widest hidden sm:block" style={{ color: 'var(--text-primary)' }}>
            RIFTBOUND
          </span>
        </NavLink>

        {/* Nav links */}
        <ul className="hidden md:flex items-center gap-6 list-none m-0 p-0">
          {NAV_LINKS.map(({ to, label, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className="nav-link font-ui font-semibold text-xs tracking-widest uppercase no-underline"
                style={({ isActive }) => ({
                  color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                })}
              >
                {({ isActive }) => (
                  <span aria-current={isActive ? 'page' : undefined}>{label}</span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {isDashboard && <LiveDot />}
          {/* Hamburger placeholder — Phase 9 mobile polish */}
          <button
            className="md:hidden font-mono text-xs p-1"
            style={{ color: 'var(--text-muted)', border: '1px solid var(--border-subtle)', background: 'transparent' }}
            aria-label="Open navigation menu"
            aria-expanded="false"
          >
            ☰
          </button>
        </div>
      </nav>

      {/* Page content — offset below ticker (32px) + nav (56px) */}
      <main className="pt-[88px]">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
