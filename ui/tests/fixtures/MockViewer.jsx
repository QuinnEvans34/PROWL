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
  callback.current = onNavigationChange
  useEffect(() => {
    let active = true
    // Match a real viewer's asynchronous load: the workspace establishes its
    // scene before the completed image reports its initial position.
    Promise.resolve().then(() => {
      if (active) callback.current?.({ ...navigation, sceneKey, origin: 'initial', fractions: navigation.frac })
    })
    return () => { active = false }
  }, [sceneKey, label, mode, activePlane])
  return <div role="status" aria-label="Synthetic viewer stub" data-testid={`synthetic-viewer-${mode}-${activePlane}`}>
    SYNTHETIC UI FIXTURE — NO CT / NO WEBGL
    <pre>{JSON.stringify({ mode, activePlane, visibleSources, resetToken, ctWindow, overlayOpacity, navigationCommand })}</pre>
  </div>
}
