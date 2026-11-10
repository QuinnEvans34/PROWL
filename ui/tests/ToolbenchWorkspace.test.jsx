import React, { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewWorkspace from '../src/components/ReviewWorkspace.jsx'
import { loadScanMeasurements } from '../src/lib/scanMeasurements.js'
import { readToolbenchLayout } from '../src/lib/toolbenchLayout.js'
import { workspaceProps } from './fixtures/workspace.js'

vi.mock('../src/components/NiivueViewer.jsx', () => import('./fixtures/MockViewer.jsx'))
vi.mock('../src/lib/scanMeasurements.js', async importOriginal => ({
  ...await importOriginal(), loadScanMeasurements: vi.fn(),
}))

const cases = {
  SYNTHETIC_A: { files: { ct: 'SYNTHETIC_A/ct.nii.gz', pred: 'SYNTHETIC_A/pred.nii.gz' }, spacing_mm: [2, 3, 4] },
  SYNTHETIC_B: { files: { ct: 'SYNTHETIC_B/ct.nii.gz', pred: 'SYNTHETIC_B/pred.nii.gz' }, spacing_mm: [2, 3, 4] },
}
function measured(context, changes = {}) {
  return {
    schema: 'prepared-mask-volume-v1', contextKey: context.key, shape: [5, 5, 5], voxelMm3: 24,
    pancreasVoxels: 3000, lesionVoxels: 125, pancreasMl: 72, lesionMl: 3,
    ctSha256: 'a'.repeat(64), predictionSha256: 'b'.repeat(64),
    coverage: 'Whole-organ coverage unverified', unitsBasis: 'NIfTI millimeter units',
    hashBasis: 'Decoded NIfTI bytes', modelLineage: 'Synthetic prepared prediction', ...changes,
  }
}
beforeEach(() => {
  loadScanMeasurements.mockReset()
  loadScanMeasurements.mockImplementation(async context => measured(context))
})

function Harness() {
  const [caseId, setCaseId] = useState('SYNTHETIC_A')
  const [drafts, setDrafts] = useState({})
  return <>
    <button onClick={() => setCaseId(current => current === 'SYNTHETIC_A' ? 'SYNTHETIC_B' : 'SYNTHETIC_A')}>Switch synthetic study</button>
    <ReviewWorkspace {...workspaceProps({
      caseId, caseData: cases[caseId], isCurated: true,
      finding: { lesionFlagged: caseId === 'SYNTHETIC_A', volumeMm3: 3000 },
      askPanel: <textarea aria-label="Expert question draft" defaultValue="" />,
      summaryStore: { drafts, onChange: (key, draft) => setDrafts(current => {
        const next = { ...current }
        if (draft) next[key] = draft
        else delete next[key]
        return next
      }) },
    })} />
  </>
}

const viewerData = node => JSON.parse(node.querySelector('pre').textContent)

async function startDraft(user) {
  await user.click(screen.getByRole('tab', { name: 'Summary' }))
  await user.click(screen.getByRole('button', { name: 'Start draft from findings' }))
  fireEvent.change(screen.getByLabelText(/Draft observations/), { target: { value: 'Synthetic reviewer observations.' } })
  fireEvent.change(screen.getByLabelText(/Your notes/), { target: { value: 'Synthetic reviewer notes.' } })
}

describe('real workspace layout with synthetic imaging only', () => {
  it('preserves mounted planes, expert questions and summary drafts through focus, hiding and resizing', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const viewers = await screen.findAllByRole('status', { name: 'Synthetic viewer stub' })
    expect(viewers).toHaveLength(3)
    await startDraft(user)
    await user.click(screen.getByRole('tab', { name: 'Ask PROWL' }))
    await user.type(screen.getByLabelText('Expert question draft'), 'Synthetic question in progress')

    const width = screen.getByRole('separator', { name: 'Expert panel width' })
    fireEvent.keyDown(width, { key: 'ArrowLeft' })
    expect(width.getAttribute('aria-valuenow')).toBe('330')
    await user.click(screen.getByRole('button', { name: 'Expert panel', exact: true }))
    expect(screen.queryByRole('tab', { name: 'Ask PROWL' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Expert panel', exact: true }))
    expect(screen.getByLabelText('Expert question draft').value).toBe('Synthetic question in progress')

    await user.click(screen.getByRole('button', { name: 'Focus workspace' }))
    expect(screen.queryByRole('tab', { name: 'Ask PROWL' })).toBeNull()
    expect(screen.getAllByRole('status', { name: 'Synthetic viewer stub' })).toEqual(viewers)
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.getByLabelText('Expert question draft').value).toBe('Synthetic question in progress')

    await user.click(screen.getByRole('button', { name: 'Hide sagittal plane' }))
    expect(screen.getAllByRole('status', { name: 'Synthetic viewer stub' })).toHaveLength(2)
    expect(screen.getAllByRole('status', { name: 'Synthetic viewer stub', hidden: true })).toEqual(viewers)
    await user.click(screen.getByRole('button', { name: 'Maximize axial plane' }))
    expect(screen.getAllByRole('status', { name: 'Synthetic viewer stub' })).toEqual([viewers[0]])
    await user.click(screen.getByRole('button', { name: 'Restore axial plane' }))
    await user.click(screen.getByRole('button', { name: 'Restore planes' }))
    expect(screen.getAllByRole('status', { name: 'Synthetic viewer stub' })).toEqual(viewers)
    const divider = screen.getByRole('separator', { name: 'Primary pane size' })
    fireEvent.keyDown(divider, { key: 'ArrowRight' })
    expect(divider.getAttribute('aria-valuenow')).toBe('66')
    await user.click(screen.getByRole('tab', { name: 'Summary' }))
    expect(screen.getByLabelText(/Draft observations/).value).toBe('Synthetic reviewer observations.')
    expect(screen.getByLabelText(/Your notes/).value).toBe('Synthetic reviewer notes.')
    expect(loadScanMeasurements).toHaveBeenCalledTimes(1)
  })

  it('restores layout without resetting evidence, window, opacity or review draft', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const viewers = await screen.findAllByRole('status', { name: 'Synthetic viewer stub' })
    await startDraft(user)
    fireEvent.change(screen.getByLabelText('CT window preset'), { target: { value: 'wide' } })
    fireEvent.change(screen.getByLabelText('Prediction overlay opacity'), { target: { value: '0.35' } })
    await user.click(screen.getByRole('button', { name: /^Prediction$/ }))
    await user.click(screen.getByRole('button', { name: 'Hide sagittal plane' }))
    fireEvent.keyDown(screen.getByRole('separator', { name: 'Expert panel width' }), { key: 'End' })
    const before = viewerData(viewers[0])
    await user.click(screen.getByRole('button', { name: 'Restore layout', exact: true }))
    expect(readToolbenchLayout()).toMatchObject({ panelWidth: 320, hiddenPlanes: [], maximizedPlane: null })
    expect(screen.getByLabelText('CT window preset').value).toBe('wide')
    expect(screen.getByLabelText('Prediction overlay opacity').value).toBe('0.35')
    expect(screen.getByRole('button', { name: /^Prediction$/ }).getAttribute('aria-pressed')).toBe('false')
    expect(viewerData(viewers[0])).toMatchObject({ ...before, ctWindow: 'wide', overlayOpacity: 0.35, visibleSources: [] })
    expect(screen.getByLabelText(/Your notes/).value).toBe('Synthetic reviewer notes.')
    expect(screen.getAllByRole('status', { name: 'Synthetic viewer stub' })).toEqual(viewers)
  })

  it('directs each slice and zoom control to its own plane', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await screen.findAllByRole('status', { name: 'Synthetic viewer stub' })
    const coronal = screen.getByRole('region', { name: 'Coronal CT plane' })
    const coronalViewer = within(coronal).getByRole('status', { name: 'Synthetic viewer stub' })
    const coronalSlice = within(coronal).getByRole('slider', { name: 'Coronal slice' })
    await waitFor(() => expect(coronalSlice.disabled).toBe(false))
    fireEvent.change(coronalSlice, { target: { value: '51' } })
    await waitFor(() => expect(viewerData(coronalViewer).navigationCommand).toMatchObject({ type: 'slice', plane: 'coronal', index: 51 }))
    const axial = screen.getByRole('region', { name: 'Axial CT plane' })
    const axialViewer = within(axial).getByRole('status', { name: 'Synthetic viewer stub' })
    expect(viewerData(axialViewer).navigationCommand).toBeNull()
    await user.click(within(axial).getByRole('button', { name: 'Zoom in axial' }))
    expect(viewerData(axialViewer).navigationCommand).toMatchObject({ type: 'zoom', factor: 1.2 })
    expect(viewerData(coronalViewer).navigationCommand).toMatchObject({ type: 'slice', plane: 'coronal', index: 51 })
  })

  it('keeps study measurements visible with the expert and rejects a late result from the previous study', async () => {
    const user = userEvent.setup()
    let resolveA
    loadScanMeasurements.mockImplementationOnce(() => new Promise(resolve => { resolveA = resolve }))
      .mockImplementationOnce(async context => measured(context, { pancreasMl: 96, pancreasVoxels: 4000 }))
    render(<Harness />)
    await screen.findAllByRole('status', { name: 'Synthetic viewer stub' })
    await waitFor(() => expect(loadScanMeasurements).toHaveBeenCalledTimes(1))
    const contextA = loadScanMeasurements.mock.calls[0][0]
    const signalA = loadScanMeasurements.mock.calls[0][1]
    await user.click(screen.getByRole('button', { name: 'Switch synthetic study' }))
    expect(signalA.aborted).toBe(true)
    await waitFor(() => expect(within(screen.getByRole('region', { name: 'Prediction measurements' })).getByText('96.00')).toBeTruthy())
    expect(screen.queryByText('72.00')).toBeNull()
    expect(screen.queryByText('Possible lesion · review required')).toBeNull()
    await user.click(screen.getByRole('tab', { name: 'Ask PROWL' }))
    expect(within(screen.getByRole('region', { name: 'Prediction measurements' })).getByText('96.00')).toBeTruthy()
    expect(within(screen.getByRole('region', { name: 'Image measurement overlay' })).getByText('96.00')).toBeTruthy()
    await act(async () => resolveA(measured(contextA)))
    expect(within(screen.getByRole('region', { name: 'Prediction measurements' })).getByText('96.00')).toBeTruthy()
    expect(screen.queryByText('72.00')).toBeNull()
    await user.click(screen.getByRole('button', { name: /^Prediction$/ }))
    expect(screen.queryByText('96.00')).toBeNull()
    expect(within(screen.getByRole('region', { name: 'Prediction measurements' })).getAllByText('Unavailable')).toHaveLength(2)
  })
})
