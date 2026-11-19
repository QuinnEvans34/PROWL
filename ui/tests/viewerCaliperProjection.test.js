import { describe, expect, it, vi } from 'vitest'
import { project3dCalipers, projectLesionMarker } from '../src/lib/viewerCaliperProjection.js'

const anchorWorldMm = [10, 20, 30]
const calipers = { plane: 'axial', anchorWorldMm, axes: [
  { lengthMm: 6, worldEndpointsMm: [[7, 20, 30], [13, 20, 30]] },
  { lengthMm: 4, worldEndpointsMm: [[10, 18, 30], [10, 22, 30]] },
] }
const deviceTile = [40, 20, 400, 300]

function viewer() {
  const nv = {
    canvas: { width: 500, height: 360, clientWidth: 250, clientHeight: 180 },
    scene: { renderAzimuth: 0, renderElevation: 0, zoom: 1, panX: 0 },
    screenSlices: [
      { axCorSag: 0, leftTopWidthHeight: [0, 0, 40, 360] },
      { axCorSag: 4, leftTopWidthHeight: deviceTile },
    ],
  }
  nv.calculateMvpMatrix = vi.fn((_, rect, azimuth) => {
    expect(rect).toEqual(deviceTile)
    const angle = azimuth * Math.PI / 180
    const x = nv.scene.zoom / 5
    const z = 1 / 10
    const c = Math.cos(angle)
    const s = Math.sin(angle)
    // Orbit around the recorded world point, then apply orthographic zoom/pan.
    return [[
      x * c, 0, -z * s, 0,
      0, x, 0, 0,
      x * s, 0, z * c, 0,
      nv.scene.panX - x * (c * 10 + s * 30), -x * 20, z * (s * 10 - c * 30), 1,
    ]]
  })
  return nv
}

const round = lines => lines.map(line => line.points.map(point => point.map(Math.round)))

describe('3D calipers', () => {
  it('projects the measured anchor and magnification into the 3D render tile at high DPI', () => {
    const nv = viewer()
    const result = project3dCalipers(nv, calipers)
    expect(nv.calculateMvpMatrix).toHaveBeenCalledExactlyOnceWith(null, deviceTile, 0, 0)
    expect(result.bounds).toEqual({ x: 20, y: 10, width: 200, height: 150 })
    expect(round(result.lines)).toEqual([[[60, 85], [180, 85]], [[120, 115], [120, 55]]])
    expect(projectLesionMarker(nv, anchorWorldMm)).toEqual({ x: 120, y: 85 })
  })

  it('keeps both arms facing the camera at an edge-on angle and follows pan and zoom', () => {
    const nv = viewer()
    const camera = nv.scene
    camera.renderAzimuth = 90
    camera.zoom = 1.2
    camera.panX = 0.1
    const result = project3dCalipers(nv, calipers)
    expect(round(result.lines)).toEqual([[[58, 85], [202, 85]], [[130, 121], [130, 49]]])
    expect(result.lines.map(line => line.lengthMm)).toEqual([6, 4])
  })

  it('preserves the unequal distances from the measured crossing', () => {
    const nv = viewer()
    const axes = [
      { lengthMm: 6, worldEndpointsMm: [[9, 20, 30], [15, 20, 30]] },
      { lengthMm: 4, worldEndpointsMm: [[10, 17, 30], [10, 21, 30]] },
    ]
    const result = project3dCalipers(nv, { ...calipers, axes })
    expect(round(result.lines)).toEqual([[[100, 85], [220, 85]], [[120, 130], [120, 70]]])
  })

  it('retains scaled endpoints for viewport clipping and hides a completely offscreen cross', () => {
    const nv = viewer()
    nv.scene.zoom = 2
    const result = project3dCalipers(nv, calipers)
    expect(result.lines[0].points).toEqual([
      [expect.closeTo(0), expect.closeTo(85)], [expect.closeTo(240), expect.closeTo(85)],
    ])
    nv.scene.panX = 3
    expect(project3dCalipers(nv, calipers)).toBeNull()
  })

  it('rejects unsupported planes, inconsistent lengths, and endpoints that do not cross at the anchor', () => {
    const nv = viewer()
    expect(project3dCalipers(nv, { ...calipers, plane: null })).toBeNull()
    expect(project3dCalipers(nv, { ...calipers, plane: 'coronal' })).toBeNull()
    expect(project3dCalipers(nv, { ...calipers, axes: [{ ...calipers.axes[0], lengthMm: 5 }, calipers.axes[1]] })).toBeNull()
    expect(project3dCalipers(nv, { ...calipers, anchorWorldMm: [11, 20, 30] })).toBeNull()
    expect(project3dCalipers(nv, { ...calipers, axes: [{ lengthMm: 6, worldEndpointsMm: [[7, 20, NaN], [13, 20, 30]] }, calipers.axes[1]] })).toBeNull()
  })

  it('requires a visible 3D render tile and a valid camera transform', () => {
    const nv = viewer()
    nv.screenSlices.pop()
    expect(project3dCalipers(nv, calipers)).toBeNull()
    nv.screenSlices.push({ axCorSag: 4, leftTopWidthHeight: deviceTile })
    nv.calculateMvpMatrix.mockReturnValue([new Float32Array(16)])
    expect(project3dCalipers(nv, calipers)).toBeNull()
    nv.canvas.clientHeight = 0
    expect(project3dCalipers(nv, calipers)).toBeNull()
  })
})
