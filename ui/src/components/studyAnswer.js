import searchConfig from '../../../configs/evidence/development-study-search-v2.json'
import catalog from '../../../configs/evidence/source-facts-ct-study-v2.json'
import config from '../../../configs/evidence/ct-study-answer-v2.json'
import wording from '../../../configs/evidence/ct-study-answer-wording-v2.json'
import { validateMeasurementSources } from './measurementAnswer'
import { validateRecordAnswer } from './recordAnswer'

export function validateStudySources(result, request, validateSearch) {
  return validateMeasurementSources(result, request, validateSearch, {
    searchConfig, catalog, reasons: ['selected_ct_visibility', 'selected_ct_study_limits', 'selected_ct_reader_variation', 'selected_ct_radiomics_limits', 'selected_ct_contour_protocol'],
  })
}

export function validateStudyAnswer(result, request, validateSources) {
  if (result.retrieval_policy !== searchConfig.retriever) throw new Error('Wrong study policy')
  return validateRecordAnswer(result, request, validateSources, {
    config, wording, catalog, schema: 'prowl-study-answer-response-v1',
  })
}
