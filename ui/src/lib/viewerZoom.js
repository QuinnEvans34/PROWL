const clamp = (value, min, max) => Math.max(min, Math.min(max, value))
const validPoint = (point, dimensions) => point?.length >= dimensions
  && Array.from(point).slice(0, dimensions).every(Number.isFinite)

export function clientToBackingPx(canvas, clientX, clientY) {
  const rect = canvas?.getBoundingClientRect()
  if (!rect?.width || !rect.height || !canvas.width || !canvas.height
    || !Number.isFinite(clientX) || !Number.isFinite(clientY)) return null
  return [
    (clientX - rect.left) * canvas.width / rect.width,
    (clientY - rect.top) * canvas.height / rect.height,
  ]
}

function normalizedViewport(viewport) {
  if (!validPoint(viewport, 4) || !viewport[2] || viewport[3] <= 0) return null
  const [left, top, width, height] = viewport
  return [Math.min(left, left + width), top, Math.abs(width), height]
}

function withinViewport(point, viewport) {
  if (!validPoint(point, 2) || !viewport) return false
  const [left, top, width, height] = viewport
  return point[0] >= left && point[0] <= left + width && point[1] >= top && point[1] <= top + height
}

function viewportCenter(viewport) {
  if (!viewport) return null
  const [left, top, width, height] = viewport
  return [left + width / 2, top + height / 2]
}

export function zoomBoxBounds(start, end, viewport) {
  const bounds = normalizedViewport(viewport)
  if (!withinViewport(start, bounds) || !validPoint(end, 2)) return null
  const [left, top, width, height] = bounds
  const x = clamp(end[0], left, left + width)
  const y = clamp(end[1], top, top + height)
  const boxWidth = Math.abs(start[0] - x)
  const boxHeight = Math.abs(start[1] - y)
  if (boxWidth < 6 || boxHeight < 6) return null
  return {
    center: [(start[0] + x) / 2, (start[1] + y) / 2],
    viewCenter: viewportCenter(bounds),
    factor: Math.min(width / boxWidth, height / boxHeight),
  }
}

function tileAt(nv, point) {
  return nv.screenSlices?.findIndex(tile => tile.axCorSag >= 0 && tile.axCorSag <= 2
    && tile.sliceFrac !== Infinity && withinViewport(point, normalizedViewport(tile.leftTopWidthHeight))) ?? -1
}

function worldAt(nv, point, tileIndex) {
  if (tileIndex < 0 || !nv.screenXY2TextureFrac) return null
  // The visible plane can include margins outside the scan, especially when
  // panned. Its texture transform still maps those pixels into slice space.
  const fraction = nv.screenXY2TextureFrac(...point, tileIndex, false)
  if (!validPoint(fraction, 3) || Array.from(fraction).slice(0, 3).every(value => value === -1)) return null
  return nv.frac2mm(fraction)
}

function apply2dZoom(nv, factor, sourceWorld, targetWorld) {
  const pan = Array.from(nv.scene.pan2Dxyzmm || [0, 0, 0, 1])
  const previousZoom = pan[3]
  if (!validPoint(pan, 4) || previousZoom <= 0 || !Number.isFinite(factor) || factor <= 0
    || !validPoint(sourceWorld, 3) || !validPoint(targetWorld, 3)) return false
  const nextZoom = clamp(previousZoom * factor, 0.25, 12)
  // The renderer projects world coordinates after scaling and adding this
  // translation. Keep their full physical origin and the chosen anchor.
  const next = pan.slice()
  for (let axis = 0; axis < 3; axis += 1) {
    next[axis] += previousZoom * (targetWorld[axis] - sourceWorld[axis]) + (previousZoom - nextZoom) * sourceWorld[axis]
  }
  next[3] = nextZoom
  if (next.every((value, index) => value === pan[index])) return false
  nv.setPan2Dxyzmm(next)
  return true
}

export function zoom2d(nv, factor, anchorBackingPx = null) {
  const world = worldAt(nv, anchorBackingPx, tileAt(nv, anchorBackingPx))
    ?? nv.frac2mm(nv.scene.crosshairPos)
  return apply2dZoom(nv, factor, world, world)
}

