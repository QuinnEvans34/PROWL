import { lazy, Suspense, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  BadgeCheck,
  BookOpen,
  Check,
  ChevronRight,
  CircleAlert,
  Database,
  Eye,
  Info,
  LayoutGrid,
  MessageSquareWarning,
  Microscope,
  Radio,
  ScanLine,
  ShieldCheck,
  Target,
  X,
} from 'lucide-react'
import ReviewWorkspace from './components/ReviewWorkspace.jsx'
const NiivueViewer = lazy(() => import('./components/NiivueViewer.jsx'))

const BASE = '/cases'
const API_BASE = 'http://localhost:8000'
const STORAGE_KEY = 'pants-review-status-v1'
const CURATED_CASE_IDS = ['PanTS_00009005', 'PanTS_00009016', 'PanTS_00009220']
const CURATED_CASE_SET = new Set(CURATED_CASE_IDS)

const CASE_PROFILES = {
  PanTS_00009005: {
    label: 'Strong overlap',
    eyebrow: 'True-positive showcase',
    summary: 'The model and source of truth identify the same lesion.',
    interpretation: 'The model finds the tumor and outlines it closely — lesion Dice 0.919, pancreas Dice 0.855.',
    strength: 'Correctly localized the lesion with a tight boundary around it.',
    limitation: 'The predicted boundary still differs slightly from the reference contour.',
    tone: 'positive',
    order: 1,
  },
  PanTS_00009016: {
    label: 'Correctly silent',
    eyebrow: 'True-negative showcase',
    summary: 'A tumor-free scan where the model correctly predicts no lesion.',
    interpretation: 'The model segments the pancreas well (Dice 0.889) and raises no false alarm.',
    strength: 'Strong pancreas segmentation with no lesion predicted on a healthy scan.',
    limitation: 'Correct silence on healthy scans is the model’s least reliable behavior overall.',
    tone: 'positive',
    order: 2,
  },
  PanTS_00009220: {
    label: 'Large false positive',
    eyebrow: 'Failure analysis',
    summary: 'The model flags a large lesion-like region on a scan with no tumor.',
    interpretation: 'A useful example of why detection specificity and human review remain important.',
    strength: 'Still produces a usable pancreas outline on a lesion-negative case.',
    limitation: 'Predicts roughly 51 cm³ of lesion where the source of truth has none.',
    tone: 'caution',
    order: 3,
  },
}

function approxDiameterMm(volumeMm3) {
  if (!volumeMm3) return 0
  return Math.round(2 * Math.cbrt((3 * volumeMm3) / (4 * Math.PI)))
}

function modelSignal(confidence) {
  if (confidence >= 0.8) return 'Higher model signal'
  if (confidence >= 0.55) return 'Moderate model signal'
  return 'Lower model signal'
}

function formatCaseId(caseId) {
  return caseId?.replace('PanTS_', 'PanTS ')
}

function friendlyScanLabel(caseId, endpointLabel) {
  const profileLabel = CASE_PROFILES[caseId]?.label
  if (profileLabel) return profileLabel

  const formattedId = formatCaseId(caseId)
  if (
    typeof endpointLabel === 'string'
    && endpointLabel.trim()
    && endpointLabel !== caseId
    && endpointLabel !== formattedId
  ) {
    return endpointLabel
  }

  return 'Unmarked pancreas CT'
}

