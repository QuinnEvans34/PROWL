import { cloneElement, isValidElement, lazy, Suspense, useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import {
  Activity,
  Box,
  ChevronDown,
  CircleHelp,
  ChevronLeft,
  ChevronRight,
  Columns2,
  Contrast,
  Crosshair,
  Database,
  Eye,
  EyeOff,
  Expand,
  LoaderCircle,
  Maximize,
  Maximize2,
  Minimize2,
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
import { REVIEW_COLORS, visibleSourcesForEvidence, EVIDENCE_META } from '../lib/viewerLayers.js'
import { ANTERIOR_CAMERA } from '../lib/viewerOrientation.js'
import FindingsPanel from './FindingsPanel.jsx'
import LesionReviewBar from './LesionReviewBar.jsx'
import SliceSlider from './SliceSlider.jsx'
import StructurePopover from './StructurePopover.jsx'
import ReviewSummary from './ReviewSummary.jsx'
import { draftKey, hasHumanContent, predictionIdentity } from '../lib/summaryDraft.js'
import { PantherBadge } from '../shell/Brand.jsx'
import { useToolbenchLayout } from '../lib/toolbenchLayout.js'
import { useWorkspaceDisplay } from './useWorkspaceDisplay.js'
import WorkspaceResizeHandle from './WorkspaceResizeHandle.jsx'
import { usePredictionMeasurements, MeasurementReadout } from './PredictionMeasurements.jsx'
import { lesionComponentAtWorld } from '../lib/lesionDimensions.js'
import ReviewDecisionPanel from './ReviewDecisionPanel.jsx'
import InspectionSourceControls from './InspectionSourceControls.jsx'
import { verifiedInspectionSource } from '../lib/viewerImageDetails.js'
import FindingKeyViews from './FindingKeyViews.jsx'
import FindingAskPanel from './FindingAskPanel.jsx'

const NiivueViewer = lazy(() => import('./NiivueViewer.jsx'))
const ToolbenchViewer = lazy(() => import('./ToolbenchViewer.jsx'))

// Display defaults; the 3D scene selector replaced the older emphasis presets.
const DEFAULT_OVERLAY_OPACITY = 0.62
const DEFAULT_CT_OPACITY = 0.44

const CT_WINDOW_OPTIONS = [
  ['soft', 'Soft tissue', 'Best general view of the pancreas and nearby organs'],
  ['contrast', 'Contrast+', 'Adds separation between similar soft tissues'],
  ['wide', 'Wide', 'Shows the broadest CT intensity range'],
]

// Keyboard camera views (azimuth, elevation), matching the Views menu order.
const CAMERA_VIEWS = [['Front', ...ANTERIOR_CAMERA], ['Back', 0, 0], ['Left', 90, 0], ['Right', 270, 0], ['Top', 0, 90], ['Bottom', 0, -90]]
const CAMERA_SHORTCUTS = {
  ...Object.fromEntries(CAMERA_VIEWS.map(([, azimuth, elevation], index) => [String(index + 1), [azimuth, elevation]])),
  0: [120, 15],
}

// Viewer controls, written for both mouse and trackpad users.
const CONTROL_HELP = {
  '3d': [
    ['Rotate', 'Drag with the Rotate tool (one finger on a trackpad)'],
    ['Pan', 'Drag to reposition the 3D view'],
    ['Zoom', 'Scroll, pinch, or + / − at any peel depth'],
    ['Box zoom', 'Left-drag to frame a region'],
    ['Select', 'Click a surface for its details'],
    ['Orbit a structure', 'Double-click a surface'],
    ['Views', '1–6 anatomical views · 0 home · F fit · R reset'],
    ['Peel', 'Choose a direction and drag the slider below the image'],
  ],
  '2d': [
    ['Crosshair', 'Click or drag with the Navigate tool'],
    ['Slices', 'Use the slider below each plane'],
    ['Pan', 'Shift-drag, or the Pan tool'],
    ['Zoom', 'Scroll over the image to zoom toward the pointer'],
    ['Box zoom', 'Left-drag to frame a region'],
    ['Brightness', 'Right-drag, or the Window tool'],
    ['View', 'F fit · R reset'],
  ],
}

const PEEL_DIRECTIONS = [
  ['frontToBack', 'Front → back', { ariaLabel: 'Front to back' }],
  ['backToFront', 'Back → front', { ariaLabel: 'Back to front' }],
]
const CUT_DEPTH_MIN = -0.5
const CUT_DEPTH_MAX = 0.5

function clipDepthFromProgress(progress) {
  if (progress <= 0) return 2
  const fraction = Math.max(0, Math.min(1, progress / 100))
  return CUT_DEPTH_MIN + fraction * (CUT_DEPTH_MAX - CUT_DEPTH_MIN)
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
  finding: suppliedFinding = {},
  overlap: suppliedOverlap = {},
  referenceCompatibility = 'compatible',
  modelLabel = 'Segmenter v1 · step 18000',
  askPanel = null,
  assistantPending = false,
  summaryPanel = null,
  summaryStore = null,
  verifiedPrediction = null,
  localCt = null,
  predictionJob = null,
  onReviewDirty = null,
  onSelectScan,
  onAnalyze,
  onShowSavedPrediction,
  onRevealTruth,
  onResetScan,
  onSetReviewStatus,
  onOpenComparison,
  onOpenLibrary,
}) {
  // Prepared contours remain the files supplied with this case. A legacy live
  // score does not replace those files, their measurements or their identity.
  const finding = {
    ...suppliedFinding,
    lesionFlagged: typeof caseData.pred_has_lesion === 'boolean' ? caseData.pred_has_lesion : suppliedFinding.lesionFlagged,
    volumeMm3: Number.isFinite(caseData.lesion_volume_mm3) ? caseData.lesion_volume_mm3 : suppliedFinding.volumeMm3,
    confidence: Number.isFinite(caseData.confidence) ? caseData.confidence : suppliedFinding.confidence,
  }
  const overlap = {
    pancreas: Number.isFinite(caseData.dice_pancreas) ? caseData.dice_pancreas : suppliedOverlap.pancreas,
    lesion: Number.isFinite(caseData.dice_lesion) ? caseData.dice_lesion : suppliedOverlap.lesion,
  }
  const hasPrediction = isCurated || hasLiveResult
  const meshFiles = verifiedPrediction?.urls?.mesh || caseData.files?.mesh
  const has3dOutline = hasPrediction && Boolean(meshFiles?.pancreas_pred || meshFiles?.lesion_pred)
  const studyKey = verifiedPrediction?.manifestHash || caseId
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

  const [state, dispatch] = useReducer(reviewReducer, { hasPrediction, start3d: has3dOutline }, makeReviewState)
  const [inspection, setInspection] = useState(null)
  const inspecting = inspection?.studyKey === studyKey ? inspection : null
  const viewMode = inspecting ? (has3dOutline ? 'split' : '2d') : state.viewMode
  const [inspectionOverlay, setInspectionOverlay] = useState('outline')
  const [sliceLocator, setSliceLocator] = useState(false)
  const [inspectionNavigation, setInspectionNavigation] = useState(null)
  const view3dRef = useRef(null)
  const inspectionViewRef = useRef(null)
  const capture3d = useCallback(handle => { view3dRef.current = handle }, [])
  const captureInspection = useCallback(handle => { inspectionViewRef.current = handle }, [])
  // Layout chrome is reviewer preference, not study state: it survives study changes.
  const [layout, setLayout, resetLayout] = useToolbenchLayout()
  const workspaceRef = useRef(null)
  const { focusMode, setFocusMode, toggleFocus, isFullscreen, toggleFullscreen, fullscreenAvailable, fullscreenError } = useWorkspaceDisplay(workspaceRef)
  const [compactWorkspace, setCompactWorkspace] = useState(() => typeof window !== 'undefined' && window.innerWidth < 1024)
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false)
  const [mobileStudiesOpen, setMobileStudiesOpen] = useState(false)
  useEffect(() => {
    const resize = () => setCompactWorkspace(window.innerWidth < 1024)
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [])
  const studyListOpen = (compactWorkspace ? mobileStudiesOpen : layout.studyListOpen) && !focusMode
  const panelOpen = (compactWorkspace ? mobilePanelOpen : layout.panelOpen) && !focusMode
  const setStudyListOpen = value => {
    if (compactWorkspace) setMobileStudiesOpen(value)
    else setLayout(previous => ({ studyListOpen: typeof value === 'function' ? value(previous.studyListOpen) : value }))
  }
  const setPanelOpen = value => {
    setFocusMode(false)
    if (compactWorkspace) setMobilePanelOpen(value)
    else setLayout(previous => ({ panelOpen: typeof value === 'function' ? value(previous.panelOpen) : value }))
  }
  const [panelTab, setPanelTab] = useState('findings')
  const [snapOpen, setSnapOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)
  const panelWide = layout.panelWidth >= 420
  const [threeDVisited, setThreeDVisited] = useState(has3dOutline)
  const [twoDVisited, setTwoDVisited] = useState(!has3dOutline)
  const [threeDZoom, setThreeDZoom] = useState(null)
  const [askDraft, setAskDraft] = useState(null)
  const [popAnchor, setPopAnchor] = useState(null)
  const [peelReveal3d, setPeelReveal3d] = useState(null)
  const [lesionSelection, setLesionSelection] = useState(null)
  const [pendingLesionPick, setPendingLesionPick] = useState(null)
  const [inspectedPancreasMeasurement, setInspectedPancreasMeasurement] = useState(null)
  const [framingStudy, setFramingStudy] = useState(null)
  const framingLocked = framingStudy === caseId && !inspecting
  useEffect(() => { setPeelReveal3d(null) }, [caseId])
  const viewerRef = useRef(null)
  const lastPointerRef = useRef(null)
  const [navigation, setNavigation] = useState({
    indices: { axial: 0, coronal: 0, sagittal: 0 },
    totals: { axial: 1, coronal: 1, sagittal: 1 },
    ranges: { pancreas: null, lesion: null },
  })
  const [pendingNavigationCommand, setNavigationCommand] = useState(null)
  const navigationCommand = pendingNavigationCommand?.studyKey === studyKey ? pendingNavigationCommand : null
  const navigationCommandId = useRef(0)
  const clipFrameRef = useRef(null)
  const pendingClipProgressRef = useRef(null)

  const clearFinding = useCallback(() => {
    setPendingLesionPick(null)
    setLesionSelection(null)
    setInspectedPancreasMeasurement(null)
    setPopAnchor(null)
    setNavigationCommand(previous => previous?.type === 'measurement-point' ? null : previous)
    lastPointerRef.current = null
    dispatch({ type: 'CLEAR_SELECTION' })
  }, [])

  const exitInspection = useCallback(() => {
    if (inspecting) {
      const camera = inspecting.camera
      if (camera && !view3dRef.current?.restore(camera)) {
        issueViewerCommand({ type: 'restore-camera', target: '3d', view: camera })
      }
      dispatch({ type: 'PATCH_SETTINGS', value: inspecting.settings })
    }
    setInspection(null)
    setInspectionNavigation(null)
    setSliceLocator(false)
    clearFinding()
  }, [clearFinding, inspecting])

  const resetView = useCallback(() => {
    exitInspection()
    dispatch({ type: 'RESET_VIEW' })
  }, [exitInspection])

  function issueViewerCommand(command) {
    navigationCommandId.current += 1
    setNavigationCommand({ ...command, id: navigationCommandId.current, studyKey })
  }

  useEffect(() => {
    if (clipFrameRef.current !== null) window.cancelAnimationFrame(clipFrameRef.current)
    clipFrameRef.current = null
    pendingClipProgressRef.current = null
    setPendingLesionPick(null)
    setLesionSelection(null)
    setInspectedPancreasMeasurement(null)
    setInspection(null)
    setInspectionNavigation(null)
    setSliceLocator(false)
    setFramingStudy(null)
    setThreeDZoom(null)
    setNavigationCommand(null)
    setThreeDVisited(has3dOutline)
    setTwoDVisited(!has3dOutline)
    dispatch({ type: 'CASE_CHANGED', hasPrediction, start3d: has3dOutline })
    setNavigation({
      indices: { axial: 0, coronal: 0, sagittal: 0 },
      totals: { axial: 1, coronal: 1, sagittal: 1 },
      ranges: { pancreas: null, lesion: null },
    })
  }, [studyKey])

  useEffect(() => () => {
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
      if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) return
      if (event.key === 'Escape') {
        if (!target?.closest?.('[aria-modal="true"]') && !isFullscreen) exitInspection()
        return
      }
      if (target?.closest?.('[role="dialog"], .pw-panel')) return
      if (target?.closest?.('[role="separator"], .tb-pane')) return
      if (event.key.toLowerCase() === 'r' && !(framingLocked && viewMode !== '3d')) resetView()
      if (event.key.toLowerCase() === 'f' && !(framingLocked && viewMode === '2d')) issueViewerCommand({ type: 'fit', target: inspecting ? 'inspection' : undefined })
      if (viewMode !== '2d') {
        // Camera shortcuts for 3D (and the 3D pane in Split): 1–6 anatomical views, 0 home.
        const view = CAMERA_SHORTCUTS[event.key]
        if (view) issueViewerCommand({ type: 'camera', azimuth: view[0], elevation: view[1] })
        if (event.key === '+' || event.key === '=') issueViewerCommand({ type: 'zoom', target: '3d', factor: 1.16 })
        if (event.key === '-' || event.key === '_') issueViewerCommand({ type: 'zoom', target: '3d', factor: 0.86 })
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [viewMode, inspecting, framingLocked, exitInspection, resetView, isFullscreen])

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
  // The prepared viewer renders caseData.files.pred. Measure that same saved mask,
  // never a numerical result returned by the separate legacy live scoring service.
  const measurementContext = useMemo(() => ({
    identity: verifiedPrediction?.manifestHash || `${caseId}:${caseData.files?.ct || ''}:${caseData.files?.pred || ''}:saved`,
    caseId, files: caseData.files, spacingMm: caseData.spacing_mm,
    source: verifiedPrediction ? 'native' : 'saved',
    ctSha256: verifiedPrediction?.manifest?.files?.ct?.content_sha256,
    predictionSha256: verifiedPrediction?.manifest?.files?.pred?.content_sha256,
    available: hasPrediction && predictionShown && !isAnalyzing && Boolean(caseData.files?.ct && caseData.files?.pred),
  }), [caseId, caseData.files, caseData.spacing_mm, hasPrediction, predictionShown, isAnalyzing, verifiedPrediction])
  const measurementState = usePredictionMeasurements(measurementContext, { measurement: verifiedPrediction?.measurement })
  const verifiedMeasurement = measurementState.status === 'ready' ? measurementState.measurement : null
  const pancreasDimensions = verifiedMeasurement?.pancreasDimensions
  const selectedPancreas = state.selectedObject?.source === 'pred' && state.selectedObject.anatomy === 'pancreas'
  const measuredPancreasVisible = predictionShown && !comparing && state.layerVisibility.pancreas && visibleSources.includes('pred')
  const pancreasInReview = selectedPancreas && measuredPancreasVisible && pancreasDimensions?.status === 'ready'
  const pancreasInspection = pancreasInReview && inspectedPancreasMeasurement === verifiedMeasurement
  // The selection is scoped to the actual verified result, not just a lesion
  // index or case name, which can repeat across prediction versions.
  const currentLesionSelection = verifiedMeasurement && lesionSelection?.measurement === verifiedMeasurement
    ? lesionSelection : null
  const measurementInspection = currentLesionSelection?.inspect ? currentLesionSelection : null
  const measuredLesionVisible = predictionShown && !comparing && state.layerVisibility.lesion && visibleSources.includes('pred')
  const selectedCalipers = currentLesionSelection?.component?.calipers
  const canShow3dCalipers = measuredLesionVisible && Boolean(selectedCalipers?.plane)
  const show3dCalipers = canShow3dCalipers && currentLesionSelection.showCalipers3d === true
  const components = verifiedMeasurement?.lesionDimensions?.components ?? []
  const selectedComponent = measuredLesionVisible ? currentLesionSelection?.component : null
  const selectedLesionNumber = selectedComponent ? components.indexOf(selectedComponent) + 1 : 0
  const awaitingPick = pendingLesionPick?.identity === measurementState.identity && measurementState.status === 'loading'
  const viewerLabel = `${caseId} · ${EVIDENCE_META[state.evidenceMode].label}`
  const studyLabel = localCt ? 'Local CT' : caseId.replace('PanTS_', 'PanTS ')

  async function analyze() {
    const outcome = await onAnalyze(caseId)
    if (outcome) {
      dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
      resetView()
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
    exitInspection()
    onResetScan()
    dispatch({ type: 'CASE_CHANGED', hasPrediction: false })
  }

  function markMeasuredLesion(component, inspect = false) {
    setPendingLesionPick(null)
    setInspectedPancreasMeasurement(null)
    setLesionSelection(previous => ({ measurement: verifiedMeasurement, component, inspect,
      showCalipers3d: previous?.measurement === verifiedMeasurement && previous.showCalipers3d === true,
    }))
    setPopAnchor(null)
    dispatch({ type: 'SELECT_OBJECT', value: { source: 'pred', anatomy: 'lesion', worldMm: component.focusWorldMm } })
    setPanelTab('findings')
    if (!compactWorkspace && !focusMode) setPanelOpen(true)
  }

  function selectLesionIn3d(component) {
    if (!verifiedMeasurement) return
    setViewMode('3d')
    if (comparing) dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
    markMeasuredLesion(component)
  }

  function inspectLesion(component) {
    inspectMeasurement(component.calipers, 'lesion', component.boundsWorldMm, () => markMeasuredLesion(component, true))
  }

  function markPancreas(worldMm, inspect = false) {
    clearFinding()
    if (inspect) setInspectedPancreasMeasurement(verifiedMeasurement)
    dispatch({ type: 'SELECT_OBJECT', value: { source: 'pred', anatomy: 'pancreas', worldMm } })
    setPanelTab('findings')
    if (!compactWorkspace && !focusMode) setPanelOpen(true)
  }

  function selectPancreasIn3d() {
    setViewMode('3d')
    if (comparing) dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
    markPancreas(pancreasDimensions?.focusWorldMm)
  }

  function inspectPancreas() {
    inspectMeasurement(pancreasDimensions?.calipers, 'pancreas', null, () => markPancreas(pancreasDimensions.focusWorldMm, true))
  }

  function inspectMeasurement(calipers, anatomy, boundsWorldMm, select) {
    if (!verifiedMeasurement || !calipers?.plane) return
    const changedFinding = inspecting?.calipers !== calipers
    if (!inspecting) {
      setInspectionOverlay('outline')
      setInspectionNavigation(null)
    }
    setInspection({
      studyKey, anatomy, calipers,
      camera: inspecting?.camera ?? view3dRef.current?.capture(),
      settings: inspecting?.settings ?? {
        clipProgress: state.clipProgress, clipEnabled: state.clipEnabled, clipDirection: state.clipDirection,
        ctWindow: state.ctWindow, ctOpacity: state.ctOpacity, overlayOpacity: state.overlayOpacity,
        scene3d: state.scene3d, evidenceMode: state.evidenceMode, sourceFocus: state.sourceFocus, layerVisibility: state.layerVisibility,
        interactionMode: state.interactionMode,
      },
    })
    if (has3dOutline) setThreeDVisited(true)
    if (state.evidenceMode !== 'prediction') dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
    select()
    issueViewerCommand({ type: 'measurement-point', target: 'inspection', plane: calipers.plane,
      worldMm: calipers.anchorWorldMm, fitBounds: changedFinding ? boundsWorldMm ?? calipers.axes?.flatMap(axis => axis.worldEndpointsMm || []) : null })
  }

  function selectFrom3d(value) {
    // A pinned cross stays in view while the reviewer explores nearby tissue.
    const pickedModelLesion = value?.source === 'pred' && value.anatomy === 'lesion'
    if (!pickedModelLesion && show3dCalipers) return
    if (!value) return inspecting ? undefined : exitInspection()
    if (value.source === 'pred' && value.anatomy === 'pancreas') {
      return inspecting ? inspectPancreas() : markPancreas(pancreasDimensions?.focusWorldMm)
    }
    setPendingLesionPick(null)
    setInspectedPancreasMeasurement(null)
    if (pickedModelLesion) {
      const component = measuredLesionVisible ? lesionComponentAtWorld(verifiedMeasurement, value.worldMm) : null
      if (component) return inspecting ? inspectLesion(component) : markMeasuredLesion(component)
      if (show3dCalipers) return
      if (measuredLesionVisible && measurementState.status === 'loading' && value.worldMm) {
        setPendingLesionPick({ identity: measurementState.identity, worldMm: value.worldMm })
      }
      setPanelTab('findings')
      if (!compactWorkspace && !focusMode) setPanelOpen(true)
      setLesionSelection({ measurement: verifiedMeasurement, unmatched: true })
    } else {
      setLesionSelection(null)
    }
    dispatch({ type: 'SELECT_OBJECT', value })
  }

  function selectFrom2d(value) {
    if (pancreasInspection || measurementInspection || show3dCalipers) return
    if (!value) return exitInspection()
    setPendingLesionPick(null)
    setLesionSelection(null)
    dispatch({ type: 'SELECT_OBJECT', value })
  }

  useEffect(() => {
    if (!pendingLesionPick) return
    if (!measuredLesionVisible || pendingLesionPick.identity !== measurementState.identity) {
      setPendingLesionPick(null)
    } else if (measurementState.status !== 'loading') {
      setPendingLesionPick(null)
      const component = lesionComponentAtWorld(verifiedMeasurement, pendingLesionPick.worldMm)
      if (component) markMeasuredLesion(component)
      else if (verifiedMeasurement) setLesionSelection({ measurement: verifiedMeasurement, unmatched: true })
    }
  }, [pendingLesionPick, measuredLesionVisible, measurementState.identity, measurementState.status, verifiedMeasurement])

  function focusStructure(anatomy) {
    const source = visibleSources.includes('pred') ? 'pred' : visibleSources.includes('gt') ? 'gt' : availableSources[0]
    if (!source) return
    setInspectedPancreasMeasurement(null)
    if (!show3dCalipers && anatomy !== 'lesion') {
      setPendingLesionPick(null)
      setLesionSelection(null)
    }
    if (!predictionShown && source === 'pred') setLayers(true, referenceShown)
    if (!show3dCalipers) dispatch({ type: 'SELECT_OBJECT', value: { source, anatomy } })
    issueViewerCommand({ type: 'focus', source, anatomy })
  }

  const coronalPancreasRange = navigation.ranges.pancreas?.coronal
  const coronalTotal = navigation.totals.coronal || 1
  const peelFromBack = state.clipDirection === 'backToFront'
  const peelDirectionLabel = peelFromBack ? 'Back-to-front' : 'Front-to-back'
  // Prefer the 3D scene's own geometry (correct for the full abdomen); fall back to the
  // 2D coronal estimate before the 3D view has loaded.
  let pancreasRevealProgress = peelReveal3d?.[state.clipDirection] ?? null
  if (pancreasRevealProgress === null && coronalPancreasRange && coronalTotal > 1) {
    const entryDistance = peelFromBack ? coronalPancreasRange[0] : coronalTotal - 1 - coronalPancreasRange[1]
    const margin = Math.max(8, Math.round(coronalTotal * 0.08))
    pancreasRevealProgress = Math.max(1, Math.min(99, Math.round((entryDistance + margin) / (coronalTotal - 1) * 100)))
  }
  function setClipProgress(value, { live = false } = {}) {
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
  }


  function setViewMode(viewMode) {
    if (viewMode === 'split' && !SPLIT_SUPPORTED) return
    if (inspecting) exitInspection()
    if (viewMode !== '2d') setThreeDVisited(true)
    if (viewMode !== '3d') setTwoDVisited(true)
    dispatch({ type: 'SET_VIEW_MODE', value: viewMode })
  }

  function changeFramingLock(locked) {
    setFramingStudy(locked ? caseId : null)
    if (locked && state.viewMode === '2d' && ['pan', 'box-zoom'].includes(state.interactionMode)) {
      dispatch({ type: 'SET_INTERACTION_MODE', value: 'navigate' })
    }
  }

  const is2dLike = viewMode !== '3d'
  const is3dLike = viewMode !== '2d'
  const boxZoom = state.interactionMode === 'box-zoom'
  const pan = state.interactionMode === 'pan'
  const twoDInteractionMode = (framingLocked && (boxZoom || pan)) || state.interactionMode === 'rotate' ? 'navigate' : state.interactionMode
  const threeDInteractionMode = boxZoom || pan ? state.interactionMode : 'rotate'
  const modelLesionPicked = state.selectedObject?.source === 'pred' && state.selectedObject.anatomy === 'lesion'
  const lesionInReview = Boolean(currentLesionSelection?.component || (is3dLike && measuredLesionVisible && modelLesionPicked))
  let lesionReviewMessage
  if (selectedComponent) {
    if (!selectedCalipers?.plane) lesionReviewMessage = 'The exact measurement slice cannot be displayed.'
    else if (measurementInspection && !is3dLike) lesionReviewMessage = 'Cross shown on the measured slice only.'
  } else if (!measuredLesionVisible) lesionReviewMessage = 'Show the model lesion to review its measurements.'
  else if (awaitingPick) lesionReviewMessage = 'Lesion clicked. Checking its outline…'
  else if (measurementState.status === 'loading') lesionReviewMessage = 'Checking the predicted outline…'
  else if (measurementState.status === 'unavailable') lesionReviewMessage = measurementState.reason
  else if (verifiedMeasurement?.lesionDimensions?.status === 'unavailable') lesionReviewMessage = verifiedMeasurement.lesionDimensions.reason
  else if (!components.length) lesionReviewMessage = 'No measurable lesion outline in this prediction.'
  else if (currentLesionSelection?.unmatched) lesionReviewMessage = 'That click did not match an outline. Select a lesion to continue.'
  else lesionReviewMessage = 'Click a predicted lesion in 3D or select it here.'
  // Full abdomen needs the exported whole-abdomen CT; fall back to the region if absent.
  const scene3d = state.scene3d === 'full' && !caseData.files?.ct_full ? 'region' : state.scene3d
  const viewerProps = {
    caseData,
    assetUrls: verifiedPrediction?.urls ?? localCt?.assetUrls,
    nativeGeometry: verifiedPrediction?.manifest?.geometry ?? localCt?.geometry,
    nativeCtOnly: Boolean(localCt),
    ctRange: verifiedPrediction?.manifest?.ct_window ?? localCt?.ctRange,
    imageDetails: localCt?.imageSource,
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
    onSelectObject: selectFrom2d,
    activePlane: state.activePlane,
    navigationCommand: navigationCommand?.target !== '3d' && navigationCommand?.target !== 'inspection'
      && (navigationCommand?.type !== 'measurement-point' || pancreasInspection || measurementInspection) ? navigationCommand : null,
    measurementAnatomy: pancreasInspection ? 'pancreas' : 'lesion',
    measurementCalipers: state.showFull ? null : pancreasInspection ? pancreasDimensions.calipers
      : measuredLesionVisible ? measurementInspection?.component.calipers : null,
    clip: {
      enabled: state.clipEnabled,
      progress: state.clipProgress,
      depth: clipDepthFromProgress(state.clipProgress),
      azimuth: peelFromBack ? 180 : 0,
      elevation: 0,
    },
    resetToken: state.resetToken,
    guided: true,
  }

  // 3D scene choice: which CT (if any) surrounds the surfaces.
  const viewer3dProps = {
    wheelZoom: true,
    anatomyLighting: true,
    showFull: scene3d === 'full',
    ctOpacity: scene3d === 'surfaces' ? 0 : state.ctOpacity,
    onPeelReveal: setPeelReveal3d,
    onSelectObject: selectFrom3d,
    selectedLesionWorldMm: measuredLesionVisible
      ? (currentLesionSelection?.component?.focusWorldMm ?? null) : null,
    measurementAnatomy: 'lesion',
    measurementCalipers: show3dCalipers ? selectedCalipers : null,
    navigationCommand: navigationCommand?.type === 'restore-finding-view' && navigationCommand.view.camera
      ? navigationCommand : ['2d', 'inspection'].includes(navigationCommand?.target) || navigationCommand?.type === 'measurement-point' ? null : navigationCommand,
    onZoomChange: scale => setThreeDZoom(Number.isFinite(scale) ? Math.round(scale * 100) : null),
    onViewHandle: capture3d,
    sliceLocatorCorners: sliceLocator && inspecting ? inspectionNavigation?.planeWorldCorners : null,
  }
  const sourceDetails = verifiedInspectionSource(verifiedPrediction, {
    studyId: caseId, predictionSha256: verifiedPrediction?.manifest?.files?.pred?.content_sha256,
  })
  const inspectionProps = inspecting ? {
    ...viewerProps, showFull: false, activePlane: inspecting.calipers.plane, onSelectObject: null,
    navigationCommand: navigationCommand?.target === 'inspection' ? navigationCommand : null,
    measurementAnatomy: inspecting.anatomy, measurementCalipers: inspecting.calipers,
    overlayMode: inspectionOverlay, onViewHandle: captureInspection,
    imageDetails: sourceDetails || { kind: 'prepared', legacyMillimeters: true },
    capturePlaneLocation: true, inspectionBounds: inspecting.anatomy === 'lesion' ? selectedComponent?.boundsWorldMm : null,
  } : null
  const selectedFinding = selectedComponent ? {
    anatomy: 'lesion', id: selectedComponent.id, ordinal: selectedLesionNumber, dimensions: selectedComponent,
  } : pancreasInReview ? {
    anatomy: 'pancreas', id: 'pancreas', dimensions: pancreasDimensions, volumeMl: verifiedMeasurement.pancreasMl,
  } : null
  const inspectSelected = selectedComponent ? () => inspectLesion(selectedComponent) : pancreasInReview ? inspectPancreas : null

  function captureKeyView() {
    const view = inspectionViewRef.current?.capture()
    if (!inspecting || !view?.worldMm?.every(Number.isFinite)) return null
    const camera = has3dOutline ? view3dRef.current?.capture() : null
    return {
      plane: inspecting.calipers.plane, worldMm: view.worldMm,
      sliceIndex: inspectionNavigation?.indices?.[inspecting.calipers.plane],
      seriesKey: sourceDetails ? 'source' : 'prepared',
      ctWindow: state.ctWindow, ctRange: view.ctRange, pan2Dxyzmm: view.pan2Dxyzmm,
      overlayMode: inspectionOverlay, overlayOpacity: state.overlayOpacity, ctOpacity: state.ctOpacity,
      clipEnabled: state.clipEnabled, clipProgress: state.clipProgress, clipDirection: state.clipDirection,
      scene3d: state.scene3d, show3dCalipers, showSliceIn3d: sliceLocator,
      camera: camera && { azimuth: camera.azimuth, elevation: camera.elevation, scale: camera.scale, pivot: camera.orbitCentre || camera.pivot3D },
    }
  }

  function reopenKeyView(record) {
    const view = record.view
    if (view.seriesKey !== (sourceDetails ? 'source' : 'prepared')) return 'The CT series for this key view is unavailable.'
    if (view.camera && !has3dOutline) return 'Wait for the 3D outline before reopening this view.'
    const component = record.finding.anatomy === 'pancreas'
      ? pancreasDimensions : components.find(item => item.id === record.finding.id)
    if (component?.calipers?.plane !== view.plane) return 'The measured plane for this finding is unavailable.'
    if (record.finding.anatomy === 'pancreas') inspectPancreas()
    else {
      inspectLesion(component)
      setLesionSelection(previous => ({ ...previous, showCalipers3d: Boolean(view.show3dCalipers) }))
    }
    const settings = {}
    for (const key of ['ctWindow', 'overlayOpacity', 'ctOpacity', 'clipEnabled', 'clipProgress', 'clipDirection', 'scene3d']) {
      if (view[key] !== undefined) settings[key] = view[key]
    }
    dispatch({ type: 'PATCH_SETTINGS', value: settings })
    setInspectionOverlay(view.overlayMode === 'outline' || view.overlayMode === 'fill' ? view.overlayMode : 'off')
    setSliceLocator(Boolean(view.showSliceIn3d))
    issueViewerCommand({ type: 'restore-finding-view', target: 'inspection', plane: view.plane, view })
    return null
  }

  function openPanel(tab) {
    setPanelTab(tab)
    setPanelOpen(true)
  }

  // Fill the Ask box with a general literature question; the reviewer decides whether to send.
  function askAbout(text) {
    setAskDraft({ text, token: Date.now() })
    openPanel('ask')
  }

  const selectionKey = state.selectedObject
    ? `${state.selectedObject.source}:${state.selectedObject.anatomy}:${state.selectedObject.region || ''}`
    : ''
  // Anchor the structure card near the click that selected it (if it was a click).
  useEffect(() => {
    if (!selectionKey) { setPopAnchor(null); return }
    const viewer = viewerRef.current
    const pointer = lastPointerRef.current
    if (!viewer || !pointer || Date.now() - pointer.t > 1500) { setPopAnchor(null); return }
    const width = viewer.clientWidth
    const height = viewer.clientHeight
    const cardWidth = 292
    const cardHeight = 340
    const left = pointer.x + 16 + cardWidth > width ? Math.max(8, pointer.x - 16 - cardWidth) : pointer.x + 16
    const top = Math.max(8, Math.min(height - cardHeight - 8, pointer.y - 24))
    setPopAnchor({ left: Math.round(left), top: Math.round(top) })
  }, [selectionKey])

  // 3D camera presets live behind one small "Views" button instead of a grid that
  // permanently covered the corner of the render.
  const snapPad = state.settingsOpen ? null : (
    <div className="pw-snap-wrap">
      <button type="button" className="pw-snap__toggle" aria-expanded={snapOpen} onClick={() => setSnapOpen((open) => !open)} title="Snap the 3D camera to an anatomical view">
        Views <ChevronDown size={13} aria-hidden="true" />
      </button>
      {snapOpen && (
        <div className="pw-snap" role="group" aria-label="Snap 3D camera to an anatomical view">
          {CAMERA_VIEWS.map(([label, azimuth, elevation], index) => (
            <button type="button" key={label} title={`${label} view (${index + 1})`} onClick={() => { issueViewerCommand({ type: 'camera', azimuth, elevation }); setSnapOpen(false) }}>{label}</button>
          ))}
          <button type="button" title="Home view (0)" onClick={() => { issueViewerCommand({ type: 'camera', azimuth: 120, elevation: 15 }); setSnapOpen(false) }}>Home</button>
        </div>
      )}
    </div>
  )

  const prediction = useMemo(
    () => predictionIdentity({ hasPrediction, liveResult: null, modelLabel }),
    [hasPrediction, modelLabel],
  )
  const seriesLabel = `Abdomen CT · prepared, ${Array.isArray(caseData.spacing_mm) ? `${caseData.spacing_mm[0]} mm voxels` : 'spacing not recorded'}`
  const summaryFacts = useMemo(() => ({
    hasPrediction,
    lesionFlagged: Boolean(finding.lesionFlagged),
    volumeMm3: measurementState.status === 'ready' ? measurementState.measurement.lesionMl * 1000 : undefined,
    pancreasVolumeMm3: measurementState.status === 'ready' ? measurementState.measurement.pancreasMl * 1000 : undefined,
    measurementStatus: measurementState.status,
    diameterMm: undefined,
    comparison: comparing
      ? { pancreas: overlap.pancreas, lesion: overlap.lesion, bothLesionAbsent: !caseData.gt_has_lesion && !finding.lesionFlagged }
      : null,
  }), [hasPrediction, finding.lesionFlagged, measurementState, comparing, overlap.pancreas, overlap.lesion, caseData.gt_has_lesion])
  const currentDraft = summaryStore?.drafts[draftKey(caseId, 'prepared-ct', prediction.key)]
  const summaryStatus = !summaryStore ? null : currentDraft ? (hasHumanContent(currentDraft) ? 'Unsaved draft · edited' : 'Unsaved draft') : 'Not started'

  const predictionStatus = !caseData.files?.pred
    ? 'No prediction available'
    : verifiedPrediction
      ? 'Verified run prediction'
      : isAnalyzing
      ? 'Analysis running…'
      : hasPrediction
        ? liveResult?.source === 'live' ? 'Live score · saved contours' : 'Saved prediction'
        : 'Prediction hidden'

  const wbClass = [
    'pw-wb',
    'pw-toolbench',
    focusMode ? 'pw-toolbench--focus' : '',
    isFullscreen ? 'pw-toolbench--fullscreen' : '',
    studyListOpen ? '' : 'pw-wb--list-closed',
    panelOpen ? '' : 'pw-wb--panel-closed',
  ].filter(Boolean).join(' ')

  return (
    <main ref={workspaceRef} className={wbClass} aria-label={`Workbench · ${studyLabel}`}
      style={{ '--pw-list-w': `${layout.studyListWidth}px`, '--pw-panel-w': `${layout.panelWidth}px` }}>
      <aside className="pw-wb__list" aria-label="Study list" hidden={!studyListOpen} inert={studyListOpen ? undefined : ''}>
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
        <WorkspaceResizeHandle label="Study list width" value={layout.studyListWidth} min={160} max={320}
          onChange={studyListWidth => setLayout({ studyListWidth })} className="pw-workspace-resize--right" />
      </aside>

      <section className="pw-wb__center">
        <header className="pw-studybar">
          {!studyListOpen && (
            <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={() => { setFocusMode(false); setStudyListOpen(true) }} aria-label="Open study list" title="Open study list">
              <PanelLeftOpen size={16} aria-hidden="true" /> Studies <span className="pw-library-count">{caseItems.length}</span>
            </button>
          )}
          <div className="pw-studybar__id">
            <h1>{studyLabel}</h1>
            <span className="pw-tag">{localCt ? 'This tab only' : verifiedPrediction ? 'Verified source CT' : isCurated ? 'Validation example' : 'Prepared study'}</span>
          </div>
          <dl className="pw-studybar__meta">
            <div><dt>Series</dt><dd>{localCt ? 'Local source CT' : `Abdomen CT · ${verifiedPrediction ? 'Source' : 'Prepared'}`}</dd></div>
            <div><dt>Prediction</dt><dd title={predictionStatus}>{predictionStatus}</dd></div>
            {summaryStatus && <div><dt>Summary</dt><dd title={summaryStatus}>{summaryStatus}</dd></div>}
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
            value={viewMode}
            onChange={setViewMode}
            options={[
              ['2d', '2D', { icon: <Crosshair size={14} aria-hidden="true" /> }],
              ['3d', '3D', { icon: <Box size={14} aria-hidden="true" />, disabled: Boolean(verifiedPrediction && !has3dOutline),
                title: verifiedPrediction?.surfaceStatus === 'loading' ? 'Preparing 3D from the verified mask' : undefined }],
              ['split', 'Split', {
                disabled: Boolean(verifiedPrediction && !has3dOutline),
                icon: <Columns2 size={14} aria-hidden="true" />,
                disabled: !SPLIT_SUPPORTED,
                title: 'Split: 2D planes and 3D surfaces side by side, sharing layers, selection and Go-to',
              }],
            ]}
          />
          {is3dLike && (
            <Segmented
              label="3D scene"
              value={scene3d}
              onChange={(value) => dispatch({ type: 'PATCH_SETTINGS', value: { scene3d: value } })}
              options={[
                ['full', 'Abdomen', { disabled: !caseData.files?.ct_full, title: 'Full abdomen: the whole abdominal CT around the surfaces' }],
                ['region', 'Region', { title: 'Pancreas region: only the cropped CT around the pancreas' }],
                ['surfaces', 'Surfaces', { title: 'Surfaces only: just the pancreas and lesion' }],
              ]}
            />
          )}
          {verifiedPrediction?.surfaceStatus === 'loading' && <span className="pw-muted" role="status">Preparing 3D outline…</span>}
          {verifiedPrediction?.surfaceStatus === 'unavailable' && <span className="pw-muted" title={verifiedPrediction.surfaceError}>3D outline unavailable</span>}
          {is2dLike && !inspecting && <Segmented label="Visible planes" value={state.activePlane === 'multiplanar' ? layout.maximizedPlane || 'multiplanar' : state.activePlane}
            onChange={value => {
              dispatch({ type: 'SET_ACTIVE_PLANE', value: 'multiplanar' })
              setLayout({ maximizedPlane: value === 'multiplanar' ? null : value, hiddenPlanes: [] })
            }}
            options={[["multiplanar", "All planes", { disabled: Boolean(verifiedPrediction || localCt) }], ["axial", "Axial"], ["coronal", "Coronal"], ["sagittal", "Sagittal"]]} />}
          <Segmented
            label="Mouse tool"
            value={is2dLike ? twoDInteractionMode : state.interactionMode}
            onChange={(value) => dispatch({ type: 'SET_INTERACTION_MODE', value })}
            options={[
              viewMode === '3d'
                ? ['rotate', 'Rotate', { icon: <Rotate3d size={14} aria-hidden="true" />, title: 'Drag to orbit the camera' }]
                : ['navigate', 'Navigate', { icon: <Crosshair size={14} aria-hidden="true" />, title: 'Click or drag the crosshair' }],
              ['pan', 'Pan', { icon: <Move size={14} aria-hidden="true" />, disabled: framingLocked && !is3dLike,
                title: framingLocked ? (is3dLike ? 'Drag to reposition the 3D view' : 'Unlock framing to pan') : 'Drag to reposition the view' }],
              ...(is2dLike ? [['window', 'Window', { icon: <Contrast size={14} aria-hidden="true" />, title: 'Drag to adjust CT brightness and contrast' }]] : []),
              ['box-zoom', 'Box zoom', { disabled: framingLocked && !is3dLike,
                title: framingLocked && !is3dLike ? 'Unlock framing to zoom' : 'Left-drag a box around a region to zoom in' }],
            ]}
          />
          <label className="pw-select pw-toolbar__window">
            <span className="pw-sr-only">CT window preset</span>
            <select value={state.ctWindow} onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { ctWindow: event.target.value } })}>
              {CT_WINDOW_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          {(!inspecting || inspectionOverlay === 'fill') && <label className="pw-toolbench-opacity"><span>Overlay <output>{Math.round(state.overlayOpacity * 100)}%</output></span>
            <input type="range" min="0" max="1" step="0.05" value={state.overlayOpacity} aria-label="Prediction overlay opacity"
              onChange={event => dispatch({ type: 'PATCH_SETTINGS', value: { overlayOpacity: Number(event.target.value) } })} />
          </label>}
          <span className="pw-toolbar__spacer" />
          {is3dLike && (
            <div className="pw-toolbar__group" role="group" aria-label="3D zoom">
              <button type="button" className="pw-icon-btn" onClick={() => issueViewerCommand({ type: 'zoom', target: '3d', factor: 0.86 })} aria-label="Zoom out" title="Zoom out (−)">−</button>
              <output className="pw-toolbar__zoom" aria-label="3D zoom level" aria-live="off" title="3D zoom relative to Fit">{threeDZoom == null ? '—' : `${threeDZoom}%`}</output>
              <button type="button" className="pw-icon-btn" onClick={() => issueViewerCommand({ type: 'zoom', target: '3d', factor: 1.16 })} aria-label="Zoom in" title="Zoom in (+)">+</button>
            </div>
          )}
          <button type="button" className="pw-icon-btn" disabled={framingLocked && !is3dLike}
            onClick={() => issueViewerCommand({ type: 'fit', target: inspecting ? 'inspection' : undefined })} aria-label="Fit" title="Fit the complete CT in the viewer (F)">
            <Maximize size={15} aria-hidden="true" />
          </button>
          <button type="button" className="pw-icon-btn" disabled={framingLocked && is2dLike}
            onClick={resetView} aria-label="Reset viewer" title="Reset viewer (R)">
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

        <div className="pw-workspace-actions" role="group" aria-label="Workspace layout">
          <span className="pw-workspace-actions__label">IMAGING WORKSPACE</span>
          {is2dLike && !inspecting && !verifiedPrediction && !localCt && <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" aria-pressed={layout.linked}
            onClick={() => setLayout({ linked: !layout.linked })}>Linked crosshairs</button>}
          {hasPrediction && !inspecting && <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" aria-pressed={layout.measurementsVisible}
            onClick={() => setLayout({ measurementsVisible: !layout.measurementsVisible })}>Volume overlay</button>}
          <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" aria-pressed={panelOpen}
            onClick={() => setPanelOpen(!panelOpen)}>Expert panel</button>
          <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" aria-pressed={focusMode}
            onClick={toggleFocus}>{focusMode ? 'Exit focus' : 'Focus workspace'}</button>
          <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" onClick={toggleFullscreen}
            title={isFullscreen ? 'Exit display full screen (Esc)' : fullscreenAvailable ? 'Fill the entire display and hide browser controls (Esc to exit)' : 'Display full screen needs a supported browser'}><Expand size={13} aria-hidden="true" /> {isFullscreen ? 'Exit full screen' : 'Full screen'}</button>
          <button type="button" className="pw-btn pw-btn--sm pw-btn--ghost" onClick={() => {
            resetLayout(); setFocusMode(false); setMobilePanelOpen(false); setMobileStudiesOpen(false)
            dispatch({ type: 'SET_ACTIVE_PLANE', value: 'multiplanar' })
          }}>Restore layout</button>
        </div>
        {fullscreenError && <p className="pw-toolbench-notice" role="status">{fullscreenError}</p>}

          {state.evidenceMode === 'ct' && !hasPrediction && (
            <div className="pw-ct-only" role="region" aria-label="Prediction not shown">
              <strong>CT only</strong>
              <span>{localCt ? 'Analysis for this file requires a configured CT-only model worker.' : 'Model outlines are hidden.'}</span>
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

        {pancreasInReview && <LesionReviewBar anatomy="pancreas"
          component={pancreasDimensions} volumeMl={verifiedMeasurement.pancreasMl}
          status={pancreasInspection ? 'Cross shown on the measured slice only.' : null}
          actions={pancreasDimensions.calipers?.plane && <button type="button" className="pw-btn pw-btn--sm pw-btn--primary"
            onClick={inspectPancreas}>{pancreasInspection ? 'Go to measured slice' : 'Inspect CT slice'}</button>}
          onExit={exitInspection} />}
        {!pancreasInReview && hasPrediction && (is3dLike || lesionInReview) && <LesionReviewBar
          component={selectedComponent} number={selectedLesionNumber}
          status={lesionReviewMessage}
          actions={selectedComponent ? <>
            {is3dLike && selectedCalipers?.plane && <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary"
              title={show3dCalipers ? 'Hide the pinned cross' : 'Show the measured dimensions as a camera-facing cross'}
              aria-pressed={show3dCalipers} onClick={() => setLesionSelection(previous => previous === currentLesionSelection
                ? { ...previous, showCalipers3d: !show3dCalipers } : previous)}>{show3dCalipers ? 'Hide calipers' : 'Show calipers'}</button>}
            {selectedComponent.boundsWorldMm && <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary"
              disabled={!is3dLike && framingLocked}
              title={is3dLike ? 'Frame the selected lesion in 3D' : 'Frame a CT slice through the selected lesion'}
              onClick={() => issueViewerCommand({
                type: 'zoom-lesion', target: inspecting ? 'inspection' : is3dLike ? '3d' : '2d',
                boundsWorldMm: selectedComponent.boundsWorldMm, worldMm: selectedComponent.focusWorldMm,
              })}>Zoom to lesion</button>}
            {selectedCalipers?.plane && <button type="button" className="pw-btn pw-btn--sm pw-btn--primary"
              onClick={() => inspectLesion(selectedComponent)}>{measurementInspection ? 'Go to measured slice' : 'Inspect CT slice'}</button>}
          </> : !measuredLesionVisible ? <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary" onClick={() => {
            dispatch({ type: 'SET_EVIDENCE_MODE', value: 'prediction' })
            dispatch({ type: 'PATCH_SETTINGS', value: { layerVisibility: { ...state.layerVisibility, pred: true, lesion: true } } })
          }}>Show model lesion</button> : components.length === 1 ? <button type="button"
            className="pw-btn pw-btn--sm pw-btn--primary" onClick={() => markMeasuredLesion(components[0])}>Select predicted lesion</button>
            : components.length > 1 ? <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary"
              onClick={() => openPanel('findings')}>Choose lesion in Findings</button> : null}
          onExit={lesionInReview ? exitInspection : null} />}

        {inspecting && <div className="pw-inspection-tools" role="toolbar" aria-label="Finding inspection tools">
          <Segmented label="CT overlay" value={inspectionOverlay} onChange={setInspectionOverlay}
            options={[[ 'outline', 'Outline' ], [ 'fill', 'Fill' ], [ 'off', 'CT only' ]]} />
          {has3dOutline && <button type="button" className="pw-btn pw-btn--sm pw-btn--ghost" aria-pressed={sliceLocator}
            onClick={() => setSliceLocator(value => !value)}>Show slice in 3D</button>}
          <InspectionSourceControls sourceAvailable={Boolean(sourceDetails)} preparedAvailable={!verifiedPrediction}
            activeSource={sourceDetails ? 'source' : 'prepared'} />
        </div>}

        <div
          className={`pw-viewer${is2dLike ? ' pw-viewer--slice-tools' : ''}${inspecting ? ' pw-viewer--inspection' : ''}`}
          ref={viewerRef}
          onPointerDownCapture={(event) => {
            const rect = viewerRef.current?.getBoundingClientRect()
            if (rect) lastPointerRef.current = { x: event.clientX - rect.left, y: event.clientY - rect.top, t: Date.now() }
          }}
        >
          <ViewerSuspense>
              <div className={`pw-toolbench-scene pw-toolbench-scene--${viewMode}${inspecting ? ' pw-toolbench-scene--inspection' : ''}`}>
                <section className="pw-toolbench-scene__planes" aria-label="2D planes" hidden={Boolean(inspecting) || viewMode === '3d'}>
                  {twoDVisited && <ToolbenchViewer {...viewerProps} mode="2d" interactionMode={twoDInteractionMode}
                    framingLocked={framingLocked} onFramingLockedChange={changeFramingLock}
                    layout={layout} onLayoutChange={setLayout} linked={layout.linked}
                    singlePane={Boolean(verifiedPrediction || localCt)} onNavigationChange={setNavigation} label={`${viewerLabel} · 2D planes`} />}
                </section>
                {inspectionProps && <section className="pw-toolbench-scene__inspection" aria-label="Measured CT">
                  <ToolbenchViewer {...inspectionProps} singlePane interactionMode={twoDInteractionMode}
                    linked={false} onNavigationChange={setInspectionNavigation} label={`${viewerLabel} · Measured CT`} />
                </section>}
                <section className="pw-toolbench-scene__3d" aria-label="3D surfaces" hidden={viewMode === '2d'}>
                  <span className="pw-split__label" title="The 3D camera moves independently of the 2D crosshair">{scene3d === 'full' ? 'Abdomen · 3D' : scene3d === 'region' ? 'Pancreas region · 3D' : 'Model surfaces · 3D'}</span>
                  {threeDVisited && <NiivueViewer {...viewerProps} {...viewer3dProps} mode="3d" interactionMode={threeDInteractionMode} label={`${viewerLabel} · 3D surfaces`} />}
                  {snapPad}
                </section>
              </div>
          </ViewerSuspense>
          {layout.measurementsVisible && predictionShown && !inspecting && (
            <div className="pw-toolbench-measure-overlay" aria-label="Displayed prediction measurements">
              <MeasurementReadout state={measurementState} compact showEvidence={false} />
            </div>
          )}

          {state.selectedObject && !lesionInReview && !pancreasInReview && (
            <StructurePopover
              object={state.selectedObject}
              anchor={popAnchor}
              finding={finding}
              measurementState={measurementState}
              overlap={overlap}
              comparing={comparing}
              gtHasLesion={Boolean(caseData.gt_has_lesion)}
              onAsk={askAbout}
              onClose={exitInspection}
              focusControl={(
                <Segmented
                  label="Focus treatment"
                  value={state.focusTreatment}
                  onChange={(value) => dispatch({ type: 'SET_FOCUS_TREATMENT', value })}
                  options={[['context', 'Show context'], ['isolate', 'Isolate']]}
                />
              )}
            />
          )}


          {comparing && (state.sourceFocus === 'difference' || state.sourceFocus === 'both') && (
            <div className="pw-viewer-legend" aria-label="Colour key">
              {state.sourceFocus === 'difference' ? (
                <>
                  <span><i style={{ '--key': REVIEW_COLORS.difference.agreement }} />Agreement</span>
                  <span><i style={{ '--key': REVIEW_COLORS.difference.predOnly }} />Prediction only</span>
                  <span><i style={{ '--key': REVIEW_COLORS.difference.gtOnly }} />Reference only</span>
                </>
              ) : (
                <>
                  <span><i style={{ '--key': REVIEW_COLORS.pred.pancreas }} />Prediction pancreas</span>
                  <span><i style={{ '--key': REVIEW_COLORS.pred.lesion }} />Prediction lesion</span>
                  <span><i className="pw-viewer-legend__ref" style={{ '--key': REVIEW_COLORS.gt.pancreas }} />Reference pancreas</span>
                  <span><i className="pw-viewer-legend__ref" style={{ '--key': REVIEW_COLORS.gt.lesion }} />Reference lesion</span>
                </>
              )}
            </div>
          )}

          {comparing && state.sourceFocus === 'difference' && viewMode !== '2d' && <p className="pw-difference-note" role="note">Smoothed 3D surfaces may hide thin differences. Check the exact overlays in 2D.</p>}
          <div className="pw-viewer-help">
            <button type="button" className="pw-viewer-help__toggle" aria-expanded={helpOpen} aria-label="Viewer controls" title="Viewer controls" onClick={() => setHelpOpen((open) => !open)}>
              <CircleHelp size={16} aria-hidden="true" />
            </button>
            {helpOpen && (
              <section className="pw-viewer-help__card" aria-label="Viewer controls">
                <header><strong>{viewMode === '2d' ? '2D controls' : '3D controls'}</strong>
                  <button type="button" className="pw-icon-btn" onClick={() => setHelpOpen(false)} aria-label="Close viewer controls"><X size={13} /></button>
                </header>
                <dl>
                  {CONTROL_HELP[viewMode === '2d' ? '2d' : '3d'].map(([term, detail]) => (
                    <div key={term}><dt>{term}</dt><dd>{detail}</dd></div>
                  ))}
                </dl>
              </section>
            )}
          </div>

          <p key={`${viewMode}-${state.interactionMode}`} className="pw-viewer__hint" aria-hidden="true" hidden={!boxZoom && !pan && ((state.evidenceMode === 'ct' && !hasPrediction) || viewMode === 'split')}>
            {boxZoom ? (framingLocked && is2dLike ? 'Left-drag a box on the 3D image · 2D framing locked' : 'Left-drag a box around the region to zoom')
              : pan ? (framingLocked && viewMode === 'split' ? 'Drag to reposition the 3D view · 2D framing locked' : 'Drag to reposition · scroll to zoom')
              : viewMode === '3d'
              ? 'Drag to orbit · scroll to zoom · click a surface to focus'
              : framingLocked ? 'Framing locked · use the slice sliders'
                : state.interactionMode === 'window' ? 'Drag to adjust brightness and contrast · scroll to zoom'
                  : 'Scroll to zoom · use the slice sliders'}
          </p>

          {state.settingsOpen && (
            <aside className="review-settings-popover pw-popover" aria-label="View settings" tabIndex={0}>
              <div className="review-settings-popover__header">
                <div><Settings2 size={15} /><strong>View settings</strong></div>
                <button type="button" onClick={() => dispatch({ type: 'TOGGLE_SETTINGS' })} aria-label="Close view settings"><X size={14} /></button>
              </div>
              <label className="review-range">
                <span>Mask strength <strong>{Math.round(state.overlayOpacity * 100)}%</strong></span>
                <input type="range" min="0" max="1" step="0.05" value={state.overlayOpacity}
                  onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { displayPreset: 'custom', overlayOpacity: Number(event.target.value) } })} />
              </label>
              {is3dLike && scene3d !== 'surfaces' && (
                <label className="review-range">
                  <span>CT visibility in 3D <strong>{Math.round((state.ctOpacity / 0.45) * 100)}%</strong></span>
                  <input type="range" min="0.04" max="0.45" step="0.01" value={state.ctOpacity}
                    onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { displayPreset: 'custom', ctOpacity: Number(event.target.value) } })} />
                </label>
              )}
              {is2dLike && (
                <label className="review-layer-check">
                  <span><ScanLine size={13} /> Full abdominal CT in 2D</span>
                  <input type="checkbox" checked={state.showFull} disabled={!caseData.files?.ct_full}
                    onChange={(event) => dispatch({ type: 'PATCH_SETTINGS', value: { showFull: event.target.checked } })} />
                </label>
              )}
              <button
                type="button"
                className="pw-btn pw-btn--link review-settings-reset"
                onClick={() => dispatch({ type: 'PATCH_SETTINGS', value: { displayPreset: 'anatomy', overlayOpacity: DEFAULT_OVERLAY_OPACITY, ctOpacity: DEFAULT_CT_OPACITY } })}
              >
                Restore default display
              </button>
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
              color={comparing && ['both', 'difference'].includes(state.sourceFocus) ? 'var(--pw-text-faint)' : referenceShown && !predictionShown ? REVIEW_COLORS.gt.pancreas : REVIEW_COLORS.pred.pancreas}
              disabled={state.evidenceMode === 'ct'}
              onClick={() => dispatch({ type: 'TOGGLE_LAYER', layer: 'pancreas' })}
            />
            <LayerToggle
              checked={state.layerVisibility.lesion}
              label="Lesion"
              color={comparing && ['both', 'difference'].includes(state.sourceFocus) ? 'var(--pw-text-faint)' : referenceShown && !predictionShown ? REVIEW_COLORS.gt.lesion : REVIEW_COLORS.pred.lesion}
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

        {layout.measurementsVisible && !inspecting && <div className="pw-toolbench-measure-strip">
          <MeasurementReadout state={measurementState} />
        </div>}
        {is3dLike && scene3d !== 'surfaces' && (
          <div className="pw-slicebar pw-slicebar--cut" role="group" aria-label="CT peel">
            <div className="pw-slicebar__direction">
              <strong className="pw-slicebar__label">Peel</strong>
              <Segmented label="Peel direction" value={state.clipDirection} options={PEEL_DIRECTIONS}
                onChange={clipDirection => dispatch({ type: 'PATCH_SETTINGS', value: { clipDirection } })} />
            </div>
            <div className="pw-slicebar__slider">
              <div className="pw-slicebar__track" style={{ '--slice-progress': `${state.clipProgress}%` }}>
                {pancreasRevealProgress !== null && (
                  <button
                    type="button"
                    className="pw-cut-marker"
                    style={{ left: `${pancreasRevealProgress}%` }}
                    onClick={() => setClipProgress(pancreasRevealProgress)}
                    aria-label={`Peel to the pancreas (${pancreasRevealProgress}%)`}
                    title={`Peel to the pancreas from the ${peelFromBack ? 'back' : 'front'}`}
                  />
                )}
                <SliceSlider min="0" max="100" step="1" value={state.clipProgress}
                  onChange={(event) => setClipProgress(Number(event.target.value), { live: true })} aria-label={`${peelDirectionLabel} CT removal`} />
              </div>
              <span className="pw-slicebar__value pw-num">{Math.round(state.clipProgress)}%</span>
            </div>
            <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" disabled={state.clipProgress === 0 && pancreasRevealProgress === null} onClick={() => setClipProgress(state.clipProgress > 0 ? 0 : pancreasRevealProgress)}>
              {state.clipProgress > 0 ? 'Restore CT' : 'Peel to pancreas'}
            </button>
          </div>
        )}
      </section>

      <aside
        className="pw-panel"
        id="pw-assistant"
        aria-label="PROWL Assistant"
        hidden={!panelOpen}
        inert={panelOpen ? undefined : ''}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && window.matchMedia?.('(max-width: 1023px)').matches) {
            setPanelOpen(false)
            document.querySelector('[aria-controls="pw-assistant"]')?.focus()
          }
        }}
      >
        <WorkspaceResizeHandle label="Expert panel width" value={layout.panelWidth} min={260} max={520} direction={-1}
          onChange={panelWidth => setLayout({ panelWidth })} className="pw-workspace-resize--left" />
        <header className="pw-panel__head">
          <PantherBadge size="sm" pulse={assistantPending} />
          <div>
            <h2>PROWL Assistant</h2>
            <p>Evidence alongside your expertise.</p>
          </div>
          <button
            type="button"
            className="pw-icon-btn pw-panel__widen"
            onClick={() => {
              // A wide assistant needs the room: tuck the study list away and re-dock any open card.
              if (!panelWide) setStudyListOpen(false)
              setPopAnchor(null)
              setLayout({ panelWidth: panelWide ? 320 : 480 })
            }}
            aria-pressed={panelWide}
            aria-label={panelWide ? 'Narrow assistant panel' : 'Widen assistant panel'}
            title={panelWide ? 'Narrow the assistant' : 'Widen the assistant for reading answers'}
          >
            {panelWide ? <Minimize2 size={15} aria-hidden="true" /> : <Maximize2 size={15} aria-hidden="true" />}
          </button>
          <button type="button" className="pw-icon-btn pw-panel__close" onClick={() => setPanelOpen(false)} aria-label="Close assistant panel" title="Close assistant panel">
            <X size={16} aria-hidden="true" />
          </button>
        </header>
        <div className="pw-toolbench-pinned-finding" aria-label="Current model finding">
          <span className="pw-swatch" style={{ background: REVIEW_COLORS.pred.lesion }} aria-hidden="true" />
          <div><strong>{selectedFinding ? selectedPancreas ? 'Predicted pancreas' : `Predicted lesion ${selectedLesionNumber}`
            : hasPrediction ? finding.lesionFlagged === true ? 'Possible lesion · review required'
              : finding.lesionFlagged === false ? 'No lesion predicted' : 'Lesion status unavailable'
              : 'Prediction not displayed'}</strong>
            <small>{selectedFinding?.dimensions?.calipers
              ? `${selectedFinding.dimensions.calipers.axes.map(axis => (axis.lengthMm / 10).toFixed(2)).join(' × ')} cm · measured slice`
              : verifiedPrediction ? modelLabel : hasPrediction ? 'Prepared saved outline · model proposal' : 'Show the prediction to inspect model findings'}</small></div>
        </div>
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
            measurementState={measurementState}
            sourceSlice={Boolean(verifiedPrediction)}
            verifiedRun={Boolean(verifiedPrediction)}
            predictionUrl={verifiedPrediction?.urls?.pred}
            selectedPancreas={selectedPancreas}
            onSelectPancreas={meshFiles?.pancreas_pred ? selectPancreasIn3d : null}
            onInspectPancreas={inspectPancreas}
            selectedLesionId={currentLesionSelection?.component?.id}
            onSelectLesion={meshFiles?.lesion_pred ? selectLesionIn3d : null}
            onInspectLesion={inspectLesion}
            lesionSelectionNotice={currentLesionSelection?.unmatched
              ? 'This click could not be matched to a measured lesion. Select a lesion in Findings to inspect it.'
              : null}
            overlap={overlap}
            referenceState={referenceState}
            comparing={comparing}
            ranges={navigation.ranges}
            analysisFailed={analysisFailed}
            onShowInViewer={focusStructure}
            onAsk={askAbout}
            onCompare={compareWithReference}
            reviewStatus={reviewStatus}
            onSetReviewStatus={onSetReviewStatus}
            onStartSummary={() => setPanelTab('summary')}
            modelLabel={modelLabel}
          />
          <FindingKeyViews scope={{ studyId: caseId, ctSha256: verifiedMeasurement?.ctSha256,
            predictionSha256: verifiedMeasurement?.predictionSha256, manifestHash: verifiedPrediction?.manifestHash }}
            finding={inspecting ? selectedFinding : null} capture={captureKeyView}
            captureThumbnail={() => inspectionViewRef.current?.thumbnail?.()} onReopen={reopenKeyView} />
        </div>
        <div className="pw-panel__body" role="tabpanel" id="pw-tabpanel-ask" aria-labelledby="pw-tab-ask" hidden={panelTab !== 'ask'}>
          <FindingAskPanel key={studyKey} measurementState={measurementState} finding={selectedFinding}
            onInspect={inspectSelected} literatureRequest={askDraft}>
            {isValidElement(askPanel) ? cloneElement(askPanel, { draftRequest: askDraft, measurementContext: null }) : askPanel}
          </FindingAskPanel>
        </div>
        <div className="pw-panel__body" role="tabpanel" id="pw-tabpanel-summary" aria-labelledby="pw-tab-summary" hidden={panelTab !== 'summary'}>
          {verifiedPrediction && predictionJob ? <ReviewDecisionPanel base={predictionJob.base}
            manifestHash={verifiedPrediction.manifestHash} manifest={verifiedPrediction.manifest} onDraftChange={onReviewDirty} />
          : summaryStore ? (
            <ReviewSummary
              studyId={caseId}
              studyLabel={studyLabel}
              seriesLabel={seriesLabel}
              prediction={prediction}
              facts={summaryFacts}
              drafts={summaryStore.drafts}
              onChange={summaryStore.onChange}
            />
          ) : summaryPanel}
        </div>
      </aside>
    </main>
  )
}
