import { describe, expect, it } from 'vitest'
import { clientToBackingPx, zoom2d, zoomBox2d, zoom3dFraming, zoomBox3dFraming } from '../src/lib/viewerZoom.js'

function mirroredCoronalView() {
  const scene = { pan2Dxyzmm: [276, -63, 155, 1.5], crosshairPos: [108, 12, -82] }
  return {
    scene,
    screenSlices: [{ axCorSag: 1, leftTopWidthHeight: [300, 30, -240, 160] }],
    screenXY2TextureFrac(x, y) {
      const [panX, , panZ, zoom] = scene.pan2Dxyzmm
      return [(180 - x - panX) / zoom, scene.crosshairPos[1], (110 - y - panZ) / zoom]
    },
    frac2mm: fraction => fraction,
    setPan2Dxyzmm: next => { scene.pan2Dxyzmm = next },
    project(world) {
      const [panX, , panZ, zoom] = scene.pan2Dxyzmm
      return [180 - (world[0] * zoom + panX), 110 - (world[2] * zoom + panZ)]
    },
  }
}

describe('viewer zoom framing', () => {
  it('converts pointer coordinates to the actual canvas backing pixels', () => {
    const canvas = {
      width: 600,
      height: 200,
      getBoundingClientRect: () => ({ left: 20, top: 40, width: 300, height: 200 }),
    }
    expect(clientToBackingPx(canvas, 130, 90)).toEqual([220, 50])
  })

  it('keeps the cursor on its image point in a mirrored, panned 2D plane', () => {
    const nv = mirroredCoronalView()
    const anchor = [125, 160]
    const world = nv.screenXY2TextureFrac(...anchor)
    const crosshair = nv.scene.crosshairPos.slice()
    expect(zoom2d(nv, 2, anchor)).toBe(true)
    expect(nv.project(world)).toEqual(anchor)
    expect(nv.scene.pan2Dxyzmm[3]).toEqual(3)
    expect(nv.scene.crosshairPos).toEqual(crosshair)
  })

  it('centers a rectangle without changing the active slice', () => {
    const nv = mirroredCoronalView()
    const start = [240, 160]
    const end = [160, 80]
    const world = nv.screenXY2TextureFrac(200, 120)
    expect(zoomBox2d(nv, start, end)).toBe(true)
    expect(nv.project(world)).toEqual([180, 110])
    expect(nv.scene.pan2Dxyzmm[3]).toEqual(3)
    expect(nv.scene.crosshairPos).toEqual([108, 12, -82])
    expect(zoomBox2d(nv, start, [242, 163])).toBe(false)
  })

  it('keeps the 3D cursor anchored after applying the maximum scale', () => {
    const pivot = [103, -66, 129]
    const viewport = [40, 60, 240, 160]
    const center = [100, -70, 124]
    const viewPoint = ([x, y]) => [center[0] - (y - 140) / 2, center[1] + (x - 160) / 2, center[2]]
    const anchor = [200, 104]
    const previousScale = 3
    const next = zoom3dFraming(previousScale, pivot, 2, viewport, viewPoint, anchor)
    expect(next.scale).toBe(4)
    const projected = ([x, y]) => [
      160 + ((x - 160) - (next.pivot[1] - pivot[1]) * 2) * next.scale / previousScale,
      140 + ((y - 140) + (next.pivot[0] - pivot[0]) * 2) * next.scale / previousScale,
    ]
    expect(projected(anchor)).toEqual(anchor)
  })

  it('centers the chosen 3D rectangle in view coordinates without moving in depth', () => {
    const pivot = [100, -70, 124]
    const viewport = [40, 60, 240, 160]
    const viewPoint = ([x, y]) => [pivot[0] - (y - 140) / 2, pivot[1] + (x - 160) / 2, pivot[2]]
    const next = zoomBox3dFraming(1, pivot, viewport, viewPoint, [95, 80], [155, 120])
    expect(next).toEqual({ scale: 4, pivot: viewPoint([125, 100]) })
  })
})
