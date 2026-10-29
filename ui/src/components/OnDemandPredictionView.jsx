import React, { useCallback, useEffect, useRef, useState } from 'react'
import { predictionCatalog, predictStudy, disposePrediction } from '../lib/onDemandPrediction.js'
import SavedPredictionView from './SavedPredictionView.jsx'

export default function OnDemandPredictionView({ onServiceStatus, onReviewDirty } = {}) {
  const [catalog, setCatalog] = useState(null)
  const [caseId, setCaseId] = useState('')
  const [error, setError] = useState('')
  const [status, setStatus] = useState('idle')
  const [reviewDirty, setReviewDirty] = useState(false)
  const changedReview = useCallback(value => { setReviewDirty(value); onReviewDirty?.(value) }, [onReviewDirty])
  const canLeaveReview = () => !reviewDirty || window.confirm('Discard this unsaved review draft? Recorded decisions will remain saved.')
  const [result, setResult] = useState(null)
  const active = useRef(null)
  useEffect(() => {
    const controller = new AbortController()
    predictionCatalog(controller.signal).then(c => {
      if (!Array.isArray(c.cases) || typeof c.configured !== 'boolean') throw new Error('Invalid inference catalog.')
      if (!controller.signal.aborted) { setCatalog(c); onServiceStatus?.(c.configured ? 'online' : 'offline') }
    }).catch(e => { if (!controller.signal.aborted) { setError(e.message); onServiceStatus?.('offline') } })
    return () => { controller.abort(); stop() }
  }, [onServiceStatus])
  function stop() {
    const previous = active.current
    active.current = null
    previous?.controller.abort()
    if (previous?.id) void disposePrediction(previous.id)
  }
  function select(value) {
    if (!canLeaveReview()) return
    stop(); setCaseId(value); setResult(null); setStatus('idle'); setError('')
  }
  async function predict() {
    if (!canLeaveReview()) return
    stop(); setResult(null); setError(''); setStatus('queued')
    const task = { controller: new AbortController(), id: null }
    active.current = task
    try {
      const job = await predictStudy(caseId, task.controller.signal,
        value => { if (active.current === task) setStatus(value) },
        id => { task.id = id; if (active.current !== task) void disposePrediction(id) })
      if (active.current === task) setResult(job)
    } catch (e) {
      if (active.current === task) { setError(e.message); setStatus('failed') }
    }
  }
  const busy = ['queued', 'running'].includes(status)
  return <section className="pw-page pw-analyze" aria-label="On-demand prediction">
    <header className="pw-analyze__head">
      <p className="pw-eyebrow">Analyze</p>
      <h1 className="pw-display">Analyze a scan</h1>
      <p className="pw-lede">Run the model once, then inspect and measure the same predicted outline. Measurement questions reuse this result.</p>
    </header>
    <div className="pw-analyze__run">
      <label className="pw-select">Scan <select value={caseId} onChange={e => select(e.target.value)}>
        <option value="">Choose a scan</option>
        {catalog?.cases.map(c => <option key={c.case_id} value={c.case_id}>{c.case_id} · pancreas-assisted</option>)}
      </select></label>
      <button type="button" className="pw-btn pw-btn--primary" disabled={!catalog?.configured || !caseId || busy} onClick={predict}>{result ? 'Run again' : 'Run prediction'}</button>
      {busy && <button type="button" className="pw-btn pw-btn--ghost" onClick={() => { stop(); setStatus('cancelled'); setResult(null) }}>Cancel prediction</button>}
      <p className="pw-analyze__status" role="status">{busy ? (status === 'queued' ? 'Starting prediction…' : 'Predicting the outline…') : status === 'cancelled' ? 'Prediction cancelled.' : ''}</p>
    </div>
    {catalog && !catalog.configured && <p className="pw-notice pw-notice--warning" role="status">The current model worker is not connected yet. No prediction will run until its checkpoint and input catalog are configured.</p>}
    {error && <p className="pw-notice pw-notice--danger" role="alert">{error}</p>}
    {!result && !busy && <div className="pw-analyze__empty">
      <ol>
        <li><strong>Choose a scan</strong><span>Prepared CTs available to the local model worker.</span></li>
        <li><strong>Run the prediction</strong><span>The model outlines the pancreas and any suspected lesion once.</span></li>
        <li><strong>Inspect and record</strong><span>Measure the outline, then record your review decision locally.</span></li>
      </ol>
    </div>}
    {result && <SavedPredictionView key={result.job_id} base={`/scan-inference/jobs/${result.job_id}/files`} expected={result} live onReviewDirty={changedReview} />}
  </section>
}
