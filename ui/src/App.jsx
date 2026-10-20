import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Database, Microscope, Radio, ShieldCheck, X } from 'lucide-react'
import AppShell from './shell/AppShell.jsx'
import { PantherBadge } from './shell/Brand.jsx'
import StudiesPage from './pages/StudiesPage.jsx'
import ReviewWorkspace from './components/ReviewWorkspace.jsx'
import LiteratureSearchPanel from './components/LiteratureSearchPanel.jsx'
import { useRoute } from './lib/router.js'
import { hasHumanContent } from './lib/summaryDraft.js'
import ImportStudyDialog from './components/ImportStudyDialog.jsx'

const ValidationComparison = lazy(() => import('./components/ValidationComparison.jsx'))
const ResearchPage = lazy(() => import('./pages/ResearchPage.jsx'))
const SavedPredictionView = lazy(() => import('./components/SavedPredictionView.jsx'))

const BASE = '/cases'
const API_BASE = 'http://localhost:8000'
const STORAGE_KEY = 'pants-review-status-v1'
const MODEL_LABEL = 'Segmenter v1 · step 18000'

// Validation examples: prepared studies whose package permits immediate reference
// comparison. Historical scientific IDs and interpretations are unchanged.
const VALIDATION_IDS = ['PanTS_00009005', 'PanTS_00009016', 'PanTS_00009220']
const VALIDATION_SET = new Set(VALIDATION_IDS)

const VALIDATION_PROFILES = {
  PanTS_00009005: {
    label: 'Strong overlap',
    eyebrow: 'True-positive example',
    interpretation: 'The model finds the tumor and outlines it closely — lesion Dice 0.919, pancreas Dice 0.855.',
    strength: 'Correctly localized the lesion with a tight boundary around it.',
    limitation: 'The predicted boundary still differs slightly from the reference contour.',
    tone: 'positive',
  },
  PanTS_00009016: {
    label: 'Correctly silent',
    eyebrow: 'True-negative example',
    interpretation: 'The model segments the pancreas well (Dice 0.889) and raises no false alarm.',
    strength: 'Strong pancreas segmentation with no lesion predicted on a lesion-negative scan.',
    limitation: 'Correct silence on lesion-negative scans is the model’s least reliable behavior overall.',
    tone: 'positive',
  },
  PanTS_00009220: {
    label: 'Large false positive',
    eyebrow: 'Failure analysis',
    interpretation: 'A useful example of why detection specificity and human review remain important.',
    strength: 'Still produces a usable pancreas outline on a lesion-negative case.',
    limitation: 'Predicts roughly 51 cm³ of lesion where the reference has none.',
    tone: 'caution',
  },
}

const PREPARED_PROFILE = {
  label: 'Prepared study',
  eyebrow: 'Prepared CT',
  tone: 'neutral',
}

export function formatStudyId(caseId) {
  return caseId?.replace('PanTS_', 'PanTS ')
}

// Equivalent spherical diameter derived from a mask volume. It is NOT a measured
// lesion width or length and must always be labeled as derived.
function equivalentDiameterMm(volumeMm3) {
  if (!Number.isFinite(volumeMm3) || volumeMm3 <= 0) return null
  return Math.round(2 * Math.cbrt((3 * volumeMm3) / (4 * Math.PI)))
}

function formatScoreTime(date = new Date()) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
}

async function fetchJson(url, options = {}, timeoutMs = 5000) {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    if (!response.ok) throw new Error(`Endpoint returned ${response.status}`)
    return await response.json()
  } finally {
    window.clearTimeout(timeoutId)
  }
}

function readStoredStatuses() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function savedResultFor(caseId, cachedCase) {
  return {
    case_id: caseId,
    lesion_flagged: Boolean(cachedCase.pred_has_lesion),
    lesion_volume_mm3: Number.isFinite(cachedCase.lesion_volume_mm3) ? cachedCase.lesion_volume_mm3 : null,
    global_peak_lesion_confidence: Number.isFinite(cachedCase.confidence) ? cachedCase.confidence : null,
    inference_seconds: null,
    dice_pancreas: cachedCase.dice_pancreas,
    dice_lesion: cachedCase.dice_lesion,
  }
}

