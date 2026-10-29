import LocalExpertReadiness from './LocalExpertReadiness.jsx'
import { serializeLiteratureCapture, downloadLiteratureCapture } from '../lib/literatureCapture.js'
import { validateSingleSummary } from './singleSummary'
import { validateGeneralExtract } from './generalExtract'
import { useEffect, useId, useRef, useState } from 'react'
import config from '../../../configs/evidence/development-search-v1.json'
import recordConfig from '../../../configs/evidence/development-search-v3-records.json'
import diseaseCatalog from '../../../configs/evidence/source-facts-disease-v1.json'
import answerConfig from '../../../configs/evidence/natural-answer-v6.1.json'
import { validateEvidenceAnswer } from './evidenceAnswer'
import { validateRecordAnswer } from './recordAnswer'
import { validateVolumeAnswer, validateVolumeSources, volumeReasons } from './volumeAnswer'
import { validateMeasurementAnswer, validateMeasurementSources } from './measurementAnswer'
import { validateStudyAnswer, validateStudySources } from './studyAnswer'
import { loadScanMeasurements, scanQuestion, measurementText, pancreasReferenceUrl } from '../lib/scanMeasurements.js'
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

export async function previewQuestion(request, signal) {
  const response = await fetch('/literature-search/interpret', { method: 'POST', signal,
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request) })
  if (!response.ok) throw new Error('Question help unavailable')
  const value = await response.json()
  if (value?.schema_version !== 'prowl-question-preview-v1' || value.request_id !== request.request_id
    || value.question !== request.question || !['suggested', 'clarification', 'unsupported', 'unchanged'].includes(value.status)
    || typeof value.message !== 'string' || value.message.length > 600 || typeof value.query !== 'string'
    || value.query.length > 500 || (value.status === 'suggested' ? !value.query.trim() : value.query !== '')) throw new Error('Invalid question preview')
  return value
}

