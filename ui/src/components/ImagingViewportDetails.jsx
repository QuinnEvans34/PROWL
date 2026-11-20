import { useLayoutEffect, useState } from 'react'
import { observeViewerDraw } from '../lib/viewerDraw.js'
import { viewportImageDetails } from '../lib/viewerImageDetails.js'
import '../styles/viewer-image-details.css'

const format = value => Number(value.toFixed(2)).toString()

export default function ImagingViewportDetails({ nvRef, loadedSceneKeyRef, sceneKey, ready, plane, source, sceneLabel = null }) {
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
    const detach = !sceneLabel || source.calibratedHu ? observeViewerDraw(nv, refresh) : undefined
    refresh()
    return detach
  }, [nvRef, loadedSceneKeyRef, sceneKey, ready, plane, source, sceneLabel])

  const details = ready && frame?.sceneKey === sceneKey && frame.source === source ? frame.details : null
  const { series, spacing, windowHu } = details ?? {}
  const spacingLabel = spacing && `${spacing.map(format).join(' × ')} mm voxels`
  const windowLabel = windowHu && `W ${format(windowHu.width)} · L ${format(windowHu.center)} HU`
  if (sceneLabel) return <div className="pw-split__label" title="The 3D camera moves independently of the 2D crosshair">
    {sceneLabel}
    {spacingLabel && <small>{spacingLabel}</small>}
    {series && <small>{series}</small>}
    {windowLabel && <small>{windowLabel}</small>}
  </div>
  if (!details) return null
  const { kind, scale } = details
  return <>
    <div className="pw-viewport-detail" role="group" aria-label="CT image details">
      <strong>{kind === 'source' ? 'Source CT' : 'Prepared CT'}</strong>
      {series && <span>{series}</span>}
      {spacingLabel && <span>{spacingLabel}</span>}
      {windowLabel && <span>{windowLabel}</span>}
    </div>
    {scale && <div className="pw-viewport-scale" role="img" aria-label={`Physical scale ${format(scale.millimeters)} millimeters`}>
      <span className="pw-viewport-scale__ruler" aria-hidden="true" style={{ width: scale.widthPx }} />
      <span>{format(scale.millimeters)} mm</span>
    </div>}
  </>
}
