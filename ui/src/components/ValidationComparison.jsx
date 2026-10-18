import { lazy, Suspense, useState } from 'react'
import { ArrowLeft, BadgeCheck, BookOpen, CircleAlert } from 'lucide-react'

const NiivueViewer = lazy(() => import('./NiivueViewer.jsx'))

function validationOutcome(caseData) {
  const predicted = Boolean(caseData?.pred_has_lesion)
  const reference = Boolean(caseData?.gt_has_lesion)
  if (predicted && reference) return 'True positive'
  if (!predicted && !reference) return 'True negative'
  if (predicted) return 'False positive'
  return 'False negative'
}

function ViewerSuspense({ children }) {
  return (
    <Suspense fallback={<div className="viewer-module-loading" role="status">Preparing medical viewer…</div>}>
      {children}
    </Suspense>
  )
}

// Validation layer: three synchronized-by-convention views of a validation example
// whose package permits reference comparison. Only rendered for those studies.
export default function ValidationComparison({ caseId, caseData, caseOptions, profile, onSelectCase, onBack }) {
  const [mode, setMode] = useState('2d')
  const bothAbsent = !caseData.gt_has_lesion && !caseData.pred_has_lesion
  const views = [
    ['pred', ['pred'], 'Model prediction', 'Prediction', [['pred-pancreas', 'Predicted pancreas'], ['pred-lesion', 'Predicted lesion']]],
    ['gt', ['gt'], 'Reference annotation', 'Reference', [['ref-pancreas', 'Reference pancreas'], ['ref-lesion', 'Reference lesion']]],
    ['both', ['gt', 'pred'], 'Combined overlay', 'Analysis', [['pred-pancreas', 'Prediction'], ['ref-pancreas', 'Reference']]],
  ]
  return (
    <main className="pw-page pw-compare" aria-labelledby="compare-title">
      <section className="pw-compare__head">
        <div>
          <button type="button" className="pw-btn pw-btn--ghost pw-btn--sm" onClick={onBack}>
            <ArrowLeft size={14} aria-hidden="true" /> Back to review
          </button>
          <p className="pw-eyebrow" style={{ marginTop: 14 }}>Validation · reference annotation visible</p>
          <h1 id="compare-title" className="pw-display">Prediction and reference, side by side.</h1>
          <p className="pw-lede">A scientific comparison of a saved model result against an independent reference annotation — not a claim of diagnostic reliability.</p>
        </div>
        <div className="pw-compare__controls">
          <label className="pw-select">
            <span>Validation example</span>
            <select value={caseId} onChange={(event) => onSelectCase(event.target.value)}>
              {caseOptions.map(([id, label]) => <option value={id} key={id}>{id.replace('PanTS_', 'PanTS ')} · {label}</option>)}
            </select>
          </label>
          <div className="pw-segmented" role="group" aria-label="Comparison view">
            <button type="button" aria-pressed={mode === '2d'} onClick={() => setMode('2d')}>Three planes</button>
            <button type="button" aria-pressed={mode === '3d'} onClick={() => setMode('3d')}>3D surfaces</button>
          </div>
        </div>
      </section>

      <dl className="pw-metric-strip">
        <div><dt>Validation outcome</dt><dd>{validationOutcome(caseData)}</dd></div>
        <div><dt title="Dice coefficient against the reference annotation">Pancreas Dice</dt><dd className="pw-num">{Number.isFinite(caseData.dice_pancreas) ? caseData.dice_pancreas.toFixed(3) : 'Unavailable'}</dd></div>
        <div>
          <dt title="Dice coefficient against the reference annotation">Lesion Dice</dt>
          <dd className="pw-num">{bothAbsent ? 'No lesion in either' : Number.isFinite(caseData.dice_lesion) ? caseData.dice_lesion.toFixed(3) : 'Unavailable'}</dd>
        </div>
        <div><dt>Predicted lesion volume</dt><dd className="pw-num">{Number.isFinite(caseData.lesion_volume_mm3) ? `${(caseData.lesion_volume_mm3 / 1000).toFixed(2)} cm³` : 'Unavailable'}</dd></div>
      </dl>

      <section className="pw-compare__grid">
        {views.map(([key, sources, title, badge, legend]) => (
          <article className="pw-compare__view" key={key}>
            <header>
              <h2>{title}</h2>
              <span className="pw-tag">{key === 'gt' && <BookOpen size={12} aria-hidden="true" />}{badge}</span>
            </header>
            <ViewerSuspense>
              <NiivueViewer
                key={`${key}-${caseId}-${mode}`}
                caseData={caseData}
                sources={sources}
                mode={mode}
                overlayOpacity={key === 'both' ? 0.6 : 0.72}
                ctOpacity={mode === '3d' ? 0 : 0.1}
                compact
                label={`${caseId} ${title.toLowerCase()}`}
              />
            </ViewerSuspense>
            <footer>
              {legend.map(([swatch, text]) => <span key={text}><i className={`pw-swatch pw-swatch--${swatch}`} aria-hidden="true" />{text}</span>)}
            </footer>
          </article>
        ))}
      </section>

      {profile && (
        <section className="pw-compare__notes">
          <span className="pw-compare__icon" aria-hidden="true">
            {caseData.gt_has_lesion ? <BadgeCheck size={18} /> : <CircleAlert size={18} />}
          </span>
          <div>
            <p className="pw-eyebrow">What this validation example shows · {profile.eyebrow}</p>
            <h2>{profile.interpretation}</h2>
            <dl>
              <div><dt>Pancreas</dt><dd>{profile.strength}</dd></div>
              <div><dt>Lesion</dt><dd>{caseData.gt_has_lesion ? 'Correct region identified.' : 'No matching reference lesion is present.'} {profile.limitation}</dd></div>
            </dl>
          </div>
        </section>
      )}
    </main>
  )
}
