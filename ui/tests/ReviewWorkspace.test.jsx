import React from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewWorkspace from '../src/components/ReviewWorkspace.jsx'
import LiteratureSearchPanel from '../src/components/LiteratureSearchPanel.jsx'
import { workspaceProps } from './fixtures/workspace.js'

vi.mock('../src/components/NiivueViewer.jsx', () => import('./fixtures/MockViewer.jsx'))

it('keeps the prediction hidden and offers no reference comparison before a prediction is shown', async () => {
  render(<ReviewWorkspace {...workspaceProps({ caseData: { files: { pred: 'p.nii.gz', gt: 'g.nii.gz' }, gt_has_lesion: false } })} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(screen.getByRole('button', { name: /^Prediction/ }).disabled).toBe(true)
  expect(screen.queryByRole('button', { name: /^Reference/ })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Compare with reference' })).toBeNull()
  expect(screen.getByRole('button', { name: 'Show saved prediction' })).toBeTruthy()
})

it('treats an absent reference as a complete review, not a missing step', async () => {
  render(<ReviewWorkspace {...workspaceProps({ isCurated: true, caseData: { files: { pred: 'p.nii.gz' }, gt_has_lesion: false } })} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(screen.queryByRole('button', { name: 'Compare with reference' })).toBeNull()
  expect(screen.getAllByText(/No reference annotation/).length).toBeGreaterThan(0)
  expect(screen.queryByText(/Dice/)).toBeNull()
})

it('explains an incompatible reference instead of overlaying it', async () => {
  render(<ReviewWorkspace {...workspaceProps({ isCurated: true, referenceCompatibility: 'incompatible', caseData: { files: { pred: 'p.nii.gz', gt: 'g.nii.gz' }, gt_has_lesion: false } })} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(screen.queryByRole('button', { name: 'Compare with reference' })).toBeNull()
  expect(screen.getAllByText(/does not match/).length).toBeGreaterThan(0)
  expect(screen.getByText(/"visibleSources":\["pred"\]/)).toBeTruthy()
})

it('changes 2D/3D, keeps the study list preference, and resets the view after switching study', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<ReviewWorkspace {...workspaceProps()} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  await user.click(screen.getByRole('button', { name: '3D', exact: true }))
  expect(screen.getByRole('button', { name: '3D', exact: true }).getAttribute('aria-pressed')).toBe('true')
  await user.click(screen.getByRole('button', { name: 'Split', exact: true }))
  const stubs = await screen.findAllByRole('status', { name: 'Synthetic viewer stub' })
  expect(stubs.map((stub) => JSON.parse(stub.textContent.replace(/^[^{]*/, '')).mode).sort()).toEqual(['2d', '3d'])
  await user.click(screen.getByRole('button', { name: '3D', exact: true }))
  if (screen.queryByRole('button', { name: 'Collapse study list' })) {
    await user.click(screen.getByRole('button', { name: 'Collapse study list' }))
  }
  expect(screen.getByRole('main').classList.contains('pw-wb--list-closed')).toBe(true)
  expect(screen.getByRole('button', { name: 'Open study list' })).toBeTruthy()
  rerender(<ReviewWorkspace {...workspaceProps({ caseId: 'SYNTHETIC_B' })} />)
  await waitFor(() => expect(screen.getByRole('button', { name: '2D', exact: true }).getAttribute('aria-pressed')).toBe('true'))
  expect(screen.getByRole('main').classList.contains('pw-wb--list-closed')).toBe(true)
})

it('keeps imaging controls usable while the literature service is unavailable', async () => {
  const user = userEvent.setup()
  const search = vi.fn().mockRejectedValue(new Error('Literature unavailable'))
  render(<ReviewWorkspace {...workspaceProps({ askPanel: <LiteratureSearchPanel search={search} findSources={search} /> })} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  await user.click(screen.getByRole('tab', { name: 'Ask PROWL' }))
  await user.type(screen.getByLabelText('Literature question'), 'What is pancreatitis?')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByRole('alert')).toBeTruthy()
  await user.click(screen.getByRole('button', { name: '3D', exact: true }))
  expect(screen.getByRole('button', { name: '3D', exact: true }).getAttribute('aria-pressed')).toBe('true')
  expect(screen.getByRole('status', { name: 'Synthetic viewer stub' })).toBeTruthy()
})

it('offers independent 3D scenes and does not guess a pancreas peel before geometry is available', async () => {
  const user = userEvent.setup()
  render(<ReviewWorkspace {...workspaceProps()} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  await user.click(screen.getByRole('button', { name: '3D', exact: true }))
  expect(screen.getByRole('button', { name: 'Peel to pancreas', exact: true }).disabled).toBe(true)
  await user.click(screen.getByRole('button', { name: 'Surfaces', exact: true }))
  expect(screen.queryByLabelText('Front-to-back CT removal')).toBeNull()
  await user.click(screen.getByRole('button', { name: 'Region', exact: true }))
  expect(screen.getByLabelText('Front-to-back CT removal').value).toBe('0')
  await user.click(screen.getByRole('button', { name: 'Viewer controls', exact: true }))
  expect(screen.getByRole('region', { name: 'Viewer controls' })).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Close viewer controls', exact: true }))
  await user.keyboard(']')
  expect(screen.getByLabelText('Front-to-back CT removal').value).toBe('5')
  await user.click(screen.getByRole('button', { name: 'Restore CT', exact: true }))
  expect(screen.getByLabelText('Front-to-back CT removal').value).toBe('0')
})
