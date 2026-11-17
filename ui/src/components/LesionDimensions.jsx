import { LESION_DIMENSIONS_POLICY } from '../lib/lesionDimensions.js'

const cm = mm => mm < 0.1 ? '<0.01' : (mm / 10).toFixed(2)
const ml = value => value < 0.01 ? '<0.01' : value.toFixed(2)

function ComponentDimensions({ component, index }) {
  const axes = component.calipers?.axes
  return <li className="pw-lesion-dimensions__item">
    <strong>Predicted lesion {index + 1}</strong>
    <dl>
      <div><dt>Centered slice calipers</dt><dd>{axes
        ? `${cm(axes[0].lengthMm)} × ${cm(axes[1].lengthMm)} cm`
        : 'Unavailable'}</dd></div>
      <div><dt>Head-to-foot extent</dt><dd>{cm(component.superiorInferiorMm)} cm</dd></div>
      <div><dt>Outline volume</dt><dd>{ml(component.volumeMl)} mL</dd></div>
    </dl>
    {axes ? <small>Native slice {component.calipers.nativeSlice + 1} · Not a maximum diameter</small>
      : <small>{component.caliperUnavailableReason}</small>}
  </li>
}

export default function LesionDimensions({ measurement }) {
  const dimensions = measurement?.lesionDimensions
  if (dimensions?.policy !== LESION_DIMENSIONS_POLICY || !measurement.lesionVoxels) return null
  const { components } = dimensions
  return <section className="pw-lesion-dimensions" aria-label="Predicted lesion dimensions">
    <h3>Lesion measurements</h3>
    {dimensions.status === 'unavailable' ? <p className="pw-muted">{dimensions.reason}</p> : <>
      <ol><ComponentDimensions component={components[0]} index={0} /></ol>
      {components.length > 1 && <details className="pw-disclosure">
        <summary>{components.length - 1} more predicted {components.length === 2 ? 'lesion' : 'lesions'}</summary>
        <ol start={2}>{components.slice(1).map((component, i) =>
          <ComponentDimensions key={component.id} component={component} index={i + 1} />)}</ol>
      </details>}
    </>}
  </section>
}
