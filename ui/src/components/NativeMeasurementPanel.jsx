import React, { useState } from 'react'
import { scanQuestion, measurementText } from '../lib/scanMeasurements.js'

// Mounted only for a verified v2 package; reload/case changes unmount this state.
export default function NativeMeasurementPanel({ measurement, live = false }) {
  const [question, setQuestion] = useState('')
  const [target, setTarget] = useState(null)
  return <section aria-label="Native scan measurements" style={{ maxWidth: 760, marginTop: 24 }}>
    <h2>Ask about this {live ? 'prediction' : 'saved prediction'}</h2>
    <p>Calculate outline volumes from the verified native-grid mask. Whole-pancreas coverage and disease interpretation remain unverified.</p>
    <form onSubmit={e => { e.preventDefault(); setTarget(scanQuestion(question) || 'unsupported') }}>
      <label htmlFor="native-question">Measurement question</label>
      <input id="native-question" value={question} maxLength={500} style={{ display: 'block', width: '100%', margin: '12px 0' }}
        onChange={e => { setQuestion(e.target.value); setTarget(null) }} placeholder="How big is this pancreas?" />
      <button disabled={!question.trim()}>Calculate volume</button>
    </form>
    <div aria-live="polite">
      {target && <>
        <h3>{measurement?.status === 'ready' && target !== 'unsupported' ? (live ? 'Predicted outline volume' : 'Saved outline volume') : 'Measurement unavailable'}</h3>
        <p>{target === 'unsupported' ? 'Ask for pancreas volume or total suspected-lesion volume. Individual dimensions, normal-range comparisons and disease interpretations are not supported.'
          : measurement?.status === 'ready' ? (live ? measurementText(measurement, target).replaceAll('saved prediction', 'prediction') : measurementText(measurement, target)) : measurement?.reason || 'No verified measurement is available.'}</p>
        {measurement?.status === 'ready' && target !== 'unsupported' && <>
          <p>{measurement.assisted ? 'Calculated from the model’s predicted labels. A provided pancreas outline defined the inference region; it was not substituted for the measured prediction.' : 'Calculated from labeled voxels; no AI estimate or reference annotation was used.'} The outline needs human review.</p>
          <details><summary>Measurement evidence</summary>
            <p>{measurement.coverage}. {measurement.modelLineage}.</p>
            <p>Volume = label count × voxel volume ({measurement.voxelMm3} mm³). Pancreas includes labels 1+2; lesion total includes label 2.</p>
            <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify({ policy: measurement.schema,
              ct: measurement.ctSha256, prediction: measurement.predictionSha256, models: measurement.modelSha256,
              result: measurement.resultSha256, inference: measurement.inferenceSha256, native_region: measurement.nativeRegion }, null, 2)}</pre>
          </details>
        </>}
      </>}
    </div>
  </section>
}
