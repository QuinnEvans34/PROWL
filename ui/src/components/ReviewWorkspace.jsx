import { lazy, Suspense, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import {
  Activity,
  Box,
  ChevronLeft,
  ChevronRight,
  Columns2,
  Contrast,
  Crosshair,
  Database,
  Eye,
  EyeOff,
  Focus,
  LoaderCircle,
  Maximize,
  Move,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Rotate3d,
  RotateCcw,
  ScanLine,
  Settings2,
  WifiOff,
  X,
} from 'lucide-react'
import { makeReviewState, reviewReducer } from '../lib/reviewState.js'
import { REVIEW_COLORS, objectLabel, visibleSourcesForEvidence, EVIDENCE_META } from '../lib/viewerLayers.js'
import FindingsPanel from './FindingsPanel.jsx'
import { PantherBadge } from '../shell/Brand.jsx'

const NiivueViewer = lazy(() => import('./NiivueViewer.jsx'))

const DISPLAY_PRESETS = {
  anatomy: { label: 'CT detail', description: 'Makes the CT anatomy easiest to read', overlayOpacity: 0.62, ctOpacity: 0.44 },
  balanced: { label: 'Balanced', description: 'Keeps both the CT and model contours clear', overlayOpacity: 0.62, ctOpacity: 0.18 },
  masks: { label: 'Masks', description: 'Emphasizes the pancreas and lesion overlays', overlayOpacity: 0.84, ctOpacity: 0.07 },
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
  return FRONT_CUT_DEPTH_MIN + fraction * (FRONT_CUT_DEPTH_MAX - FRONT_CUT_DEPTH_MIN)
}

function evidenceModeFor(prediction, reference) {
  if (prediction && reference) return 'overlap'
  if (prediction) return 'prediction'
  if (reference) return 'truth'
  return 'ct'
}

function ViewerSuspense({ children }) {
  return (
    <Suspense fallback={<div className="viewer-module-loading" role="status">Preparing medical viewer…</div>}>
      {children}
    </Suspense>
  )
}

function Segmented({ label, value, options, onChange, disabled = false, className = '' }) {
  return (
    <div className={`pw-segmented ${className}`} role="group" aria-label={label}>
      {options.map(([key, text, extra = {}]) => (
        <button
          type="button"
          key={key}
          aria-pressed={value === key}
          onClick={() => onChange(key)}
          disabled={disabled || extra.disabled}
          title={extra.title}
          aria-label={extra.ariaLabel || (extra.icon ? text : undefined)}
        >
          {extra.icon}{extra.icon ? <span className="pw-seg-text">{text}</span> : text}
        </button>
      ))}
    </div>
  )
}

function LayerToggle({ checked, label, sublabel, color, onClick, disabled = false, title }) {
  return (
    <button type="button" className="pw-layer" onClick={onClick} disabled={disabled} aria-pressed={checked} title={title}>
      <span className="pw-layer__check" aria-hidden="true">{checked ? <Eye size={13} /> : <EyeOff size={13} />}</span>
      <i style={{ '--layer-color': color }} aria-hidden="true" />
      <span>{label}{sublabel && <small>{sublabel}</small>}</span>
    </button>
  )
}

// Split = two NiiVue instances (2D planes + 3D surfaces) sharing one review state:
// layers, selection, focus/Go-to, reset, window and slice commands go to both.
// The 3D camera stays independent; 3D crosshair display is not enabled.
const SPLIT_SUPPORTED = true

export default function ReviewWorkspace({
  caseId,
  caseData,
  profile,
  caseItems,
  isCurated,
  hasLiveResult,
  liveResult,
  isAnalyzing,
  analysisFailed = false,
  endpointStatus,
  truthRevealed,
  reviewStatus,
  finding,
  overlap,
  referenceCompatibility = 'compatible',
  modelLabel = 'Segmenter v1 · step 18000',
  askPanel = null,
  assistantPending = false,
  summaryPanel = null,
  summaryStatus = null,
  onSelectScan,
  onAnalyze,
  onShowSavedPrediction,
  onRevealTruth,
  onResetScan,
  onSetReviewStatus,
  onOpenComparison,
  onOpenLibrary,
}) {
  const hasPrediction = isCurated || hasLiveResult
  const truthUnlocked = isCurated || truthRevealed
  const differenceAvailable = Boolean(caseData.files?.difference)
  const referenceFile = Boolean(caseData.files?.gt)
  const referenceState = !referenceFile
    ? 'absent'
    : referenceCompatibility === 'incompatible'
      ? 'incompatible'
      : truthUnlocked
        ? 'ready'
        : hasPrediction
          ? 'permitted'
          : 'locked'

  const [state, dispatch] = useReducer(reviewReducer, { hasPrediction }, makeReviewState)
  // Layout chrome is reviewer preference, not study state: it survives study changes.
  const [studyListOpen, setStudyListOpen] = useState(() => (typeof window === 'undefined' ? true : window.innerWidth >= 1360))
  const [panelOpen, setPanelOpen] = useState(() => (typeof window === 'undefined' ? true : window.innerWidth >= 1024))
  const [panelTab, setPanelTab] = useState('findings')
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

  const navigatorPlane = state.activePlane === 'multiplanar' ? 'axial' : state.activePlane
  const navigatorIndex = navigation.indices[navigatorPlane] || 0
  const navigatorTotal = navigation.totals[navigatorPlane] || 1

  function issueViewerCommand(command) {
    navigationCommandId.current += 1
    setNavigationCommand({ ...command, id: navigationCommandId.current })
  }

  function setSlice(index, { live = false } = {}) {
    const command = { type: 'slice', plane: navigatorPlane, index: Math.max(0, Math.min(navigatorTotal - 1, index)) }
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

  // A prediction became available for a study that opened CT-only: advance from the
  // bare CT to the model proposal without resetting the rest of the view.
  useEffect(() => {
    if (hasPrediction) dispatch({ type: 'PREDICTION_READY' })
  }, [hasPrediction])

  useEffect(() => {
    function handleKeyDown(event) {
      const target = event.target
      const tagName = target?.tagName?.toLowerCase()
      if (tagName === 'input' || tagName === 'select' || tagName === 'textarea' || target?.isContentEditable) return
      if (event.metaKey || event.ctrlKey || event.altKey) return
      if (target?.closest?.('[role="dialog"], .pw-panel')) return
      if (event.key === 'Escape') dispatch({ type: 'CLEAR_SELECTION' })
      if (state.viewMode !== '3d' && ['ArrowLeft', 'ArrowDown'].includes(event.key)) {
        event.preventDefault()
        setSlice(navigatorIndex - 1)
      }
      if (state.viewMode !== '3d' && ['ArrowRight', 'ArrowUp'].includes(event.key)) {
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
    if (truthUnlocked && referenceState === 'ready') next.push('gt')
    return next
  }, [hasPrediction, truthUnlocked, referenceState])

  const visibleSources = useMemo(
    () => visibleSourcesForEvidence(state.evidenceMode, state.sourceFocus, state.layerVisibility),
    [state.evidenceMode, state.sourceFocus, state.layerVisibility],
  )

  const predictionShown = state.evidenceMode === 'prediction' || state.evidenceMode === 'overlap'
  const referenceShown = state.evidenceMode === 'truth' || state.evidenceMode === 'overlap'
  const comparing = referenceShown && referenceState === 'ready'
  const viewerLabel = `${caseId} · ${EVIDENCE_META[state.evidenceMode].label}`
  const selectedLabel = objectLabel(state.selectedObject)
  const studyLabel = caseId.replace('PanTS_', 'PanTS ')

  async function analyze() {
    const outcome = await onAnalyze(caseId)
    if (outcome) {
      dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
      dispatch({ type: 'RESET_VIEW' })
    }
  }

  function showSaved() {
    if (onShowSavedPrediction?.(caseId)) dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
  }

  function setLayers(prediction, reference) {
    const mode = evidenceModeFor(prediction && hasPrediction, reference && truthUnlocked && referenceState === 'ready')
    dispatch({ type: 'SET_EVIDENCE_MODE', value: mode })
  }

  function compareWithReference() {
    if (referenceState === 'permitted') {
      if (!onRevealTruth()) return
      dispatch({ type: 'SET_EVIDENCE_MODE', value: 'overlap' })
      return
    }
    if (referenceState === 'ready') setLayers(true, true)
  }

  function endComparison() {
    setLayers(hasPrediction, false)
  }

  function resetScan() {
    onResetScan()
    dispatch({ type: 'CASE_CHANGED', hasPrediction: false })
  }

  function setDisplayPreset(value) {
    const preset = DISPLAY_PRESETS[value]
    dispatch({ type: 'PATCH_SETTINGS', value: { displayPreset: value, overlayOpacity: preset.overlayOpacity, ctOpacity: preset.ctOpacity } })
  }

  function focusStructure(anatomy) {
    const source = visibleSources.includes('pred') ? 'pred' : visibleSources.includes('gt') ? 'gt' : availableSources[0]
    if (!source) return
    if (!predictionShown && source === 'pred') setLayers(true, referenceShown)
    dispatch({ type: 'SELECT_OBJECT', value: { source, anatomy } })
    issueViewerCommand({ type: 'focus', source, anatomy })
  }

  function markerStyle(anatomy) {
    const range = navigation.ranges[anatomy]?.[navigatorPlane]
    if (!range || navigatorTotal <= 1) return null
    const start = Math.max(0, Math.min(100, (range[0] / (navigatorTotal - 1)) * 100))
    const end = Math.max(start, Math.min(100, (range[1] / (navigatorTotal - 1)) * 100))
    return { left: `${start}%`, width: `${Math.max(1, end - start)}%` }
  }

  const pancreasMarker = markerStyle('pancreas')
  const lesionMarker = markerStyle('lesion')
  const planeName = navigatorPlane[0].toUpperCase() + navigatorPlane.slice(1)
  const sliceProgress = navigatorTotal > 1 ? (navigatorIndex / (navigatorTotal - 1)) * 100 : 0
  const coronalPancreasRange = navigation.ranges.pancreas?.coronal
  const coronalTotal = navigation.totals.coronal || 1
  const pancreasRevealProgress = coronalPancreasRange && coronalTotal > 1
    ? Math.max(1, Math.min(99, Math.round(Math.min(1, (coronalPancreasRange[1] + Math.max(8, Math.round(coronalTotal * 0.08))) / (coronalTotal - 1)) * 100)))
    : null
  const cutStatus = !state.clipEnabled
    ? 'Cut off'
    : state.clipProgress <= 0
      ? 'Full CT'
      : state.clipProgress >= 100
        ? 'Mask only'
        : pancreasRevealProgress !== null && Math.abs(state.clipProgress - pancreasRevealProgress) <= 1
          ? 'Pancreas revealed'
          : `${Math.round(state.clipProgress)}% removed`

  function setClipProgress(value, { snapFront = false, live = false } = {}) {
    const nextProgress = Math.max(0, Math.min(100, Number(value)))
    const commit = (progress) => dispatch({ type: 'PATCH_SETTINGS', value: { clipEnabled: true, clipProgress: progress } })
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
    if (snapFront) issueViewerCommand({ type: 'camera', azimuth: 0, elevation: 0 })
  }

  function setClipEnabled(enabled) {
    dispatch({ type: 'PATCH_SETTINGS', value: { clipEnabled: enabled } })
    if (enabled) issueViewerCommand({ type: 'camera', azimuth: 0, elevation: 0 })
  }

  function setViewMode(viewMode) {
    if (viewMode === 'split' && !SPLIT_SUPPORTED) return
    dispatch({ type: 'SET_VIEW_MODE', value: viewMode })
  }

  const is2dLike = state.viewMode !== '3d'
  const is3dLike = state.viewMode !== '2d'
  const viewerProps = {
    caseData,
    sources: availableSources,
    visibleSources,
    showFull: state.showFull,
    overlayOpacity: state.overlayOpacity,
    ctOpacity: state.ctOpacity,
    ctWindow: state.ctWindow,
    showPancreas: state.layerVisibility.pancreas,
    showLesion: state.layerVisibility.lesion,
    anatomyFocus: state.anatomyFocus,
    sourceFocus: state.sourceFocus,
    differenceMode: state.evidenceMode === 'overlap' && state.sourceFocus === 'difference',
    enableDifferenceAssets: truthUnlocked && referenceState === 'ready',
    focusTreatment: state.focusTreatment,
    selectedObject: state.selectedObject,
    onSelectObject: (value) => dispatch({ type: value ? 'SELECT_OBJECT' : 'CLEAR_SELECTION', value }),
    activePlane: state.activePlane,
    navigationCommand,
    clip: {
      enabled: state.clipEnabled,
      progress: state.clipProgress,
      depth: clipDepthFromProgress(state.clipProgress),
      azimuth: 0,
      elevation: 0,
    },
    resetToken: state.resetToken,
    guided: true,
  }

  function openPanel(tab) {
    setPanelTab(tab)
    setPanelOpen(true)
  }

  const snapPad = state.settingsOpen ? null : (
    <div className="pw-snap" role="group" aria-label="Snap 3D camera to an anatomical view">
                {[['Front', 0, 0], ['Back', 180, 0], ['Left', 90, 0], ['Right', 270, 0], ['Top', 0, 90], ['Bottom', 0, -90]].map(([label, azimuth, elevation]) => (
                  <button type="button" key={label} onClick={() => issueViewerCommand({ type: 'camera', azimuth, elevation })}>{label}</button>
                ))}
                <button type="button" onClick={() => issueViewerCommand({ type: 'camera', azimuth: 120, elevation: 15 })}>Home</button>
              </div>
  )

  const predictionStatus = !caseData.files?.pred
    ? 'No prediction available'
    : isAnalyzing
      ? 'Analysis running…'
      : hasPrediction
        ? liveResult?.source === 'live' ? `Live prediction · ${liveResult.scoredAt}` : 'Saved prediction'
        : 'Prediction hidden'

  const wbClass = [
    'pw-wb',
    studyListOpen ? '' : 'pw-wb--list-closed',
    panelOpen ? '' : 'pw-wb--panel-closed',
  ].filter(Boolean).join(' ')

  return (
    <main className={wbClass} aria-label={`Workbench · ${studyLabel}`}>
      <aside className="pw-wb__list" aria-label="Study list" inert={studyListOpen ? undefined : ''}>
        <div className="pw-wb__list-head">
          <strong>Studies</strong>
          <span className="pw-muted">{caseItems.length}</span>
          <button type="button" className="pw-icon-btn" onClick={() => setStudyListOpen(false)} aria-label="Collapse study list" title="Collapse study list">
            <PanelLeftClose size={16} aria-hidden="true" />
          </button>
        </div>
        <ul className="pw-wb__list-items">
          {caseItems.map((item) => (
            <li key={item.id}>
              <button type="button" className={item.id === caseId ? 'is-active' : ''} aria-current={item.id === caseId ? 'true' : undefined} onClick={() => onSelectScan(item.id)}>
                <code>{item.shortId}</code>
                <small>{item.label}</small>
                {item.status !== 'unreviewed' && <i className={`pw-mark-dot pw-mark-dot--${item.status}`} title={item.status === 'reviewed' ? 'Marked reviewed (local)' : 'Marked for discussion (local)'} aria-label={item.status === 'reviewed' ? 'Marked reviewed' : 'Marked for discussion'} />}
              </button>
            </li>
          ))}
        </ul>
        <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm pw-wb__list-all" onClick={onOpenLibrary}>
          <ChevronLeft size={14} aria-hidden="true" /> All studies
        </button>
      </aside>

      <section className="pw-wb__center">
        <header className="pw-studybar">
          {!studyListOpen && (
            <button type="button" className="pw-icon-btn" onClick={() => setStudyListOpen(true)} aria-label="Open study list" title="Open study list">
              <PanelLeftOpen size={16} aria-hidden="true" />
            </button>
          )}
          <div className="pw-studybar__id">
            <h1>{studyLabel}</h1>
            <span className="pw-tag">{isCurated ? 'Validation example' : 'Prepared study'}</span>
          </div>
          <dl className="pw-studybar__meta">
            <div><dt>Series</dt><dd>Abdomen CT · {Array.isArray(caseData.spacing_mm) ? `${caseData.spacing_mm[0]} mm` : 'spacing not recorded'}</dd></div>
            <div><dt>Prediction</dt><dd>{predictionStatus}</dd></div>
            {summaryStatus && <div><dt>Summary</dt><dd>{summaryStatus}</dd></div>}
          </dl>
          <div className="pw-studybar__actions">
            {isCurated && (
              <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={onOpenComparison} title="Open the three-view validation comparison">
                <Columns2 size={14} aria-hidden="true" /> Validation view
              </button>
            )}
            <button type="button" className="pw-btn pw-btn--primary pw-btn--sm" onClick={() => openPanel('summary')}>
              Review summary
            </button>
            <button
              type="button"
              className="pw-icon-btn"
              onClick={() => setPanelOpen((open) => !open)}
              aria-label={panelOpen ? 'Hide assistant panel' : 'Show assistant panel'}
              aria-expanded={panelOpen}
              aria-controls="pw-assistant"
              title={panelOpen ? 'Hide assistant panel' : 'Show assistant panel'}
            >
              {panelOpen ? <PanelRightClose size={16} aria-hidden="true" /> : <PanelRightOpen size={16} aria-hidden="true" />}
            </button>
          </div>
        </header>

        <div className="pw-toolbar" role="toolbar" aria-label="Viewer tools">
          <Segmented
            label="Viewer mode"
            value={state.viewMode}
            onChange={setViewMode}
            options={[
              ['2d', '2D', { icon: <Crosshair size={14} aria-hidden="true" /> }],
              ['3d', '3D', { icon: <Box size={14} aria-hidden="true" /> }],
              ['split', 'Split', {
                icon: <Columns2 size={14} aria-hidden="true" />,
                disabled: !SPLIT_SUPPORTED,
                title: 'Split: 2D planes and 3D surfaces side by side, sharing layers, selection and Go-to',
              }],
            ]}
          />
          {is2dLike && (
            <Segmented
              label="Plane"
              value={state.activePlane}
              onChange={(value) => dispatch({ type: 'SET_ACTIVE_PLANE', value })}
              options={[['multiplanar', 'All 3'], ['axial', 'Axial'], ['coronal', 'Coronal'], ['sagittal', 'Sagittal']]}
            />
          )}
          <Segmented
            label="Mouse tool"
            value={state.interactionMode}
            onChange={(value) => dispatch({ type: 'SET_INTERACTION_MODE', value })}
            options={state.viewMode === '3d'
              ? [['rotate', 'Rotate', { icon: <Rotate3d size={14} aria-hidden="true" />, title: 'Rotate: drag to orbit the camera' }], ['move', 'Move', { icon: <Move size={14} aria-hidden="true" />, title: 'Move: drag to reframe the anatomy' }]]
              : [
                  ['navigate', 'Navigate', { icon: <Crosshair size={14} aria-hidden="true" />, title: 'Navigate: click or drag the crosshair; scroll through slices' }],
                  ['pan', 'Pan + zoom', { icon: <Move size={14} aria-hidden="true" />, title: 'Pan + zoom: drag to reposition; scroll to zoom' }],
                  ['window', 'Window', { icon: <Contrast size={14} aria-hidden="true" />, title: 'Window: drag to adjust CT brightness and contrast' }],
                ]}
          />
          <label className="pw-select pw-toolbar__window">
            <span className="pw-sr-only">CT window preset</span>
            <select value={state.ctWindow} onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { ctWindow: event.target.value } })}>
              {CT_WINDOW_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <span className="pw-toolbar__spacer" />
          {is3dLike && (
            <div className="pw-toolbar__group" role="group" aria-label="3D zoom">
              <button type="button" className="pw-icon-btn" onClick={() => issueViewerCommand({ type: 'zoom', factor: 0.86 })} aria-label="Zoom out" title="Zoom out">−</button>
              <button type="button" className="pw-icon-btn" onClick={() => issueViewerCommand({ type: 'zoom', factor: 1.16 })} aria-label="Zoom in" title="Zoom in">+</button>
            </div>
          )}
          <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={() => issueViewerCommand({ type: 'fit' })} title="Fit the complete CT in the viewer">
            <Maximize size={14} aria-hidden="true" /> Fit
          </button>
          <button type="button" className="pw-icon-btn" onClick={() => dispatch({ type: 'RESET_VIEW' })} aria-label="Reset viewer" title="Reset viewer (R)">
            <RotateCcw size={15} aria-hidden="true" />
          </button>
          <button
            type="button"
            className={`pw-icon-btn${state.settingsOpen ? ' active' : ''}`}
            onClick={() => dispatch({ type: 'TOGGLE_SETTINGS' })}
            aria-label="View settings"
            aria-expanded={state.settingsOpen}
            title="View settings"
          >
            <Settings2 size={16} aria-hidden="true" />
          </button>
        </div>

        <div className="pw-viewer">
          <ViewerSuspense>
            {state.viewMode === 'split' ? (
              <div className="pw-split">
                <section className="pw-split__pane" aria-label="2D planes">
                  <span className="pw-split__label">2D planes</span>
                  <NiivueViewer {...viewerProps} mode="2d" interactionMode={state.interactionMode} onNavigationChange={setNavigation} label={`${viewerLabel} · 2D planes`} />
                </section>
                <section className="pw-split__pane" aria-label="3D surfaces">
                  <span className="pw-split__label">3D surfaces <small>camera independent</small></span>
                  <NiivueViewer {...viewerProps} mode="3d" interactionMode="rotate" label={`${viewerLabel} · 3D surfaces`} />
                  {snapPad}
                </section>
              </div>
            ) : (
              <NiivueViewer
                {...viewerProps}
                mode={state.viewMode}
                interactionMode={state.interactionMode}
                onNavigationChange={setNavigation}
                label={viewerLabel}
              />
            )}
          </ViewerSuspense>

          {state.viewMode === '3d' && snapPad}

          {state.evidenceMode === 'ct' && !hasPrediction && (
            <div className="pw-ct-only" role="region" aria-label="Prediction not shown">
              <strong>CT only</strong>
              <span>Model outlines are hidden.</span>
              <div>
                {endpointStatus === 'online' && (
                  <button type="button" className="pw-btn pw-btn--primary pw-btn--sm" onClick={analyze} disabled={isAnalyzing}>
                    {isAnalyzing ? <LoaderCircle size={14} className="spin" aria-hidden="true" /> : <Activity size={14} aria-hidden="true" />}
                    {isAnalyzing ? 'Analyzing…' : 'Analyze live'}
                  </button>
                )}
                {caseData.files?.pred && !isAnalyzing && (
                  <button type="button" className={`pw-btn pw-btn--sm ${endpointStatus === 'online' ? 'pw-btn--secondary' : 'pw-btn--primary'}`} onClick={showSaved}>
                    <Database size={14} aria-hidden="true" /> Show saved prediction
                  </button>
                )}
              </div>
              {analysisFailed && (
                <small role="alert"><WifiOff size={11} aria-hidden="true" /> Live analysis failed or is offline. No new prediction was produced.</small>
              )}
              {!analysisFailed && endpointStatus !== 'online' && caseData.files?.pred && (
                <small><WifiOff size={11} aria-hidden="true" /> Live analysis offline · the saved prediction was produced earlier.</small>
              )}
            </div>
          )}

          {state.selectedObject && (
            <div className="viewer-selection-card pw-selection" role="status">
              <i style={{
                '--selection-color': state.selectedObject.source === 'difference'
                  ? REVIEW_COLORS.difference[state.selectedObject.region]
                  : REVIEW_COLORS[state.selectedObject.source][state.selectedObject.anatomy],
              }} />
              <div>
                <small>Focused structure</small>
                <strong>{selectedLabel}</strong>
              </div>
              <Segmented
                label="Focus treatment"
                value={state.focusTreatment}
                onChange={(value) => dispatch({ type: 'SET_FOCUS_TREATMENT', value })}
                options={[['context', 'Context'], ['isolate', 'Isolate']]}
              />
              <button type="button" className="pw-icon-btn" onClick={() => dispatch({ type: 'CLEAR_SELECTION' })} aria-label="Clear structure focus"><X size={14} /></button>
            </div>
          )}


          <p className="pw-viewer__hint" aria-hidden="true" hidden={state.evidenceMode === 'ct' && !hasPrediction}>
            {state.viewMode === 'split'
              ? '2D: scroll slices, drag the crosshair · 3D: drag to orbit'
              : state.viewMode === '3d'
              ? state.interactionMode === 'move' ? 'Drag to reframe · scroll to zoom' : 'Drag to orbit · scroll to zoom · click a surface to focus'
              : state.interactionMode === 'pan' ? 'Drag to reposition · scroll to zoom'
                : state.interactionMode === 'window' ? 'Drag to tune brightness and contrast'
                  : 'Scroll slices · drag the crosshair · ← → step slices'}
          </p>

          {state.settingsOpen && (
            <aside className="review-settings-popover pw-popover" aria-label="View settings" tabIndex={0}>
              <div className="review-settings-popover__header">
                <div><Settings2 size={15} /><strong>View settings</strong></div>
                <button type="button" onClick={() => dispatch({ type: 'TOGGLE_SETTINGS' })} aria-label="Close view settings"><X size={14} /></button>
              </div>
              <div className="review-settings-group">
                <span>Display emphasis</span>
                <Segmented
                  label="Display emphasis"
                  value={state.displayPreset}
                  onChange={setDisplayPreset}
                  options={Object.entries(DISPLAY_PRESETS).map(([value, preset]) => [value, preset.label, { title: preset.description }])}
                />
                <small className="ct-window-help">
                  {state.displayPreset === 'custom' ? 'Custom visibility settings are active.' : DISPLAY_PRESETS[state.displayPreset]?.description}
                </small>
              </div>
              <label className="review-range">
                <span>Mask visibility <strong>{Math.round(state.overlayOpacity * 100)}%</strong></span>
                <input type="range" min="0.2" max="1" step="0.05" value={state.overlayOpacity}
                  onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { displayPreset: 'custom', overlayOpacity: Number(event.target.value) } })} />
              </label>
              <label className="review-layer-check">
                <span><ScanLine size={13} /> Full abdominal CT</span>
                <input type="checkbox" checked={state.showFull} disabled={!caseData.files?.ct_full}
                  onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { showFull: event.target.checked } })} />
              </label>
              {is3dLike && (
                <>
                  <label className="review-range">
                    <span>CT background <strong>{Math.round(state.ctOpacity * 100)}%</strong></span>
                    <input type="range" min="0" max="0.45" step="0.02" value={state.ctOpacity}
                      onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { displayPreset: 'custom', ctOpacity: Number(event.target.value) } })} />
                  </label>
                  <label className="review-layer-check">
                    <span><Focus size={13} /> Front-to-back CT cut</span>
                    <input type="checkbox" checked={state.clipEnabled} onChange={(event) => setClipEnabled(event.target.checked)} />
                  </label>
                </>
              )}
              <p className="display-mesh-provenance">
                Display surface · {caseData.display_mesh_version ? 'v2, explicit normals' : 'v1, source-grid reconstruction'}
                <span>Metrics remain derived from the original NIfTI masks.</span>
              </p>
            </aside>
          )}
        </div>

        <div className="pw-layerbar">
          <div className="pw-layerbar__layers" role="group" aria-label="Layers">
            <LayerToggle
              checked={predictionShown}
              label="Prediction"
              sublabel={hasPrediction ? null : caseData.files?.pred ? 'hidden' : 'none'}
              color={REVIEW_COLORS.pred.pancreas}
              disabled={!hasPrediction}
              onClick={() => setLayers(!predictionShown, referenceShown)}
              title={hasPrediction ? 'Show or hide the model prediction' : 'No prediction is displayed yet'}
            />
            {referenceState === 'ready' && (
              <LayerToggle
                checked={referenceShown}
                label="Reference"
                color={REVIEW_COLORS.gt.pancreas}
                onClick={() => setLayers(predictionShown, !referenceShown)}
              />
            )}
            <span className="pw-layerbar__divider" aria-hidden="true" />
            <LayerToggle
              checked={state.layerVisibility.pancreas}
              label="Pancreas"
              color={referenceShown && !predictionShown ? REVIEW_COLORS.gt.pancreas : REVIEW_COLORS.pred.pancreas}
              disabled={state.evidenceMode === 'ct'}
              onClick={() => dispatch({ type: 'TOGGLE_LAYER', layer: 'pancreas' })}
            />
            <LayerToggle
              checked={state.layerVisibility.lesion}
              label="Lesion"
              color={referenceShown && !predictionShown ? REVIEW_COLORS.gt.lesion : REVIEW_COLORS.pred.lesion}
              disabled={state.evidenceMode === 'ct'}
              onClick={() => dispatch({ type: 'TOGGLE_LAYER', layer: 'lesion' })}
            />
          </div>

          {comparing && state.evidenceMode === 'overlap' && (
            <Segmented
              label="Compare source"
              value={state.sourceFocus}
              onChange={(value) => dispatch({ type: 'SET_SOURCE_FOCUS', value })}
              options={[
                ['both', 'Both'],
                ['pred', 'Model'],
                ['gt', 'Reference'],
                ['difference', 'Difference', { disabled: !differenceAvailable }],
              ]}
            />
          )}

          <span className="pw-toolbar__spacer" />
          <div className="pw-layerbar__goto" role="group" aria-label="Go to structure">
            <span>Go to</span>
            <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={() => focusStructure('pancreas')} disabled={!availableSources.length || !navigation.ranges.pancreas}>Pancreas</button>
            <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={() => focusStructure('lesion')} disabled={!availableSources.length || !navigation.ranges.lesion}>Lesion</button>
          </div>
          {(referenceState === 'permitted' || (referenceState === 'ready' && !comparing)) && (
            <button type="button" className="pw-btn pw-btn--link" onClick={compareWithReference}>Compare with reference</button>
          )}
          {comparing && (
            <button type="button" className="pw-btn pw-btn--link" onClick={endComparison}>End comparison</button>
          )}
          {referenceState === 'incompatible' && <span className="pw-hint">Reference geometry does not match · comparison unavailable</span>}
          {referenceState === 'absent' && <span className="pw-hint">No reference annotation</span>}
          {!isCurated && truthUnlocked && (
            <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={resetScan} title="Hide prediction and reference and start this study again">
              <RotateCcw size={13} aria-hidden="true" /> Start over
            </button>
          )}
        </div>

        {is2dLike && (
          <div className="pw-slicebar" aria-label="2D slice navigation">
            <span className="pw-slicebar__readout"><strong>{planeName}</strong> <span className="pw-num">{navigatorIndex + 1}</span><span className="pw-muted"> / {navigatorTotal}</span></span>
            <button type="button" className="pw-icon-btn" onClick={() => setSlice(navigatorIndex - 1)} disabled={navigatorIndex <= 0} aria-label={`Previous ${planeName.toLowerCase()} slice`} title="Previous slice (←)">
              <ChevronLeft size={15} aria-hidden="true" />
            </button>
            <div className="pw-slicebar__track" style={{ '--slice-progress': `${sliceProgress}%` }}>
              {pancreasMarker && <i className="pw-range pw-range--pancreas" style={pancreasMarker} title="Slices containing predicted pancreas" />}
              {lesionMarker && <i className="pw-range pw-range--lesion" style={lesionMarker} title="Slices containing predicted lesion" />}
              <input
                type="range"
                min="0"
                max={Math.max(0, navigatorTotal - 1)}
                step="1"
                value={Math.min(navigatorIndex, navigatorTotal - 1)}
                onChange={(event) => setSlice(Number(event.target.value), { live: true })}
                aria-label={`${planeName} slice`}
                aria-valuetext={`${planeName} slice ${navigatorIndex + 1} of ${navigatorTotal}`}
              />
            </div>
            <button type="button" className="pw-icon-btn" onClick={() => setSlice(navigatorIndex + 1)} disabled={navigatorIndex >= navigatorTotal - 1} aria-label={`Next ${planeName.toLowerCase()} slice`} title="Next slice (→)">
              <ChevronRight size={15} aria-hidden="true" />
            </button>
            {(pancreasMarker || lesionMarker) && (
              <span className="pw-slicebar__legend" aria-label="Slice range markers">
                {pancreasMarker && <span><i className="pw-range-key pw-range-key--pancreas" />Pancreas</span>}
                {lesionMarker && <span><i className="pw-range-key pw-range-key--lesion" />Lesion</span>}
              </span>
            )}
          </div>
        )}
        {is3dLike && (
          <div className="pw-slicebar pw-slicebar--cut" aria-label="3D CT cutaway">
            <span className="pw-slicebar__readout"><strong>Cutaway</strong> <span className="pw-muted">front → back</span></span>
            <Segmented
              label="Front-to-back CT removal presets"
              value={state.clipEnabled && state.clipProgress === 0 ? 'full'
                : state.clipEnabled && state.clipProgress === 100 ? 'masks'
                  : state.clipEnabled && pancreasRevealProgress !== null && Math.abs(state.clipProgress - pancreasRevealProgress) <= 1 ? 'pancreas' : null}
              onChange={(value) => setClipProgress(value === 'full' ? 0 : value === 'masks' ? 100 : pancreasRevealProgress, { snapFront: true })}
              options={[['full', 'Full scan'], ['pancreas', 'Pancreas', { disabled: pancreasRevealProgress === null }], ['masks', 'Masks only']]}
            />
            <div className="pw-slicebar__track" style={{ '--slice-progress': `${state.clipProgress}%` }}>
              {pancreasRevealProgress !== null && <i className="pw-cut-marker" style={{ left: `${pancreasRevealProgress}%` }} title={`Pancreas is revealed near ${pancreasRevealProgress}% removal`} />}
              <input type="range" min="0" max="100" step="1" value={state.clipProgress}
                onChange={(event) => setClipProgress(Number(event.target.value), { live: true })} aria-label="Front-to-back CT removal" />
            </div>
            <code className="pw-slicebar__status">{cutStatus}</code>
          </div>
        )}
      </section>

      <aside
        className="pw-panel"
        id="pw-assistant"
        aria-label="PROWL Assistant"
        inert={panelOpen ? undefined : ''}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && window.matchMedia?.('(max-width: 1023px)').matches) {
            setPanelOpen(false)
            document.querySelector('[aria-controls="pw-assistant"]')?.focus()
          }
        }}
      >
        <header className="pw-panel__head">
          <PantherBadge size="sm" pulse={assistantPending} />
          <div>
            <h2>PROWL Assistant</h2>
            <p>Evidence alongside your expertise.</p>
          </div>
          <button type="button" className="pw-icon-btn pw-panel__close" onClick={() => setPanelOpen(false)} aria-label="Close assistant panel" title="Close assistant panel">
            <X size={16} aria-hidden="true" />
          </button>
        </header>
        <div className="pw-tabs" role="tablist" aria-label="Assistant sections">
          {[['findings', 'Findings'], ['ask', 'Ask PROWL'], ['summary', 'Summary']].map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              id={`pw-tab-${key}`}
              aria-selected={panelTab === key}
              aria-controls={`pw-tabpanel-${key}`}
              tabIndex={panelTab === key ? 0 : -1}
              onClick={() => setPanelTab(key)}
              onKeyDown={(event) => {
                const keys = ['findings', 'ask', 'summary']
                const index = keys.indexOf(panelTab)
                if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
                  event.preventDefault()
                  const next = keys[(index + (event.key === 'ArrowRight' ? 1 : keys.length - 1)) % keys.length]
                  setPanelTab(next)
                  document.getElementById(`pw-tab-${next}`)?.focus()
                }
              }}
            >
              {label}
              {key === 'ask' && assistantPending && <span className="pw-tab-dot" aria-label="working" />}
            </button>
          ))}
        </div>
        {/* Tab panels stay mounted so drafts, questions and scroll survive tab switches. */}
        <div className="pw-panel__body" role="tabpanel" id="pw-tabpanel-findings" aria-labelledby="pw-tab-findings" hidden={panelTab !== 'findings'}>
          <FindingsPanel
            caseId={caseId}
            caseData={caseData}
            hasPrediction={hasPrediction}
            predictionFile={Boolean(caseData.files?.pred)}
            liveResult={isCurated && !liveResult ? null : liveResult}
            isCurated={isCurated}
            finding={finding}
            overlap={overlap}
            referenceState={referenceState}
            comparing={comparing}
            ranges={navigation.ranges}
            analysisFailed={analysisFailed}
            onShowInViewer={focusStructure}
            onCompare={compareWithReference}
            reviewStatus={reviewStatus}
            onSetReviewStatus={onSetReviewStatus}
            onStartSummary={() => setPanelTab('summary')}
            modelLabel={modelLabel}
          />
        </div>
        <div className="pw-panel__body" role="tabpanel" id="pw-tabpanel-ask" aria-labelledby="pw-tab-ask" hidden={panelTab !== 'ask'}>
          {askPanel}
        </div>
        <div className="pw-panel__body" role="tabpanel" id="pw-tabpanel-summary" aria-labelledby="pw-tab-summary" hidden={panelTab !== 'summary'}>
          {summaryPanel}
        </div>
      </aside>
    </main>
  )
}
