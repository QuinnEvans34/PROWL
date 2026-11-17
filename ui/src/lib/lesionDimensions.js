const MAX_LABEL_VOXELS = 250_000
const MAX_COMPONENTS = 512
export const LESION_DIMENSIONS_POLICY = 'native-centered-slice-calipers-v1'

// Called only after measureMask has validated the matched grids, units, labels
// and coverage. Native voxel coordinates refer to voxel centers.
export function lesionDimensions(labels, { shape: [nx, ny, nz], affine, lesionVoxels, voxelMm3 }) {
  const record = (status, components, reason) => ({ policy: LESION_DIMENSIONS_POLICY, status, components, reason })
  if (!lesionVoxels) return record('ready', [])
  if (lesionVoxels > MAX_LABEL_VOXELS) return record('unavailable', [], 'Too many lesion voxels to measure components in this viewer.')

  const xy = nx * ny
  const queue = new Uint32Array(lesionVoxels)
  const visited = new Uint8Array(Math.ceil(labels.length / 8))
  const visit = (index, tail) => {
    const bit = 1 << (index % 8)
    if (labels[index] !== 2 || (visited[index >> 3] & bit)) return tail
    visited[index >> 3] |= bit
    queue[tail] = index
    return tail + 1
  }
  const world = point => affine.slice(0, 3).map(row => row[3] + row[0] * point[0] + row[1] * point[1] + row[2] * point[2])
  const iAxis = affine.slice(0, 3).map(row => row[0])
  const jAxis = affine.slice(0, 3).map(row => row[1])
  const iMm = Math.hypot(...iAxis)
  const jMm = Math.hypot(...jAxis)
  const orthogonal = Math.abs(iAxis.reduce((dot, value, n) => dot + value * jAxis[n], 0)) <= 1e-5 * iMm * jMm
  const voxelHeight = affine[2].slice(0, 3).reduce((sum, v) => sum + Math.abs(v), 0)
  const components = []
  let measuredVoxels = 0
  for (let seed = 0; seed < labels.length && measuredVoxels < lesionVoxels; seed++) {
    let size = visit(seed, 0)
    if (!size) continue
    if (components.length >= MAX_COMPONENTS) return record('unavailable', [], 'Too many separate lesion regions to measure in this viewer.')
    const slices = new Map()
    let bottom = Infinity
    let top = -Infinity
    for (let head = 0; head < size; head++) {
      const index = queue[head]
      const x = index % nx
      const y = Math.floor(index / nx) % ny
      const z = Math.floor(index / xy)
      if (x > 0) size = visit(index - 1, size)
      if (x + 1 < nx) size = visit(index + 1, size)
      if (y > 0) size = visit(index - nx, size)
      if (y + 1 < ny) size = visit(index + nx, size)
      if (z > 0) size = visit(index - xy, size)
      if (z + 1 < nz) size = visit(index + xy, size)
      const row = affine[2]
      const height = row[0] * x + row[1] * y + row[2] * z
      bottom = Math.min(bottom, height)
      top = Math.max(top, height)
      const stats = slices.get(z) || { count: 0, x: 0, y: 0 }
      stats.count++; stats.x += x; stats.y += y
      slices.set(z, stats)
    }
    measuredVoxels += size
    let calipers = null
    if (orthogonal) {
      let k = null
      let largest = null
      for (const [z, stats] of slices) {
        if (!largest || stats.count > largest.count || (stats.count === largest.count && z < k)) {
          largest = stats; k = z
        }
      }
      let anchor = 0
      let closest = Infinity
      for (let n = 0; n < size; n++) {
        const index = queue[n]
        if (Math.floor(index / xy) !== k) continue
        const distance = ((index % nx - largest.x / largest.count) * iMm) ** 2
          + ((Math.floor(index / nx) % ny - largest.y / largest.count) * jMm) ** 2
        if (distance < closest || (distance === closest && index < anchor)) {
          closest = distance; anchor = index
        }
      }
      const center = [anchor % nx, Math.floor(anchor / nx) % ny, k]
      const axes = [1, nx].map((step, axis) => {
        let lo = center[axis]
        let hi = lo
        const start = anchor - lo * step
        while (lo > 0 && labels[start + (lo - 1) * step] === 2) lo--
        while (hi + 1 < shapeSize(axis) && labels[start + (hi + 1) * step] === 2) hi++
        const ends = [lo - 0.5, hi + 0.5].map(edge => center.map((v, i) => i === axis ? edge : v))
        return { lengthMm: (hi - lo + 1) * (axis === 0 ? iMm : jMm), voxelEndpoints: ends, worldEndpointsMm: ends.map(world) }
      })
      calipers = { nativeSlice: k, anchorVoxel: center, anchorWorldMm: world(center), axes }
    }
    components.push({ id: seed, voxelCount: size, volumeMl: size * voxelMm3 / 1000,
      superiorInferiorMm: top - bottom + voxelHeight, calipers,
      caliperUnavailableReason: orthogonal ? undefined : 'The native slice axes are not perpendicular.' })
  }
  function shapeSize(axis) { return axis === 0 ? nx : ny }
  components.sort((a, b) => b.voxelCount - a.voxelCount || a.id - b.id)
  return record('ready', components)
}
