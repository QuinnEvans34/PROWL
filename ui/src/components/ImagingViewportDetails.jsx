import { useLayoutEffect, useState } from 'react'
import { observeViewerDraw } from '../lib/viewerDraw.js'
import { viewportImageDetails } from '../lib/viewerImageDetails.js'
import '../styles/viewer-image-details.css'

const format = value => Number(value.toFixed(2)).toString()

export default function ImagingViewportDetails({ nvRef, loadedSceneKeyRef, sceneKey, ready, plane, source }) {
  const [frame, setFrame] = useState(null)

  useLayoutEffect(() => {
    const nv = nvRef.current
    if (!ready || !source || !nv) return undefined
    let previous
    function refresh() {
      if (nvRef.current !== nv || loadedSceneKeyRef.current !== sceneKey) return
      const details = viewportImageDetails(nv, plane, source)
      const signature = JSON.stringify(details)
      if (signature === previous) return
      previous = signature
      setFrame({ sceneKey, source, details })
    }
    const detach = observeViewerDraw(nv, refresh)
    refresh()
    return detach
  }, [nvRef, loadedSceneKeyRef, sceneKey, ready, plane, source])

  const details = ready && frame?.sceneKey === sceneKey && frame.source === source ? frame.details : null
  if (!details) return null
  const { kind, series, spacing, scale, windowHu } = details
  return <>
    <div className="pw-viewport-detail" role="group" aria-label="CT image details">
      <strong>{kind === 'source' ? 'Source CT' : 'Prepared CT'}</strong>
      {series && <span>{series}</span>}
      {spacing && <span>{spacing.map(format).join(' × ')} mm voxels</span>}
      {windowHu && <span>W {format(windowHu.width)} · L {format(windowHu.center)} HU</span>}
    </div>
    {scale && <div className="pw-viewport-scale" role="img" aria-label={`Physical scale ${format(scale.millimeters)} millimeters`}>
      <span className="pw-viewport-scale__ruler" aria-hidden="true" style={{ width: scale.widthPx }} />
      <span>{format(scale.millimeters)} mm</span>
    </div>}
  </>
}
