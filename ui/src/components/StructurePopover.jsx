import { MessageSquareText, X } from 'lucide-react'
import { REVIEW_COLORS, objectLabel } from '../lib/viewerLayers.js'
import { structureQuestions } from '../lib/structureQuestions.js'

function fmt(value, digits) {
  return Number.isFinite(value) ? value.toFixed(digits) : null
}

function structureFacts(object, { finding, overlap, comparing, gtHasLesion }) {
  if (object.source === 'difference') {
    const dice = fmt(overlap?.[object.anatomy], 3)
    return [
      ['Region', { agreement: 'Both outlines', predOnly: 'Prediction only', gtOnly: 'Reference only' }[object.region] || 'Difference'],
      ['Dice', dice ?? (object.anatomy === 'lesion' && !gtHasLesion && !finding.lesionFlagged ? 'Absent in both' : 'Unavailable')],
    ]
  }
  const facts = [['Source', object.source === 'gt' ? 'Reference annotation' : 'Model proposal']]
  if (object.source === 'pred' && object.anatomy === 'lesion') {
    const volume = Number.isFinite(finding.volumeMm3) ? `${(finding.volumeMm3 / 1000).toFixed(2)} cm³` : 'Unavailable'
    facts.push(['Volume', volume])
    if (finding.diameterMm) facts.push(['Equiv. diameter', `${finding.diameterMm} mm`])
  }
  if (comparing) {
    const dice = fmt(overlap?.[object.anatomy], 3)
    if (dice) facts.push(['Dice vs. reference', dice])
  }
  return facts
}

// Small card anchored where the reviewer clicked a surface or mask. It summarises the
// already-published facts for that structure and offers general literature questions.
export default function StructurePopover({
  object,
  anchor,
  finding,
  overlap,
  comparing,
  gtHasLesion,
  focusControl,
  onAsk,
  onClose,
}) {
  const color = object.source === 'difference'
    ? REVIEW_COLORS.difference[object.region]
    : REVIEW_COLORS[object.source]?.[object.anatomy]
  const facts = structureFacts(object, { finding, overlap, comparing, gtHasLesion })
  const questions = structureQuestions(object)
  const style = anchor ? { left: `${anchor.left}px`, top: `${anchor.top}px` } : undefined
  return (
    <section className={`pw-structure-pop${anchor ? '' : ' pw-structure-pop--docked'}`} style={style} role="dialog" aria-label={`${objectLabel(object)} details`}>
      <header className="pw-structure-pop__head">
        <i style={{ '--selection-color': color }} aria-hidden="true" />
        <div>
          <small>Focused structure</small>
          <strong>{objectLabel(object)}</strong>
        </div>
        <button type="button" className="pw-icon-btn" onClick={onClose} aria-label="Clear structure focus"><X size={14} /></button>
      </header>
      <dl className="pw-structure-pop__facts">
        {facts.map(([label, value]) => (
          <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
        ))}
      </dl>
      {focusControl}
      {questions.length > 0 && (
        <div className="pw-structure-pop__ask">
          <span><MessageSquareText size={13} aria-hidden="true" /> Ask PROWL about this</span>
          {questions.map((text) => (
            <button type="button" key={text} onClick={() => onAsk(text)}>{text}</button>
          ))}
          <small>Answers come from published literature, not from this scan.</small>
        </div>
      )}
    </section>
  )
}
