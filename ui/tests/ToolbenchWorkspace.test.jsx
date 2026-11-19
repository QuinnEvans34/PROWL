import React, { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewWorkspace from '../src/components/ReviewWorkspace.jsx'
import { loadScanMeasurements, measureMask } from '../src/lib/scanMeasurements.js'
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
  it('sends the selected lesion or pancreas measurement to the exact 2D plane', async () => {
    const user = userEvent.setup()
    const affine = [[2, 0, 0, -4], [0, 0, -4, 10], [0, 3, 0, 1], [0, 0, 0, 1]]
    const hdr = { dims: [3, 8, 8, 8, 1, 1, 1, 1], affine, xyzt_units: 2, sform_code: 1 }
    const labels = new Uint8Array(8 ** 3)
    const index = (x, y, z) => x + 8 * (y + 8 * z)
    labels[index(1, 1, 1)] = 1
    labels[index(2, 2, 2)] = labels[index(2, 3, 2)] = 2
    labels[index(4, 4, 5)] = 2
    const volumes = measureMask(hdr, hdr, labels)
    const second = volumes.lesionDimensions.components[1]
    let finish
    loadScanMeasurements.mockImplementationOnce(context => new Promise(resolve => { finish = () => resolve(measured(context, volumes)) }))
      .mockImplementation(async context => measured(context, volumes))
    const props = (caseId, syntheticLesionPick) => workspaceProps({ caseId, isCurated: true,
      caseData: { ...cases[caseId], files: { ...cases[caseId].files, mesh: { lesion_pred: 'synthetic.obj', pancreas_pred: 'synthetic.obj' } },
        syntheticLesionPick },
    })
    const { rerender } = render(<ReviewWorkspace {...props('SYNTHETIC_A', [4, -10, 13])} />)
    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    const rail = () => within(screen.getByRole('region', { name: 'Lesion review' }))
    const toggle = () => screen.getByRole('button', { name: 'Show calipers', exact: true })
    const hide = () => screen.getByRole('button', { name: 'Hide calipers', exact: true })
    const exit = () => rail().getByRole('button', { name: 'Exit inspection' })
    const pickLesion = () => user.click(screen.getByRole('button', { name: 'Pick synthetic lesion surface' }))
    const pickEmpty = () => user.click(screen.getByRole('button', { name: 'Pick empty space' }))
    expect(rail().getByText('Checking the predicted outline…')).toBeTruthy()
    await user.click(await screen.findByRole('button', { name: 'Pick synthetic lesion surface' }))
    expect(rail().getByText('Lesion clicked. Checking its outline…')).toBeTruthy()
    await act(async () => finish())
    const findings = await screen.findByRole('region', { name: 'Predicted lesion dimensions' })
    expect(findings.querySelector('[data-selected]')?.textContent).toContain('Predicted lesion 2')
    expect(within(findings).getByText('Selected')).toBeTruthy()
    const viewer3d = () => viewerData(screen.getByTestId(/^synthetic-viewer-3d/))
    expect(viewer3d().selectedLesionWorldMm).toEqual(second.focusWorldMm)
    expect(toggle().disabled).toBe(false)
    expect(toggle().getAttribute('aria-pressed')).toBe('false')
    expect(viewer3d().measurementCalipers).toBeNull()
    await user.click(toggle())
    expect(hide().getAttribute('aria-pressed')).toBe('true')
    expect(viewer3d().measurementCalipers).toEqual(second.calipers)
    await user.click(screen.getByRole('button', { name: 'Pick surrounding synthetic tissue' }))
    await pickEmpty()
    expect(rail().getByText('Predicted lesion 2')).toBeTruthy()
    expect(viewer3d().measurementCalipers).toEqual(second.calipers)
    await user.click(rail().getByRole('button', { name: 'Zoom to lesion' }))
    expect(viewer3d().navigationCommand).toMatchObject({ type: 'zoom-lesion', target: '3d', boundsWorldMm: second.boundsWorldMm })
    await user.click(hide())
    expect(viewer3d().measurementCalipers).toBeNull()
    await pickEmpty()
    expect(viewer3d()).toMatchObject({ selectedObject: null, selectedLesionWorldMm: null })
    expect(rail().queryByText('Predicted lesion 2')).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Pick surrounding synthetic tissue' }))
    const pancreas = within(screen.getByRole('region', { name: 'Predicted pancreas dimensions' }))
    expect(pancreas.getByText('Selected')).toBeTruthy()
    expect(pancreas.getAllByText(/cm$/)).toHaveLength(2)
    await user.click(pancreas.getByRole('button', { name: 'Inspect pancreas measurement' }))
    const pancreasViewer = within(screen.getByRole('region', { name: 'Coronal CT plane' }))
      .getByRole('status', { name: 'Synthetic viewer stub' })
    const pancreasCalipers = volumes.pancreasDimensions.calipers
    expect(viewerData(pancreasViewer)).toMatchObject({
      measurementAnatomy: 'pancreas', measurementCalipers: pancreasCalipers,
      navigationCommand: { type: 'measurement-point', plane: 'coronal', worldMm: pancreasCalipers.anchorWorldMm },
    })
    await user.click(screen.getByRole('button', { name: 'Lesion', exact: true, pressed: true }))
    expect(viewerData(pancreasViewer).measurementCalipers).toEqual(pancreasCalipers)
    await user.click(screen.getByRole('button', { name: 'Lesion', exact: true, pressed: false }))
    await user.click(within(screen.getByRole('region', { name: 'Pancreas review' })).getByRole('button', { name: 'Exit inspection' }))
    expect(viewerData(pancreasViewer).measurementCalipers).toBeUndefined()
    await user.click(pancreas.getByRole('button', { name: 'Select pancreas in 3D' }))
    expect(viewer3d().selectedObject).toMatchObject({ source: 'pred', anatomy: 'pancreas' })
    await pickLesion()
    await user.click(toggle())
    await user.click(rail().getByRole('button', { name: 'Inspect CT slice' }))
    const coronal = within(screen.getByRole('region', { name: 'Coronal CT plane' })).getByRole('status', { name: 'Synthetic viewer stub' })
    await waitFor(() => expect(viewerData(coronal).navigationCommand).toMatchObject({
      type: 'measurement-point', plane: 'coronal', worldMm: [4, -10, 13],
    }))
    expect(viewerData(coronal).measurementCalipers).toEqual(second.calipers)
    expect(screen.getByRole('button', { name: '2D', exact: true }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.queryByRole('region', { name: 'Axial CT plane' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Show calipers', exact: true })).toBeNull()
    await user.click(rail().getByRole('button', { name: 'Zoom to lesion' }))
    expect(viewerData(coronal).navigationCommand).toMatchObject({ type: 'zoom-lesion', target: '2d', worldMm: second.focusWorldMm })
    expect(viewer3d().navigationCommand).toBeNull()

    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    expect(viewer3d().measurementCalipers).toEqual(second.calipers)
    await user.click(within(findings).getByText('1 more predicted lesion'))
    await user.click(within(findings).getByRole('button', { name: 'Select lesion 1 in 3D' }))
    expect(hide().getAttribute('aria-pressed')).toBe('true')
    expect(viewer3d().measurementCalipers).toEqual(volumes.lesionDimensions.components[0].calipers)

    await user.click(exit())
    expect(viewer3d()).toMatchObject({ selectedObject: null, selectedLesionWorldMm: null, measurementCalipers: null })
    expect(within(findings).queryByText('Selected')).toBeNull()

    await pickLesion()
    await user.click(toggle())
    await user.click(rail().getByRole('button', { name: 'Inspect CT slice' }))
    const coronalPane = screen.getByRole('region', { name: 'Coronal CT plane' })
    fireEvent.keyDown(coronalPane, { key: 'Escape' })
    const coronalAfterExit = within(coronalPane).getByRole('status', { name: 'Synthetic viewer stub' })
    expect(viewerData(coronalAfterExit)).toMatchObject({ activePlane: 'coronal', selectedObject: null, navigationCommand: null })
    expect(viewerData(coronalAfterExit).measurementCalipers).toBeUndefined()
    expect(viewer3d().measurementCalipers).toBeNull()
    expect(screen.getByRole('button', { name: '2D', exact: true }).getAttribute('aria-pressed')).toBe('true')

    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    await pickLesion()
    await user.click(toggle())
    rerender(<ReviewWorkspace {...props('SYNTHETIC_B', null)} />)
    const next = await screen.findByRole('region', { name: 'Predicted lesion dimensions' })
    expect(within(next).queryByText('Selected')).toBeNull()
    expect(viewerData(screen.getByTestId('synthetic-viewer-2d-coronal')).measurementCalipers).toBeUndefined()
    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    expect(screen.queryByRole('button', { name: 'Show calipers', exact: true })).toBeNull()
    expect(viewer3d().measurementCalipers).toBeNull()
  })

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

  it('uses the focused plane slider for slice changes and keeps zoom local', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await screen.findAllByRole('status', { name: 'Synthetic viewer stub' })
    const coronal = screen.getByRole('region', { name: 'Coronal CT plane' })
    const coronalViewer = within(coronal).getByRole('status', { name: 'Synthetic viewer stub' })
    const coronalSlice = within(coronal).getByRole('slider', { name: 'Coronal slice' })
    await waitFor(() => expect(coronalSlice.disabled).toBe(false))
    fireEvent.keyDown(coronal, { key: 'ArrowRight' })
    fireEvent.keyDown(document.body, { key: 'ArrowDown' })
    expect(viewerData(coronalViewer).navigationCommand).toBeNull()
    expect(within(coronal).queryByRole('spinbutton')).toBeNull()
    expect(within(coronal).queryByRole('button', { name: /Next|Previous.*slice/ })).toBeNull()
    act(() => coronalSlice.focus())
    fireEvent.change(coronalSlice, { target: { value: '51' } })
    await waitFor(() => expect(viewerData(coronalViewer).navigationCommand).toMatchObject({ type: 'slice', plane: 'coronal', index: 51 }))
    const sliceCommand = viewerData(coronalViewer).navigationCommand
    expect(fireEvent.wheel(coronalSlice, { deltaY: 40 })).toBe(false)
    expect(document.activeElement).toBe(coronalSlice)
    expect(viewerData(coronalViewer).navigationCommand).toEqual(sliceCommand)
    const axial = screen.getByRole('region', { name: 'Axial CT plane' })
    const axialViewer = within(axial).getByRole('status', { name: 'Synthetic viewer stub' })
    expect(viewerData(axialViewer).navigationCommand).toBeNull()
    await user.click(within(axial).getByRole('button', { name: 'Zoom in axial' }))
    expect(viewerData(axialViewer).navigationCommand).toMatchObject({ type: 'zoom', factor: 1.2 })
    expect(viewerData(coronalViewer).navigationCommand).toMatchObject({ type: 'slice', plane: 'coronal', index: 51 })
  })

  it('uses anatomical camera presets independently of the 3D peel slider', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    expect(screen.queryByRole('button', { name: 'Move', exact: true })).toBeNull()
    const peel = screen.getByRole('slider', { name: 'Front-to-back CT removal' })
    act(() => peel.focus())
    fireEvent.change(peel, { target: { value: '37' } })
    await waitFor(() => expect(peel.value).toBe('37'))
    expect(fireEvent.wheel(peel, { deltaY: -40 })).toBe(false)
    expect(peel.value).toBe('37')
    expect(document.activeElement).toBe(peel)
    await user.click(screen.getByRole('button', { name: 'Views', exact: true }))
    await user.click(screen.getByRole('button', { name: 'Front', exact: true }))
    const viewer = screen.getByTestId(/^synthetic-viewer-3d/)
    expect(viewerData(viewer).navigationCommand).toMatchObject({ type: 'camera', azimuth: 180, elevation: 0 })
    await user.keyboard('2')
    expect(viewerData(viewer).navigationCommand).toMatchObject({ type: 'camera', azimuth: 0, elevation: 0 })
    expect(peel.value).toBe('37')
    await user.click(screen.getByRole('button', { name: '2D', exact: true }))
    expect(screen.getByRole('button', { name: 'Pan', exact: true })).toBeTruthy()
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
