import { useEffect, useRef, useState } from 'react'
import { prepareLocalCt } from '../lib/localCtImport.js'

export default function LocalCtImport({ onOpenStudy }) {
  const [deidentified, setDeidentified] = useState(false)
  const [state, setState] = useState({ phase: 'idle' })
  const active = useRef(null)

  function releasePending() {
    const previous = active.current
    active.current = null
    previous?.controller.abort()
    previous?.study?.release()
  }
  useEffect(() => releasePending, [])

  async function choose(file) {
    releasePending()
    if (!file) { setState({ phase: 'idle' }); return }
    const current = { controller: new AbortController(), study: null }
    active.current = current
    setState({ phase: 'checking' })
    try {
      const study = await prepareLocalCt(file, current.controller.signal)
      if (active.current !== current) { study.release(); return }
      current.study = study
      setState({ phase: 'ready', shape: study.geometry.shape, spacing: study.caseData.spacing_mm })
    } catch (error) {
      if (active.current === current) setState({ phase: 'error', error: error.message })
    }
  }

  function open() {
    const current = active.current
    if (!current?.study || !onOpenStudy) return
    if (onOpenStudy(current.study) === false) return
    active.current = null
    setState({ phase: 'idle' })
  }

  return <section className="pw-import__drop" aria-label="Open local NIfTI CT">
    <h3>Open a NIfTI CT</h3>
    <p className="pw-muted">Choose one .nii or .nii.gz file. The CT stays in this browser tab. Analysis requires a configured CT-only model worker.</p>
    <label className="pw-check"><input type="checkbox" checked={deidentified} onChange={event => {
      setDeidentified(event.target.checked)
      if (!event.target.checked) { releasePending(); setState({ phase: 'idle' }) }
    }} />This research CT is already de-identified</label>
    {deidentified && <label className="pw-field">Choose a NIfTI CT
      <input type="file" accept=".nii,.nii.gz" onChange={event => {
        const file = event.target.files?.[0]
        event.target.value = ''
        void choose(file)
      }} />
    </label>}
    {state.phase === 'checking' && <p role="status">Checking the local CT and its geometry…</p>}
    {state.phase === 'error' && <p role="alert" className="pw-notice pw-notice--danger">{state.error}</p>}
    {state.phase === 'ready' && <>
      <p role="status">Ready to review · {state.shape.join(' × ')} voxels · {state.spacing.map(value => Number(value.toFixed(3))).join(' × ')} mm</p>
      <button type="button" className="pw-btn pw-btn--primary" onClick={open}>Open CT in Workbench</button>
    </>}
  </section>
}
