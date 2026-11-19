import React, { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
// Load the real toolbench after its canvas mock is installed. The 2D and 3D
// lazy imports then share the same mock rather than racing WebGL initialization.
import '../src/components/ToolbenchViewer.jsx'
import ReviewWorkspace from '../src/components/ReviewWorkspace.jsx'
import { loadScanMeasurements, measureMask } from '../src/lib/scanMeasurements.js'
import { readToolbenchLayout } from '../src/lib/toolbenchLayout.js'
import { workspaceProps } from './fixtures/workspace.js'

vi.mock('../src/components/NiivueViewer.jsx', () => import('./fixtures/MockViewer.jsx'))
vi.mock('../src/lib/scanMeasurements.js', async importOriginal => ({
  ...await importOriginal(), loadScanMeasurements: vi.fn(),
}))

const cases = {
  SYNTHETIC_A: { files: { ct: 'SYNTHETIC_A/ct.nii.gz', pred: 'SYNTHETIC_A/pred.nii.gz' }, spacing_mm: [2, 3, 4],
    syntheticPeelReveal: { frontToBack: 30, backToFront: 52 } },
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

function measuredFindings() {
  const affine = [[2, 0, 0, -4], [0, 0, -4, 10], [0, 3, 0, 1], [0, 0, 0, 1]]
  const hdr = { dims: [3, 8, 8, 8, 1, 1, 1, 1], affine, xyzt_units: 2, sform_code: 1 }
  const labels = new Uint8Array(8 ** 3)
  const index = (x, y, z) => x + 8 * (y + 8 * z)
  labels[index(1, 1, 1)] = 1
  labels[index(2, 2, 2)] = labels[index(2, 3, 2)] = 2
  labels[index(4, 4, 5)] = 2
  return measureMask(hdr, hdr, labels)
}

const lesionLocation = [4, -10, 13]
const planeCorners = [[-8, -10, 3], [16, -10, 3], [16, -10, 24], [-8, -10, 24]]
const camera = { azimuth: 71, elevation: 26, scale: 1.5, pivot3D: lesionLocation, orbitCentre: lesionLocation }
const meshStudy = ({ caseId = 'SYNTHETIC_A', syntheticLesionPick = lesionLocation, syntheticRestore = vi.fn() } = {}) =>
  workspaceProps({ caseId, isCurated: true,
    caseData: { ...cases[caseId], files: { ...cases[caseId].files, mesh: { lesion_pred: 'synthetic.obj', pancreas_pred: 'synthetic.obj' } },
      syntheticLesionPick, syntheticPlaneCorners: planeCorners, syntheticView: { '3d': camera }, syntheticRestore },
  })

const lesionRail = () => within(screen.getByRole('region', { name: 'Lesion review' }))
const showCalipers = () => screen.getByRole('button', { name: 'Show calipers', exact: true })
const hideCalipers = () => screen.getByRole('button', { name: 'Hide calipers', exact: true })
const viewer3d = () => viewerData(screen.getByTestId(/^synthetic-viewer-3d/))
const measuredViewer = async () => within(await screen.findByRole('region', { name: 'Measured CT' }))
  .findByRole('status', { name: 'Synthetic viewer stub' })

describe('real workspace layout with synthetic imaging only', () => {
  it('keeps lesion calipers pinned and takes the selected pancreas to its prepared measurement', async () => {
    const user = userEvent.setup()
    const volumes = measuredFindings()
    const second = volumes.lesionDimensions.components[1]
    let finish
    loadScanMeasurements.mockImplementationOnce(context => new Promise(resolve => { finish = () => resolve(measured(context, volumes)) }))
      .mockImplementation(async context => measured(context, volumes))
    render(<ReviewWorkspace {...meshStudy()} />)
    expect(screen.getByRole('button', { name: '3D', exact: true, pressed: true })).toBeTruthy()
    const pickLesion = () => user.click(screen.getByRole('button', { name: 'Pick synthetic lesion surface' }))
    const pickEmpty = () => user.click(screen.getByRole('button', { name: 'Pick empty space' }))
    expect(lesionRail().getByText('Checking the predicted outline…')).toBeTruthy()
    await user.click(await screen.findByRole('button', { name: 'Pick synthetic lesion surface' }))
    expect(lesionRail().getByText('Lesion clicked. Checking its outline…')).toBeTruthy()
    await act(async () => finish())
    const findings = await screen.findByRole('region', { name: 'Predicted lesion dimensions' })
    expect(findings.querySelector('[data-selected]')?.textContent).toContain('Predicted lesion 2')
    expect(within(findings).getByText('Selected')).toBeTruthy()
    expect(viewer3d().selectedLesionWorldMm).toEqual(second.focusWorldMm)
    expect(showCalipers().disabled).toBe(false)
    expect(showCalipers().getAttribute('aria-pressed')).toBe('false')
    expect(viewer3d().measurementCalipers).toBeNull()
    await user.click(showCalipers())
    expect(hideCalipers().getAttribute('aria-pressed')).toBe('true')
    expect(viewer3d().measurementCalipers).toEqual(second.calipers)
    await user.click(screen.getByRole('button', { name: 'Pick surrounding synthetic tissue' }))
    await pickEmpty()
    expect(lesionRail().getByText('Predicted lesion 2')).toBeTruthy()
    expect(viewer3d().measurementCalipers).toEqual(second.calipers)
    await user.click(lesionRail().getByRole('button', { name: 'Zoom to lesion' }))
    expect(viewer3d().navigationCommand).toMatchObject({ type: 'zoom-lesion', target: '3d', boundsWorldMm: second.boundsWorldMm })
    await user.click(hideCalipers())
    expect(viewer3d().measurementCalipers).toBeNull()
    await pickEmpty()
    expect(viewer3d()).toMatchObject({ selectedObject: null, selectedLesionWorldMm: null })
    expect(lesionRail().queryByText('Predicted lesion 2')).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Pick surrounding synthetic tissue' }))
    const pancreas = within(screen.getByRole('region', { name: 'Predicted pancreas dimensions' }))
    expect(pancreas.getByText('Selected')).toBeTruthy()
    expect(pancreas.getAllByText(/cm$/)).toHaveLength(2)
    expect(pancreas.getByText(/Prepared slice/)).toBeTruthy()
    await user.click(pancreas.getByRole('button', { name: 'Inspect pancreas measurement' }))
    const pancreasViewer = await measuredViewer()
    const pancreasCalipers = volumes.pancreasDimensions.calipers
    expect(viewerData(pancreasViewer)).toMatchObject({
      measurementAnatomy: 'pancreas', measurementCalipers: pancreasCalipers,
      navigationCommand: { type: 'measurement-point', target: 'inspection', plane: 'coronal', worldMm: pancreasCalipers.anchorWorldMm },
    })
    await user.click(screen.getByRole('button', { name: 'Lesion', exact: true, pressed: true }))
    expect(viewerData(pancreasViewer).measurementCalipers).toEqual(pancreasCalipers)
    await user.click(screen.getByRole('button', { name: 'Lesion', exact: true, pressed: false }))
    await user.click(within(screen.getByRole('region', { name: 'Pancreas review' })).getByRole('button', { name: 'Exit inspection' }))
    expect(screen.queryByRole('region', { name: 'Measured CT' })).toBeNull()
    await user.click(pancreas.getByRole('button', { name: 'Select pancreas in 3D' }))
    expect(viewer3d().selectedObject).toMatchObject({ source: 'pred', anatomy: 'pancreas' })
    await pickLesion()
    await user.click(showCalipers())
    await user.click(within(findings).getByText('1 more predicted lesion'))
    await user.click(within(findings).getByRole('button', { name: 'Select lesion 1 in 3D' }))
    expect(hideCalipers().getAttribute('aria-pressed')).toBe('true')
    expect(viewer3d().measurementCalipers).toEqual(volumes.lesionDimensions.components[0].calipers)
    await user.click(lesionRail().getByRole('button', { name: 'Exit inspection' }))
    expect(viewer3d()).toMatchObject({ selectedObject: null, selectedLesionWorldMm: null, measurementCalipers: null })
    expect(within(findings).queryByText('Selected')).toBeNull()
  })

  it('links the measured CT and mounted 3D view while preserving the earlier camera and peel', async () => {
    const user = userEvent.setup()
    const volumes = measuredFindings()
    const second = volumes.lesionDimensions.components[1]
    const restoreCamera = vi.fn()
    loadScanMeasurements.mockImplementation(async context => measured(context, volumes))
    render(<ReviewWorkspace {...meshStudy({ syntheticRestore: restoreCamera })} />)
    const original3d = await screen.findByTestId(/^synthetic-viewer-3d/)
    const inspectionTools = () => within(screen.getByRole('toolbar', { name: 'Finding inspection tools' }))
    await user.click(screen.getByRole('button', { name: 'Back to front', exact: true }))
    const peel = screen.getByRole('slider', { name: 'Back-to-front CT removal' })
    fireEvent.change(peel, { target: { value: '27' } })
    await waitFor(() => expect(viewer3d().clip).toMatchObject({ progress: 27, azimuth: 180 }))
    await screen.findByRole('region', { name: 'Predicted lesion dimensions' })
    await user.click(screen.getByRole('button', { name: 'Pick synthetic lesion surface' }))
    await user.click(showCalipers())
    await user.click(lesionRail().getByRole('button', { name: 'Inspect CT slice' }))
    const coronal = await measuredViewer()
    await waitFor(() => expect(viewerData(coronal).navigationCommand).toMatchObject({
      type: 'measurement-point', target: 'inspection', plane: 'coronal', worldMm: [4, -10, 13],
    }))
    expect(viewerData(coronal).measurementCalipers).toEqual(second.calipers)
    expect(screen.getByRole('button', { name: 'Split', exact: true, pressed: true })).toBeTruthy()
    expect(screen.getByTestId(/^synthetic-viewer-3d/)).toBe(original3d)
    expect(screen.queryByRole('region', { name: '2D planes' })).toBeNull()
    expect(screen.queryByRole('region', { name: 'Axial CT plane' })).toBeNull()
    expect(hideCalipers().getAttribute('aria-pressed')).toBe('true')
    expect(viewer3d().measurementCalipers).toEqual(second.calipers)
    const measurementCommand = viewerData(coronal).navigationCommand
    expect(viewerData(coronal).overlayMode).toBe('outline')
    await user.click(inspectionTools().getByRole('button', { name: 'Fill' }))
    expect(viewerData(coronal).overlayMode).toBe('fill')
    await user.click(inspectionTools().getByRole('button', { name: 'CT only' }))
    expect(viewerData(coronal).overlayMode).toBe('off')
    await user.click(inspectionTools().getByRole('button', { name: 'Outline' }))
    expect(viewerData(coronal).navigationCommand).toEqual(measurementCommand)
    expect(viewer3d().navigationCommand).toBeNull()
    await user.click(inspectionTools().getByRole('button', { name: 'Show slice in 3D' }))
    expect(viewer3d().sliceLocatorCorners).toEqual(planeCorners)
    expect(viewer3d().clip).toMatchObject({ progress: 27, azimuth: 180 })
    await user.click(inspectionTools().getByRole('button', { name: 'Show slice in 3D' }))
    expect(viewer3d().sliceLocatorCorners).toBeNull()
    await user.click(lesionRail().getByRole('button', { name: 'Zoom to lesion' }))
    expect(viewerData(coronal).navigationCommand).toMatchObject({ type: 'zoom-lesion', target: 'inspection', worldMm: second.focusWorldMm })
    expect(viewer3d().navigationCommand).toBeNull()
    await user.click(lesionRail().getByRole('button', { name: 'Go to measured slice' }))
    expect(viewerData(coronal).navigationCommand).toMatchObject({ type: 'measurement-point', worldMm: [4, -10, 13] })
    await user.click(screen.getByRole('button', { name: 'Front to back', exact: true }))
    expect(viewer3d().clip.azimuth).toBe(0)

    fireEvent.keyDown(coronal, { key: 'Escape' })
    expect(screen.queryByRole('region', { name: 'Measured CT' })).toBeNull()
    expect(screen.getByRole('button', { name: '3D', exact: true, pressed: true })).toBeTruthy()
    expect(restoreCamera).toHaveBeenLastCalledWith(expect.objectContaining(camera))
    expect(viewer3d().clip).toMatchObject({ progress: 27, azimuth: 180 })
    expect(viewer3d().measurementCalipers).toBeNull()
  })

  it('clears linked inspection and pinned calipers when the study changes', async () => {
    const user = userEvent.setup()
    const volumes = measuredFindings()
    loadScanMeasurements.mockImplementation(async context => measured(context, volumes))
    const { rerender } = render(<ReviewWorkspace {...meshStudy()} />)
    const button = await screen.findByRole('button', { name: 'Inspect measurement for lesion 1' })
    await user.click(button)
    await measuredViewer()
    await user.click(showCalipers())
    expect(viewer3d().measurementCalipers).toEqual(volumes.lesionDimensions.components[0].calipers)
    rerender(<ReviewWorkspace {...meshStudy({ caseId: 'SYNTHETIC_B', syntheticLesionPick: null })} />)
    const next = await screen.findByRole('region', { name: 'Predicted lesion dimensions' })
    expect(within(next).queryByText('Selected')).toBeNull()
    expect(screen.queryByRole('region', { name: 'Measured CT' })).toBeNull()
    await user.click(screen.getByRole('button', { name: '2D', exact: true }))
    expect(viewerData(await screen.findByTestId('synthetic-viewer-2d-coronal')).measurementCalipers).toBeUndefined()
    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    expect(screen.queryByRole('button', { name: 'Show calipers', exact: true })).toBeNull()
    expect(viewer3d().measurementCalipers).toBeNull()
  })

  it('opens one measured CT pane when the prediction has no 3D meshes', async () => {
    const user = userEvent.setup()
    const volumes = measuredFindings()
    loadScanMeasurements.mockImplementation(async context => measured(context, volumes))
    render(<Harness />)
    const originalPanes = within(screen.getByRole('region', { name: '2D planes' }))
    const oldViewers = await originalPanes.findAllByRole('status', { name: 'Synthetic viewer stub' })
    const lesion = await screen.findByRole('button', { name: 'Inspect measurement for lesion 1' })
    await user.click(lesion)
    const inspected = within(await screen.findByRole('region', { name: 'Measured CT' }))
    const measuredNode = await inspected.findByRole('status', { name: 'Synthetic viewer stub' })
    expect(viewerData(measuredNode)).toMatchObject({
      measurementCalipers: volumes.lesionDimensions.components[0].calipers, overlayMode: 'outline',
    })
    expect(screen.getByRole('button', { name: '2D', exact: true, pressed: true })).toBeTruthy()
    expect(screen.queryByRole('region', { name: '3D surfaces' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Show slice in 3D' })).toBeNull()
    await user.click(within(screen.getByRole('region', { name: 'Lesion review' })).getByRole('button', { name: 'Exit inspection' }))
    expect(screen.queryByRole('region', { name: 'Measured CT' })).toBeNull()
    expect(originalPanes.getAllByRole('status', { name: 'Synthetic viewer stub' })).toEqual(oldViewers)
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

  it('reverses the peel at the current depth independently of anatomical camera presets', async () => {
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
    expect(viewerData(viewer).clip).toMatchObject({ azimuth: 0, progress: 37 })
    expect(screen.getByRole('button', { name: 'Peel to the pancreas (30%)' })).toBeTruthy()
    const cameraCommand = viewerData(viewer).navigationCommand
    await user.click(screen.getByRole('button', { name: 'Back to front', exact: true }))
    expect(screen.getByRole('button', { name: 'Back to front', pressed: true })).toBeTruthy()
    expect(screen.getByRole('slider', { name: 'Back-to-front CT removal' }).value).toBe('37')
    expect(viewerData(viewer).navigationCommand).toEqual(cameraCommand)
    expect(viewerData(viewer).clip).toMatchObject({ azimuth: 180, progress: 37 })
    await user.keyboard('2')
    expect(viewerData(viewer).navigationCommand).toMatchObject({ type: 'camera', azimuth: 0, elevation: 0 })
    expect(peel.value).toBe('37')
    await user.click(screen.getByRole('button', { name: 'Peel to the pancreas (52%)' }))
    expect(viewerData(viewer).clip).toMatchObject({ azimuth: 180, progress: 52 })
    await user.click(screen.getByRole('button', { name: 'Restore CT', exact: true }))
    expect(viewerData(viewer).clip).toMatchObject({ azimuth: 180, progress: 0, depth: 2 })
    await user.click(screen.getByRole('button', { name: 'Front to back', exact: true }))
    expect(viewerData(viewer).clip).toMatchObject({ azimuth: 0, progress: 0, depth: 2 })
  })

  it('allows 3D pan while 2D framing is locked', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    const lock = await screen.findByRole('button', { name: 'Lock framing' })
    await waitFor(() => expect(lock.disabled).toBe(false))
    await user.click(lock)
    const pan = () => screen.getByRole('button', { name: 'Pan', exact: true })
    expect(pan().disabled).toBe(true)

    await user.click(screen.getByRole('button', { name: '3D', exact: true }))
    const viewer = await screen.findByTestId(/^synthetic-viewer-3d/)
    const rotate = screen.getByRole('button', { name: 'Rotate', pressed: true })
    expect(viewerData(viewer).interactionMode).toBe('rotate')
    await user.click(pan())
    expect(viewerData(viewer).interactionMode).toBe('pan')
    await user.click(rotate)
    expect(viewerData(viewer).interactionMode).toBe('rotate')

    await user.click(screen.getByRole('button', { name: 'Split', exact: true }))
    await user.click(pan())
    expect(viewerData(viewer).interactionMode).toBe('pan')
    expect(viewerData(screen.getByTestId('synthetic-viewer-2d-axial')).interactionMode).toBe('navigate')
    await user.click(screen.getByRole('button', { name: '2D', exact: true }))
    expect(pan().disabled).toBe(true)
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
