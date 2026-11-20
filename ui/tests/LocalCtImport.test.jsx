import { expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LocalCtImport from '../src/components/LocalCtImport.jsx'
import { prepareLocalCt } from '../src/lib/localCtImport.js'

vi.mock('../src/lib/localCtImport.js', () => ({ prepareLocalCt: vi.fn() }))

it('requires de-identification confirmation and transfers the local CT only on an explicit open', async () => {
  const user = userEvent.setup()
  const study = { caseData: { spacing_mm: [1, 2, 3] }, geometry: { shape: [6, 7, 8] }, release: vi.fn() }
  prepareLocalCt.mockResolvedValue(study)
  const onOpenStudy = vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true)
  const { unmount } = render(<LocalCtImport onOpenStudy={onOpenStudy} />)
  expect(screen.queryByLabelText('Choose a NIfTI CT')).toBeNull()
  await user.click(screen.getByRole('checkbox'))
  const input = screen.getByLabelText('Choose a NIfTI CT')
  await user.upload(input, new File(['synthetic'], 'synthetic.nii'))
  const open = await screen.findByRole('button', { name: 'Open CT in Workbench' })
  expect(onOpenStudy).not.toHaveBeenCalled()
  await user.click(open)
  await user.click(open)
  expect(onOpenStudy).toHaveBeenLastCalledWith(study)
  unmount()
  expect(study.release).not.toHaveBeenCalled()
})
