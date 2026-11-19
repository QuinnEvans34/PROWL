import { useEffect, useRef, useState } from 'react'
import { Eye, EyeOff, Link2, LockKeyhole, LockKeyholeOpen, Maximize2, Minimize2, Scan, ZoomIn, ZoomOut } from 'lucide-react'
import NiivueViewer from './NiivueViewer.jsx'
import SliceSlider from './SliceSlider.jsx'
import { viewerSceneKey } from '../lib/viewerSceneKey.js'
import '../styles/toolbench-viewer.css'

const PLANES = ['axial', 'coronal', 'sagittal']
const TITLES = { axial: 'Axial', coronal: 'Coronal', sagittal: 'Sagittal' }
const EXPLANATIONS = { axial: 'Superior / inferior', coronal: 'Anterior / posterior', sagittal: 'Left / right' }
const DEFAULT_LAYOUT = { primaryShare: 64, secondaryShare: 50, hiddenPlanes: [], maximizedPlane: null }
const clampShare = (value, fallback = 50) => Math.max(25, Math.min(80, Number(value) || fallback))
const samePosition = (a, b) => a?.length === 3 && b?.length === 3 && a.every((value, index) => Math.abs(value - b[index]) < 0.000001)

function PaneDivider({ orientation, value, onChange, label, containerRef, min = 25, max = 80 }) {
  const dragging = useRef(false)
  return <div
    className={`tb-divider tb-divider--${orientation}`}
    role="separator"
    tabIndex={0}
    aria-label={label}
    aria-orientation={orientation}
    aria-valuemin={min}
    aria-valuemax={max}
    aria-valuenow={Math.round(value)}
    onPointerDown={event => {
      dragging.current = true
      event.currentTarget.setPointerCapture?.(event.pointerId)
      event.preventDefault()
    }}
    onPointerMove={event => {
      if (!dragging.current) return
      const bounds = containerRef.current?.getBoundingClientRect()
      if (!bounds?.width || !bounds?.height) return
      const proportion = orientation === 'vertical'
        ? (event.clientX - bounds.left) / bounds.width
        : (event.clientY - bounds.top) / bounds.height
      onChange(Math.max(min, Math.min(max, proportion * 100)))
    }}
    onPointerUp={event => { dragging.current = false; event.currentTarget.releasePointerCapture?.(event.pointerId) }}
    onPointerCancel={() => { dragging.current = false }}
    onKeyDown={event => {
      const decrease = orientation === 'vertical' ? 'ArrowLeft' : 'ArrowUp'
      const increase = orientation === 'vertical' ? 'ArrowRight' : 'ArrowDown'
      if (![decrease, increase, 'Home', 'End'].includes(event.key)) return
      event.preventDefault()
      event.stopPropagation()
      onChange(event.key === 'Home' ? min : event.key === 'End' ? max : Math.max(min, Math.min(max, value + (event.key === decrease ? -2 : 2))))
    }}
  ><span /></div>
}

