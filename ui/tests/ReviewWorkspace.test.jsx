import React from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewWorkspace from '../src/components/ReviewWorkspace.jsx'
import { workspaceProps } from './fixtures/workspace.js'

vi.mock('../src/components/NiivueViewer.jsx', () => import('./fixtures/MockViewer.jsx'))

it('locks prediction and reference before analysis', async () => {
  render(<ReviewWorkspace {...workspaceProps()} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(screen.getByRole('button', { name: 'Model prediction' }).disabled).toBe(true)
  expect(screen.getByRole('button', { name: 'Source of truth' }).disabled).toBe(true)
  expect(screen.getByRole('button', { name: 'Original CT' }).getAttribute('aria-pressed')).toBe('true')
})

it('changes 2D/3D, toggles library, and resets after switching case', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<ReviewWorkspace {...workspaceProps()} />)
  await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  await user.click(screen.getByRole('button', { name: '3D', exact: true }))
  expect(screen.getByRole('button', { name: '3D', exact: true }).getAttribute('aria-pressed')).toBe('true')
  await user.click(screen.getByRole('button', { name: 'Collapse scan library' }))
  expect(screen.getByRole('main').classList.contains('review-workspace-v2--drawer-closed')).toBe(true)
  expect(screen.getByRole('button', { name: 'Open scan library' })).toBeTruthy()
  rerender(<ReviewWorkspace {...workspaceProps({ caseId: 'SYNTHETIC_B' })} />)
  await waitFor(() => expect(screen.getByRole('button', { name: '2D', exact: true }).getAttribute('aria-pressed')).toBe('true'))
  expect(screen.getByRole('main').classList.contains('review-workspace-v2--drawer-closed')).toBe(false)
})

it('keeps imaging controls usable while the literature service is unavailable', async () => {
  const user = userEvent.setup()
  const fetch = vi.fn().mockRejectedValue(new Error('Literature unavailable'))
  vi.stubGlobal('fetch', fetch)
  try {
    render(<ReviewWorkspace {...workspaceProps()} />)
    await screen.findByRole('status', { name: 'Synthetic viewer stub' })
    await user.click(screen.getByText('Guided evidence questions'))
    await user.click(screen.getByRole('button', { name: 'Ask and save fixture response' }))
    expect(await screen.findByRole('alert')).toBeTruthy()
    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    expect(screen.getByRole('button', { name: '3D', exact: true }).getAttribute('aria-pressed')).toBe('true')
    await user.click(screen.getByRole('button', { name: 'Collapse scan library' }))
    expect(screen.getByRole('button', { name: 'Open scan library' })).toBeTruthy()
    expect(screen.getByRole('status', { name: 'Synthetic viewer stub' })).toBeTruthy()
  } finally {
    vi.unstubAllGlobals()
  }
})
