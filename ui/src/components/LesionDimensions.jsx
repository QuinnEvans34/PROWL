import { useEffect, useRef } from 'react'
import { LESION_DIMENSIONS_POLICY } from '../lib/lesionDimensions.js'

const cm = mm => mm < 0.1 ? '<0.01' : (mm / 10).toFixed(2)
const ml = value => value < 0.01 ? '<0.01' : value.toFixed(2)

function ComponentDimensions({ component, index, selected, onSelect, onInspect, sourceSlice }) {
  const axes = component.calipers?.axes
  return <li className="pw-lesion-dimensions__item" data-selected={selected || undefined}>
    <strong>Predicted lesion {index + 1}</strong> {selected && <span className="pw-lesion-dimensions__selected">Selected</span>}
    <dl>
      <div><dt>Centered slice calipers</dt><dd>{axes
        ? `${cm(axes[0].lengthMm)} × ${cm(axes[1].lengthMm)} cm`
        : 'Unavailable'}</dd></div>
      <div><dt>Head-to-foot extent</dt><dd>{cm(component.superiorInferiorMm)} cm</dd></div>
      <div><dt>Outline volume</dt><dd>{ml(component.volumeMl)} mL</dd></div>
    </dl>
    {axes ? <small>{sourceSlice ? 'Source slice' : 'Prepared slice'} {component.calipers.nativeSlice + 1} · Centered measurement</small>
      : <small>{component.caliperUnavailableReason}</small>}
    {(onSelect || onInspect) && <div className="pw-lesion-dimensions__actions">
      {onSelect && <button type="button" className="pw-btn pw-btn--secondary pw-btn--sm"
        aria-label={`Select lesion ${index + 1} in 3D`} onClick={() => onSelect(component)}>Select in 3D</button>}
      {onInspect && component.calipers?.plane && <button type="button" className="pw-btn pw-btn--primary pw-btn--sm"
        aria-label={`Inspect measurement for lesion ${index + 1}`} onClick={() => onInspect(component)}>Inspect measurement</button>}
    </div>}
    {onInspect && axes && !component.calipers.plane && <p className="pw-muted">This viewer cannot display the exact measurement plane.</p>}
  </li>
}

export default function LesionDimensions({ measurement, selectedId, onSelect, onInspect, selectionNotice, sourceSlice = false }) {
  const dimensions = measurement?.lesionDimensions
  const region = useRef(null)
  useEffect(() => {
    if (selectedId !== undefined && selectedId !== null) region.current?.scrollIntoView?.({ block: 'start' })
  }, [selectedId])
  if (dimensions?.policy !== LESION_DIMENSIONS_POLICY || !measurement.lesionVoxels) return null
  const { components } = dimensions
  const selectedIndex = components.findIndex(component => component.id === selectedId)
  const primaryIndex = Math.max(0, selectedIndex)
  const item = (component, index) => <ComponentDimensions key={component.id} component={component} index={index}
    selected={selectedId === component.id} onSelect={onSelect} onInspect={onInspect} sourceSlice={sourceSlice} />
  return <section className="pw-lesion-dimensions" aria-label="Predicted lesion dimensions" ref={region}>
    <h3>Lesion measurements</h3>
    {selectionNotice && <p className="pw-muted" role="status">{selectionNotice}</p>}
    {dimensions.status === 'unavailable' ? <p className="pw-muted">{dimensions.reason}</p> : <>
      {components[primaryIndex] && <ol>{item(components[primaryIndex], primaryIndex)}</ol>}
      {components.length > 1 && <details className="pw-disclosure">
        <summary>{components.length - 1} more predicted {components.length === 2 ? 'lesion' : 'lesions'}</summary>
        <ol>{components.map((component, i) => i !== primaryIndex && item(component, i))}</ol>
      </details>}
    </>}
  </section>
}
