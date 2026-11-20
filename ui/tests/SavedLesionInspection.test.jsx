import React from 'react'
import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import SavedPredictionView from '../src/components/SavedPredictionView.jsx'
import { loadSavedPrediction } from '../src/lib/savedPrediction.js'
import { measureMask } from '../src/lib/scanMeasurements.js'

vi.mock('../src/lib/savedPrediction.js', () => ({ loadSavedPrediction: vi.fn() }))
vi.mock('../src/components/NiivueViewer.jsx', () => ({
  default: ({ activePlane, measurementCalipers, navigationCommand, showLesion, label, mode, showFull, interactionMode, assetUrls }) =>
    <output aria-label={label}>{JSON.stringify({ activePlane, measurementCalipers, navigationCommand, showLesion, mode, showFull, interactionMode,
      ctUrl: assetUrls?.ct, meshes: assetUrls?.mesh })}</output>,
}))

const ctSha256 = 'a'.repeat(64)
const predictionSha256 = 'b'.repeat(64)

function prediction(caseId, offset = 0) {
  const affine = [[2, 0, 0, offset], [0, 0, -4, 10], [0, 3, 0, 1], [0, 0, 0, 1]]
  const header = { dims: [3, 8, 8, 8, 1, 1, 1, 1], affine, xyzt_units: 2, sform_code: 1 }
  const labels = new Uint8Array(8 ** 3)
  const index = (x, y, z) => x + 8 * (y + 8 * z)
  labels[index(1, 1, 1)] = 1
  labels[index(2, 2, 2)] = labels[index(2, 3, 2)] = 2
  return {
    manifest: { case_id: caseId, result_sha256: caseId, model_sha256: {}, warnings: [], geometry: {},
      files: { ct: { content_sha256: ctSha256 }, pred: { content_sha256: predictionSha256 } } },
    manifestHash: caseId, urls: {}, release: vi.fn(),
    measurement: { ...measureMask(header, header, labels), status: 'ready',
      schema: 'native-mask-volume-v1', ctSha256, predictionSha256 },
  }
}

const viewer = caseId => JSON.parse(screen.getByLabelText(`Saved CT and prediction for ${caseId}`).textContent)
const inspect = user => user.click(screen.getByRole('button', { name: 'Inspect measurement for lesion 1' }))

beforeEach(() => {
  loadSavedPrediction.mockReset()
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ packages: [], history: [] }))))
})

it.each([false, true])('opens the exact measurement slice for both saved and live results (live=%s)', async live => {
  const user = userEvent.setup()
  const result = prediction('A')
  loadSavedPrediction.mockResolvedValue(result)
  render(<SavedPredictionView live={live} />)
  await screen.findByLabelText('Saved CT and prediction for A')
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: true, mode: '3d', showFull: true, interactionMode: 'rotate' })
  const pan = screen.getByRole('button', { name: 'Pan', exact: true })
  await user.click(pan)
  expect(viewer('A').interactionMode).toBe('pan')

  await user.click(screen.getByRole('checkbox', { name: 'Predicted lesion' }))
  await inspect(user)
  const calipers = result.measurement.lesionDimensions.components[0].calipers
  expect(viewer('A')).toMatchObject({
    activePlane: 'coronal', showLesion: true, measurementCalipers: calipers,
    mode: '2d', showFull: false, interactionMode: 'pan',
    navigationCommand: { id: 1, type: 'measurement-point', plane: 'coronal', worldMm: [4, 2, 7] },
  })
  expect(within(screen.getByRole('region', { name: 'Predicted lesion dimensions' })).getByText('Selected')).toBeTruthy()
  expect(screen.getByText('Inspecting the lesion measurement on the coronal CT plane.')).toBeTruthy()

  await inspect(user)
  expect(viewer('A').navigationCommand.id).toBe(2)
  await user.click(screen.getByRole('button', { name: 'Return to all planes' }))
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: true, mode: '2d', showFull: false, interactionMode: 'pan' })
  await inspect(user)
  await user.click(screen.getByRole('checkbox', { name: 'Predicted lesion' }))
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: false, mode: '2d', showFull: false, interactionMode: 'pan' })
  await user.click(screen.getByRole('button', { name: '3D Abdomen' }))
  expect(viewer('A')).toMatchObject({ mode: '3d', showFull: true, interactionMode: 'pan' })
})

it('clears inspection on reload and never carries calipers to another result', async () => {
  const user = userEvent.setup()
  const a = prediction('A')
  const next = prediction('A', 20)
  const b = prediction('B', 40)
  loadSavedPrediction.mockResolvedValueOnce(a).mockResolvedValueOnce(next).mockResolvedValueOnce(b)
  const { rerender } = render(<SavedPredictionView base="/a" />)
  await screen.findByLabelText('Saved CT and prediction for A')
  await inspect(user)
  expect(viewer('A').navigationCommand.worldMm).toEqual([4, 2, 7])
  await user.click(screen.getByRole('button', { name: 'Reload saved package' }))
  await screen.findByLabelText('Saved CT and prediction for A')
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: true, mode: '3d', showFull: true, interactionMode: 'rotate' })
  await inspect(user)
  expect(viewer('A').navigationCommand.worldMm).toEqual([24, 2, 7])

  rerender(<SavedPredictionView base="/b" />)
  expect(screen.queryByLabelText('Saved CT and prediction for A')).toBeNull()
  await screen.findByLabelText('Saved CT and prediction for B')
  expect(viewer('B')).toEqual({ activePlane: 'multiplanar', showLesion: true, mode: '3d', showFull: true, interactionMode: 'rotate' })
})

it('keeps the archive CT visible while deriving matching 3D surfaces and releases generated meshes on exit', async () => {
  const workers = []
  vi.stubGlobal('Worker', class {
    postMessage = vi.fn()
    terminate = vi.fn()
    constructor() { workers.push(this) }
  })
  const createObjectURL = vi.fn(() => 'blob:derived-pancreas')
  const revokeObjectURL = vi.fn()
  vi.stubGlobal('URL', class extends URL {
    static createObjectURL = createObjectURL
    static revokeObjectURL = revokeObjectURL
  })
  const result = prediction('A')
  result.urls = { ct: 'blob:verified-ct', pred: 'blob:verified-prediction' }
  result.manifest.files.pred.bytes = 42
  loadSavedPrediction.mockResolvedValue(result)
  const { unmount } = render(<SavedPredictionView />)
  await screen.findByLabelText('Saved CT and prediction for A')
  expect(viewer('A')).toMatchObject({ mode: '3d', showFull: true, ctUrl: result.urls.ct })
  expect(viewer('A').meshes).toBeUndefined()
  expect(workers[0].postMessage).toHaveBeenCalledWith({
    url: result.urls.pred, bytes: 42, geometry: result.manifest.geometry,
  })
  act(() => workers[0].onmessage({ data: { surfaces: { pancreas_pred: new ArrayBuffer(1) } } }))
  expect(viewer('A')).toMatchObject({ ctUrl: result.urls.ct, meshes: { pancreas_pred: 'blob:derived-pancreas' } })
  unmount()
  expect(revokeObjectURL).toHaveBeenCalledWith('blob:derived-pancreas')
  expect(result.release).toHaveBeenCalledOnce()
})
