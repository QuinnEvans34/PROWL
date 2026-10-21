import { Info } from 'lucide-react'
import { hrefFor } from '../lib/router.js'
import { Wordmark } from './Brand.jsx'

const NAV = [
  ['studies', 'Studies'],
  ['workbench', 'Workbench'],
  ['predict', 'Analyze'],
  ['saved', 'Saved reviews'],
  ['research', 'Research'],
]

function ServiceStatus({ status }) {
  if (status === null) return <span className="pw-hint">Local research workspace</span>
  const label = status === 'online'
    ? 'Live analysis connected'
    : status === 'offline'
      ? 'Live analysis offline · saved results available'
      : 'Checking live analysis…'
  return (
    <span className={`pw-service pw-service--${status}`} role="status" aria-live="polite">
      <i aria-hidden="true" />
      <span>{label}</span>
    </span>
  )
}

export default function AppShell({ route, navigate, activeStudy, endpointStatus, modelLabel, onAbout, children }) {
  function go(event, view) {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button === 1) return
    event.preventDefault()
    navigate(view === 'workbench' ? { view, study: activeStudy } : { view })
  }
  const current = route.view
  return (
    <div className="pw-app">
      <a className="pw-skip" href="#pw-main">Skip to content</a>
      <header className="pw-header">
        <Wordmark onClick={(event) => go(event, 'studies')} />
        <nav className="pw-nav" aria-label="Primary">
          {NAV.map(([view, label]) => (
            <a
              key={view}
              href={hrefFor(view === 'workbench' ? { view, study: activeStudy } : { view })}
              className={current === view ? 'active' : ''}
              aria-current={current === view ? 'page' : undefined}
              onClick={(event) => go(event, view)}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="pw-header__end">
          <ServiceStatus status={endpointStatus} />
          <button type="button" className="pw-icon-btn" onClick={onAbout} aria-label="About PROWL" title="About PROWL">
            <Info size={17} aria-hidden="true" />
          </button>
        </div>
      </header>
      <div className="pw-body" id="pw-main" tabIndex={-1}>
        {children}
      </div>
      <footer className="pw-footer">
        <span><strong>Research use</strong> · Human review required · Not a diagnosis</span>
        <span className="pw-footer__model">{modelLabel}</span>
      </footer>
    </div>
  )
}
