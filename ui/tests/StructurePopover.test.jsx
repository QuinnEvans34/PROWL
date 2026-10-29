import React from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import StructurePopover from '../src/components/StructurePopover.jsx'
import LiteratureSearchPanel from '../src/components/LiteratureSearchPanel.jsx'
import { structureQuestions } from '../src/lib/structureQuestions.js'

const finding = { lesionFlagged: true, volumeMm3: 15630, diameterMm: 31 }

it('shows published facts for a predicted lesion and offers general literature questions', async () => {
  const user = userEvent.setup()
  const onAsk = vi.fn()
  render(<StructurePopover object={{ source: 'pred', anatomy: 'lesion' }} anchor={{ left: 10, top: 10 }}
    finding={finding} overlap={{}} comparing={false} gtHasLesion onAsk={onAsk} onClose={() => {}} />)
  expect(screen.getByText('15.63 cm³')).toBeTruthy()
  expect(screen.getByText('31 mm')).toBeTruthy()
  expect(screen.getByText(/not from this scan/)).toBeTruthy()
  const [first] = structureQuestions({ source: 'pred', anatomy: 'lesion' })
  await user.click(screen.getByRole('button', { name: first }))
  expect(onAsk).toHaveBeenCalledWith(first)
})

it('describes a difference region by its Dice only, never as a finding', () => {
  render(<StructurePopover object={{ source: 'difference', anatomy: 'pancreas', region: 'predOnly' }} anchor={null}
    finding={finding} overlap={{ pancreas: 0.855 }} comparing gtHasLesion onAsk={() => {}} onClose={() => {}} />)
  expect(screen.getByText('Prediction only')).toBeTruthy()
  expect(screen.getByText('0.855')).toBeTruthy()
  expect(screen.queryByText(/cm³/)).toBeNull()
})

it('keeps suggested structure questions general (no scan-specific wording)', () => {
  const all = ['pancreas', 'lesion'].flatMap((anatomy) => ['pred', 'gt', 'difference']
    .flatMap((source) => structureQuestions({ source, anatomy, region: 'agreement' })))
  all.forEach((text) => expect(text).not.toMatch(/\bthis (scan|patient|lesion|pancreas)\b/i))
})

it('fills the Ask box from a draft request without sending it', async () => {
  const search = vi.fn()
  const { rerender } = render(<LiteratureSearchPanel variant="panel" search={search} />)
  rerender(<LiteratureSearchPanel variant="panel" search={search} draftRequest={{ text: 'Why can pancreas boundaries be hard to outline on CT?', token: 1 }} />)
  expect(screen.getByLabelText('Literature question').value).toBe('Why can pancreas boundaries be hard to outline on CT?')
  expect(search).not.toHaveBeenCalled()
})