export function validateAnswer(result, request) {
  if (result?.schema_version === 'prowl-single-summary-response-v1') return validateSingleSummary(result, request, validateSourceSearch)
  if (result?.schema_version === 'prowl-general-extract-response-v1') return validateGeneralExtract(result, request, validateSourceSearch)
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
  interpret = previewQuestion,
  variant = 'page',
  contextKey = null,
  contextLabel = null,
  onPendingChange = null,
  measurementContext = null,
  measure = loadScanMeasurements,
  downloadCapture = downloadLiteratureCapture,
  suggestions = variant === 'panel' ? SUGGESTED_QUESTIONS : [],
}) {
  const panel = variant === 'panel'
  const measurementKey = measurementContext?.key ?? null
  const [history, setHistory] = useState([])
  const remember = entry => setHistory(items => [...items, entry].slice(-6))
  const [scanResult, setScanResult] = useState(null)
  const measurementRef = useRef(measurementKey)
  useEffect(() => {
    if (measurementRef.current === measurementKey) return
    setHistory([])
    measurementRef.current = measurementKey
    if (active.current) { active.current.abort(); active.current = null; setPhase('idle') }
    setScanResult(null)
  }, [measurementKey])
  const [question, setQuestion] = useState('')
  const [submittedQuestion, setSubmittedQuestion] = useState('')
  const [readiness, setReadiness] = useState(null)
  const [preview, setPreview] = useState(null)
  const [previewText, setPreviewText] = useState('')
  const [helpMode, setHelpMode] = useState(false)
  const [helpError, setHelpError] = useState(false)
  const [originalQuestion, setOriginalQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [capture, setCapture] = useState(null)
  const [captureNotice, setCaptureNotice] = useState('')
  const [phase, setPhase] = useState('idle')
  const [elapsed, setElapsed] = useState(0)
  const [sourceMode, setSourceMode] = useState(false)
  const [askedFor, setAskedFor] = useState(null)
  const [contextNotice, setContextNotice] = useState('')
  const active = useRef(null)
  const questionInput = useRef(null)
  const contextRef = useRef(contextKey)
  useEffect(() => () => active.current?.abort(), [])
  useEffect(() => { onPendingChange?.(phase === 'loading') }, [phase, onPendingChange])
  useEffect(() => {
    if (contextRef.current === contextKey) return
    setHistory([])
    contextRef.current = contextKey
    setPreview(null); setHelpError(false)
    if (active.current) {
      active.current.abort(); active.current = null
      setPhase('idle'); setResult(null); setCapture(null); setCaptureNotice('')
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
    if (active.current && !helpMode) { setQuestion(value); return }
    active.current?.abort(); active.current = null
    setPreview(null); setHelpError(false); setHelpMode(false); setOriginalQuestion('')
    setQuestion(value); setScanResult(null); setResult(null); setCapture(null); setCaptureNotice(''); setPhase('idle'); setContextNotice('')
  }
  function cancelQuestion() {
    const previous = active.current
    active.current = null // Invalidate before abort: old callbacks cannot own the UI.
    previous?.abort()
    change(question)
    setContextNotice('Cancelled. Your draft is kept; you can ask a new question. The local service may still be finishing the previous request, but its response will not appear here.')
  }
  async function helpWithQuestion() {
    if (!question.trim() || active.current) return
    const control = new AbortController(); active.current = control
    const request = { schema_version: 'prowl-expert-request-v1', request_id: crypto.randomUUID(), question: question.trim() }
    const timeout = setTimeout(() => control.abort(), 25000)
    setSubmittedQuestion(request.question)
    setHelpMode(true); setHelpError(false); setPreview(null); setResult(null); setCapture(null); setCaptureNotice(''); setScanResult(null); setElapsed(0); setPhase('loading')
    try {
      const value = await interpret(request, control.signal)
      if (active.current === control && !control.signal.aborted) {
        setPreview(value); setPreviewText(value.query); setPhase('idle')
      } else if (active.current === control) { setHelpError(true); setPhase('idle') }
    } catch { if (active.current === control) { setHelpError(true); setPhase('idle') } }
    finally { clearTimeout(timeout); if (active.current === control) active.current = null }
  }
  async function submit(event, sourcesOnly = phase === 'error' && sourceMode) {
    event.preventDefault()
    if (!question.trim() || active.current) return
    const control = new AbortController(); active.current = control
    const request = { schema_version: 'prowl-expert-request-v1', request_id: crypto.randomUUID(), question: question.trim() }
    const timeout = setTimeout(() => control.abort(), 150000)
    setSubmittedQuestion(request.question)
    setHelpMode(false); setHelpError(false); setPreview(null)
    setScanResult(null); setSourceMode(sourcesOnly); setElapsed(0); setPhase('loading'); setResult(null); setCapture(null); setCaptureNotice(''); setContextNotice('')
    setAskedFor({ key: contextKey, label: contextLabel })
    try {
      const target = measurementContext ? scanQuestion(question) : null
      if (target) {
        let value
        if (sourcesOnly) value = { message: 'Use Ask question to calculate the saved outline volume. Find sources searches general literature.' }
        else if (target === 'unsupported') value = { message: 'I can calculate the loaded pancreas or total suspected-lesion mask volume. I can also compare the pancreas outline volume with a published study mean. Head measurements, individual lesion dimensions, clinical normal-range classification and disease interpretations of this scan are not connected yet.' }
        else {
          try {
            const measurement = await measure(measurementContext, control.signal)
            if (measurement.contextKey !== measurementKey) throw new Error('The prediction changed. Ask again for the current study.')
            value = { measurement, target }
          } catch (error) { value = { message: error.message || 'The saved mask could not be measured.' } }
        }
        if (active.current === control && !control.signal.aborted) {
          setScanResult({ ...value, key: measurementKey, requestId: request.request_id }); setPhase('done')
          remember({ id: request.request_id, question: request.question, label: contextLabel || 'Current study',
            text: value.measurement ? measurementText(value.measurement, value.target) : value.message,
            comparison: value.target === 'pancreas_comparison', measured: Boolean(value.measurement) })
        } else if (active.current === control) setPhase('error')
        return
      }
      const response = sourcesOnly
        ? validateSourceSearch(await findSources(request, control.signal), request)
        : validateAnswer(await search(request, control.signal), request)
      if (active.current === control && !control.signal.aborted) {
        setResult(response); setPhase('done')
        remember({ id: request.request_id, question: request.question, label: 'General literature', response, sourceMode: sourcesOnly })
        if (!sourcesOnly) {
          try { setCapture(serializeLiteratureCapture(request, response)) }
          catch (error) { setCaptureNotice(error.message) }
        }
      }
      else if (active.current === control) setPhase('error')
    } catch { if (active.current === control) setPhase('error') }
    finally { clearTimeout(timeout); if (active.current === control) active.current = null }
  }
  const staleContext = result && askedFor && askedFor.key !== contextKey
  return <section className={`guided-evidence literature-search${panel ? ' literature-search--panel' : ''}`} aria-labelledby="literature-search-title">
    {panel ? <>
      <p className="literature-search__scope"><span aria-hidden="true" />{measurementContext ? `Saved case: ${contextLabel || 'current study'} · ${measurementContext.available ? 'Outline measurements available for checking' : 'Show a saved prediction to enable measurements'}` : 'General literature · No scan attached'}</p>
      <h2 id="literature-search-title">{phase === 'loading' ? 'On it.' : result || scanResult ? 'Here’s what I found' : 'How can I help?'}</h2>
      {phase !== 'loading' && !result && !scanResult && <p>{measurementContext ? 'Ask me about the saved outline or explore the research behind your question.' : 'Use your own words. For help turning a question into search terms, choose Help phrase my question.'}</p>}
    </> : <>
      <h2 id="literature-search-title">Ask about pancreatic research</h2>
      <p>Use your own words. Get a cited explanation when the evidence supports one, or inspect the research passages.</p>
    </>}
    {(!panel || (phase !== 'loading' && !result && !scanResult)) && <p className="literature-search__notice">{panel ? 'Development preview · Do not enter patient information.' : measurementContext ? 'Development preview · Saved-mask calculations and cited literature answers. Do not enter patient information.' : 'Local AI answers from research sources · Development preview. Use general questions; do not enter patient information.'}</p>}
    {!panel && <p className="literature-search__scope">General literature · No scan attached</p>}
    <LocalExpertReadiness onStatus={setReadiness} />
    <form className="guided-evidence__body" onSubmit={submit}>
      <label htmlFor="literature-question">Literature question</label>
      <textarea ref={questionInput} id="literature-question" rows={3} maxLength={500} value={question}
        placeholder={panel ? "Ask PROWL a question…" : "What imaging findings help distinguish pancreatitis from pancreatic cancer?"}
        aria-describedby="literature-question-shortcut"
        onKeyDown={e => {
          if (e.key !== 'Enter' || e.shiftKey || e.nativeEvent.isComposing || e.nativeEvent.keyCode === 229) return
          e.preventDefault()
          if (!e.repeat && question.trim() && phase !== 'loading') e.currentTarget.form.requestSubmit()
        }}
        onChange={e => change(e.target.value)} />
      <small id="literature-question-shortcut">{phase === 'loading' ? 'You can draft your next question. Cancel this request before sending another.' : 'Enter to send · Shift+Enter for a new line'}</small>
      <div className="literature-search__actions">
        <button type="submit" disabled={!question.trim() || phase === 'loading' || (readiness?.gpu_busy && !(measurementContext && scanQuestion(question)))}>{phase === 'loading' ? (helpMode ? 'Understanding question…' : sourceMode ? 'Finding sources…' : measurementContext && scanQuestion(submittedQuestion) ? 'Measuring saved outline…' : 'Working…') : phase === 'error' ? 'Try again' : 'Ask question'}</button>
        {phase === 'loading' && <button type="button" onClick={cancelQuestion}>Cancel</button>}
        <span>{question.length}/500</span>
      </div>
      {panel ? phase !== 'loading' && <details className="literature-search__tools"><summary>Search tools</summary><div className="literature-search__actions">
        <button type="button" disabled={!question.trim() || phase === 'loading'} onClick={e => submit(e, true)}>Find sources</button>
        <button type="button" className="literature-search__help-button" disabled={!question.trim() || phase === 'loading' || readiness?.gpu_busy} onClick={helpWithQuestion}>Help phrase my question</button>
      </div></details> : <div className="literature-search__actions">
        <button type="button" disabled={!question.trim() || phase === 'loading'} onClick={e => submit(e, true)}>Find sources</button>
        <button type="button" className="literature-search__help-button" disabled={!question.trim() || phase === 'loading' || readiness?.gpu_busy} onClick={helpWithQuestion}>Help phrase my question</button>
      </div>}
    </form>
    {suggestions.length > 0 && !result && !scanResult && phase !== 'loading' && <details className="literature-search__question-ideas"><summary>Explore suggested questions</summary><div className="literature-search__suggestions" role="group" aria-label="Suggested general questions">
      {(measurementContext ? ['How big is this pancreas?', 'What is the size of the lesion in this scan?', ...suggestions] : suggestions).map(text => <button type="button" key={text} onClick={() => change(text)}>{text}</button>)}
    </div></details>}

    {originalQuestion && <details className="literature-search__interpretation"><summary>Original question</summary><p>{originalQuestion}</p></details>}
    {helpError && <p role="status">Question help is unavailable or timed out. Your question is unchanged; you can still use Ask question.</p>}
    {preview && <section className="literature-search__interpretation" aria-label="Question interpretation">
      <h3>{preview.status === 'suggested' ? 'Suggested search wording' : preview.status === 'unchanged' ? 'Keep your original question' : 'Let’s clarify the question'}</h3>
      <p>{preview.message}</p>
      {preview.status === 'suggested' && <>
        <label htmlFor="interpreted-question">Review or edit the wording</label>
        <textarea id="interpreted-question" rows={3} maxLength={500} value={previewText} onChange={e => setPreviewText(e.target.value)} />
        <button type="button" disabled={!previewText.trim()} onClick={() => { const original = originalQuestion || question; change(previewText.trim()); setOriginalQuestion(original); questionInput.current?.focus() }}>Use this wording</button>
      </>}
      <button type="button" onClick={() => setPreview(null)}>Keep my question</button>
    </section>}
    <div aria-live="polite" aria-busy={phase === 'loading'}>
      {(phase === 'loading' || result || scanResult) && <p className="literature-search__question"><small>{phase === 'loading' ? 'Processing question' : 'You asked'}</small>{submittedQuestion}</p>}
      {scanResult?.key === measurementKey && scanResult && <article className="literature-search__answer-card" aria-label="Current scan measurement">
        <h3>{scanResult.measurement && scanResult.target === 'pancreas_comparison' ? 'Outline compared with a published study' : scanResult.measurement ? 'Volume of this outline' : 'Measurement unavailable'}</h3>
        <p>{scanResult.measurement ? measurementText(scanResult.measurement, scanResult.target) : scanResult.message}</p>
        {scanResult.measurement && scanResult.target === 'pancreas_comparison' && <p><a href={pancreasReferenceUrl} target="_blank" rel="noreferrer">Study source: MRI pancreas volume (PMID 25950180)</a></p>}
        {scanResult.measurement && <>
          <p>The model outline needs human review before using this measurement.</p>
          <details><summary>Measurement source and limitations</summary>
            <p>Calculated locally from the saved prediction mask. {scanResult.measurement.unitsBasis}. {scanResult.measurement.coverage}. {scanResult.measurement.modelLineage}.</p>
            <p>Method: label count × absolute affine determinant. Pancreas includes labels 1 and 2; suspected-lesion total includes label 2 only. No reference annotation is used.</p>
            <p>Grid: {scanResult.measurement.shape.join(' × ')}; voxel volume: {scanResult.measurement.voxelMm3} mm³.</p>
            <p>{scanResult.measurement.hashBasis}.</p>
            <small>CT SHA-256: {scanResult.measurement.ctSha256}<br />Prediction SHA-256: {scanResult.measurement.predictionSha256}</small>
          </details>
        </>}
      </article>}
      {contextNotice && <p className="literature-search__context-notice">{contextNotice}</p>}
      {phase === 'loading' && <div className="literature-search__activity" role="status">
        <div className="literature-search__activity-head"><span className="literature-search__pulse" aria-hidden="true" /><strong>{helpMode ? 'Working on your wording' : measurementContext && scanQuestion(submittedQuestion) ? 'Checking the saved outline' : sourceMode ? 'Looking for sources' : 'Working on your question'}</strong><small>{elapsed}s elapsed</small></div>
        <p>{helpMode ? 'Preparing a search suggestion for you to review…' : measurementContext && scanQuestion(submittedQuestion) ? 'Checking the saved image geometry and calculating outline volume…' : sourceMode ? 'Finding source passages and their supporting context…' : 'I’m waiting for the local research service to return an answer and supporting sources.'}</p>
        <details><summary>What’s happening?</summary><p>{helpMode ? 'Your question is being rephrased. You choose whether to use the suggestion.' : measurementContext && scanQuestion(submittedQuestion) ? 'Measurements are calculated locally from the saved mask after geometry and coverage checks.' : 'The service processes your question as one request. Individual retrieval and answer-writing stages are not reported live. Returned evidence and citations will be available to inspect.'}</p></details>
      </div>}
      {phase === 'error' && <p role="alert">Search is unavailable or timed out. Use “Check status” or “Prepare AI expert” above. If the teacher is running, use “Find sources” until it is paused.</p>}
      {result && <article className="literature-search__answer-card" aria-label="Literature search results">
        {staleContext && <p className="literature-search__stale">General literature · asked while reviewing {askedFor.label || 'another study'}. Not about the current study.</p>}
        <h3>{result.state === 'retrieval_failed' ? 'Search unavailable' : result.reason?.startsWith('clarification_') ? 'Clarify your question' : result.record_selection?.policy === 'source-linked-volume-search-v1' && volumeReasons[result.record_selection.reason] && result.state !== 'not_searched' ? 'Clarify your question' : result.state === 'not_searched' ? 'Search needs a different question' : result.state === 'no_results' ? 'No passages found' : result.answer ? 'Answer' : 'Retrieved passages'}</h3>
        {result.answer ? <details className="literature-search__provenance"><summary>About this response</summary>
        <ResponseExplanation result={result} sourceMode={sourceMode} />
        </details> : <ResponseExplanation result={result} sourceMode={sourceMode} />}

        {sourceMode && result.record_selection?.matches.some(m => m.comparison) && <p>Comparisons: {result.record_selection.matches.map(m => m.comparison.join(' versus ').replace('focal_AIP', 'focal AIP')).join('; ')}. MFCP: mass-forming chronic pancreatitis. Focal AIP: focal autoimmune pancreatitis. PDAC: pancreatic ductal adenocarcinoma.</p>}
        {result.evidence.length > 0 && <LiteratureReadingView key={result.request_id} evidence={result.evidence} answer={result.answer} />}
        {!sourceMode && <details><summary>Keep this response</summary>
          <p>Download the submitted question, response, and citations for later inspection. This is general literature; no scan context is added automatically, and the file is not attached to your saved review.</p>
          {capture && <button type="button" onClick={() => {
            try { downloadCapture(capture); setCaptureNotice('Download requested. Check your downloads; your saved review has not changed.') }
            catch { setCaptureNotice('Download could not start. Your response is still available here; try again.') }
          }}>Download response and citations</button>}
          {captureNotice && <p role="status">{captureNotice}</p>}
        </details>}
        {result.state !== 'not_searched' && <details><summary>Search details</summary>
          <p>{config.source_count} papers · {config.passage_count.toLocaleString()} indexed passages · {result.answer_policy === 'single-pass-summary-v1' ? 'Single-call summary · Citation links checked; factual support requires review' : result.answer_policy === 'general-source-extract-v1' ? 'General source-sentence selection · Local Qwen3 8B · Development preview' : result.retrieval_policy === 'evidence-led-answer-v1' ? 'Evidence-led section selection · Local Qwen · Development regression' : sourceMode ? 'Reviewed source records with dense-search fallback · No answer model called' : result.answer_policy ? 'Reviewed source records · Qwen3 8B constrained composition · Independent review pending' : 'Exact dense search · Local Qwen3 answer model'}</p>
          <small>Collection: {result.collection}<br />Corpus: {result.target.inventory.content_sha256}<br />Request: {result.request_id}</small>
        </details>}
      </article>}
    </div>
    {history.some(entry => entry.id !== result?.request_id && entry.id !== scanResult?.requestId) && <section className="literature-search__history" aria-label="Recent responses">
      <h3>Recent responses</h3>
      <p>Last six responses in this session. Each question is answered independently.</p>
      {history.filter(entry => entry.id !== result?.request_id && entry.id !== scanResult?.requestId).map(entry => <RecentResponse key={entry.id} entry={entry} />)}
      <button type="button" onClick={() => setHistory([])}>Clear recent responses</button>
    </section>}
    <small>{panel ? measurementContext ? 'Each question is independent. Saved-mask measurements stay local; scan data is not sent to literature search. Results are not saved to your review.' : 'Each question is answered independently. No scan is attached. Responses are not saved automatically. Use Keep this response to download a copy.' : 'No scan is attached. Responses are not saved automatically. Use Keep this response to download a copy.'}</small>
  </section>
}

export function LiteratureReadingView({ evidence, answer }) {
  const sourceId = useId()
  const [view, setView] = useState(answer ? 'answer' : 'reading')
  const [selected, setSelected] = useState(null)
  const sources = useRef({})
  useEffect(() => {
    if (view === 'sources' && selected !== null) sources.current[selected]?.focus()
  }, [view, selected])
  return <div className="literature-search__reading-view">
    {view === 'answer' ? <div className="literature-search__prose" aria-label="AI answer">
      {answer.status === 'insufficient' && !answer.limitation && <p>I couldn’t find enough directly relevant evidence in the passages returned by this search to answer your question. You can inspect them in Sources or try a more specific question.</p>}
      {answer.claims.map((c, i) => <div className="literature-search__passage" key={i}>
        <p>{c.text}{' '}{c.citations.map(x => <button key={x.rank} type="button" className="literature-search__reference"
          aria-label={`View source ${x.rank}`} onClick={() => { setSelected(x.rank); setView('sources') }}>[{x.rank}]</button>)}</p>
      </div>)}
      {answer.scope && <p className="literature-search__qualification">{answer.scope}</p>}
      {answer.limitation && <p className="literature-search__qualification">{answer.limitation}</p>}
    </div> : view === 'reading' ? <div className="literature-search__prose" aria-label="Retrieved text">
      {evidence.map(({ rank, record: r }) => <div className="literature-search__passage" key={r.passage.passage_id}>
        <p>{r.text}</p>
        <button type="button" className="literature-search__reference" aria-label={`View source ${rank}`}
          onClick={() => { setSelected(rank); setView('sources') }}>Source [{rank}]</button>
      </div>)}
    </div> : <section className="literature-search__sources" aria-label="Sources">
      {evidence.map(({ rank, record: r }) => <section className="literature-search__result" key={r.passage.passage_id}
        aria-labelledby={`${sourceId}-source-${rank}`}>
        <h4 id={`${sourceId}-source-${rank}`} tabIndex={-1} ref={node => { sources.current[rank] = node }}>
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
    <div className="literature-search__view-switch" role="group" aria-label="Result view">
      {answer && <button type="button" aria-pressed={view === 'answer'} onClick={() => setView('answer')}>Answer</button>}
      <button type="button" aria-pressed={view === 'reading'} onClick={() => setView('reading')}>Read passages</button>
      <button type="button" aria-pressed={view === 'sources'} onClick={() => { setSelected(null); setView('sources') }}>Sources ({evidence.length})</button>
    </div>
  </div>
}

function ResponseExplanation({ result, sourceMode }) {
  return <p>{result.message || (result.state !== 'not_searched' && result.record_selection?.policy === 'source-linked-volume-search-v1' && volumeReasons[result.record_selection.reason] ? volumeReasons[result.record_selection.reason] : result.state === 'not_searched' ? reasons[result.reason] : result.state === 'no_results'
          ? 'No matching passages were returned. Try a broader pancreatic topic.'
          : result.answer?.provenance === 'model_synthesized_passages' ? 'AI summary · Preview · Check the linked sources for details.'
          : result.answer?.provenance === 'model_selected_source_sentences' ? 'Source-based answer · The local AI selected these quotations; wording is copied from the research.'
          : result.answer?.provenance === 'local_model_composition' ? 'Local AI summary · Select a citation to inspect its evidence.'
          : result.answer?.provenance === 'reviewed_source_fallback' ? 'The local AI could not finish a valid composition. This is a reviewed source summary assembled by the application, not model-written text.'
          : result.generation === 'completed' ? (result.answer?.status === 'insufficient' ? 'The search returned passages, but they did not support a checked answer.' : 'Written by the local AI using the sources below. Check the citations; this is a development preview.') : sourceMode ? (result.record_selection.status === 'matched' ? (result.retrieval_policy === 'source-linked-study-search-v1' ? 'The selected study passages and their limitations are shown below. These describe published research, not findings from your scan.' : result.retrieval_policy === 'source-linked-measurement-search-v1' ? 'The CT study’s measurement methods and limitations are shown below.' : result.retrieval_policy === 'source-linked-volume-search-v1' ? 'The selected MRI study groups and their supporting passages are shown below. These are study examples, not a normal range.' : 'Relevant comparison sources and their qualifications are shown below. These are literature examples, not an exhaustive list of diseases or a diagnosis.') : 'No reviewed source record matched this wording. Showing general literature search results.') : result.answer_policy ? 'This wording is outside the reviewed summary coverage. No answer model was called; the search passages are available to inspect.' : generationFailures[result.generation_failure] || 'The local AI could not produce a checked answer. You can still read the retrieved passages.')}</p>
}

function RecentResponse({ entry }) {
  const [open, setOpen] = useState(false)
  return <details onToggle={event => setOpen(event.currentTarget.open)}>
    <summary>{entry.question}</summary>
    {open && <div className="literature-search__history-body">
      <small>{entry.label}</small>
      {entry.response ? <>
        {entry.response.answer ? <LiteratureReadingView evidence={entry.response.evidence} answer={entry.response.answer} /> : <>
          <ResponseExplanation result={entry.response} sourceMode={entry.sourceMode} />
          {entry.response.evidence.length > 0 && <LiteratureReadingView evidence={entry.response.evidence} />}
        </>}
      </> : <>
        <p>{entry.text}</p>
        {entry.measured && <p>Calculated from the saved prediction outline; human review is required.</p>}
        {entry.comparison && entry.measured && <a href={pancreasReferenceUrl} target="_blank" rel="noreferrer">Study source: MRI pancreas volume (PMID 25950180)</a>}
      </>}
    </div>}
  </details>
}