function ViewerSuspense({ children, label = 'Preparing medical viewer…' }) {
  return <Suspense fallback={<div className="pw-empty" role="status"><p>{label}</p></div>}>{children}</Suspense>
}

function WorkbenchEmpty({ onStudies, onImport, missingStudy }) {
  return (
    <main className="pw-empty" aria-labelledby="wb-empty-title">
      <PantherBadge size="empty" />
      <h1 id="wb-empty-title">{missingStudy ? 'Study not found' : 'No study open'}</h1>
      <p>{missingStudy
        ? `“${missingStudy}” is not in this workstation’s prepared studies.`
        : 'Open a prepared study to inspect the CT and its predicted outlines. Reviews without a reference annotation are complete reviews.'}</p>
      <div className="pw-empty__actions">
        <button type="button" className="pw-btn pw-btn--primary" onClick={onStudies}>Browse studies</button>
        <button type="button" className="pw-btn pw-btn--secondary" onClick={onImport}>Import CT</button>
      </div>
    </main>
  )
}

function AboutDialog({ onClose }) {
  const closeRef = useRef(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose
  useEffect(() => {
    const previous = document.activeElement
    closeRef.current?.focus()
    function onKey(event) { if (event.key === 'Escape') onCloseRef.current() }
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('keydown', onKey); previous?.focus?.() }
  }, [])
  return (
    <div className="pw-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="pw-dialog" role="dialog" aria-modal="true" aria-labelledby="about-title" onMouseDown={(event) => event.stopPropagation()}>
        <button ref={closeRef} type="button" className="pw-icon-btn pw-dialog__close" onClick={onClose} aria-label="Close about PROWL"><X size={17} /></button>
        <PantherBadge size="sm" />
        <h2 id="about-title" style={{ marginTop: 14 }}>About PROWL</h2>
        <p className="pw-muted">A pancreatic CT review workbench for research. PROWL shows model-proposed pancreas and possible-lesion outlines, optional reference annotations, and cited literature. The reviewer keeps judgment; PROWL does not diagnose.</p>
        <ul className="pw-about-list">
          <li><Microscope size={16} aria-hidden="true" /><span><strong>Model</strong>{MODEL_LABEL}. Saved predictions were produced offline and are labeled as saved.</span></li>
          <li><Radio size={16} aria-hidden="true" /><span><strong>Live analysis</strong>When the local inference endpoint is connected, Analyze scores a study live and records its time and duration.</span></li>
          <li><Database size={16} aria-hidden="true" /><span><strong>Data</strong>Prepared studies are de-identified research CTs served from this workstation. Nothing is uploaded.</span></li>
          <li><ShieldCheck size={16} aria-hidden="true" /><span><strong>Scope</strong>Research use only. Not a medical device, signed report, or clinical record.</span></li>
        </ul>
        <div className="pw-dialog__foot">
          <button type="button" className="pw-btn pw-btn--secondary" onClick={onClose}>Close</button>
        </div>
      </section>
    </div>
  )
}

