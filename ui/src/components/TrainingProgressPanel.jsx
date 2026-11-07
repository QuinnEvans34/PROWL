import { useEffect, useRef, useState } from 'react'
import retained from '../../../configs/training-progress/lenovo-stunet-20261106.json'
import { acceptTrainingProgress, MAX_PROGRESS_BYTES, trainingProgressSummary, validateTrainingProgress } from '../lib/trainingProgress.js'
import './TrainingProgressPanel.css'

const clock = () => Date.now()
const number = n => n.toLocaleString()
const dice = n => n.toFixed(4)
const duration = n => `${Math.floor(n / 3600)}h ${Math.floor(n % 3600 / 60)}m`
const phaseLabels = { training: 'Training', validating: 'Validating', paused: 'Paused', failed: 'Failed', completed: 'Completed' }

function DiceChart({ points, target }) {
  const x = step => 40 + step / target * 520
  const y = score => 125 - score * 100
  return <figure className="pw-progress__chart">
    <svg viewBox="0 0 600 155" role="img" aria-label="Completed validation DICE curve, from zero to one">
      <title>Completed native validation scores; unmeasured steps have no points</title>
      {[0, 0.5, 1].map(tick => <g key={tick}>
        <line x1="40" x2="560" y1={y(tick)} y2={y(tick)} className="pw-progress__grid" />
        <text x="30" y={y(tick) + 4} textAnchor="end">{tick}</text>
      </g>)}
      {[0, target / 2, target].map(tick => <text key={tick} x={x(tick)} y="148" textAnchor="middle">{number(tick)}</text>)}
      {['lesion_dice', 'pancreas_dice'].map(metric => <g key={metric} className={`pw-progress__${metric}`}>
        <polyline points={points.map(p => `${x(p.step)},${y(p[metric])}`).join(' ')} fill="none" strokeWidth="2.5" />
        {points.map(p => <circle key={p.step} cx={x(p.step)} cy={y(p[metric])} r="4"><title>{`${number(p.step)} updates: ${dice(p[metric])}`}</title></circle>)}
      </g>)}
    </svg>
    <figcaption><span className="pw-progress__legend-lesion">Lesion</span><span className="pw-progress__legend-pancreas">Pancreas</span><span>Completed validations only · optimizer updates</span></figcaption>
  </figure>
}

