import { useState } from 'react'

export default function LocalExpertReadiness({ onStatus }) {
  const [busy, setBusy] = useState(null)
  const [state, setState] = useState(null)
  const [error, setError] = useState('')
  async function check(prepare) {
    setBusy(prepare ? 'prepare' : 'status'); setError('')
    try {
      const response = await fetch(`/local-expert/${prepare ? 'prepare' : 'status'}`, {
        method: prepare ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(prepare ? 245000 : 15000),
      })
      const value = await response.json()
      if (!response.ok || value.error) throw new Error(value.error || 'Readiness check unavailable.')
      if (['drive', 'database', 'search', 'ollama', 'model', 'gpu_busy'].some(k => typeof value[k] !== 'boolean')) throw new Error('Readiness check unavailable.')
      setState(value); onStatus?.(value)
    } catch (e) { setError(e.name === 'TimeoutError' ? (prepare ? 'Preparation timed out. Check status before trying again.' : 'Status check timed out. Try checking again.') : e.message) }
    finally { setBusy(null) }
  }
  return <aside aria-label="AI expert readiness" className="literature-search__readiness">
    <div className="literature-search__actions">
      <button type="button" disabled={Boolean(busy)} onClick={() => check(true)}>{busy === 'prepare' ? 'Preparing local services…' : 'Prepare AI expert'}</button>
      <button type="button" disabled={Boolean(busy)} onClick={() => check(false)}>{busy === 'status' ? 'Checking status…' : 'Check status'}</button>
    </div>
    <div aria-live="polite">
      {busy && <p>{busy === 'prepare' ? 'Checking local storage and starting missing services. This can take a few minutes.' : 'Checking local service status.'}</p>}
      {state && !error && !busy && <>
        <p>{state.search ? 'Source search is ready.' : 'Source search needs preparation.'} {state.gpu_busy ? 'The teacher is using the GPU. Pause it before testing AI answers; source search can run alongside it.' : state.model && state.search ? 'The local model is loaded and ready for questions.' : 'Prepare the AI expert to load the local model.'}</p>
        <details><summary>Service status</summary><ul>
          {Object.entries({ drive: 'Literature storage', database: 'Literature database', search: 'Search service', ollama: 'Model service', model: 'Answer model loaded' }).map(([key, label]) => <li key={key}>{label}: {state[key] ? 'Ready' : 'Not ready'}</li>)}
        </ul></details>
      </>}
      {error && <p role="alert">{error}</p>}
    </div>
  </aside>
}
