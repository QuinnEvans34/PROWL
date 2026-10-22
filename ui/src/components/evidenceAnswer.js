const policy = 'evidence-led-answer-v1'
const modelSha = '500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41'

// Transport integrity only. Semantic support is checked separately on the server;
// neither a valid JSON envelope nor an exact citation proves clinical correctness.
export function validateEvidenceAnswer(result, request, validateSearch) {
  const fail = () => { throw new Error('Invalid evidence-led answer') }
  if (result?.schema_version !== 'prowl-evidence-answer-response-v1'
    || result.answer_policy !== policy || result.retrieval_policy !== policy
    || !['not_called', 'completed', 'unavailable'].includes(result.generation)) fail()
  validateSearch({ ...result, schema_version: 'prowl-development-search-response-v1',
    generation: 'not_called', answer: null }, request, 50)
  if (result.message !== undefined && (typeof result.message !== 'string' || result.message.length > 1000)) fail()
  if (result.generation !== 'completed') {
    if (result.answer !== null) fail()
    return result
  }
  const a = result.answer
  if (result.state !== 'evidence_unassessed' || !a || a.policy !== policy
    || a.model !== 'qwen3:8b' || a.model_sha256 !== modelSha
    || a.validation !== 'canonical_citations_and_separate_criteria'
    || a.quality !== 'development_regression'
    || !['summarized', 'insufficient'].includes(a.status)
    || typeof a.limitation !== 'string' || a.limitation.length > 1000
    || (a.status === 'insufficient' && !a.limitation.trim())
    || !Array.isArray(a.claims) || a.claims.length > 8
    || (a.status === 'summarized' && !a.claims.length)
    || !a.claims.every(c => typeof c.text === 'string' && c.text.trim() && c.text.length <= 1800
      && Array.isArray(c.citations) && c.citations.length >= 1 && c.citations.length <= 8
      && new Set(c.citations.map(x => x.rank)).size === c.citations.length
      && c.citations.every(x => Number.isInteger(x.rank) && typeof x.quote === 'string'
        && x.quote === result.evidence.find(e => e.rank === x.rank)?.record.text))) fail()
  return result
}