/** Three persistent imaging canvases: layout changes never destroy a pane's view. */
export default function ToolbenchViewer({
  viewerProps = null,
  layout = null,
  onLayoutChange = null,
  linked = true,
  onLinkedChange = null,
  framingLocked: controlledFraming = null,
  onFramingLockedChange = null,
  overlay = null,
  ...directViewerProps
}) {
  const props = { ...viewerProps, ...directViewerProps, mode: '2d' }
  const { activePlane = 'multiplanar', navigationCommand, onNavigationChange, ctWindow, ctRange, label = 'CT viewer' } = props
  const sceneKey = viewerSceneKey(props)
  const framingStudy = props.caseData?.case_id || props.caseData?.files?.ct
  const [lockedStudy, setLockedStudy] = useState(null)
  // Returning to a study starts unlocked, even when its presentation was saved.
  useEffect(() => { setLockedStudy(null) }, [framingStudy])
  const framingLocked = controlledFraming ?? (framingStudy != null && lockedStudy === framingStudy)
  function toggleFraming() {
    setLockedStudy(framingLocked ? null : framingStudy)
    onFramingLockedChange?.(!framingLocked)
  }
  const [localLayout, setLocalLayout] = useState(DEFAULT_LAYOUT)
  const settings = { ...DEFAULT_LAYOUT, ...localLayout, ...layout }
  const primaryShare = clampShare(settings.primaryShare, 64)
  const secondaryShare = clampShare(settings.secondaryShare)
  const hiddenPlanes = (settings.hiddenPlanes || []).filter(plane => PLANES.includes(plane))
  const maximized = PLANES.includes(settings.maximizedPlane) ? settings.maximizedPlane : null
  const visible = activePlane !== 'multiplanar' && PLANES.includes(activePlane)
    ? [activePlane]
    : maximized ? [maximized] : PLANES.filter(plane => !hiddenPlanes.includes(plane))
  if (!visible.length) visible.push('axial')

  const containerRef = useRef(null)
  const serial = useRef(0)
  const anchorRef = useRef(null)
  const snapshotsRef = useRef({})
  const onNavigationRef = useRef(onNavigationChange)
  onNavigationRef.current = onNavigationChange
  const [snapshots, setSnapshots] = useState({})
  const [zoomLevels, setZoomLevels] = useState({})
  const [syncCrosshair, setSyncCrosshair] = useState(null)
  const [syncWindow, setSyncWindow] = useState(null)
  const [commands, setCommands] = useState({})
  const [active, setActive] = useState('axial')
  const effectiveActive = visible.includes(active) ? active : visible[0]
  const lastCommand = useRef(null)

  function changeLayout(partial) {
    setLocalLayout(current => ({ ...current, ...partial }))
    onLayoutChange?.(partial)
  }

  useEffect(() => {
    anchorRef.current = null
    snapshotsRef.current = {}
    setSnapshots({})
    setSyncCrosshair(null)
    setSyncWindow(null)
    setCommands({})
  }, [sceneKey])

  // A selected window is shared; a manual right-drag is shared through syncWindow.
  // Clear the manual override when the user selects a new explicit preset/range.
  useEffect(() => { setSyncWindow(null) }, [ctWindow, ctRange?.[0], ctRange?.[1]])

  useEffect(() => {
    if (!linked) return
    const snapshot = snapshotsRef.current[effectiveActive]
    if (!snapshot?.fractions) return
    anchorRef.current = { sceneKey, fractions: snapshot.fractions }
    setSyncCrosshair({ id: ++serial.current, sceneKey, fractions: snapshot.fractions })
  }, [linked])

  function command(plane, next) {
    setCommands(current => ({ ...current, [plane]: { ...next, id: `pane-${++serial.current}` } }))
  }

  useEffect(() => {
    if (!navigationCommand || lastCommand.current === navigationCommand.id) return
    lastCommand.current = navigationCommand.id
    const target = PLANES.includes(navigationCommand.plane) ? navigationCommand.plane : effectiveActive
    command(target, navigationCommand)
  }, [navigationCommand?.id])

  function receiveNavigation(plane, snapshot) {
    if (!snapshot || snapshot.sceneKey !== sceneKey) return
    snapshotsRef.current = { ...snapshotsRef.current, [plane]: snapshot }
    setSnapshots(snapshotsRef.current)
    if (linked && snapshot.fractions && snapshot.origin !== 'sync') {
      const anchor = anchorRef.current
      // Each canvas loads asynchronously. Later initial loads must follow the
      // established position rather than replacing it with their own default.
      if (snapshot.origin === 'initial' && anchor?.sceneKey === sceneKey) return
      if (anchor?.sceneKey !== sceneKey || !samePosition(anchor.fractions, snapshot.fractions)) {
        anchorRef.current = { sceneKey, fractions: snapshot.fractions }
        setSyncCrosshair({ id: ++serial.current, sceneKey, fractions: snapshot.fractions })
      }
    }
    if (snapshot.origin === 'sync') return
    const aggregate = {
      ...snapshot,
      indices: { ...snapshot.indices },
      totals: { ...snapshot.totals },
      activePlane: plane,
    }
    if (!linked) {
      for (const key of PLANES) {
        const peer = snapshotsRef.current[key]
        if (peer?.indices) aggregate.indices[key] = peer.indices[key]
        if (peer?.totals) aggregate.totals[key] = peer.totals[key]
      }
    }
    onNavigationRef.current?.(aggregate)
  }

  function receiveZoom(plane, scale) {
    const percent = Number.isFinite(scale) ? Math.round(scale * 100) : null
    setZoomLevels(current => current[plane]?.sceneKey === sceneKey && current[plane]?.percent === percent
      ? current : { ...current, [plane]: { sceneKey, percent } })
  }

  const areas = visible.length === 3
    ? '"axial primary coronal" "axial primary secondary" "axial primary sagittal"'
    : visible.length === 2 ? `"${visible[0]} primary ${visible[1]}"` : `"${visible[0]}"`
  const gridStyle = {
    gridTemplateAreas: areas,
    gridTemplateColumns: visible.length > 1 ? `minmax(0, ${primaryShare}fr) 8px minmax(0, ${100 - primaryShare}fr)` : 'minmax(0, 1fr)',
    gridTemplateRows: visible.length === 3 ? `minmax(0, ${secondaryShare}fr) 8px minmax(0, ${100 - secondaryShare}fr)` : 'minmax(0, 1fr)',
  }

  return <div className="tb-viewer" aria-label="Adjustable CT workspace">
    <div className="tb-viewer__rail">
      <span className="tb-viewer__context"><span className="tb-live-dot" />2D imaging <small>{visible.length === 1 ? TITLES[visible[0]] : `${visible.length} planes`}</small></span>
      <div className="tb-viewer__rail-actions">
        <button type="button" className="tb-viewer__framing" aria-pressed={framingLocked}
          disabled={!framingLocked && !visible.some(plane => snapshots[plane]?.sceneKey === sceneKey)}
          onClick={toggleFraming} title={framingLocked ? 'Pan and zoom are locked; slicing and window controls still work' : 'Keep pan and zoom steady while browsing slices'}>
          {framingLocked ? <LockKeyhole size={13} aria-hidden="true" /> : <LockKeyholeOpen size={13} aria-hidden="true" />}
          Lock framing
        </button>
        {onLinkedChange ? <button className="tb-link" type="button" aria-pressed={linked} onClick={() => onLinkedChange(!linked)} title="Link anatomical crosshairs across planes"><Link2 size={13} />{linked ? 'Linked' : 'Independent'}</button> : <span className="tb-link"><Link2 size={13} />{linked ? 'Linked crosshairs' : 'Independent planes'}</span>}
        {hiddenPlanes.length > 0 && activePlane === 'multiplanar' && !maximized && <button type="button" onClick={() => changeLayout({ hiddenPlanes: [] })}><Eye size={13} />Restore planes</button>}
        {maximized && activePlane === 'multiplanar' && <button type="button" onClick={() => changeLayout({ maximizedPlane: null })}><Minimize2 size={13} />Restore layout</button>}
      </div>
    </div>
    <div className="tb-viewer__grid" ref={containerRef} style={gridStyle} data-visible-planes={visible.length}>
      {PLANES.map(plane => {
        const snapshot = snapshots[plane]?.sceneKey === sceneKey ? snapshots[plane] : null
        const paneCommand = commands[plane]
        const total = snapshot?.totals?.[plane] || 1
        const index = snapshot?.indices?.[plane] || 0
        const ready = Boolean(snapshot)
        const zoom = ready && zoomLevels[plane]?.sceneKey === sceneKey ? zoomLevels[plane].percent : null
        const shown = visible.includes(plane)
        const only = visible.length === 1
        return <section
          key={plane}
          className={`tb-pane${effectiveActive === plane ? ' tb-pane--active' : ''}`}
          style={{ gridArea: plane, display: shown ? undefined : 'none' }}
          aria-label={`${TITLES[plane]} CT plane`}
          aria-hidden={!shown}
          tabIndex={shown ? 0 : -1}
          onPointerDownCapture={() => setActive(plane)}
          onFocusCapture={() => setActive(plane)}
        >
          <header className="tb-pane__header">
            <span className="tb-pane__title"><strong>{TITLES[plane]}</strong><small>{EXPLANATIONS[plane]}</small></span>
            <div className="tb-pane__actions">
              <button type="button" disabled={!ready || framingLocked} aria-label={`Zoom out ${TITLES[plane].toLowerCase()}`} title="Zoom out" onClick={() => command(plane, { type: 'zoom', factor: 1 / 1.2 })}><ZoomOut size={13} /></button>
              <output className="tb-pane__zoom" aria-label={`${TITLES[plane]} zoom level`} aria-live="off" title="Zoom relative to Fit">{zoom == null ? '—' : `${zoom}%`}</output>
              <button type="button" disabled={!ready || framingLocked} aria-label={`Zoom in ${TITLES[plane].toLowerCase()}`} title="Zoom in" onClick={() => command(plane, { type: 'zoom', factor: 1.2 })}><ZoomIn size={13} /></button>
              <button type="button" disabled={!ready || framingLocked} aria-label={`Fit ${TITLES[plane].toLowerCase()} image`} title="Fit image" onClick={() => command(plane, { type: 'fit' })}><Scan size={13} /></button>
              {activePlane === 'multiplanar' && <button type="button" aria-label={`${maximized === plane ? 'Restore' : 'Maximize'} ${TITLES[plane].toLowerCase()} plane`} title={maximized === plane ? 'Restore layout' : 'Maximize plane'} onClick={() => changeLayout({ maximizedPlane: maximized === plane ? null : plane })}>{maximized === plane ? <Minimize2 size={13} /> : <Maximize2 size={13} />}</button>}
              {activePlane === 'multiplanar' && !only && <button type="button" aria-label={`Hide ${TITLES[plane].toLowerCase()} plane`} title="Hide plane" onClick={() => changeLayout({ hiddenPlanes: [...hiddenPlanes, plane] })}><EyeOff size={13} /></button>}
            </div>
          </header>
          <div className="tb-pane__image">
            <NiivueViewer
              {...props}
              mode="2d"
              wheelZoom
              framingLocked={framingLocked}
              activePlane={plane}
              navigationCommand={paneCommand?.type === 'measurement-point' && !props.measurementCalipers ? null : paneCommand || null}
              syncCrosshair={linked ? syncCrosshair : null}
              syncWindow={syncWindow}
              showPlaneLabels={false}
              onNavigationChange={snapshot => receiveNavigation(plane, snapshot)}
              onZoomChange={scale => receiveZoom(plane, scale)}
              onWindowChange={window => {
                if (window.sceneKey === sceneKey) setSyncWindow({ ...window, id: ++serial.current })
              }}
              label={`${label} · ${TITLES[plane]}`}
            />
          </div>
          <footer className="tb-pane__navigator">
            <span aria-hidden="true">Slice</span>
            <SliceSlider aria-label={`${TITLES[plane]} slice`} min="0" max={total - 1} step="1" value={index}
              disabled={!ready} aria-valuetext={ready ? `Slice ${index + 1} of ${total}` : 'Loading scan'}
              onChange={event => command(plane, { type: 'slice', plane, index: Number(event.target.value) })} />
            <span className="tb-pane__slice-count" aria-hidden="true">{ready ? `${index + 1} / ${total}` : '—'}</span>
          </footer>
        </section>
      })}
      {visible.length > 1 && <div className="tb-viewer__primary-divider" style={{ gridArea: 'primary' }}><PaneDivider orientation="vertical" label="Primary pane size" min={40} max={80} value={primaryShare} onChange={value => changeLayout({ primaryShare: value })} containerRef={containerRef} /></div>}
      {visible.length === 3 && <div className="tb-viewer__secondary-divider" style={{ gridArea: 'secondary' }}><PaneDivider orientation="horizontal" label="Secondary pane size" min={25} max={75} value={secondaryShare} onChange={value => changeLayout({ secondaryShare: value })} containerRef={containerRef} /></div>}
      {overlay && <div className="tb-viewer__overlay">{overlay}</div>}
    </div>
  </div>
}
