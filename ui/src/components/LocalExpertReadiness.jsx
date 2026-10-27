import { useState } from 'react'

export default function LocalExpertReadiness({ onStatus }) {
  const [busy, setBusy] = useState(false)
  const [state, setState] = useState(null)
  const [error, setError] = useState('')
  async function check(prepare) {
    setBusy(true); setError('')
    try {
      const response = await fetch(`/local-expert/${prepare ? 'prepare' : 'status'}`, {
        method: prepare ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(245000),
      })
      const value = await response.json()
      if (!response.ok || value.error) throw new Error(value.error || 'Readiness check unavailable.')
      if (['drive', 'database', 'search', 'ollama', 'model', 'gpu_busy'].some(k => typeof value[k] !== 'boolean')) throw new Error('Readiness check unavailable.')
      setState(value); onStatus?.(value)
    } catch (e) { setError(e.name === 'TimeoutError' ? 'Preparation timed out. Check status before trying again.' : e.message) }
    finally { setBusy(false) }
  }
  return <aside aria-label="AI expert readiness" className="literature-search__readiness">
    <div className="literature-search__actions">
      <button type="button" disabled={busy} onClick={() => check(true)}>{busy ? 'Checking local services…' : 'Prepare AI expert'}</button>
      <button type="button" disabled={busy} onClick={() => check(false)}>Check status</button>
    </div>
    <div aria-live="polite">
      {busy && <p>Checking the drive and starting missing services. This can take a few minutes.</p>}
      {state && <>
        <p>{state.search ? 'Source search is ready.' : 'Source search needs preparation.'} {state.gpu_busy ? 'The teacher is using the GPU. Pause it before testing AI answers; source search can run alongside it.' : state.model && state.search ? 'The local model is loaded and ready for questions.' : 'Prepare the AI expert to load the local model.'}</p>
        <details><summary>Service status</summary><ul>
          {Object.entries({ drive: 'Data drive and storage', database: 'Literature database', search: 'Search service', ollama: 'Model service', model: 'Answer model loaded' }).map(([key, label]) => <li key={key}>{label}: {state[key] ? 'Ready' : 'Not ready'}</li>)}
        </ul></details>
      </>}
      {error && <p role="alert">{error}</p>}
    </div>
  </aside>
}
