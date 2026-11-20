import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import ValidationComparison from '../src/components/ValidationComparison.jsx'

vi.mock('../src/components/NiivueViewer.jsx', () => ({
  default: ({ sources, mode, activePlane, showFull, preferNativeFull, ctOpacity, interactionMode, label }) =>
    <output aria-label={label}>{JSON.stringify({ sources, mode, activePlane, showFull, preferNativeFull, ctOpacity, interactionMode })}</output>,
}))

const study = {
  files: { ct: 'synthetic-region.nii.gz', ct_full: 'synthetic-abdomen.nii.gz', ct_full_native: 'synthetic-native-abdomen.nii.gz' },
  gt_has_lesion: true,
  pred_has_lesion: true,
  dice_pancreas: 0.855,
  dice_lesion: 0.919,
  lesion_volume_mm3: 15630,
}
const comparison = (caseId, caseData = study) => <ValidationComparison
  caseId={caseId} caseData={caseData} caseOptions={[]} />
const viewer = (caseId, title = 'model prediction') =>
  JSON.parse(screen.getByLabelText(`${caseId} ${title}`).textContent)

it('opens the full abdomen, keeps Pan available in both modes, and retains the comparison statistics', async () => {
  const user = userEvent.setup()
  render(comparison('synthetic-study'))
  await screen.findByLabelText('synthetic-study model prediction')
  const titles = ['model prediction', 'reference annotation', 'combined overlay']
  titles.forEach(title => expect(viewer('synthetic-study', title)).toMatchObject({
    mode: '3d', showFull: true, preferNativeFull: false, ctOpacity: 0.44, interactionMode: 'rotate',
  }))
  expect(screen.getByText('0.919')).toBeTruthy()
  expect(screen.getByText('15.63 cm³')).toBeTruthy()

  await user.click(screen.getByRole('button', { name: 'Pan', exact: true }))
  titles.forEach(title => expect(viewer('synthetic-study', title).interactionMode).toBe('pan'))
  await user.click(screen.getByRole('button', { name: '2D planes' }))
  await user.click(screen.getByRole('button', { name: 'Coronal' }))
  titles.forEach(title => expect(viewer('synthetic-study', title)).toMatchObject({
    mode: '2d', activePlane: 'coronal', showFull: false, interactionMode: 'pan',
  }))
  await user.click(screen.getByRole('button', { name: 'Abdomen', exact: true }))
  expect(viewer('synthetic-study')).toMatchObject({ mode: '3d', showFull: true, interactionMode: 'pan' })
  await user.click(screen.getByRole('button', { name: 'Surfaces', exact: true }))
  expect(viewer('synthetic-study')).toMatchObject({ mode: '3d', ctOpacity: 0 })
})

it('uses the prepared region honestly for a crop-only comparison study', async () => {
  const { rerender } = render(comparison('full-study'))
  await screen.findByLabelText('full-study model prediction')
  rerender(comparison('crop-study', { ...study, files: { ct: 'synthetic-region.nii.gz' } }))
  await screen.findByLabelText('crop-study model prediction')
  expect(screen.getByRole('button', { name: 'Abdomen', exact: true }).disabled).toBe(true)
  expect(screen.getByRole('button', { name: 'Region', exact: true }).getAttribute('aria-pressed')).toBe('true')
  expect(viewer('crop-study')).toMatchObject({ mode: '3d', showFull: false, ctOpacity: 0.44 })
})
