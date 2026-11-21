import { ArrowUpRight, Check, Database, Download, Info, MessageSquareText, MessageSquareWarning, Radio, TriangleAlert } from 'lucide-react'
import { studyDisplayName, useStudyNames } from '../lib/studyNames.js'
import { REVIEW_COLORS } from '../lib/viewerLayers.js'
import { structureQuestions } from '../lib/structureQuestions.js'
import LesionDimensions from './LesionDimensions.jsx'
import PancreasDimensions from './PancreasDimensions.jsx'
import { LesionCharacteristics, StructuredSummary, VesselRelationship } from './FindingsInsights.jsx'

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
  insights = null,
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
  measurementState,
  selectedPancreas,
  onSelectPancreas,
  onInspectPancreas,
  selectedLesionId,
  onSelectLesion,
  onInspectLesion,
  lesionSelectionNotice,
  sourceSlice = false,
  verifiedRun = false,
  predictionUrl = null,
}) {
  const verifiedMeasurements = verifiedRun || measurementState !== undefined
  const measurement = measurementState?.status === 'ready' ? measurementState.measurement : null
  const source = verifiedRun ? { icon: Database, label: 'Verified prediction' }
    : !verifiedMeasurements && liveResult?.source === 'live'
      ? { icon: Radio, label: `Live analysis · ${liveResult.scoredAt}`, detail: `${fmt(liveResult.result.inference_seconds, 1)} s inference` }
      : { icon: Database, label: 'Saved prediction' }
  const predictionDownload = verifiedRun ? predictionUrl
    : caseData.files?.pred ? `/cases/${caseData.files.pred}` : null
  const SourceIcon = source.icon
  const lesionFlagged = Number.isSafeInteger(measurement?.lesionVoxels) && measurement.lesionVoxels >= 0
    ? measurement.lesionVoxels > 0
    : typeof finding.lesionFlagged === 'boolean' ? finding.lesionFlagged : null
  const volumeCm3 = verifiedMeasurements ? measurement?.lesionMl : Number.isFinite(finding.volumeMm3) ? finding.volumeMm3 / 1000 : null
  const [studyNames] = useStudyNames()
  const studyLabel = studyDisplayName(caseId, studyNames)
  const pending = measurementState?.status === 'loading'
  const volume = value => Number.isFinite(value)
    ? <><span className="pw-num">{value > 0 && value < 0.01 ? '<0.01' : value.toFixed(2)}</span> {verifiedMeasurements ? 'mL' : 'cm³'}</>
    : <Unavailable>{pending ? 'Checking…' : 'Unavailable'}</Unavailable>

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

      <section className={`pw-finding-summary${lesionFlagged ? ' is-flagged' : ''}`} aria-label="Finding summary">
        <header>
          <span className="pw-finding-summary__dot" aria-hidden="true" />
          <strong>{lesionFlagged ? 'Lesion predicted' : lesionFlagged === false ? 'No lesion predicted' : pending ? 'Checking prediction' : 'Lesion status unavailable'}</strong>
          <small>Model proposal · review required</small>
        </header>
        <dl>
          <div><dt>Lesion volume</dt><dd>{volume(volumeCm3)}</dd></div>
          {verifiedMeasurements && <div><dt>Pancreas outline</dt><dd>{volume(measurement?.pancreasMl)}</dd></div>}
          {comparing && Number.isFinite(overlap?.lesion) && <div><dt>Lesion Dice</dt><dd className="pw-num">{overlap.lesion.toFixed(3)}</dd></div>}
          {comparing && Number.isFinite(overlap?.pancreas) && <div><dt>Pancreas Dice</dt><dd className="pw-num">{overlap.pancreas.toFixed(3)}</dd></div>}
        </dl>
      </section>

      <details className="pw-section" open>
        <summary>Measurements</summary>
        <LesionDimensions measurement={measurement} selectedId={selectedLesionId}
          onSelect={onSelectLesion} onInspect={onInspectLesion} selectionNotice={lesionSelectionNotice} sourceSlice={sourceSlice} />
        {(onSelectPancreas || onInspectPancreas) && <PancreasDimensions measurementState={measurementState}
          selected={selectedPancreas} onSelect={onSelectPancreas} onInspect={onInspectPancreas} sourceSlice={sourceSlice} />}
      </details>

      {insights && hasPrediction && <>
        <LesionCharacteristics insights={insights} />
        <VesselRelationship insights={insights} />
        <StructuredSummary insights={insights} studyLabel={studyLabel} />
      </>}

      <ul className="pw-structures" aria-label="Structures in this prediction">
        <li className="pw-structure">
          <span className="pw-swatch" style={{ background: REVIEW_COLORS.pred.pancreas }} aria-hidden="true" />
          <div className="pw-structure__main">
            <h3 id="finding-pancreas">Pancreas</h3>
            <small>Model outline</small>
          </div>
          {verifiedMeasurements && <dl className="pw-structure__metrics">
            <div><dt title="Predicted pancreas outline including lesion labels; whole-organ coverage remains unverified.">Outline volume</dt><dd>{volume(measurement?.pancreasMl)}</dd></div>
          </dl>}
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
            <h3 id="finding-lesion">{lesionFlagged ? 'Possible lesion' : 'Lesion'}</h3>
            <small>{lesionFlagged ? 'Model proposal' : lesionFlagged === false ? 'None predicted'
              : pending ? 'Checking prediction' : 'Lesion status unavailable'}</small>
          </div>
          {(lesionFlagged || verifiedMeasurements) && (
            <dl className="pw-structure__metrics">
              <div>
                <dt>{verifiedMeasurements ? 'Total volume' : 'Volume'}</dt>
                <dd>{volume(volumeCm3)}</dd>
              </div>
              {!verifiedMeasurements && <div>
                <dt title="Diameter of a sphere with the same volume. Not a measured width or length.">≈ Diameter</dt>
                <dd>{finding.diameterMm ? <><span className="pw-num">{finding.diameterMm}</span> mm</> : <Unavailable />}</dd>
              </div>}
            </dl>
          )}
          <div className="pw-structure__actions">
            {lesionFlagged && (
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
                <dd>{caseData.gt_has_lesion === false && lesionFlagged === false ? 'Absent in both' : fmt(overlap.lesion, 3) ? <span className="pw-num">{fmt(overlap.lesion, 3)}</span> : <Unavailable />}</dd>
              </div>
            </dl>
          </li>
        )}
      </ul>
      <details className="pw-disclosure pw-disclosure--quiet">
        <summary><Info size={14} aria-hidden="true" /> About these numbers</summary>
      <p className="pw-fine">
        {verifiedMeasurements
          ? 'Volumes measure the displayed prediction’s outlines. Pancreas includes lesion labels; lesion total combines all lesion labels. Whole-organ coverage and model accuracy remain unverified. Human review is required.'
          : lesionFlagged
          ? 'Lesion volume comes from the predicted mask; ≈ diameter is a same-volume sphere, not a measured width or length. Proposals for review, not a diagnosis.'
          : lesionFlagged === false ? 'The model did not predict a lesion. This does not establish that no lesion is present.'
            : 'The available prediction does not report lesion status.'}
        {comparing ? ' Dice is computed against this study’s reference annotation and shown only while comparing.' : ''}
        {' '}Click a structure in the viewer for details and related literature questions.
      </p>
      </details>
      {verifiedMeasurements && measurementState?.status !== 'ready' && <p className="pw-fine" role="status">
        {pending ? 'Checking CT and prediction geometry before showing outline volumes.' : measurementState?.reason || 'Verified outline volumes are unavailable.'}
      </p>}
      {verifiedMeasurements && measurement?.lesionVoxels === 0 && <p className="pw-fine">No lesion-labeled voxels were found. This does not establish that no lesion is present.</p>}

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
          {!verifiedMeasurements && liveResult?.source === 'live' && <div><dt>Inference</dt><dd>{source.detail}</dd></div>}
          {!verifiedMeasurements && <div>
            <dt title="Peak model output. Not a probability of disease.">Peak model score</dt>
            <dd>{fmt(finding.confidence) ?? <Unavailable />} <small>not a probability</small></dd>
          </div>}
          <div><dt>Voxel spacing</dt><dd>{Array.isArray(caseData.spacing_mm) ? `${caseData.spacing_mm.join(' × ')} mm` : <Unavailable />}</dd></div>
          <div><dt>Pancreas outline volume</dt><dd>{verifiedMeasurements ? volume(measurement?.pancreasMl) : <Unavailable>Not published in this package</Unavailable>}</dd></div>
          <div><dt>Display surfaces</dt><dd>{verifiedRun && !caseData.files?.mesh ? 'No surfaces packaged' : caseData.display_mesh_version === 'v3-difference-main-smoothing' ? 'v3, matched smoothing' : caseData.display_mesh_version ? 'v2, explicit normals' : 'v1, source-grid reconstruction'}</dd></div>
          <div><dt>Study type</dt><dd>{verifiedRun ? 'Verified prediction package' : isCurated ? 'Test-set example' : 'Prepared study'}</dd></div>
        </dl>
        <p className="pw-fine">Measurements derive from the original NIfTI masks, not the display surfaces.</p>
        {predictionDownload && (
          <a className="pw-btn pw-btn--ghost pw-btn--sm" href={predictionDownload} download={verifiedRun ? caseData.files?.pred || '' : true}>
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
