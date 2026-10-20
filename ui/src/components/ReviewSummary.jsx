import { useMemo, useState } from 'react'
import { Copy, Download, FilePlus2, RefreshCw, Trash2 } from 'lucide-react'
import { createDraft, draftKey, generateObservations, hasHumanContent, isEdited, summaryText } from '../lib/summaryDraft.js'

// Durable persistence is a named dependency: no reviewed writer/receipt contract exists yet.
export const NO_PERSISTENCE = {
  available: false,
  reason: 'Durable saving isn’t connected yet. This draft lives only in this browser tab and is lost on reload.',
}

export default function ReviewSummary({ studyId, studyLabel, seriesKey = 'prepared-ct', seriesLabel, prediction, facts, drafts, onChange, persistence = NO_PERSISTENCE }) {
  const key = draftKey(studyId, seriesKey, prediction.key)
  const draft = drafts[key]
  const generated = useMemo(() => generateObservations({ ...facts, studyLabel, seriesLabel, prediction }), [facts, studyLabel, seriesLabel, prediction])
  const [pendingRegenerate, setPendingRegenerate] = useState(false)
  const [confirmDiscard, setConfirmDiscard] = useState(false)
  const [copyState, setCopyState] = useState('')
  const others = Object.values(drafts).filter((item) => item.studyId === studyId && item.key !== key && hasHumanContent(item))
  const stale = draft && draft.generated !== generated

  function update(patch) {
    onChange(key, { ...draft, ...patch })
  }

  function start() {
    onChange(key, createDraft({ key, studyId, prediction, generated }))
  }

  function regenerate() {
    if (isEdited(draft)) { setPendingRegenerate(true); return }
    update({ generated, observations: generated })
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(summaryText(draft))
      setCopyState('Copied')
    } catch {
      setCopyState('Copy unavailable in this browser')
    }
    window.setTimeout(() => setCopyState(''), 2500)
  }

  function download() {
    const blob = new Blob([summaryText(draft)], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${studyId}-review-draft.txt`
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  }

  return (
    <div className="pw-summary">
      <p className="pw-context-chip"><i aria-hidden="true" />{studyLabel} · {draft ? 'Editable draft' : 'No draft yet'}</p>
      <div className="pw-summary__head">
        <div>
          <h3 className="pw-panel-title">Review summary</h3>
          <p className="pw-muted">Shape the observations in your own words.</p>
        </div>
        {draft && <span className="pw-pill pw-pill--warning" title={persistence.reason}>Unsaved · session only</span>}
      </div>

      {others.map((item) => (
        <div key={item.key} className="pw-notice" role="note">
          <div>
            <strong>Draft for an earlier prediction</strong>
            <p>A draft written against “{item.predictionLabel}” is kept. It is not shown as current because the prediction changed.</p>
            {draft && item.notes.trim() && (
              <button type="button" className="pw-btn pw-btn--link" onClick={() => update({ notes: [draft.notes, item.notes].filter((text) => text.trim()).join('\n\n') })}>
                Copy its notes into this draft
              </button>
            )}
          </div>
        </div>
      ))}

      {!draft ? (
        <div className="pw-card">
          <p className="pw-muted">
            {facts.hasPrediction
              ? 'Start from the validated findings shown for this prediction. Nothing is inferred beyond them.'
              : 'No prediction is displayed, so the draft will contain no model-derived observations. You can still write notes.'}
          </p>
          <button type="button" className="pw-btn pw-btn--primary" onClick={start}>
            <FilePlus2 size={15} aria-hidden="true" /> Start draft from findings
          </button>
        </div>
      ) : (
        <>
          <label className="pw-field">
            <span>
              Draft observations
              <small>{isEdited(draft) ? 'Edited by you' : 'Generated from findings · editable'}</small>
            </span>
            <textarea value={draft.observations} rows={11} onChange={(event) => update({ observations: event.target.value })} />
          </label>

          {stale && !pendingRegenerate && (
            <p className="pw-notice pw-notice--warning" role="status">
              The findings changed since this draft was generated (for example, a reference comparison was opened).
              <button type="button" className="pw-btn pw-btn--link" onClick={regenerate}>Review the update</button>
            </p>
          )}

          {pendingRegenerate && (
            <div className="pw-card pw-regenerate" role="group" aria-label="Regenerate draft">
              <strong>Regenerating would replace your edited observations.</strong>
              <p className="pw-muted">Your notes are never changed. New generated text:</p>
              <pre>{generated}</pre>
              <div className="pw-row">
                <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm" onClick={() => { update({ generated, observations: generated }); setPendingRegenerate(false) }}>Replace my edits</button>
                <button type="button" className="pw-btn pw-btn--primary pw-btn--sm" onClick={() => { update({ generated }); setPendingRegenerate(false) }}>Keep my edits</button>
              </div>
            </div>
          )}

          <label className="pw-field">
            <span>Your notes <small>reviewer-authored</small></span>
            <textarea value={draft.notes} rows={5} placeholder="Add your review notes…" onChange={(event) => update({ notes: event.target.value })} />
          </label>

          <div className="pw-row pw-row--wrap">
            <button type="button" className="pw-btn pw-btn--primary pw-btn--sm" disabled={!persistence.available} title={persistence.reason}>Save review</button>
            <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm" onClick={copy}><Copy size={13} aria-hidden="true" /> Copy</button>
            <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm" onClick={download}><Download size={13} aria-hidden="true" /> Download .txt</button>
            <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={regenerate} title="Rebuild the generated observations from current findings"><RefreshCw size={13} aria-hidden="true" /> Regenerate</button>
            <span className="pw-hint" role="status" aria-live="polite">{copyState}</span>
          </div>
          <p className="pw-fine">{persistence.reason} Draft only · not a signed or saved clinical report.</p>

          <div className="pw-summary__discard">
            {confirmDiscard ? (
              <>
                <span>Discard this draft and your notes?</span>
                <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm" onClick={() => setConfirmDiscard(false)}>Keep</button>
                <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm pw-btn--danger" onClick={() => { onChange(key, null); setConfirmDiscard(false) }}>Discard</button>
              </>
            ) : (
              <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={() => setConfirmDiscard(true)}><Trash2 size={13} aria-hidden="true" /> Discard draft</button>
            )}
          </div>
        </>
      )}
    </div>
  )
}
