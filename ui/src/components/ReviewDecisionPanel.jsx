import React, { useEffect, useRef, useState } from 'react'

const labels = { accept: 'Accept', edit_required: 'Needs correction', reject: 'Reject' }
const reasons = {
  contour_acceptable: 'Contours usable for research annotation', boundary_correction: 'Boundary needs correction',
  missed_lesion: 'Missed lesion', false_positive_lesion: 'False positive lesion', pancreas_localization_error: 'Pancreas location error',
  pancreas_contour_error: 'Pancreas contour error', measurement_error: 'Measurement error', insufficient_image_quality: 'Image quality prevents review', other: 'Other',
}
const allowed = action => action === 'accept' ? ['contour_acceptable'] : Object.keys(reasons).filter(r => r !== 'contour_acceptable' && (action === 'reject' || r !== 'insufficient_image_quality'))
export function reviewSource(base) {
  if (base === '/saved-prediction') return 'saved'
  let match = /^\/scan-inference\/jobs\/([a-f0-9]{32})\/files$/.exec(base)
  if (match) return `job/${match[1]}`
  match = /^\/review-records\/packages\/([a-f0-9]{64})\/files$/.exec(base)
  return match ? `archive/${match[1]}` : null
}
export async function reviewRequest(path, options = {}) {
  const response = await fetch(`/review-records/${path}`, { ...options, cache: 'no-store', signal: options.signal || AbortSignal.timeout(60000) })
  let data
  try { data = await response.json() } catch { throw new Error('Review service is unavailable. Your draft is still here.') }
  if (!response.ok) { const error = new Error(data.error || 'Review could not be saved. Your draft is still here.'); error.status = response.status; throw error }
  return data
}
function validRecord(record, hash) {
  const e = record?.event, r = record?.receipt
  return e?.case_package_id === `case-package:${hash}` && e.prediction_id === `prediction:${hash}`
    && Object.hasOwn(labels, e.action) && Number.isSafeInteger(e.revision) && e.revision > 0
    && /^review:[a-f0-9-]{36}$/.test(e.review_event_id) && Array.isArray(e.reason_codes) && e.reason_codes.every(k => Object.hasOwn(reasons,k))
    && typeof e.reviewer?.reviewer_id === 'string' && typeof e.recorded_at === 'string'
    && r?.review_event_id === e.review_event_id && r.revision === e.revision && r.sequence === e.revision
    && r.case_package_id === e.case_package_id && r.prediction_id === e.prediction_id && /^[a-f0-9]{64}$/.test(r.content_sha256)
    && r.location === `${hash}/event-${String(e.revision).padStart(6, '0')}.json`
}
export default function ReviewDecisionPanel({ base, manifestHash, manifest, onSaved, onDraftChange }) {
  const source = reviewSource(base)
  const [history, setHistory] = useState(null), [error, setError] = useState(''), [notice, setNotice] = useState('')
  const [reviewer, setReviewer] = useState(''), [action, setAction] = useState(''), [selected, setSelected] = useState([]), [note, setNote] = useState('')
  const [confirmation, setConfirmation] = useState(false), [busy, setBusy] = useState(false)
  const pending = useRef(null), alive = useRef(false)
  const endpoint = `targets/${source}`
  async function reload(signal) {
    const data = await reviewRequest(endpoint, { signal })
    if (data.manifest_sha256 !== manifestHash || data.case_package_id !== `case-package:${manifestHash}`
      || data.prediction_id !== `prediction:${manifestHash}` || !Array.isArray(data.history) || !data.history.every(r => validRecord(r, manifestHash))) throw new Error('Review target changed. Reload the prediction before saving.')
    if (alive.current) { setHistory(data.history); pending.current = null; setConfirmation(false); setError('') }
  }
  useEffect(() => {
    alive.current = true
    const controller = new AbortController()
    if (source) reload(controller.signal).catch(e => { if (!controller.signal.aborted) setError(e.message) })
    return () => { alive.current = false; controller.abort() }
  }, [source, manifestHash])
  useEffect(() => { onDraftChange?.(!!(action || note)); return () => onDraftChange?.(false) }, [action, note, onDraftChange])
  useEffect(() => {
    const warn = e => { e.preventDefault(); e.returnValue = '' }
    if (action || note || pending.current) window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [action, note])
  async function save() {
    setBusy(true); setError(''); setNotice('')
    if (!pending.current) pending.current = { request_id: crypto.randomUUID(), manifest_sha256: manifestHash,
      expected_latest_id: history.at(-1)?.event.review_event_id || null, reviewer: { reviewer_id: reviewer.trim(), role: 'research_operator' }, action, reason_codes: selected, note }
    try {
      const record = await reviewRequest(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(pending.current) })
      if (!validRecord(record, manifestHash) || record.event.revision !== history.length+1) throw new Error('Save acknowledgment could not be verified. Retry or reload history.')
      if (!alive.current) return
      setHistory([...history, record]); pending.current = null; setConfirmation(false); setAction(''); setSelected([]); setNote('')
      setNotice(`Saved locally — revision ${record.event.revision}. The exact prediction can be reopened from Saved prediction review.`)
      onSaved?.()
    } catch(e) { if (alive.current) {
      if ([400,403,404,409,507].includes(e.status)) { pending.current = null; setConfirmation(false) }
      setError(e.message)
    } }
    finally { if (alive.current) setBusy(false) }
  }
  if (!source) return null
  const valid = history !== null && reviewer.trim() && action && selected.length && (selected.includes('other') ? note.trim() : true)
  return <section aria-labelledby="review-decision-title" style={{ marginTop: 32, padding: 20, border: '1px solid #657184', borderRadius: 8 }}>
    <h2 id="review-decision-title">Record your review</h2>
    <p>Accept means usable for research annotation. Needs correction means editing is required outside this viewer. Reject means unusable. These decisions do not confirm a diagnosis.</p>
    {notice && <p role="status">{notice}</p>}
    {error && <p role="alert">{error}</p>}
    {history === null && !error && <p role="status">Loading recorded decisions…</p>}
    <button disabled={busy || !!pending.current} onClick={() => reload().catch(e => setError(e.message))}>Reload review history</button>
    {history !== null && <>
      <h3>Recorded history</h3>
      {history.length === 0 ? <p>No recorded decisions for this prediction.</p> : <ol>{history.map(({event, receipt}) => <li key={event.review_event_id}>
        <strong>Revision {event.revision}: {labels[event.action]}</strong> — {event.reviewer.reviewer_id} · {new Date(event.recorded_at).toLocaleString()}
        <p>{event.reason_codes.map(r => reasons[r]).join('; ')}</p>{event.note && <p style={{whiteSpace:'pre-wrap'}}>{event.note}</p>}
        <details><summary>Durable receipt</summary><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(receipt,null,2)}</pre></details>
      </li>)}</ol>}
      <form onSubmit={e => {e.preventDefault();setNotice('');setConfirmation(true)}}>
        <fieldset disabled={busy || confirmation}>
          <legend>{history.length ? 'Append a revised decision' : 'New decision'}</legend>
          <p><label>Your name <input required maxLength={120} value={reviewer} onChange={e => setReviewer(e.target.value)} /></label> · Research operator</p>
          <p><label>Decision <select required value={action} onChange={e => {setAction(e.target.value);setSelected(e.target.value === 'accept' ? ['contour_acceptable'] : [])}}>
            <option value="">Choose a decision</option>{Object.entries(labels).map(([key,label]) => <option key={key} value={key}>{label}</option>)}
          </select></label></p>
          {action && <fieldset><legend>Reasons (choose at least one)</legend>{allowed(action).map(key => <label key={key} style={{display:'block',margin:'8px 0'}}>
            <input type="checkbox" checked={selected.includes(key)} onChange={e => setSelected(e.target.checked ? [...selected,key] : selected.filter(k => k !== key))} /> {reasons[key]}
          </label>)}</fieldset>}
          <p><label>Review note {selected.includes('other') ? '(required)' : '(optional)'}<br/><textarea rows={3} maxLength={2000} value={note} required={selected.includes('other')} onChange={e => setNote(e.target.value)} style={{width:'100%'}} /></label></p>
          <button disabled={!valid} type="submit">Review before saving</button>
        </fieldset>
      </form>
      {confirmation && <div aria-label="Confirm review" style={{overflowWrap:'anywhere'}}>
        <h3>Confirm {labels[action]?.toLowerCase()} for {manifest.case_id}</h3>
        <p>Saving retains this CT, prediction, and provenance locally so you can reopen them. Earlier decisions remain in history. Drafts are not saved until a receipt appears.</p>
        <p>Package: <code>case-package:{manifestHash}</code><br/>Prediction: <code>prediction:{manifestHash}</code><br/>Model: <code>{manifest.model_sha256.segmenter}</code></p>
        <button disabled={busy} onClick={save}>{busy ? 'Saving…' : pending.current ? 'Retry same save' : 'Confirm and save locally'}</button>{' '}
        <button disabled={busy || !!pending.current} onClick={() => setConfirmation(false)}>Back to draft</button>
        {pending.current && <p>If a save is uncertain, retry the same request to recover its receipt before revising it.</p>}
      </div>}
    </>}
  </section>
}
