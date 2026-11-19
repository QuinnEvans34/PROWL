import { useEffect, useMemo, useState } from 'react'
import LiteratureSearchPanel from './LiteratureSearchPanel.jsx'
import ReviewWorkspace from './ReviewWorkspace.jsx'
import { predictionJobForReview } from '../lib/onDemandPrediction.js'
import { loadSavedPrediction } from '../lib/savedPrediction.js'

function NativeWorkspace({ job, loaded, caseItems, onSelectScan, onOpenLibrary, onReviewDirty }) {
  const { manifest, manifestHash, measurement } = loaded
  const [assistantPending, setAssistantPending] = useState(false)
  const [reviewStatus, setReviewStatus] = useState('unreviewed')
  const [surface, setSurface] = useState({ status: 'loading' })
  const caseId = manifest.case_id
  const caseData = useMemo(() => ({
    case_id: caseId,
    files: { ct: manifest.files.ct.uri, pred: manifest.files.pred.uri },
    spacing_mm: [0, 1, 2].map(axis => Math.hypot(...manifest.geometry.affine.slice(0, 3).map(row => row[axis]))),
  }), [manifest, caseId])
  const measured = measurement?.status === 'ready'
  const modelLabel = `Segmenter · ${manifest.model_sha256.segmenter.slice(0, 12)}`
  const typeLabel = manifest.prediction_mode === 'pancreas_assisted' ? 'Pancreas-assisted prediction' : 'CT-only prediction'
  const measurementContext = { key: manifestHash, available: measured }
  useEffect(() => {
    let worker
    const mesh = {}
    const unavailable = reason => setSurface({ status: 'unavailable', reason })
    try {
      worker = new Worker(new URL('../lib/predictionSurfaceWorker.js', import.meta.url), { type: 'module' })
      worker.onmessage = ({ data }) => {
        worker.terminate()
        if (data.error) { unavailable(data.error); return }
        for (const [anatomy, buffer] of Object.entries(data.surfaces || {}))
          mesh[anatomy] = URL.createObjectURL(new Blob([buffer], { type: 'application/octet-stream' }))
        if (!Object.keys(mesh).length) { unavailable('The prediction has no 3D outline.'); return }
        setSurface({ status: 'ready', mesh })
      }
      worker.onerror = () => {
        worker.terminate()
        unavailable('The verified 3D outline could not be prepared.')
      }
      worker.postMessage({ url: loaded.urls.pred, bytes: manifest.files.pred.bytes, geometry: manifest.geometry })
    } catch {
      unavailable('This browser could not prepare the verified 3D outline.')
    }
    return () => {
      worker?.terminate()
      Object.values(mesh).forEach(url => URL.revokeObjectURL(url))
    }
  }, [loaded, manifest])
  const verifiedPrediction = useMemo(() => ({
    ...loaded, urls: { ...loaded.urls, mesh: surface.mesh }, surfaceStatus: surface.status, surfaceError: surface.reason,
  }), [loaded, surface])
  function measure(context, signal) {
    signal?.throwIfAborted()
    if (context.key !== manifestHash || !measured)
      throw new Error(measurement?.reason || 'Verified measurements are unavailable for this prediction.')
    return { ...measurement, contextKey: manifestHash }
  }
  return <ReviewWorkspace
    caseId={caseId}
    caseData={caseData}
    caseItems={[
      { id: caseId, shortId: caseId, label: typeLabel, tone: 'neutral', status: 'unreviewed' },
      ...caseItems.filter(item => item.id !== caseId),
    ]}
    profile={{ label: typeLabel, eyebrow: 'Verified source CT', tone: 'neutral' }}
    hasLiveResult
    finding={{ lesionFlagged: measured ? measurement.lesionVoxels > 0 : undefined }}
    overlap={{}}
    modelLabel={modelLabel}
    verifiedPrediction={verifiedPrediction}
    predictionJob={job}
    onReviewDirty={onReviewDirty}
    reviewStatus={reviewStatus}
    onSetReviewStatus={setReviewStatus}
    assistantPending={assistantPending}
    askPanel={<LiteratureSearchPanel variant="panel" contextKey={manifestHash} contextLabel={caseId}
      onPendingChange={setAssistantPending} measurementContext={measurementContext} measure={measure} />}
    onSelectScan={id => { if (id !== caseId) onSelectScan(id) }}
    onOpenLibrary={onOpenLibrary}
  />
}

export default function VerifiedPredictionWorkspace({
  run, study, expected, caseItems, onSelectScan, onOpenLibrary, onAnalyze, onVerify, onReviewDirty,
}) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState({ phase: 'checking' })
  useEffect(() => {
    const controller = new AbortController()
    let loaded
    async function verify() {
      setState({ phase: 'checking' })
      onVerify(run, study, 'checking')
      try {
        const job = await predictionJobForReview(run, study, controller.signal, expected)
        const result = await loadSavedPrediction(job.base, controller.signal, job)
        if (controller.signal.aborted) { result.release(); return }
        loaded = result
        setState({ phase: 'online', job, loaded })
        onVerify(run, study, 'online')
      } catch (error) {
        if (controller.signal.aborted) return
        setState({ phase: 'offline', error: error.message })
        onVerify(run, study, 'offline')
      }
    }
    void verify()
    return () => { controller.abort(); loaded?.release() }
  }, [run, study, expected, attempt, onVerify])

  if (state.phase === 'online') return <NativeWorkspace job={state.job} loaded={state.loaded}
    caseItems={caseItems} onSelectScan={onSelectScan} onOpenLibrary={onOpenLibrary} onReviewDirty={onReviewDirty} />
  return <main className="pw-empty" aria-labelledby="run-review-title">
    <h1 id="run-review-title">{state.phase === 'offline' ? 'Prediction unavailable' : 'Verifying prediction'}</h1>
    {state.phase === 'offline' ? <>
      <p role="alert">{state.error}</p>
      <div className="pw-empty__actions">
        <button type="button" className="pw-btn pw-btn--primary" onClick={() => setAttempt(value => value + 1)}>Retry verification</button>
        <button type="button" className="pw-btn pw-btn--secondary" onClick={onAnalyze}>Open Analyze</button>
        <button type="button" className="pw-btn pw-btn--secondary" onClick={onOpenLibrary}>Browse studies</button>
      </div>
    </> : <p role="status">Checking the source CT, prediction mask, and measurement evidence for {study}…</p>}
  </main>
}
