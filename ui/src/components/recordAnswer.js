import config from '../../../configs/evidence/record-answer-v1.json'
import wording from '../../../configs/evidence/record-answer-wording-v1.json'
import catalog from '../../../configs/evidence/source-facts-disease-v1.json'

// Verify the displayed prose itself, not just a model's self-reported checks.
export function validateRecordAnswer(result, request, validateSources) {
  const fail = () => { throw new Error('Invalid reviewed-record answer') }
  if (result.schema_version !== 'prowl-record-answer-response-v1' || result.answer_policy !== config.version
    || !['not_called', 'completed', 'fallback'].includes(result.generation)) fail()
  validateSources({ ...result, schema_version: 'prowl-development-search-response-v1', generation: 'not_called', answer: null }, request)
  if (result.record_selection.status !== 'matched') {
    if (result.generation !== 'not_called' || result.answer !== null) fail()
    return result
  }
  const a = result.answer, generated = result.generation === 'completed'
  if (!a || !['completed', 'fallback'].includes(result.generation) || a.status !== 'summarized'
    || a.policy !== config.version || a.prompt_sha256 !== config.prompt_sha256
    || a.wording_content_sha256 !== config.wording_content_sha256
    || a.validation !== 'complete_reviewed_units_and_exact_citations'
    || a.quality !== 'engineering_reviewed_independent_review_pending'
    || a.provenance !== (generated ? 'local_model_composition' : 'reviewed_source_fallback')
    || a.model !== (generated ? config.model : null) || a.model_sha256 !== (generated ? config.model_sha256 : null)
    || (generated ? a.failure !== null : !['timeout', 'model_unavailable', 'incomplete', 'invalid_composition'].includes(a.failure))
    || a.scope !== config.scope || a.limitation !== config.limitation
    || !Array.isArray(a.claims) || a.claims.length < 1 || a.claims.length > 6) fail()
  const ids = result.record_selection.matches.map(m => m.record_id)
  const observed = new Map(ids.map(id => [id, []])), blocks = [], counts = new Map()
  for (const claim of a.claims) {
    if (!ids.includes(claim.record_id) || !Array.isArray(claim.units) || !claim.units.length || claim.units.length > 4) fail()
    const rid = claim.record_id, record = catalog.records.find(r => r.id === rid), units = wording.records[rid].units
    if (blocks.at(-1) !== rid) blocks.push(rid)
    counts.set(rid, (counts.get(rid) || 0) + 1)
    const texts = [], pids = new Set(), kinds = new Set()
    for (const choice of claim.units) {
      const unit = units.find(u => u.id === choice.unit_id)
      if (!unit || !Number.isInteger(choice.wording) || ![0, 1].includes(choice.wording)) fail()
      observed.get(rid).push(unit.id); texts.push(unit.wordings[choice.wording]); kinds.add(unit.qualification)
      unit.facts.forEach(i => record.facts[i].evidence.forEach(sid => pids.add(catalog.spans[sid].passage_id)))
    }
    const sources = result.evidence.filter(e => pids.has(e.record.passage.passage_id))
    if (kinds.size !== 1 || claim.text !== texts.join(' ') || !Array.isArray(claim.citations)
      || sources.length !== pids.size || claim.citations.length !== sources.length
      || !claim.citations.every((c, i) => c.rank === sources[i].rank && c.quote === sources[i].record.text)) fail()
  }
  if (blocks.length !== ids.length || ids.some(id => counts.get(id) > 2
    || JSON.stringify(observed.get(id)) !== JSON.stringify(wording.records[id].units.map(u => u.id)))) fail()
  return result
}
