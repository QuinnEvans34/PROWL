import { lazy, Suspense, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import {
  Activity,
  BookOpen,
  Box,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleDot,
  Crosshair,
  Database,
  Download,
  Eye,
  EyeOff,
  Focus,
  Layers3,
  LoaderCircle,
  Maximize2,
  MessageSquareWarning,
  Microscope,
  PanelLeftClose,
  PanelLeftOpen,
  Radio,
  RotateCcw,
  ScanLine,
  Settings2,
  ShieldCheck,
  Sparkles,
  WifiOff,
  X,
} from 'lucide-react'
import { makeReviewState, reviewReducer } from '../lib/reviewState.js'
import GuidedEvidencePanel from './GuidedEvidencePanel.jsx'
import {
  EVIDENCE_META,
  REVIEW_COLORS,
  objectLabel,
  sourcesForEvidence,
  visibleSourcesForEvidence,
} from '../lib/viewerLayers.js'

const NiivueViewer = lazy(() => import('./NiivueViewer.jsx'))

const DISPLAY_PRESETS = {
  anatomy: {
    label: 'CT detail',
    description: 'Makes the CT anatomy easiest to read',
    overlayOpacity: 0.62,
    ctOpacity: 0.44,
  },
  balanced: {
    label: 'Balanced',
    description: 'Keeps both the CT and model contours clear',
    overlayOpacity: 0.62,
    ctOpacity: 0.18,
  },
  masks: {
    label: 'Masks',
    description: 'Emphasizes the pancreas and lesion overlays',
    overlayOpacity: 0.84,
    ctOpacity: 0.07,
  },
}

const CT_WINDOW_OPTIONS = [
  ['soft', 'Soft tissue', 'Best general view of the pancreas and nearby organs'],
  ['contrast', 'Contrast+', 'Adds separation between similar soft tissues'],
  ['wide', 'Wide', 'Shows the broadest CT intensity range'],
]

const FRONT_CUT_DEPTH_MIN = -0.5
const FRONT_CUT_DEPTH_MAX = 0.5

function clipDepthFromProgress(progress) {
  if (progress <= 0) return 2
  const fraction = Math.max(0, Math.min(1, progress / 100))
  return FRONT_CUT_DEPTH_MIN
    + fraction * (FRONT_CUT_DEPTH_MAX - FRONT_CUT_DEPTH_MIN)
}

function ViewerSuspense({ children }) {
  return (
    <Suspense fallback={<div className="viewer-module-loading" role="status">Preparing medical viewer…</div>}>
      {children}
    </Suspense>
  )
}

function StageRail({ stage, curated }) {
  if (curated) {
    return (
      <div className="review-stage-rail review-stage-rail--curated" aria-label="Curated evidence is unlocked">
        <ShieldCheck size={13} aria-hidden="true" />
        <span>Curated evidence</span>
        <i />
        <strong>Prediction + reference ready</strong>
      </div>
    )
  }

  return (
    <div className="review-stage-rail" aria-label={`Review workflow, stage ${stage} of 3`}>
      {[
        ['01', 'Unmarked'],
        ['02', 'Prediction'],
        ['03', 'Reference'],
      ].map(([number, label], index) => {
        const itemStage = index + 1
        const state = itemStage < stage ? 'complete' : itemStage === stage ? 'active' : 'locked'
        return (
          <span className={`review-stage-rail__step review-stage-rail__step--${state}`} key={number}>
            <i>{state === 'complete' ? <Check size={10} aria-hidden="true" /> : number}</i>
            <span>{label}</span>
          </span>
        )
      })}
    </div>
  )
}

function EvidenceButton({ mode, active, unlocked, onClick }) {
  const meta = EVIDENCE_META[mode]
  return (
    <button
      type="button"
      className={`evidence-button${active ? ' active' : ''}`}
      onClick={onClick}
      disabled={!unlocked}
      aria-pressed={active}
      title={unlocked ? meta.description : `${meta.label} has not been unlocked yet`}
    >
      {mode === 'ct' && <ScanLine size={14} aria-hidden="true" />}
      {mode === 'prediction' && <Sparkles size={14} aria-hidden="true" />}
      {mode === 'truth' && <BookOpen size={14} aria-hidden="true" />}
      {mode === 'overlap' && <Layers3 size={14} aria-hidden="true" />}
      <span>{meta.shortLabel}</span>
      {!unlocked && <i className="evidence-button__lock" aria-hidden="true" />}
    </button>
  )
}

function LayerToggle({ checked, label, color, onClick, disabled = false }) {
  return (
    <button
      type="button"
      className={`review-layer-toggle${checked ? ' active' : ''}`}
      onClick={onClick}
      disabled={disabled}
      aria-pressed={checked}
    >
      <i style={{ '--layer-color': color }} aria-hidden="true" />
      <span>{label}</span>
      {checked ? <Eye size={13} aria-hidden="true" /> : <EyeOff size={13} aria-hidden="true" />}
    </button>
  )
}

function ObjectChip({ source, anatomy, state, dispatch }) {
  const selected = state.selectedObject?.source === source && state.selectedObject?.anatomy === anatomy
  const visible = state.layerVisibility[source] && state.layerVisibility[anatomy]
  const label = `${source === 'gt' ? 'Reference' : 'Prediction'} ${anatomy}`
  return (
    <button
      type="button"
      className={`object-chip${selected ? ' active' : ''}${visible ? '' : ' muted'}`}
      onClick={() => dispatch({
        type: selected ? 'CLEAR_SELECTION' : 'SELECT_OBJECT',
        value: selected ? null : { source, anatomy },
      })}
      aria-pressed={selected}
      title={`${selected ? 'Clear' : 'Focus'} ${label.toLowerCase()}`}
    >
      <i style={{ '--object-color': REVIEW_COLORS[source][anatomy] }} aria-hidden="true" />
      <span>{anatomy === 'lesion' ? 'Lesion' : 'Pancreas'}</span>
      <small>{source === 'gt' ? 'Truth' : 'Model'}</small>
    </button>
  )
}

function DifferenceChip({ region, state, dispatch, disabled = false }) {
  const anatomy = state.anatomyFocus === 'lesion' ? 'lesion' : 'pancreas'
  const selected = state.selectedObject?.source === 'difference'
    && state.selectedObject?.anatomy === anatomy
    && state.selectedObject?.region === region
  const meta = {
    agreement: ['Agreement', REVIEW_COLORS.difference.agreement],
    predOnly: ['Prediction only', REVIEW_COLORS.difference.predOnly],
    gtOnly: ['Reference only', REVIEW_COLORS.difference.gtOnly],
  }[region]
  return (
    <button
      type="button"
      className={`object-chip difference-chip${selected ? ' active' : ''}`}
      onClick={() => dispatch({
        type: selected ? 'CLEAR_SELECTION' : 'SELECT_OBJECT',
        value: selected ? null : { source: 'difference', anatomy, region },
      })}
      disabled={disabled}
      aria-pressed={selected}
      title={disabled ? `No ${meta[0].toLowerCase()} 3D surface exists for this case` : `Focus ${meta[0].toLowerCase()} ${anatomy}`}
    >
      <i style={{ '--object-color': meta[1] }} aria-hidden="true" />
      <span>{meta[0]}</span>
      <small>{anatomy}</small>
    </button>
  )
}

function MetricsCard({
  hasResult,
  isCurated,
  liveResult,
  lesionFlagged,
  volumeMm3,
  confidence,
  diameterMm,
  endpointStatus,
  isAnalyzing,
}) {
  if (!hasResult && !isCurated) return null

  const isLive = liveResult?.source === 'live'
  return (
    <section className="review-metrics-card" aria-label="Model finding summary">
      <div className="review-metrics-card__heading">
        <span className={`finding-signal${lesionFlagged ? ' finding-signal--flagged' : ''}`}>
          <CircleDot size={14} aria-hidden="true" />
          {lesionFlagged ? 'Possible lesion flagged' : 'No lesion flagged'}
        </span>
        <span className={`result-source-badge${isLive ? ' result-source-badge--live' : ''}`}>
          {isLive ? <Radio size={11} aria-hidden="true" /> : <Database size={11} aria-hidden="true" />}
          {isLive
            ? `Live · ${liveResult.scoredAt} · ${liveResult.result.inference_seconds.toFixed(1)}s`
            : 'Precomputed'}
        </span>
      </div>
      <div className="review-metrics-card__values">
        <div><span>Volume</span><strong>{(volumeMm3 / 1000).toFixed(2)} <small>cm³</small></strong></div>
        <div><span>Diameter</span><strong>{diameterMm} <small>mm</small></strong></div>
        <div><span>Confidence</span><strong>{Math.round(confidence * 100)}<small>%</small></strong></div>
      </div>
      {endpointStatus === 'offline' && !isAnalyzing && (
        <p className="review-offline-note">
          <WifiOff size={12} aria-hidden="true" />
          endpoint offline — showing cached result
        </p>
      )}
    </section>
  )
}

export default function ReviewWorkspace({
  caseId,
  caseData,
  profile,
  caseItems,
  isCurated,
  hasLiveResult,
  liveResult,
  isAnalyzing,
  endpointStatus,
  truthRevealed,
  reviewStatus,
  finding,
  overlap,
  onSelectScan,
  onAnalyze,
  onRevealTruth,
  onResetScan,
  onSetReviewStatus,
  onOpenComparison,
  onOpenLibrary,
}) {
  const hasPrediction = isCurated || hasLiveResult
  const truthUnlocked = isCurated || truthRevealed
  const differenceAvailable = Boolean(caseData.files.difference)
  const stage = truthUnlocked ? 3 : hasPrediction ? 2 : 1
  const [state, dispatch] = useReducer(
    reviewReducer,
    { hasPrediction },
    makeReviewState,
  )
  const [navigation, setNavigation] = useState({
    indices: { axial: 0, coronal: 0, sagittal: 0 },
    totals: { axial: 1, coronal: 1, sagittal: 1 },
    ranges: { pancreas: null, lesion: null },
  })
  const [navigationCommand, setNavigationCommand] = useState(null)
  const navigationCommandId = useRef(0)
  const sliceFrameRef = useRef(null)
  const pendingSliceRef = useRef(null)
  const clipFrameRef = useRef(null)
  const pendingClipProgressRef = useRef(null)

  const navigatorPlane = state.activePlane === 'multiplanar'
    ? 'axial'
    : state.activePlane
  const navigatorIndex = navigation.indices[navigatorPlane] || 0
  const navigatorTotal = navigation.totals[navigatorPlane] || 1

  function issueViewerCommand(command) {
    navigationCommandId.current += 1
    setNavigationCommand({ ...command, id: navigationCommandId.current })
  }

  function setSlice(index, { live = false } = {}) {
    const command = {
      type: 'slice',
      plane: navigatorPlane,
      index: Math.max(0, Math.min(navigatorTotal - 1, index)),
    }
    if (!live) {
      if (sliceFrameRef.current !== null) {
        window.cancelAnimationFrame(sliceFrameRef.current)
        sliceFrameRef.current = null
      }
      pendingSliceRef.current = null
      issueViewerCommand(command)
      return
    }

    pendingSliceRef.current = command
    if (sliceFrameRef.current === null) {
      sliceFrameRef.current = window.requestAnimationFrame(() => {
        sliceFrameRef.current = null
        const pending = pendingSliceRef.current
        pendingSliceRef.current = null
        if (pending) issueViewerCommand(pending)
      })
    }
  }

  useEffect(() => {
    if (sliceFrameRef.current !== null) window.cancelAnimationFrame(sliceFrameRef.current)
    if (clipFrameRef.current !== null) window.cancelAnimationFrame(clipFrameRef.current)
    sliceFrameRef.current = null
    clipFrameRef.current = null
    pendingSliceRef.current = null
    pendingClipProgressRef.current = null
    dispatch({ type: 'CASE_CHANGED', hasPrediction: isCurated })
    setNavigation({
      indices: { axial: 0, coronal: 0, sagittal: 0 },
      totals: { axial: 1, coronal: 1, sagittal: 1 },
      ranges: { pancreas: null, lesion: null },
    })
  }, [caseId, isCurated])

  useEffect(() => () => {
    if (sliceFrameRef.current !== null) window.cancelAnimationFrame(sliceFrameRef.current)
    if (clipFrameRef.current !== null) window.cancelAnimationFrame(clipFrameRef.current)
  }, [])

  // The reset above runs on case change, when an unmarked scan has no prediction yet.
  // When the live result lands, `hasPrediction` flips true but that effect does not
  // re-run (and must not — it would reset the whole view), so advance the evidence mode
  // here. Without this the predicted mask loads but the viewer stays on the bare CT.
  useEffect(() => {
    if (hasPrediction) dispatch({ type: 'PREDICTION_READY' })
  }, [hasPrediction])

  useEffect(() => {
    function handleKeyDown(event) {
      const tagName = event.target?.tagName?.toLowerCase()
      if (tagName === 'input' || tagName === 'select' || tagName === 'textarea') return
      if (event.key === 'Escape') dispatch({ type: 'CLEAR_SELECTION' })
      if (state.viewMode === '2d' && ['ArrowLeft', 'ArrowDown'].includes(event.key)) {
        event.preventDefault()
        setSlice(navigatorIndex - 1)
      }
      if (state.viewMode === '2d' && ['ArrowRight', 'ArrowUp'].includes(event.key)) {
        event.preventDefault()
        setSlice(navigatorIndex + 1)
      }
      if (event.key.toLowerCase() === 'r') dispatch({ type: 'RESET_VIEW' })
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [state.viewMode, navigatorIndex, navigatorPlane, navigatorTotal])

  const availableSources = useMemo(() => {
    const next = []
    if (hasPrediction) next.push('pred')
    if (truthUnlocked) next.push('gt')
    return next
  }, [hasPrediction, truthUnlocked])

  const visibleSources = useMemo(
    () => visibleSourcesForEvidence(state.evidenceMode, state.sourceFocus, state.layerVisibility),
    [state.evidenceMode, state.sourceFocus, state.layerVisibility],
  )

  const activeEvidenceSources = sourcesForEvidence(state.evidenceMode)
  const viewerLabel = `${caseId} · ${EVIDENCE_META[state.evidenceMode].label}`
  const selectedLabel = objectLabel(state.selectedObject)

  async function analyze() {
    const outcome = await onAnalyze(caseId)
    if (outcome) {
      dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
      dispatch({ type: 'RESET_VIEW' })
    }
  }

  function revealTruth() {
    if (!onRevealTruth()) return
    dispatch({ type: 'SET_EVIDENCE_MODE', value: 'truth' })
  }

  function resetScan() {
    onResetScan()
    dispatch({ type: 'CASE_CHANGED', hasPrediction: false })
  }

  function setEvidenceMode(mode) {
    const unlocked = mode === 'ct'
      || (mode === 'prediction' && hasPrediction)
      || ((mode === 'truth' || mode === 'overlap') && truthUnlocked)
    if (unlocked) dispatch({ type: 'SET_EVIDENCE_MODE', value: mode })
  }

  function setDisplayPreset(value) {
    const preset = DISPLAY_PRESETS[value]
    dispatch({
      type: 'PATCH_SETTINGS',
      value: {
        displayPreset: value,
        overlayOpacity: preset.overlayOpacity,
        ctOpacity: preset.ctOpacity,
      },
    })
  }

  function focusStructure(anatomy) {
    const source = visibleSources.includes('pred')
      ? 'pred'
      : visibleSources.includes('gt')
        ? 'gt'
        : availableSources[0]
    if (!source) return
    dispatch({ type: 'SELECT_OBJECT', value: { source, anatomy } })
    issueViewerCommand({ type: 'focus', source, anatomy })
  }

  function markerStyle(anatomy) {
    const range = navigation.ranges[anatomy]?.[navigatorPlane]
    if (!range || navigatorTotal <= 1) return null
    const start = Math.max(0, Math.min(100, (range[0] / (navigatorTotal - 1)) * 100))
    const end = Math.max(start, Math.min(100, (range[1] / (navigatorTotal - 1)) * 100))
    return {
      left: `${start}%`,
      width: `${Math.max(1, end - start)}%`,
    }
  }

  const pancreasMarker = markerStyle('pancreas')
  const lesionMarker = markerStyle('lesion')
  const planeName = navigatorPlane[0].toUpperCase() + navigatorPlane.slice(1)
  const sliceProgress = navigatorTotal > 1
    ? (navigatorIndex / (navigatorTotal - 1)) * 100
    : 0
  const coronalPancreasRange = navigation.ranges.pancreas?.coronal
  const coronalTotal = navigation.totals.coronal || 1
  const pancreasRevealProgress = coronalPancreasRange && coronalTotal > 1
    ? Math.max(
        1,
        Math.min(
          99,
          Math.round(
            Math.min(
              1,
              (coronalPancreasRange[1] + Math.max(8, Math.round(coronalTotal * 0.08)))
                / (coronalTotal - 1),
            ) * 100,
          ),
        ),
      )
    : null
  const cutStatus = !state.clipEnabled
    ? 'Cut off'
    : state.clipProgress <= 0
      ? 'Full CT'
      : state.clipProgress >= 100
        ? 'Mask only'
        : pancreasRevealProgress !== null
            && Math.abs(state.clipProgress - pancreasRevealProgress) <= 1
          ? 'Pancreas revealed'
          : `${Math.round(state.clipProgress)}% removed`

  function setClipProgress(value, { snapFront = false, live = false } = {}) {
    const nextProgress = Math.max(0, Math.min(100, Number(value)))
    const commit = (progress) => dispatch({
      type: 'PATCH_SETTINGS',
      value: { clipEnabled: true, clipProgress: progress },
    })
    if (!live) {
      if (clipFrameRef.current !== null) {
        window.cancelAnimationFrame(clipFrameRef.current)
        clipFrameRef.current = null
      }
      pendingClipProgressRef.current = null
      commit(nextProgress)
    } else {
      pendingClipProgressRef.current = nextProgress
      if (clipFrameRef.current === null) {
        clipFrameRef.current = window.requestAnimationFrame(() => {
          clipFrameRef.current = null
          const pending = pendingClipProgressRef.current
          pendingClipProgressRef.current = null
          if (pending !== null) commit(pending)
        })
      }
    }
    if (snapFront) {
      issueViewerCommand({ type: 'camera', azimuth: 0, elevation: 0 })
    }
  }

  function setClipEnabled(enabled) {
    dispatch({
      type: 'PATCH_SETTINGS',
      value: { clipEnabled: enabled },
    })
    if (enabled) {
      issueViewerCommand({ type: 'camera', azimuth: 0, elevation: 0 })
    }
  }

  function setViewMode(viewMode) {
    dispatch({ type: 'SET_VIEW_MODE', value: viewMode })
  }

  return (
    <main className={`review-workspace-v2${state.drawerOpen ? '' : ' review-workspace-v2--drawer-closed'}`}>
      <aside className="study-drawer" aria-label="Scan library">
        <div className="study-drawer__header">
          <div>
            <span className="eyebrow">Scan library</span>
            <strong>{caseItems.length} studies</strong>
          </div>
          <button type="button" onClick={() => dispatch({ type: 'TOGGLE_DRAWER' })} aria-label="Collapse scan library">
            <PanelLeftClose size={16} />
          </button>
        </div>
        <div className="study-drawer__list">
          {caseItems.map((item) => (
            <button
              type="button"
              className={`study-drawer__case${item.id === caseId ? ' active' : ''}`}
              key={item.id}
              onClick={() => onSelectScan(item.id)}
            >
              <i className={`case-indicator case-indicator--${item.tone}`} aria-hidden="true" />
              <span>
                <code>{item.shortId}</code>
                <small>{item.label}</small>
              </span>
              <b className={`review-status-dot review-status-dot--${item.status}`} aria-label={item.status} />
            </button>
          ))}
        </div>
        <button className="study-drawer__library" type="button" onClick={onOpenLibrary}>
          <ChevronLeft size={14} aria-hidden="true" />
          Browse all scans
        </button>
      </aside>

      {!state.drawerOpen && (
        <button
          type="button"
          className="study-drawer-open"
          onClick={() => dispatch({ type: 'TOGGLE_DRAWER' })}
          aria-label="Open scan library"
        >
          <PanelLeftOpen size={17} />
        </button>
      )}

      <section className="review-stage">
        <header className="review-command-bar">
          <div className="review-case-title">
            <span className="eyebrow">{profile.eyebrow}</span>
            <div>
              <strong>{caseId.replace('PanTS_', 'PanTS ')}</strong>
              <span>{profile.label}</span>
            </div>
          </div>

          <StageRail stage={stage} curated={isCurated} />

          <div className="review-command-bar__actions">
            <div className="view-mode-control" aria-label="Viewer mode">
              <button
                type="button"
                className={state.viewMode === '2d' ? 'active' : ''}
                onClick={() => setViewMode('2d')}
                aria-pressed={state.viewMode === '2d'}
              >
                <Crosshair size={14} aria-hidden="true" /> 2D
              </button>
              <button
                type="button"
                className={state.viewMode === '3d' ? 'active' : ''}
                onClick={() => setViewMode('3d')}
                aria-pressed={state.viewMode === '3d'}
              >
                <Box size={14} aria-hidden="true" /> 3D
              </button>
            </div>
            <button
              type="button"
              className="review-icon-button"
              onClick={() => dispatch({ type: 'RESET_VIEW' })}
              aria-label="Reset viewer"
              title="Reset viewer"
            >
              <RotateCcw size={15} />
            </button>
            <button
              type="button"
              className={`review-icon-button${state.settingsOpen ? ' active' : ''}`}
              onClick={() => dispatch({ type: 'TOGGLE_SETTINGS' })}
              aria-label="View settings"
              aria-expanded={state.settingsOpen}
            >
              <Settings2 size={16} />
            </button>
          </div>
        </header>

        <div className="evidence-toolbar">
          <div className="evidence-mode-control" aria-label="Evidence mode">
            {['ct', 'prediction', 'truth', 'overlap'].map((mode) => (
              <EvidenceButton
                mode={mode}
                key={mode}
                active={state.evidenceMode === mode}
                unlocked={
                  mode === 'ct'
                  || (mode === 'prediction' && hasPrediction)
                  || ((mode === 'truth' || mode === 'overlap') && truthUnlocked)
                }
                onClick={() => setEvidenceMode(mode)}
              />
            ))}
          </div>

          <span className="evidence-toolbar__divider" aria-hidden="true" />

          <div className="anatomy-focus-control" aria-label="Anatomy focus">
            <span>Highlight</span>
            {['all', 'pancreas', 'lesion'].map((focus) => (
              <button
                type="button"
                key={focus}
                className={state.anatomyFocus === focus ? 'active' : ''}
                onClick={() => dispatch({ type: 'SET_ANATOMY_FOCUS', value: focus })}
                disabled={state.evidenceMode === 'ct'}
                aria-pressed={state.anatomyFocus === focus}
              >
                {focus === 'all' ? 'All' : focus[0].toUpperCase() + focus.slice(1)}
              </button>
            ))}
          </div>

          {state.evidenceMode === 'overlap' && (
            <div className="source-focus-control" aria-label="Overlap source focus">
              <span>Source</span>
              {[
                ['both', 'Both'],
                ['pred', 'Model'],
                ['gt', 'Truth'],
                ['difference', 'Difference'],
              ].map(([value, label]) => (
                <button
                  type="button"
                  key={value}
                  className={state.sourceFocus === value ? 'active' : ''}
                  onClick={() => dispatch({ type: 'SET_SOURCE_FOCUS', value })}
                  disabled={value === 'difference' && !differenceAvailable}
                  aria-pressed={state.sourceFocus === value}
                >
                  {label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="review-viewer-shell">
          <ViewerSuspense>
            <NiivueViewer
              caseData={caseData}
              sources={availableSources}
              visibleSources={visibleSources}
              mode={state.viewMode}
              showFull={state.showFull}
              overlayOpacity={state.overlayOpacity}
              ctOpacity={state.ctOpacity}
              ctWindow={state.ctWindow}
              showPancreas={state.layerVisibility.pancreas}
              showLesion={state.layerVisibility.lesion}
              anatomyFocus={state.anatomyFocus}
              sourceFocus={state.sourceFocus}
              differenceMode={state.evidenceMode === 'overlap' && state.sourceFocus === 'difference'}
              enableDifferenceAssets={truthUnlocked}
              focusTreatment={state.focusTreatment}
              selectedObject={state.selectedObject}
              onSelectObject={(value) => dispatch({
                type: value ? 'SELECT_OBJECT' : 'CLEAR_SELECTION',
                value,
              })}
              activePlane={state.activePlane}
              interactionMode={state.interactionMode}
              navigationCommand={navigationCommand}
              onNavigationChange={setNavigation}
              clip={{
                enabled: state.clipEnabled,
                progress: state.clipProgress,
                depth: clipDepthFromProgress(state.clipProgress),
                azimuth: 0,
                elevation: 0,
              }}
              resetToken={state.resetToken}
              guided
              label={viewerLabel}
            />
          </ViewerSuspense>

          {state.viewMode === '2d' && (
            <div className="viewer-guidance viewer-guidance--2d" aria-label="2D scan navigation">
              <div className="viewer-guidance__row">
                <div className="viewer-control-group viewer-control-group--planes">
                  <span>Plane</span>
                  {[
                    ['multiplanar', 'All 3'],
                    ['axial', 'Axial'],
                    ['coronal', 'Coronal'],
                    ['sagittal', 'Sagittal'],
                  ].map(([value, label]) => (
                    <button
                      type="button"
                      key={value}
                      className={state.activePlane === value ? 'active' : ''}
                      onClick={() => dispatch({ type: 'SET_ACTIVE_PLANE', value })}
                      aria-pressed={state.activePlane === value}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <i className="viewer-guidance__divider" aria-hidden="true" />

                <div className="viewer-control-group">
                  <span>Mouse</span>
                  {[
                    ['navigate', 'Navigate', 'Click or drag the crosshair; scroll through slices'],
                    ['pan', 'Pan + zoom', 'Drag to reposition; scroll to zoom'],
                    ['window', 'CT contrast', 'Drag to adjust CT brightness and contrast'],
                  ].map(([value, label, title]) => (
                    <button
                      type="button"
                      key={value}
                      className={state.interactionMode === value ? 'active' : ''}
                      onClick={() => dispatch({ type: 'SET_INTERACTION_MODE', value })}
                      aria-pressed={state.interactionMode === value}
                      title={title}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <i className="viewer-guidance__divider" aria-hidden="true" />

                <div className="viewer-control-group viewer-control-group--jumps">
                  <span>Jump to</span>
                  <button
                    type="button"
                    onClick={() => focusStructure('pancreas')}
                    disabled={!availableSources.length || !navigation.ranges.pancreas}
                  >
                    Pancreas
                  </button>
                  <button
                    type="button"
                    onClick={() => focusStructure('lesion')}
                    disabled={!availableSources.length || !navigation.ranges.lesion}
                  >
                    Lesion
                  </button>
                  <button
                    type="button"
                    onClick={() => issueViewerCommand({ type: 'fit' })}
                    title="Fit the complete CT in the viewer"
                  >
                    Fit CT
                  </button>
                </div>
              </div>

              <div className="slice-navigator">
                <div className="slice-navigator__readout">
                  <strong>{planeName}</strong>
                  <span>slice</span>
                  <code>{navigatorIndex + 1} / {navigatorTotal}</code>
                </div>
                <button
                  type="button"
                  onClick={() => setSlice(navigatorIndex - 1)}
                  disabled={navigatorIndex <= 0}
                  aria-label={`Previous ${planeName.toLowerCase()} slice`}
                  title="Previous slice (←)"
                >
                  <ChevronLeft size={13} aria-hidden="true" />
                </button>
                <div
                  className="slice-navigator__track"
                  style={{ '--slice-progress': `${sliceProgress}%` }}
                >
                  {pancreasMarker && (
                    <i
                      className="slice-range slice-range--pancreas"
                      style={pancreasMarker}
                      title="Slices containing pancreas"
                    />
                  )}
                  {lesionMarker && (
                    <i
                      className="slice-range slice-range--lesion"
                      style={lesionMarker}
                      title="Slices containing lesion"
                    />
                  )}
                  <input
                    type="range"
                    min="0"
                    max={Math.max(0, navigatorTotal - 1)}
                    step="1"
                    value={Math.min(navigatorIndex, navigatorTotal - 1)}
                    onChange={(event) => setSlice(Number(event.target.value), { live: true })}
                    aria-label={`${planeName} slice`}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => setSlice(navigatorIndex + 1)}
                  disabled={navigatorIndex >= navigatorTotal - 1}
                  aria-label={`Next ${planeName.toLowerCase()} slice`}
                  title="Next slice (→)"
                >
                  <ChevronRight size={13} aria-hidden="true" />
                </button>
                <div className="slice-navigator__legend" aria-label="Slice range markers">
                  <span><i className="pancreas" /> Pancreas</span>
                  <span><i className="lesion" /> Lesion</span>
                </div>
              </div>
            </div>
          )}

          {state.viewMode === '3d' && (
            <>
              <div className="viewer-guidance viewer-guidance--3d" aria-label="3D scan controls">
                <div className="viewer-guidance__row">
                  <div className="viewer-control-group">
                    <span>Mouse</span>
                    <button
                      type="button"
                      className={state.interactionMode === 'rotate' ? 'active' : ''}
                      onClick={() => dispatch({ type: 'SET_INTERACTION_MODE', value: 'rotate' })}
                      aria-pressed={state.interactionMode === 'rotate'}
                      title="Drag to rotate the camera"
                    >
                      Rotate
                    </button>
                    <button
                      type="button"
                      className={state.interactionMode === 'move' ? 'active' : ''}
                      onClick={() => dispatch({ type: 'SET_INTERACTION_MODE', value: 'move' })}
                      aria-pressed={state.interactionMode === 'move'}
                      title="Drag to reframe the anatomy"
                    >
                      Move
                    </button>
                  </div>

                  <i className="viewer-guidance__divider" aria-hidden="true" />

                  <div className="viewer-control-group viewer-control-group--jumps">
                    <span>Center</span>
                    <button
                      type="button"
                      onClick={() => focusStructure('pancreas')}
                      disabled={!availableSources.length || !navigation.ranges.pancreas}
                    >
                      Pancreas
                    </button>
                    <button
                      type="button"
                      onClick={() => focusStructure('lesion')}
                      disabled={!availableSources.length || !navigation.ranges.lesion}
                    >
                      Lesion
                    </button>
                    <button type="button" onClick={() => issueViewerCommand({ type: 'fit' })}>
                      Fit scan
                    </button>
                  </div>

                  <i className="viewer-guidance__divider" aria-hidden="true" />

                  <div className="viewer-control-group viewer-control-group--zoom">
                    <span>Zoom</span>
                    <button
                      type="button"
                      onClick={() => issueViewerCommand({ type: 'zoom', factor: 0.86 })}
                      aria-label="Zoom out"
                    >
                      −
                    </button>
                    <button
                      type="button"
                      onClick={() => issueViewerCommand({ type: 'zoom', factor: 1.16 })}
                      aria-label="Zoom in"
                    >
                      +
                    </button>
                  </div>

                  <i className="viewer-guidance__divider" aria-hidden="true" />

                  <div className="viewer-control-group">
                    <span>View</span>
                    <button
                      type="button"
                      onClick={() => issueViewerCommand({ type: 'camera', azimuth: 0, elevation: 0 })}
                      title="Return to the anatomical front view without changing the cut"
                    >
                      Return to front
                    </button>
                  </div>
                </div>

                <div className="front-cut-control">
                  <div className="front-cut-control__identity">
                    <span>CT cutaway</span>
                    <strong>Front <i>→</i> Back</strong>
                  </div>
                  <div className="front-cut-control__presets" aria-label="Front-to-back CT removal presets">
                    <button
                      type="button"
                      className={state.clipEnabled && state.clipProgress === 0 ? 'active' : ''}
                      onClick={() => setClipProgress(0, { snapFront: true })}
                    >
                      Full scan
                    </button>
                    <button
                      type="button"
                      className={
                        state.clipEnabled
                          && pancreasRevealProgress !== null
                          && Math.abs(state.clipProgress - pancreasRevealProgress) <= 1
                          ? 'active'
                          : ''
                      }
                      onClick={() => setClipProgress(pancreasRevealProgress, { snapFront: true })}
                      disabled={pancreasRevealProgress === null}
                    >
                      Pancreas
                    </button>
                    <button
                      type="button"
                      className={state.clipEnabled && state.clipProgress === 100 ? 'active' : ''}
                      onClick={() => setClipProgress(100, { snapFront: true })}
                    >
                      Masks only
                    </button>
                  </div>
                  <div
                    className="front-cut-control__track"
                    style={{ '--cut-progress': `${state.clipProgress}%` }}
                  >
                    {pancreasRevealProgress !== null && (
                      <i
                        className="front-cut-control__pancreas-marker"
                        style={{ left: `${pancreasRevealProgress}%` }}
                        title={`Pancreas is revealed near ${pancreasRevealProgress}% removal`}
                      />
                    )}
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="1"
                      value={state.clipProgress}
                      onChange={(event) => setClipProgress(Number(event.target.value), { live: true })}
                      aria-label="Front-to-back CT removal"
                    />
                  </div>
                  <code>{cutStatus}</code>
                </div>
              </div>

              {!state.settingsOpen && (
                <div className="viewer-orientation-pad" aria-label="Snap 3D camera to an anatomical view">
                  <span><Box size={12} aria-hidden="true" /> Snap view</span>
                  <div>
                    {[
                      ['Front', 0, 0],
                      ['Back', 180, 0],
                      ['Left', 90, 0],
                      ['Right', 270, 0],
                      ['Top', 0, 90],
                      ['Bottom', 0, -90],
                    ].map(([label, azimuth, elevation]) => (
                      <button
                        type="button"
                        key={label}
                        onClick={() => issueViewerCommand({ type: 'camera', azimuth, elevation })}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="viewer-orientation-pad__home"
                    onClick={() => issueViewerCommand({ type: 'camera', azimuth: 120, elevation: 15 })}
                  >
                    Home angle
                  </button>
                </div>
              )}
            </>
          )}

          {state.evidenceMode === 'ct' && !hasPrediction && (
            <div className="analyze-hero">
              <span><ScanLine size={18} aria-hidden="true" /></span>
              <small>Stage 1 · Clean CT</small>
              <h2>Inspect first. Then let the model draw.</h2>
              <p>No prediction or reference annotation is visible.</p>
              <button type="button" onClick={analyze} disabled={isAnalyzing}>
                {isAnalyzing
                  ? <LoaderCircle size={16} className="spin" aria-hidden="true" />
                  : <Activity size={16} aria-hidden="true" />}
                {isAnalyzing ? 'Scoring scan…' : 'Analyze scan'}
              </button>
              {endpointStatus === 'offline' && !isAnalyzing && (
                <small className="analyze-hero__offline">
                  <WifiOff size={11} aria-hidden="true" /> Cached result will keep the demonstration available.
                </small>
              )}
            </div>
          )}

          {activeEvidenceSources.length > 0 && (
            <div className="viewer-object-dock" aria-label="Selectable structures">
              <button
                type="button"
                className={`object-chip object-chip--all${state.anatomyFocus === 'all' ? ' active' : ''}`}
                onClick={() => dispatch({ type: 'CLEAR_SELECTION' })}
                aria-pressed={state.anatomyFocus === 'all'}
              >
                <Maximize2 size={13} aria-hidden="true" />
                <span>All</span>
              </button>
              {visibleSources.map((source) => (
                <div className="viewer-object-dock__source" key={source}>
                  {state.layerVisibility.pancreas && (
                    <ObjectChip source={source} anatomy="pancreas" state={state} dispatch={dispatch} />
                  )}
                  {state.layerVisibility.lesion && caseData.files.mesh?.[`lesion_${source}`] && (
                    <ObjectChip source={source} anatomy="lesion" state={state} dispatch={dispatch} />
                  )}
                </div>
              ))}
              {state.evidenceMode === 'overlap' && state.sourceFocus === 'difference' && (
                <div className="viewer-object-dock__source viewer-object-dock__source--difference">
                  {[
                    ['agreement', 'agreement'],
                    ['predOnly', 'pred_only'],
                    ['gtOnly', 'gt_only'],
                  ].map(([region, suffix]) => (
                    <DifferenceChip
                      key={region}
                      region={region}
                      state={state}
                      dispatch={dispatch}
                      disabled={
                        state.viewMode === '3d'
                        && !caseData.files.mesh?.[`${state.anatomyFocus === 'lesion' ? 'lesion' : 'pancreas'}_${suffix}`]
                      }
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {state.selectedObject && (
            <div className="viewer-selection-card" role="status">
              <i style={{
                '--selection-color': state.selectedObject.source === 'difference'
                  ? REVIEW_COLORS.difference[state.selectedObject.region]
                  : REVIEW_COLORS[state.selectedObject.source][state.selectedObject.anatomy],
              }} />
              <div>
                <small>Focused structure</small>
                <strong>{selectedLabel}</strong>
              </div>
              <div className="focus-treatment-control" aria-label="Focus treatment">
                <button
                  type="button"
                  className={state.focusTreatment === 'context' ? 'active' : ''}
                  onClick={() => dispatch({ type: 'SET_FOCUS_TREATMENT', value: 'context' })}
                  aria-pressed={state.focusTreatment === 'context'}
                >
                  Context
                </button>
                <button
                  type="button"
                  className={state.focusTreatment === 'isolate' ? 'active' : ''}
                  onClick={() => dispatch({ type: 'SET_FOCUS_TREATMENT', value: 'isolate' })}
                  aria-pressed={state.focusTreatment === 'isolate'}
                >
                  Isolate
                </button>
              </div>
              <button type="button" onClick={() => dispatch({ type: 'CLEAR_SELECTION' })} aria-label="Clear structure focus">
                <X size={14} />
              </button>
            </div>
          )}

          <div className="viewer-mode-note">
            {state.viewMode === '3d'
              ? state.interactionMode === 'move'
                ? 'Move mode · drag to reframe · scroll to zoom'
                : 'Rotate mode · drag to orbit · scroll to zoom · click a surface to focus'
              : state.interactionMode === 'pan'
                ? 'Pan + zoom mode · drag to reposition · scroll to zoom'
                : state.interactionMode === 'window'
                  ? 'CT contrast mode · drag to tune brightness and contrast'
                  : 'Navigate mode · scroll slices · drag the crosshair to synchronize'}
          </div>

          {state.settingsOpen && (
            <aside className="review-settings-popover" aria-label="View settings" tabIndex={0}>
              <div className="review-settings-popover__header">
                <div><Settings2 size={15} /><strong>View settings</strong></div>
                <button type="button" onClick={() => dispatch({ type: 'TOGGLE_SETTINGS' })} aria-label="Close view settings"><X size={14} /></button>
              </div>

              <div className="review-settings-group">
                <span>Display emphasis</span>
                <div className="display-preset-control" aria-label="Display emphasis">
                  {Object.entries(DISPLAY_PRESETS).map(([value, preset]) => (
                    <button
                      type="button"
                      key={value}
                      className={state.displayPreset === value ? 'active' : ''}
                      onClick={() => setDisplayPreset(value)}
                      aria-pressed={state.displayPreset === value}
                      title={preset.description}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
                <small className="ct-window-help">
                  {state.displayPreset === 'custom'
                    ? 'Custom visibility settings are active.'
                    : DISPLAY_PRESETS[state.displayPreset]?.description}
                </small>
              </div>

              <div className="review-settings-group">
                <span>Structures</span>
                <LayerToggle
                  checked={state.layerVisibility.pancreas}
                  label="Pancreas"
                  color={REVIEW_COLORS.pred.pancreas}
                  disabled={state.evidenceMode === 'ct'}
                  onClick={() => dispatch({ type: 'TOGGLE_LAYER', layer: 'pancreas' })}
                />
                <LayerToggle
                  checked={state.layerVisibility.lesion}
                  label="Lesion"
                  color={REVIEW_COLORS.pred.lesion}
                  disabled={state.evidenceMode === 'ct'}
                  onClick={() => dispatch({ type: 'TOGGLE_LAYER', layer: 'lesion' })}
                />
              </div>

              <div className="review-settings-group">
                <span>CT contrast</span>
                <div className="ct-window-control" aria-label="CT contrast preset">
                  {CT_WINDOW_OPTIONS.map(([value, label, description]) => (
                    <button
                      type="button"
                      key={value}
                      className={state.ctWindow === value ? 'active' : ''}
                      onClick={() => dispatch({
                        type: 'PATCH_SETTINGS',
                        value: { ctWindow: value },
                      })}
                      aria-pressed={state.ctWindow === value}
                      title={description}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <small className="ct-window-help">
                  {CT_WINDOW_OPTIONS.find(([value]) => value === state.ctWindow)?.[2]}
                </small>
              </div>

              {state.evidenceMode === 'overlap' && (
                <div className="review-settings-group">
                  <span>Evidence sources</span>
                  <LayerToggle
                    checked={state.layerVisibility.pred}
                    label="Prediction"
                    color={REVIEW_COLORS.pred.pancreas}
                    onClick={() => dispatch({ type: 'TOGGLE_LAYER', layer: 'pred' })}
                  />
                  <LayerToggle
                    checked={state.layerVisibility.gt}
                    label="Source of truth"
                    color={REVIEW_COLORS.gt.lesion}
                    onClick={() => dispatch({ type: 'TOGGLE_LAYER', layer: 'gt' })}
                  />
                </div>
              )}

              <label className="review-range">
                <span>Mask visibility <strong>{Math.round(state.overlayOpacity * 100)}%</strong></span>
                <input
                  type="range"
                  min="0.2"
                  max="1"
                  step="0.05"
                  value={state.overlayOpacity}
                  onChange={(event) => dispatch({
                    type: 'PATCH_SETTINGS',
                    value: {
                      displayPreset: 'custom',
                      overlayOpacity: Number(event.target.value),
                    },
                  })}
                />
              </label>

              <label className="review-layer-check">
                <span><ScanLine size={13} /> Full abdominal CT</span>
                <input
                  type="checkbox"
                  checked={state.showFull}
                  disabled={!caseData.files.ct_full}
                  onChange={(event) => dispatch({
                    type: 'PATCH_SETTINGS',
                    value: { showFull: event.target.checked },
                  })}
                />
              </label>

              {state.viewMode === '3d' && (
                <>
                  <label className="review-range">
                    <span>CT background <strong>{Math.round(state.ctOpacity * 100)}%</strong></span>
                    <input
                      type="range"
                      min="0"
                      max="0.45"
                      step="0.02"
                      value={state.ctOpacity}
                      onChange={(event) => dispatch({
                        type: 'PATCH_SETTINGS',
                        value: {
                          displayPreset: 'custom',
                          ctOpacity: Number(event.target.value),
                        },
                      })}
                    />
                  </label>
                  <label className="review-layer-check">
                    <span><Focus size={13} /> Front-to-back CT cut</span>
                    <input
                      type="checkbox"
                      checked={state.clipEnabled}
                      onChange={(event) => setClipEnabled(event.target.checked)}
                    />
                  </label>
                  {state.clipEnabled && (
                    <>
                      <label className="review-range">
                        <span>CT removed <strong>{Math.round(state.clipProgress)}%</strong></span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          step="1"
                          value={state.clipProgress}
                          onChange={(event) => setClipProgress(Number(event.target.value), { live: true })}
                        />
                      </label>
                      <p className="review-settings-hint">
                        The cut stays anatomical when you rotate the camera.
                      </p>
                    </>
                  )}
                </>
              )}
              <p className="display-mesh-provenance">
                Display surface · {caseData.display_mesh_version
                  ? 'v2, explicit normals'
                  : 'v1, source-grid reconstruction'}
                <span>Metrics remain derived from the original NIfTI masks.</span>
              </p>
            </aside>
          )}
        </div>

        <footer className="review-context-bar">
          <div className="review-context-bar__mode">
            <i className={`review-context-bar__signal review-context-bar__signal--${state.evidenceMode}`} aria-hidden="true" />
            <div>
              <small>Viewing</small>
              <strong>{EVIDENCE_META[state.evidenceMode].label}</strong>
            </div>
            <span>{EVIDENCE_META[state.evidenceMode].description}</span>
          </div>

          <MetricsCard
            hasResult={hasLiveResult}
            isCurated={isCurated}
            liveResult={liveResult}
            lesionFlagged={finding.lesionFlagged}
            volumeMm3={finding.volumeMm3}
            confidence={finding.confidence}
            diameterMm={finding.diameterMm}
            endpointStatus={endpointStatus}
            isAnalyzing={isAnalyzing}
          />

          {!isCurated && hasPrediction && !truthUnlocked && (
            <button className="context-primary-action context-primary-action--truth" type="button" onClick={revealTruth}>
              <Microscope size={15} aria-hidden="true" />
              <span><small>Next</small>Reveal source of truth</span>
              <ChevronRight size={14} aria-hidden="true" />
            </button>
          )}

          {!isCurated && truthUnlocked && (
            <button className="context-secondary-action" type="button" onClick={resetScan}>
              <RotateCcw size={13} aria-hidden="true" />
              Reset / new scan
            </button>
          )}
        </footer>

        {truthUnlocked && state.evidenceMode === 'overlap' && (
          <section className="overlap-payoff" aria-label="Overlap with source of truth">
            <div className="overlap-payoff__title">
              <span><ShieldCheck size={17} aria-hidden="true" /></span>
              <div>
                <small>Scientific comparison</small>
                <strong>Overlap with source of truth</strong>
              </div>
            </div>
            <div className="overlap-payoff__metric">
              <span><i style={{ background: REVIEW_COLORS.gt.pancreas }} />Pancreas Dice</span>
              <strong>{Number.isFinite(overlap.pancreas) ? overlap.pancreas.toFixed(3) : '—'}</strong>
            </div>
            <div className="overlap-payoff__metric">
              <span><i style={{ background: REVIEW_COLORS.gt.lesion }} />Lesion Dice</span>
              <strong>
                {!caseData.gt_has_lesion && !finding.lesionFlagged
                  ? 'No lesion'
                  : Number.isFinite(overlap.lesion) ? overlap.lesion.toFixed(3) : '—'}
              </strong>
              {!caseData.gt_has_lesion && !finding.lesionFlagged && <small>Absent in both masks</small>}
            </div>
            <p>Toggle Model, Truth, Both, or Difference to inspect agreement, over-segmentation, and missed reference regions.</p>
          </section>
        )}

        <GuidedEvidencePanel key={caseId} />
        <div className="review-status-bar">
          <span>Review status</span>
          <button
            type="button"
            className={reviewStatus === 'reviewed' ? 'active' : ''}
            onClick={() => onSetReviewStatus('reviewed')}
          >
            <Check size={13} /> Mark reviewed
          </button>
          <button
            type="button"
            className={reviewStatus === 'discussion' ? 'active' : ''}
            onClick={() => onSetReviewStatus('discussion')}
          >
            <MessageSquareWarning size={13} /> Discuss
          </button>
          {hasPrediction && caseData.files.pred && (
            <a href={`/cases/${caseData.files.pred}`} download>
              <Download size={13} /> Export prediction
            </a>
          )}
          {isCurated && (
            <button type="button" className="review-status-bar__comparison" onClick={onOpenComparison}>
              Scientific comparison <ChevronRight size={13} />
            </button>
          )}
        </div>
      </section>
    </main>
  )
}