function formatScoreTime(date = new Date()) {
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
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

function statusLabel(status) {
  if (status === 'reviewed') return 'Reviewed'
  if (status === 'discussion') return 'Discussion'
  return 'Unreviewed'
}

function validationOutcome(caseData) {
  const predicted = Boolean(caseData?.pred_has_lesion)
  const reference = Boolean(caseData?.gt_has_lesion)
  if (predicted && reference) return 'True positive'
  if (!predicted && !reference) return 'True negative'
  if (predicted) return 'False positive'
  return 'False negative'
}

function StatusPill({ status }) {
  const icon = status === 'reviewed'
    ? <Check size={13} aria-hidden="true" />
    : status === 'discussion'
      ? <MessageSquareWarning size={13} aria-hidden="true" />
      : <span className="status-dot" aria-hidden="true" />

  return (
    <span className={`status-pill status-pill--${status || 'unreviewed'}`}>
      {icon}
      {statusLabel(status)}
    </span>
  )
}

function BrandMark({ large = false }) {
  return (
    <span className={`brand-mark${large ? ' brand-mark--large' : ''}`} aria-hidden="true">
      <span>P</span>
      <i />
    </span>
  )
}

function ScanCard({ scan, endpointStatus, busy, onLoad, featured = false }) {
  return (
    <button
      type="button"
      className={`scan-card${featured ? ' scan-card--featured' : ''}`}
      onClick={() => onLoad(scan.caseId)}
      disabled={!scan.cachedCase || busy}
      aria-label={`Load ${scan.caseId}, ${scan.label}`}
    >
      <span className="scan-card__topline">
        <span>Study {scan.studyNumber}</span>
        <span className={scan.curated ? 'scan-card__status scan-card__status--live' : 'scan-card__status'}>
          {scan.curated ? 'Curated evidence' : endpointStatus === 'online' ? 'Ready to analyze' : 'CT available'}
        </span>
      </span>
      <span className="scan-card__visual" aria-hidden="true">
        <img src={`${BASE}/${scan.caseId}/thumbnail.webp`} alt="" />
        <span className="scan-card__visual-scanline" />
      </span>
      <span className="scan-card__copy">
        <strong>{scan.label}</strong>
        <code>{scan.caseId}</code>
      </span>
      <span className="scan-card__meta">
        <span>{scan.cachedCase?.spacing_mm?.[0]?.toFixed(1) || '1.5'} mm voxels</span>
        <span>{scan.curated ? 'Prediction + reference' : 'CT only until analyzed'}</span>
      </span>
      <span className="scan-card__action">
        {scan.curated
          ? <Microscope size={15} aria-hidden="true" />
          : <ScanLine size={15} aria-hidden="true" />}
        {scan.curated ? 'Open evidence review' : 'Load clean scan'}
        <ChevronRight size={15} aria-hidden="true" />
      </span>
    </button>
  )
}

function ViewerSuspense({ children }) {
  return (
    <Suspense fallback={<div className="viewer-module-loading" role="status">Preparing medical viewer…</div>}>
      {children}
    </Suspense>
  )
}

function EmptyState() {
  return (
    <main className="empty-state">
      <Database size={28} aria-hidden="true" />
      <h1>No prepared cases found</h1>
      <p>The application could not find a case manifest at <code>/cases/results.json</code>.</p>
    </main>
  )
}

export default function App() {
  const [cases, setCases] = useState({})
  const [loadError, setLoadError] = useState('')
  const [activeTab, setActiveTab] = useState('queue')
  const [caseId, setCaseId] = useState(null)
  const [reviewStatuses, setReviewStatuses] = useState(readStoredStatuses)
  const [comparisonMode, setComparisonMode] = useState('2d')
  const [showAbout, setShowAbout] = useState(false)
  const [apiCases, setApiCases] = useState([])
  const [endpointStatus, setEndpointStatus] = useState('checking')
  const [liveResults, setLiveResults] = useState({})
  const [inferenceState, setInferenceState] = useState({ status: 'idle', caseId: null })
  const [truthRevealedCaseId, setTruthRevealedCaseId] = useState(null)

  useEffect(() => {
    fetch(`${BASE}/results.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Case manifest returned ${response.status}`)
        return response.json()
      })
      .then((data) => {
        setCases(data)
        const ids = Object.keys(data).sort((a, b) => {
          const aOrder = CASE_PROFILES[a]?.order ?? 99
          const bOrder = CASE_PROFILES[b]?.order ?? 99
          return aOrder - bOrder
        })
        setCaseId(ids[0] || null)
      })
      .catch((error) => setLoadError(error.message))
  }, [])

  useEffect(() => {
    let cancelled = false

    fetchJson(`${API_BASE}/cases`)
      .then((data) => {
        if (!Array.isArray(data) || !data.length) throw new Error('No live cases available')
        const available = data.filter((item) => (
          item
          && typeof item.case_id === 'string'
          && typeof item.label === 'string'
        ))
        if (!available.length) throw new Error('Invalid live case catalog')
        if (!cancelled) {
          setApiCases(available)
          setEndpointStatus('online')
        }
      })
      .catch(() => {
        if (!cancelled) setEndpointStatus('offline')
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviewStatuses))
  }, [reviewStatuses])

  const caseIds = useMemo(
    () => Object.keys(cases).sort((a, b) => {
      const aOrder = CASE_PROFILES[a]?.order ?? 99
      const bOrder = CASE_PROFILES[b]?.order ?? 99
      return aOrder - bOrder
    }),
    [cases],
  )
  const curatedCaseIds = useMemo(
    () => CURATED_CASE_IDS.filter((id) => cases[id]),
    [cases],
  )

  const libraryCases = useMemo(() => {
    const source = apiCases.length
      ? apiCases
      : Object.keys(cases).sort().map((id) => ({ case_id: id, label: null }))

    return source.map((item, index) => ({
      caseId: item.case_id,
      label: friendlyScanLabel(item.case_id, item.label),
      cachedCase: cases[item.case_id] || null,
      curated: CURATED_CASE_SET.has(item.case_id),
      studyNumber: String(index + 1).padStart(2, '0'),
    }))
  }, [apiCases, cases])
  const curatedLibraryCases = useMemo(
    () => libraryCases
      .filter((scan) => scan.curated)
      .map((scan, index) => ({
        ...scan,
        studyNumber: String(index + 1).padStart(2, '0'),
      })),
    [libraryCases],
  )
  const readyLibraryCases = useMemo(
    () => libraryCases
      .filter((scan) => !scan.curated)
      .map((scan, index) => ({
        ...scan,
        studyNumber: String(curatedLibraryCases.length + index + 1).padStart(2, '0'),
      })),
    [curatedLibraryCases, libraryCases],
  )

  const reviewCaseItems = useMemo(
    () => caseIds.map((id) => ({
      id,
      shortId: id.replace('PanTS_', ''),
      label: CASE_PROFILES[id]?.label || 'Unmarked scan',
      tone: CASE_PROFILES[id]?.tone || 'neutral',
      status: reviewStatuses[id] || 'unreviewed',
    })),
    [caseIds, reviewStatuses],
  )

  const currentCase = caseId ? cases[caseId] : null
  const currentLive = caseId ? liveResults[caseId] : null
  const isAnalyzing = inferenceState.status === 'loading' && inferenceState.caseId === caseId
  const hasLiveResult = Boolean(currentLive)
  const isCuratedCase = CURATED_CASE_SET.has(caseId)
  // Once truth is revealed for this case it stays revealed. `hasLiveResult` is deliberately
  // NOT part of this: reveal can only be triggered when a live result exists, and gating on
  // it here meant anything that cleared liveResults silently re-locked truth and pulled the
  // gt mask back out of the viewer after it had already loaded.
  const isTruthRevealed = !isCuratedCase && truthRevealedCaseId === caseId
  const overlapPancreas = Number.isFinite(currentLive?.result?.dice_pancreas)
    ? currentLive.result.dice_pancreas
    : currentCase?.dice_pancreas
  const overlapLesion = Number.isFinite(currentLive?.result?.dice_lesion)
    ? currentLive.result.dice_lesion
    : currentCase?.dice_lesion
  const findingHasLesion = hasLiveResult ? currentLive.result.lesion_flagged : currentCase?.pred_has_lesion
  const findingVolumeMm3 = hasLiveResult
    ? currentLive.result.lesion_volume_mm3
    : currentCase?.lesion_volume_mm3 || 0
  const findingConfidence = hasLiveResult
    ? currentLive.result.global_peak_lesion_confidence
    : currentCase?.confidence || 0
  const currentProfile = CASE_PROFILES[caseId] || {
    label: 'Unmarked scan',
    eyebrow: 'Prospective review',
    summary: 'A clean CT awaiting a live model score.',
    interpretation: 'Run live inference before reviewing the model proposal.',
    strength: 'The CT can be inspected without model or reference annotations.',
    limitation: 'No prediction is shown until live analysis completes.',
    tone: 'neutral',
  }

  function openCase(id, destination = 'review') {
    setCaseId(id)
    setActiveTab(destination)
    setTruthRevealedCaseId(null)
    setInferenceState({ status: 'idle', caseId: null })
  }

  function selectScan(id) {
    setCaseId(id)
    setTruthRevealedCaseId(null)
    if (!CURATED_CASE_SET.has(id)) {
      setLiveResults((previous) => {
        const next = { ...previous }
        delete next[id]
        return next
      })
    }
    setInferenceState({ status: 'idle', caseId: null })
  }

  async function analyzeScan(targetCaseId) {
    const requestedCaseId = typeof targetCaseId === 'string' ? targetCaseId : caseId
    if (!requestedCaseId || inferenceState.status === 'loading') return null

    setTruthRevealedCaseId(null)
    setLiveResults((previous) => {
      const next = { ...previous }
      delete next[requestedCaseId]
      return next
    })
    setInferenceState({ status: 'loading', caseId: requestedCaseId })

    try {
      const result = await fetchJson(
        `${API_BASE}/predict`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ case_id: requestedCaseId, split: 'test' }),
        },
        30000,
      )
      if (
        result?.case_id !== requestedCaseId
        || typeof result.lesion_flagged !== 'boolean'
        || !Number.isFinite(result.lesion_volume_mm3)
        || !Number.isFinite(result.global_peak_lesion_confidence)
        || !Number.isFinite(result.inference_seconds)
      ) {
        throw new Error('Invalid prediction response')
      }
      setLiveResults((previous) => ({
        ...previous,
        [requestedCaseId]: {
          result,
          scoredAt: formatScoreTime(),
          source: 'live',
        },
      }))
      setEndpointStatus('online')
      setInferenceState({ status: 'complete', caseId: requestedCaseId })
      return { source: 'live', result }
    } catch {
      const cachedCase = cases[requestedCaseId]
      if (cachedCase) {
        const cachedResult = {
          case_id: requestedCaseId,
          lesion_flagged: Boolean(cachedCase.pred_has_lesion),
          lesion_volume_mm3: Number(cachedCase.lesion_volume_mm3 || 0),
          global_peak_lesion_confidence: Number(cachedCase.confidence || 0),
          inference_seconds: null,
          dice_pancreas: cachedCase.dice_pancreas,
          dice_lesion: cachedCase.dice_lesion,
        }
        setLiveResults((previous) => ({
          ...previous,
          [requestedCaseId]: {
            result: cachedResult,
            scoredAt: null,
            source: 'cached',
          },
        }))
      }
      setEndpointStatus('offline')
      setInferenceState({ status: 'offline', caseId: requestedCaseId })
      return cachedCase ? { source: 'cached' } : null
    }
  }

  function loadLibraryScan(id) {
    if (!cases[id] || inferenceState.status === 'loading') return
    selectScan(id)
    setActiveTab('review')
  }

  function revealSourceOfTruth() {
    if (isCuratedCase || !hasLiveResult || !caseId) return false
    setTruthRevealedCaseId(caseId)
    return true
  }

  function resetUnmarkedScan() {
    if (isCuratedCase || !caseId) return
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

  function resetDemo() {
    setReviewStatuses({})
    localStorage.removeItem(STORAGE_KEY)
  }

  if (loadError) return <EmptyState />

  return (
    <div className="app">
      <header className="app-header">
        <button className="brand" type="button" onClick={() => setActiveTab('queue')} aria-label="Open demo cases">
          <BrandMark />
          <span className="brand-copy">
            <strong>PanTS Review</strong>
            <span>Pancreas evidence workspace</span>
          </span>
        </button>

        <nav className="primary-nav" aria-label="Primary navigation">
          <button className={activeTab === 'queue' ? 'active' : ''} onClick={() => setActiveTab('queue')}>
            Demo cases
          </button>
          <button className={activeTab === 'library' ? 'active' : ''} onClick={() => setActiveTab('library')}>
            Scan library
          </button>
          <button onClick={() => window.location.assign('/research')}>
            Research evidence
          </button>
          <button className={activeTab === 'review' ? 'active' : ''} onClick={() => setActiveTab('review')} disabled={!currentCase}>
            Review workspace
          </button>
          <button
            className={activeTab === 'comparison' ? 'active' : ''}
            onClick={() => setActiveTab('comparison')}
            disabled={!currentCase || !isCuratedCase}
          >
            Scientific comparison
          </button>
        </nav>

        <div className="header-actions">
          <div className="header-provenance">
            <span className="prepared-badge">
              <Activity size={13} aria-hidden="true" />
              Segmenter v1 · step 18000
            </span>
            <span className="header-freshness">
              <Radio size={11} aria-hidden="true" />
              {endpointStatus === 'online'
                ? 'Live inference connected · cached fallback ready'
                : endpointStatus === 'offline'
                  ? 'Prepared results · live endpoint offline'
                  : 'Checking live inference · cached fallback ready'}
            </span>
          </div>
          <button className="icon-button" onClick={() => setShowAbout(true)} aria-label="About this research interface">
            <Info size={18} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="research-notice">
        <ShieldCheck size={14} aria-hidden="true" />
        <span><strong>Research use only.</strong> Segmentation and annotation assist—not a diagnosis.</span>
        <span className="notice-detail">Live scores include scoring time and duration.</span>
      </div>

      {activeTab === 'queue' && (
        <main className="queue-page">
          <section className="queue-hero">
            <div>
              <span className="eyebrow">Five-week project · prepared demonstration</span>
              <h1>Review the model as a scientist would.</h1>
              <p>
                Three deliberately selected cases show where pancreas-aware segmentation succeeds,
                where it over-calls, and why the source of truth matters.
              </p>
            </div>
            <div className="queue-summary" aria-label="Prepared case summary">
              <div><strong>{curatedCaseIds.length}</strong><span>curated cases</span></div>
              <div><strong>1</strong><span>strong result</span></div>
              <div><strong>2</strong><span>failure analyses</span></div>
            </div>
          </section>

          <section className="queue-section">
            <div className="section-heading">
              <div>
                <h2>Demo cases</h2>
                <p>Three intentional examples: a strong result, correct silence, and a failure analysis.</p>
              </div>
              <button className="text-button" onClick={resetDemo}>Reset review status</button>
            </div>

            <div className="case-table" role="table" aria-label="Prepared demonstration cases">
              <div className="case-table__header" role="row">
                <span>Case</span>
                <span>Model summary</span>
                <span>Scientific role</span>
                <span>Status</span>
                <span />
              </div>
              {curatedCaseIds.map((id) => {
                const item = cases[id]
                const profile = CASE_PROFILES[id]
                const status = reviewStatuses[id] || 'unreviewed'
                return (
                  <div className="case-row" role="row" key={id}>
                    <div className="case-identity">
                      <span className={`case-indicator case-indicator--${profile.tone}`} aria-hidden="true" />
                      <div>
                        <strong>{formatCaseId(id)}</strong>
                        <span>Prepared validation case</span>
                      </div>
                    </div>
                    <div>
                      <strong>{item.pred_has_lesion ? 'Possible finding flagged' : 'No finding flagged'}</strong>
                      <span>{approxDiameterMm(item.lesion_volume_mm3)} mm estimated diameter · {modelSignal(item.confidence)}</span>
                    </div>
                    <div>
                      <strong>{profile.label}</strong>
                      <span>{profile.eyebrow}</span>
                    </div>
                    <StatusPill status={status} />
                    <button className="review-button" onClick={() => openCase(id)}>
                      Review <ChevronRight size={15} aria-hidden="true" />
                    </button>
                  </div>
                )
              })}
            </div>
          </section>

          <section className="workflow-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Presentation workflow</span>
                <h2>One honest story, from prediction to evidence.</h2>
              </div>
            </div>
            <div className="workflow-grid">
              <article>
                <span className="step-number">01</span>
                <Target size={20} aria-hidden="true" />
                <h3>Select a prepared case</h3>
                <p>The CT, segmentation, surface meshes, and result summary are already available.</p>
              </article>
              <article>
                <span className="step-number">02</span>
                <Eye size={20} aria-hidden="true" />
                <h3>Inspect the proposal</h3>
                <p>Review the predicted pancreas and lesion in synchronized planes or 3D.</p>
              </article>
              <article>
                <span className="step-number">03</span>
                <Microscope size={20} aria-hidden="true" />
                <h3>Reveal the source of truth</h3>
                <p>Compare identical views and explain agreement, over-segmentation, or false positives.</p>
              </article>
              <article>
                <span className="step-number">04</span>
                <BadgeCheck size={20} aria-hidden="true" />
                <h3>Record the review</h3>
                <p>Mark the case reviewed or flag it for a deeper scientific discussion.</p>
              </article>
            </div>
          </section>
        </main>
      )}

      {activeTab === 'library' && (
        <main className="library-page">
          <section className="library-hero">
            <div>
              <span className="eyebrow">Prepared scan repository</span>
              <h1>Choose a study. Score it live.</h1>
              <p>
                Curated studies open with their scientific evidence. Every other card opens as a
                clean, unmarked CT. Analyze reveals the model proposal; source of truth remains
                concealed until you explicitly reveal it.
              </p>
            </div>
            <div className="library-source" aria-live="polite">
              <span className={`library-source__signal library-source__signal--${endpointStatus}`} aria-hidden="true" />
              <div>
                <strong>
                  {endpointStatus === 'online'
                    ? 'Live endpoint connected'
                    : endpointStatus === 'offline'
                      ? 'Cached library available'
                      : 'Checking live endpoint'}
                </strong>
                <span>
                  {endpointStatus === 'online'
                    ? `${libraryCases.length} scans discovered by FastAPI`
                    : `${libraryCases.length} scans loaded from results.json`}
                </span>
              </div>
            </div>
          </section>

          <section className="library-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Guided presentation cases</span>
                <h2>Curated evidence</h2>
                <p>Open with the prediction, source of truth, and scientific interpretation ready to discuss.</p>
              </div>
              <span className="library-count"><Microscope size={14} aria-hidden="true" /> {curatedLibraryCases.length} studies</span>
            </div>

            <div className="scan-gallery scan-gallery--curated" aria-label="Curated evidence studies">
              {curatedLibraryCases.map((scan) => (
                <ScanCard
                  key={scan.caseId}
                  scan={scan}
                  endpointStatus={endpointStatus}
                  busy={inferenceState.status === 'loading'}
                  onLoad={loadLibraryScan}
                  featured
                />
              ))}
            </div>
          </section>

          <section className="library-section library-section--ready">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Prospective workflow</span>
                <h2>Ready to analyze</h2>
                <p>Begin with an unmarked CT, run the model, then reveal the reference only when you are ready to compare.</p>
              </div>
              <span className="library-count"><LayoutGrid size={14} aria-hidden="true" /> {readyLibraryCases.length} scans</span>
            </div>

            <div className="scan-gallery" aria-label="Ready-to-analyze scan library">
              {readyLibraryCases.map((scan) => (
                <ScanCard
                  key={scan.caseId}
                  scan={scan}
                  endpointStatus={endpointStatus}
                  busy={inferenceState.status === 'loading'}
                  onLoad={loadLibraryScan}
                />
              ))}
            </div>
          </section>
        </main>
      )}

      {activeTab === 'review' && currentCase && (
        <ReviewWorkspace
          caseId={caseId}
          caseData={currentCase}
          profile={currentProfile}
          caseItems={reviewCaseItems}
          isCurated={isCuratedCase}
          hasLiveResult={hasLiveResult}
          liveResult={currentLive}
          isAnalyzing={isAnalyzing}
          endpointStatus={endpointStatus}
          truthRevealed={isTruthRevealed}
          reviewStatus={reviewStatuses[caseId] || 'unreviewed'}
          finding={{
            lesionFlagged: findingHasLesion,
            volumeMm3: findingVolumeMm3,
            confidence: findingConfidence,
            diameterMm: approxDiameterMm(findingVolumeMm3),
          }}
          overlap={{ pancreas: overlapPancreas, lesion: overlapLesion }}
          onSelectScan={selectScan}
          onAnalyze={analyzeScan}
          onRevealTruth={revealSourceOfTruth}
          onResetScan={resetUnmarkedScan}
          onSetReviewStatus={setReviewStatus}
          onOpenComparison={() => setActiveTab('comparison')}
          onOpenLibrary={() => setActiveTab('library')}
        />
      )}

      {activeTab === 'comparison' && currentCase && isCuratedCase && (
        <main className="comparison-page">
          <section className="comparison-header">
            <div>
              <span className="eyebrow">Validation mode · source of truth visible</span>
              <h1>Prediction, evidence, and error—side by side.</h1>
              <p>
                The same prepared scan is shown three ways so the audience can inspect what the
                model captured, what it missed, and where it predicted too much.
              </p>
            </div>
            <div className="comparison-controls">
              <label>
                <span>Case</span>
                <select value={caseId} onChange={(event) => setCaseId(event.target.value)}>
                  {curatedCaseIds.map((id) => <option value={id} key={id}>{formatCaseId(id)} · {CASE_PROFILES[id]?.label}</option>)}
                </select>
              </label>
              <div className="segmented-control" aria-label="Scientific comparison view">
                <button className={comparisonMode === '2d' ? 'active' : ''} onClick={() => setComparisonMode('2d')}>Three planes</button>
                <button className={comparisonMode === '3d' ? 'active' : ''} onClick={() => setComparisonMode('3d')}>3D surfaces</button>
              </div>
            </div>
          </section>

          <section className="evidence-strip">
            <div>
              <span>Validation outcome</span>
              <strong>{validationOutcome(currentCase)}</strong>
            </div>
            <div>
              <span title="Dice coefficient">Pancreas outline agreement</span>
              <strong>{currentCase.dice_pancreas.toFixed(3)}</strong>
            </div>
            <div>
              <span title="Dice coefficient">Lesion outline agreement</span>
              <strong>
                {!currentCase.gt_has_lesion && !currentCase.pred_has_lesion
                  ? 'No lesion'
                  : currentCase.dice_lesion.toFixed(3)}
              </strong>
              {!currentCase.gt_has_lesion && !currentCase.pred_has_lesion && <small>Absent in both masks</small>}
            </div>
            <div>
              <span>Predicted lesion volume</span>
              <strong>{(currentCase.lesion_volume_mm3 / 1000).toFixed(2)} cm³</strong>
            </div>
          </section>

          <section className="comparison-grid">
            <article className="comparison-view">
              <header>
                <div>
                  <span className="view-number">01</span>
                  <h2>Model prediction</h2>
                </div>
                <span className="view-badge">Proposal</span>
              </header>
              <ViewerSuspense>
                <NiivueViewer
                  key={`pred-${caseId}-${comparisonMode}`}
                  caseData={currentCase}
                  sources={['pred']}
                  mode={comparisonMode}
                  overlayOpacity={0.72}
                  ctOpacity={comparisonMode === '3d' ? 0 : 0.1}
                  compact
                  label={`${formatCaseId(caseId)} model prediction`}
                />
              </ViewerSuspense>
              <footer>
                <span><i className="legend-dot legend-dot--pancreas" /> Predicted pancreas</span>
                <span><i className="legend-dot legend-dot--lesion" /> Predicted lesion</span>
              </footer>
            </article>

            <article className="comparison-view comparison-view--truth">
              <header>
                <div>
                  <span className="view-number">02</span>
                  <h2>Source of truth</h2>
                </div>
                <span className="view-badge view-badge--truth"><BookOpen size={12} aria-hidden="true" /> Reference</span>
              </header>
              <ViewerSuspense>
                <NiivueViewer
                  key={`gt-${caseId}-${comparisonMode}`}
                  caseData={currentCase}
                  sources={['gt']}
                  mode={comparisonMode}
                  overlayOpacity={0.72}
                  ctOpacity={comparisonMode === '3d' ? 0 : 0.1}
                  compact
                  label={`${formatCaseId(caseId)} source-of-truth segmentation`}
                />
              </ViewerSuspense>
              <footer>
                <span><i className="legend-dot legend-dot--truth-pancreas" /> Reference pancreas</span>
                <span><i className="legend-dot legend-dot--truth-lesion" /> Reference lesion</span>
              </footer>
            </article>

            <article className="comparison-view comparison-view--overlay">
              <header>
                <div>
                  <span className="view-number">03</span>
                  <h2>Combined overlay</h2>
                </div>
                <span className="view-badge view-badge--analysis">Analysis</span>
              </header>
              <ViewerSuspense>
                <NiivueViewer
                  key={`both-${caseId}-${comparisonMode}`}
                  caseData={currentCase}
                  sources={['gt', 'pred']}
                  mode={comparisonMode}
                  overlayOpacity={0.6}
                  ctOpacity={comparisonMode === '3d' ? 0 : 0.08}
                  compact
                  label={`${formatCaseId(caseId)} prediction and source-of-truth overlay`}
                />
              </ViewerSuspense>
              <footer>
                <span>Prediction + source of truth</span>
                <span>Inspect boundary agreement</span>
              </footer>
            </article>
          </section>

          <section className="analysis-section">
            <article className="analysis-narrative">
              <span className={`analysis-icon analysis-icon--${currentProfile.tone}`}>
                {currentCase.gt_has_lesion
                  ? <BadgeCheck size={20} aria-hidden="true" />
                  : <CircleAlert size={20} aria-hidden="true" />}
              </span>
              <div>
                <span className="eyebrow">What this case demonstrates</span>
                <h2>{currentProfile.interpretation}</h2>
                <p>
                  The overlays are intentionally shown without hiding disagreement. This is a scientific
                  comparison of a saved model result—not a claim of diagnostic reliability.
                </p>
              </div>
            </article>
            <div className="analysis-table">
              <div className="analysis-row analysis-row--header">
                <span>Structure</span><span>What worked</span><span>Where it falls short</span>
              </div>
              <div className="analysis-row">
                <strong>Pancreas</strong>
                <span>{currentProfile.strength}</span>
                <span>Small boundary disagreements remain visible in the combined view.</span>
              </div>
              <div className="analysis-row">
                <strong>Lesion</strong>
                <span>{currentCase.gt_has_lesion ? 'Correct region identified.' : 'No matching reference lesion is present.'}</span>
                <span>{currentProfile.limitation}</span>
              </div>
            </div>
          </section>
        </main>
      )}

      {showAbout && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowAbout(false)}>
          <section className="about-modal" role="dialog" aria-modal="true" aria-labelledby="about-title" onMouseDown={(event) => event.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowAbout(false)} aria-label="Close about panel"><X size={18} /></button>
            <BrandMark large />
            <span className="eyebrow">About this interface</span>
            <h2 id="about-title">A transparent segmentation demonstration.</h2>
            <p>
              PanTS Review presents pancreas and lesion segmentations from a five-week machine-learning
              project. It is designed to make both model strengths and errors inspectable.
            </p>
            <div className="about-provenance">
              <Activity size={17} aria-hidden="true" />
              <div>
                <strong>Model provenance</strong>
                <code>Model: pancreas-lesion-segmenter v1 · checkpoint step 18000</code>
              </div>
            </div>
            <div className="about-points">
              <div><Radio size={17} aria-hidden="true" /><span><strong>Data freshness</strong>Predictions are computed live by a deployed FastAPI endpoint when available, with cached results as fallback. Live results show their scoring time and inference duration in the finding panel.</span></div>
              <div><Database size={17} aria-hidden="true" /><span><strong>Cached results</strong>Saved NIfTI volumes, surface meshes, and measurements keep every prepared case reviewable when the inference endpoint is offline.</span></div>
              <div><Microscope size={17} aria-hidden="true" /><span><strong>Scientific transparency</strong>Source-of-truth contours and case metrics live in a dedicated validation surface.</span></div>
              <div><ShieldCheck size={17} aria-hidden="true" /><span><strong>Research scope</strong>This is an annotation-assist and segmentation project, not a diagnostic system.</span></div>
            </div>
            <button className="primary-button" onClick={() => setShowAbout(false)}>Return to workspace</button>
          </section>
        </div>
      )}
    </div>
  )
}
