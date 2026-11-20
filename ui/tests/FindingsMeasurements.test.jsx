import React from 'react'
import { it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import FindingsPanel from '../src/components/FindingsPanel.jsx'
import StructurePopover from '../src/components/StructurePopover.jsx'
import { LESION_DIMENSIONS_POLICY } from '../src/lib/lesionDimensions.js'

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
  // Summary card (lesion + pancreas) plus the structures list and provenance facts.
  expect(screen.getAllByText('Checking…')).toHaveLength(5)
})

it('shows per-lesion lengths in centimeters and clears them when the prediction changes', () => {
  const measurement = { ...ready.measurement, lesionDimensions: {
    policy: LESION_DIMENSIONS_POLICY, status: 'ready',
    components: [
      { id: 1, volumeMl: 2, superiorInferiorMm: 24, calipers: { nativeSlice: 3, axes: [{ lengthMm: 28 }, { lengthMm: 19 }] } },
      { id: 2, volumeMl: 1, superiorInferiorMm: 10, calipers: null,
        caliperUnavailableReason: 'The native slice axes are not perpendicular.' },
    ],
  } }
  const { rerender } = render(<FindingsPanel {...props} measurementState={{ status: 'ready', measurement }} />)
  const dimensions = within(screen.getByRole('region', { name: 'Predicted lesion dimensions' }))
  expect(dimensions.getByText('2.80 × 1.90 cm')).toBeTruthy()
  expect(dimensions.getByText('2.40 cm')).toBeTruthy()
  expect(dimensions.getByText('2.00 mL')).toBeTruthy()
  expect(dimensions.getByText(/Prepared slice 4/)).toBeTruthy()
  expect(dimensions.getByText('1 more predicted lesion')).toBeTruthy()
  rerender(<FindingsPanel {...props} measurementState={{ status: 'loading' }} />)
  expect(screen.queryByRole('region', { name: 'Predicted lesion dimensions' })).toBeNull()
})

it('identifies source-grid calipers and exports the verified run mask from its checked URL', () => {
  const calipers = { nativeSlice: 3, plane: 'axial', axes: [{ lengthMm: 28 }, { lengthMm: 19 }] }
  const measurement = { ...ready.measurement,
    lesionDimensions: {
      policy: LESION_DIMENSIONS_POLICY, status: 'ready',
      components: [{ id: 1, volumeMl: 3, superiorInferiorMm: 24, calipers }],
    },
    pancreasDimensions: { status: 'ready', superiorInferiorMm: 85, calipers },
  }
  render(<FindingsPanel {...props} verifiedRun sourceSlice predictionUrl="blob:verified-mask"
    caseData={{ ...props.caseData, files: { pred: 'prediction.nii.gz' } }}
    measurementState={{ status: 'ready', measurement }} onInspectPancreas={vi.fn()} />)
  expect(screen.getAllByText(/Source slice 4/)).toHaveLength(2)
  expect(screen.getByText(/PanTS 00000001 · Verified prediction/)).toBeTruthy()
  const download = screen.getByRole('link', { name: 'Export prediction (NIfTI)', hidden: true })
  expect(download.getAttribute('href')).toBe('blob:verified-mask')
})

it('exposes unavailable lesion status on a verified run with no flag or verified measurements', () => {
  render(<FindingsPanel {...props} verifiedRun finding={{}}
    measurementState={{ status: 'unavailable', reason: 'The outline geometry could not be measured.' }} />)
  expect(within(screen.getByRole('list', { name: 'Structures in this prediction' })).getByText('Lesion status unavailable')).toBeTruthy()
  expect(within(screen.getByRole('region', { name: 'Finding summary' })).getByText('Lesion status unavailable')).toBeTruthy()
  expect(screen.getByText('The outline geometry could not be measured.')).toBeTruthy()
  expect(screen.queryByText('None predicted')).toBeNull()
  expect(screen.queryByRole('link', { name: 'Export prediction (NIfTI)', hidden: true })).toBeNull()
})

it('displays zero total lesion volume without equating it with absence of disease', () => {
  render(<FindingsPanel {...props} finding={{ ...legacy, lesionFlagged: false }}
    measurementState={{ status: 'ready', measurement: { ...ready.measurement, lesionMl: 0, lesionVoxels: 0 } }} />)
  expect(within(screen.getByRole('list', { name: 'Structures in this prediction' })).getByText('0.00')).toBeTruthy()
  expect(screen.getByText(/does not establish that no lesion is present/)).toBeTruthy()
})

it('retains legacy callers while measurements are absent', () => {
  render(<FindingsPanel {...props} />)
  expect(within(screen.getByRole('list', { name: 'Structures in this prediction' })).getByText('15.63')).toBeTruthy()
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
