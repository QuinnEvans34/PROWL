import { useEffect, useRef, useState } from 'react'
import { evidenceFixture, evidenceStates, requestEvidence } from '../lib/guidedEvidence.js'
import './GuidedEvidencePanel.css'

export default function GuidedEvidencePanel({ loadResponse = requestEvidence }) {
  const [questionId, setQuestionId] = useState('workflow')
  const [response, setResponse] = useState(null)
  const [phase, setPhase] = useState('idle')
  const pending = useRef(null)
  const controller = useRef(null)
  useEffect(() => () => controller.current?.abort(), [])

  async function submit() {
    if (controller.current) return
    const request = pending.current || { request_id: crypto.randomUUID(), question_id: questionId }
    pending.current = request
    const active = new AbortController()
    controller.current = active
    setResponse(null)
    setPhase('loading')
    try {
      const saved = await loadResponse(request, active.signal)
      if (!active.signal.aborted) {
        setResponse(saved)
        setPhase('saved')
        pending.current = null
      }
    } catch {
      if (!active.signal.aborted) setPhase('unavailable')
    } finally {
      if (controller.current === active) controller.current = null
    }
  }

  return (
    <details className="guided-evidence">
      <summary>Guided evidence questions <span>Fixture demonstration</span></summary>
      <div className="guided-evidence__body">
        <p>{evidenceFixture.notice}</p>
        <p>PROWL supports research review. It cannot diagnose a patient or recommend treatment.
          Evidence support does not guarantee clinical truth.</p>
        <label htmlFor="guided-evidence-question">Reviewer question</label>
        <select id="guided-evidence-question" value={questionId} disabled={phase === 'loading'}
          onChange={event => { setQuestionId(event.target.value); setResponse(null); setPhase('idle'); pending.current = null }}>
          {evidenceFixture.questions.map(q => <option key={q.id} value={q.id}>{q.label}</option>)}
        </select>
        <button type="button" disabled={phase === 'loading'} onClick={submit}>
          {phase === 'loading' ? 'Saving fixture response…' : phase === 'unavailable' ? 'Retry same request' : 'Ask and save fixture response'}
        </button>
        <div aria-live="polite">
          {phase === 'loading' && <p>Checking the fixed passage and saving one response…</p>}
          {phase === 'unavailable' && <p role="alert">Evidence service unavailable or response invalid.
            A saved response could not be confirmed. No evidence conclusion can be drawn from this failure.
            Retry reuses the same request. The image viewer and review controls remain available.</p>}
          {response && <article aria-label="Saved fixture response">
            <h3>{evidenceStates[response.state]}</h3>
            <p>{response.message}</p>
            {response.claims.map(claim => <p key={claim.id}>{claim.text}</p>)}
            {response.citations.map(citation => <details key={citation.id}>
              <summary>Supporting passage: {citation.title}</summary>
              <blockquote>{citation.text}</blockquote>
              <p>{citation.locator} · {citation.rights}</p>
              <p>No publication year, DOI, or external literature link: this is a synthetic fixture.</p>
            </details>)}
            <p>Saved locally by the fixture service. Each new request creates a separate artifact.</p>
            <a href={`/evidence-fixture/responses/${response.response_id}`} download={`${response.response_id}.json`}>Download saved response JSON</a>
            <details><summary>Response provenance</summary>
              <p>Response: {response.response_id}</p>
              <p>Corpus: {response.provenance.corpus}; adapter: {response.provenance.adapter}</p>
              <p>No live index or generation model.</p>
              <p>Content SHA-256: {response.content_sha256}</p>
            </details>
          </article>}
        </div>
        <small>One response is shown at a time. Saved artifacts stay on the service’s disk;
          switching cases clears this panel. This demo does not attach evidence to a patient record.</small>
      </div>
    </details>
  )
}
