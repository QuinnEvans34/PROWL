import React, { useEffect, useRef } from 'react'
import { viewerSceneKey } from '../../src/lib/viewerSceneKey.js'
export { viewerSceneKey } from '../../src/lib/viewerSceneKey.js'

// Fixed synthetic navigation only: no scans, geometry parsing or WebGL. A ref
// prevents inline parent callbacks from repeatedly emitting the same snapshot.
const navigation = {
  indices: { axial: 40, coronal: 30, sagittal: 60 },
  totals: { axial: 100, coronal: 80, sagittal: 120 },
  ranges: { pancreas: null, lesion: null },
  frac: [0.5, 0.375, 0.4],
}
export default function MockViewer(props) {
  const { mode, activePlane, visibleSources, resetToken, ctWindow, overlayOpacity, label, onNavigationChange, navigationCommand } = props
  const sceneKey = viewerSceneKey(props)
  const callback = useRef(onNavigationChange)
  const revealCallback = useRef(props.onPeelReveal)
  callback.current = onNavigationChange
  revealCallback.current = props.onPeelReveal
  useEffect(() => {
    let active = true
    // Match a real viewer's asynchronous load: the workspace establishes its
    // scene before the completed image reports its initial position.
    Promise.resolve().then(() => {
      if (active) callback.current?.({ ...navigation, sceneKey, origin: 'initial', fractions: navigation.frac })
    })
    return () => { active = false }
  }, [sceneKey, label, mode, activePlane])
  const peelReveal = props.caseData.syntheticPeelReveal
  useEffect(() => {
    if (mode === '3d' && peelReveal) revealCallback.current?.(peelReveal)
  }, [sceneKey, mode, peelReveal])
  return <div role="status" aria-label="Synthetic viewer stub" data-testid={`synthetic-viewer-${mode}-${activePlane}`}>
    SYNTHETIC UI FIXTURE — NO CT / NO WEBGL
    <pre>{JSON.stringify({ mode, activePlane, visibleSources, resetToken, ctWindow, overlayOpacity, navigationCommand,
      clip: props.clip, interactionMode: props.interactionMode,
      measurementCalipers: props.measurementCalipers, selectedLesionWorldMm: props.selectedLesionWorldMm,
      measurementAnatomy: props.measurementAnatomy,
      selectedObject: props.selectedObject })}</pre>
    {mode === '3d' && props.caseData.syntheticLesionPick && <button type="button"
      onClick={() => props.onSelectObject?.({ source: 'pred', anatomy: 'lesion', worldMm: props.caseData.syntheticLesionPick })}>
      Pick synthetic lesion surface
    </button>}
    {mode === '3d' && props.caseData.syntheticLesionPick && <button type="button"
      onClick={() => props.onSelectObject?.({ source: 'pred', anatomy: 'pancreas' })}>
      Pick surrounding synthetic tissue
    </button>}
    {mode === '3d' && props.caseData.syntheticLesionPick && <button type="button"
      onClick={() => props.onSelectObject?.(null)}>
      Pick empty space
    </button>}
  </div>
}
