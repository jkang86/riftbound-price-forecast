import { lazy, Suspense } from 'react'
import { createHashRouter, RouterProvider } from 'react-router-dom'
import Layout from './components/Layout'

const Landing     = lazy(() => import('./pages/Landing'))
const Dashboard   = lazy(() => import('./pages/Dashboard'))
const Explorer    = lazy(() => import('./pages/Explorer'))
const Detail      = lazy(() => import('./pages/Detail'))
const Models      = lazy(() => import('./pages/Models'))
const MetaTracker = lazy(() => import('./pages/MetaTracker'))

function PageShell({ children }) {
  return (
    <Suspense fallback={
      <div
        className="flex items-center justify-center"
        style={{ minHeight: 'calc(100vh - 88px)', background: 'var(--bg-primary)' }}
      >
        <span
          className="font-display text-2xl"
          style={{ color: 'var(--accent-gold)', opacity: 0.4, letterSpacing: '0.1em' }}
        >
          LOADING...
        </span>
      </div>
    }>
      {children}
    </Suspense>
  )
}

const router = createHashRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true,       element: <PageShell><Landing /></PageShell> },
      { path: 'dashboard', element: <PageShell><Dashboard /></PageShell> },
      { path: 'cards',     element: <PageShell><Explorer /></PageShell> },
      { path: 'cards/:id', element: <PageShell><Detail /></PageShell> },
      { path: 'models',    element: <PageShell><Models /></PageShell> },
      { path: 'meta',      element: <PageShell><MetaTracker /></PageShell> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
