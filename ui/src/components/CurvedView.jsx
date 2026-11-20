import { useState } from 'react'
import { ANATOMY_STRUCTURES, rgb } from '../lib/studyInsights.js'

const BASE = '/cases'

// Straightened curved reformat along the predicted pancreas (head left, tail right).
// Images are precomputed by scripts/build_workbench_insights.py; overlays share the same grid.
export default function CurvedView({ caseData, insights, showPrediction = true, showReference = false, showAnatomy = true }) {
  const cpr = insights?.cpr
  const files = caseData?.files?.cpr
  const [hoverMm, setHoverMm] = useState(null)
  if (!cpr || !files) {
    return <div className="pw-curved pw-curved--empty" role="region" aria-label="Curved pancreas view">
      <p>A curved view is not available for this study.</p>
    </div>
  }
  const [width, height] = cpr.pixels
  const ticks = []
  for (let mm = 0; mm <= cpr.length_mm; mm += 10) ticks.push(mm)
  const span = cpr.lesion_span_mm
  const pct = mm => `${(mm / cpr.length_mm) * 100}%`
  const anatomyInView = ANATOMY_STRUCTURES.filter(item => insights.anatomy?.some(a => a.name === item.name && a.annotated !== false))

  return (
    <div className="pw-curved" role="region" aria-label="Curved pancreas view">
      <header className="pw-curved__head">
        <div>
          <strong>Curved pancreas view</strong>
          <small>Straightened along the predicted pancreas · {cpr.length_mm.toFixed(0)} mm long · ±{(cpr.width_mm / 2).toFixed(0)} mm</small>
        </div>
        {hoverMm !== null && <output className="pw-num" aria-live="off">{hoverMm.toFixed(0)} mm from head end</output>}
      </header>
      <div className="pw-curved__frame">
        <span className="pw-curved__axis pw-curved__axis--top">Anterior</span>
        <span className="pw-curved__axis pw-curved__axis--left">Head</span>
        <span className="pw-curved__axis pw-curved__axis--right">Tail</span>
        <div className="pw-curved__plot" style={{ width: `min(100%, calc(var(--pw-curved-max-h, 52vh) * ${(width / height).toFixed(4)}))` }}>
        <div className="pw-curved__image" style={{ aspectRatio: `${width} / ${height}` }}
          onPointerMove={event => {
            const rect = event.currentTarget.getBoundingClientRect()
            setHoverMm(Math.max(0, Math.min(cpr.length_mm, ((event.clientX - rect.left) / rect.width) * cpr.length_mm)))
          }}
          onPointerLeave={() => setHoverMm(null)}>
          <img src={`${BASE}/${files.ct}`} alt={`Curved CT reformat along the pancreas, ${cpr.length_mm.toFixed(0)} mm`} draggable="false" />
          {showAnatomy && files.anatomy && <img src={`${BASE}/${files.anatomy}`} alt="" aria-hidden="true" draggable="false" />}
          {showReference && files.reference && <img src={`${BASE}/${files.reference}`} alt="" aria-hidden="true" draggable="false" className="pw-curved__dashed" />}
          {showPrediction && files.prediction && <img src={`${BASE}/${files.prediction}`} alt="" aria-hidden="true" draggable="false" />}
          {span && <span className="pw-curved__span" style={{ left: pct(span[0]), width: pct(span[1] - span[0]) }}
            title={`Predicted lesion ${span[0].toFixed(0)}–${span[1].toFixed(0)} mm from the head end`} />}
          {hoverMm !== null && <span className="pw-curved__cursor" style={{ left: pct(hoverMm) }} aria-hidden="true" />}
        </div>
        <div className="pw-curved__ruler" aria-hidden="true">
          {ticks.map(mm => <span key={mm} style={{ left: pct(mm) }} className={mm % 50 === 0 ? 'major' : ''}>{mm % 50 === 0 ? `${mm} mm` : ''}</span>)}
        </div>
        </div>
      </div>
      <footer className="pw-curved__legend">
        {showPrediction && <><span><i style={{ background: '#26c5a6' }} />Predicted pancreas</span><span><i style={{ background: '#f96363' }} />Predicted lesion</span></>}
        {showReference && <span><i className="dashed" style={{ borderColor: '#38bdf8' }} />Reference outline</span>}
        {showAnatomy && anatomyInView.map(item => <span key={item.name}><i style={{ background: rgb(item.color) }} />{item.label}</span>)}
      </footer>
      <p className="pw-curved__note">{cpr.method}. Reference anatomy comes from the dataset annotation, not the model.
        {span ? ` Predicted lesion spans ${span[0].toFixed(0)}–${span[1].toFixed(0)} mm from the head end.` : ' No predicted lesion along the gland.'}</p>
    </div>
  )
}
