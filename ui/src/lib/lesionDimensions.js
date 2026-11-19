const MAX_LABEL_VOXELS = 250_000
const MAX_COMPONENTS = 512
export const LESION_DIMENSIONS_POLICY = 'native-centered-slice-calipers-v1'

// Keep the sparse picking index out of serializable measurement/review data.
// It expires with the exact verified dimensions record and retains no mask.
const componentIndexes = new WeakMap()
const column = (affine, j) => affine.slice(0, 3).map(row => row[j])
const dot = (a, b) => a.reduce((sum, value, i) => sum + value * b[i], 0)
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
]

function parallelToAxis(vector, axis) {
  const tolerance = 1e-6 * Math.hypot(...vector)
  return vector.every((value, index) => index === axis || Math.abs(value) <= tolerance)
}

function anatomicalPlane(i, j, k) {
  const normal = cross(i, j)
  // In-plane rotation and signed permutations are fine. A tilted normal or
  // a k axis with an in-plane component requires unsupported reslicing.
  const axis = normal.findIndex((_, i) => parallelToAxis(normal, i) && parallelToAxis(k, i))
  return ['sagittal', 'coronal', 'axial'][axis] ?? null
}

function slotAt(packed, voxelIndex) {
  const target = voxelIndex * MAX_COMPONENTS
  let lo = 0
  let hi = packed.length
  while (lo < hi) {
    const middle = (lo + hi) >> 1
    if (packed[middle] < target) lo = middle + 1
    else hi = middle
  }
  return packed[lo] < target + MAX_COMPONENTS ? packed[lo] - target : -1
}

// A mesh hit may lie exactly on a voxel face, edge or corner. Accept it only
// if it touches occupied voxels from one component; never snap to a nearby
// component from background or choose between two ambiguous components.
function touchingVoxels(coordinate, extent) {
  const centered = coordinate + 0.5
  const nearestFace = Math.round(centered)
  const candidates = Math.abs(centered - nearestFace) <= 1e-6
    ? [nearestFace - 1, nearestFace] : [Math.floor(centered)]
  return candidates.filter(index => index >= 0 && index < extent)
}

export function lesionComponentAtWorld(measurement, worldMm) {
  const index = componentIndexes.get(measurement?.lesionDimensions)
  if (!index || worldMm?.length !== 3 || !Array.from(worldMm).every(Number.isFinite)) return null
  const { packed, slots, inverse, origin, shape } = index
  const relative = origin.map((offset, axis) => worldMm[axis] - offset)
  const [xs, ys, zs] = inverse.map((row, axis) => touchingVoxels(dot(row, relative), shape[axis]))
  let slot = -1
  for (const z of zs) for (const y of ys) for (const x of xs) {
    const hit = slotAt(packed, x + shape[0] * (y + shape[1] * z))
    if (hit < 0) continue
    if (slot >= 0 && slot !== hit) return null
    slot = hit
  }
  return slots[slot] ?? null
}

// Called only after measureMask has validated the matched grids, units, labels
// and coverage. Native voxel coordinates refer to voxel centers.
export function lesionDimensions(labels, { shape: [nx, ny, nz], affine, lesionVoxels, voxelMm3 }) {
  const record = (status, components, reason) => ({ policy: LESION_DIMENSIONS_POLICY, status, components, reason })
  if (!lesionVoxels) return record('ready', [])
  if (lesionVoxels > MAX_LABEL_VOXELS) return record('unavailable', [], 'Too many lesion voxels to measure components in this viewer.')

  const xy = nx * ny
  const queue = new Uint32Array(lesionVoxels)
  const visited = new Uint8Array(Math.ceil(labels.length / 8))
  // Exact cell ownership uses <= 2 MB, bounded by occupied voxels. Pack the
  // linear voxel index and component slot into an exactly representable integer.
  const packed = new Float64Array(lesionVoxels)
  const visit = (index, tail) => {
    const bit = 1 << (index % 8)
    if (labels[index] !== 2 || (visited[index >> 3] & bit)) return tail
    visited[index >> 3] |= bit
    queue[tail] = index
    return tail + 1
  }
  const world = point => affine.slice(0, 3).map(row => row[3] + row[0] * point[0] + row[1] * point[1] + row[2] * point[2])
  const [iAxis, jAxis, kAxis] = [0, 1, 2].map(axis => column(affine, axis))
  const iMm = Math.hypot(...iAxis)
  const jMm = Math.hypot(...jAxis)
  const orthogonal = Math.abs(dot(iAxis, jAxis)) <= 1e-5 * iMm * jMm
  const plane = orthogonal ? anatomicalPlane(iAxis, jAxis, kAxis) : null
  const voxelHeight = affine[2].slice(0, 3).reduce((sum, v) => sum + Math.abs(v), 0)
  const components = []
  let measuredVoxels = 0
  for (let seed = 0; seed < labels.length && measuredVoxels < lesionVoxels; seed++) {
    let size = visit(seed, 0)
    if (!size) continue
    if (components.length >= MAX_COMPONENTS) return record('unavailable', [], 'Too many separate lesion regions to measure in this viewer.')
    const slices = new Map()
    const lo = [nx, ny, nz]
    const hi = [-1, -1, -1]
    let bottom = Infinity
    let top = -Infinity
    for (let head = 0; head < size; head++) {
      const index = queue[head]
      packed[measuredVoxels + head] = index * MAX_COMPONENTS + components.length
      const x = index % nx
      const y = Math.floor(index / nx) % ny
      const z = Math.floor(index / xy)
      lo[0] = Math.min(lo[0], x)
      lo[1] = Math.min(lo[1], y)
      lo[2] = Math.min(lo[2], z)
      hi[0] = Math.max(hi[0], x)
      hi[1] = Math.max(hi[1], y)
      hi[2] = Math.max(hi[2], z)
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
      calipers = { nativeSlice: k, plane, anchorVoxel: center, anchorWorldMm: world(center), axes }
    }
    // Camera framing uses the outer voxel edges in the original affine.
    const boundsWorldMm = []
    for (const z of [lo[2] - 0.5, hi[2] + 0.5]) {
      for (const y of [lo[1] - 0.5, hi[1] + 0.5]) {
        for (const x of [lo[0] - 0.5, hi[0] + 0.5]) {
          boundsWorldMm.push(world([x, y, z]))
        }
      }
    }
    components.push({ id: seed, voxelCount: size, volumeMl: size * voxelMm3 / 1000,
      superiorInferiorMm: top - bottom + voxelHeight, calipers, boundsWorldMm,
      focusWorldMm: calipers?.anchorWorldMm ?? world([seed % nx, Math.floor(seed / nx) % ny, Math.floor(seed / xy)]),
      caliperUnavailableReason: orthogonal ? undefined : 'The native slice axes are not perpendicular.' })
  }
  function shapeSize(axis) { return axis === 0 ? nx : ny }
  const dimensions = record('ready', [...components].sort((a, b) => b.voxelCount - a.voxelCount || a.id - b.id))
  const cofactors = [cross(jAxis, kAxis), cross(kAxis, iAxis), cross(iAxis, jAxis)]
  const determinant = dot(iAxis, cofactors[0])
  componentIndexes.set(dimensions, {
    packed: packed.sort(), slots: components, shape: [nx, ny, nz],
    inverse: cofactors.map(row => row.map(n => n / determinant)), origin: column(affine, 3),
  })
  return dimensions
}
