import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, Eye, EyeOff, Link2, Maximize2, Minimize2, Scan, ZoomIn, ZoomOut } from 'lucide-react'
import NiivueViewer from './NiivueViewer.jsx'
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
  onActivePlaneChange = null,
  overlay = null,
  ...directViewerProps
}) {
  const props = { ...viewerProps, ...directViewerProps, mode: '2d' }
  const { activePlane = 'multiplanar', navigationCommand, onNavigationChange, ctWindow, ctRange, label = 'CT viewer' } = props
  const sceneKey = viewerSceneKey(props)
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
  const callbacks = useRef({ onNavigationChange, onActivePlaneChange })
  callbacks.current = { onNavigationChange, onActivePlaneChange }
  const [snapshots, setSnapshots] = useState({})
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

  function activate(plane) {
    setActive(plane)
    callbacks.current.onActivePlaneChange?.(plane)
  }

  useEffect(() => {
    callbacks.current.onActivePlaneChange?.(effectiveActive)
  }, [effectiveActive, sceneKey])

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
    callbacks.current.onNavigationChange?.(aggregate)
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
        {onLinkedChange ? <button className="tb-link" type="button" aria-pressed={linked} onClick={() => onLinkedChange(!linked)} title="Link anatomical crosshairs across planes"><Link2 size={13} />{linked ? 'Linked' : 'Independent'}</button> : <span className="tb-link"><Link2 size={13} />{linked ? 'Linked crosshairs' : 'Independent planes'}</span>}
        {hiddenPlanes.length > 0 && activePlane === 'multiplanar' && !maximized && <button type="button" onClick={() => changeLayout({ hiddenPlanes: [] })}><Eye size={13} />Restore planes</button>}
        {maximized && activePlane === 'multiplanar' && <button type="button" onClick={() => changeLayout({ maximizedPlane: null })}><Minimize2 size={13} />Restore layout</button>}
      </div>
    </div>
    <div className="tb-viewer__grid" ref={containerRef} style={gridStyle} data-visible-planes={visible.length}>
      {PLANES.map(plane => {
        const snapshot = snapshots[plane]?.sceneKey === sceneKey ? snapshots[plane] : null
        const total = snapshot?.totals?.[plane] || 1
        const index = snapshot?.indices?.[plane] || 0
        const ready = Boolean(snapshot)
        const shown = visible.includes(plane)
        const only = visible.length === 1
        return <section
          key={plane}
          className={`tb-pane${effectiveActive === plane ? ' tb-pane--active' : ''}`}
          style={{ gridArea: plane, display: shown ? undefined : 'none' }}
          aria-label={`${TITLES[plane]} CT plane`}
          aria-hidden={!shown}
          tabIndex={shown ? 0 : -1}
          onPointerDownCapture={() => activate(plane)}
          onFocusCapture={() => activate(plane)}
          onKeyDown={event => {
            if (event.target.closest('button, input, select, textarea') || !ready || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return
            event.preventDefault()
            event.stopPropagation()
            const delta = ['ArrowLeft', 'ArrowDown'].includes(event.key) ? -1 : 1
            command(plane, { type: 'slice', plane, index: Math.max(0, Math.min(total - 1, index + delta * (event.shiftKey ? 10 : 1))) })
          }}
        >
          <header className="tb-pane__header">
            <span className="tb-pane__title"><strong>{TITLES[plane]}</strong><small>{EXPLANATIONS[plane]}</small></span>
            <div className="tb-pane__actions">
              <button type="button" disabled={!ready} aria-label={`Zoom out ${TITLES[plane].toLowerCase()}`} title="Zoom out" onClick={() => command(plane, { type: 'zoom', factor: 1 / 1.2 })}><ZoomOut size={13} /></button>
              <button type="button" disabled={!ready} aria-label={`Zoom in ${TITLES[plane].toLowerCase()}`} title="Zoom in" onClick={() => command(plane, { type: 'zoom', factor: 1.2 })}><ZoomIn size={13} /></button>
              <button type="button" disabled={!ready} aria-label={`Fit ${TITLES[plane].toLowerCase()} image`} title="Fit image" onClick={() => command(plane, { type: 'fit' })}><Scan size={13} /></button>
              {activePlane === 'multiplanar' && <button type="button" aria-label={`${maximized === plane ? 'Restore' : 'Maximize'} ${TITLES[plane].toLowerCase()} plane`} title={maximized === plane ? 'Restore layout' : 'Maximize plane'} onClick={() => changeLayout({ maximizedPlane: maximized === plane ? null : plane })}>{maximized === plane ? <Minimize2 size={13} /> : <Maximize2 size={13} />}</button>}
              {activePlane === 'multiplanar' && !only && <button type="button" aria-label={`Hide ${TITLES[plane].toLowerCase()} plane`} title="Hide plane" onClick={() => changeLayout({ hiddenPlanes: [...hiddenPlanes, plane] })}><EyeOff size={13} /></button>}
            </div>
          </header>
          <div className="tb-pane__image">
            <NiivueViewer
              {...props}
              mode="2d"
              activePlane={plane}
              navigationCommand={commands[plane] || null}
              syncCrosshair={linked ? syncCrosshair : null}
              syncWindow={syncWindow}
              showPlaneLabels={false}
              onNavigationChange={snapshot => receiveNavigation(plane, snapshot)}
              onWindowChange={window => {
                if (window.sceneKey === sceneKey) setSyncWindow({ ...window, id: ++serial.current })
              }}
              label={`${label} · ${TITLES[plane]}`}
            />
          </div>
          <footer className="tb-pane__navigator">
            <button type="button" disabled={!ready || index === 0} aria-label={`Previous ${TITLES[plane].toLowerCase()} slice`} onClick={() => command(plane, { type: 'slice', plane, index: index - 1 })}><ChevronLeft size={14} /></button>
            <input type="range" aria-label={`${TITLES[plane]} slice`} min="0" max={Math.max(0, total - 1)} value={index} disabled={!ready} aria-valuetext={ready ? `Slice ${index + 1} of ${total}` : 'Loading scan'} onChange={event => command(plane, { type: 'slice', plane, index: Number(event.target.value) })} />
            <button type="button" disabled={!ready || index >= total - 1} aria-label={`Next ${TITLES[plane].toLowerCase()} slice`} onClick={() => command(plane, { type: 'slice', plane, index: index + 1 })}><ChevronRight size={14} /></button>
            <output>{ready ? `${index + 1} / ${total}` : '— / —'}</output>
          </footer>
        </section>
      })}
      {visible.length > 1 && <div className="tb-viewer__primary-divider" style={{ gridArea: 'primary' }}><PaneDivider orientation="vertical" label="Primary pane size" min={40} max={80} value={primaryShare} onChange={value => changeLayout({ primaryShare: value })} containerRef={containerRef} /></div>}
      {visible.length === 3 && <div className="tb-viewer__secondary-divider" style={{ gridArea: 'secondary' }}><PaneDivider orientation="horizontal" label="Secondary pane size" min={25} max={75} value={secondaryShare} onChange={value => changeLayout({ secondaryShare: value })} containerRef={containerRef} /></div>}
      {overlay && <div className="tb-viewer__overlay">{overlay}</div>}
    </div>
  </div>
}
