import { ArrowUpRight, Check, Database, Download, Info, MessageSquareText, MessageSquareWarning, Radio, TriangleAlert } from 'lucide-react'
import { REVIEW_COLORS } from '../lib/viewerLayers.js'
import { structureQuestions } from '../lib/structureQuestions.js'

function fmt(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : null
}

function Unavailable({ children = 'Unavailable' }) {
  return <span className="pw-unavailable">{children}</span>
}

// Findings use only validated, already-published values. Missing values are shown as
// unavailable — never zero, never recomputed from a visual bounding box.
export default function FindingsPanel({
  caseId,
  caseData,
  hasPrediction,
  predictionFile,
  liveResult,
  isCurated,
  finding,
  overlap,
  referenceState,
  comparing,
  ranges,
  analysisFailed,
  onShowInViewer,
  onAsk = null,
  onCompare,
  reviewStatus,
  onSetReviewStatus,
  onStartSummary,
  modelLabel,
}) {
  const source = liveResult?.source === 'live'
    ? { icon: Radio, label: `Live analysis · ${liveResult.scoredAt}`, detail: `${fmt(liveResult.result.inference_seconds, 1)} s inference` }
    : { icon: Database, label: 'Saved prediction', detail: 'Produced earlier from the prepared CT' }
  const SourceIcon = source.icon
  const volumeCm3 = Number.isFinite(finding.volumeMm3) ? finding.volumeMm3 / 1000 : null
  const studyLabel = caseId.replace('PanTS_', 'PanTS ')

  if (!predictionFile) {
    return (
      <div className="pw-findings">
        <p className="pw-context-chip"><i aria-hidden="true" />{studyLabel} · No prediction</p>
        <div className="pw-card">
          <h3>No prediction available</h3>
          <p className="pw-muted">This study has a CT but no published model prediction. The CT remains fully reviewable.</p>
        </div>
      </div>
    )
  }

  if (!hasPrediction) {
    return (
      <div className="pw-findings">
        <p className="pw-context-chip"><i aria-hidden="true" />{studyLabel} · CT only</p>
        <h3 className="pw-panel-title">Inspect the CT first</h3>
        <p className="pw-muted">Model outlines are hidden until you show them. Findings appear here once a prediction is displayed.</p>
        {analysisFailed && (
          <p className="pw-notice pw-notice--warning" role="alert">
            <TriangleAlert size={15} aria-hidden="true" />
            <span>Live analysis failed or is offline. No new prediction was produced; nothing was substituted.</span>
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="pw-findings">
      <p className="pw-context-chip"><i aria-hidden="true" />{studyLabel} · {source.label}</p>

      <ul className="pw-structures" aria-label="Structures in this prediction">
        <li className="pw-structure">
          <span className="pw-swatch" style={{ background: REVIEW_COLORS.pred.pancreas }} aria-hidden="true" />
          <div className="pw-structure__main">
            <h3 id="finding-pancreas">Pancreas</h3>
            <small>Model outline</small>
          </div>
          <div className="pw-structure__actions">
            <button type="button" className="pw-icon-btn" disabled={!ranges.pancreas} onClick={() => onShowInViewer('pancreas')} aria-label="Show pancreas in viewer" title="Show in viewer">
              <ArrowUpRight size={14} aria-hidden="true" />
            </button>
            {onAsk && (
              <button type="button" className="pw-icon-btn" onClick={() => onAsk(structureQuestions({ source: 'pred', anatomy: 'pancreas' })[0])} aria-label="Ask PROWL about the pancreas" title="Ask PROWL (general literature)">
                <MessageSquareText size={14} aria-hidden="true" />
              </button>
            )}
          </div>
        </li>
        <li className="pw-structure">
          <span className="pw-swatch" style={{ background: REVIEW_COLORS.pred.lesion }} aria-hidden="true" />
          <div className="pw-structure__main">
            <h3 id="finding-lesion">{finding.lesionFlagged ? 'Possible lesion' : 'Lesion'}</h3>
            <small>{finding.lesionFlagged ? 'Model proposal' : 'None predicted'}</small>
          </div>
          {finding.lesionFlagged && (
            <dl className="pw-structure__metrics">
              <div>
                <dt>Volume</dt>
                <dd>{volumeCm3 !== null ? <><span className="pw-num">{volumeCm3.toFixed(2)}</span> cm³</> : <Unavailable />}</dd>
              </div>
              <div>
                <dt title="Diameter of a sphere with the same volume. Not a measured width or length.">≈ Diameter</dt>
                <dd>{finding.diameterMm ? <><span className="pw-num">{finding.diameterMm}</span> mm</> : <Unavailable />}</dd>
              </div>
            </dl>
          )}
          <div className="pw-structure__actions">
            {finding.lesionFlagged && (
              <button type="button" className="pw-icon-btn" disabled={!ranges.lesion} onClick={() => onShowInViewer('lesion')} aria-label="Show lesion in viewer" title="Show in viewer">
                <ArrowUpRight size={14} aria-hidden="true" />
              </button>
            )}
            {onAsk && (
              <button type="button" className="pw-icon-btn" onClick={() => onAsk(structureQuestions({ source: 'pred', anatomy: 'lesion' })[0])} aria-label="Ask PROWL about pancreatic lesions" title="Ask PROWL (general literature)">
                <MessageSquareText size={14} aria-hidden="true" />
              </button>
            )}
          </div>
        </li>
        {comparing && (
          <li className="pw-structure pw-structure--reference" aria-labelledby="finding-reference">
            <span className="pw-swatch" style={{ background: REVIEW_COLORS.gt.pancreas }} aria-hidden="true" />
            <div className="pw-structure__main">
              <h3 id="finding-reference">Agreement with reference</h3>
              <small>Dice</small>
            </div>
            <dl className="pw-structure__metrics">
              <div><dt>Pancreas</dt><dd>{fmt(overlap.pancreas, 3) ? <span className="pw-num">{fmt(overlap.pancreas, 3)}</span> : <Unavailable />}</dd></div>
              <div>
                <dt>Lesion</dt>
                <dd>{!caseData.gt_has_lesion && !finding.lesionFlagged ? 'Absent in both' : fmt(overlap.lesion, 3) ? <span className="pw-num">{fmt(overlap.lesion, 3)}</span> : <Unavailable />}</dd>
              </div>
            </dl>
          </li>
        )}
      </ul>
      <p className="pw-fine">
        {finding.lesionFlagged
          ? 'Lesion volume comes from the predicted mask; ≈ diameter is a same-volume sphere, not a measured width or length. Proposals for review, not a diagnosis.'
          : 'The model did not predict a lesion. This does not establish that no lesion is present.'}
        {comparing ? ' Dice is computed against this study’s reference annotation and shown only while comparing.' : ''}
        {' '}Click a structure in the viewer for details and related literature questions.
      </p>

      {!comparing && referenceState !== 'absent' && (
        <p className="pw-reference-line">
          {referenceState === 'incompatible'
            ? 'A reference annotation exists but its geometry does not match this CT. Comparison is unavailable.'
            : referenceState === 'locked'
              ? 'Reference annotation available. It stays hidden during review.'
              : <>Reference annotation available. <button type="button" className="pw-btn pw-btn--link" onClick={onCompare}>Compare with reference</button></>}
        </p>
      )}
      {referenceState === 'absent' && (
        <p className="pw-reference-line">No reference annotation for this study. The review is complete without one.</p>
      )}

      <button type="button" className="pw-btn pw-btn--secondary pw-btn--block" onClick={onStartSummary}>
        Start review summary
      </button>

      <details className="pw-disclosure">
        <summary><Info size={14} aria-hidden="true" /> Source and provenance</summary>
        <dl className="pw-facts pw-facts--compact">
          <div><dt>Prediction</dt><dd><SourceIcon size={12} aria-hidden="true" /> {source.label}</dd></div>
          <div><dt>Model</dt><dd>{modelLabel}</dd></div>
          {liveResult?.source === 'live' && <div><dt>Inference</dt><dd>{source.detail}</dd></div>}
          <div>
            <dt title="Peak model output. Not a probability of disease.">Peak model score</dt>
            <dd>{fmt(finding.confidence) ?? <Unavailable />} <small>not a probability</small></dd>
          </div>
          <div><dt>Voxel spacing</dt><dd>{Array.isArray(caseData.spacing_mm) ? `${caseData.spacing_mm.join(' × ')} mm` : <Unavailable />}</dd></div>
          <div><dt>Pancreas volume</dt><dd><Unavailable>Not published in this package</Unavailable></dd></div>
          <div><dt>Display surfaces</dt><dd>{caseData.display_mesh_version === 'v3-difference-main-smoothing' ? 'v3, matched smoothing' : caseData.display_mesh_version ? 'v2, explicit normals' : 'v1, source-grid reconstruction'}</dd></div>
          <div><dt>Study type</dt><dd>{isCurated ? 'Validation example' : 'Prepared study'}</dd></div>
        </dl>
        <p className="pw-fine">Measurements derive from the original NIfTI masks, not the display surfaces.</p>
        {caseData.files?.pred && (
          <a className="pw-btn pw-btn--ghost pw-btn--sm" href={`/cases/${caseData.files.pred}`} download>
            <Download size={13} aria-hidden="true" /> Export prediction (NIfTI)
          </a>
        )}
      </details>

      <div className="pw-marks" role="group" aria-label="Local review mark">
        <span>Local mark <small>this browser only</small></span>
        <button type="button" className={`pw-btn pw-btn--ghost pw-btn--sm${reviewStatus === 'reviewed' ? ' is-on' : ''}`} aria-pressed={reviewStatus === 'reviewed'} onClick={() => onSetReviewStatus('reviewed')}>
          <Check size={13} aria-hidden="true" /> Mark reviewed
        </button>
        <button type="button" className={`pw-btn pw-btn--ghost pw-btn--sm${reviewStatus === 'discussion' ? ' is-on' : ''}`} aria-pressed={reviewStatus === 'discussion'} onClick={() => onSetReviewStatus('discussion')}>
          <MessageSquareWarning size={13} aria-hidden="true" /> Discuss
        </button>
      </div>
    </div>
  )
}
