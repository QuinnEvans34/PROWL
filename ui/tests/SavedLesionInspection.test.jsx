import React from 'react'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import SavedPredictionView from '../src/components/SavedPredictionView.jsx'
import { loadSavedPrediction } from '../src/lib/savedPrediction.js'
import { measureMask } from '../src/lib/scanMeasurements.js'

vi.mock('../src/lib/savedPrediction.js', () => ({ loadSavedPrediction: vi.fn() }))
vi.mock('../src/components/NiivueViewer.jsx', () => ({
  default: ({ activePlane, measurementCalipers, navigationCommand, showLesion, label }) =>
    <output aria-label={label}>{JSON.stringify({ activePlane, measurementCalipers, navigationCommand, showLesion })}</output>,
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
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: true })

  await user.click(screen.getByRole('checkbox', { name: 'Predicted lesion' }))
  await inspect(user)
  const calipers = result.measurement.lesionDimensions.components[0].calipers
  expect(viewer('A')).toMatchObject({
    activePlane: 'coronal', showLesion: true, measurementCalipers: calipers,
    navigationCommand: { id: 1, type: 'measurement-point', plane: 'coronal', worldMm: [4, 2, 7] },
  })
  expect(within(screen.getByRole('region', { name: 'Predicted lesion dimensions' })).getByText('Selected')).toBeTruthy()
  expect(screen.getByText('Inspecting the lesion measurement on the coronal CT plane.')).toBeTruthy()

  await inspect(user)
  expect(viewer('A').navigationCommand.id).toBe(2)
  await user.click(screen.getByRole('button', { name: 'Return to all planes' }))
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: true })
  await inspect(user)
  await user.click(screen.getByRole('checkbox', { name: 'Predicted lesion' }))
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: false })
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
  expect(viewer('A')).toEqual({ activePlane: 'multiplanar', showLesion: true })
  await inspect(user)
  expect(viewer('A').navigationCommand.worldMm).toEqual([24, 2, 7])

  rerender(<SavedPredictionView base="/b" />)
  expect(screen.queryByLabelText('Saved CT and prediction for A')).toBeNull()
  await screen.findByLabelText('Saved CT and prediction for B')
  expect(viewer('B')).toEqual({ activePlane: 'multiplanar', showLesion: true })
})