export function zoomBox2d(nv, start, end) {
  const tileIndex = tileAt(nv, start)
  if (tileIndex < 0) return false
  const box = zoomBoxBounds(start, end, nv.screenSlices[tileIndex].leftTopWidthHeight)
  if (!box) return false
  return apply2dZoom(nv, box.factor, worldAt(nv, box.center, tileIndex), worldAt(nv, box.viewCenter, tileIndex))
}

export function zoomToBounds2d(nv, boundsWorldMm) {
  const tileIndex = nv.screenSlices?.findIndex(tile => tile.axCorSag >= 0 && tile.axCorSag <= 2 && tile.sliceFrac !== Infinity)
  const tile = nv.screenSlices?.[tileIndex]
  const viewport = normalizedViewport(tile?.leftTopWidthHeight)
  if (!viewport || !validPoint(tile.fovMM, 2) || !boundsWorldMm?.length) return false
  const target = worldAt(nv, viewportCenter(viewport), tileIndex)
  if (!validPoint(target, 3)) return false
  const points = boundsWorldMm.map(point => nv.frac2mm(nv.mm2frac(point, 0, true)))
  if (points.some(point => !validPoint(point, 3))) return false

  const source = Array.from(target).slice(0, 3)
  const axes = [[0, 1], [0, 2], [1, 2]][tile.axCorSag]
  const factor = Math.min(...axes.map((axis, index) => {
    const coordinates = points.map(point => point[axis])
    const min = Math.min(...coordinates)
    const max = Math.max(...coordinates)
    source[axis] = (min + max) / 2
    return 0.65 * Math.abs(tile.fovMM[index]) / (max - min)
  }))
  return apply2dZoom(nv, factor, source, target)
}

export function zoom3dFraming(previousScale, pivot, factor, viewport, viewPoint, anchor = null) {
  if (!Number.isFinite(previousScale) || previousScale <= 0 || !Number.isFinite(factor) || factor <= 0) return null
  const scale = clamp(previousScale * factor, 0.45, 4)
  const bounds = normalizedViewport(viewport)
  const nextPivot = validPoint(pivot, 3) ? Array.from(pivot).slice(0, 3) : null
  if (nextPivot && viewPoint && scale !== previousScale && withinViewport(anchor, bounds)) {
    const centerWorld = viewPoint(viewportCenter(bounds))
    const anchorWorld = viewPoint(anchor)
    if (validPoint(centerWorld, 3) && validPoint(anchorWorld, 3)) {
      const delta = 1 - previousScale / scale
      for (let axis = 0; axis < 3; axis += 1) nextPivot[axis] += (anchorWorld[axis] - centerWorld[axis]) * delta
    }
  }
  return { scale, pivot: nextPivot }
}

export function zoomBox3dFraming(previousScale, pivot, viewport, viewPoint, start, end) {
  const box = zoomBoxBounds(start, end, viewport)
  if (!box || !validPoint(pivot, 3) || !viewPoint) return null
  const centerWorld = viewPoint(box.viewCenter)
  const boxWorld = viewPoint(box.center)
  if (!validPoint(centerWorld, 3) || !validPoint(boxWorld, 3)) return null
  return zoom3dFraming(
    previousScale,
    Array.from(pivot).slice(0, 3).map((value, axis) => value + boxWorld[axis] - centerWorld[axis]),
    box.factor,
  )
}

export function pan3dPivot(pivot, viewPoint, previousPx, nextPx) {
  if (!validPoint(pivot, 3) || !validPoint(previousPx, 2) || !validPoint(nextPx, 2)
    || (previousPx[0] === nextPx[0] && previousPx[1] === nextPx[1])) return null

  const previousWorld = viewPoint(previousPx)
  const nextWorld = viewPoint(nextPx)
  if (!validPoint(previousWorld, 3) || !validPoint(nextWorld, 3)) return null
  // Unprojecting both positions at the same depth yields a translation in the
  // camera plane. Move its center opposite the drag so the scan follows it.
  return [0, 1, 2].map(axis => pivot[axis] + (previousWorld[axis] - nextWorld[axis]))
}
