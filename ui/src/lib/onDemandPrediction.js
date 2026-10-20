const BASE = '/scan-inference'
export async function request(path, options = {}) {
  const signal = options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(10000)]) : AbortSignal.timeout(10000)
  const response = await fetch(BASE + path, { ...options, signal, cache: 'no-store' })
  const value = await response.json()
  if (!response.ok) throw new Error(value.error || `Prediction service returned ${response.status}.`)
  return value
}
export const predictionCatalog = signal => request('/cases', { signal })
const delay = (ms, signal) => new Promise((resolve, reject) => {
  if (signal?.aborted) return reject(signal.reason)
  const cancel = () => { clearTimeout(timer); reject(signal.reason) }
  const timer = setTimeout(() => { signal?.removeEventListener('abort', cancel); resolve() }, ms)
  signal?.addEventListener('abort', cancel, { once: true })
})
export async function disposePrediction(id) {
  try {
    await request(`/jobs/${id}/cancel`, { method: 'POST' })
    for (let i = 0; i < 20; i++) {
      const job = await request(`/jobs/${id}`)
      if (!['queued', 'running', 'cancelling'].includes(job.status)) {
        await request(`/jobs/${id}`, { method: 'DELETE' })
        return
      }
      await delay(250)
    }
  } catch { /* Server shutdown also releases session storage. */ }
}
export async function predictStudy(caseId, signal, onState, onJob) {
  // Retain POST's job ID even if the user changes studies before its response arrives.
  let job = await request('/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ case_id: caseId }) })
  if (!/^[a-f0-9]{32}$/.test(job.job_id) || job.case_id !== caseId || !/^[a-f0-9]{64}$/.test(job.request_identity)) throw new Error('Invalid prediction job identity.')
  const id = job.job_id, identity = job.request_identity
  onJob(id)
  const deadline = Date.now() + 610000
  try {
    for (;;) {
      signal.throwIfAborted()
      if (job.case_id !== caseId || job.job_id !== id || job.request_identity !== identity) throw new Error('Prediction job identity changed.')
      onState(job.status)
      if (job.status === 'ready') return job
      if (!['queued', 'running'].includes(job.status)) throw new Error(job.error || 'Prediction was cancelled or failed.')
      if (Date.now() >= deadline) throw new Error('Prediction timed out.')
      await delay(500, signal)
      job = await request(`/jobs/${id}`, { signal })
    }
  } catch (error) {
    void disposePrediction(id)
    throw error
  }
}
