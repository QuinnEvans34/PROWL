import React from 'react'
import { it, expect, vi } from 'vitest'
import { fireEvent, render, screen, within, waitFor } from '@testing-library/react'
import ProgressPanel from '../src/components/TrainingProgressPanel.jsx'
import retained from '../../configs/training-progress/lenovo-stunet-20261106.json'
const fixture = () => structuredClone(retained)
const TrainingProgressPanel = props => <ProgressPanel initialSnapshot={retained} {...props} />
const now = () => Date.parse(retained.observed_at) + 20 * 60000
const response = snapshot => new Response(JSON.stringify({ snapshot, read_state: 'local_snapshot', note: 'Saved export read.' }))

it('shows completed scores, denominators, source age and exploratory scope without claiming live status', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => response(retained)))
  render(<TrainingProgressPanel now={now} />)
  await screen.findByText('Saved export read.')
  expect(screen.getByText('Older saved observation')).toBeTruthy()
  expect(screen.getByText(/20 minutes old/)).toBeTruthy()
  expect(screen.getByText('Lenovo · Training at last observation')).toBeTruthy()
  expect(screen.getByText('6,814 / 12,000 updates')).toBeTruthy()
  const table = screen.getByRole('table')
  expect(within(table).getAllByRole('row')).toHaveLength(4)
  expect(within(table).getByText('0.3472')).toBeTruthy()
  expect(within(table).getByText('30/36')).toBeTruthy()
  expect(within(table).getByText('26/34')).toBeTruthy()
  expect(screen.getByText(/do not establish autonomous or independent-test/)).toBeTruthy()
  expect(screen.getByRole('img', { name: /Completed validation DICE curve/ })).toBeTruthy()
})

it('shows partial validation progress while retaining the last full score', async () => {
  const d = fixture(); d.run.step = 8000; d.run.phase = 'validating'
  d.run.validation = { step: 8000, completed_cases: 51, total_cases: 70 }
  vi.stubGlobal('fetch', vi.fn(async () => response(d)))
  render(<TrainingProgressPanel now={now} />)
  await screen.findByText(/Validation at 8,000 updates: 51\/70/)
  expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(4)
  expect(within(screen.getByRole('table')).queryByText('8,000')).toBeNull()
})

it('shows no score before the first full validation instead of a zero', async () => {
  const d = fixture(); d.run.step = 18; d.validations = []
  vi.stubGlobal('fetch', vi.fn(async () => response(d)))
  render(<TrainingProgressPanel initialSnapshot={d} now={now} />)
  await screen.findByText('Saved export read.')
  expect(screen.getByText(/No complete validation yet/)).toBeTruthy()
  expect(screen.queryByRole('table')).toBeNull()
  expect(screen.queryByText('0.0000')).toBeNull()
})

it('retains completed scores and observation time when the endpoint fails', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 503 })))
  render(<TrainingProgressPanel now={now} />)
  expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Could not read a newer export. Keeping the last verified results.')
  expect(within(screen.getByRole('table')).getByText('0.3472')).toBeTruthy()
  expect(screen.getByText(/20 minutes old/)).toBeTruthy()
})

it('rejects a response that rewrites completed scores', async () => {
  const d = fixture(); d.validations[0].lesion_dice = 0.99
  vi.stubGlobal('fetch', vi.fn(async () => response(d)))
  render(<TrainingProgressPanel now={now} />)
  await screen.findByRole('alert')
  expect(within(screen.getByRole('table')).getByText('0.1442')).toBeTruthy()
  expect(screen.queryByText('0.9900')).toBeNull()
})

it('recovers on an explicit refresh without changing source time or mixing history', async () => {
  const d = fixture(); d.run.step = 7000; d.run.elapsed_seconds += 30; d.observed_at = '2026-11-07T19:05:00Z'
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response('', { status: 503 })).mockResolvedValueOnce(response(d)))
  render(<TrainingProgressPanel now={now} />)
  await screen.findByRole('alert')
  fireEvent.click(screen.getByRole('button', { name: 'Refresh saved results' }))
  await screen.findByText('7,000 / 12,000 updates')
  expect(screen.queryByRole('alert')).toBeNull()
  expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(4)
  expect(document.querySelector('time').dateTime).toBe(d.observed_at)
})

it('isolates a late response from an unmounted request, even if transport ignores cancellation', async () => {
  let resolve
  const delayed = new Promise(r => { resolve = r })
  vi.stubGlobal('fetch', vi.fn().mockReturnValueOnce(delayed).mockResolvedValueOnce(response(retained)))
  const old = render(<TrainingProgressPanel now={now} />)
  old.unmount()
  render(<TrainingProgressPanel now={now} />)
  await screen.findByText('Saved export read.')
  const late = fixture(); late.run.step = 7000; late.run.elapsed_seconds++; late.observed_at = '2026-11-07T19:00:00Z'
  resolve(response(late))
  await waitFor(() => expect(screen.getByText('6,814 / 12,000 updates')).toBeTruthy())
  expect(screen.queryByText('7,000 / 12,000 updates')).toBeNull()
})

it('separates new continuation updates and time from global checkpoint and validation labels', async () => {
  const d = fixture(); d.run.starting_step = 12000
  d.source.run_id = 'corrected-continuation'; d.run.title = 'Corrected continuation'
  vi.stubGlobal('fetch', vi.fn(async () => response(d)))
  render(<TrainingProgressPanel initialSnapshot={d} now={now} />)
  await screen.findByText('Saved export read.')
  expect(screen.getByText('6,814 / 12,000 updates')).toBeTruthy()
  expect(screen.getByText('18,814/24,000')).toBeTruthy()
  expect(screen.getByText(/Session time above covers this phase only/)).toBeTruthy()
  const table = screen.getByRole('table')
  expect(within(table).getByText('Global updates')).toBeTruthy()
  expect(within(table).getByText('14,000')).toBeTruthy()
  expect(within(table).queryByText('2,000')).toBeNull()
})
