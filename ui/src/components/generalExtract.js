// Exact quotations, not model paraphrases. Semantic selection still needs evaluation.
export function validateGeneralExtract(result, request, validateSources) {
  const fail = () => { throw new Error('Invalid general source answer') }
  if (result.schema_version !== 'prowl-general-extract-response-v1' || result.answer_policy !== 'general-source-extract-v1'
      || result.state !== 'evidence_unassessed' || result.record_selection?.status !== 'dense_fallback'
      || !['completed','unavailable'].includes(result.generation)) fail()
  validateSources({...result,schema_version:'prowl-development-search-response-v1',generation:'not_called',answer:null},request)
  if (result.generation === 'unavailable') {
    if (result.answer !== null || typeof result.message !== 'string' || result.message.length>300) fail()
    return result
  }
  const a=result.answer
  if (!a || a.policy !== result.answer_policy || a.model !== 'qwen3:8b'
      || a.model_sha256 !== '500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41'
      || a.prompt_sha256 !== 'cb216828f532b41c3913f37c668ae25b8f96bd4ca287c476bcad37e601e545d6'
      || a.provenance !== 'model_selected_source_sentences' || a.validation !== 'exact_source_sentences'
      || !['supported','partial','none'].includes(a.coverage) || !['summarized','insufficient'].includes(a.status)
      || !Array.isArray(a.claims) || a.claims.length>6 || (a.status==='insufficient') !== (a.claims.length===0)
      || (a.coverage==='none') !== (a.claims.length===0)
      || typeof a.limitation !== 'string' || a.limitation.length>300
      || !a.claims.every(c=>typeof c.text==='string' && c.text.length>=20 && c.text.length<=4000
        && Array.isArray(c.citations) && c.citations.length===1
        && c.citations[0].quote===c.text && Number.isInteger(c.citations[0].rank)
        && result.evidence.find(e=>e.rank===c.citations[0].rank)?.record.text.includes(c.text))) fail()
  return result
}
