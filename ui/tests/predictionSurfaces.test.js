import { expect, it } from 'vitest'
import { buildPredictionSurfaces } from '../src/lib/predictionSurfaces.js'
import { viewerSceneKey } from '../src/lib/viewerSceneKey.js'

const identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

function triangles(binary) {
  const view = new DataView(binary)
  return Array.from({ length: view.getUint32(80, true) }, (_, n) =>
    [0, 1, 2].map(vertex => [0, 1, 2].map(axis => view.getFloat32(96 + n * 50 + vertex * 12 + axis * 4, true))))
}

it('builds the combined pancreas shell and distinct lesion without internal faces', () => {
  const surfaces = buildPredictionSurfaces(Uint8Array.of(1, 2), { shape: [2, 1, 1], affine: identity })
  expect(triangles(surfaces.pancreas_pred)).toHaveLength(20)
  expect(triangles(surfaces.lesion_pred)).toHaveLength(12)
  expect(Math.min(...triangles(surfaces.lesion_pred).flat().map(point => point[0]))).toBe(0.5)
})

it('places all vertices in affine world coordinates with outward faces on a reflected scan', () => {
  const affine = [[-2, 0, 0, 10], [0, 0, 3, 20], [0, -4, 0, 30], identity[3]]
  const triangles3d = triangles(buildPredictionSurfaces(Uint8Array.of(1), { shape: [1, 1, 1], affine }).pancreas_pred)
  const coordinates = triangles3d.flat()
  expect([0, 1, 2].map(axis => Math.min(...coordinates.map(point => point[axis])))).toEqual([9, 18.5, 28])
  expect([0, 1, 2].map(axis => Math.max(...coordinates.map(point => point[axis])))).toEqual([11, 21.5, 32])
  const sixVolumes = triangles3d.map(([a, b, c]) => a[0] * (b[1] * c[2] - b[2] * c[1])
    + a[1] * (b[2] * c[0] - b[0] * c[2]) + a[2] * (b[0] * c[1] - b[1] * c[0]))
  expect(sixVolumes.reduce((sum, value) => sum + value) / 6).toBe(24)
})

it('has no mesh for an empty mask and refuses excessive surface faces', () => {
  const geometry = { shape: [1, 1, 1], affine: identity }
  expect(buildPredictionSurfaces(Uint8Array.of(0), geometry)).toEqual({})
  expect(() => buildPredictionSurfaces(Uint8Array.of(1), geometry, 5)).toThrow(/too detailed/)
})

it('only changes the 3D scene key when exact-mask surfaces arrive', () => {
  const options = { caseData: { case_id: 'Synthetic', files: { ct: 'ct.nii.gz', pred: 'prediction.nii.gz' } } }
  const assetUrls = { ct: 'blob:ct', pred: 'blob:pred' }
  const withMesh = { ...assetUrls, mesh: { pancreas_pred: 'blob:mesh' } }
  expect(viewerSceneKey({ ...options, mode: '2d', assetUrls })).toBe(viewerSceneKey({ ...options, mode: '2d', assetUrls: withMesh }))
  expect(viewerSceneKey({ ...options, mode: '3d', assetUrls })).not.toBe(viewerSceneKey({ ...options, mode: '3d', assetUrls: withMesh }))
})
