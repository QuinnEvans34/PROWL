import { useEffect, useReducer, useRef } from 'react'
import { AlertTriangle, ArrowLeft, Check, CircleSlash, FolderOpen, Info, X } from 'lucide-react'
import { EXAMPLE_SERIES, IMPORT_ERRORS, importReducer, initialImportState, unavailableAdapter } from '../lib/importAdapter.js'

function useFocusTrap(ref, onClose) {
  const closeRef = useRef(onClose)
  closeRef.current = onClose
  useEffect(() => {
    const node = ref.current
    const previous = document.activeElement
    const focusables = () => [...node.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])')]
    focusables()[0]?.focus()
    function onKey(event) {
      if (event.key === 'Escape') { event.preventDefault(); closeRef.current(); return }
      if (event.key !== 'Tab') return
      const items = focusables()
      if (!items.length) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    node.addEventListener('keydown', onKey)
    return () => { node.removeEventListener('keydown', onKey); previous?.focus?.() }
  }, [ref])
}

const STEPS = [['selecting', 'Choose files'], ['series_selection', 'Select series'], ['importing', 'Import'], ['ready', 'Open']]

function Stepper({ step }) {
  const order = { selecting: 0, validating: 0, series_selection: 1, importing: 2, ready: 3, failed: 2, cancelled: -1 }
  const current = order[step] ?? 0
  return (
    <ol className="pw-steps" aria-label="Import steps">
      {STEPS.map(([key, label], index) => (
        <li key={key} className={index < current ? 'is-done' : index === current ? 'is-current' : ''} aria-current={index === current ? 'step' : undefined}>
          <span aria-hidden="true">{index < current ? <Check size={12} /> : index + 1}</span>{label}
        </li>
      ))}
    </ol>
  )
}

function spacing(series) {
  return series.spacingMm ? `${series.spacingMm.join(' × ')} mm` : '—'
}

