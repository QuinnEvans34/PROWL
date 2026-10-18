import { useEffect, useRef, useState } from 'react'
import config from '../../../configs/evidence/development-search-v1.json'
import answerConfig from '../../../configs/evidence/natural-answer-v5.json'
import './GuidedEvidencePanel.css'

const reasons = {
  out_of_scope: 'Use a general literature question. This search cannot diagnose a case, recommend treatment, or disclose private information.',
  case_context_unavailable: 'This search does not have access to your scan. Ask about a general topic, such as pancreatic enlargement.',
  measurement_unavailable: 'Scan measurements are not connected yet. You can search the literature for general measurement or imaging information.',
  pancreas_topic_required: 'Include a pancreatic topic in your question, such as pancreatitis, pancreas size, or PDAC.',
}

export function validateSearch(result, request) {
  if (result?.schema_version !== 'prowl-development-search-response-v1'
    || result.request_id !== request.request_id || result.question !== request.question
    || result.collection !== config.collection || result.generation !== 'not_called' || result.answer !== null
    || result.target?.manifest_sha256 !== config.manifest.sha256
    || result.target?.inventory?.content_sha256 !== config.corpus_content_sha256
    || !['evidence_unassessed', 'no_results', 'not_searched'].includes(result.state)
    || !Array.isArray(result.evidence) || result.evidence.length > 5
    || (result.state === 'evidence_unassessed') !== (result.evidence.length > 0)
    || (result.state === 'not_searched' ? !Object.hasOwn(reasons, result.reason) : result.reason !== null)
    || new Set(result.evidence.map(e => e.record?.passage?.passage_id)).size !== result.evidence.length
    || !result.evidence.every((e, i) => e.rank === i + 1 && Number.isFinite(e.score)
      && typeof e.record?.text === 'string' && e.record.text.length > 0
      && /^psg:[a-f0-9]{64}$/.test(e.record?.passage?.passage_id)
      && typeof e.record?.citation?.title === 'string' && /^PMC\d+$/.test(e.record?.citation?.pmcid)
      && /^\d+$/.test(e.record?.citation?.pmid) && Array.isArray(e.record?.citation?.authors)
      && e.record.citation.authors.every(a => typeof a === 'string')
      && e.record?.rights?.permissions?.display_snippet === true)) throw new Error('Invalid search response')
  return result
}

export function validateAnswer(result, request) {
  if (result?.schema_version !== 'prowl-development-answer-response-v1'
      || !['not_called', 'completed', 'unavailable'].includes(result.generation)) throw new Error('Invalid answer envelope')
  validateSearch({ ...result, schema_version: 'prowl-development-search-response-v1', generation: 'not_called', answer: null }, request)
  if (result.generation !== 'completed') {
    if (result.answer !== null || (result.generation === 'unavailable' && result.state !== 'evidence_unassessed')
      || (result.generation === 'not_called' && result.state === 'evidence_unassessed')) throw new Error('Invalid answer state')
    return result
  }
  const a = result.answer
  if (result.state !== 'evidence_unassessed' || !a || !['summarized', 'insufficient'].includes(a.status)
    || a.model !== answerConfig.model || a.model_sha256 !== answerConfig.model_sha256 || a.policy !== answerConfig.version
    || a.prompt_sha256 !== answerConfig.prompt_sha256 || a.validation !== 'exact_quotes_and_model_review'
    || a.quality !== 'development_unvalidated' || !Array.isArray(a.claims) || a.claims.length > 3
    || (a.status === 'insufficient') !== (a.claims.length === 0)
    || !a.claims.every(c => typeof c.text === 'string' && c.text.trim().length > 0 && c.text.length <= 900
      && Array.isArray(c.citations) && c.citations.length >= 1 && c.citations.length <= 2
      && new Set(c.citations.map(x => x.rank)).size === c.citations.length
      && c.citations.every(x => Number.isInteger(x.rank) && typeof x.quote === 'string' && x.quote.length >= 20
        && result.evidence.find(e => e.rank === x.rank)?.record.text.includes(x.quote)))) throw new Error('Invalid cited answer')
  return result
}

export async function searchLiterature(request, signal) {
  const response = await fetch('/literature-search/answer', { method: 'POST',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request), signal })
  if (!response.ok) throw new Error('Search unavailable')
  return validateAnswer(await response.json(), request)
}

