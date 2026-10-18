// DICOM import — frontend adapter boundary (docs/.../08-COMPONENT-AND-INTEGRATION-SPEC.md §5).
//
// NO REAL ADAPTER EXISTS. The analysis pipeline accepts mm NIfTI only
// (src/inference/autonomous_cascade_v1.py::run_case); DICOM conversion is a separate,
// not-yet-built ingestion service. The UI must not parse, repair, or convert DICOM.
//
// Contract a future ingestion service adapter must satisfy:
//   capabilities: { available, reason, inputs: ['dicom-folder'|'dicom-zip'|'nifti'], local, cancellable, reportsStages }
//   inspect(selection, signal) -> { studies: [{ studyKey, series: [SeriesCandidate] }], warnings: [] }
//     SeriesCandidate: { seriesKey, modality, description, instanceCount, orientation, spacingMm,
//                        eligible, reasons: [], warnings: [] }   // all values reported by the validator
//   importSeries(seriesKey, signal) -> { studyHandle } | throws ImportError({ code })
//   ImportError codes: unsupported_format, unsupported_modality, ambiguous_series, incomplete_input,
//                      conversion_failed, duplicate_study, service_unavailable, cancelled
// Selecting files must never start model inference, and files must not leave the workstation
// unless an approved service explicitly says so.

export const IMPORT_ERRORS = {
  unsupported_format: 'These files are not a supported CT format.',
  unsupported_modality: 'This series is not CT. Only CT series can be imported.',
  ambiguous_series: 'The selection mixes series that cannot be combined. Choose one series.',
  incomplete_input: 'Some images in this series are missing, so it cannot be assembled reliably.',
  conversion_failed: 'The series could not be converted. Nothing was imported.',
  duplicate_study: 'This study is already in your list. Open the existing study instead.',
  service_unavailable: 'The import service is not available.',
}

export const unavailableAdapter = {
  id: 'unavailable',
  capabilities: {
    available: false,
    reason: 'DICOM import is not connected on this workstation. The analysis pipeline currently accepts prepared NIfTI studies; DICOM conversion requires a validated ingestion service that has not been built yet.',
    inputs: [],
    local: true,
    cancellable: false,
    reportsStages: false,
  },
  async inspect() { throw Object.assign(new Error(IMPORT_ERRORS.service_unavailable), { code: 'service_unavailable' }) },
  async importSeries() { throw Object.assign(new Error(IMPORT_ERRORS.service_unavailable), { code: 'service_unavailable' }) },
}

// Example walkthrough data. Entirely synthetic, never derived from files, never imported.
export const EXAMPLE_SERIES = [
  {
    seriesKey: 'example-1', modality: 'CT', description: 'Scout / localizer', instanceCount: 2,
    orientation: 'Not volumetric', spacingMm: null, eligible: false,
    reasons: ['Localizer images are not a volumetric series.'], warnings: [],
  },
  {
    seriesKey: 'example-2', modality: 'CT', description: 'Abdomen · portal venous · axial', instanceCount: 240,
    orientation: 'Axial', spacingMm: [0.78, 0.78, 1.0], eligible: true, reasons: [], warnings: [],
  },
  {
    seriesKey: 'example-3', modality: 'CT', description: 'Abdomen · axial · thick', instanceCount: 48,
    orientation: 'Axial', spacingMm: [0.78, 0.78, 5.0], eligible: true, reasons: [],
    warnings: ['5 mm slices. Thin-slice series are preferred for pancreas review.'],
  },
  {
    seriesKey: 'example-4', modality: 'SR', description: 'Dose report', instanceCount: 1,
    orientation: '—', spacingMm: null, eligible: false,
    reasons: ['Structured report, not CT images.'], warnings: [],
  },
]

export const initialImportState = { step: 'idle', mode: 'live', selectedSeries: null, error: null, outcome: 'success' }

// idle → selecting → validating → series_selection → importing → ready, plus cancelled / failed.
export function importReducer(state, action) {
  switch (action.type) {
    case 'START_EXAMPLE': return { ...initialImportState, mode: 'example', step: 'selecting' }
    case 'BACK_TO_LIVE': return { ...initialImportState }
    case 'CHOOSE_INPUT': return state.step === 'selecting' ? { ...state, step: 'validating', error: null } : state
    case 'VALIDATED': return state.step === 'validating' ? { ...state, step: 'series_selection' } : state
    case 'SELECT_SERIES': return state.step === 'series_selection' ? { ...state, selectedSeries: action.seriesKey, error: null } : state
    case 'SET_OUTCOME': return { ...state, outcome: action.outcome }
    case 'CONFIRM': {
      if (state.step !== 'series_selection' || !state.selectedSeries) return state
      const series = EXAMPLE_SERIES.find((item) => item.seriesKey === state.selectedSeries)
      if (!series?.eligible) return { ...state, error: series?.modality !== 'CT' ? 'unsupported_modality' : 'ambiguous_series' }
      return { ...state, step: 'importing', error: null }
    }
    case 'IMPORT_RESULT':
      if (state.step !== 'importing') return state
      return action.error ? { ...state, step: 'failed', error: action.error } : { ...state, step: 'ready', error: null }
    case 'CANCEL': return ['ready', 'failed', 'idle'].includes(state.step) ? state : { ...state, step: 'cancelled', error: null }
    case 'RESTART': return { ...initialImportState, mode: state.mode, step: state.mode === 'example' ? 'selecting' : 'idle' }
    default: return state
  }
}
