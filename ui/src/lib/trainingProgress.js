// Aggregate metadata only. This contract never treats an export as a live host check.
export const PROGRESS_SCHEMA = 'prowl-training-progress-v1'
export const MAX_PROGRESS_BYTES = 128 * 1024
const phases = new Set(['training', 'validating', 'paused', 'failed', 'completed'])
const fail = () => { throw new Error('Invalid training progress export') }
const integer = (n, min, max) => { if (!Number.isSafeInteger(n) || n < min || n > max) fail() }
const score = n => { if (typeof n !== 'number' || !Number.isFinite(n) || n < 0 || n > 1) fail() }
const text = (s, max = 200) => { if (typeof s !== 'string' || !s.trim() || s.length > max) fail() }
const keys = (value, allowed) => {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).some(k => !allowed.includes(k))) fail()
}

export function validateTrainingProgress(value) {
  if (!value || value.schema !== PROGRESS_SCHEMA) fail()
  keys(value, ['schema', 'observed_at', 'source', 'run', 'cohort', 'validations'])
  const { source, run, cohort, validations, observed_at: observed } = value
  if (typeof observed !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z$/.test(observed) || !Number.isFinite(Date.parse(observed))) fail()
  if (new Date(observed).toISOString().slice(0, 19) !== observed.slice(0, 19)) fail()
  keys(source, ['machine', 'kind', 'run_id', 'receipt_sha256', 'mlflow_run_id'])
  if (!source || !['Mac', 'Lenovo'].includes(source.machine) || source.kind !== 'saved_metadata_export') fail()
  text(source.run_id); text(source.mlflow_run_id)
  if (!/^[a-f0-9]{64}$/.test(source.receipt_sha256)) fail()
  if (!run || !phases.has(run.phase) || run.scope !== 'provided_pancreas_region_exploratory' || run.exposure !== 'pretraining_overlap_unresolved') fail()
  keys(run, ['title', 'scope', 'exposure', 'phase', 'step', 'target_steps', 'starting_step', 'validation_interval', 'elapsed_seconds', 'validation'])
  text(run.title)
  integer(run.target_steps, 1, 1000000); integer(run.step, 0, run.target_steps)
  integer(run.starting_step ?? 0, 0, 1000000 - run.target_steps)
  integer(run.validation_interval, 1, run.target_steps)
  if (run.target_steps % run.validation_interval !== 0 || typeof run.elapsed_seconds !== 'number' || !Number.isFinite(run.elapsed_seconds) || run.elapsed_seconds < 0) fail()
  if (!cohort) fail()
  keys(cohort, ['training_cases', 'development_cases', 'positive_cases', 'reference_empty_cases'])
  integer(cohort.training_cases, 1, 1000000); integer(cohort.development_cases, 1, 1000000)
  integer(cohort.positive_cases, 1, cohort.development_cases); integer(cohort.reference_empty_cases, 0, cohort.development_cases)
  if (cohort.positive_cases + cohort.reference_empty_cases !== cohort.development_cases) fail()
  if (!Array.isArray(validations) || validations.length > 100) fail()
  validations.forEach((point, index) => {
    keys(point, ['step', 'lesion_dice', 'pancreas_dice', 'detected_positive_cases', 'false_alarm_cases', 'completed_cases'])
    if (!point || point.step !== (index + 1) * run.validation_interval || point.step > run.step || point.completed_cases !== cohort.development_cases) fail()
    score(point.lesion_dice); score(point.pancreas_dice)
    integer(point.detected_positive_cases, 0, cohort.positive_cases)
    integer(point.false_alarm_cases, 0, cohort.reference_empty_cases)
  })
  const scheduled = Math.floor(run.step / run.validation_interval)
  if (run.phase === 'validating') {
    const pending = run.validation
    keys(pending, ['step', 'completed_cases', 'total_cases'])
    if (!pending || pending.step !== run.step || pending.total_cases !== cohort.development_cases || run.step === 0 || run.step % run.validation_interval !== 0) fail()
    integer(pending.completed_cases, 0, pending.total_cases)
    if (validations.length !== scheduled - 1) fail()
  } else {
    if (run.validation !== null) fail()
    if (['training', 'completed'].includes(run.phase) && validations.length !== scheduled) fail()
    if (['paused', 'failed'].includes(run.phase) && ![scheduled, Math.max(0, scheduled - 1)].includes(validations.length)) fail()
  }
  if (run.phase === 'completed' && run.step !== run.target_steps) fail()
  return value
}

export function acceptTrainingProgress(previous, candidate) {
  const next = validateTrainingProgress(candidate)
  if (!previous) return next
  if (Date.parse(next.observed_at) < Date.parse(previous.observed_at)) throw new Error('Older training export')
  if (next.source.run_id === previous.source.run_id) {
    const same = ['receipt_sha256', 'mlflow_run_id', 'machine'].every(k => next.source[k] === previous.source[k])
      && ['target_steps', 'validation_interval', 'scope', 'exposure'].every(k => next.run[k] === previous.run[k])
      && (next.run.starting_step ?? 0) === (previous.run.starting_step ?? 0)
      && Object.keys(previous.cohort).every(k => next.cohort[k] === previous.cohort[k])
    if (!same || next.run.step < previous.run.step || next.run.elapsed_seconds < previous.run.elapsed_seconds) throw new Error('Training identity or progress changed')
    if (previous.run.phase === 'completed' && next.run.phase !== 'completed') throw new Error('Completed run phase changed')
    for (const [index, old] of previous.validations.entries()) {
      const current = next.validations[index]
      if (!current || Object.keys(old).some(k => current[k] !== old[k])) throw new Error('Completed validation changed')
    }
    if (previous.run.validation && next.run.validation && previous.run.step === next.run.step && next.run.validation.completed_cases < previous.run.validation.completed_cases) throw new Error('Validation progress regressed')
  }
  return next
}

export function trainingProgressSummary(snapshot, now = Date.now()) {
  const latest = snapshot.validations.at(-1) || null
  const best = snapshot.validations.reduce((best, point) => !best || point.lesion_dice > best.lesion_dice ? point : best, null)
  const age = (now - Date.parse(snapshot.observed_at)) / 60000
  return { latest, best, ageMinutes: Math.max(0, Math.floor(age)), freshness: age < -5 ? 'clock_ahead' : age > 15 ? 'older' : 'recent' }
}
