/** Select between only the image sources bound to the active finding. */
export default function InspectionSourceControls({ sourceAvailable, preparedAvailable = true, activeSource = 'prepared',
  onSourceChange, sourcePending = false, sourceError = '' }) {
  return <div className="pw-inspection-source" role="group" aria-label="Inspection CT source">
    {sourceAvailable && preparedAvailable ? <>
      <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" aria-pressed={activeSource === 'prepared'}
        onClick={() => onSourceChange('prepared')}>Prepared CT</button>
      <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" aria-pressed={activeSource === 'source'}
        disabled={sourcePending} onClick={() => onSourceChange('source')}>Source CT</button>
    </> : <span>{sourceAvailable ? 'Source CT' : 'Prepared CT'}</span>}
    {sourcePending ? <span role="status">Loading source CT…</span>
      : sourceError ? <span role="status">{sourceError}</span>
        : !sourceAvailable && <span className="pw-muted">Source CT unavailable for this prediction</span>}
  </div>
}
