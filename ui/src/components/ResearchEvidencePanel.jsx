import { useEffect, useRef, useState } from 'react'
import wording from '../../../configs/evidence/evidence-wording-v1.json'
import questions from '../../../configs/evidence/research-questions-v1.json'
import './GuidedEvidencePanel.css'

export async function requestResearch(request, signal, answers = false) {
  const reply = await fetch(`${answers ? '/research-answers' : '/research-evidence'}/responses`, { method: 'POST',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request), signal })
  if (!reply.ok) throw new Error('Search unavailable')
  return validateResearch(await reply.json(), request, answers)
}

export function validateResearch(result, request, answers = false) {
  if (result.schema_version !== (answers ? 'prowl-research-answer-v1' : 'prowl-research-search-v1') || result.response_id !== request.request_id
    || result.request?.question_id !== request.question_id || result.request?.request_id !== request.request_id
    || result.question !== questions.find(q => q.id === request.question_id)?.label
    || (answers ? result.provenance?.generation_model !== 'qwen3:8b' : result.provenance?.generation_model !== null) || result.provenance?.collection !== 'research-v1'
    || !['retrieved', 'no_results'].includes(result.state) || !Array.isArray(result.passages)
    || result.passages.length > 5 || (result.state === 'retrieved') !== (result.passages.length > 0)
    || !result.passages.every(p => typeof p.record?.text === 'string' && p.record?.passage?.passage_id
      && /^\d+$/.test(p.record?.citation?.pmid) && /^PMC\d+$/.test(p.record?.citation?.pmcid)
      && p.record?.rights?.permissions?.display_snippet === true)) throw new Error('Invalid research response')
  if (answers) {
    const answer = result.generation?.answer
    if (!answer || !['excerpts', 'insufficient_evidence'].includes(answer.status)
      || !Array.isArray(answer.extracts) || answer.extracts.length > 3
      || (answer.status === 'excerpts') !== (answer.extracts.length > 0)
      || !answer.extracts.every(e => typeof e.quote === 'string' && e.quote.length >= 40
        && result.passages.some(p => p.record.passage.passage_id === e.passage_id && p.record.text.includes(e.quote)))) {
      throw new Error('Invalid grounded answer')
    }
  }
  return result
}

export default function ResearchEvidencePanel({ loadResponse = requestResearch, answers = false }) {
  const prefix = answers ? '/research-answers' : '/research-evidence'
  const inputId = answers ? 'answer-question' : 'research-question'
  const [question, setQuestion] = useState(questions[0].id)
  const [result, setResult] = useState(null)
  const [phase, setPhase] = useState('idle')
  const pending = useRef(null), active = useRef(null)
  useEffect(() => () => active.current?.abort(), [])
  async function submit() {
    if (active.current) return
    const request = pending.current || { request_id: crypto.randomUUID(), question_id: question }
    pending.current = request
    const control = new AbortController(); active.current = control
    const timeout = setTimeout(() => control.abort(), answers ? 110000 : 45000)
    setPhase('loading'); setResult(null)
    try {
      const response = await loadResponse(request, control.signal, answers)
      if (!control.signal.aborted) { setResult(response); setPhase('saved'); pending.current = null }
      else setPhase('unavailable')
    } catch { setPhase('unavailable') }
    finally { clearTimeout(timeout); active.current = null }
  }
  return <details className="guided-evidence">
    <summary>{answers ? 'Grounded research answers' : 'Research passage search'} <span>{answers ? 'Local AI · verified quotations' : 'Live local retrieval'}</span></summary>
    <div className="guided-evidence__body">
      <p>{answers ? 'The local model selects quotations from two research reviews. Quotations are checked against the cited passages; relevance and completeness still need your review.' : 'Search two research reviews. Results are source excerpts, not generated answers or verified conclusions.'} PROWL cannot diagnose patients or recommend treatment.</p>
      <label htmlFor={inputId}>{answers ? 'Evidence question' : 'Research question'}</label>
      <select id={inputId} value={question} disabled={phase === 'loading'} onChange={e => {
        setQuestion(e.target.value); setResult(null); setPhase('idle'); pending.current = null
      }}>{questions.map(q => <option key={q.id} value={q.id}>{q.label}</option>)}</select>
      <button disabled={phase === 'loading'} onClick={submit}>{phase === 'loading' ? (answers ? 'Selecting evidence and saving…' : 'Searching and saving…') : phase === 'unavailable' ? (answers ? 'Retry evidence answer' : 'Retry research search') : (answers ? 'Answer with cited excerpts' : 'Search and save passages')}</button>
      <div aria-live="polite">
        {phase === 'unavailable' && <p role="alert">Research search is unavailable or the save could not be confirmed. Check the local service and drive, then retry the same request.</p>}
        {result && <article aria-label={answers ? "Saved evidence answer" : "Saved research search"}>
          {answers && <section aria-label="Model-selected evidence">
            <h3>{result.generation.answer.status === "excerpts" ? "Cited evidence excerpts" : "Unable to provide a supported answer"}</h3>
            {result.generation.answer.status === "insufficient_evidence" && <p>{result.generation.validation === "generation_rejected" ? "We could not verify the model’s response against the retrieved passages. Please review the sources or try again." : wording.insufficient_evidence}</p>}
            {result.generation.answer.extracts.map((e, i) => <div key={i}><blockquote>{e.quote}</blockquote><a href={`#answer-passage-${e.passage_id}`} onClick={() => { const target = document.getElementById(`answer-passage-${e.passage_id}`); if (target) target.open = true }}>Source [{i + 1}]</a></div>)}
            <p>Quotation matching does not establish medical accuracy or a complete answer.</p>
          </section>}
          <h3>{result.passages.length ? 'Retrieved research passages' : 'No passages found'}</h3>
          <p>Similarity does not establish that a passage answers the question. Read the source and its limitations.</p>
          {result.passages.map(({ record: r }) => <details id={`${answers ? "answer" : "search"}-passage-${r.passage.passage_id}`} key={r.passage.passage_id}>
            <summary>{r.citation.title} ({r.citation.year})</summary>
            <blockquote>{r.text}</blockquote>
            <p>{r.citation.authors.join('; ')}</p>
            <a href={`https://pmc.ncbi.nlm.nih.gov/articles/${r.citation.pmcid}/`} target="_blank" rel="noreferrer">Read source · PMID {r.citation.pmid}</a>
            <p>DOI: {r.citation.doi} · {r.citation.attribution} · CC BY 4.0</p>
            <p>Section {r.passage.section_id}, characters {r.passage.start}–{r.passage.end}. Source status reflects the retained snapshot.</p>
          </details>)}
          <a href={`${prefix}/responses/${result.response_id}`} download>{answers ? "Download saved evidence answer" : "Download saved research search"}</a>
          <details><summary>Search provenance</summary><p>Collection: {result.provenance.collection}</p>
            <p>Encoder: {result.provenance.encoder_id}</p><p>Response: {result.response_id}</p>
            <p>Content SHA-256: {result.content_sha256}</p><p>{answers ? `Model: ${result.provenance.generation_model}; quotation validation: ${result.generation.validation}` : "No generation model used."}</p></details>
        </article>}
      </div>
      <small>One saved search per request. No patient data is sent or attached.</small>
    </div>
  </details>
}
