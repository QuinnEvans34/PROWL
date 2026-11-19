import { act, fireEvent, render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import ImagingViewportDetails from '../src/components/ImagingViewportDetails.jsx'
import InspectionSourceControls from '../src/components/InspectionSourceControls.jsx'

it('updates the drawn scale and calibrated window without keeping details from another scene', () => {
  const draw = vi.fn(() => 'frame')
  const viewer = {
    drawSceneCore: draw,
    canvas: { width: 480, clientWidth: 240 },
    volumes: [{ hdr: { affine: [[2, 0, 0, 0], [0, 3, 0, 0], [0, 0, 4, 0], [0, 0, 0, 1]], xyzt_units: 2 },
      cal_min: -100, cal_max: 300 }],
    screenSlices: [{ axCorSag: 0, leftTopWidthHeight: [0, 0, 480, 240], fovMM: [120, 120], sliceFrac: 0.45 }],
  }
  const nvRef = { current: viewer }
  const loadedSceneKeyRef = { current: 'study1' }
  const source = { kind: 'source', series: 'Abdomen CT', calibratedHu: true }
  const view = sceneKey => <ImagingViewportDetails {...{ nvRef, loadedSceneKeyRef, sceneKey, source }} ready plane="axial" />
  const { rerender, unmount } = render(view('study1'))
  expect(screen.getByText('W 400 · L 100 HU')).toBeTruthy()
  expect(screen.getByRole('img', { name: 'Physical scale 50 millimeters' })).toBeTruthy()
  viewer.volumes[0].cal_max = 500
  viewer.screenSlices[0].fovMM[0] = 60
  act(() => { expect(viewer.drawSceneCore()).toBe('frame') })
  expect(screen.getByText('W 600 · L 200 HU')).toBeTruthy()
  expect(screen.getByRole('img', { name: 'Physical scale 20 millimeters' })).toBeTruthy()
  rerender(view('study2'))
  expect(screen.queryByRole('group', { name: 'CT image details' })).toBeNull()
  unmount()
  expect(viewer.drawSceneCore).toBe(draw)
})

it('offers source selection only when both CT views belong to the active result', () => {
  const onSourceChange = vi.fn()
  const view = props => <InspectionSourceControls onSourceChange={onSourceChange} {...props} />
  const { rerender } = render(view({ sourceAvailable: false }))
  expect(screen.getByText('Source CT unavailable for this prediction')).toBeTruthy()
  expect(screen.queryByRole('button', { name: 'Source CT' })).toBeNull()
  rerender(view({ sourceAvailable: true }))
  fireEvent.click(screen.getByRole('button', { name: 'Source CT' }))
  expect(onSourceChange).toHaveBeenCalledWith('source')
  rerender(view({ sourceAvailable: true, sourcePending: true }))
  expect(screen.getByRole('button', { name: 'Source CT' }).disabled).toBe(true)
  expect(screen.getByRole('status').textContent).toBe('Loading source CT…')
  rerender(view({ sourceAvailable: true, preparedAvailable: false, activeSource: 'source' }))
  expect(screen.getByText('Source CT')).toBeTruthy()
  expect(screen.queryByRole('button', { name: 'Prepared CT' })).toBeNull()
})
