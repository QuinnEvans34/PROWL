import searchConfig from '../../../configs/evidence/development-study-search-v4.json'
import catalog from '../../../configs/evidence/source-facts-ct-study-v4.json'
import config from '../../../configs/evidence/ct-study-answer-v4.json'
import wording from '../../../configs/evidence/ct-study-answer-wording-v4.json'
import { validateMeasurementSources } from './measurementAnswer'
import { validateRecordAnswer } from './recordAnswer'

export function validateStudySources(result, request, validateSearch) {
  return validateMeasurementSources(result, request, validateSearch, {
    searchConfig, catalog, reasons: ['selected_ct_visibility', 'selected_ct_study_limits', 'selected_ct_reader_variation', 'selected_ct_radiomics_limits', 'selected_ct_contour_protocol', ...catalog.records.filter(r => !r.topic.startsWith('ct_')).map(r => 'selected_'+r.topic)],
  })
}

export function validateStudyAnswer(result, request, validateSources) {
  if (result.retrieval_policy !== searchConfig.retriever) throw new Error('Wrong study policy')
  return validateRecordAnswer(result, request, validateSources, {
    config, wording, catalog, schema: 'prowl-study-answer-response-v1',
  })
}
