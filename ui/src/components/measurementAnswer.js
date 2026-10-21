import searchConfig from '../../../configs/evidence/development-measurement-search-v1.json'
import catalog from '../../../configs/evidence/source-facts-measurement-v1.json'
import config from '../../../configs/evidence/measurement-answer-v1.json'
import wording from '../../../configs/evidence/measurement-answer-wording-v1.json'
import { validateRecordAnswer } from './recordAnswer'

export function validateMeasurementSources(result, request, validateSearch) {
  const fail = () => { throw new Error('Invalid measurement method selection') }
  validateSearch(result, request, 20)
  const s = result.record_selection
  if (result.retrieval_policy !== searchConfig.retriever || s?.policy !== searchConfig.retriever
    || !['matched', 'dense_fallback', 'not_searched'].includes(s.status)
    || !Array.isArray(s.matches) || s.matches.length > 1
    || (s.status === 'matched') !== (s.matches.length === 1)
    || (s.status === 'not_searched') !== (result.state === 'not_searched')
    || (s.status !== 'matched' && result.evidence.length > 5)
    || (s.status === 'matched' && s.reason !== 'selected_ct_measurement_method_not_patient_interpretation')) fail()
  const returned = new Set(result.evidence.map(e => e.record.passage.passage_id)), expected = new Set()
  for (const m of s.matches) {
    const r = catalog.records.find(r => r.id === m.record_id)
    if (!r || r.topic !== m.topic || !Number.isFinite(m.score) || m.score <= 0
      || JSON.stringify(m.anchor_passage_ids) !== JSON.stringify(r.retrieval_anchors)
      || !Array.isArray(m.evidence_passage_ids)) fail()
    const required = new Set(r.facts.flatMap(f => f.evidence.map(id => catalog.spans[id].passage_id)))
    if (new Set(m.evidence_passage_ids).size !== required.size || m.evidence_passage_ids.length !== required.size
      || !m.evidence_passage_ids.every(id => required.has(id) && returned.has(id))) fail()
    required.forEach(id => expected.add(id))
  }
  if (s.status === 'matched' && (returned.size !== expected.size || ![...expected].every(id => returned.has(id)))) fail()
  return result
}

export function validateMeasurementAnswer(result, request, validateSources) {
  if (result.retrieval_policy !== searchConfig.retriever) throw new Error('Wrong measurement policy')
  return validateRecordAnswer(result, request, validateSources, {
    config, wording, catalog, schema: 'prowl-measurement-answer-response-v1',
  })
}
