import React, { useEffect, useMemo, useState } from 'react'
import NiivueViewer from './NiivueViewer.jsx'
import { loadSavedPrediction } from '../lib/savedPrediction.js'

export default function SavedPredictionView({ base = '/saved-prediction' }) {
  const [state, setState] = useState({ status: 'loading' })
  const [showPancreas, setShowPancreas] = useState(true)
  const [showLesion, setShowLesion] = useState(true)
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    let active = true, loaded
    setState({ status: 'loading' })
    loadSavedPrediction(base, controller.signal).then(result => {
      if (!active) { result.release(); return }
      loaded = result
      setState({ status: 'ready', base, revision, ...result })
    }).catch(error => { if (active) setState({ status: 'error', message: error.message }) })
    return () => { active = false; controller.abort(); loaded?.release() }
  }, [base, revision])
  const caseData = useMemo(() => state.manifest ? { case_id: state.manifest.case_id, files: { ct: 'ct.nii.gz', pred: 'prediction.nii.gz' } } : null, [state.manifest])
  const ready = state.status === 'ready' && state.base === base && state.revision === revision
  return <main style={{ padding: 24, maxWidth: 1400, margin: 'auto' }}>
    <h1>Saved prediction review</h1>
    <p>Development demonstration · Not for diagnosis</p>
    <button onClick={() => setRevision(n => n + 1)}>Reload saved package</button>
    {state.status === 'error' ? <p role="alert">{state.message}</p> : !ready && <p role="status">Loading and verifying saved package…</p>}
    {ready && <>
      <h2>{state.manifest.case_id}</h2>
      {state.manifest.warnings.map(w => <p key={w}>{w}</p>)}
      <p>Native CT with predicted pancreas (green) and lesion (red). Reference annotations are not loaded.</p>
      <label><input type="checkbox" checked={showPancreas} onChange={e => setShowPancreas(e.target.checked)} /> Predicted pancreas</label>{' '}
      <label><input type="checkbox" checked={showLesion} onChange={e => setShowLesion(e.target.checked)} /> Predicted lesion</label>
      <div style={{ height: '65vh', minHeight: 420 }}>
        <NiivueViewer key={`${base}:${revision}:${state.manifest.result_sha256}`} caseData={caseData}
          assetUrls={state.urls} nativeGeometry={state.manifest.geometry} ctRange={state.manifest.ct_window}
          showPancreas={showPancreas} showLesion={showLesion} label={`Saved CT and prediction for ${state.manifest.case_id}`} />
      </div>
      <details><summary>Case and model provenance</summary><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify({ case_id: state.manifest.case_id, models: state.manifest.model_sha256, source_ct: state.manifest.files.ct.content_sha256, prediction: state.manifest.files.pred.content_sha256, result: state.manifest.result_sha256, inference: state.manifest.inference_evidence_sha256 }, null, 2)}</pre></details>
    </>}
  </main>
}
