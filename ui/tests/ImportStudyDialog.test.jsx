import React, { useState } from 'react'
import { expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ImportStudyDialog from '../src/components/ImportStudyDialog.jsx'
import { importReducer, initialImportState } from '../src/lib/importAdapter.js'

function Harness({ onOpenStudies = () => {} }) {
  const [open, setOpen] = useState(false)
  return <>
    <button onClick={() => setOpen(true)}>Import CT</button>
    {open && <ImportStudyDialog onClose={() => setOpen(false)} onOpenStudies={onOpenStudies} />}
  </>
}

it('shows an honest unavailable state with no working file picker in live mode', async () => {
  const user = userEvent.setup()
  render(<Harness />)
  await user.click(screen.getByRole('button', { name: 'Import CT' }))
  expect(screen.getByRole('dialog', { name: 'Import CT study' })).toBeTruthy()
  expect(screen.getByText(/DICOM import isn’t connected yet/)).toBeTruthy()
  expect(document.querySelector('input[type=file]')).toBeNull()
  expect(screen.queryByText(/Example/)).toBeNull()
})

it('closes on Escape and returns focus to the opener', async () => {
  const user = userEvent.setup()
  render(<Harness />)
  const opener = screen.getByRole('button', { name: 'Import CT' })
  await user.click(opener)
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.activeElement).toBe(opener)
})

it('walks the labeled example through rejection, selection, failure and cancellation', async () => {
  const user = userEvent.setup()
  render(<Harness />)
  await user.click(screen.getByRole('button', { name: 'Import CT' }))
  await user.click(screen.getByRole('button', { name: /See the example walkthrough/ }))
  expect(screen.getByRole('note').textContent).toMatch(/No files are read/)
  await user.click(screen.getByRole('button', { name: 'Use example folder' }))
  await user.click(screen.getByRole('button', { name: 'Show example result' }))
  await user.click(screen.getByLabelText(/Scout \/ localizer/))
  await user.click(screen.getByRole('button', { name: 'Import selected series' }))
  expect(screen.getByRole('alert').textContent).toMatch(/not a volumetric series/)
  await user.click(screen.getByLabelText(/portal venous/))
  await user.click(screen.getByRole('button', { name: 'Import selected series' }))
  await user.click(screen.getByRole('button', { name: 'Conversion fails' }))
  expect(screen.getByRole('alert').textContent).toMatch(/No partial study was added/)
  await user.click(screen.getByRole('button', { name: 'Start again' }))
  await user.click(screen.getByRole('button', { name: 'Cancel import' }))
  expect(screen.getByText('Import cancelled')).toBeTruthy()
})

it('only reaches ready through an explicit import result, never by elapsed time', () => {
  let state = importReducer(initialImportState, { type: 'START_EXAMPLE' })
  state = importReducer(state, { type: 'IMPORT_RESULT' })
  expect(state.step).toBe('selecting')
  for (const action of [{ type: 'CHOOSE_INPUT' }, { type: 'VALIDATED' }, { type: 'SELECT_SERIES', seriesKey: 'example-2' }, { type: 'CONFIRM' }]) state = importReducer(state, action)
  expect(state.step).toBe('importing')
  expect(importReducer(state, { type: 'IMPORT_RESULT', error: 'duplicate_study' })).toMatchObject({ step: 'failed', error: 'duplicate_study' })
  expect(importReducer(state, { type: 'IMPORT_RESULT' }).step).toBe('ready')
})
