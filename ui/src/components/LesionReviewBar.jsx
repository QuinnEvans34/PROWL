const cm = mm => mm < 0.1 ? '<0.01' : (mm / 10).toFixed(2)
const ml = amount => amount < 0.01 ? '<0.01' : amount.toFixed(2)

export default function LesionReviewBar({ anatomy = 'lesion', component, number, status, actions, onExit, volumeMl = component?.volumeMl }) {
  const calipers = component?.calipers
  const isPancreas = anatomy === 'pancreas'
  return <section className="pw-lesion-review" aria-label={isPancreas ? 'Pancreas review' : 'Lesion review'} data-selected={component ? '' : undefined}>
    <div className="pw-lesion-review__readout" role="status">
      <strong>{isPancreas ? 'Predicted pancreas' : component ? `Predicted lesion ${number}` : 'Lesion review'}</strong>
      {component && <dl aria-label={`Selected ${anatomy} measurements`}>
        {calipers && <div><dt>Slice</dt><dd>{calipers.axes.map(axis => cm(axis.lengthMm)).join(' × ')} cm</dd></div>}
        <div><dt>Head to foot</dt><dd>{cm(component.superiorInferiorMm)} cm</dd></div>
        {Number.isFinite(volumeMl) && <div><dt>Volume</dt><dd>{ml(volumeMl)} mL</dd></div>}
      </dl>}
      {status && <span className="pw-lesion-review__status">{status}</span>}
    </div>
    {(actions || onExit) && <div className="pw-lesion-review__actions">
      {actions}
      {onExit && <button type="button" className="pw-btn pw-btn--sm pw-btn--secondary"
        title="Exit inspection (Esc)" aria-keyshortcuts="Escape" onClick={onExit}>Exit inspection</button>}
    </div>}
  </section>
}
