import { useEffect, useRef, useState } from 'react'
import { Info, Settings } from 'lucide-react'
import { hrefFor } from '../lib/router.js'
import { Wordmark } from './Brand.jsx'
import LocalExpertReadiness from '../components/LocalExpertReadiness.jsx'

// The review flow lives in two places: Studies (choose a scan) and the Workbench.
// Earlier development pages stay reachable from the settings menu, so nothing is lost.
const NAV = [
  ['studies', 'Studies'],
  ['workbench', 'Workbench'],
]
const MORE = [
  ['predict', 'Analyze a scan', 'Run the model on a prepared CT (needs the model worker)'],
  ['saved', 'Saved reviews', 'Reopen recorded review decisions'],
  ['research', 'Research', 'Literature search workspace'],
  ['training', 'Training', 'Recorded training runs'],
]

function SettingsMenu({ current, onNavigate }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)
  useEffect(() => {
    if (!open) return undefined
    const close = event => { if (!rootRef.current?.contains(event.target)) setOpen(false) }
    const escape = event => { if (event.key === 'Escape') setOpen(false) }
    document.addEventListener('pointerdown', close)
    document.addEventListener('keydown', escape)
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', escape) }
  }, [open])
  const onMorePage = MORE.some(([view]) => view === current)
  return (
    <div className="pw-settings" ref={rootRef}>
      <button type="button" className={`pw-icon-btn${open || onMorePage ? ' active' : ''}`} aria-haspopup="dialog" aria-expanded={open}
        onClick={() => setOpen(value => !value)} aria-label="Settings and tools" title="Settings and tools">
        <Settings size={17} aria-hidden="true" />
      </button>
      {open && (
        <div className="pw-settings__menu" role="dialog" aria-label="Settings and tools">
          <section>
            <h2>AI expert</h2>
            <p>Start the local literature search and answer model before asking questions.</p>
            <LocalExpertReadiness />
          </section>
          <section>
            <h2>More tools</h2>
            <ul>
              {MORE.map(([view, label, detail]) => (
                <li key={view}>
                  <a href={hrefFor({ view })} aria-current={current === view ? 'page' : undefined}
                    onClick={event => { setOpen(false); onNavigate(event, view) }}>
                    <strong>{label}</strong><small>{detail}</small>
                  </a>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  )
}

// Analyze talks to the on-demand model worker; the Workbench talks to live analysis of
// prepared studies. They are separate services, so name the one being reported.
const STATUS_LABELS = {
  predict: { online: 'Model worker connected', offline: 'Model worker not connected', checking: 'Checking model worker…' },
  workbench: { online: 'Live analysis connected', offline: 'Live analysis offline · saved results available', checking: 'Checking live analysis…' },
  run: { online: 'Prediction artifact verified', offline: 'Prediction artifact unavailable', checking: 'Verifying prediction artifact…' },
}

function ServiceStatus({ status, view }) {
  if (view === 'training') return <span className="pw-hint">Recorded experiment time</span>
  if (status === null) return <span className="pw-hint">Local research workspace</span>
  const labels = STATUS_LABELS[view] || STATUS_LABELS.workbench
  const label = labels[status] || labels.checking
  return (
    <span className={`pw-service pw-service--${status}`} role="status" aria-live="polite" title={label}>
      <i aria-hidden="true" />
      <span>{label}</span>
    </span>
  )
}

export default function AppShell({ route, navigate, activeStudy, activePrediction, endpointStatus, modelLabel, onAbout, children }) {
  function target(view) {
    return view === 'workbench'
      ? { view, study: activePrediction?.study || activeStudy, run: activePrediction?.run }
      : { view }
  }
  function go(event, view) {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button === 1) return
    event.preventDefault()
    navigate(target(view))
  }
  const current = route.view
  return (
    <div className="pw-app">
      <a className="pw-skip" href="#pw-main">Skip to content</a>
      <header className="pw-header">
        <Wordmark onClick={(event) => go(event, 'studies')} />
        <nav className="pw-nav" aria-label="Primary">
          {NAV.map(([view, label, short]) => (
            <a
              key={view}
              href={hrefFor(target(view))}
              className={current === view ? 'active' : ''}
              aria-current={current === view ? 'page' : undefined}
              onClick={(event) => go(event, view)}
            >
              {short ? <><span className="pw-nav__full">{label}</span><span className="pw-nav__short" aria-hidden="true">{short}</span></> : label}
            </a>
          ))}
        </nav>
        <div className="pw-header__end">
          <ServiceStatus status={endpointStatus} view={route.run || route.invalidRun ? 'run' : route.view} />
          <SettingsMenu current={current} onNavigate={go} />
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
