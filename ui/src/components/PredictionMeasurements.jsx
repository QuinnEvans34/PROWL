import React, { useEffect, useMemo, useState } from 'react'
import { CircleCheck, Info, LoaderCircle, TriangleAlert } from 'lucide-react'
import { loadScanMeasurements, MEASUREMENT_POLICY } from '../lib/scanMeasurements.js'
import './PredictionMeasurements.css'

const EMPTY_REASON = 'Show a prediction to calculate volumes from its outline.'
const finite = value => typeof value === 'number' && Number.isFinite(value)
const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value)

// Only measurement records produced by the mask arithmetic are accepted. In
// particular, a legacy manifest's volume/diameter/score is never a fallback.
function completeMeasurement(measurement) {
  if (![MEASUREMENT_POLICY, 'native-mask-volume-v1'].includes(measurement?.schema)) return false
  const { pancreasMl, lesionMl, pancreasVoxels, lesionVoxels, voxelMm3 } = measurement
  if (!finite(pancreasMl) || pancreasMl <= 0 || !finite(lesionMl) || lesionMl < 0 || lesionMl > pancreasMl
    || !Number.isSafeInteger(pancreasVoxels) || !Number.isSafeInteger(lesionVoxels)
    || lesionVoxels < 0 || pancreasVoxels <= lesionVoxels || !finite(voxelMm3) || voxelMm3 <= 0
    || !digest(measurement.ctSha256) || !digest(measurement.predictionSha256)) return false
  return [[pancreasMl, pancreasVoxels], [lesionMl, lesionVoxels]].every(([volume, count]) =>
    Math.abs(volume - count * voxelMm3 / 1000) <= Math.max(1e-10, volume * 1e-8))
}

/** Native callers may reuse the object returned by loadSavedPrediction. */
export function measurementState(measurement, identity = '') {
  if (measurement?.status === 'unavailable') return { status: 'unavailable', identity,
    reason: measurement.reason || 'Outline coverage could not be verified. Volumes are withheld.',
    coverageDiagnostics: measurement.coverageDiagnostics, measurement }
  if (!completeMeasurement(measurement)) return { status: 'unavailable', identity,
    reason: 'A complete, verified mask measurement is unavailable.' }
  return { status: 'ready', identity, measurement }
}

function contextIdentity(context) {
  return JSON.stringify([context?.identity ?? context?.key ?? '', context?.caseId ?? '',
    context?.source ?? '', Boolean(context?.available), context?.files?.ct ?? '', context?.files?.pred ?? '',
    context?.spacingMm ?? null, context?.ctSha256 ?? '', context?.predictionSha256 ?? ''])
}

/**
 * Load once in the workspace, then share its state with strip and image overlay.
 * The identity includes file paths and availability, so a study switch or hidden
 * prediction immediately masks old values, before the next effect has run.
 * Native reuse requires the expected CT and prediction hashes from that package.
 */
export function usePredictionMeasurements(context, { measurement, load = loadScanMeasurements } = {}) {
  const identity = contextIdentity(context)
  const bound = useMemo(() => ({ ...context, key: context?.key ?? context?.identity ?? identity }), [identity])
  const [state, setState] = useState({ status: 'loading', identity: '' })

  useEffect(() => {
    const control = new AbortController()
    let active = true
    if (!bound.available) {
      setState({ status: 'unavailable', identity, reason: bound.files?.pred ? EMPTY_REASON : 'No prediction mask is available for this study.' })
      return () => { active = false; control.abort() }
    }
    if (measurement !== undefined) {
      const matched = digest(bound.ctSha256) && digest(bound.predictionSha256)
        && measurement?.ctSha256 === bound.ctSha256 && measurement?.predictionSha256 === bound.predictionSha256
      setState(matched ? measurementState(measurement, identity) : { status: 'unavailable', identity,
        reason: 'The measurement is not bound to the displayed CT and prediction.' })
      return () => { active = false; control.abort() }
    }
    setState({ status: 'loading', identity })
    Promise.resolve().then(() => load(bound, control.signal)).then(result => {
      if (!active || control.signal.aborted) return
      if (result?.contextKey !== bound.key) {
        setState({ status: 'unavailable', identity, reason: 'The measurement belongs to a different prediction.' })
        return
      }
      setState(measurementState(result, identity))
    }).catch(error => {
      if (!active || control.signal.aborted) return
      setState({ status: 'unavailable', identity,
        reason: error.message || 'The displayed prediction could not be measured.', coverageDiagnostics: error.coverageDiagnostics })
    })
    return () => { active = false; control.abort() }
  }, [bound, identity, measurement, load])

  if (state.identity === identity) return state
  return bound.available ? { status: 'loading', identity } : { status: 'unavailable', identity,
    reason: bound.files?.pred ? EMPTY_REASON : 'No prediction mask is available for this study.' }
}

