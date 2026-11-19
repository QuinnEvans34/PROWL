import { expect, it } from 'vitest'
import { lesionDimensions } from '../src/lib/lesionDimensions.js'

it('bounds each lesion at its voxel edges in the original rotated affine', () => {
  const labels = new Uint8Array(5 * 5 * 4)
  for (const [x, y, z] of [[1, 1, 1], [2, 1, 1], [2, 2, 1], [2, 2, 2], [4, 4, 3]]) {
    labels[x + 5 * y + 25 * z] = 2
  }
  const { components } = lesionDimensions(labels, {
    shape: [5, 5, 4],
    affine: [[1, -2, 0, 100], [1, 2, 0, -20], [0, 0, 4, 5], [0, 0, 0, 1]],
    lesionVoxels: 5,
    voxelMm3: 16,
  })

  expect(components.map(component => component.voxelCount)).toEqual([4, 1])
  expect(components[0].boundsWorldMm).toEqual([
    [99.5, -18.5, 7], [101.5, -16.5, 7], [95.5, -14.5, 7], [97.5, -12.5, 7],
    [99.5, -18.5, 15], [101.5, -16.5, 15], [95.5, -14.5, 15], [97.5, -12.5, 15],
  ])
  expect(components[1].boundsWorldMm).toEqual([
    [96.5, -9.5, 15], [97.5, -8.5, 15], [94.5, -7.5, 15], [95.5, -6.5, 15],
    [96.5, -9.5, 19], [97.5, -8.5, 19], [94.5, -7.5, 19], [95.5, -6.5, 19],
  ])
})
