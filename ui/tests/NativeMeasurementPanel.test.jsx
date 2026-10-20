import React from 'react'
import { it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
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
  await user.type(screen.getByLabelText('Measurement question'),'How big is this pancreas?')
  await user.click(screen.getByRole('button',{name:'Calculate volume'}))
  expect(screen.getByText(/Inference crop boundary/)).toBeTruthy(); expect(screen.queryByText(/mL/)).toBeNull()
})
it('does not turn a measurement into a disease interpretation', async () => {
  const user=userEvent.setup(); render(<NativeMeasurementPanel measurement={m} />)
  await user.type(screen.getByLabelText('Measurement question'),'Is this pancreas normal?')
  await user.click(screen.getByRole('button',{name:'Calculate volume'}))
  expect(screen.getByText(/Individual dimensions/)).toBeTruthy(); expect(screen.queryByText(/about 44/)).toBeNull()
})
