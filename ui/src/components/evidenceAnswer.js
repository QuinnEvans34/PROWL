const policy = 'evidence-led-answer-v1'
const models = { 'qwen3:30b-a3b-instruct-2507-q4_K_M': '19e422b0231392335cfc49cfd172de7034bb1aeabb08aa307cce745c60b272fe', 'qwen2.5:14b': '7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6', 'qwen3:8b': '500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41',
  'qwen3:30b': 'ad815644918f0eaab341c12b67837cc6dd4562342cdaf118f83d5d554cb37226' }

// Transport integrity only. Semantic support is checked separately on the server;
// neither a valid JSON envelope nor an exact citation proves clinical correctness.
export function validateEvidenceAnswer(result, request, validateSearch) {
  const fail = () => { throw new Error('Invalid evidence-led answer') }
  if (result?.schema_version !== 'prowl-evidence-answer-response-v1'
    || result.answer_policy !== policy || result.retrieval_policy !== policy
    || !['not_called', 'completed', 'unavailable'].includes(result.generation)) fail()
  if (result.state === 'retrieval_failed' && (result.generation !== 'unavailable' || result.evidence?.length)) fail()
  validateSearch({ ...result, state: result.state === 'retrieval_failed' ? 'no_results' : result.state, schema_version: 'prowl-development-search-response-v1',
    generation: 'not_called', answer: null }, request, 50)
  if (result.message !== undefined && (typeof result.message !== 'string' || result.message.length > 1000)) fail()
  if (result.generation !== 'completed') {
    if (result.answer !== null) fail()
    return result
  }
  const a = result.answer
  if (result.state !== 'evidence_unassessed' || !a || a.policy !== policy
    || !Object.hasOwn(models, a.model) || a.model_sha256 !== models[a.model]
    || a.validation !== 'canonical_citations_and_separate_criteria'
    || a.quality !== 'development_regression'
    || !['summarized', 'insufficient', 'refused'].includes(a.status)
    || typeof a.limitation !== 'string' || a.limitation.length > 1000
    || (['insufficient', 'refused'].includes(a.status) && !a.limitation.trim())
    || (a.status === 'refused' && a.claims?.length)
    || !Array.isArray(a.claims) || a.claims.length > 8
    || (a.status === 'summarized' && !a.claims.length)
    || !a.claims.every(c => typeof c.text === 'string' && c.text.trim() && c.text.length <= 1800
      && Array.isArray(c.citations) && c.citations.length >= 1 && c.citations.length <= 8
      && new Set(c.citations.map(x => x.rank)).size === c.citations.length
      && c.citations.every(x => Number.isInteger(x.rank) && typeof x.quote === 'string'
        && x.quote === result.evidence.find(e => e.rank === x.rank)?.record.text))) fail()
  return result
}