function volume(value) {
  if (value === 0) return '0.00'
  return value < 0.01 ? '<0.01' : value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function Evidence({ measurement }) {
  return <details className="pw-measurements__evidence">
    <summary><Info size={12} aria-hidden="true" /> Measurement evidence</summary>
    <div>
      <p>Volumes are calculated from the displayed prediction’s labeled voxels and physical voxel volume. Pancreas includes pancreas and lesion labels; lesion total combines all lesion labels.</p>
      <p>{measurement.coverage || 'Whole-organ coverage unverified'}. Model outlines require human review.</p>
      {measurement.assisted && <p>A provided pancreas outline defined the inference region. These volumes measure the model output.</p>}
      {measurement.lesionVoxels === 0 && <p>No lesion-labeled voxels were found. This does not establish that no lesion is present.</p>}
      <p>{measurement.unitsBasis}. Voxel volume: {measurement.voxelMm3} mm³.</p>
      <p>{measurement.hashBasis}. {measurement.modelLineage}.</p>
      <dl>
        <div><dt>CT SHA-256</dt><dd>{measurement.ctSha256}</dd></div>
        <div><dt>Prediction SHA-256</dt><dd>{measurement.predictionSha256}</dd></div>
      </dl>
    </div>
  </details>
}

export function MeasurementReadout({ state: input, compact = false, showEvidence = !compact, className = '' }) {
  const state = input?.status === 'ready' ? measurementState(input.measurement, input.identity) : input
  const ready = state?.status === 'ready'
  const loading = state?.status === 'loading'
  const measurement = ready ? state.measurement : null
  return <section className={`pw-measurements${compact ? ' pw-measurements--compact' : ''} ${className}`}
    aria-label={compact ? 'Image measurement overlay' : 'Prediction measurements'} aria-live={compact ? undefined : 'polite'} aria-busy={loading}>
    <div className="pw-measurements__values">
      <div className="pw-measurements__value" title="Volume of the predicted pancreas outline, including lesion labels; whole-organ coverage remains unverified.">
        <span><i className="pw-measurements__dot pw-measurements__dot--pancreas" aria-hidden="true" />Pancreas outline</span>
        <strong>{ready ? <>{volume(measurement.pancreasMl)} <small>mL</small></> : <small>{loading ? 'Checking…' : 'Unavailable'}</small>}</strong>
      </div>
      <div className="pw-measurements__value" title="Combined volume of all lesion-labeled regions, not an individual diameter or diagnosis.">
        <span><i className="pw-measurements__dot pw-measurements__dot--lesion" aria-hidden="true" />Lesion total</span>
        <strong>{ready ? <>{volume(measurement.lesionMl)} <small>mL</small></> : <small>{loading ? 'Checking…' : 'Unavailable'}</small>}</strong>
      </div>
      <div className={`pw-measurements__status${ready ? ' is-ready' : ''}`}>
        {loading ? <LoaderCircle size={13} className="pw-measurements__spinner" aria-hidden="true" />
          : ready ? <CircleCheck size={13} aria-hidden="true" /> : <TriangleAlert size={13} aria-hidden="true" />}
        <span>{loading ? 'Checking mask geometry' : ready ? 'Geometry checked' : 'Measurements unavailable'}
          {ready && <small>{measurement.schema === 'native-mask-volume-v1' ? 'Verified native package' : 'Prepared prediction'} · coverage unverified</small>}
        </span>
      </div>
    </div>
    {!ready && !loading && <p className="pw-measurements__reason">{state?.reason || 'No verified measurement is available.'}</p>}
    {ready && !compact && <p className="pw-measurements__note">Predicted outline volumes · Human review required{measurement.lesionVoxels === 0 ? ' · No lesion labels; absence of disease is not established' : ''}</p>}
    {ready && showEvidence && <Evidence measurement={measurement} />}
  </section>
}

export default function PredictionMeasurements({ context, measurement, compact = false, onMeasurementChange, ...props }) {
  const state = usePredictionMeasurements(context, { measurement })
  useEffect(() => { onMeasurementChange?.(state) }, [state, onMeasurementChange])
  return <MeasurementReadout {...props} state={state} compact={compact} />
}
