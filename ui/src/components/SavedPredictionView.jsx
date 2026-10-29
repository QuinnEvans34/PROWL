import React, { useCallback, useEffect, useMemo, useState } from 'react'
import NativeMeasurementPanel from './NativeMeasurementPanel.jsx'
import ReviewDecisionPanel, { reviewRequest } from './ReviewDecisionPanel.jsx'
import LiteratureSearchPanel from './LiteratureSearchPanel.jsx'
import NiivueViewer from './NiivueViewer.jsx'
import { loadSavedPrediction } from '../lib/savedPrediction.js'

export default function SavedPredictionView({ base: initialBase = '/saved-prediction', expected = null, live = false, onDemandHref = null, onReviewDirty, reviewHash = null, onSelectReview }) {
  const [dirty, setDirty] = useState(false)
  const changedDraft = useCallback(value => { setDirty(value); onReviewDirty?.(value) }, [onReviewDirty])
  const canLeaveDraft = () => !dirty || window.confirm('Discard this unsaved review draft? Recorded decisions will remain saved.')
  const [localReview, setLocalReview] = useState(null)
  const selectedReview = onSelectReview ? reviewHash : localReview
  const archivedBase = selectedReview ? `/review-records/packages/${selectedReview}/files` : null
  function selectReview(hash) {
    // Controlled navigation uses the shell's guard, avoiding a second confirmation.
    if (onSelectReview) onSelectReview(hash)
    else if (canLeaveDraft()) setLocalReview(hash)
  }
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
  const Root = live ? 'section' : 'main'
  return <Root className={`pw-saved${live ? ' pw-saved--live' : ''}`}>
    <header className="pw-saved__head">
      <div>
        <p className="pw-eyebrow">{live ? 'On-demand result' : 'Saved reviews'}</p>
        <h1 className={live ? 'pw-saved__title--live' : 'pw-display'}>{live ? 'Prediction and measurements' : 'Saved prediction review'}</h1>
        <p className="pw-lede">Development demonstration · Not for diagnosis</p>
      </div>
      {!live && onDemandHref && <a className="pw-btn pw-btn--secondary" href={onDemandHref}>Run a prediction on demand</a>}
    </header>
    {!live && <section className="pw-saved__picker" aria-label="Reopen a reviewed prediction"><h2>Reopen a reviewed prediction</h2>
      <p className="pw-muted">Recorded decisions retain the original CT, contours, and provenance.</p>
      {archiveError && <p className="pw-notice pw-notice--warning">{archiveError}</p>}
      <div className="pw-saved__controls">
        <label className="pw-select">Prediction <select value={selectedReview || ''} onChange={e => selectReview(e.target.value || null)}>
          <option value="">Configured demonstration package</option>
          {selectedReview && !packages.some(p => p.manifest_sha256 === selectedReview) && <option value={selectedReview}>Requested saved prediction · {selectedReview.slice(0,8)}</option>}
          {packages.map(p => <option key={p.manifest_sha256} value={p.manifest_sha256}>{p.case_id} — {p.latest.action.replace('_',' ')} — revision {p.latest.revision} — {p.manifest_sha256.slice(0,8)}</option>)}
        </select></label>
        <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={refreshPackages}>Refresh saved reviews</button>
        <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={() => { if (canLeaveDraft()) setRevision(n => n + 1) }}>Reload saved package</button>
      </div>
    </section>}
    {live && <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={() => { if (canLeaveDraft()) setRevision(n => n + 1) }}>Recheck this result</button>}
    {state.status === 'error' ? <p className="pw-notice pw-notice--danger" role="alert">{state.message}</p> : !ready && <p className="pw-saved__loading" role="status">Loading and verifying saved package…</p>}
    {ready && <>
      <div className="pw-saved__case">
        <h2 className="pw-mono-id">{state.manifest.case_id}</h2>
        <div className="pw-saved__layers" role="group" aria-label="Prediction layers">
          <label className="pw-check"><input type="checkbox" checked={showPancreas} onChange={e => setShowPancreas(e.target.checked)} /><i className="pw-swatch pw-swatch--pred-pancreas" aria-hidden="true" /> Predicted pancreas</label>
          <label className="pw-check"><input type="checkbox" checked={showLesion} onChange={e => setShowLesion(e.target.checked)} /><i className="pw-swatch pw-swatch--pred-lesion" aria-hidden="true" /> Predicted lesion</label>
        </div>
      </div>
      {(state.manifest.warnings.length > 0 || state.manifest.prediction_mode === 'pancreas_assisted') && <div className="pw-notice pw-saved__notes">
        <div>
          {state.manifest.warnings.map(w => <p key={w}>{w}</p>)}
          {state.manifest.prediction_mode === 'pancreas_assisted' && <p>Pancreas-assisted prediction: a provided pancreas outline defined the search region. Volumes measure the model’s output.</p>}
        </div>
      </div>}
      <p className="pw-fineprint">Native CT with predicted pancreas (green) and lesion (red). Reference annotations are not loaded.</p>
      <div className="pw-saved__viewer">
        <NiivueViewer key={`${base}:${revision}:${state.manifest.result_sha256}`} caseData={caseData}
          assetUrls={state.urls} nativeGeometry={state.manifest.geometry} ctRange={state.manifest.ct_window}
          showPancreas={showPancreas} showLesion={showLesion} label={`Saved CT and prediction for ${state.manifest.case_id}`} />
      </div>
      <div className="pw-saved__panels">
        {state.measurement && <div className="pw-saved__card"><NativeMeasurementPanel key={`${base}:${revision}:${state.manifest.result_sha256}`} measurement={state.measurement} live={live} /></div>}
        {state.measurement && <div className="pw-saved__card"><ReviewDecisionPanel key={`${base}:${state.manifestHash}`} base={base} manifestHash={state.manifestHash} manifest={state.manifest} onSaved={refreshPackages} onDraftChange={changedDraft} /></div>}
      </div>
      {state.measurement && <details className="pw-disclosure"><summary>Search supporting literature</summary><p className="pw-muted">General literature answers are independent of this scan. Use the measurement panel above for this prediction’s measurements.</p><LiteratureSearchPanel variant="panel" /></details>}
      <details className="pw-disclosure"><summary>Case and model provenance</summary><pre className="pw-saved__provenance">{JSON.stringify({ case_id: state.manifest.case_id, models: state.manifest.model_sha256, source_ct: state.manifest.files.ct.content_sha256, prediction: state.manifest.files.pred.content_sha256, result: state.manifest.result_sha256, inference: state.manifest.inference_evidence_sha256 }, null, 2)}</pre></details>
    </>}
  </Root>
}
