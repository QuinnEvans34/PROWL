import React from 'react'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'

const harness = vi.hoisted(() => ({ instances: [], observers: [], origin: [0, 0, 0], spacing: [1, 1, 1] }))
vi.mock('@niivue/niivue', () => ({
  DRAG_MODE: { none: 0, crosshair: 8, pan: 3, windowing: 9 },
  Niivue: class SyntheticNiivue {
    constructor(options) {
      this.opts = { dragMode: 0, clipPlaneHotKey: 'KeyC', cycleClipPlaneHotKey: 'KeyP', ...options }
      this.scene = { crosshairPos: new Float32Array([.5, .5, .5]), pan2Dxyzmm: new Float32Array([0, 0, 0, 1]), volScaleMultiplier: 1 }
      this.volumes = []
      this.meshes = []
      this.screenSlices = []
      this.sliceTypeAxial = 0; this.sliceTypeCoronal = 1; this.sliceTypeSagittal = 2; this.sliceTypeMultiplanar = 3; this.sliceTypeRender = 4
      this.loadVolumes = vi.fn(async specs => {
        const dims = [3, 11, 21, 31]
        const [sx, sy, sz] = harness.spacing
        const [x, y, z] = harness.origin
        const affine = [[sx, 0, 0, x], [0, sy, 0, y], [0, 0, sz, z], [0, 0, 0, 1]]
        this.volumes = specs.map(spec => ({
          ...spec,
          setColormapLabel(value) { this.labelColormap = value },
          hdr: { dims, affine, xyzt_units: 2 },
          img: new Uint8Array(11 * 21 * 31),
        }))
      })
      this.resizeListener = vi.fn(() => {
        this.canvas.width = this.canvas.offsetWidth * window.devicePixelRatio
        this.canvas.height = this.canvas.offsetHeight * window.devicePixelRatio
      })
      this.loadMeshes = vi.fn(async specs => {
        this.meshes = specs.map((spec, id) => ({ ...spec, id, visible: true, pts: new Float32Array([.25, 0, .8]) }))
      })
      this.calculateMvpMatrix = vi.fn(() => [[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]])
      this.drawScene = vi.fn()
      this.mouseMove = vi.fn()
      this.nativeGesture = vi.fn()
      this.cleanup = vi.fn(() => this.nativeGestures?.abort())
      harness.instances.push(this)
    }
    attachToCanvas(canvas) {
      this.canvas = canvas
      this.nativeGestures = new AbortController()
      for (const event of ['wheel', 'touchstart', 'touchmove', 'keydown', 'keyup']) {
        canvas.addEventListener(event, this.nativeGesture, { signal: this.nativeGestures.signal })
      }
    }
    updateGLVolume() {}
    clearCustomLayout() {}
    setSliceType() {
      // Exercise our preservation contract even if a renderer resets its view.
      this.scene.pan2Dxyzmm = new Float32Array([0, 0, 0, 1])
    }
    setCrosshairColor() {}
    setAtlasOutline() {}
    setMeshShader(id, shader) { this.meshes[id].shader = shader }
    setMeshProperty(id, key, value) { this.meshes[id][key] = value }
    setRenderAzimuthElevation(azimuth, elevation) { this.scene.renderAzimuth = azimuth; this.scene.renderElevation = elevation }
    setClipPlaneColor() {}
    setClipPlane(value) { this.scene.clipPlane = value }
    resetBriCon() {}
    setDragMode(value) { this.opts.dragMode = value }
    setMouseEventConfig(config) { this.opts.mouseEventConfig = config }
    setTouchEventConfig(config) { this.opts.touchEventConfig = config }
    setOpacity(index, opacity) { this.volumes[index].opacity = opacity }
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
import ToolbenchViewer from '../src/components/ToolbenchViewer.jsx'
import { projectCalipers } from '../src/lib/viewerCaliperProjection.js'

const caseData = { case_id: 'SYNTHETIC_ONLY', files: { ct: 'synthetic-only.nii.gz' } }
const base = { caseData, sources: [], activePlane: 'axial', label: 'Synthetic CT' }
const anatomyProps = {
  ...base,
  sources: ['pred'],
  caseData: {
    ...caseData,
    files: {
      ...caseData.files,
      pred: 'synthetic-pred.nii.gz',
      mesh: { pancreas_pred: 'synthetic-pancreas.obj', lesion_pred: 'synthetic-lesion.obj' },
    },
  },
}

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

it('keeps CT and surrounding surfaces at their configured opacity during inspection', async () => {
  const props = { ...anatomyProps, mode: '3d', ctOpacity: .44 }
  const { rerender } = render(<NiivueViewer {...props} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  const [pancreas, lesion] = nv.meshes
  const baseline = { pancreas: pancreas.opacity, lesion: lesion.opacity }
  const selectedLesion = { source: 'pred', anatomy: 'lesion', worldMm: [1, 2, 3] }
  const selectedPancreas = { source: 'pred', anatomy: 'pancreas', worldMm: [4, 5, 6] }

  rerender(<NiivueViewer {...props} selectedObject={selectedLesion} />)
  expect(nv.volumes[0].opacity).toBe(.44)
  expect(pancreas.opacity).toBe(baseline.pancreas)
  expect(lesion.shader).toBe('Toon')
  rerender(<NiivueViewer {...props} selectedObject={selectedPancreas} />)
  expect(nv.volumes[0].opacity).toBe(.44)
  expect(lesion.opacity).toBe(baseline.lesion)
  expect(pancreas.shader).toBe('Toon')

  rerender(<NiivueViewer {...props} selectedObject={selectedPancreas} focusTreatment="isolate" />)
  expect(nv.volumes[0].opacity).toBe(.44)
  expect(lesion.visible).toBe(false)
  rerender(<NiivueViewer {...props} selectedObject={selectedPancreas} clip={{ enabled: true, progress: 100 }} />)
  expect(nv.volumes[0].opacity).toBe(0)
  rerender(<NiivueViewer {...props} selectedObject={selectedPancreas} ctOpacity={0} />)
  expect(nv.volumes[0].opacity).toBe(0)

  rerender(<NiivueViewer {...props} />)
  expect(pancreas.opacity).toBe(baseline.pancreas)
  expect(lesion.opacity).toBe(baseline.lesion)
  expect(nv.pivot3D).toEqual(selectedPancreas.worldMm)
  nv.pivot3D = [0, 0, 0]
  rerender(<NiivueViewer {...props} selectedObject={selectedPancreas} />)
  expect(nv.pivot3D).toEqual(selectedPancreas.worldMm)
})

it('preserves the 2D anatomy overlays on an inspected slice unless isolation is requested', async () => {
  const { rerender } = render(<NiivueViewer {...anatomyProps} />)
  await screen.findByLabelText('Prepared result loaded')
  const [ct, prediction] = harness.instances[0].volumes
  const selected = { source: 'pred', anatomy: 'lesion', worldMm: [1, 2, 3] }
  expect(prediction.labelColormap.A).toEqual([0, 188, 255])
  rerender(<NiivueViewer {...anatomyProps} selectedObject={selected} />)
  expect(ct.opacity).toBe(1)
  expect(prediction.labelColormap.A).toEqual([0, 188, 255])
  rerender(<NiivueViewer {...anatomyProps} selectedObject={selected} focusTreatment="isolate" />)
  expect(ct.opacity).toBe(1)
  expect(prediction.labelColormap.A).toEqual([0, 0, 255])
})

it('keeps the reference fill unless a matching CT grid has the requested single plane', async () => {
  const props = {
    ...anatomyProps,
    sources: ['pred', 'gt'],
    overlayOpacity: .6,
    caseData: {
      ...anatomyProps.caseData,
      files: { ...anatomyProps.caseData.files, gt: 'synthetic-reference.nii.gz' },
    },
  }
  const { rerender } = render(<NiivueViewer {...props} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  const [ct, prediction, reference] = nv.volumes
  const grid = { dimsRAS: [3, 11, 21, 31], matRAS: Float32Array.from([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]) }
  Object.assign(ct, grid)
  Object.assign(reference, grid, { matRAS: grid.matRAS.slice() })
  expect(reference.opacity).toBe(.6)

  nv.screenSlices = [{ axCorSag: nv.sliceTypeAxial, sliceFrac: .5 }]
  rerender(<NiivueViewer {...props} overlayOpacity={.5} />)
  expect(prediction.opacity).toBe(.5)
  expect(reference.opacity).toBe(0)

  rerender(<NiivueViewer {...props} activePlane="coronal" />)
  expect(reference.opacity).toBe(.6)
  rerender(<NiivueViewer {...props} activePlane="multiplanar" />)
  expect(reference.opacity).toBe(.6)

  ct.matRAS[12] = 10
  rerender(<NiivueViewer {...props} />)
  expect(reference.opacity).toBe(.6)
  rerender(<NiivueViewer {...props} overlayMode="off" />)
  expect(prediction.opacity).toBe(0)
  expect(reference.opacity).toBe(0)
})

it('keeps other difference regions visible while inspecting one region', async () => {
  const props = {
    ...anatomyProps,
    mode: '3d',
    sources: ['pred', 'gt'],
    differenceMode: true,
    enableDifferenceAssets: true,
    caseData: {
      ...caseData,
      files: {
        ...anatomyProps.caseData.files,
        gt: 'synthetic-gt.nii.gz',
        difference: { pancreas: 'synthetic-diff-pancreas.nii.gz', lesion: 'synthetic-diff-lesion.nii.gz' },
        mesh: {
          pancreas_agreement: 'pancreas-agreement.obj',
          pancreas_pred_only: 'pancreas-pred-only.obj',
          lesion_gt_only: 'lesion-gt-only.obj',
        },
      },
    },
  }
  const { rerender } = render(<NiivueViewer {...props} />)
  await screen.findByLabelText('Prepared result loaded')
  const [agreement, predictionOnly, referenceLesion] = harness.instances[0].meshes
  const lesionOpacity = referenceLesion.opacity
  const selected = { source: 'difference', anatomy: 'pancreas', region: 'agreement', worldMm: [4, 5, 6] }

  rerender(<NiivueViewer {...props} selectedObject={selected} />)
  expect(agreement.shader).toBe('Toon')
  expect(predictionOnly.opacity).toBe(1)
  expect(referenceLesion.opacity).toBe(lesionOpacity)

  rerender(<NiivueViewer {...props} selectedObject={selected} focusTreatment="isolate" />)
  expect(agreement.visible).toBe(true)
  expect(predictionOnly.visible).toBe(false)
  expect(referenceLesion.visible).toBe(false)
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

it('locks 2D framing while allowing slice steps and windowing, then unlocks without applying skipped commands', async () => {
  const { rerender } = render(<NiivueViewer {...base} interactionMode="pan" />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.opts.dragMode = 3
  const framing = [3, -5, 7, 2]
  nv.scene.pan2Dxyzmm = new Float32Array(framing)
  const beforeSlice = nv.scene.crosshairPos[2]
  const view = options => <NiivueViewer {...base} interactionMode="pan" framingLocked {...options} />
  rerender(view({ navigationCommand: { id: 1, type: 'slice', plane: 'axial', index: 23 } }))
  expect(nv.scene.crosshairPos[2]).not.toBe(beforeSlice)
  expect(nv.scene.crosshairPos[2]).toBeCloseTo(23.5 / 31)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(framing)
  expect(nv.opts.mouseEventConfig).toEqual({ leftButton: { primary: 8, withShift: 0, withCtrl: 8 }, rightButton: 9, centerButton: 0 })
  expect(nv.opts.touchEventConfig).toEqual({ singleTouch: 8, doubleTouch: 0 })
  expect(nv.opts.dragMode).toBe(0)
  const modeCycle = new KeyboardEvent('keydown', { code: 'KeyM', bubbles: true, cancelable: true })
  act(() => nv.canvas.dispatchEvent(modeCycle))
  expect(modeCycle.defaultPrevented).toBe(true)
  const fit = { id: 2, type: 'fit' }
  rerender(view({ navigationCommand: fit, resetToken: 1 }))
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(framing)
  expect(nv.scene.crosshairPos[2]).toBeCloseTo(23.5 / 31)
  rerender(view({ navigationCommand: { id: 3, type: 'zoom', factor: 2 }, interactionMode: 'window', resetToken: 1 }))
  expect(nv.opts.mouseEventConfig.leftButton.primary).toBe(9)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(framing)
  rerender(view({ navigationCommand: fit, resetToken: 1 }))
  rerender(view({ framingLocked: false, navigationCommand: fit, resetToken: 1 }))
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(framing)
  expect(nv.opts.dragMode).toBe(3)
  rerender(view({ framingLocked: false, navigationCommand: { id: 4, type: 'fit' }, resetToken: 1 }))
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual([0, 0, 0, 1])
  expect(nv.scene.crosshairPos[2]).toBeCloseTo(23.5 / 31)
})

it('keeps the zoomed CT steady while choosing another slice on the slider', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<ToolbenchViewer {...base} />)
  const lock = screen.getByRole('button', { name: 'Lock framing' })
  await waitFor(() => expect(lock.disabled).toBe(false))
  const nv = harness.instances[0]
  const zoom = screen.getByRole('button', { name: 'Zoom in axial' })
  await user.click(zoom)
  const framing = Array.from(nv.scene.pan2Dxyzmm)
  expect(framing[3]).toBeCloseTo(1.2)
  await user.click(lock)
  expect(lock.getAttribute('aria-pressed')).toBe('true')
  expect(zoom.disabled).toBe(true)
  const slider = screen.getByRole('slider', { name: 'Axial slice' })
  fireEvent.change(slider, { target: { value: '8' } })
  await waitFor(() => expect(nv.scene.crosshairPos[2]).toBeCloseTo(8.5 / 31))
  await waitFor(() => expect(slider.getAttribute('aria-valuetext')).toBe('Slice 9 of 31'))
  fireEvent.change(slider, { target: { value: '13' } })
  await waitFor(() => expect(nv.scene.crosshairPos[2]).toBeCloseTo(13.5 / 31))
  await waitFor(() => expect(slider.getAttribute('aria-valuetext')).toBe('Slice 14 of 31'))
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(framing)
  rerender(<ToolbenchViewer {...base} caseData={{ case_id: 'OTHER', files: { ct: 'other.nii.gz' } }} />)
  expect(lock.getAttribute('aria-pressed')).toBe('false')
  await waitFor(() => expect(zoom.disabled).toBe(false))
})

it('turns canvas wheel gestures into anchored zoom in every 2D tool and blocks them when locked', async () => {
  harness.origin = [-342.55, -397.22, -16]
  const view = (interactionMode = 'navigate', framingLocked = false) =>
    <NiivueViewer {...base} wheelZoom interactionMode={interactionMode} framingLocked={framingLocked} />
  const { rerender } = render(view())
  const nv = harness.instances[0]
  expect(fireEvent.wheel(nv.canvas, { deltaY: -40 })).toBe(false)
  await screen.findByLabelText('Prepared result loaded')
  const crosshair = [...nv.scene.crosshairPos]
  const world = nv.frac2mm(crosshair)
  const projected = () => world.map((coordinate, axis) => coordinate * nv.scene.pan2Dxyzmm[3] + nv.scene.pan2Dxyzmm[axis])
  const anchor = projected()

  for (const mode of ['navigate', 'pan', 'window']) {
    rerender(view(mode))
    const zoom = nv.scene.pan2Dxyzmm[3]
    expect(fireEvent.wheel(nv.canvas, { deltaY: -40, deltaMode: 0 })).toBe(false)
    expect(nv.scene.pan2Dxyzmm[3]).toBeGreaterThan(zoom)
    projected().forEach((coordinate, axis) => expect(coordinate).toBeCloseTo(anchor[axis]))
    expect(fireEvent.wheel(nv.canvas, { deltaY: 40, ctrlKey: true })).toBe(false)
    expect(nv.scene.pan2Dxyzmm[3]).toBeCloseTo(zoom)
    expect([...nv.scene.crosshairPos]).toEqual(crosshair)
    projected().forEach((coordinate, axis) => expect(coordinate).toBeCloseTo(anchor[axis]))
  }

  const framing = [...nv.scene.pan2Dxyzmm]
  rerender(view('navigate', true))
  expect(fireEvent.wheel(nv.canvas, { deltaY: -100 })).toBe(false)
  expect([...nv.scene.pan2Dxyzmm]).toEqual(framing)
  expect([...nv.scene.crosshairPos]).toEqual(crosshair)
  expect(nv.nativeGesture).not.toHaveBeenCalled()
})

it('zooms touchscreen pinches without invoking native slice gestures and starts fresh after cancellation', async () => {
  const { rerender } = render(<NiivueViewer {...base} wheelZoom />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  const crosshair = [...nv.scene.crosshairPos]
  const touches = distance => [{ clientX: 0, clientY: 0 }, { clientX: distance, clientY: 0 }]

  fireEvent.touchStart(nv.canvas, { touches: touches(100) })
  fireEvent.touchMove(nv.canvas, { touches: touches(150) })
  expect(nv.scene.pan2Dxyzmm[3]).toBeCloseTo(1.5)
  fireEvent.touchCancel(nv.canvas, { touches: [] })
  fireEvent.touchStart(nv.canvas, { touches: touches(60) })
  expect(nv.scene.pan2Dxyzmm[3]).toBeCloseTo(1.5)
  fireEvent.touchMove(nv.canvas, { touches: touches(40) })
  expect(nv.scene.pan2Dxyzmm[3]).toBeCloseTo(1)
  fireEvent.touchEnd(nv.canvas, { touches: touches(40).slice(0, 1) })
  fireEvent.touchMove(nv.canvas, { touches: touches(40).slice(0, 1) })
  fireEvent.touchEnd(nv.canvas, { touches: [] })

  expect(fireEvent.keyDown(nv.canvas, { code: 'KeyJ', key: 'j' })).toBe(false)
  expect(fireEvent.keyDown(nv.canvas, { code: 'KeyU', key: 'u', ctrlKey: true })).toBe(false)
  expect(fireEvent.keyDown(nv.canvas, { code: 'ArrowRight', key: 'ArrowRight' })).toBe(false)
  expect(nv.nativeGesture).not.toHaveBeenCalled()
  expect([...nv.scene.crosshairPos]).toEqual(crosshair)

  rerender(<NiivueViewer {...base} wheelZoom framingLocked />)
  fireEvent.touchStart(nv.canvas, { touches: touches(75) })
  fireEvent.touchMove(nv.canvas, { touches: touches(125) })
  expect(nv.scene.pan2Dxyzmm[3]).toBeCloseTo(1)
  expect(nv.nativeGesture).not.toHaveBeenCalled()
  expect([...nv.scene.crosshairPos]).toEqual(crosshair)
  fireEvent.touchEnd(nv.canvas, { touches: [] })
  fireEvent.touchStart(nv.canvas, { touches: touches(75).slice(0, 1) })
  expect(nv.nativeGesture).toHaveBeenCalledOnce()
})

it('keeps the 3D cut fixed during rotation and zoom', async () => {
  const view = (depth, navigationCommand = null) => <NiivueViewer {...base} mode="3d" wheelZoom
    clip={{ enabled: true, depth }} navigationCommand={navigationCommand} />
  const { rerender } = render(view(2))
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  expect(nv.scene.renderAzimuth).toBe(180)
  expect(nv.opts.mouseEventConfig).toEqual({
    leftButton: { primary: 8, withShift: 0, withCtrl: 8 }, rightButton: 0, centerButton: 0,
  })
  expect(nv.opts.touchEventConfig).toEqual({ singleTouch: 8, doubleTouch: 0 })
  const setClipPlane = vi.spyOn(nv, 'setClipPlane')
  const initialScale = nv.scene.volScaleMultiplier

  rerender(view(-0.15))
  await waitFor(() => expect(setClipPlane).toHaveBeenLastCalledWith([-0.15, 0, 0]))
  setClipPlane.mockClear()
  nv.nativeGesture.mockImplementation(() => nv.setClipPlane([0, 0, 0]))
  expect(fireEvent.keyUp(nv.canvas, { code: 'KeyC' })).toBe(false)
  expect(fireEvent.keyUp(nv.canvas, { code: 'KeyP' })).toBe(false)
  expect(fireEvent.touchMove(nv.canvas, { touches: [{ clientX: 12, clientY: 24 }] })).toBe(false)
  expect(nv.mouseMove).toHaveBeenCalledWith(12, 24)
  expect(fireEvent.wheel(nv.canvas, { deltaY: -60 })).toBe(false)
  expect(nv.scene.volScaleMultiplier).toBeGreaterThan(initialScale)
  expect(fireEvent.wheel(nv.canvas, { deltaY: 60, ctrlKey: true })).toBe(false)
  expect(nv.scene.volScaleMultiplier).toBeCloseTo(initialScale)
  expect(nv.scene.pan2Dxyzmm[3]).toBe(1)

  const touches = distance => [{ clientX: 0, clientY: 0 }, { clientX: distance, clientY: 0 }]
  fireEvent.touchStart(nv.canvas, { touches: touches(10) })
  fireEvent.touchMove(nv.canvas, { touches: touches(100) })
  expect(nv.scene.volScaleMultiplier).toBe(4)
  fireEvent.touchEnd(nv.canvas, { touches: [] })
  rerender(view(-0.15, { id: 1, type: 'zoom', factor: 0.01 }))
  expect(nv.scene.volScaleMultiplier).toBe(0.45)
  expect(nv.scene.clipPlane).toEqual([-0.15, 0, 0])
  expect(setClipPlane).not.toHaveBeenCalled()
  expect(nv.nativeGesture).not.toHaveBeenCalled()
})

it('reverses the peel at its existing depth and calculates the pancreas shortcut for each entry side', async () => {
  const onPeelReveal = vi.fn()
  const view = azimuth => <NiivueViewer {...anatomyProps} mode="3d" onPeelReveal={onPeelReveal}
    clip={{ enabled: true, depth: -0.2, azimuth }} />
  const { rerender } = render(view(0))
  const nv = harness.instances[0]
  nv.sceneExtentsMinMax = () => [[0, -50, 0], [100, 50, 100], [100, 100, 100]]
  const loadMeshes = nv.loadMeshes.getMockImplementation()
  nv.loadMeshes.mockImplementation(async specs => {
    await loadMeshes(specs)
    Object.assign(nv.meshes[0], { extentsMin: [0, -8, 0], extentsMax: [10, 19, 10] })
  })
  await screen.findByLabelText('Prepared result loaded')
  expect(onPeelReveal).toHaveBeenCalledExactlyOnceWith({ frontToBack: 34, backToFront: 45 })
  expect(nv.scene.clipPlane).toEqual([-0.2, 0, 0])
  nv.setRenderAzimuthElevation(35, 22)
  nv.setScale(2)

  rerender(view(180))
  await waitFor(() => expect(nv.scene.clipPlane).toEqual([-0.2, 180, 0]))
  expect(nv.scene.renderAzimuth).toBe(35)
  expect(nv.scene.renderElevation).toBe(22)
  expect(nv.scene.volScaleMultiplier).toBe(2)
  expect(nv.loadVolumes).toHaveBeenCalledOnce()
})

it.each([
  ['axial', 0, 45, [112, -97, 14, 2]],
  ['coronal', 1, -45, [-88, 13, -96, 2]],
  ['sagittal', 2, 45, [12, 113, -96, 2]],
])('pans the %s image from its margin, without changing slice or zoom', async (activePlane, axCorSag, horizontalFov, expected) => {
  const onSelectObject = vi.fn()
  render(<NiivueViewer {...base} activePlane={activePlane} wheelZoom interactionMode="pan" onSelectObject={onSelectObject} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.canvas.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 100 })
  nv.canvas.width = 200
  nv.canvas.height = 200
  nv.screenSlices = [{ axCorSag, leftTopWidthHeight: [60, 45, 90, 120], fovMM: [horizontalFov, 60] }]
  nv.setPan2Dxyzmm([12, 13, 14, 2])
  const beforeSlice = Array.from(nv.scene.crosshairPos)
  const pointer = (type, clientX, clientY) => fireEvent(nv.canvas, new MouseEvent(type, {
    bubbles: true, cancelable: true, button: 0, clientX, clientY,
  }))
  pointer('pointerdown', 15, 20)
  pointer('pointermove', 35, 30)
  pointer('pointermove', 65, 75)
  pointer('pointerup', 65, 75)
  expect(Array.from(nv.scene.pan2Dxyzmm)).toEqual(expected)
  expect(Array.from(nv.scene.crosshairPos)).toEqual(beforeSlice)
  expect(onSelectObject).not.toHaveBeenCalled()
  expect(pointer('mousedown', 20, 20)).toBe(false)

  const touch = [{ clientX: 60, clientY: 55 }]
  expect(fireEvent.touchStart(nv.canvas, { touches: touch })).toBe(false)
  expect(fireEvent.touchMove(nv.canvas, { touches: touch })).toBe(false)
  expect(nv.nativeGesture).not.toHaveBeenCalled()
  expect(fireEvent.wheel(nv.canvas, { deltaY: -60, clientX: 65, clientY: 75 })).toBe(false)
  expect(nv.scene.pan2Dxyzmm[3]).toBeGreaterThan(2)
  expect(Array.from(nv.scene.crosshairPos)).toEqual(beforeSlice)
})

it('pans the 3D camera while preserving angles, zoom, peel and click selection', async () => {
  const onSelectObject = vi.fn()
  render(<NiivueViewer {...base} mode="3d" wheelZoom interactionMode="pan"
    onSelectObject={onSelectObject} clip={{ enabled: true, depth: -0.2, azimuth: 180 }} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.canvas.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 100 })
  nv.canvas.width = 200
  nv.canvas.height = 200
  nv.screenSlices = [{ axCorSag: nv.sliceTypeRender, leftTopWidthHeight: [0, 0, 200, 200] }]
  nv.pivot3D = [0, 0, 0]
  nv.setRenderAzimuthElevation(35, 22)
  nv.setScale(2)

  const pointer = (type, clientX, clientY) => fireEvent(nv.canvas, new MouseEvent(type, {
    bubbles: true, cancelable: true, button: 0, clientX, clientY,
  }))
  pointer('pointerdown', 40, 40)
  pointer('pointermove', 60, 55)
  pointer('pointerup', 60, 55)
  expect(nv.pivot3D[0]).toBeCloseTo(-0.4)
  expect(nv.pivot3D[1]).toBeCloseTo(0.3)
  expect(nv.pivot3D[2]).toBe(0)
  expect(nv.scene.renderAzimuth).toBe(35)
  expect(nv.scene.renderElevation).toBe(22)
  expect(nv.scene.volScaleMultiplier).toBe(2)
  expect(nv.scene.clipPlane).toEqual([-0.2, 180, 0])
  expect(onSelectObject).not.toHaveBeenCalled()

  const touch = [{ clientX: 60, clientY: 55 }]
  expect(fireEvent.touchStart(nv.canvas, { touches: touch })).toBe(false)
  expect(fireEvent.touchMove(nv.canvas, { touches: touch })).toBe(false)
  expect(nv.nativeGesture).not.toHaveBeenCalled()
  expect(nv.mouseMove).not.toHaveBeenCalled()

  pointer('pointerdown', 40, 40)
  pointer('pointerup', 40, 40)
  await waitFor(() => expect(onSelectObject).toHaveBeenCalledExactlyOnceWith(null))
})

it.each([{}, { mode: '3d' }])('preserves native wheel input outside opted-in viewers %#', async (options) => {
  render(<NiivueViewer {...base} {...options} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  expect(fireEvent.wheel(nv.canvas, { deltaY: -40 })).toBe(true)
  expect(nv.nativeGesture).toHaveBeenCalledOnce()
  expect(nv.scene.pan2Dxyzmm[3]).toBe(1)
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

it('jumps to the measured physical slice and tracks its calipers through redraw and resize', async () => {
  harness.origin = [-55, -70, -100]
  harness.spacing = [2, 3, 4]
  const props = { ...base, sources: ['pred'], caseData: { ...caseData, files: { ...caseData.files, pred: 'synthetic-pred.nii.gz' } } }
  const { rerender } = render(<NiivueViewer {...props} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  let size = 240
  for (const prop of ['clientWidth', 'clientHeight', 'offsetWidth', 'offsetHeight']) {
    Object.defineProperty(nv.canvas, prop, { configurable: true, get: () => size })
  }
  nv.canvas.width = 240
  nv.canvas.height = 240
  nv.drawScene.mockImplementation(() => {
    const [panX, panY, , zoom] = nv.scene.pan2Dxyzmm
    nv.screenSlices = [{ axCorSag: 0, sliceFrac: nv.scene.crosshairPos[2], leftTopWidthHeight: [0, 0, nv.canvas.width, nv.canvas.height],
      leftTopMM: [(-60 - panX) / zoom, (-80 - panY) / zoom], fovMM: [30 / zoom, 60 / zoom] }]
  })
  const anchorWorldMm = [-45, -40, -72]
  const measurementCalipers = { plane: 'axial', anchorWorldMm, axes: [
    { lengthMm: 8, worldEndpointsMm: [[-49, -40, -72], [-41, -40, -72]] },
    { lengthMm: 12, worldEndpointsMm: [[-45, -46, -72], [-45, -34, -72]] },
  ] }
  const command = { type: 'measurement-point', id: 10, worldMm: anchorWorldMm }
  const inspect = options => <NiivueViewer {...props} measurementCalipers={measurementCalipers} navigationCommand={command} {...options} />
  rerender(inspect())
  expect(nv.scene.crosshairPos[2]).toBeCloseTo(7.5 / 31)
  const overlay = screen.getByRole('img', { name: /Lesion calipers/ })
  expect(overlay.textContent).toContain('0.80 cm')
  expect(overlay.textContent).toContain('1.20 cm')
  const drawPath = () => screen.getByRole('img', { name: /Lesion calipers/ }).querySelector('[data-caliper-arm="0"]').getAttribute('d')
  const before = drawPath()
  act(() => { nv.scene.pan2Dxyzmm = new Float32Array([45, 40, 0, 2]); nv.drawScene() })
  expect(drawPath()).not.toBe(before)
  const afterZoom = drawPath()
  size = 480
  act(() => harness.observers.at(-1).callback())
  await waitFor(() => expect(drawPath()).not.toBe(afterZoom))
  rerender(inspect({ navigationCommand: { id: 11, type: 'slice', plane: 'axial', index: 8 } }))
  expect(screen.queryByRole('img', { name: /Lesion calipers/ })).toBeNull()
  rerender(inspect({ navigationCommand: { ...command, id: 12 } }))
  expect(screen.getByRole('img', { name: /Lesion calipers/ })).toBeTruthy()
  const pancreasProps = { measurementAnatomy: 'pancreas', showLesion: false, navigationCommand: { ...command, id: 13 } }
  rerender(inspect(pancreasProps))
  expect(screen.getByRole('img', { name: 'Pancreas calipers: 0.80 cm by 1.20 cm' })).toBeTruthy()
  expect(screen.queryByRole('img', { name: /Lesion calipers/ })).toBeNull()
  rerender(inspect({ ...pancreasProps, showPancreas: false, showLesion: true }))
  expect(screen.queryByRole('img', { name: /Pancreas calipers/ })).toBeNull()
  rerender(inspect({ ...pancreasProps, visibleSources: [] }))
  expect(screen.queryByRole('img', { name: /Pancreas calipers/ })).toBeNull()
  rerender(inspect({ ...pancreasProps, differenceMode: true }))
  expect(screen.queryByRole('img', { name: /Pancreas calipers/ })).toBeNull()
  rerender(inspect({ caseData: { case_id: 'OTHER', files: { ct: 'other.nii.gz', pred: 'other-mask.nii.gz' } }, measurementCalipers: null }))
  expect(screen.queryByRole('img', { name: /Lesion calipers/ })).toBeNull()
  await screen.findByLabelText('Prepared result loaded')
  expect(screen.queryByRole('img', { name: /Lesion calipers/ })).toBeNull()
})

it('projects only onto the matching anatomical plane and follows radiological mirroring at high DPI', () => {
  const calipers = { plane: 'coronal', anchorWorldMm: [2, 3, 2], axes: [
    { lengthMm: 4, worldEndpointsMm: [[0, 3, 2], [4, 3, 2]] },
    { lengthMm: 2, worldEndpointsMm: [[2, 3, 1], [2, 3, 3]] },
  ] }
  const mirrored = { axCorSag: 1, sliceFrac: .35, leftTopWidthHeight: [0, 0, 400, 300],
    leftTopMM: [10, 0], fovMM: [-10, 10] }
  const nv = {
    canvas: { width: 400, height: 300, clientWidth: 200, clientHeight: 150 },
    volumes: [{ dimsRAS: [3, 10, 10, 10] }],
    mm2frac: (point, _, forceWorld) => { expect(forceWorld).toBe(true); return point.map(v => (v + .5) / 10) },
    frac2mm: point => point.map(v => v * 10 - .5),
    screenSlices: [{ ...mirrored, axCorSag: 0 }, mirrored],
  }
  expect(projectCalipers(nv, calipers).lines[0].points).toEqual([[200, 120], [120, 120]])
  expect(projectCalipers(nv, { ...calipers, plane: null })).toBeNull()
  expect(projectCalipers(nv, { ...calipers, axes: [calipers.axes[0], { ...calipers.axes[1], worldEndpointsMm: [[2, 3, 1], [2, 3.1, 3]] }] })).toBeNull()
  mirrored.sliceFrac = .45
  expect(projectCalipers(nv, calipers)).toBeNull()
})

it('binds a 3D surface pick to a lesion voxel along the ray and projects its marker through orbit redraws', async () => {
  harness.origin = [-5, -10, -15]
  const onSelectObject = vi.fn()
  const props = {
    ...base, mode: '3d', sources: ['pred'], onSelectObject,
    caseData: { ...caseData, files: { ...caseData.files, pred: 'synthetic-pred.nii.gz', mesh: { lesion_pred: 'synthetic-lesion.obj' } } },
  }
  const { rerender } = render(<NiivueViewer {...props} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  for (const name of ['clientWidth', 'clientHeight', 'width', 'height']) {
    Object.defineProperty(nv.canvas, name, { configurable: true, value: 100 })
  }
  // A synthetic displaced vertex marks the click location, but it is not
  // inside the mask itself. The validated click ray reaches this label voxel.
  nv.volumes[1].img[5 + 11 * (10 + 21 * 15)] = 2
  nv.screenSlices = [{ axCorSag: 4, leftTopWidthHeight: [0, 0, 100, 100] }]
  function click() {
    for (const type of ['pointerdown', 'pointerup']) nv.canvas.dispatchEvent(new MouseEvent(type, { bubbles: true, clientX: 62, clientY: 50 }))
  }
  act(click)
  await waitFor(() => expect(onSelectObject).toHaveBeenLastCalledWith({ source: 'pred', anatomy: 'lesion', worldMm: [0, 0, 0] }))
  const worldMm = onSelectObject.mock.lastCall[0].worldMm
  rerender(<NiivueViewer {...props} selectedLesionWorldMm={worldMm} />)
  const markerX = () => screen.getByRole('img', { name: 'Selected predicted lesion marker' }).querySelector('circle').getAttribute('cx')
  expect(markerX()).toBe('50')
  act(() => {
    nv.calculateMvpMatrix.mockReturnValue([[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, .4, 0, 0, 1]])
    nv.drawScene()
  })
  expect(markerX()).toBe('70')
  const measurementCalipers = { plane: 'axial', anchorWorldMm: worldMm, axes: [
    { lengthMm: 1, worldEndpointsMm: [[-.5, 0, 0], [.5, 0, 0]] },
    { lengthMm: 1, worldEndpointsMm: [[0, -.5, 0], [0, .5, 0]] },
  ] }
  const caliperView = changes => <NiivueViewer {...props} selectedLesionWorldMm={worldMm}
    measurementCalipers={measurementCalipers} {...changes} />
  rerender(caliperView())
  expect(screen.queryByRole('img', { name: 'Selected predicted lesion marker' })).toBeNull()
  const crossName = { name: '3D lesion calipers from the measured CT slice: 0.10 cm by 0.10 cm' }
  const arms = () => Array.from(screen.getByRole('img', crossName).querySelectorAll('[data-caliper-arm]'),
    arm => arm.getAttribute('d'))
  const beforeOrbit = arms()
  expect(beforeOrbit).toHaveLength(2)
  act(() => {
    // The native axial cross would be edge-on from the front.
    nv.calculateMvpMatrix.mockReturnValue([[1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1]])
    nv.drawScene()
  })
  const [[x1, y1, x2, y2], [x3, y3, x4, y4]] = arms().map(path => path.split(' ').slice(0, 6)
    .filter(value => value !== 'M' && value !== 'L').map(Number))
  expect(y1).toBe(y2)
  expect(x3).toBe(x4)
  expect(Math.abs(x2 - x1)).toBe(50)
  expect(Math.abs(y4 - y3)).toBe(50)
  rerender(caliperView({ showLesion: false }))
  expect(screen.queryByRole('img', crossName)).toBeNull()
  rerender(caliperView({ measurementCalipers: null }))
  expect(screen.queryByRole('img', crossName)).toBeNull()
  expect(markerX()).toBe('50')
})

it('treats a 3D background click as a miss instead of selecting near a previous crosshair', async () => {
  const onSelectObject = vi.fn()
  render(<NiivueViewer {...anatomyProps} mode="3d" onSelectObject={onSelectObject} />)
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  // There is no mesh ray hit. The nearest-vertex test should only run for
  // coordinates produced by this click's depth picker.
  nv.indexNearestXYZmm = vi.fn(id => [0, id + 1])
  function click() {
    for (const type of ['pointerdown', 'pointerup']) nv.canvas.dispatchEvent(new MouseEvent(type, { bubbles: true, clientX: 50, clientY: 50 }))
  }
  act(click)
  await waitFor(() => expect(onSelectObject).toHaveBeenLastCalledWith(null))
  expect(nv.indexNearestXYZmm).not.toHaveBeenCalled()

  nv.resetBriCon = () => { nv.scene.crosshairPos = new Float32Array([.5, .5, .5]) }
  act(click)
  await waitFor(() => expect(onSelectObject).toHaveBeenLastCalledWith({ source: 'pred', anatomy: 'pancreas' }))
  expect(nv.indexNearestXYZmm).toHaveBeenCalledWith(0, 5, 10, 15)
})

it('keys full-volume scenes by the CT they load and preserves existing 2D and source keys', () => {
  const study = { ...caseData, files: { ...caseData.files, ct_full: 'synthetic-abdomen.nii.gz' } }
  const nativeStudy = { ...study, files: { ...study.files, ct_full_native: 'synthetic-native-abdomen.nii.gz' } }
  const key = (caseData, options) => viewerSceneKey({ caseData, showFull: true, ...options })
  expect(key(nativeStudy, { mode: '3d' })).not.toBe(key(study, { mode: '3d' }))
  for (const options of [
    { mode: '2d' },
    { mode: '3d', showFull: false },
    { mode: '3d', preferNativeFull: false },
    { mode: '3d', assetUrls: { ct: 'blob:synthetic-source' } },
  ]) {
    expect(key(nativeStudy, options)).toBe(key(study, options))
  }
})

it('uses the native full CT in 3D while preserving separate framing and world crosshair positions', async () => {
  const study = { ...caseData, files: { ...caseData.files,
    ct_full: 'synthetic-abdomen.nii.gz', ct_full_native: 'synthetic-native-abdomen.nii.gz' } }
  const imageDetails = { kind: 'prepared', legacyMillimeters: true }
  const view = (showFull, options = {}) => <NiivueViewer {...base} caseData={study} mode="3d" showFull={showFull}
    sceneLabel={showFull ? 'Abdomen · 3D' : 'Pancreas region · 3D'} imageDetails={imageDetails} {...options} />
  const { rerender } = render(view(false))
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  const point = [3, 7, 12]
  function moveCrosshair(world) {
    nv.scene.crosshairPos = new Float32Array(nv.mm2frac(world))
  }
  function expectCrosshair(world) {
    nv.frac2mm(nv.scene.crosshairPos).forEach((position, axis) => expect(position).toBeCloseTo(world[axis]))
  }
  nv.setRenderAzimuthElevation(64, 16)
  nv.setScale(2.6)
  moveCrosshair(point)

  expect(screen.getByText('1 × 1 × 1 mm voxels')).toBeTruthy()
  harness.origin = [-2, -3, -5]
  harness.spacing = [.86, .86, 2.5]
  rerender(view(true))
  expect(screen.queryByText('1 × 1 × 1 mm voxels')).toBeNull()
  await waitFor(() => expect(nv.loadVolumes).toHaveBeenCalledTimes(2))
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.volumes[0].url).toBe('/cases/synthetic-native-abdomen.nii.gz')
  expect(screen.getByText('0.86 × 0.86 × 2.5 mm voxels')).toBeTruthy()
  expect(nv.scene.volScaleMultiplier).toBe(1)
  expect(nv.scene.renderAzimuth).not.toBe(64)
  expectCrosshair(point)

  nv.setRenderAzimuthElevation(108, 25)
  nv.setScale(1.6)
  moveCrosshair([4, 8, 13])
  harness.origin = [0, 0, 0]
  harness.spacing = [1, 1, 1]
  rerender(view(false))
  await waitFor(() => expect(nv.loadVolumes).toHaveBeenCalledTimes(3))
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.volumes[0].url).toBe('/cases/synthetic-only.nii.gz')
  expect(nv.scene.volScaleMultiplier).toBe(2.6)
  expect(nv.scene.renderAzimuth).toBe(64)
  expectCrosshair([4, 8, 13])

  harness.origin = [-2, -3, -5]
  harness.spacing = [.86, .86, 2.5]
  rerender(view(true))
  await waitFor(() => expect(nv.loadVolumes).toHaveBeenCalledTimes(4))
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.scene.volScaleMultiplier).toBe(1.6)
  expect(nv.scene.renderAzimuth).toBe(108)

  rerender(view(true, { mode: '2d', sceneLabel: null, imageDetails: null }))
  await waitFor(() => expect(nv.loadVolumes).toHaveBeenCalledTimes(5))
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.volumes[0].url).toBe('/cases/synthetic-abdomen.nii.gz')

  rerender(view(true, { preferNativeFull: false, sceneLabel: null, imageDetails: null }))
  await waitFor(() => expect(nv.loadVolumes).toHaveBeenCalledTimes(6))
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.volumes[0].url).toBe('/cases/synthetic-abdomen.nii.gz')
})

it('retains the 3D source CT camera when its prediction mesh arrives', async () => {
  const study = { ...caseData, files: { ...caseData.files,
    pred: 'synthetic-source-pred.nii.gz', ct_full_native: 'synthetic-native-abdomen.nii.gz' } }
  const assetUrls = { ct: 'blob:synthetic-source', pred: 'blob:synthetic-source-pred' }
  let handle
  const onViewHandle = next => { handle = next }
  const view = urls => <NiivueViewer {...base} caseData={study} assetUrls={urls} sources={['pred']} mode="3d" showFull onViewHandle={onViewHandle} />
  const { rerender } = render(view(assetUrls))
  await screen.findByLabelText('Prepared result loaded')
  const nv = harness.instances[0]
  nv.setRenderAzimuthElevation(73, -17)
  nv.setScale(1.9)
  const camera = handle.capture()

  rerender(view({ ...assetUrls, mesh: { pancreas_pred: 'blob:synthetic-pancreas' } }))
  await waitFor(() => expect(nv.loadMeshes).toHaveBeenCalledOnce())
  await screen.findByLabelText('Prepared result loaded')
  expect(nv.volumes[0].url).toBe(assetUrls.ct)
  expect(nv.scene.volScaleMultiplier).toBe(1.9)
  expect(nv.scene.renderAzimuth).toBe(73)
  expect(nv.scene.renderElevation).toBe(-17)
  nv.setScale(1.2)
  expect(handle.restore(camera)).toBe(true)
  expect(nv.scene.volScaleMultiplier).toBe(1.9)
})
