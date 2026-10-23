import React from 'react'
import { it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LiteratureSearchPanel from '../src/components/LiteratureSearchPanel.jsx'
const context = { key: 'one:saved', available: true, source: 'saved' }
const measurement = { contextKey: context.key, pancreasMl: 72, lesionMl: 3, lesionVoxels: 50, shape: [5,5,5], voxelMm3: 24, unitsBasis: 'NIfTI millimeter units', coverage: 'Whole-organ coverage unverified' }
async function ask(user, q = 'how big is this pancreas?') {
  await user.type(screen.getByLabelText('Literature question'), q)
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
}
it('answers locally and shows provenance without sending scan data to literature', async () => {
  const user = userEvent.setup(); const search = vi.fn(); const measure = vi.fn(async () => measurement)
  render(<LiteratureSearchPanel variant="panel" measurementContext={context} measure={measure} search={search} />)
  await ask(user)
  expect(await screen.findByText(/about 72.00 mL/)).toBeTruthy()
  expect(screen.getByText(/Calculated locally/)).toBeTruthy()
  expect(screen.getByText('Measurement source and limitations')).toBeTruthy()
  expect(search).not.toHaveBeenCalled()
})
it('clears completed results when prediction identity changes within one study', async () => {
  const user = userEvent.setup(); const props = { variant: 'panel', contextKey: 'one', measure: async () => measurement }
  const { rerender } = render(<LiteratureSearchPanel {...props} measurementContext={context} />)
  await ask(user); expect(await screen.findByText(/about 72.00 mL/)).toBeTruthy()
  rerender(<LiteratureSearchPanel {...props} measurementContext={{ ...context, key: 'one:new' }} />)
  expect(screen.queryByText(/about 72.00 mL/)).toBeNull()
})
it('discards a late measurement after a study switch', async () => {
  const user = userEvent.setup(); let finish
  const measure = vi.fn(() => new Promise(resolve => { finish = resolve }))
  const { rerender } = render(<LiteratureSearchPanel measurementContext={context} measure={measure} />)
  await ask(user)
  rerender(<LiteratureSearchPanel measurementContext={{ ...context, key: 'two:saved' }} measure={measure} />)
  expect(measure.mock.calls[0][1].aborted).toBe(true)
  await act(async () => finish(measurement))
  expect(screen.queryByRole('article')).toBeNull()
})
it('refuses compound scan interpretation without calling either service', async () => {
  const user = userEvent.setup(); const search = vi.fn(); const measure = vi.fn()
  render(<LiteratureSearchPanel measurementContext={context} measure={measure} search={search} />)
  await ask(user, 'How big is this pancreas and is it cancer?')
  expect(screen.getByText(/Head measurements/)).toBeTruthy()
  expect(measure).not.toHaveBeenCalled(); expect(search).not.toHaveBeenCalled()
})
it('keeps source search for current-scan questions local and explains the distinction', async () => {
  const user = userEvent.setup(); const findSources = vi.fn()
  render(<LiteratureSearchPanel measurementContext={context} findSources={findSources} />)
  await user.type(screen.getByLabelText('Literature question'), 'how big is this pancreas?')
  await user.click(screen.getByRole('button', { name: 'Find sources' }))
  expect(screen.getByText(/Use Ask question to calculate/)).toBeTruthy(); expect(findSources).not.toHaveBeenCalled()
})
it('shows an invalid geometry refusal without a numeric answer', async () => {
  const user = userEvent.setup()
  render(<LiteratureSearchPanel measurementContext={context} measure={async () => { throw new Error('The CT and prediction grids do not match.') }} />)
  await ask(user)
  expect(await screen.findByText(/grids do not match/)).toBeTruthy()
  expect(screen.queryByText(/Calculated locally/)).toBeNull()
})

it('answers study comparisons locally with a source and explicit limits', async () => {
  const user = userEvent.setup(); const search = vi.fn()
  render(<LiteratureSearchPanel measurementContext={context} measure={async () => measurement} search={search} />)
  await ask(user, 'Is this pancreas big or small?')
  expect(await screen.findByText(/10.6 mL .* below/)).toBeTruthy()
  expect(screen.getByRole('link', {name: /Study source/}).getAttribute('href')).toContain('25950180')
  expect(search).not.toHaveBeenCalled()
})
