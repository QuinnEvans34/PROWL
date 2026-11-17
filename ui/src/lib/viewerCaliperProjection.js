const PLANES = {
  axial: { sliceType: 0, axes: [0, 1, 2] },
  coronal: { sliceType: 1, axes: [0, 2, 1] },
  sagittal: { sliceType: 2, axes: [1, 2, 0] },
}

const validPoint = p => p?.length >= 3 && Number.isFinite(p[0]) && Number.isFinite(p[1]) && Number.isFinite(p[2])

function pixels(nv) {
  // screenSlices describe the drawing buffer; the SVG overlays the CSS canvas.
  const canvas = nv.canvas
  if (!canvas?.width || !canvas.height || !canvas.clientWidth || !canvas.clientHeight) return null
  return [canvas.clientWidth / canvas.width, canvas.clientHeight / canvas.height]
}

export function projectCalipers(nv, calipers) {
  const plane = PLANES[calipers?.plane]
  const scale = pixels(nv)
  if (!plane || !scale || !validPoint(calipers.anchorWorldMm) || calipers.axes?.length !== 2) return null

  const [xAxis, yAxis, depth] = plane.axes
  const volume = nv.volumes?.[0]
  const voxelCount = (volume?.dimsRAS || volume?.hdr?.dims)?.[depth + 1]
  if (!Number.isFinite(voxelCount) || voxelCount < 1) return null
  const anchor = nv.mm2frac(calipers.anchorWorldMm, 0, true)
  if (!validPoint(anchor) || anchor[depth] < 0 || anchor[depth] > 1) return null

  // A different slice can be within the library's permissive projection
  // tolerance. Require the actual rendered slice position to agree to 0.02 voxel.
  const coplanar = value => Math.abs(value - anchor[depth]) * voxelCount <= 0.02
  const tile = nv.screenSlices?.find(slice => slice.axCorSag === plane.sliceType && coplanar(slice.sliceFrac))
  if (!tile) return null
  const [left, top, width, height] = tile.leftTopWidthHeight || []
  const [x0, y0] = tile.leftTopMM || []
  const [fovX, fovY] = tile.fovMM || []
  if (![left, top, width, height, x0, y0, fovX, fovY].every(Number.isFinite)
    || width === 0 || height <= 0 || fovX === 0 || fovY === 0) return null

  const lines = []
  for (const axis of calipers.axes) {
    if (!Number.isFinite(axis.lengthMm) || axis.lengthMm <= 0 || axis.worldEndpointsMm?.length !== 2) return null
    const projected = []
    for (const world of axis.worldEndpointsMm) {
      if (!validPoint(world)) return null
      const fraction = nv.mm2frac(world, 0, true)
      if (!validPoint(fraction) || !coplanar(fraction[depth])) return null
      // The renderer may display orthogonal voxel millimeters rather than
      // native world millimeters. The fraction bridges the two coordinate spaces.
      const mm = nv.frac2mm(fraction)
      if (!validPoint(mm)) return null
      projected.push([
        (left + width * ((mm[xAxis] - x0) / fovX)) * scale[0],
        (top + height * (1 - (mm[yAxis] - y0) / fovY)) * scale[1],
      ])
    }
    lines.push({ points: projected, lengthMm: axis.lengthMm })
  }
  return { lines, bounds: { x: Math.min(left, left + width) * scale[0], y: top * scale[1],
    width: Math.abs(width) * scale[0], height: height * scale[1] } }
}

export function projectLesionMarker(nv, world) {
  const scale = pixels(nv)
  const tile = nv.screenSlices?.find(slice => slice.axCorSag === 4)
  if (!scale || !tile || !validPoint(world) || typeof nv.calculateMvpMatrix !== 'function') return null
  const [left, top, width, height] = tile.leftTopWidthHeight
  if (![left, top, width, height].every(Number.isFinite) || width <= 0 || height <= 0) return null
  const [matrix] = nv.calculateMvpMatrix(null, tile.leftTopWidthHeight, nv.scene.renderAzimuth, nv.scene.renderElevation)
  if (!matrix || matrix.length !== 16) return null
  const clip = Array.from({ length: 4 }, (_, n) => world[0] * matrix[n] + world[1] * matrix[n + 4] + world[2] * matrix[n + 8] + matrix[n + 12])
  if (!clip.every(Number.isFinite) || clip[3] <= 0) return null
  const ndc = clip.slice(0, 3).map(v => v / clip[3])
  if (ndc.some(v => Math.abs(v) > 1)) return null
  return { x: (left + width * (1 + ndc[0]) / 2) * scale[0], y: (top + height * (1 - ndc[1]) / 2) * scale[1] }
}
