import React from 'react'
import { it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import NativeMeasurementPanel from '../src/components/NativeMeasurementPanel.jsx'
const m = { status: 'ready', pancreasMl: 44, lesionMl: 2, lesionVoxels: 4, modelSha256: { localizer: 'a', segmenter: 'b' }, coverage: 'Anatomical completeness remains unverified' }
it('answers from native measurements and exposes evidence', async () => {
  const user=userEvent.setup(); render(<NativeMeasurementPanel measurement={m} />)
  await user.type(screen.getByLabelText('Measurement question'),'How big is this pancreas?')
  await user.click(screen.getByRole('button',{name:'Calculate volume'}))
  expect(screen.getByText(/about 44.00 mL/)).toBeTruthy(); expect(screen.getByText('Measurement evidence')).toBeTruthy()
})
it('shows the coverage failure without reporting volume', async () => {
  const user=userEvent.setup(); render(<NativeMeasurementPanel measurement={{status:'unavailable',reason:'Inference crop boundary contact.'}} />)
  expect(screen.getByRole('note').textContent).toContain('Inference crop boundary')
  await user.type(screen.getByLabelText('Measurement question'),'How big is this pancreas?')
  await user.click(screen.getByRole('button',{name:'Calculate volume'}))
  const response=screen.getByRole('heading',{name:'Measurement unavailable'}).parentElement
  expect(within(response).getByText(/Inference crop boundary/)).toBeTruthy(); expect(screen.queryByText(/mL/)).toBeNull()
})
it('does not turn a measurement into a disease interpretation', async () => {
  const user=userEvent.setup(); render(<NativeMeasurementPanel measurement={m} />)
  await user.type(screen.getByLabelText('Measurement question'),'Is this pancreas normal?')
  await user.click(screen.getByRole('button',{name:'Calculate volume'}))
  expect(screen.getByText(/not a finding that your pancreas is enlarged, small, or normal/)).toBeTruthy()
  expect(screen.getByText(/not an individual normal range/)).toBeTruthy()
  expect(screen.getByText(/Whole-organ coverage and model accuracy are unverified/)).toBeTruthy()
})
it('explains boundary counts and preserves provenance without releasing the lesion total', async () => {
  const user = userEvent.setup()
  render(<NativeMeasurementPanel live measurement={{status:'unavailable',reason:'Crop boundary contact.',
    predictionSha256:'verified-mask-hash',modelSha256:{segmenter:'verified-model-hash'},
    coverageDiagnostics:{schema:'mask-boundary-counts-v1',cropContact:{pancreasLabel:67,lesionLabel:0},
      imageContact:{pancreasLabel:0,lesionLabel:0},cropFaces:[]}}} />)
  await user.type(screen.getByLabelText('Measurement question'),'How big is this lesion?')
  await user.click(screen.getByRole('button',{name:'Calculate volume'}))
  expect(screen.getByText(/67 pancreas-label voxels and 0 lesion-label voxels/)).toBeTruthy()
  expect(screen.getByText(/counts cannot distinguish/)).toBeTruthy()
  expect(screen.getByText(/verified-mask-hash/)).toBeTruthy()
  expect(screen.queryByText(/mL/)).toBeNull()
  expect(screen.queryByText('Predicted outline volume')).toBeNull()
})
