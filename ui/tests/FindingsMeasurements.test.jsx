import React from 'react'
import { it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import FindingsPanel from '../src/components/FindingsPanel.jsx'
import StructurePopover from '../src/components/StructurePopover.jsx'

const legacy = { lesionFlagged: true, volumeMm3: 15630, diameterMm: 31, confidence: 0.95 }
const ready = { status: 'ready', measurement: { pancreasMl: 72, lesionMl: 3, lesionVoxels: 125 } }
const props = { caseId: 'PanTS_00000001', caseData: { files: {}, spacing_mm: [1, 1, 1], gt_has_lesion: true },
  finding: legacy, overlap: {}, hasPrediction: true, predictionFile: 'PanTS_00000001/pred.nii.gz', ranges: {},
  referenceState: 'absent', comparing: false, onStartSummary: vi.fn(), onSetReviewStatus: vi.fn(), modelLabel: 'Prepared model' }
const popover = { object: { source: 'pred', anatomy: 'lesion' }, finding: legacy, overlap: {}, comparing: false,
  onAsk: vi.fn(), onClose: vi.fn() }

it('uses verified outline volumes rather than headline size, score or diameter', () => {
  render(<FindingsPanel {...props} measurementState={ready}
    liveResult={{ source: 'live', scoredAt: 'now', result: { inference_seconds: 3 } }} />)
  const structures = screen.getByRole('list', { name: 'Structures in this prediction' })
  expect(within(structures).getByText('72.00')).toBeTruthy()
  expect(within(structures).getByText('3.00')).toBeTruthy()
  expect(screen.queryByText('15.63')).toBeNull()
  expect(screen.queryByText('31')).toBeNull()
  expect(screen.queryByText('0.95')).toBeNull()
  expect(screen.queryByText(/Live analysis/)).toBeNull()
  expect(screen.getByText(/Whole-organ coverage and model accuracy remain unverified/)).toBeTruthy()
})

it('shows unavailable volumes and the cause rather than restoring legacy values', () => {
  render(<FindingsPanel {...props} measurementState={{ status: 'unavailable', reason: 'Prediction touches the crop edge.' }} />)
  const structures = screen.getByRole('list', { name: 'Structures in this prediction' })
  expect(within(structures).getAllByText('Unavailable')).toHaveLength(2)
  expect(screen.getByText('Prediction touches the crop edge.')).toBeTruthy()
  expect(screen.queryByText('15.63')).toBeNull()
})

it('clears old volumes while the next displayed mask is being checked', () => {
  const { rerender } = render(<FindingsPanel {...props} measurementState={ready} />)
  expect(screen.getAllByText('72.00').length).toBeGreaterThan(0)
  rerender(<FindingsPanel {...props} measurementState={{ status: 'loading' }} />)
  expect(screen.queryByText('72.00')).toBeNull()
  expect(screen.getAllByText('Checking…')).toHaveLength(3)
})

it('displays zero total lesion volume without equating it with absence of disease', () => {
  render(<FindingsPanel {...props} finding={{ ...legacy, lesionFlagged: false }}
    measurementState={{ status: 'ready', measurement: { ...ready.measurement, lesionMl: 0, lesionVoxels: 0 } }} />)
  expect(screen.getByText('0.00')).toBeTruthy()
  expect(screen.getByText(/does not establish that no lesion is present/)).toBeTruthy()
})

it('retains legacy callers while measurements are absent', () => {
  render(<FindingsPanel {...props} />)
  expect(screen.getByText('15.63')).toBeTruthy()
  expect(screen.getByText('31')).toBeTruthy()
  expect(screen.getByText('0.95')).toBeTruthy()
})

it('keeps the structure card consistent with the verified findings', () => {
  const { rerender } = render(<StructurePopover {...popover} measurementState={ready} />)
  expect(screen.getByText('3.00 mL')).toBeTruthy()
  expect(screen.queryByText('15.63 cm³')).toBeNull()
  expect(screen.queryByText('31 mm')).toBeNull()
  rerender(<StructurePopover {...popover} object={{ source: 'pred', anatomy: 'pancreas' }} measurementState={ready} />)
  expect(screen.getByText('72.00 mL')).toBeTruthy()
  expect(screen.queryByText('3.00 mL')).toBeNull()
  rerender(<StructurePopover {...popover} measurementState={{ status: 'unavailable', reason: 'Mask geometry differs.' }} />)
  expect(screen.getByText('Unavailable')).toBeTruthy()
  expect(screen.getByText('Mask geometry differs.')).toBeTruthy()
  expect(screen.queryByText('15.63 cm³')).toBeNull()
})

it('never attaches model volume to a reference annotation', () => {
  render(<StructurePopover {...popover} object={{ source: 'gt', anatomy: 'pancreas' }} measurementState={ready} />)
  expect(screen.getByText('Reference annotation')).toBeTruthy()
  expect(screen.queryByText('72.00 mL')).toBeNull()
})
