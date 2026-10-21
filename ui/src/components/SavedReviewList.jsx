import { useEffect, useState } from 'react'
import { reviewRequest } from './ReviewDecisionPanel.jsx'
import { hrefFor } from '../lib/router.js'

const decisions = { accept: 'Accepted', edit_required: 'Needs correction', reject: 'Rejected' }

function checkedPackages(data) {
  if (!Array.isArray(data?.packages) || data.packages.length > 20) throw new Error('Invalid saved review list.')
  const seen = new Set()
  for (const p of data.packages) {
    const e = p?.latest, hash = p?.manifest_sha256
    if (!/^[a-f0-9]{64}$/.test(hash || '') || seen.has(hash)
      || typeof p.case_id !== 'string' || !p.case_id || p.case_id.length > 80
      || e?.case_package_id !== `case-package:${hash}` || e?.prediction_id !== `prediction:${hash}`
      || !Object.hasOwn(decisions, e?.action) || !Number.isSafeInteger(e.revision) || e.revision < 1
      || typeof e.recorded_at !== 'string' || !Number.isFinite(Date.parse(e.recorded_at))
      || typeof e.reviewer?.reviewer_id !== 'string') throw new Error('Invalid saved review list.')
    seen.add(hash)
  }
  return [...data.packages].sort((a,b) => Date.parse(b.latest.recorded_at) - Date.parse(a.latest.recorded_at)
    || a.manifest_sha256.localeCompare(b.manifest_sha256))
}

export default function SavedReviewList({ navigate }) {
  const [reload, setReload] = useState(0)
  const [state, setState] = useState({ status: 'loading', packages: [] })
  useEffect(() => {
    const controller = new AbortController()
    setState({ status: 'loading', packages: [] })
    reviewRequest('packages', { signal: controller.signal }).then(checkedPackages).then(packages => {
      if (!controller.signal.aborted) setState({ status: 'ready', packages })
    }).catch(() => {
      if (!controller.signal.aborted) setState({ status: 'error', packages: [] })
    })
    return () => controller.abort()
  }, [reload])
  function open(event, target) {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return
    event.preventDefault(); navigate(target)
  }
  return <section className="pw-page pw-section" aria-labelledby="retained-reviews-title">
    <div className="pw-section__head">
      <div><h2 id="retained-reviews-title">Saved reviews</h2>
        <p className="pw-muted">Reopen the retained CT, predicted contours, and recorded decisions. Each row identifies one exact prediction.</p></div>
      <div className="pw-welcome__actions">
        <a className="pw-btn pw-btn--primary" href={hrefFor({view:'predict'})} onClick={e => open(e,{view:'predict'})}>Analyze a scan</a>
        <button className="pw-btn pw-btn--secondary" disabled={state.status === 'loading'} onClick={() => setReload(n => n+1)}>Refresh saved reviews</button>
      </div>
    </div>
    {state.status === 'loading' && <p role="status">Loading saved reviews…</p>}
    {state.status === 'error' && <p role="alert">Saved reviews could not be loaded. Check the local review service and refresh. Existing records have not been removed.</p>}
    {state.status === 'ready' && !state.packages.length && <p>No recorded reviews yet. Analyze a scan, inspect its result, and record a decision to retain it here.</p>}
    {state.status === 'ready' && state.packages.length > 0 && <div className="pw-table-wrap"><table className="pw-table">
      <caption className="pw-sr-only">Retained predictions and latest recorded decisions</caption>
      <thead><tr><th scope="col">Study / prediction</th><th scope="col">Latest decision</th><th scope="col">Recorded by</th><th scope="col">Recorded at</th><th scope="col">Open</th></tr></thead>
      <tbody>{state.packages.map(p => <tr key={p.manifest_sha256}>
        <td><strong className="pw-mono-id">{p.case_id}</strong><small>Prediction {p.manifest_sha256.slice(0,12)}</small></td>
        <td><span className="pw-cell-main">{decisions[p.latest.action]}</span><small>Revision {p.latest.revision}</small></td>
        <td>{p.latest.reviewer.reviewer_id}</td>
        <td><time dateTime={p.latest.recorded_at}>{new Date(p.latest.recorded_at).toLocaleString()}</time></td>
        <td><a className="pw-btn pw-btn--secondary pw-btn--sm" href={hrefFor({view:'saved',review:p.manifest_sha256})}
          aria-label={`Reopen ${p.case_id}, prediction ${p.manifest_sha256.slice(0,12)}`}
          onClick={e => open(e,{view:'saved',review:p.manifest_sha256})}>Reopen review</a></td>
      </tr>)}</tbody>
    </table></div>}
    <p className="pw-fineprint">Recorded decisions are research reviews. They do not establish measurement accuracy or a diagnosis. Model provenance and measurement limitations appear with the opened prediction.</p>
  </section>
}
