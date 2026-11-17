import { useId, useLayoutEffect, useState } from 'react'
import { projectCalipers, projectLesionMarker } from '../lib/viewerCaliperProjection.js'

function displayCm(lengthMm) {
  return lengthMm < 0.1 ? '<0.01 cm' : `${(lengthMm / 10).toFixed(2)} cm`
}

function Arm({ line, index, bounds }) {
  const [[x1, y1], [x2, y2]] = line.points
  const dx = x2 - x1
  const dy = y2 - y1
  const pixelLength = Math.hypot(dx, dy)
  if (pixelLength < 0.1) return null
  const tx = -dy / pixelLength * 4
  const ty = dx / pixelLength * 4
  const path = `M ${x1} ${y1} L ${x2} ${y2} M ${x1 - tx} ${y1 - ty} L ${x1 + tx} ${y1 + ty} M ${x2 - tx} ${y2 - ty} L ${x2 + tx} ${y2 + ty}`
  const horizontal = Math.abs(dx) >= Math.abs(dy)
  // Keep the value outside the caliper so the label leaves the CT texture and
  // the crossing itself readable, including when the lesion is small.
  const right = x1 > x2 ? [x1, y1] : [x2, y2]
  const left = x1 > x2 ? [x2, y2] : [x1, y1]
  const top = y1 < y2 ? [x1, y1] : [x2, y2]
  const bottom = y1 < y2 ? [x2, y2] : [x1, y1]
  const putRight = right[0] + 70 < bounds.x + bounds.width
  const putAbove = top[1] - 22 >= bounds.y
  const x = horizontal ? (putRight ? right[0] + 8 : left[0] - 8) : (putAbove ? top[0] : bottom[0])
  const y = horizontal ? (putRight ? right[1] : left[1]) + 4 : (putAbove ? top[1] - 7 : bottom[1] + 16)
  return <g>
    <path d={path} fill="none" stroke="#191208" strokeWidth="4" />
    <path d={path} fill="none" stroke="#ffcf8e" strokeWidth="1.7" data-caliper-arm={index} />
    <text x={x} y={y} textAnchor={horizontal ? (putRight ? 'start' : 'end') : 'middle'} fill="#ffdfb5" stroke="#191208"
      paintOrder="stroke" strokeWidth="4" strokeLinejoin="round" fontSize="12" fontWeight="600">
      {displayCm(line.lengthMm)}
    </text>
  </g>
}

/**
 * NiiVue updates tile transforms during its draw (including mouse pan/zoom and
 * resize). Read those transforms after the draw instead of reconstructing the
 * camera from controls, which would lag behind interaction.
 */
export default function ViewerMeasurementOverlay({ nvRef, loadedSceneKeyRef, sceneKey, ready, mode,
  calipers, marker }) {
  const clip = useId()
  const input = mode === '2d' ? calipers : marker
  const [frame, setFrame] = useState(null)
  useLayoutEffect(() => {
    const nv = nvRef.current
    if (!ready || !input || !nv) return undefined
    let last = null
    function refresh() {
      if (nvRef.current !== nv || loadedSceneKeyRef.current !== sceneKey) return
      const projection = mode === '2d' ? projectCalipers(nv, input) : projectLesionMarker(nv, input)
      const signature = JSON.stringify(projection)
      if (signature === last) return
      last = signature
      setFrame({ input, sceneKey, projection })
    }
    const original = nv.drawScene
    function drawWithMeasurement(...args) {
      const result = original.apply(this, args)
      refresh()
      return result
    }
    nv.drawScene = drawWithMeasurement
    refresh()
    return () => { if (nv.drawScene === drawWithMeasurement) nv.drawScene = original }
  }, [input, loadedSceneKeyRef, mode, nvRef, ready, sceneKey])

  const projection = ready && frame?.input === input && frame.sceneKey === sceneKey ? frame.projection : null
  if (!projection) return null
  const style = { position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }
  if (mode === '3d') return <svg style={style} role="img" aria-label="Selected predicted lesion marker">
    <circle cx={projection.x} cy={projection.y} r="8" fill="none" stroke="#191208" strokeWidth="4" />
    <circle cx={projection.x} cy={projection.y} r="8" fill="none" stroke="#ffcf8e" strokeWidth="2" />
    <circle cx={projection.x} cy={projection.y} r="2" fill="#ffdfb5" />
  </svg>

  return <svg style={style} role="img" aria-label={`Lesion calipers: ${projection.lines.map(line => displayCm(line.lengthMm)).join(' by ')}`}>
    <defs><clipPath id={clip}><rect {...projection.bounds} /></clipPath></defs>
    <g clipPath={`url(#${clip})`}>
      {projection.lines.map((line, index) => <Arm key={index} line={line} index={index} bounds={projection.bounds} />)}
    </g>
  </svg>
}
