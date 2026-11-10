import React from 'react'
import { act, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'

const harness = vi.hoisted(() => ({ instances: [], observers: [], origin: [0, 0, 0], spacing: [1, 1, 1] }))
vi.mock('@niivue/niivue', () => ({
  DRAG_MODE: { crosshair: 0, pan: 1, windowing: 2 },
  Niivue: class SyntheticNiivue {
    constructor(options) {
      this.opts = options
      this.scene = { crosshairPos: new Float32Array([.5, .5, .5]), pan2Dxyzmm: new Float32Array([0, 0, 0, 1]), volScaleMultiplier: 1 }
      this.volumes = []
      this.meshes = []
      this.screenSlices = []
      this.sliceTypeAxial = 0; this.sliceTypeCoronal = 1; this.sliceTypeSagittal = 2; this.sliceTypeMultiplanar = 3
      this.loadVolumes = vi.fn(async specs => {
        this.volumes = specs.map(spec => ({ ...spec, hdr: { dims: [3, 11, 21, 31], affine: [[harness.spacing[0], 0, 0, harness.origin[0]], [0, harness.spacing[1], 0, harness.origin[1]], [0, 0, harness.spacing[2], harness.origin[2]], [0, 0, 0, 1]] }, img: new Uint8Array(11 * 21 * 31) }))
      })
      this.resizeListener = vi.fn(() => {
        this.canvas.width = this.canvas.offsetWidth * window.devicePixelRatio
        this.canvas.height = this.canvas.offsetHeight * window.devicePixelRatio
      })
      this.drawScene = vi.fn()
      this.cleanup = vi.fn()
      harness.instances.push(this)
    }
    attachToCanvas(canvas) { this.canvas = canvas }
    updateGLVolume() {}
    clearCustomLayout() {}
    setSliceType() {
      // Exercise our preservation contract even if a renderer resets its view.
      this.scene.pan2Dxyzmm = new Float32Array([0, 0, 0, 1])
    }
    setCrosshairColor() {}
    setAtlasOutline() {}
    setMouseEventConfig() {}
    setTouchEventConfig() {}
    setOpacity() {}
    setPan2Dxyzmm(value) { this.scene.pan2Dxyzmm = new Float32Array(value) }
    setScale(value) { this.scene.volScaleMultiplier = value }
    mm2frac(point) {
      const hdr = this.volumes[0].hdr
      return point.map((value, axis) => ((value - hdr.affine[axis][3]) / hdr.affine[axis][axis] + .5) / hdr.dims[axis + 1])
    }
    frac2mm(fractions) {
      const hdr = this.volumes[0].hdr
      return Array.from(fractions, (fraction, axis) => (fraction * hdr.dims[axis + 1] - .5) * hdr.affine[axis][axis] + hdr.affine[axis][3])
    }
  },
}))

import NiivueViewer, { navigationSnapshot, viewerSceneKey } from '../src/components/NiivueViewer.jsx'

const caseData = { case_id: 'SYNTHETIC_ONLY', files: { ct: 'synthetic-only.nii.gz' } }
const base = { caseData, sources: [], activePlane: 'axial', label: 'Synthetic CT' }

beforeEach(() => {
  harness.instances.length = 0
  harness.observers.length = 0
  harness.origin = [0, 0, 0]
  harness.spacing = [1, 1, 1]
  vi.stubGlobal('ResizeObserver', class {
    constructor(callback) { this.callback = callback; harness.observers.push(this) }
    observe() {}
    disconnect() {}
  })
})

it('links anatomical position without changing local pan or zoom, and tags remote updates', async () => {
  const report = vi.fn()
  const { rerender } = render(<NiivueViewer {...base} onNavigationChange={report} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.scene.pan2Dxyzmm = new Float32Array([12, -7, 9, 2.2])
  const sceneKey = viewerSceneKey(base)
  rerender(<NiivueViewer {...base} onNavigationChange={report} syncCrosshair={{ id: 1, sceneKey, fractions: [.2, .6, .8] }} />)
  await waitFor(() => expect(nv.scene.crosshairPos[2]).toBeCloseTo(.8))
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual([12, -7, 9, expect.closeTo(2.2)])
  expect(report.mock.lastCall[0]).toMatchObject({ origin: 'sync', sceneKey, indices: { axial: 24, coronal: 12, sagittal: 2 } })
  const calls = report.mock.calls.length
  rerender(<NiivueViewer {...base} onNavigationChange={report} syncCrosshair={{ id: 2, sceneKey, fractions: [.2, .6, .8] }} />)
  expect(report.mock.calls.length).toBe(calls)
})

it('preserves pan and zoom when changing plane or resizing, and zooms the 2D image independently', async () => {
  const { rerender } = render(<NiivueViewer {...base} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.scene.pan2Dxyzmm = new Float32Array([3, -5, 7, 2])
  rerender(<NiivueViewer {...base} activePlane="coronal" />)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual([3, -5, 7, 2])
  act(() => harness.observers.at(-1).callback())
  await waitFor(() => expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual([3, -5, 7, 2]))
  rerender(<NiivueViewer {...base} activePlane="coronal" navigationCommand={{ id: 1, type: 'zoom', factor: 1.5 }} />)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual([-2, -15, -8, 3])
  expect(nv.scene.volScaleMultiplier).toBe(1)
  expect(harness.instances).toHaveLength(1)
  expect(nv.loadVolumes).toHaveBeenCalledTimes(1)
})

it('anchors zoom at the crosshair for non-origin CT affines, without zooming another plane', async () => {
  harness.origin = [-342.55, -397.22, -16]
  harness.spacing = [1.5, 1.5, 1.5]
  const renderPair = navigationCommand => <>
    <NiivueViewer {...base} label="Synthetic axial" navigationCommand={navigationCommand} />
    <NiivueViewer {...base} label="Synthetic coronal" activePlane="coronal" />
  </>
  const { rerender } = render(renderPair(null))
  await waitFor(() => expect(screen.getAllByLabelText('Prepared result loaded')).toHaveLength(2))
  const [nv, peer] = harness.instances
  nv.scene.pan2Dxyzmm = new Float32Array([8, -3, 7, 1])
  const position = Array.from(nv.scene.crosshairPos)
  const anchor = nv.frac2mm(position)
  // In NiiVue's 2D camera, world*zoom + pan determines where a world point
  // appears. It must remain identical through zoom and its inverse.
  const initialProjection = anchor.map((value, axis) => value + nv.scene.pan2Dxyzmm[axis])
  const peerView = Array.from(peer.scene.pan2Dxyzmm)
  rerender(renderPair({ id: 1, type: 'zoom', factor: 1.2 }))
  rerender(renderPair({ id: 2, type: 'zoom', factor: 1.2 }))
  expect(nv.scene.pan2Dxyzmm[3]).toBeCloseTo(1.44)
  initialProjection.forEach((value, axis) => expect(anchor[axis] * nv.scene.pan2Dxyzmm[3] + nv.scene.pan2Dxyzmm[axis]).toBeCloseTo(value, 4))
  expect(Array.from(nv.scene.crosshairPos)).toEqual(position)
  expect(Array.from(peer.scene.pan2Dxyzmm)).toEqual(peerView)
  rerender(renderPair({ id: 3, type: 'zoom', factor: 1 / 1.44 }))
  Array.from(nv.scene.pan2Dxyzmm).forEach((value, axis) => expect(value).toBeCloseTo([8, -3, 7, 1][axis], 4))
})

it('grows the rendered scan with the pane and restores its original size without changing the anatomical camera', async () => {
  harness.origin = [-342.55, -397.22, -16]
  harness.spacing = [1.5, 1.5, 1.5]
  render(<NiivueViewer {...base} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  const canvas = nv.canvas
  let size = { width: 512, height: 320 }
  for (const [property, dimension] of [['clientWidth', 'width'], ['offsetWidth', 'width'], ['clientHeight', 'height'], ['offsetHeight', 'height']]) {
    Object.defineProperty(canvas, property, { configurable: true, get: () => size[dimension] })
  }
  nv.scene.crosshairPos = new Float32Array([.2, .4, .8])
  nv.scene.pan2Dxyzmm = new Float32Array([8, -3, 7, 1.44])
  nv.volumes[0].cal_min = .2
  nv.volumes[0].cal_max = .8
  const position = Array.from(nv.scene.crosshairPos)
  const camera = Array.from(nv.scene.pan2Dxyzmm)
  const anchor = nv.frac2mm(position)
  const projection = anchor.map((value, axis) => value * camera[3] + camera[axis])
  const resize = async () => {
    const calls = nv.resizeListener.mock.calls.length
    act(() => harness.observers.at(-1).callback())
    await waitFor(() => expect(nv.resizeListener).toHaveBeenCalledTimes(calls + 1))
  }
  await resize()
  const initialBuffer = [canvas.width, canvas.height]
  size = { width: 1024, height: 640 }
  await resize()
  // The renderer receives twice as many pixels per anatomical unit instead
  // of stretching a stale buffer or retaining the smaller drawing viewport.
  expect([canvas.width, canvas.height]).toEqual(initialBuffer.map(value => value * 2))
  expect(nv.drawScene).toHaveBeenCalled()
  expect(Array.from(nv.scene.crosshairPos)).toEqual(position)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(camera)
  projection.forEach((value, axis) => expect(anchor[axis] * nv.scene.pan2Dxyzmm[3] + nv.scene.pan2Dxyzmm[axis]).toBeCloseTo(value, 4))
  expect([nv.volumes[0].cal_min, nv.volumes[0].cal_max]).toEqual([.2, .8])
  size = { width: 512, height: 320 }
  await resize()
  expect([canvas.width, canvas.height]).toEqual(initialBuffer)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(camera)
  expect(nv.loadVolumes).toHaveBeenCalledTimes(1)
})

it('moves each slice slider to a voxel center, including the first and last slice', async () => {
  const report = vi.fn()
  const { rerender } = render(<NiivueViewer {...base} onNavigationChange={report} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  rerender(<NiivueViewer {...base} onNavigationChange={report} navigationCommand={{ id: 1, type: 'slice', plane: 'axial', index: 0 }} />)
  expect(nv.scene.crosshairPos[2]).toBeCloseTo(.5 / 31)
  rerender(<NiivueViewer {...base} onNavigationChange={report} navigationCommand={{ id: 2, type: 'slice', plane: 'axial', index: 30 }} />)
  expect(nv.scene.crosshairPos[2]).toBeCloseTo(30.5 / 31)
  await waitFor(() => expect(report.mock.lastCall[0].indices.axial).toBe(30))
})

it('fits the 2D image without changing its anatomical slice', async () => {
  const { rerender } = render(<NiivueViewer {...base} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.scene.crosshairPos = new Float32Array([.2, .4, .8])
  nv.scene.pan2Dxyzmm = new Float32Array([8, -3, 7, 2])
  const position = Array.from(nv.scene.crosshairPos)
  rerender(<NiivueViewer {...base} navigationCommand={{ id: 'fit-current-slice', type: 'fit' }} />)
  expect(Array.from(nv.scene.crosshairPos)).toEqual(position)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual([0, 0, 0, 1])
})

it('does not replay a retained navigation command when the image source reloads', async () => {
  const navigationCommand = { id: 1, type: 'zoom', factor: 2 }
  const { rerender } = render(<NiivueViewer {...base} navigationCommand={navigationCommand} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  expect(nv.scene.pan2Dxyzmm[3]).toBe(2)
  rerender(<NiivueViewer {...base} assetUrls={{ ct: '/synthetic-source-version-2.nii.gz' }} navigationCommand={navigationCommand} />)
  await waitFor(() => expect(nv.loadVolumes).toHaveBeenCalledTimes(2))
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.scene.pan2Dxyzmm[3]).toBe(2)
})

it('refuses position and window updates belonging to a previous study', async () => {
  const { rerender } = render(<NiivueViewer {...base} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  const before = Array.from(nv.scene.crosshairPos)
  rerender(<NiivueViewer {...base} syncCrosshair={{ id: 1, sceneKey: 'STALE', fractions: [0, 0, 0] }} syncWindow={{ id: 1, sceneKey: 'STALE', range: [-50, 200] }} />)
  expect(Array.from(nv.scene.crosshairPos)).toEqual(before)
  expect(nv.volumes[0].cal_min).toBe(.08)
  const sceneKey = viewerSceneKey(base)
  rerender(<NiivueViewer {...base} syncWindow={{ id: 2, sceneKey, range: [-50, 200] }} />)
  expect(nv.volumes[0].cal_min).toBe(-50)
  expect(nv.volumes[0].cal_max).toBe(200)
})

it('retains a manually adjusted window when layers change and resets only for an explicit preset', async () => {
  const onWindowChange = vi.fn()
  const { rerender } = render(<NiivueViewer {...base} onWindowChange={onWindowChange} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.volumes[0].cal_min = .2
  nv.volumes[0].cal_max = .8
  act(() => nv.onIntensityChange(nv.volumes[0]))
  expect(onWindowChange).toHaveBeenCalledWith({ sceneKey: viewerSceneKey(base), range: [.2, .8] })
  rerender(<NiivueViewer {...base} onWindowChange={onWindowChange} overlayOpacity={.25} showPancreas={false} />)
  expect(nv.volumes[0].cal_min).toBe(.2)
  expect(nv.volumes[0].cal_max).toBe(.8)
  rerender(<NiivueViewer {...base} onWindowChange={onWindowChange} ctWindow="wide" />)
  expect(nv.volumes[0].cal_min).toBe(0)
  expect(nv.volumes[0].cal_max).toBe(1)
})

it('serializes slow study loads so a previous scan cannot populate the new scene', async () => {
  const { rerender } = render(<NiivueViewer {...base} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  const load = nv.loadVolumes.getMockImplementation()
  let release
  const barrier = new Promise(resolve => { release = resolve })
  nv.loadVolumes.mockImplementationOnce(async specs => { await barrier; await load(specs) })
  const second = { case_id: 'SYNTHETIC_SECOND', files: { ct: 'second.nii.gz' } }
  const third = { case_id: 'SYNTHETIC_THIRD', files: { ct: 'third.nii.gz' } }
  rerender(<NiivueViewer {...base} caseData={second} />)
  await waitFor(() => expect(nv.loadVolumes).toHaveBeenCalledTimes(2))
  rerender(<NiivueViewer {...base} caseData={third} />)
  expect(screen.getByLabelText('Synthetic CT').style.visibility).toBe('hidden')
  expect(nv.loadVolumes).toHaveBeenCalledTimes(2)
  await act(async () => { release(); await barrier })
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.loadVolumes).toHaveBeenCalledTimes(3)
  expect(nv.volumes[0].url).toBe('/cases/third.nii.gz')
  expect(screen.getByLabelText('Synthetic CT').style.visibility).toBe('')
})

it('reports displayed anatomical axes and mask ranges for a permuted native file grid', () => {
  const hdr = { dims: [3, 2, 3, 4], affine: [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]] }
  const mask = { hdr, img: new Uint8Array(24) }
  mask.img[1 + 2 * (1 + 3 * 2)] = 2
  const nv = {
    volumes: [{ hdr, dimsRAS: [3, 4, 3, 2] }],
    scene: { crosshairPos: [.625, .5, .75] },
    mm2frac: world => world.map((value, axis) => (value + .5) / [4, 3, 2][axis]),
  }
  expect(navigationSnapshot(nv, mask)).toMatchObject({
    indices: { sagittal: 2, coronal: 1, axial: 1 },
    totals: { sagittal: 4, coronal: 3, axial: 2 },
    ranges: { lesion: { sagittal: [2, 2], coronal: [1, 1], axial: [1, 1] }, pancreas: null },
  })
})
