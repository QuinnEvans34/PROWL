import { centeredSliceCalipers, nativeSliceGeometry, voxelToWorld } from './sliceCalipers.js'

export const PANCREAS_DIMENSIONS_POLICY = 'native-centered-pancreas-slice-calipers-v1'
const isPancreasOutline = label => label === 1 || label === 2

// Measure the same label union as the pancreas volume, on the verified native grid.
export function pancreasDimensions(labels, { shape, affine }) {
  const [nx, ny, nz] = shape
  const sliceSize = nx * ny
  let widestSlice = null
  let bottom = Infinity
  let top = -Infinity
  const heightRow = affine[2]

  for (let z = 0; z < nz; z++) {
    const start = z * sliceSize
    let count = 0
    let sumX = 0
    let sumY = 0
    for (let offset = 0; offset < sliceSize; offset++) {
      if (!isPancreasOutline(labels[start + offset])) continue
      const x = offset % nx
      const y = Math.floor(offset / nx)
      count++
      sumX += x
      sumY += y
      const height = heightRow[0] * x + heightRow[1] * y + heightRow[2] * z
      bottom = Math.min(bottom, height)
      top = Math.max(top, height)
    }
    // Pixel area is constant across the native grid. Keep the first slice
    // among ties, so the inspection target is deterministic.
    if (count && (!widestSlice || count > widestSlice.count)) {
      widestSlice = { z, count, centerX: sumX / count, centerY: sumY / count }
    }
  }

  const policy = PANCREAS_DIMENSIONS_POLICY
  if (!widestSlice) return { policy, status: 'unavailable', reason: 'A usable pancreas outline is not available.',
    calipers: null, focusWorldMm: null, superiorInferiorMm: null }

  const geometry = nativeSliceGeometry(affine)
  const { iMm, jMm, orthogonal, plane } = geometry
  const { z, centerX, centerY } = widestSlice
  const start = z * sliceSize
  let anchor = -1
  let nearest = Infinity
  for (let offset = 0; offset < sliceSize; offset++) {
    if (!isPancreasOutline(labels[start + offset])) continue
    const distance = ((offset % nx - centerX) * iMm) ** 2
      + ((Math.floor(offset / nx) - centerY) * jMm) ** 2
    if (anchor === -1 || distance < nearest) {
      anchor = start + offset
      nearest = distance
    }
  }

  const calipers = orthogonal ? centeredSliceCalipers(labels, shape, affine, geometry, anchor, isPancreasOutline) : null
  const focusWorldMm = calipers?.anchorWorldMm ?? voxelToWorld(affine, [anchor % nx, Math.floor(anchor / nx) % ny, z])
  const voxelHeight = heightRow.slice(0, 3).reduce((sum, value) => sum + Math.abs(value), 0)
  const caliperUnavailableReason = !orthogonal ? 'The native slice axes are not perpendicular.'
    : !plane ? 'The native slice does not align with a viewer plane.' : undefined
  return { policy, status: 'ready', calipers, focusWorldMm, superiorInferiorMm: top - bottom + voxelHeight, caliperUnavailableReason }
}
