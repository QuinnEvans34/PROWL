import { useEffect, useRef, useState } from 'react'
import config from '../../../configs/evidence/development-search-v1.json'
import recordConfig from '../../../configs/evidence/development-search-v3-records.json'
import diseaseCatalog from '../../../configs/evidence/source-facts-disease-v1.json'
import answerConfig from '../../../configs/evidence/natural-answer-v6.1.json'
import { validateEvidenceAnswer } from './evidenceAnswer'
import { validateRecordAnswer } from './recordAnswer'
import { validateVolumeAnswer, validateVolumeSources, volumeReasons } from './volumeAnswer'
import { validateMeasurementAnswer, validateMeasurementSources } from './measurementAnswer'
import { validateStudyAnswer, validateStudySources } from './studyAnswer'
import { loadScanMeasurements, scanQuestion, measurementText } from '../lib/scanMeasurements.js'
import './GuidedEvidencePanel.css'

const reasons = {
  clarification_negation: 'Your question includes a negative or an exclusion. Which finding or comparison do you want explained? Please ask that part directly; I will not assume the opposite meaning.',
  clarification_subject: 'Which organ or lesion do you mean, and are you asking about a published study or the current scan?',
  clarification_size: 'Do you mean whole-pancreas volume or a length such as the head diameter? For volume, ask for a published study example; it is not a universal normal range.',
  out_of_scope: 'Use a general literature question. This search cannot diagnose a case, recommend treatment, or disclose private information.',
  case_context_unavailable: 'This search does not have access to your scan. Ask about a general topic, such as pancreatic enlargement.',
  measurement_unavailable: 'This literature search cannot measure a scan. Open a saved prediction for available measurements, or ask a general literature question.',
  pancreas_topic_required: 'Include a pancreatic topic in your question, such as pancreatitis, pancreas size, or PDAC.',
}
const generationFailures = {
  timeout: 'The local AI reached its 60-second answer limit. The retrieved passages are available below.',
  incomplete: 'The local AI stopped before finishing its answer. The retrieved passages are available below.',
  support_rejected: 'The evidence review could not confirm the draft answer. The retrieved passages are available below.',
  qualifier_mismatch: 'The draft overstated or changed the source’s qualifications. You can inspect the retrieved passages in Sources.',
  model_unavailable: 'The local answer model is unavailable. The retrieved passages are available below.',
  validation_failed: 'The draft did not pass citation or answer-format checks. The retrieved passages are available below.',
}