export default function TrainingProgressPanel({ initialSnapshot = retained, now = clock }) {
  const [snapshot, setSnapshot] = useState(() => validateTrainingProgress(initialSnapshot))
  const current = useRef(snapshot)
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('Saved metadata export; this page does not connect to Lenovo.')
  const [error, setError] = useState('')
  const [observedNow, setObservedNow] = useState(now)
  const [refresh, setRefresh] = useState(0)
  useEffect(() => {
    let disposed = false, timer
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      const timeout = setTimeout(() => controller.abort(), 10000)
      try {
        const response = await fetch('/training-progress', { signal: controller.signal, cache: 'no-store' })
        if (!response.ok) throw new Error('Read failed')
        const body = await response.text()
        if (body.length > MAX_PROGRESS_BYTES) throw new Error('Export too large')
        const result = JSON.parse(body)
        if (!['local_snapshot', 'retained_snapshot'].includes(result.read_state)) throw new Error('Unknown source')
        const candidate = validateTrainingProgress(result.snapshot)
        if (disposed || controller.signal.aborted) return
        const admitted = acceptTrainingProgress(current.current, candidate)
        current.current = admitted
        setSnapshot(admitted)
        setNotice(typeof result.note === 'string' ? result.note.slice(0, 300) : 'Saved metadata export.')
        setError('')
      } catch {
        if (!disposed) setError('Could not read a newer export. Keeping the last verified results.')
      } finally {
        clearTimeout(timeout)
        if (!disposed) {
          setLoading(false); setObservedNow(now())
          timer = setTimeout(() => setRefresh(n => n + 1), 60000)
        }
      }
    }
    load()
    return () => { disposed = true; clearTimeout(timer); controller.abort() }
  }, [refresh, now])

  const { latest, best, ageMinutes, freshness } = trainingProgressSummary(snapshot, observedNow)
  const { run, cohort, source } = snapshot
  const freshnessLabel = freshness === 'clock_ahead' ? 'Source clock is ahead; freshness is uncertain'
    : freshness === 'older' ? 'Older saved observation' : 'Recent saved observation'
  return <section className="pw-progress" aria-labelledby="experiment-progress-heading">
    <header className="pw-progress__header"><div><p className="pw-eyebrow">Experiment results</p>
      <h2 id="experiment-progress-heading">{run.title}</h2><p>{source.machine} · {phaseLabels[run.phase]} at last observation</p>
    </div><button type="button" onClick={() => setRefresh(n => n + 1)} disabled={loading}>{loading ? 'Reading export…' : 'Refresh saved results'}</button></header>
    <div className="pw-progress__freshness" data-freshness={freshness}>
      <strong>{freshnessLabel}</strong><span>{freshness !== 'clock_ahead' && `${number(ageMinutes)} minutes old · `}<time dateTime={snapshot.observed_at}>{new Date(snapshot.observed_at).toLocaleString()}</time></span>
      <p>{notice}</p>{error && <p role="alert">{error}</p>}
    </div>
    <div className="pw-progress__updates"><strong>{number(run.step)} / {number(run.target_steps)} updates</strong><span>{duration(run.elapsed_seconds)} recorded session time</span></div>
    <progress value={run.step} max={run.target_steps} aria-label="Recorded optimizer updates" />
    {run.validation && <p className="pw-progress__pending" role="status">Validation at {number(run.validation.step)} updates: {run.validation.completed_cases}/{run.validation.total_cases} cases checked. DICE will appear when the complete report is ready.</p>}
    {latest ? <>
      <div className="pw-progress__metrics">
        <div><span>Latest lesion DICE</span><strong>{dice(latest.lesion_dice)}</strong><small>{number(latest.step)} updates</small></div>
        <div><span>Best lesion DICE so far</span><strong>{dice(best.lesion_dice)}</strong><small>{number(best.step)} updates</small></div>
        <div><span>Latest pancreas DICE</span><strong>{dice(latest.pancreas_dice)}</strong><small>{number(latest.step)} updates</small></div>
      </div>
      <DiceChart points={snapshot.validations} target={run.target_steps} />
      <p>At the latest completed validation: lesion overlap in <strong>{latest.detected_positive_cases}/{cohort.positive_cases}</strong> positive cases; predicted lesions in <strong>{latest.false_alarm_cases}/{cohort.reference_empty_cases}</strong> reference-empty cases.</p>
      <div className="pw-progress__table"><table><caption>Complete {cohort.development_cases}-case validation history</caption>
        <thead><tr><th>Updates</th><th>Lesion DICE</th><th>Pancreas DICE</th><th>Detected positive cases</th><th>Reference-empty false alarms</th></tr></thead>
        <tbody>{snapshot.validations.map(point => <tr key={point.step}><th scope="row">{number(point.step)}{point.step === best.step && <small>Best lesion score</small>}</th><td>{dice(point.lesion_dice)}</td><td>{dice(point.pancreas_dice)}</td><td>{point.detected_positive_cases}/{cohort.positive_cases}</td><td>{point.false_alarm_cases}/{cohort.reference_empty_cases}</td></tr>)}</tbody>
      </table></div>
    </> : <p className="pw-progress__pending">No complete validation yet. First DICE is scheduled at {number(run.validation_interval)} updates, after all {cohort.development_cases} cases have been checked.</p>}
    <p className="pw-progress__scope">Uses supplied pancreas regions. Development results; pretraining overlap remains unresolved. These scores do not establish autonomous or independent-test performance.</p>
    <details className="pw-progress__definitions"><summary>Metric definitions and result source</summary>
      <p>Lesion DICE averages the {cohort.positive_cases} positive cases. Pancreas DICE averages all {cohort.development_cases} cases. Detection means any lesion overlap; a false alarm means any predicted lesion on a reference-empty case. Best means the highest completed lesion DICE observed so far.</p>
      <p>Training cohort: {number(cohort.training_cases)} cases. Session time includes validation, checkpoints and I/O. It is not personal working time and is not added again to the accounting totals below.</p>
      <dl><dt>Execution</dt><dd>{source.run_id}</dd><dt>MLflow run</dt><dd>{source.mlflow_run_id}</dd><dt>Frozen receipt SHA256</dt><dd>{source.receipt_sha256}</dd></dl>
    </details>
  </section>
}