export default function App() {
  const [route, navigate] = useRoute()
  const [cases, setCases] = useState(null)
  const [loadError, setLoadError] = useState('')
  const [caseId, setCaseId] = useState(null)
  const [reviewStatuses, setReviewStatuses] = useState(readStoredStatuses)
  const [showAbout, setShowAbout] = useState(false)
  const [endpointStatus, setEndpointStatus] = useState('checking')
  const [liveResults, setLiveResults] = useState({})
  const [inferenceState, setInferenceState] = useState({ status: 'idle', caseId: null })
  const [truthRevealedCaseId, setTruthRevealedCaseId] = useState(null)
  const [askPending, setAskPending] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  // Review drafts: in memory only (session). Never written to localStorage.
  const [drafts, setDrafts] = useState({})
  const updateDraft = useCallback((key, draft) => {
    setDrafts((previous) => {
      const next = { ...previous }
      if (draft) next[key] = draft
      else delete next[key]
      return next
    })
  }, [])
  const summaryStore = useMemo(() => ({ drafts, onChange: updateDraft }), [drafts, updateDraft])
  const dirtyDraft = Object.values(drafts).some(hasHumanContent)

  // In-app navigation keeps drafts (they live above the routes); only reload/close can lose
  // them, so warn there.
  useEffect(() => {
    if (!dirtyDraft) return undefined
    function onBeforeUnload(event) { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [dirtyDraft])

  useEffect(() => {
    fetch(`${BASE}/results.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Case manifest returned ${response.status}`)
        return response.json()
      })
      .then(setCases)
      .catch((error) => setLoadError(error.message))
  }, [])

  useEffect(() => {
    let cancelled = false
    fetchJson(`${API_BASE}/cases`)
      .then((data) => {
        if (!Array.isArray(data) || !data.some((item) => typeof item?.case_id === 'string')) throw new Error('No live cases')
        if (!cancelled) setEndpointStatus('online')
      })
      .catch(() => { if (!cancelled) setEndpointStatus('offline') })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(reviewStatuses)) } catch { /* storage unavailable */ }
  }, [reviewStatuses])

  const selectScan = useCallback((id) => {
    setCaseId(id)
    setTruthRevealedCaseId(null)
    if (!VALIDATION_SET.has(id)) {
      setLiveResults((previous) => {
        if (!previous[id]) return previous
        const next = { ...previous }
        delete next[id]
        return next
      })
    }
    setInferenceState({ status: 'idle', caseId: null })
  }, [])

  // URL is the source of truth for the active study once cases are known.
  useEffect(() => {
    if (!cases || route.view !== 'workbench' || !route.study) return
    if (route.study !== caseId && cases[route.study]) selectScan(route.study)
  }, [cases, route.view, route.study, caseId, selectScan])

  const currentCase = caseId && cases ? cases[caseId] : null
  const currentLive = caseId ? liveResults[caseId] : null
  const isAnalyzing = inferenceState.status === 'loading' && inferenceState.caseId === caseId
  const hasLiveResult = Boolean(currentLive)
  const isValidation = VALIDATION_SET.has(caseId)
  const isTruthRevealed = !isValidation && truthRevealedCaseId === caseId

  useEffect(() => {
    const titles = {
      studies: 'Studies',
      research: 'Research',
      saved: 'Saved prediction',
      workbench: currentCase ? `${formatStudyId(caseId)} · Workbench` : 'Workbench',
    }
    document.title = `${titles[route.view]} · PROWL`
  }, [route.view, caseId, currentCase])

  const studies = useMemo(() => Object.keys(cases || {}).sort().map((id) => {
    const item = cases[id]
    const validation = VALIDATION_SET.has(id)
    const spacing = Array.isArray(item.spacing_mm) && item.spacing_mm.every(Number.isFinite)
      ? `${item.spacing_mm.map((v) => v.toFixed(1)).join(' × ')} mm voxels`
      : 'Voxel spacing not recorded'
    return {
      id,
      displayId: formatStudyId(id),
      kind: validation ? 'validation' : 'prepared',
      thumbnail: `${BASE}/${id}/thumbnail.webp`,
      spacingLabel: spacing,
      referenceAvailable: Boolean(item.files?.gt),
      status: inferenceState.status === 'loading' && inferenceState.caseId === id
        ? 'analyzing'
        : validation || liveResults[id] ? 'ready' : item.files?.pred ? 'saved' : 'image',
      mark: reviewStatuses[id] === 'reviewed' || reviewStatuses[id] === 'discussion' ? reviewStatuses[id] : null,
      draft: Object.values(drafts).some((draft) => draft.studyId === id && hasHumanContent(draft)),
    }
  }), [cases, inferenceState, liveResults, reviewStatuses, drafts])

  const reviewCaseItems = useMemo(() => studies.map((study) => ({
    id: study.id,
    shortId: study.id.replace('PanTS_', ''),
    label: VALIDATION_PROFILES[study.id]?.label || 'Prepared study',
    tone: VALIDATION_PROFILES[study.id]?.tone || 'neutral',
    status: reviewStatuses[study.id] || 'unreviewed',
  })), [studies, reviewStatuses])

  const overlapPancreas = Number.isFinite(currentLive?.result?.dice_pancreas) ? currentLive.result.dice_pancreas : currentCase?.dice_pancreas
  const overlapLesion = Number.isFinite(currentLive?.result?.dice_lesion) ? currentLive.result.dice_lesion : currentCase?.dice_lesion
  const findingHasLesion = hasLiveResult ? currentLive.result.lesion_flagged : currentCase?.pred_has_lesion
  const findingVolumeMm3 = hasLiveResult ? currentLive.result.lesion_volume_mm3 : currentCase?.lesion_volume_mm3
  const findingConfidence = hasLiveResult ? currentLive.result.global_peak_lesion_confidence : currentCase?.confidence
  const currentProfile = VALIDATION_PROFILES[caseId] || PREPARED_PROFILE

  function openStudy(id) {
    if (!cases?.[id] || inferenceState.status === 'loading') return
    if (id !== caseId) selectScan(id)
    navigate({ view: 'workbench', study: id })
  }

  // Live analysis only. A failed request never substitutes a saved result; the
  // reviewer can choose "Show saved prediction" explicitly instead.
  async function analyzeScan(targetCaseId) {
    const requestedCaseId = typeof targetCaseId === 'string' ? targetCaseId : caseId
    if (!requestedCaseId || inferenceState.status === 'loading') return null
    setTruthRevealedCaseId(null)
    setInferenceState({ status: 'loading', caseId: requestedCaseId })
    try {
      const result = await fetchJson(`${API_BASE}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: requestedCaseId, split: 'test' }),
      }, 30000)
      if (
        result?.case_id !== requestedCaseId
        || typeof result.lesion_flagged !== 'boolean'
        || !Number.isFinite(result.lesion_volume_mm3)
        || !Number.isFinite(result.global_peak_lesion_confidence)
        || !Number.isFinite(result.inference_seconds)
      ) throw new Error('Invalid prediction response')
      setLiveResults((previous) => ({ ...previous, [requestedCaseId]: { result, scoredAt: formatScoreTime(), source: 'live' } }))
      setEndpointStatus('online')
      setInferenceState({ status: 'complete', caseId: requestedCaseId })
      return { source: 'live', result }
    } catch {
      setEndpointStatus('offline')
      setInferenceState({ status: 'failed', caseId: requestedCaseId })
      return null
    }
  }

  function showSavedPrediction(targetCaseId) {
    const id = typeof targetCaseId === 'string' ? targetCaseId : caseId
    const cachedCase = cases?.[id]
    if (!cachedCase?.files?.pred) return null
    setLiveResults((previous) => ({ ...previous, [id]: { result: savedResultFor(id, cachedCase), scoredAt: null, source: 'saved' } }))
    setInferenceState({ status: 'idle', caseId: null })
    return { source: 'saved' }
  }

  function revealSourceOfTruth() {
    if (isValidation || !hasLiveResult || !caseId) return false
    setTruthRevealedCaseId(caseId)
    return true
  }

  function resetUnmarkedScan() {
    if (isValidation || !caseId) return
    setLiveResults((previous) => {
      const next = { ...previous }
      delete next[caseId]
      return next
    })
    setTruthRevealedCaseId(null)
    setInferenceState({ status: 'idle', caseId: null })
  }

  function setReviewStatus(status) {
    if (!caseId) return
    setReviewStatuses((previous) => ({ ...previous, [caseId]: status }))
  }

  const showWorkbench = route.view === 'workbench'
  const showCompare = showWorkbench && route.layout === 'compare' && currentCase && isValidation

  let content
  if (loadError) {
    content = (
      <main className="pw-empty">
        <Database size={28} aria-hidden="true" />
        <h1>No prepared studies found</h1>
        <p>PROWL could not read the study manifest at <code>/cases/results.json</code> ({loadError}).</p>
      </main>
    )
  }

  return (
    <AppShell
      route={route}
      navigate={navigate}
      activeStudy={caseId}
      endpointStatus={endpointStatus}
      modelLabel={route.view === 'saved' ? 'Saved package · see model provenance' : MODEL_LABEL}
      onAbout={() => setShowAbout(true)}
    >
      {content}
      {!loadError && route.view === 'studies' && (
        cases
          ? <StudiesPage studies={studies} activeStudy={caseId} onOpen={openStudy} onImport={() => setImportOpen(true)} importAvailable={false} />
          : <main className="pw-empty" role="status"><p>Loading studies…</p></main>
      )}

      {/* The workbench stays mounted once a study is open so Research and back keep
          the viewer, layers, and drafts exactly where the reviewer left them. */}
      {!loadError && currentCase && (
        <div className="pw-route" hidden={!showWorkbench || showCompare}>
          <ReviewWorkspace
            caseId={caseId}
            caseData={currentCase}
            profile={currentProfile}
            caseItems={reviewCaseItems}
            isCurated={isValidation}
            hasLiveResult={hasLiveResult}
            liveResult={currentLive}
            isAnalyzing={isAnalyzing}
            analysisFailed={inferenceState.status === 'failed' && inferenceState.caseId === caseId}
            modelLabel={MODEL_LABEL}
            assistantPending={askPending}
            summaryStore={summaryStore}
            askPanel={(
              <LiteratureSearchPanel
                variant="panel"
                contextKey={caseId}
                contextLabel={formatStudyId(caseId)}
                onPendingChange={setAskPending}
                measurementContext={{
                  key: `${caseId}:${isValidation || hasLiveResult}:${currentLive?.source || 'saved'}:${currentLive?.scoredAt || 'saved'}:${isAnalyzing}:${currentCase.files?.pred}`,
                  caseId, files: currentCase.files, spacingMm: currentCase.spacing_mm,
                  available: (isValidation || hasLiveResult) && !isAnalyzing,
                  source: currentLive?.source || 'saved',
                }}
              />
            )}
            endpointStatus={endpointStatus}
            truthRevealed={isTruthRevealed}
            reviewStatus={reviewStatuses[caseId] || 'unreviewed'}
            finding={{
              lesionFlagged: findingHasLesion,
              volumeMm3: findingVolumeMm3,
              confidence: findingConfidence,
              diameterMm: equivalentDiameterMm(findingVolumeMm3),
            }}
            overlap={{ pancreas: overlapPancreas, lesion: overlapLesion }}
            onSelectScan={openStudy}
            onAnalyze={analyzeScan}
            onShowSavedPrediction={showSavedPrediction}
            onRevealTruth={revealSourceOfTruth}
            onResetScan={resetUnmarkedScan}
            onSetReviewStatus={setReviewStatus}
            onOpenComparison={() => navigate({ view: 'workbench', study: caseId, layout: 'compare' })}
            onOpenLibrary={() => navigate({ view: 'studies' })}
          />
        </div>
      )}
      {showCompare && (
        <ViewerSuspense>
          <ValidationComparison
            caseId={caseId}
            caseData={currentCase}
            profile={VALIDATION_PROFILES[caseId]}
            caseOptions={VALIDATION_IDS.filter((id) => cases[id]).map((id) => [id, VALIDATION_PROFILES[id].label])}
            onSelectCase={(id) => { selectScan(id); navigate({ view: 'workbench', study: id, layout: 'compare' }, { replace: true }) }}
            onBack={() => navigate({ view: 'workbench', study: caseId })}
          />
        </ViewerSuspense>
      )}
      {!loadError && showWorkbench && cases && !currentCase && (
        <WorkbenchEmpty
          onStudies={() => navigate({ view: 'studies' })}
          onImport={() => setImportOpen(true)}
          missingStudy={route.study && !cases[route.study] ? route.study : null}
        />
      )}

      {route.view === 'research' && (
        <ViewerSuspense label="Loading research…">
          <ResearchPage
            activeStudyLabel={currentCase ? formatStudyId(caseId) : null}
            onReturnToStudy={() => navigate({ view: 'workbench', study: caseId })}
          />
        </ViewerSuspense>
      )}
      {route.view === 'saved' && (
        <ViewerSuspense label="Loading saved viewer…">
          <div className="pw-page"><SavedPredictionView /></div>
        </ViewerSuspense>
      )}

      {showAbout && <AboutDialog onClose={() => setShowAbout(false)} />}
      {importOpen && <ImportStudyDialog onClose={() => setImportOpen(false)} onOpenStudies={() => navigate({ view: 'studies' })} />}
    </AppShell>
  )
}