export function validateSearch(result, request, limit = 5) {
  if (result?.schema_version !== 'prowl-development-search-response-v1'
    || result.request_id !== request.request_id || result.question !== request.question
    || result.collection !== config.collection || result.generation !== 'not_called' || result.answer !== null
    || result.target?.manifest_sha256 !== config.manifest.sha256
    || result.target?.inventory?.content_sha256 !== config.corpus_content_sha256
    || !['evidence_unassessed', 'no_results', 'not_searched'].includes(result.state)
    || !Array.isArray(result.evidence) || result.evidence.length > limit
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

export function validateSourceSearch(result, request) {
  if (result?.schema_version === 'prowl-evidence-answer-response-v1') return validateEvidenceAnswer(result, request, validateSearch)
  if (result?.retrieval_policy === 'source-linked-study-search-v1') return validateStudySources(result, request, validateSearch)
  if (result?.retrieval_policy === 'source-linked-measurement-search-v1') return validateMeasurementSources(result, request, validateSearch)
  if (result?.retrieval_policy === 'source-linked-volume-search-v1') return validateVolumeSources(result, request, validateSearch)
  validateSearch(result, request, 20)
  const selection = result.record_selection
  if (![recordConfig.retriever, ...(recordConfig.compatible_response_versions || [])].includes(result.retrieval_policy)
    || selection?.policy !== result.retrieval_policy
    || !['matched', 'dense_fallback', 'not_searched'].includes(selection.status)
    || !Array.isArray(selection.matches) || selection.matches.length > 3
    || (selection.status === 'matched') !== (selection.matches.length > 0)
    || (selection.status === 'not_searched') !== (result.state === 'not_searched')
    || new Set(selection.matches.map(m => m.record_id)).size !== selection.matches.length
    || (selection.status !== 'matched' && result.evidence.length > 5)) throw new Error('Invalid record selection')
  const returned = new Set(result.evidence.map(e => e.record.passage.passage_id))
  const expected = new Set()
  for (const match of selection.matches) {
    const record = diseaseCatalog.records.find(r => r.id === match.record_id)
    if (!record || !Number.isFinite(match.score) || match.score <= 0 || match.topic !== record.topic
      || JSON.stringify(match.comparison) !== JSON.stringify(record.comparison)
      || JSON.stringify(match.anchor_passage_ids) !== JSON.stringify(record.retrieval_anchors)
      || !Array.isArray(match.evidence_passage_ids)) throw new Error('Unknown comparison')
    const required = new Set(record.facts.flatMap(f => f.evidence.map(id => diseaseCatalog.spans[id].passage_id)))
    if (required.size !== match.evidence_passage_ids.length
      || !match.evidence_passage_ids.every(id => required.has(id) && returned.has(id))) throw new Error('Missing source context')
    required.forEach(id => expected.add(id))
  }
  if (selection.status === 'matched' && (returned.size !== expected.size || ![...returned].every(id => expected.has(id)))) throw new Error('Unexpected source context')
  return result
}

export async function findLiteratureSources(request, signal) {
  const response = await fetch('/literature-search/query', { method: 'POST',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request), signal })
  if (!response.ok) throw new Error('Search unavailable')
  return validateSourceSearch(await response.json(), request)
}

export function validateAnswer(result, request) {
  if (result?.schema_version === 'prowl-evidence-answer-response-v1') return validateEvidenceAnswer(result, request, validateSearch)
  if (result?.schema_version === 'prowl-study-answer-response-v1') return validateStudyAnswer(result, request, validateSourceSearch)
  if (result?.schema_version === 'prowl-measurement-answer-response-v1') return validateMeasurementAnswer(result, request, validateSourceSearch)
  if (result?.schema_version === 'prowl-volume-answer-response-v1') return validateVolumeAnswer(result, request, validateSourceSearch)
  if (result?.schema_version === 'prowl-record-answer-response-v1') return validateRecordAnswer(result, request, validateSourceSearch)
  if (result?.retrieval_policy !== undefined || result?.record_selection !== undefined
      || result?.schema_version !== 'prowl-development-answer-response-v1'
      || !['not_called', 'completed', 'unavailable'].includes(result.generation)) throw new Error('Invalid answer envelope')
  validateSearch({ ...result, schema_version: 'prowl-development-search-response-v1', generation: 'not_called', answer: null }, request)
  if (result.generation !== 'completed') {
    if (result.answer !== null || (result.generation === 'unavailable' && result.state !== 'evidence_unassessed')
      || (result.generation === 'not_called' && result.state === 'evidence_unassessed')) throw new Error('Invalid answer state')
    if (result.generation_failure !== undefined
      && (result.generation !== 'unavailable' || !Object.hasOwn(generationFailures, result.generation_failure))) throw new Error('Invalid failure category')
    return result
  }
  const a = result.answer
  if (result.generation_failure !== undefined) throw new Error('Unexpected generation failure')
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

export const SUGGESTED_QUESTIONS = [
  'What imaging findings help distinguish mass-forming chronic pancreatitis from pancreatic cancer?',
  'How can focal autoimmune pancreatitis be distinguished from PDAC on imaging?',
  'Could pancreatic head enlargement indicate disease?',
  'What is the average pancreas volume reported in research?',
  'How does measuring pancreatic tumor diameter differ from measuring its volume on CT?',
]

// variant="panel" renders inside the Workbench assistant. Validation, request identity,
// timeouts and answer/source semantics are identical in both variants.
// contextKey: the active study. Literature answers are general; switching study cancels a
// pending request (its late result is discarded) and labels earlier results as general.
export default function LiteratureSearchPanel({
  search = searchLiterature,
  findSources = findLiteratureSources,
  variant = 'page',
  contextKey = null,
  contextLabel = null,
  onPendingChange = null,
  measurementContext = null,
  measure = loadScanMeasurements,
  suggestions = variant === 'panel' ? SUGGESTED_QUESTIONS : [],
}) {
  const panel = variant === 'panel'
  const measurementKey = measurementContext?.key ?? null
  const [scanResult, setScanResult] = useState(null)
  const measurementRef = useRef(measurementKey)
  useEffect(() => {
    if (measurementRef.current === measurementKey) return
    measurementRef.current = measurementKey
    if (active.current) { active.current.abort(); active.current = null; setPhase('idle') }
    setScanResult(null)
  }, [measurementKey])
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [phase, setPhase] = useState('idle')
  const [elapsed, setElapsed] = useState(0)
  const [sourceMode, setSourceMode] = useState(false)
  const [askedFor, setAskedFor] = useState(null)
  const [contextNotice, setContextNotice] = useState('')
  const active = useRef(null)
  const contextRef = useRef(contextKey)
  useEffect(() => () => active.current?.abort(), [])
  useEffect(() => { onPendingChange?.(phase === 'loading') }, [phase, onPendingChange])
  useEffect(() => {
    if (contextRef.current === contextKey) return
    contextRef.current = contextKey
    if (active.current) {
      active.current.abort(); active.current = null
      setPhase('idle'); setResult(null)
      setContextNotice('Your pending question was cancelled because you switched studies. The question is kept; ask again if it still applies.')
    }
  }, [contextKey])
  useEffect(() => {
    if (phase !== 'loading') return
    const started = Date.now()
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => clearInterval(timer)
  }, [phase])
  function change(value) {
    active.current?.abort(); active.current = null
    setQuestion(value); setScanResult(null); setResult(null); setPhase('idle'); setContextNotice('')
  }
  async function submit(event, sourcesOnly = phase === 'error' && sourceMode) {
    event.preventDefault()
    if (!question.trim() || active.current) return
    const control = new AbortController(); active.current = control
    const request = { schema_version: 'prowl-expert-request-v1', request_id: crypto.randomUUID(), question: question.trim() }
    const timeout = setTimeout(() => control.abort(), 150000)
    setScanResult(null); setSourceMode(sourcesOnly); setElapsed(0); setPhase('loading'); setResult(null); setContextNotice('')
    setAskedFor({ key: contextKey, label: contextLabel })
    try {
      const target = measurementContext ? scanQuestion(question) : null
      if (target) {
        let value
        if (sourcesOnly) value = { message: 'Use Ask question to calculate the saved outline volume. Find sources searches general literature.' }
        else if (target === 'unsupported') value = { message: 'I can calculate the loaded pancreas or total suspected-lesion mask volume. Head measurements, individual lesion dimensions, normal-range comparisons and disease interpretations of this scan are not connected yet.' }
        else {
          try {
            const measurement = await measure(measurementContext, control.signal)
            if (measurement.contextKey !== measurementKey) throw new Error('The prediction changed. Ask again for the current study.')
            value = { measurement, target }
          } catch (error) { value = { message: error.message || 'The saved mask could not be measured.' } }
        }
        if (active.current === control && !control.signal.aborted) {
          setScanResult({ ...value, key: measurementKey }); setPhase('done')
        } else if (active.current === control) setPhase('error')
        return
      }
      const response = sourcesOnly
        ? validateSourceSearch(await findSources(request, control.signal), request)
        : validateAnswer(await search(request, control.signal), request)
      if (active.current === control && !control.signal.aborted) { setResult(response); setPhase('done') }
      else if (active.current === control) setPhase('error')
    } catch { if (active.current === control) setPhase('error') }
    finally { clearTimeout(timeout); if (active.current === control) active.current = null }
  }
  const staleContext = result && askedFor && askedFor.key !== contextKey
  return <section className={`guided-evidence literature-search${panel ? ' literature-search--panel' : ''}`} aria-labelledby="literature-search-title">
    {panel ? <>
      <p className="literature-search__scope"><span aria-hidden="true" />{measurementContext ? 'Saved-mask volumes · General literature' : 'Literature only · Scan context not connected'}</p>
      <h2 id="literature-search-title">A second perspective. Your decision.</h2>
      <p>{measurementContext ? 'Ask how big this pancreas is to calculate the saved outline volume, or ask a general literature question. Whole-organ coverage and disease interpretation of this scan are not verified.' : `Ask a general question about the pancreas. Answers cite ${config.source_count} research papers; they do not see this scan and do not remember earlier questions.`}</p>
    </> : <>
      <h2 id="literature-search-title">Search pancreatic literature</h2>
      <p>Ask a question or enter a topic. Search {config.source_count} papers about the pancreas, pancreatitis and pancreatic cancer.</p>
    </>}
    <p className="literature-search__notice">{measurementContext ? 'Development preview · Saved-mask calculations and cited literature answers. Do not enter patient information.' : 'Local AI answers from research sources · Development preview. Use general questions; do not enter patient information.'}</p>
    {!panel && <p>Ask question summarizes reviewed disease comparisons, MRI volume study results and CT tumor measurement methods. Open Sources to inspect the supporting passages. Other topics currently return search results.</p>}
    {suggestions.length > 0 && !result && !scanResult && phase !== 'loading' && <div className="literature-search__suggestions" role="group" aria-label="Suggested general questions">
      {(measurementContext ? ['How big is this pancreas?', 'What is the size of the lesion in this scan?', ...suggestions] : suggestions).map(text => <button type="button" key={text} onClick={() => change(text)}>{text}</button>)}
    </div>}
    <form className="guided-evidence__body" onSubmit={submit}>
      <label htmlFor="literature-question">Literature question</label>
      <textarea id="literature-question" rows={3} maxLength={500} value={question}
        placeholder="What imaging findings help distinguish pancreatitis from pancreatic cancer?"
        onChange={e => change(e.target.value)} />
      <div className="literature-search__actions">
        <button type="submit" disabled={!question.trim() || phase === 'loading'}>{phase === 'loading' ? (sourceMode ? 'Finding sources…' : measurementContext && scanQuestion(question) ? 'Measuring saved outline…' : 'Writing answer…') : phase === 'error' ? 'Try again' : 'Ask question'}</button>
        <button type="button" disabled={!question.trim() || phase === 'loading'} onClick={e => submit(e, true)}>Find sources</button>
        {phase === 'loading' && <button type="button" onClick={() => change(question)}>Cancel</button>}
        <span>{question.length}/500</span>
      </div>
    </form>
    <div aria-live="polite" aria-busy={phase === 'loading'}>
      {scanResult?.key === measurementKey && scanResult && <article aria-label="Current scan measurement">
        <h3>{scanResult.measurement ? 'Saved outline volume' : 'Measurement unavailable'}</h3>
        <p>{scanResult.measurement ? measurementText(scanResult.measurement, scanResult.target) : scanResult.message}</p>
        {scanResult.measurement && <>
          <p>Calculated locally from the saved prediction mask, not estimated by the AI. The model outline needs human review.</p>
          <details><summary>Measurement source and limitations</summary>
            <p>{scanResult.measurement.unitsBasis}. {scanResult.measurement.coverage}. {scanResult.measurement.modelLineage}.</p>
            <p>Method: label count × absolute affine determinant. Pancreas includes labels 1 and 2; suspected-lesion total includes label 2 only. No reference annotation is used.</p>
            <p>Grid: {scanResult.measurement.shape.join(' × ')}; voxel volume: {scanResult.measurement.voxelMm3} mm³.</p>
            <p>{scanResult.measurement.hashBasis}.</p>
            <small>CT SHA-256: {scanResult.measurement.ctSha256}<br />Prediction SHA-256: {scanResult.measurement.predictionSha256}</small>
          </details>
        </>}
      </article>}
      {contextNotice && <p className="literature-search__context-notice">{contextNotice}</p>}
      {phase === 'loading' && <p className="literature-search__pending"><span className="literature-search__pulse" aria-hidden="true" />{measurementContext && scanQuestion(question) ? 'Checking the saved image geometry and calculating outline volume…' : sourceMode ? 'Finding source passages and their supporting context…' : 'Finding evidence, writing an answer, and checking its citations…'} {elapsed}s elapsed. {!sourceMode && !(measurementContext && scanQuestion(question)) && 'You can cancel while the local model works.'}</p>}
      {phase === 'error' && <p role="alert">Search is unavailable or timed out. Check the local search service and data drive, then retry.</p>}
      {result && <article aria-label="Literature search results">
        {staleContext && <p className="literature-search__stale">General literature · asked while reviewing {askedFor.label || 'another study'}. Not about the current study.</p>}
        <h3>{result.state === 'retrieval_failed' ? 'Search unavailable' : result.reason?.startsWith('clarification_') ? 'Clarify your question' : result.record_selection?.policy === 'source-linked-volume-search-v1' && volumeReasons[result.record_selection.reason] && result.state !== 'not_searched' ? 'Clarify your question' : result.state === 'not_searched' ? 'Search needs a different question' : result.state === 'no_results' ? 'No passages found' : result.answer ? 'Answer' : 'Retrieved passages'}</h3>
        <p>{result.message || (result.state !== 'not_searched' && result.record_selection?.policy === 'source-linked-volume-search-v1' && volumeReasons[result.record_selection.reason] ? volumeReasons[result.record_selection.reason] : result.state === 'not_searched' ? reasons[result.reason] : result.state === 'no_results'
          ? 'No matching passages were returned. Try a broader pancreatic topic.'
          : result.answer?.provenance === 'local_model_composition' ? 'The local AI selected reviewed wording and arranged the source facts below. Citations and required qualifications are preserved.'
          : result.answer?.provenance === 'reviewed_source_fallback' ? 'The local AI could not finish a valid composition. This is a reviewed source summary assembled by the application, not model-written text.'
          : result.generation === 'completed' ? (result.answer?.status === 'insufficient' ? 'The search returned passages, but they did not support a checked answer.' : 'Written by the local AI using the sources below. Check the citations; this is a development preview.') : sourceMode ? (result.record_selection.status === 'matched' ? (result.retrieval_policy === 'source-linked-study-search-v1' ? 'The selected study passages and their limitations are shown below. These describe published research, not findings from your scan.' : result.retrieval_policy === 'source-linked-measurement-search-v1' ? 'The CT study’s measurement methods and limitations are shown below.' : result.retrieval_policy === 'source-linked-volume-search-v1' ? 'The selected MRI study groups and their supporting passages are shown below. These are study examples, not a normal range.' : 'Relevant comparison sources and their qualifications are shown below. These are literature examples, not an exhaustive list of diseases or a diagnosis.') : 'No reviewed source record matched this wording. Showing general literature search results.') : result.answer_policy ? 'This wording is outside the reviewed summary coverage. No answer model was called; the search passages are available to inspect.' : generationFailures[result.generation_failure] || 'The local AI could not produce a checked answer. You can still read the retrieved passages.')}</p>
        {sourceMode && result.record_selection?.matches.some(m => m.comparison) && <p>Comparisons: {result.record_selection.matches.map(m => m.comparison.join(' versus ').replace('focal_AIP', 'focal AIP')).join('; ')}. MFCP: mass-forming chronic pancreatitis. Focal AIP: focal autoimmune pancreatitis. PDAC: pancreatic ductal adenocarcinoma.</p>}
        {result.evidence.length > 0 && <LiteratureReadingView key={result.request_id} evidence={result.evidence} answer={result.answer} />}
        {result.state !== 'not_searched' && <details><summary>Search details</summary>
          <p>{config.source_count} papers · {config.passage_count.toLocaleString()} indexed passages · {result.retrieval_policy === 'evidence-led-answer-v1' ? 'Evidence-led section selection · Local Qwen3 · Development regression' : sourceMode ? 'Reviewed source records with dense-search fallback · No answer model called' : result.answer_policy ? 'Reviewed source records · Qwen3 8B constrained composition · Independent review pending' : 'Exact dense search · Local Qwen3 answer model'}</p>
          <small>Collection: {result.collection}<br />Corpus: {result.target.inventory.content_sha256}<br />Request: {result.request_id}</small>
        </details>}
      </article>}
    </div>
    <small>{panel ? measurementContext ? 'Each question is independent. Saved-mask measurements stay local; scan data is not sent to literature search. Results are not saved.' : 'Each question is answered independently. Questions and results are not saved. No scan is attached.' : 'Questions and results are not automatically saved. No scan is attached.'}</small>
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
      {answer.scope && <p>{answer.scope}</p>}
      {answer.status === 'insufficient' && !answer.limitation && <p>I couldn’t find enough directly relevant evidence in the passages returned by this search to answer your question. You can inspect them in Sources or try a more specific question.</p>}
      {answer.claims.map((c, i) => <div className="literature-search__passage" key={i}>
        <p>{c.text}{' '}{c.citations.map(x => <button key={x.rank} type="button" className="literature-search__reference"
          aria-label={`View source ${x.rank}`} onClick={() => { setSelected(x.rank); setView('sources') }}>[{x.rank}]</button>)}</p>
      </div>)}
      {answer.limitation && <p>{answer.limitation}</p>}
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