export default function LiteratureSearchPanel({ search = searchLiterature }) {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [phase, setPhase] = useState('idle')
  const active = useRef(null)
  useEffect(() => () => active.current?.abort(), [])
  function change(value) {
    active.current?.abort(); active.current = null
    setQuestion(value); setResult(null); setPhase('idle')
  }
  async function submit(event) {
    event.preventDefault()
    if (!question.trim() || active.current) return
    const control = new AbortController(); active.current = control
    const request = { schema_version: 'prowl-expert-request-v1', request_id: crypto.randomUUID(), question: question.trim() }
    const timeout = setTimeout(() => control.abort(), 165000)
    setPhase('loading'); setResult(null)
    try {
      const response = validateAnswer(await search(request, control.signal), request)
      if (active.current === control && !control.signal.aborted) { setResult(response); setPhase('done') }
      else if (active.current === control) setPhase('error')
    } catch { if (active.current === control) setPhase('error') }
    finally { clearTimeout(timeout); if (active.current === control) active.current = null }
  }
  return <section className="guided-evidence literature-search" aria-labelledby="literature-search-title">
    <h2 id="literature-search-title">Search pancreatic literature</h2>
    <p>Ask a question or enter a topic. Search {config.source_count} papers about the pancreas, pancreatitis and pancreatic cancer.</p>
    <p className="literature-search__notice">Local AI answers from research sources · Development preview. Use general questions; do not enter patient information.</p>
    <form className="guided-evidence__body" onSubmit={submit}>
      <label htmlFor="literature-question">Literature question</label>
      <textarea id="literature-question" rows={3} maxLength={500} value={question}
        placeholder="What imaging findings help distinguish pancreatitis from pancreatic cancer?"
        onChange={e => change(e.target.value)} />
      <div className="literature-search__actions">
        <button type="submit" disabled={!question.trim() || phase === 'loading'}>{phase === 'loading' ? 'Writing answer…' : phase === 'error' ? 'Try again' : 'Ask question'}</button>
        {phase === 'loading' && <button type="button" onClick={() => change(question)}>Cancel</button>}
        <span>{question.length}/500</span>
      </div>
    </form>
    <div aria-live="polite" aria-busy={phase === 'loading'}>
      {phase === 'loading' && <p>Finding evidence and writing a source-checked answer with the local model…</p>}
      {phase === 'error' && <p role="alert">Search is unavailable or timed out. Check the local search service and data drive, then retry.</p>}
      {result && <article aria-label="Literature search results">
        <h3>{result.state === 'not_searched' ? 'Search needs a different question' : result.state === 'no_results' ? 'No passages found' : result.generation === 'completed' ? 'Answer' : 'Retrieved passages'}</h3>
        <p>{result.state === 'not_searched' ? reasons[result.reason] : result.state === 'no_results'
          ? 'No matching passages were returned. Try a broader pancreatic topic.'
          : result.generation === 'completed' ? 'Written by the local AI using the sources below. Check the citations; this is a development preview.' : 'The local AI could not produce a checked answer. You can still read the retrieved passages.'}</p>
        {result.evidence.length > 0 && <LiteratureReadingView key={result.request_id} evidence={result.evidence} answer={result.answer} />}
        {result.state !== 'not_searched' && <details><summary>Search details</summary>
          <p>{config.source_count} papers · {config.passage_count.toLocaleString()} indexed passages · Exact dense search · Local Qwen3 answer model</p>
          <small>Collection: {result.collection}<br />Corpus: {result.target.inventory.content_sha256}<br />Request: {result.request_id}</small>
        </details>}
      </article>}
    </div>
    <small>Questions and results are not automatically saved. No scan is attached.</small>
  </section>
}

function LiteratureReadingView({ evidence, answer }) {
  const [view, setView] = useState(answer ? 'answer' : 'reading')
  const [selected, setSelected] = useState(null)
  const sources = useRef({})
  useEffect(() => {
    if (view === 'sources' && selected !== null) sources.current[selected]?.focus()
  }, [view, selected])
  return <div className="literature-search__reading-view">
    <div className="literature-search__view-switch" role="group" aria-label="Result view">
      {answer && <button type="button" aria-pressed={view === 'answer'} onClick={() => setView('answer')}>Answer</button>}
      <button type="button" aria-pressed={view === 'reading'} onClick={() => setView('reading')}>Read passages</button>
      <button type="button" aria-pressed={view === 'sources'} onClick={() => { setSelected(null); setView('sources') }}>Sources ({evidence.length})</button>
    </div>
    {view === 'answer' ? <div className="literature-search__prose" aria-label="AI answer">
      {answer.status === 'insufficient' && <p>I couldn’t find enough directly relevant evidence in these sources to answer your question.</p>}
      {answer.claims.map((c, i) => <div className="literature-search__passage" key={i}>
        <p>{c.text}{' '}{c.citations.map(x => <button key={x.rank} type="button" className="literature-search__reference"
          aria-label={`View source ${x.rank}`} onClick={() => { setSelected(x.rank); setView('sources') }}>[{x.rank}]</button>)}</p>
      </div>)}
    </div> : view === 'reading' ? <div className="literature-search__prose" aria-label="Retrieved text">
      {evidence.map(({ rank, record: r }) => <div className="literature-search__passage" key={r.passage.passage_id}>
        <p>{r.text}</p>
        <button type="button" className="literature-search__reference" aria-label={`View source ${rank}`}
          onClick={() => { setSelected(rank); setView('sources') }}>Source [{rank}]</button>
      </div>)}
    </div> : <section className="literature-search__sources" aria-label="Sources">
      {evidence.map(({ rank, record: r }) => <section className="literature-search__result" key={r.passage.passage_id}
        aria-labelledby={`literature-source-${rank}`}>
        <h4 id={`literature-source-${rank}`} tabIndex={-1} ref={node => { sources.current[rank] = node }}>
          [{rank}] {r.citation.title} ({r.citation.year})
        </h4>
        <p>{r.citation.authors.join('; ')}</p>
        <p><a href={`https://pmc.ncbi.nlm.nih.gov/articles/${r.citation.pmcid}/`} target="_blank" rel="noreferrer">Read full source · PMID {r.citation.pmid}</a></p>
        <p>{r.citation.attribution} · CC BY 4.0 · DOI: {r.citation.doi || 'Not recorded'}</p>
        <details open={selected === rank}><summary>Original excerpt [{rank}]</summary>
          <blockquote>{r.text}</blockquote>
          <small>Section {r.passage.section_id}, characters {r.passage.start}–{r.passage.end}. Source status reflects the retained snapshot.</small>
        </details>
      </section>)}
    </section>}
  </div>
}
