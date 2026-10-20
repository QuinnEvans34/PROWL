import searchConfig from '../../../configs/evidence/development-volume-search-v1.json'
import catalog from '../../../configs/evidence/source-facts-volume-v1.json'
import config from '../../../configs/evidence/volume-answer-v1.json'
import wording from '../../../configs/evidence/volume-answer-wording-v1.json'
import { validateRecordAnswer } from './recordAnswer'

// Same statement-to-field mapping as FactCatalog.render; no server-supplied prose trusted.
const fields = [
  ['object', 'extent', 'quantity', 'unit', 'population', 'sample_size', 'method', 'statistic', 'mean'],
  ['uncertainty', 'uncertainty_kind', 'unit'],
  ['matching'],
  ['population', 'sample_size', 'method'],
]
const projection = { spans: catalog.spans, records: catalog.records.map(record => ({
  id: record.id,
  facts: fields.map(names => ({ evidence: [...new Set(names.flatMap(n => record.fields[n].evidence))] })),
})) }

export const volumeReasons = {
  specify_volume_or_linear_size: 'Do you mean the volume of the whole pancreas, or a length such as the head diameter? The reviewed study results cover whole-pancreas volume measured with MRI.',
  diabetes_population_unspecified: 'Which diabetes group do you mean? The reviewed volume study covers a selected group with well-controlled type 2 diabetes taking only metformin.',
  comparison_groups_unspecified: 'Which study groups would you like to compare? The reviewed MRI study includes a normal-glucose-tolerance comparison group and a group with well-controlled type 2 diabetes taking only metformin.',
  comparison_relationship_unspecified: 'Would you like to compare the two groups’ average whole-pancreas volumes?',
  study_mean_scope_required: 'Are you asking for an average whole-pancreas volume reported in a study? The reviewed MRI results are study-group means, not an individual normal range.',
}

export function validateVolumeSources(result, request, validateSearch) {
  const fail = () => { throw new Error('Invalid volume source selection') }
  validateSearch(result, request, 20)
  const s = result.record_selection
  if (result.retrieval_policy !== searchConfig.retriever || s?.policy !== searchConfig.retriever
    || !['matched', 'dense_fallback', 'not_searched'].includes(s.status)
    || !Array.isArray(s.matches) || s.matches.length > 2
    || (s.status === 'matched') !== (s.matches.length > 0)
    || (s.status === 'not_searched') !== (result.state === 'not_searched')
    || new Set(s.matches.map(m => m.record_id)).size !== s.matches.length
    || (s.status !== 'matched' && result.evidence.length > 5)
    || (s.status === 'matched' && s.reason !== 'selected_study_examples_not_reference_ranges')) fail()
  const returned = new Set(result.evidence.map(e => e.record.passage.passage_id)), expected = new Set()
  for (const match of s.matches) {
    const r = catalog.records.find(r => r.id === match.record_id)
    if (!r || match.population !== r.fields.population.value || !Number.isFinite(match.score) || match.score <= 0
      || !Array.isArray(match.evidence_passage_ids)) fail()
    const required = new Set(Object.values(r.fields).flatMap(f => f.evidence.map(id => catalog.spans[id].passage_id)))
    if (new Set(match.evidence_passage_ids).size !== required.size || match.evidence_passage_ids.length !== required.size
      || !match.evidence_passage_ids.every(id => required.has(id) && returned.has(id))) fail()
    required.forEach(id => expected.add(id))
  }
  if (s.status === 'matched' && (returned.size !== expected.size || ![...expected].every(id => returned.has(id)))) fail()
  return result
}

export function validateVolumeAnswer(result, request, validateSources) {
  if (result.retrieval_policy !== searchConfig.retriever) throw new Error('Wrong volume retrieval policy')
  return validateRecordAnswer(result, request, validateSources, {
    config, wording, catalog: projection, schema: 'prowl-volume-answer-response-v1',
  })
}
