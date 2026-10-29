import { expect, it, vi } from 'vitest'
import { batchViewerUpdate } from '../src/lib/viewerUpdates.js'
function viewer() {
  const nv = Object.create({ updateGLVolume() { this.refresh(); this.drawScene() }, drawScene() { this.draw() } })
  nv.refresh = vi.fn(); nv.draw = vi.fn()
  return nv
}
it('applies all mesh edits with one texture refresh and one draw', () => {
  const nv = viewer()
  batchViewerUpdate(nv, () => {
    for (let i = 0; i < 30; i++) { nv.updateGLVolume(); nv.drawScene() }
    nv.opacity = 0.6
    expect(nv.refresh).not.toHaveBeenCalled()
  })
  expect(nv.opacity).toBe(0.6)
  expect(nv.refresh).toHaveBeenCalledTimes(1)
  expect(nv.draw).toHaveBeenCalledTimes(1)
  expect(Object.hasOwn(nv, 'updateGLVolume')).toBe(false)
})
it('restores instance methods after a failure without rendering partial edits', () => {
  const nv = viewer(), draw = vi.fn(); nv.drawScene = draw
  expect(() => batchViewerUpdate(nv, () => { nv.updateGLVolume(); throw Error('failed') })).toThrow('failed')
  expect(nv.drawScene).toBe(draw)
  expect(nv.refresh).not.toHaveBeenCalled()
  nv.updateGLVolume()
  expect(draw).toHaveBeenCalledTimes(1)
})
it('draws camera-only changes without uploading textures, and supports nested batches', () => {
  const nv = viewer()
  batchViewerUpdate(nv, () => { batchViewerUpdate(nv, () => nv.drawScene()); nv.drawScene() })
  expect(nv.refresh).not.toHaveBeenCalled()
  expect(nv.draw).toHaveBeenCalledTimes(1)
})
