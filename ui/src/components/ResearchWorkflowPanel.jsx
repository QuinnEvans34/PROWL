import { useEffect, useRef, useState } from 'react'
import questions from '../../../configs/evidence/research-questions-v1.json'
import { validateResearch } from './ResearchEvidencePanel.jsx'

const stages = ['retrieve', 'select', 'validate', 'save']
const labels = { retrieve: 'Retrieve passages', select: 'Select evidence', validate: 'Verify quotations', save: 'Save answer' }
const states = { pending: 'Waiting', running: 'In progress', completed: 'Complete', reused: 'Reused from prior attempt', failed: 'Failed' }

export async function workflowRequest(request, signal, inspect = false) {
  const url = '/research-workflow/runs' + (inspect ? `/${request.request_id}` : '')
  const reply = await fetch(url, inspect ? { signal } : { method: 'POST', signal,
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request) })
  if (!reply.ok) throw new Error('Workflow unavailable')
  const run = await reply.json()
  if (run.schema_version !== 'prowl-research-workflow-v1' || run.run_id !== request.request_id
    || run.request?.request_id !== request.request_id || run.request?.question_id !== request.question_id
    || run.request?.resume_of !== request.resume_of
    || run.question !== questions.find(q => q.id === request.question_id)?.label
    || !['running', 'completed', 'failed', 'interrupted'].includes(run.state)
    || !Array.isArray(run.stages) || run.stages.length !== 4
    || !run.stages.every((s, i) => s.stage === stages[i] && Object.hasOwn(states, s.state))) {
    throw new Error('Invalid workflow record')
  }
  if (run.state === 'completed') {
    if (!run.stages.every(s => ['completed', 'reused'].includes(s.state))) throw new Error('Incomplete workflow')
    validateResearch(run.response, { request_id: request.request_id, question_id: request.question_id }, true)
    if (run.response.generation.validation === 'generation_rejected') throw new Error('Rejected answer')
  } else if (run.response) throw new Error('Premature answer')
  return run
}

export default function ResearchWorkflowPanel({ loadWorkflow = workflowRequest }) {
  const [question, setQuestion] = useState(questions[0].id)
  const [run, setRun] = useState(null)
  const [phase, setPhase] = useState('idle')
  const pending = useRef(null), active = useRef(null)
  useEffect(() => () => active.current?.abort(), [])
  async function submit() {
    if (active.current) return
    const retry = ['failed', 'interrupted'].includes(run?.state)
    const request = pending.current || { request_id: crypto.randomUUID(), question_id: question,
      ...(retry ? { resume_of: run.run_id } : {}) }
    pending.current = request
    const controller = new AbortController(); active.current = controller
    setPhase('loading'); setRun(null)
    const timeout = setTimeout(() => controller.abort(), 120000)
    let inspecting = false
    const progress = setInterval(async () => {
      if (inspecting || controller.signal.aborted) return
      inspecting = true
      try {
        const next = await loadWorkflow(request, controller.signal, true)
        if (active.current === controller && !controller.signal.aborted) setRun(next)
      } catch { /* A new run may not have been published yet. POST remains authoritative. */ }
      finally { inspecting = false }
    }, 750)
    try {
      let next = await loadWorkflow(request, controller.signal)
      while (next.state === 'running' && !controller.signal.aborted) {
        setRun(next)
        await new Promise(resolve => setTimeout(resolve, 750))
        if (!controller.signal.aborted) next = await loadWorkflow(request, controller.signal, true)
      }
      if (controller.signal.aborted) throw new Error('Status unconfirmed')
      setRun(next); setPhase('saved'); pending.current = null
    } catch {
      if (active.current === controller) setPhase('unavailable')
    } finally {
      clearInterval(progress); clearTimeout(timeout)
      controller.abort()
      if (active.current === controller) active.current = null
    }
  }
  const failed = ['failed', 'interrupted'].includes(run?.state)
  const rejected = run?.stages.some(s => s.reason === 'invalid_generation')
  const response = phase === 'saved' && run?.state === 'completed' ? run.response : null
  return <details className="guided-evidence">
    <summary>Research evidence workflow <span>Stage status and recovery</span></summary>
    <div className="guided-evidence__body">
      <p>Retrieve passages, select evidence, verify quotations, and save an answer. A retry reuses verified work from the original search. Relevance and completeness still need review.</p>
      <label htmlFor="workflow-question">Workflow question</label>
      <select id="workflow-question" value={question} disabled={phase === 'loading'} onChange={e => {
        setQuestion(e.target.value); setRun(null); setPhase('idle'); pending.current = null
      }}>{questions.map(q => <option key={q.id} value={q.id}>{q.label}</option>)}</select>
      <button disabled={phase === 'loading'} onClick={submit}>
        {phase === 'loading' ? 'Working through evidence…' : phase === 'unavailable' ? 'Check same request' : failed ? 'Retry failed stage' : 'Run evidence workflow'}
      </button>
      <div aria-live="polite">
        {phase === 'unavailable' && <p role="alert">We could not confirm the workflow status. Check the same request before starting another attempt.</p>}
        {run && <>
          <ol aria-label="Evidence workflow stages">{run.stages.map(s => <li key={s.stage}>{labels[s.stage]}: {states[s.state]}</li>)}</ol>
          {phase === 'saved' && failed && <p role="alert">{rejected
            ? 'Generation failed verification. This does not mean the sources lack evidence. No answer was published.'
            : run.state === 'interrupted' ? 'The workflow was interrupted. An explicit retry will preserve this attempt and reuse verified work.'
            : 'A workflow stage failed. No answer was published. Check the local services and storage before retrying.'}</p>}
          {response && <article aria-label="Saved workflow answer">
            <h3>{response.generation.answer.status === 'excerpts' ? 'Verified source quotations' : 'Insufficient evidence in the selected passages'}</h3>
            {response.generation.answer.status === 'insufficient_evidence' && <p>The workflow completed, but the selected passages did not provide a supported answer.</p>}
            {response.generation.answer.extracts.map((e, i) => {
              const source = response.passages.find(p => p.record.passage.passage_id === e.passage_id).record
              return <div key={i}><blockquote>{e.quote}</blockquote><p>{source.citation.title}{source.citation.year ? ` (${source.citation.year})` : ''} · {source.citation.authors.join('; ')}</p>
                <a href={`https://pmc.ncbi.nlm.nih.gov/articles/${source.citation.pmcid}/`} target="_blank" rel="noreferrer">Read source · PMID {source.citation.pmid}</a>
                <p>{source.citation.attribution} · CC BY 4.0</p></div>
            })}
            <p>Quotation matching does not establish medical accuracy or completeness. PROWL cannot diagnose patients or recommend treatment.</p>
            <a href={`/research-workflow/responses/${run.run_id}`} download>Download workflow answer</a>
          </article>}
          <a href={`/research-workflow/runs/${run.run_id}`} download>Download workflow history</a>
          {run.request.resume_of && <p>Prior attempt: <a href={`/research-workflow/runs/${run.request.resume_of}`}>{run.request.resume_of}</a>. The original search snapshot was retained.</p>}
        </>}
      </div>
      <small>Local development service required. Each explicit recovery creates a linked attempt; no automatic model retries. No patient data is sent or attached.</small>
    </div>
  </details>
}
