import { expect, it } from 'vitest'
import { measureMask } from '../src/lib/scanMeasurements.js'

const shape = [8, 8, 8]
const aligned = [[0, -3, 0, -9], [2, 0, 0, 4], [0, 0, 4, 2], [0, 0, 0, 1]]

function measure(voxels, affine = aligned) {
  const header = { dims: [3, ...shape, 1, 1, 1, 1], affine, xyzt_units: 2, sform_code: 1 }
  const labels = new Uint8Array(8 ** 3)
  for (const [x, y, z, label = 1] of voxels) labels[x + 8 * y + 64 * z] = label
  return measureMask(header, header, labels).pancreasDimensions
}

it('measures the pancreas and lesion label union on the largest native slice', () => {
  const voxels = [[1, 1, 1], [1, 1, 5]]
  for (let y = 2; y <= 4; y++) {
    for (let x = 2; x <= 5; x++) voxels.push([x, y, 3, y === 3 && x >= 3 ? 2 : 1])
  }
  const dimensions = measure(voxels)

  expect(dimensions).toMatchObject({
    status: 'ready', superiorInferiorMm: 20, focusWorldMm: [-18, 10, 14],
    calipers: {
      nativeSlice: 3, plane: 'axial', anchorVoxel: [3, 3, 3], anchorWorldMm: [-18, 10, 14],
      axes: [
        { lengthMm: 8, worldEndpointsMm: [[-18, 7, 14], [-18, 15, 14]] },
        { lengthMm: 9, worldEndpointsMm: [[-13.5, 10, 14], [-22.5, 10, 14]] },
      ],
    },
  })
})

it('keeps calipers inside a concave outline and uses the first equally large slice', () => {
  const voxels = []
  for (const z of [2, 4]) for (let y = 1; y <= 3; y++) for (let x = 1; x <= 3; x++) {
    if (x !== 2 || y !== 2) voxels.push([x, y, z])
  }
  const { calipers } = measure(voxels)

  expect(calipers.anchorVoxel).toEqual([1, 2, 2])
  expect(calipers.axes[0].voxelEndpoints).toEqual([[0.5, 2, 2], [1.5, 2, 2]])
  expect(calipers.axes.map(axis => axis.lengthMm)).toEqual([2, 9])
})

it('retains physical spans without assigning an inexact anatomical viewer plane', () => {
  const { calipers, caliperUnavailableReason } = measure([[2, 2, 2], [3, 2, 2]], [
    [2, 0, 0, 1], [0, Math.SQRT2, -Math.SQRT2, 10], [0, Math.SQRT2, Math.SQRT2, -2], [0, 0, 0, 1],
  ])

  expect(calipers.plane).toBeNull()
  expect(calipers.axes[0].lengthMm).toBe(4)
  expect(calipers.axes[1].lengthMm).toBeCloseTo(2)
  expect(caliperUnavailableReason).toMatch(/does not align/)
})

it('withholds perpendicular calipers for a sheared slice while retaining head-to-foot extent', () => {
  const dimensions = measure([[2, 2, 2], [3, 2, 2]], [
    [2, 1, 0, -9], [0, 3, 0, 4], [0.5, 0, 4, 2], [0, 0, 0, 1],
  ])

  expect(dimensions).toMatchObject({ calipers: null, superiorInferiorMm: 5, caliperUnavailableReason: expect.stringMatching(/not perpendicular/) })
})
