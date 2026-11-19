import { describe, expect, it, vi } from 'vitest'
import { projectPredictedContours } from '../src/lib/viewerContour.js'
import { observeViewerDraw } from '../src/lib/viewerDraw.js'

const orientation = () => Float32Array.from([3, 0, 0, 0, 0, 2, 0, 0, 0, 0, 4, 0, 0, 0, 0, 1])

function fixture() {
  // The mask was loaded with a flipped native first axis. The displayed slice
  // contains a two-by-two pancreas with a one-voxel internal lesion.
  const mask = {
    matRAS: orientation(),
    dimsRAS: [3, 3, 2, 2],
    img2RASstep: [-1, 3, 6],
    img2RASstart: [2, 0, 0],
    img: Uint8Array.from([0, 2, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0]),
  }
  const ct = { matRAS: orientation(), dimsRAS: [3, 3, 2, 2] }
  const viewer = {
    volumes: [ct, mask],
    frac2mm: ([x, y, z]) => [x * 9, y * 4, z * 8],
    canvas: { width: 200, height: 160, clientWidth: 100, clientHeight: 80 },
    screenSlices: [{ axCorSag: 0, sliceFrac: 0.25, leftTopWidthHeight: [0, 0, 200, 160],
      leftTopMM: [9, 0], fovMM: [-9, 4] }],
  }
  return { mask, viewer }
}

describe('predicted mask contours', () => {
  it('matches the displayed RAS slice and follows mirrored and scaled pixels', () => {
    const { viewer, mask } = fixture()
    const contour = projectPredictedContours(viewer, mask, 'axial')
    expect(contour.paths).toEqual({
      pancreas: 'M0 0H2M0 2H2M0 0V2M2 0V2',
      lesion: 'M1 0H2M1 1H2M1 0V1M2 0V1',
    })
    expect(contour.bounds).toEqual({ x: 0, y: 0, width: 100, height: 80 })
    expect(contour.transform).toBe('matrix(-33.333333333333336 0 0 -40 100 80)')
    viewer.screenSlices[0].fovMM[0] = -4.5
    const zoomed = projectPredictedContours(viewer, mask, 'axial')
    expect(zoomed.paths).toBe(contour.paths)
    expect(zoomed.transform).toBe('matrix(-66.66666666666667 0 0 -40 200 80)')
    viewer.screenSlices[0].sliceFrac = 0.75
    expect(projectPredictedContours(viewer, mask, 'axial').paths).toEqual({ pancreas: '', lesion: '' })
  })

  it('withholds contours for a mismatched scan or unsupported projection', () => {
    const { viewer, mask } = fixture()
    mask.matRAS[3] += 1
    expect(projectPredictedContours(viewer, mask, 'axial')).toBeNull()
    mask.matRAS = orientation()
    viewer.frac2mm = ([x, y, z]) => [x * 9, y * 4, z * 8 + x]
    expect(projectPredictedContours(viewer, mask, 'axial')).toBeNull()
    expect(projectPredictedContours(viewer, mask, 'coronal')).toBeNull()
  })
})

it('keeps independent overlays subscribed with a single wrapped draw', () => {
  const draw = vi.fn(() => 'frame')
  const viewer = { drawSceneCore: draw }
  const a = vi.fn()
  const b = vi.fn()
  const detachA = observeViewerDraw(viewer, a)
  const shared = viewer.drawSceneCore
  const detachB = observeViewerDraw(viewer, b)
  expect(viewer.drawSceneCore).toBe(shared)
  expect(viewer.drawSceneCore()).toBe('frame')
  expect(draw).toHaveBeenCalledOnce()
  expect(a).toHaveBeenCalledOnce()
  expect(b).toHaveBeenCalledOnce()
  detachA()
  viewer.drawSceneCore()
  expect(a).toHaveBeenCalledOnce()
  expect(b).toHaveBeenCalledTimes(2)
  detachB()
  expect(viewer.drawSceneCore).toBe(draw)
})
