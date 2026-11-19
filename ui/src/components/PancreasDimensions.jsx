import { useEffect, useRef } from 'react'

function centimetres(mm) {
  return mm < 0.1 ? '<0.01' : (mm / 10).toFixed(2)
}

export default function PancreasDimensions({ measurementState, selected, onSelect, onInspect, sourceSlice = false }) {
  const region = useRef(null)
  useEffect(() => {
    if (selected) region.current?.scrollIntoView?.({ block: 'nearest' })
  }, [selected])

  const dimensions = measurementState?.status === 'ready' ? measurementState.measurement?.pancreasDimensions : null
  const calipers = dimensions?.calipers
  const axes = calipers?.axes
  const hasCalipers = axes?.length === 2 && axes.every(axis => Number.isFinite(axis.lengthMm) && axis.lengthMm > 0)
  const extent = dimensions?.superiorInferiorMm
  const hasExtent = Number.isFinite(extent) && extent > 0
  const pending = measurementState?.status === 'loading'
  const reason = dimensions?.caliperUnavailableReason || dimensions?.reason

  return <section className="pw-pancreas-dimensions" aria-label="Predicted pancreas dimensions"
    data-selected={selected || undefined} ref={region}>
    <h3>Pancreas measurements{selected && <span className="pw-lesion-dimensions__selected">Selected</span>}</h3>
    {pending ? <p className="pw-muted" role="status">Checking the pancreas outline…</p>
      : hasCalipers || hasExtent ? <>
        <dl>
          <div><dt>Centered slice calipers</dt><dd>{hasCalipers ? `${axes.map(axis => centimetres(axis.lengthMm)).join(' × ')} cm` : 'Unavailable'}</dd></div>
          <div><dt>Head-to-foot extent</dt><dd>{hasExtent ? `${centimetres(extent)} cm` : 'Unavailable'}</dd></div>
        </dl>
        {hasCalipers && <small>{sourceSlice ? 'Source slice' : 'Prepared slice'} {calipers.nativeSlice + 1} · Largest outlined area</small>}
        {reason && (!hasCalipers || !calipers.plane) && <p className="pw-muted">{reason}</p>}
      </> : <p className="pw-muted">{reason || measurementState?.reason || 'Pancreas dimensions unavailable.'}</p>}
    <div className="pw-lesion-dimensions__actions">
      {onSelect && <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm"
        aria-label="Select pancreas in 3D" disabled={!hasExtent && !hasCalipers} onClick={onSelect}>Select in 3D</button>}
      {onInspect && hasCalipers && calipers.plane && <button type="button" className="pw-btn pw-btn--primary pw-btn--sm"
        aria-label="Inspect pancreas measurement" onClick={onInspect}>Inspect measurement</button>}
    </div>
  </section>
}
