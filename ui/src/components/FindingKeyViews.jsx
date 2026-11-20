import { useRef, useState } from 'react'
import {
  createFindingKeyView, exportFindingKeyView, importFindingKeyView, keyViewScope,
  KEY_VIEW_EXPORT_LIMIT, KEY_VIEW_NOTE_LIMIT, matchesKeyViewScope, readFindingKeyViews, saveFindingKeyView,
} from '../lib/findingKeyViews.js'
import './FindingKeyViews.css'

function downloadKeyView(text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'application/json' }))
  try {
    const link = document.createElement('a')
    link.href = url
    link.download = 'prowl-key-view.json'
    document.body.appendChild(link)
    link.click()
    link.remove()
  } finally {
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
}

function findingName(finding) {
  if (finding.anatomy === 'pancreas') return 'Pancreas'
  return finding.ordinal ? `Predicted lesion ${finding.ordinal}` : 'Predicted lesion'
}

export default function FindingKeyViews({
  scope, finding, capture, captureThumbnail, onReopen, storage, download = downloadKeyView,
}) {
  const [saved, setSaved] = useState(() => readFindingKeyViews(storage))
  const [notice, setNotice] = useState(null)
  const [portable, setPortable] = useState(null)
  const [thumbnails, setThumbnails] = useState({})
  const ready = keyViewScope(scope)
  const noticeKey = JSON.stringify([scope?.studyId, ready?.ctSha256, ready?.predictionSha256, ready?.manifestHash])
  const current = useRef(null)
  current.current = { scope: ready, noticeKey, onReopen }
  const pendingFile = useRef(0)
  const items = saved.filter(item => item.scope.studyId === scope?.studyId)
  const activePortable = matchesKeyViewScope(ready, portable?.keyView) ? portable : null
  const message = notice?.key === noticeKey ? notice.text : ''

  function announce(text) {
    setNotice({ key: current.current.noticeKey, text })
  }

  function save() {
    pendingFile.current += 1
    try {
      const record = createFindingKeyView(ready, finding, capture())
      if (!record) {
        announce('Wait for the selected finding and its image to finish loading.')
        return
      }
      const updated = saveFindingKeyView(record, storage)
      setSaved(updated)
      const image = captureThumbnail?.()
      if (image) setThumbnails(previous => Object.fromEntries(updated
        .map(item => [item.id, item.id === record.id ? image : previous[item.id]])
        .filter(([, preview]) => preview)))
      setPortable({ keyView: record, reviewerNote: '' })
      announce('Key view saved on this browser.')
    } catch (error) {
      announce(error.message || 'The key view could not be saved.')
    }
  }

  function reopen(record, reviewerNote = '') {
    pendingFile.current += 1
    const { scope: openScope, onReopen: restore } = current.current
    if (!openScope) {
      announce('Show the verified prediction to reopen this key view.')
      return false
    }
    if (!matchesKeyViewScope(openScope, record)) {
      announce('This key view belongs to a different study, CT series, or prediction.')
      return false
    }
    const reason = restore(record)
    if (reason) {
      announce(reason)
      return false
    }
    setPortable({ keyView: record, reviewerNote })
    announce('Key view opened.')
    return true
  }

  async function openFile(event) {
    const file = event.currentTarget.files?.[0]
    event.currentTarget.value = ''
    if (!file) return
    const request = ++pendingFile.current
    try {
      if (file.size > KEY_VIEW_EXPORT_LIMIT) throw new Error('The key view file is too large.')
      const { keyView, reviewerNote } = importFindingKeyView(await file.text())
      if (pendingFile.current === request) reopen(keyView, reviewerNote)
    } catch (error) {
      if (pendingFile.current === request) announce(error.message || 'The key view file could not be opened.')
    }
  }

  function exportCopy() {
    try {
      download(exportFindingKeyView(activePortable.keyView, activePortable.reviewerNote))
      announce('Key view download requested.')
    } catch (error) {
      announce(error.message || 'The key view could not be exported.')
    }
  }

  return <section className="pw-finding-key-views" aria-label="Key views">
    <div className="pw-finding-key-views__heading">
      <h3>Key views</h3>
      {finding && <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm"
        disabled={!ready || !capture} onClick={save}>Save key view</button>}
    </div>
    <p className="pw-fine pw-finding-key-views__notice" role="status">{message}</p>
    {items.length > 0 && <ul className="pw-finding-key-views__list">
      {items.map(item => <li key={item.id}>
        {matchesKeyViewScope(ready, item) && thumbnails[item.id] && <img className="pw-finding-key-views__thumbnail"
          src={thumbnails[item.id]} alt="Captured CT slice" />}
        <div>
          <strong>{findingName(item.finding)}</strong>
          <small>{item.view.plane}{Number.isSafeInteger(item.view.sliceIndex) ? ` · slice ${item.view.sliceIndex + 1}` : ''}
            {' · '}<time dateTime={item.createdAt}>{new Date(item.createdAt).toLocaleString()}</time></small>
        </div>
        <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" aria-label={`Reopen ${findingName(item.finding)} key view`}
          onClick={() => reopen(item)}>Reopen</button>
      </li>)}
    </ul>}
    <details className="pw-disclosure">
      <summary>Key view file</summary>
      <div className="pw-finding-key-views__portable">
        <label>
          Open a key view file for this prediction
          <input type="file" accept=".json,application/json" onChange={openFile} />
        </label>
        {activePortable && <>
          <label>
            Reviewer note for export <small>Optional. Saved in the downloaded file.</small>
            <textarea value={activePortable.reviewerNote} rows={3} maxLength={KEY_VIEW_NOTE_LIMIT}
              onChange={event => setPortable({ ...activePortable, reviewerNote: event.target.value })} />
          </label>
          <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm" onClick={exportCopy}>Download key view</button>
        </>}
      </div>
    </details>
  </section>
}
