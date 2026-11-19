import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import FindingAskPanel from '../src/components/FindingAskPanel.jsx'

const finding = {
  anatomy: 'lesion', ordinal: 2,
  dimensions: { volumeMl: 8.31, superiorInferiorMm: 18,
    calipers: { plane: 'axial', axes: [{ lengthMm: 15 }, { lengthMm: 21.3 }] } },
}
const measurementState = { status: 'ready', measurement: { pancreasMl: 83, lesionMl: 8.31 } }
const evidence = <textarea aria-label="Literature question" />

it('shows the selected outline and reopens its measurement without losing the literature draft', async () => {
  const user = userEvent.setup()
  const inspect = vi.fn()
  render(<FindingAskPanel finding={finding} measurementState={measurementState} onInspect={inspect}>
    {evidence}
  </FindingAskPanel>)
  await user.type(screen.getByRole('textbox', { name: 'Literature question' }), 'Synthetic literature question')
  await user.click(screen.getByRole('button', { name: 'This outline' }))
  expect(screen.getByRole('heading', { name: 'Predicted lesion 2' })).toBeTruthy()
  expect(screen.getByText('1.50 × 2.13 cm')).toBeTruthy()
  expect(screen.getByText('8.31 mL')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Show measured slice' }))
  expect(inspect).toHaveBeenCalledOnce()
  expect(screen.queryByRole('textbox', { name: 'Literature question' })).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Published evidence' }))
  expect(screen.getByRole('textbox', { name: 'Literature question' }).value).toBe('Synthetic literature question')
})

it('immediately replaces earlier measurements when the prediction changes during loading', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<FindingAskPanel finding={finding} measurementState={measurementState}>{evidence}</FindingAskPanel>)
  await user.click(screen.getByRole('button', { name: 'This outline' }))
  rerender(<FindingAskPanel finding={finding} measurementState={{ status: 'loading' }}>{evidence}</FindingAskPanel>)
  expect(screen.getByRole('status').textContent).toBe('Checking the displayed outline…')
  expect(screen.queryByText('8.31 mL')).toBeNull()
  rerender(<FindingAskPanel measurementState={{ status: 'unavailable', reason: 'The mask is unavailable.' }}
    literatureRequest={{ token: 42 }}>{evidence}</FindingAskPanel>)
  expect(screen.getByRole('button', { name: 'Published evidence', pressed: true })).toBeTruthy()
})
