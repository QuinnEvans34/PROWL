const FACE_LIMIT = 180_000
const faces = [
  [[-.5, -.5, -.5], [-.5, -.5, .5], [-.5, .5, .5], [-.5, .5, -.5]],
  [[.5, -.5, -.5], [.5, .5, -.5], [.5, .5, .5], [.5, -.5, .5]],
  [[-.5, -.5, -.5], [.5, -.5, -.5], [.5, -.5, .5], [-.5, -.5, .5]],
  [[-.5, .5, -.5], [-.5, .5, .5], [.5, .5, .5], [.5, .5, -.5]],
  [[-.5, -.5, -.5], [-.5, .5, -.5], [.5, .5, -.5], [.5, -.5, -.5]],
  [[-.5, -.5, .5], [.5, -.5, .5], [.5, .5, .5], [-.5, .5, .5]],
]

function handedness(affine) {
  const [[a, b, c], [d, e, f], [g, h, i]] = affine
  return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
}

function writeStl(exposed, shape, affine, sign) {
  const [nx, ny] = shape
  const sliceSize = nx * ny
  const binary = new ArrayBuffer(84 + 100 * exposed.length)
  const view = new DataView(binary)
  view.setUint32(80, 2 * exposed.length, true)
  const order = sign > 0 ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2]
  let triangle = 84
  for (const item of exposed) {
    const index = Math.floor(item / 6)
    const x = index % nx
    const y = Math.floor(index / nx) % ny
    const z = Math.floor(index / sliceSize)
    const corners = faces[item % 6]
    for (let vertex = 0; vertex < order.length; vertex++) {
      const [dx, dy, dz] = corners[order[vertex]]
      const offset = triangle + 12 + (vertex % 3) * 12
      for (let axis = 0; axis < 3; axis++) {
        const [a, b, c, t] = affine[axis]
        view.setFloat32(offset + axis * 4, a * (x + dx) + b * (y + dy) + c * (z + dz) + t, true)
      }
      if (vertex % 3 === 2) triangle += 50
    }
  }
  // The NiiVue STL reader derives normals from the outward-wound triangles.
  return binary
}

export function buildPredictionSurfaces(labels, { shape, affine }, maxFaces = FACE_LIMIT) {
  const [nx, ny, nz] = shape
  const sliceSize = nx * ny
  const sign = handedness(affine)
  if (nx * ny * nz !== labels.length || !Number.isFinite(sign) || sign === 0)
    throw new Error('The prediction surface geometry is invalid.')

  const pancreas = []
  const lesion = []
  for (let index = 0; index < labels.length; index++) {
    const label = labels[index]
    if (label === 0) continue
    const x = index % nx
    const y = Math.floor(index / nx) % ny
    const z = Math.floor(index / sliceSize)
    // A neighbor outside the image is background. This closes the displayed
    // voxel surface without supplying any size or coverage claims.
    const neighbors = [
      x > 0 ? labels[index - 1] : 0, x < nx - 1 ? labels[index + 1] : 0,
      y > 0 ? labels[index - nx] : 0, y < ny - 1 ? labels[index + nx] : 0,
      z > 0 ? labels[index - sliceSize] : 0, z < nz - 1 ? labels[index + sliceSize] : 0,
    ]
    for (let side = 0; side < 6; side++) {
      const face = index * 6 + side
      if (neighbors[side] === 0) pancreas.push(face)
      if (label === 2 && neighbors[side] !== 2) lesion.push(face)
    }
    if (pancreas.length + lesion.length > maxFaces)
      throw new Error('The prediction is too detailed to display as a 3D surface on this workstation.')
  }
  return Object.fromEntries([['pancreas_pred', pancreas], ['lesion_pred', lesion]]
    .filter(([, exposed]) => exposed.length)
    .map(([anatomy, exposed]) => [anatomy, writeStl(exposed, shape, affine, sign)]))
}
