import React, { useEffect, useRef, useState } from 'react'
import { predictionCatalog, predictStudy, disposePrediction } from '../lib/onDemandPrediction.js'
import SavedPredictionView from './SavedPredictionView.jsx'

export default function OnDemandPredictionView({ onServiceStatus } = {}) {
  const [catalog, setCatalog] = useState(null)
  const [caseId, setCaseId] = useState('')
  const [error, setError] = useState('')
  const [status, setStatus] = useState('idle')
  const [reviewDirty, setReviewDirty] = useState(false)
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
  return <section style={{ padding: 24 }} aria-label="On-demand prediction">
    <h1>Analyze a scan</h1>
    <p>Run the model once, then inspect and measure the same predicted outline. Measurement questions reuse this result.</p>
    {catalog && !catalog.configured && <p role="status">The current model worker is not connected yet. No prediction will run until its checkpoint and input catalog are configured.</p>}
    <label>Scan <select value={caseId} onChange={e => select(e.target.value)}>
      <option value="">Choose a scan</option>
      {catalog?.cases.map(c => <option key={c.case_id} value={c.case_id}>{c.case_id} · pancreas-assisted</option>)}
    </select></label>{' '}
    <button disabled={!catalog?.configured || !caseId || busy} onClick={predict}>{result ? 'Run again' : 'Run prediction'}</button>{' '}
    {busy && <button onClick={() => { stop(); setStatus('cancelled'); setResult(null) }}>Cancel prediction</button>}
    <p role="status">{busy ? (status === 'queued' ? 'Starting prediction…' : 'Predicting the outline…') : status === 'cancelled' ? 'Prediction cancelled.' : ''}</p>
    {error && <p role="alert">{error}</p>}
    {result && <SavedPredictionView key={result.job_id} base={`/scan-inference/jobs/${result.job_id}/files`} expected={result} live onReviewDirty={setReviewDirty} />}
  </section>
}
