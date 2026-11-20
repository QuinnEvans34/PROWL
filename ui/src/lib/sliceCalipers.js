export const column = (affine, j) => affine.slice(0, 3).map(row => row[j])
export const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0)
export const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
]

function parallelToAxis(vector, axis) {
  const tolerance = 1e-6 * Math.hypot(...vector)
  return vector.every((value, index) => index === axis || Math.abs(value) <= tolerance)
}

export function nativeSliceGeometry(affine) {
  const [iAxis, jAxis, kAxis] = [0, 1, 2].map(axis => column(affine, axis))
  const iMm = Math.hypot(...iAxis)
  const jMm = Math.hypot(...jAxis)
  const orthogonal = Math.abs(dot(iAxis, jAxis)) <= 1e-5 * iMm * jMm
  const normal = cross(iAxis, jAxis)
  // An in-plane rotation still matches an anatomical slice. A tilted normal
  // or a k axis with an in-plane component requires reslicing.
  const axis = normal.findIndex((_, i) => parallelToAxis(normal, i) && parallelToAxis(kAxis, i))
  return { iAxis, jAxis, kAxis, iMm, jMm, orthogonal,
    plane: orthogonal ? (['sagittal', 'coronal', 'axial'][axis] ?? null) : null }
}

export function voxelToWorld(affine, point) {
  return affine.slice(0, 3).map(row => row[3] + row[0] * point[0] + row[1] * point[1] + row[2] * point[2])
}

export function centeredSliceCalipers(labels, shape, affine, { iMm, jMm, plane }, anchor, contains) {
  const [nx, ny] = shape
  const center = [anchor % nx, Math.floor(anchor / nx) % ny, Math.floor(anchor / (nx * ny))]
  const axes = [1, nx].map((step, axis) => {
    let lo = center[axis]
    let hi = lo
    const start = anchor - lo * step
    while (lo > 0 && contains(labels[start + (lo - 1) * step])) lo--
    while (hi + 1 < shape[axis] && contains(labels[start + (hi + 1) * step])) hi++
    const ends = [lo - 0.5, hi + 0.5].map(edge => center.map((value, i) => i === axis ? edge : value))
    return { lengthMm: (hi - lo + 1) * (axis === 0 ? iMm : jMm),
      voxelEndpoints: ends, worldEndpointsMm: ends.map(point => voxelToWorld(affine, point)) }
  })
  return { nativeSlice: center[2], plane, anchorVoxel: center, anchorWorldMm: voxelToWorld(affine, center), axes }
}
