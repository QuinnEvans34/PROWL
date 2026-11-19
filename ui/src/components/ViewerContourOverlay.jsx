import { useId, useLayoutEffect, useState } from 'react'
import { projectPredictedContours } from '../lib/viewerContour.js'
import { observeViewerDraw } from '../lib/viewerDraw.js'

export default function ViewerContourOverlay({ nvRef, loadedSceneKeyRef, sceneKey, ready, mask, plane,
  showLesion, showPancreas, opacity = 1 }) {
  const clip = useId()
  const [frame, setFrame] = useState(null)
  useLayoutEffect(() => {
    const nv = nvRef.current
    if (!ready || !nv || !mask) return undefined
    let previous
    function refresh() {
      if (nvRef.current !== nv || loadedSceneKeyRef.current !== sceneKey) return
      const projection = projectPredictedContours(nv, mask, plane)
      const signature = JSON.stringify([projection?.transform, projection?.bounds])
      if (previous?.signature === signature && previous.paths === projection?.paths) return
      previous = { signature, paths: projection?.paths }
      setFrame({ projection, sceneKey, mask, plane })
    }
    const detach = observeViewerDraw(nv, refresh)
    refresh()
    return detach
  }, [nvRef, loadedSceneKeyRef, sceneKey, ready, mask, plane])

  const projection = ready && frame?.sceneKey === sceneKey && frame.mask === mask && frame.plane === plane ? frame.projection : null
  if (!projection || !(showLesion && projection.paths.lesion || showPancreas && projection.paths.pancreas)) return null
  return <svg role="img" aria-label="Predicted contours"
    style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
    <defs><clipPath id={clip}><rect {...projection.bounds} /></clipPath></defs>
    <g clipPath={`url(#${clip})`}>
      <g transform={projection.transform} fill="none" strokeWidth="1.5" opacity={opacity}>
        {showPancreas && projection.paths.pancreas && <path d={projection.paths.pancreas} stroke="#26c5a6" vectorEffect="non-scaling-stroke" />}
        {showLesion && projection.paths.lesion && <path d={projection.paths.lesion} stroke="#f96363" vectorEffect="non-scaling-stroke" />}
      </g>
    </g>
  </svg>
}
