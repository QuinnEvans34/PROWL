import { useMemo, useState } from 'react'

function Thumb({ src }) {
  const [failed, setFailed] = useState(false)
  return (
    <span className="pw-thumb">
      {src && !failed
        ? <img src={src} alt="" loading="lazy" onError={() => setFailed(true)} />
        : <FileStack size={16} aria-hidden="true" />}
    </span>
  )
}
import { ArrowRight, FileStack, Plus, Search } from 'lucide-react'
import { PantherBadge } from '../shell/Brand.jsx'

const STATUS = {
  analyzing: ['running', 'Analysis running'],
  ready: ['ready', 'Prediction ready'],
  saved: ['image', 'CT first · prediction saved'],
  image: ['image', 'Image ready'],
}

const MARK = { reviewed: 'Marked reviewed', discussion: 'Marked for discussion' }

export function studyStatus(study) {
  return STATUS[study.status] || STATUS.image
}

export default function StudiesPage({ studies, activeStudy, onOpen, onImport, importAvailable }) {
  const [query, setQuery] = useState('')
  const [reference, setReference] = useState('all')
  const [kind, setKind] = useState('all')

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase().replace(/\s+/g, '')
    return studies.filter((study) => (
      (!q || study.id.toLowerCase().replace(/_/g, '').includes(q.replace(/_/g, '')))
      && (reference === 'all' || (reference === 'available') === study.referenceAvailable)
      && (kind === 'all' || study.kind === kind)
    ))
  }, [studies, query, reference, kind])

  const filtered = rows.length !== studies.length
  // Shared series facts are stated once in the header instead of on every row.
  const spacings = [...new Set(studies.map((study) => study.spacingLabel))]
  const sharedSpacing = spacings.length === 1 ? spacings[0] : null

  return (
    <main className="pw-page pw-studies" aria-labelledby="studies-title">
      <section className="pw-welcome">
        <div className="pw-welcome__copy">
          <p className="pw-eyebrow">Your review workspace</p>
          <h1 className="pw-display">A clearer view. A considered review.</h1>
          <p className="pw-lede">Bring your study, explore the pancreas, and keep the evidence close.</p>
          <div className="pw-welcome__actions">
            <button type="button" className={`pw-btn ${importAvailable ? 'pw-btn--primary' : 'pw-btn--secondary'}`} onClick={onImport}>
              <Plus size={16} aria-hidden="true" /> Import CT study
            </button>
            {!importAvailable && <span className="pw-hint">DICOM import is not connected yet · prepared studies below are ready to review</span>}
          </div>
        </div>
        <div className="pw-welcome__mark">
          <PantherBadge size="hero" />
        </div>
      </section>

      <section className="pw-section" aria-labelledby="studies-title">
        <div className="pw-section__head">
          <div>
            <h2 id="studies-title">Studies</h2>
            <p className="pw-muted">
              {studies.length} prepared abdominal CT {studies.length === 1 ? 'study' : 'studies'} on this workstation{sharedSpacing ? ` · ${sharedSpacing}` : ''}.
            </p>
          </div>
          <div className="pw-filters" role="search">
            <label className="pw-search">
              <Search size={15} aria-hidden="true" />
              <span className="pw-sr-only">Search studies by ID</span>
              <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search study ID" />
            </label>
            <label className="pw-select">
              <span>Reference</span>
              <select value={reference} onChange={(event) => setReference(event.target.value)}>
                <option value="all">All</option>
                <option value="available">Available</option>
                <option value="none">Not provided</option>
              </select>
            </label>
            <label className="pw-select">
              <span>Type</span>
              <select value={kind} onChange={(event) => setKind(event.target.value)}>
                <option value="all">All studies</option>
                <option value="prepared">Prepared</option>
                <option value="validation">Validation examples</option>
              </select>
            </label>
          </div>
        </div>

        <div className="pw-table-wrap">
          <table className="pw-table">
            <caption className="pw-sr-only">Prepared CT studies{filtered ? `, ${rows.length} shown after filtering` : ''}</caption>
            <thead>
              <tr>
                <th scope="col">Study</th>
                <th scope="col" title="Reference annotations stay hidden until you choose to compare">Reference</th>
                <th scope="col">Status</th>
                <th scope="col"><span className="pw-sr-only">Open</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((study) => {
                const [tone, label] = studyStatus(study)
                const active = study.id === activeStudy
                return (
                  <tr key={study.id} className={active ? 'is-active' : ''} onClick={() => onOpen(study.id)}>
                    <td>
                      <div className="pw-study-cell">
                        <Thumb src={study.thumbnail} />
                        <span>
                          <strong className="pw-mono-id">{study.displayId}</strong>
                          <small>
                            {study.kind === 'validation' ? 'Validation example' : 'Prepared study'}
                            {!sharedSpacing && ` · ${study.spacingLabel}`}
                            {active && ' · Open in workbench'}
                          </small>
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="pw-cell-main">{study.referenceAvailable ? 'Available' : 'Not provided'}</span>
                    </td>
                    <td>
                      <span className={`pw-status pw-status--${tone}`}><i aria-hidden="true" />{label}</span>
                      {(study.draft || study.mark) && (
                        <small>
                          {[study.draft && 'Unsaved draft', study.mark && MARK[study.mark]].filter(Boolean).join(' · ')}
                        </small>
                      )}
                    </td>
                    <td className="pw-table__action">
                      <button
                        type="button"
                        className="pw-btn pw-btn--secondary pw-btn--sm"
                        onClick={(event) => { event.stopPropagation(); onOpen(study.id) }}
                        aria-label={`Review ${study.displayId}`}
                      >
                        {active ? 'Resume' : 'Review'} <ArrowRight size={14} aria-hidden="true" />
                      </button>
                    </td>
                  </tr>
                )
              })}
              {!rows.length && (
                <tr className="pw-table__empty">
                  <td colSpan={4}>No studies match these filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="pw-fineprint">
          Validation examples open with their saved prediction; prepared studies open on the CT alone until you show the saved prediction.
          Reference annotations, when available, stay hidden until you choose to compare.
        </p>
        <p className="pw-fineprint">
          Study IDs come from the prepared PanTS research set. No patient names or demographics are shown or stored.
          “Marked reviewed” labels are local browser notes, not durable review records.
        </p>
      </section>
    </main>
  )
}
