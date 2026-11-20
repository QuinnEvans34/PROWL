import React from 'react'
import { expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ReviewWorkspace from '../src/components/ReviewWorkspace.jsx'
import ValidationComparison from '../src/components/ValidationComparison.jsx'
import LiteratureSearchPanel from '../src/components/LiteratureSearchPanel.jsx'
import { workspaceProps } from './fixtures/workspace.js'

vi.mock('../src/components/NiivueViewer.jsx', () => import('./fixtures/MockViewer.jsx'))

const preparedFiles = workspaceProps().caseData.files
const modeButton = name => screen.getByRole('button', { name, exact: true })
const viewerData = node => JSON.parse(node.querySelector('pre').textContent)

it('keeps the prediction hidden and offers no reference comparison before a prediction is shown', async () => {
  render(<ReviewWorkspace {...workspaceProps({ caseData: { files: { ...preparedFiles, pred: 'p.nii.gz', gt: 'g.nii.gz' }, gt_has_lesion: false } })} />)
  expect(viewerData(await screen.findByRole('status', { name: 'Synthetic viewer stub' }))).toMatchObject({ mode: '3d', showFull: true, visibleSources: [] })
  expect(modeButton('Abdomen').getAttribute('aria-pressed')).toBe('true')
  expect(screen.getByRole('button', { name: /^Prediction/ }).disabled).toBe(true)
  expect(screen.queryByRole('button', { name: /^Reference/ })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Compare with reference' })).toBeNull()
  expect(screen.getByRole('button', { name: 'Show saved prediction' })).toBeTruthy()
})

it('treats an absent reference as a complete review, not a missing step', async () => {
  render(<ReviewWorkspace {...workspaceProps({ isCurated: true, caseData: { files: { ...preparedFiles, pred: 'p.nii.gz' }, gt_has_lesion: false } })} />)
  expect(viewerData(await screen.findByRole('status', { name: 'Synthetic viewer stub' }))).toMatchObject({ mode: '3d', showFull: true })
  expect(screen.queryByRole('button', { name: 'Compare with reference' })).toBeNull()
  expect(screen.getAllByText(/No reference annotation/).length).toBeGreaterThan(0)
  expect(screen.queryByText(/Dice/)).toBeNull()
})

it('explains an incompatible reference instead of overlaying it', async () => {
  render(<ReviewWorkspace {...workspaceProps({ isCurated: true, referenceCompatibility: 'incompatible', caseData: { files: { ...preparedFiles, pred: 'p.nii.gz', gt: 'g.nii.gz' }, gt_has_lesion: false } })} />)
  expect(viewerData(await screen.findByRole('status', { name: 'Synthetic viewer stub' }))).toMatchObject({ mode: '3d', showFull: true, visibleSources: ['pred'] })
  expect(screen.queryByRole('button', { name: 'Compare with reference' })).toBeNull()
  expect(screen.getAllByText(/does not match/).length).toBeGreaterThan(0)
})

it('changes 2D/3D, keeps the study list preference, and resets the view after switching study', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<ReviewWorkspace {...workspaceProps()} />)
  expect(viewerData(await screen.findByRole('status', { name: 'Synthetic viewer stub' })).mode).toBe('3d')
  await user.click(modeButton('2D'))
  await waitFor(() => expect(screen.getAllByRole('status', { name: 'Synthetic viewer stub' })).toHaveLength(3))
  await user.click(modeButton('Split'))
  const stubs = await screen.findAllByRole('status', { name: 'Synthetic viewer stub' })
  expect(stubs.map((stub) => JSON.parse(stub.textContent.replace(/^[^{]*/, '')).mode).sort()).toEqual(['2d', '2d', '2d', '3d'])
  await user.click(modeButton('Region'))
  expect(modeButton('Split').getAttribute('aria-pressed')).toBe('true')
  if (screen.queryByRole('button', { name: 'Collapse study list' })) {
    await user.click(screen.getByRole('button', { name: 'Collapse study list' }))
  }
  expect(screen.getByRole('main').classList.contains('pw-wb--list-closed')).toBe(true)
  expect(screen.getByRole('button', { name: 'Open study list' })).toBeTruthy()
  rerender(<ReviewWorkspace {...workspaceProps({ caseId: 'SYNTHETIC_B' })} />)
  await waitFor(() => expect(modeButton('3D').getAttribute('aria-pressed')).toBe('true'))
  expect(modeButton('Abdomen').getAttribute('aria-pressed')).toBe('true')
  expect(screen.getByRole('main').classList.contains('pw-wb--list-closed')).toBe(true)
})

it('keeps imaging controls usable while the literature service is unavailable', async () => {
  const user = userEvent.setup()
  const search = vi.fn().mockRejectedValue(new Error('Literature unavailable'))
  render(<ReviewWorkspace {...workspaceProps({ askPanel: <LiteratureSearchPanel search={search} findSources={search} /> })} />)
  expect(viewerData(await screen.findByRole('status', { name: 'Synthetic viewer stub' })).mode).toBe('3d')
  await user.click(screen.getByRole('tab', { name: 'Ask PROWL' }))
  await user.type(screen.getByLabelText('Literature question'), 'What is pancreatitis?')
  await user.click(screen.getByRole('button', { name: 'Ask question' }))
  expect(await screen.findByRole('alert')).toBeTruthy()
  await user.click(modeButton('Pan'))
  expect(modeButton('Pan').getAttribute('aria-pressed')).toBe('true')
  expect(viewerData(screen.getByRole('status', { name: 'Synthetic viewer stub' })).interactionMode).toBe('pan')
})

it('offers independent 3D scenes and does not guess a pancreas peel before geometry is available', async () => {
  const user = userEvent.setup()
  const caseData = { files: { ...preparedFiles, pred: 'synthetic-prediction.nii.gz', mesh: { pancreas_pred: 'synthetic-pancreas.obj' } } }
  render(<ReviewWorkspace {...workspaceProps({ caseData, isCurated: true })} />)
  const viewport = await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(screen.getByRole('button', { name: 'Peel to pancreas', exact: true }).disabled).toBe(true)
  expect(modeButton('Abdomen').getAttribute('aria-pressed')).toBe('true')
  await user.click(modeButton('Surfaces'))
  expect(viewerData(viewport).ctOpacity).toBe(0)
  expect(screen.queryByLabelText('Front-to-back CT removal')).toBeNull()
  await user.click(modeButton('Region'))
  expect(viewerData(viewport).showFull).toBe(false)
  await user.click(modeButton('2D'))
  await user.click(modeButton('Abdomen'))
  expect(modeButton('3D').getAttribute('aria-pressed')).toBe('true')
  expect(viewerData(viewport).showFull).toBe(true)
  expect(screen.getByLabelText('Front-to-back CT removal').value).toBe('0')
  await user.click(screen.getByRole('button', { name: 'Viewer controls', exact: true }))
  expect(screen.getByRole('region', { name: 'Viewer controls' })).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Close viewer controls', exact: true }))
  const peel = screen.getByLabelText('Front-to-back CT removal')
  await user.keyboard(']')
  expect(peel.value).toBe('0')
  fireEvent.change(peel, { target: { value: '5' } })
  await waitFor(() => expect(peel.value).toBe('5'))
  await user.click(screen.getByRole('button', { name: 'Restore CT', exact: true }))
  expect(peel.value).toBe('0')
})

it('starts a study with only a prepared crop in 3D Region', async () => {
  render(<ReviewWorkspace {...workspaceProps({ caseData: { files: { ct: preparedFiles.ct } } })} />)
  expect(viewerData(await screen.findByRole('status', { name: 'Synthetic viewer stub' }))).toMatchObject({ mode: '3d', showFull: false })
  expect(modeButton('Region').getAttribute('aria-pressed')).toBe('true')
  expect(modeButton('Abdomen').disabled).toBe(true)
})

it('offers a native-only full abdomen in 3D and keeps the full 2D option unavailable', async () => {
  const user = userEvent.setup()
  const caseData = { files: { ct: preparedFiles.ct, ct_full_native: 'synthetic-native-abdomen.nii.gz' } }
  render(<ReviewWorkspace {...workspaceProps({ caseData })} />)
  const viewport = await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(viewerData(viewport)).toMatchObject({ mode: '3d', showFull: true })
  expect(modeButton('Abdomen').disabled).toBe(false)
  expect(modeButton('Abdomen').getAttribute('aria-pressed')).toBe('true')
  await user.click(modeButton('2D'))
  await user.click(modeButton('View settings'))
  expect(screen.getByRole('checkbox', { name: 'Full abdominal CT in 2D' }).disabled).toBe(true)
})

it.each(['local', 'verified'])('opens %s source CT in 3D before any surfaces are available', async kind => {
  const user = userEvent.setup()
  const assetUrls = { ct: 'blob:synthetic-source' }
  const caseData = { files: { ct: 'synthetic-source.nii.gz' } }
  const sourceProps = kind === 'local'
    ? { localCt: { assetUrls, imageSource: { kind: 'source' } } }
    : { verifiedPrediction: { urls: assetUrls, manifest: { files: {} }, surfaceStatus: 'loading' } }
  render(<ReviewWorkspace {...workspaceProps({ caseData, ...sourceProps })} />)
  const viewport = await screen.findByRole('status', { name: 'Synthetic viewer stub' })
  expect(viewerData(viewport)).toMatchObject({ mode: '3d', assetUrls })
  expect(screen.getByText('Full source CT · 3D')).toBeTruthy()
  expect(modeButton('Abdomen').getAttribute('aria-pressed')).toBe('true')
  expect(modeButton('3D').disabled).toBe(false)
  await user.click(modeButton('Split'))
  expect(modeButton('Split').getAttribute('aria-pressed')).toBe('true')
  expect(screen.getByRole('region', { name: '2D planes' })).toBeTruthy()
  expect(screen.getByRole('region', { name: '3D surfaces' })).toBeTruthy()
})

it('starts all comparison panes in 3D Abdomen and keeps Pan selected between 2D and 3D', async () => {
  const user = userEvent.setup()
  const options = [['SYNTHETIC_A', 'Full CT'], ['SYNTHETIC_B', 'Prepared crop']]
  const props = { caseOptions: options, onSelectCase: vi.fn(), onBack: vi.fn() }
  const { rerender } = render(<ValidationComparison {...props} caseId="SYNTHETIC_A" caseData={{ files: preparedFiles }} />)
  const viewers = () => screen.getAllByRole('status', { name: 'Synthetic viewer stub' }).map(viewerData)
  await waitFor(() => expect(viewers()).toHaveLength(3))
  expect(viewers()).toEqual(Array(3).fill(expect.objectContaining({ mode: '3d', showFull: true, interactionMode: 'rotate' })))
  await user.click(modeButton('Pan'))
  await user.click(modeButton('2D planes'))
  expect(viewers()).toEqual(Array(3).fill(expect.objectContaining({ mode: '2d', interactionMode: 'pan' })))
  await user.click(modeButton('Abdomen'))
  expect(modeButton('Pan').getAttribute('aria-pressed')).toBe('true')
  expect(viewers()).toEqual(Array(3).fill(expect.objectContaining({ mode: '3d', showFull: true, interactionMode: 'pan' })))
  rerender(<ValidationComparison {...props} caseId="SYNTHETIC_B" caseData={{ files: { ct: preparedFiles.ct } }} />)
  expect(viewers()).toEqual(Array(3).fill(expect.objectContaining({ mode: '3d', showFull: false, interactionMode: 'rotate' })))
  expect(modeButton('Region').getAttribute('aria-pressed')).toBe('true')
  expect(modeButton('Abdomen').disabled).toBe(true)
})
