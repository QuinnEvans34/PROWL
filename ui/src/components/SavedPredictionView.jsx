import React, { useCallback, useEffect, useMemo, useState } from 'react'
import NativeMeasurementPanel from './NativeMeasurementPanel.jsx'
import ReviewDecisionPanel, { reviewRequest } from './ReviewDecisionPanel.jsx'
import LiteratureSearchPanel from './LiteratureSearchPanel.jsx'
import NiivueViewer from './NiivueViewer.jsx'
import { loadSavedPrediction } from '../lib/savedPrediction.js'

export default function SavedPredictionView({ base: initialBase = '/saved-prediction', expected = null, live = false, onDemandHref = null, onReviewDirty }) {
  const [dirty, setDirty] = useState(false)
  const changedDraft = useCallback(value => { setDirty(value); onReviewDirty?.(value) }, [onReviewDirty])
  const canLeaveDraft = () => !dirty || window.confirm('Discard this unsaved review draft? Recorded decisions will remain saved.')
  const [archivedBase, setArchivedBase] = useState(null)
  const base = live ? initialBase : archivedBase || initialBase
  const [packages, setPackages] = useState([])
  const [archiveError, setArchiveError] = useState('')
  const refreshPackages = () => reviewRequest('packages').then(data => { setPackages(data.packages); setArchiveError('') }).catch(() => setArchiveError('Saved review list is unavailable.'))
  useEffect(() => { if (!live) refreshPackages() }, [live])
  const [state, setState] = useState({ status: 'loading' })
  const [showPancreas, setShowPancreas] = useState(true)
  const [showLesion, setShowLesion] = useState(true)
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    let active = true, loaded
    setState({ status: 'loading' })
    loadSavedPrediction(base, controller.signal, expected).then(result => {
      if (!active) { result.release(); return }
      loaded = result
      setState({ status: 'ready', base, revision, ...result })
    }).catch(error => { if (active) setState({ status: 'error', message: error.message }) })
    return () => { active = false; controller.abort(); loaded?.release() }
  }, [base, revision, expected])
  const caseData = useMemo(() => state.manifest ? { case_id: state.manifest.case_id, files: { ct: 'ct.nii.gz', pred: 'prediction.nii.gz' } } : null, [state.manifest])
  const ready = state.status === 'ready' && state.base === base && state.revision === revision
  return <main style={{ padding: 24, maxWidth: 1400, margin: 'auto' }}>
    <h1>{live ? 'Prediction and measurements' : 'Saved prediction review'}</h1>
    <p>Development demonstration · Not for diagnosis</p>
    {!live && onDemandHref && <p><a href={onDemandHref}>Run a prediction on demand</a></p>}
    {!live && <section aria-label="Reopen a reviewed prediction"><h2>Reopen a reviewed prediction</h2>
      <p>Recorded decisions retain the original CT, contours, and provenance.</p>
      {archiveError && <p>{archiveError}</p>}
      <button onClick={refreshPackages}>Refresh saved reviews</button>{' '}
      <label>Prediction <select value={archivedBase || ''} onChange={e => { if (canLeaveDraft()) setArchivedBase(e.target.value || null) }}>
        <option value="">Configured demonstration package</option>
        {packages.map(p => <option key={p.manifest_sha256} value={`/review-records/packages/${p.manifest_sha256}/files`}>{p.case_id} — {p.latest.action.replace('_',' ')} — revision {p.latest.revision} — {p.manifest_sha256.slice(0,8)}</option>)}
      </select></label>
    </section>}
    <button onClick={() => { if (canLeaveDraft()) setRevision(n => n + 1) }}>{live ? 'Recheck this result' : 'Reload saved package'}</button>
    {state.status === 'error' ? <p role="alert">{state.message}</p> : !ready && <p role="status">Loading and verifying saved package…</p>}
    {ready && <>
      <h2>{state.manifest.case_id}</h2>
      {state.manifest.warnings.map(w => <p key={w}>{w}</p>)}
      {state.manifest.prediction_mode === 'pancreas_assisted' && <p>Pancreas-assisted prediction: a provided pancreas outline defined the search region. Volumes measure the model’s output.</p>}
      <p>Native CT with predicted pancreas (green) and lesion (red). Reference annotations are not loaded.</p>
      <label><input type="checkbox" checked={showPancreas} onChange={e => setShowPancreas(e.target.checked)} /> Predicted pancreas</label>{' '}
      <label><input type="checkbox" checked={showLesion} onChange={e => setShowLesion(e.target.checked)} /> Predicted lesion</label>
      <div style={{ height: '65vh', minHeight: 420 }}>
        <NiivueViewer key={`${base}:${revision}:${state.manifest.result_sha256}`} caseData={caseData}
          assetUrls={state.urls} nativeGeometry={state.manifest.geometry} ctRange={state.manifest.ct_window}
          showPancreas={showPancreas} showLesion={showLesion} label={`Saved CT and prediction for ${state.manifest.case_id}`} />
      </div>
      {state.measurement && <NativeMeasurementPanel key={`${base}:${revision}:${state.manifest.result_sha256}`} measurement={state.measurement} live={live} />}
      {state.measurement && <>
        <details style={{marginTop:24}}><summary>Search supporting literature</summary><p>General literature answers are independent of this scan. Use the measurement panel above for this prediction’s measurements.</p><LiteratureSearchPanel variant="panel" /></details>
        <ReviewDecisionPanel key={`${base}:${state.manifestHash}`} base={base} manifestHash={state.manifestHash} manifest={state.manifest} onSaved={refreshPackages} onDraftChange={changedDraft} />
      </>}
      <details><summary>Case and model provenance</summary><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify({ case_id: state.manifest.case_id, models: state.manifest.model_sha256, source_ct: state.manifest.files.ct.content_sha256, prediction: state.manifest.files.pred.content_sha256, result: state.manifest.result_sha256, inference: state.manifest.inference_evidence_sha256 }, null, 2)}</pre></details>
    </>}
  </main>
}
