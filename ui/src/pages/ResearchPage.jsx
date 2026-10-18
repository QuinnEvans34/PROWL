import { lazy, Suspense, useState } from 'react'
import { ArrowLeft, FlaskConical } from 'lucide-react'
import LiteratureSearchPanel from '../components/LiteratureSearchPanel.jsx'

// Older fixture/guided demonstrations stay available, but only behind an explicit entry.
const GuidedEvidencePanel = lazy(() => import('../components/GuidedEvidencePanel.jsx'))

export default function ResearchPage({ activeStudyLabel, onReturnToStudy }) {
  const [showDemos, setShowDemos] = useState(false)
  return (
    <main className="pw-page pw-research" aria-labelledby="research-title">
      <header className="pw-research__head">
        <p className="pw-eyebrow">PROWL Research</p>
        <h1 id="research-title" className="pw-display">Follow the evidence.</h1>
        <p className="pw-lede">Explore pancreatic literature without leaving your study behind.</p>
      </header>
      <div className="pw-research__grid">
        <div className="pw-research__main">
          <LiteratureSearchPanel variant="page" />
        </div>
        <aside className="pw-research__aside" aria-label="Context">
          <h2>Keep the context clear</h2>
          <p>Literature answers are general. They do not establish a finding in any study and do not see your scans.</p>
          {activeStudyLabel ? (
            <>
              <p className="pw-context-chip"><i aria-hidden="true" />{activeStudyLabel} · retained</p>
              <p>Your viewer, layers and review draft stay exactly where you left them.</p>
              <button type="button" className="pw-btn pw-btn--secondary" onClick={onReturnToStudy}>
                <ArrowLeft size={15} aria-hidden="true" /> Return to {activeStudyLabel}
              </button>
            </>
          ) : (
            <p className="pw-muted">No study is open. Research works on its own.</p>
          )}
        </aside>
      </div>

      <section className="pw-research__demos" aria-labelledby="demos-title">
        <div className="pw-research__demos-head">
          <div>
            <h2 id="demos-title"><FlaskConical size={16} aria-hidden="true" /> Earlier guided demonstrations</h2>
            <p className="pw-muted">Separate prototypes using the original two-review collection and fixed questions. Fixture services; not the current literature search.</p>
          </div>
          <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" aria-expanded={showDemos} aria-controls="pw-demos" onClick={() => setShowDemos((open) => !open)}>
            {showDemos ? 'Hide demonstrations' : 'Show demonstrations'}
          </button>
        </div>
        {showDemos && (
          <div id="pw-demos" className="pw-research__demos-body">
            <Suspense fallback={<p role="status">Loading demonstrations…</p>}>
              <GuidedEvidencePanel />
            </Suspense>
          </div>
        )}
      </section>
    </main>
  )
}
