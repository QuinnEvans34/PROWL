import { describe, it, expect } from 'vitest'
import retained from '../../configs/training-progress/lenovo-stunet-20261106.json'
import { validateTrainingProgress, acceptTrainingProgress, trainingProgressSummary } from '../src/lib/trainingProgress.js'
const fixture = () => structuredClone(retained)

describe('completed validation admission', () => {
  it('keeps every complete point and separates best/latest without interpolating scores', () => {
    const d = fixture(); d.validations[1].lesion_dice = 0.5
    const s = trainingProgressSummary(validateTrainingProgress(d), Date.parse(d.observed_at))
    expect(s.best.step).toBe(4000); expect(s.latest.step).toBe(6000)
    expect(s.latest.lesion_dice).toBe(retained.validations[2].lesion_dice)
  })
  it('admits partial validation as progress, never as a score', () => {
    const d = fixture(); d.run.step = 8000; d.run.phase = 'validating'
    d.run.validation = { step: 8000, completed_cases: 51, total_cases: 70 }
    expect(trainingProgressSummary(validateTrainingProgress(d)).latest.step).toBe(6000)
    d.validations.push({ ...d.validations[2], step: 8000, completed_cases: 51 })
    expect(() => validateTrainingProgress(d)).toThrow()
  })
  it.each([
    d => { d.validations[0].lesion_dice = NaN },
    d => { d.validations[1].pancreas_dice = 1.1 },
    d => { d.validations[2].false_alarm_cases = 35 },
    d => { d.validations.splice(1, 1) },
    d => { d.cohort.positive_cases = 35 },
    d => { d.run.phase = 'completed' },
    d => { d.run.step = '6814' },
    d => { d.observed_at = 'not a timestamp' },
    d => { d.observed_at = '2026-02-30T00:00:00Z' },
    d => { d.patient_ids = ['not-for-this-export'] },
    d => { d.validations[0].case_paths = ['private'] },
    d => { d.run.scope = 'independent_test' },
  ])('rejects invalid scores, denominators, missing history or unsupported scope', mutate => {
    const d = fixture(); mutate(d); expect(() => validateTrainingProgress(d)).toThrow()
  })
  it('admits a just-started run without inventing a zero DICE', () => {
    const d = fixture(); d.run.step = 18; d.validations = []
    expect(trainingProgressSummary(validateTrainingProgress(d)).latest).toBeNull()
  })
})

describe('export freshness and immutability', () => {
  it('uses observation time rather than the time a file is read', () => {
    const d = fixture(), t = Date.parse(d.observed_at)
    expect(trainingProgressSummary(d, t + 16 * 60000).freshness).toBe('older')
    expect(trainingProgressSummary(d, t - 6 * 60000).freshness).toBe('clock_ahead')
  })
  it('rejects older exports, changed receipts and rewrites of completed results', () => {
    const old = fixture()
    for (const change of [d => { d.observed_at = '2026-11-06T00:00:00Z' }, d => { d.source.receipt_sha256 = 'a'.repeat(64) }, d => { d.validations[0].lesion_dice = 0.9 }]) {
      const d = fixture(); change(d); expect(() => acceptTrainingProgress(old, d)).toThrow()
    }
  })
  it('accepts advancing same-run progress while preserving completed points', () => {
    const old = fixture(), next = fixture()
    next.run.step++; next.run.elapsed_seconds++; next.observed_at = '2026-11-07T19:00:00Z'
    expect(acceptTrainingProgress(old, next)).toBe(next)
  })
})