export default function ImportStudyDialog({ adapter = unavailableAdapter, onClose, onOpenStudies }) {
  const [state, dispatch] = useReducer(importReducer, initialImportState)
  const ref = useRef(null)
  useFocusTrap(ref, onClose)
  const example = state.mode === 'example'
  const selected = EXAMPLE_SERIES.find((series) => series.seriesKey === state.selectedSeries)

  return (
    <div className="pw-backdrop" role="presentation" onMouseDown={onClose}>
      <section ref={ref} className="pw-dialog pw-import" role="dialog" aria-modal="true" aria-labelledby="import-title" aria-describedby="import-desc" onMouseDown={(event) => event.stopPropagation()}>
        <button type="button" className="pw-icon-btn pw-dialog__close" onClick={onClose} aria-label="Close import"><X size={17} /></button>
        <h2 id="import-title">{example ? 'Import CT study · example walkthrough' : 'Import CT study'}</h2>

        {example && (
          <p className="pw-example-banner" role="note">
            <strong>Example</strong> Synthetic walkthrough. No files are read, nothing is converted, and no study is created.
          </p>
        )}

        {!example && (
          <>
            <p id="import-desc" className="pw-muted">Bring a CT study into PROWL, choose the series to review, then open it in the Workbench.</p>
            {!adapter.capabilities.available && (
              <div className="pw-notice pw-notice--warning" role="status">
                <CircleSlash size={16} aria-hidden="true" />
                <div>
                  <strong>DICOM import isn’t connected yet</strong>
                  <p>{adapter.capabilities.reason}</p>
                </div>
              </div>
            )}
            <div className="pw-import__options">
              <button type="button" className="pw-option" onClick={() => { onClose(); onOpenStudies() }}>
                <strong>Open a prepared study</strong>
                <span>Prepared CT studies are ready to review now.</span>
              </button>
              <button type="button" className="pw-option" onClick={() => dispatch({ type: 'START_EXAMPLE' })}>
                <strong>See the example walkthrough</strong>
                <span>Step through series selection and its error states with synthetic data.</span>
              </button>
            </div>
            <p className="pw-fine">When connected, selecting files will not start analysis. You will see the study first and choose when to analyze.</p>
          </>
        )}

        {example && (
          <>
            <Stepper step={state.step} />
            <div className="pw-import__body" aria-live="polite">
              {state.step === 'selecting' && (
                <div className="pw-import__drop">
                  <FolderOpen size={22} aria-hidden="true" />
                  <p><strong>Choose a DICOM folder or ZIP</strong></p>
                  <p className="pw-muted">Files stay on this workstation. The ingestion service groups them by study and series and checks each one.</p>
                  <button type="button" className="pw-btn pw-btn--primary" onClick={() => dispatch({ type: 'CHOOSE_INPUT' })}>Use example folder</button>
                </div>
              )}
              {state.step === 'validating' && (
                <div className="pw-import__drop">
                  <p><strong>Checking files</strong></p>
                  <p className="pw-muted">A connected service would report what it found here. In this example, continue to see its result.</p>
                  <button type="button" className="pw-btn pw-btn--primary" onClick={() => dispatch({ type: 'VALIDATED' })}>Show example result</button>
                </div>
              )}
              {state.step === 'series_selection' && (
                <>
                  <p className="pw-muted" id="series-help">1 example study, {EXAMPLE_SERIES.length} series found. Choose one CT series. Series are never merged.</p>
                  <div className="pw-series" role="radiogroup" aria-labelledby="series-help">
                    {EXAMPLE_SERIES.map((series) => (
                      <label key={series.seriesKey} className={`pw-series__row${state.selectedSeries === series.seriesKey ? ' is-selected' : ''}${series.eligible ? '' : ' is-ineligible'}`}>
                        <input type="radio" name="series" value={series.seriesKey} checked={state.selectedSeries === series.seriesKey}
                          onChange={() => dispatch({ type: 'SELECT_SERIES', seriesKey: series.seriesKey })} />
                        <span className="pw-series__main">
                          <strong>{series.description}</strong>
                          <small>{series.modality} · {series.instanceCount} images · {series.orientation} · {spacing(series)}</small>
                          {series.reasons.map((reason) => <small key={reason} className="pw-series__reason"><CircleSlash size={11} aria-hidden="true" /> {reason}</small>)}
                          {series.warnings.map((warning) => <small key={warning} className="pw-series__warning"><AlertTriangle size={11} aria-hidden="true" /> {warning}</small>)}
                        </span>
                        <span className={`pw-tag${series.eligible ? '' : ' pw-tag--muted'}`}>{series.eligible ? 'Eligible' : 'Not eligible'}</span>
                      </label>
                    ))}
                  </div>
                  {state.error && <p className="pw-notice pw-notice--danger" role="alert"><AlertTriangle size={15} aria-hidden="true" /> {IMPORT_ERRORS[state.error]} {selected?.reasons?.[0]}</p>}
                  {selected?.eligible && (
                    <dl className="pw-facts pw-import__meta" aria-label="Selected series details">
                      <div><dt>Modality</dt><dd>{selected.modality}</dd></div>
                      <div><dt>Images</dt><dd>{selected.instanceCount}</dd></div>
                      <div><dt>Orientation</dt><dd>{selected.orientation}</dd></div>
                      <div><dt>Voxel spacing</dt><dd>{spacing(selected)}</dd></div>
                    </dl>
                  )}
                </>
              )}
              {state.step === 'importing' && (
                <div className="pw-import__drop">
                  <p><strong>Importing {selected?.description}</strong></p>
                  <p className="pw-muted">A connected service would report its real conversion progress here. PROWL never shows a percentage it does not receive. Choose how this example ends:</p>
                  <div className="pw-import__outcomes">
                    <button type="button" className="pw-btn pw-btn--primary" onClick={() => dispatch({ type: 'IMPORT_RESULT' })}>Conversion succeeds</button>
                    <button type="button" className="pw-btn pw-btn--secondary" onClick={() => dispatch({ type: 'IMPORT_RESULT', error: 'conversion_failed' })}>Conversion fails</button>
                    <button type="button" className="pw-btn pw-btn--secondary" onClick={() => dispatch({ type: 'IMPORT_RESULT', error: 'duplicate_study' })}>Already imported</button>
                  </div>
                </div>
              )}
              {state.step === 'ready' && (
                <div className="pw-import__drop">
                  <Check size={22} aria-hidden="true" />
                  <p><strong>Example ready to open</strong></p>
                  <p className="pw-muted">In a connected version, the converted series would open in the Workbench as CT only. Analysis would not start until you choose Analyze. This example creates no study.</p>
                </div>
              )}
              {state.step === 'failed' && (
                <div className="pw-notice pw-notice--danger" role="alert">
                  <AlertTriangle size={16} aria-hidden="true" />
                  <div><strong>Import did not complete</strong><p>{IMPORT_ERRORS[state.error]} No partial study was added.</p></div>
                </div>
              )}
              {state.step === 'cancelled' && (
                <div className="pw-notice" role="status">
                  <Info size={16} aria-hidden="true" />
                  <div><strong>Import cancelled</strong><p>Nothing was imported.</p></div>
                </div>
              )}
            </div>
            <div className="pw-dialog__foot">
              <button type="button" className="pw-btn pw-btn--ghost" onClick={() => dispatch({ type: 'BACK_TO_LIVE' })}>
                <ArrowLeft size={14} aria-hidden="true" /> Exit example
              </button>
              <span className="pw-toolbar__spacer" />
              {['selecting', 'validating', 'series_selection', 'importing'].includes(state.step) && (
                <button type="button" className="pw-btn pw-btn--secondary" onClick={() => dispatch({ type: 'CANCEL' })}>Cancel import</button>
              )}
              {state.step === 'series_selection' && (
                <button type="button" className="pw-btn pw-btn--primary" disabled={!state.selectedSeries} onClick={() => dispatch({ type: 'CONFIRM' })}>Import selected series</button>
              )}
              {['ready', 'failed', 'cancelled'].includes(state.step) && (
                <button type="button" className="pw-btn pw-btn--secondary" onClick={() => dispatch({ type: 'RESTART' })}>Start again</button>
              )}
              {state.step === 'ready' && (
                <button type="button" className="pw-btn pw-btn--primary" onClick={() => { onClose(); onOpenStudies() }}>Done</button>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  )
}
