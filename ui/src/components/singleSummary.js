import config from '../../../configs/evidence/single-summary-candidate-v1.json'
export function validateSingleSummary(result, request, validateSources) {
  const fail = () => { throw new Error('Invalid candidate summary') }
  if (result.schema_version !== 'prowl-single-summary-response-v1' || result.answer_policy !== config.policy
    || result.state !== 'evidence_unassessed' || !['completed','unavailable'].includes(result.generation)) fail()
  validateSources({...result,schema_version:'prowl-development-search-response-v1',generation:'not_called',answer:null},request)
  if (result.generation === 'unavailable') {
    if (result.answer !== null || typeof result.message !== 'string' || result.message.length > 300) fail()
    return result
  }
  const a=result.answer
  if (!a || Object.entries(config).some(([k,v]) => a[k] !== v)
    || a.provenance !== 'model_synthesized_passages' || a.validation !== 'citation_binding_only'
    || !['supported','partial','none'].includes(a.coverage) || !['summarized','insufficient'].includes(a.status)
    || !Array.isArray(a.claims) || a.claims.length > 3 || (a.coverage==='none') !== (a.claims.length===0)
    || (a.status==='insufficient') !== (a.claims.length===0)
    || typeof a.limitation !== 'string' || a.limitation.length > 300
    || (a.coverage !== 'supported' && !a.limitation.trim())
    || !a.claims.every(c => typeof c.text==='string' && c.text.length>=10 && c.text.length<=1800
      && Array.isArray(c.citations) && c.citations.length>=1 && c.citations.length<=3
      && new Set(c.citations.map(x=>x.rank)).size===c.citations.length
      && c.citations.every(x=>Number.isInteger(x.rank) && typeof x.quote==='string' && x.quote.length>=20
        && x.quote.length<=4000 && result.evidence.find(e=>e.rank===x.rank)?.record.text.includes(x.quote)))) fail()
  return result
}
