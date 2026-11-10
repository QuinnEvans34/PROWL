import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { act, render, renderHook, screen, waitFor } from '@testing-library/react'
import { MeasurementReadout, measurementState, usePredictionMeasurements } from '../src/components/PredictionMeasurements.jsx'

const context = { key: 'PanTS_00000001:saved', available: true, source: 'saved', caseId: 'PanTS_00000001',
  files: { ct: 'PanTS_00000001/ct.nii.gz', pred: 'PanTS_00000001/pred.nii.gz' }, spacingMm: [2, 3, 4] }
function measured(changes = {}) {
  return { schema: 'prepared-mask-volume-v1', contextKey: context.key, shape: [5, 5, 5], voxelMm3: 24,
    pancreasVoxels: 3000, lesionVoxels: 125, pancreasMl: 72, lesionMl: 3,
    ctSha256: 'a'.repeat(64), predictionSha256: 'b'.repeat(64),
    coverage: 'Whole-organ coverage unverified', unitsBasis: 'NIfTI millimeter units',
    hashBasis: 'Decoded NIfTI bytes', modelLineage: 'Prepared prediction', ...changes }
}

describe('workspace measurement lifetime', () => {
  it('loads the exact selected context once and can share a result across readouts', async () => {
    const load = vi.fn(async () => measured())
    const { result, rerender } = renderHook(({ value }) => usePredictionMeasurements(value, { load }), { initialProps: { value: context } })
    await waitFor(() => expect(result.current.status).toBe('ready'))
    expect(load).toHaveBeenCalledTimes(1)
    expect(load.mock.calls[0][0]).toEqual(context)
    rerender({ value: { ...context, files: { ...context.files } } })
    expect(load).toHaveBeenCalledTimes(1)
    render(<><MeasurementReadout state={result.current} /><MeasurementReadout state={result.current} compact /></>)
    expect(screen.getAllByText('72.00')).toHaveLength(2)
    expect(screen.getAllByText('3.00')).toHaveLength(2)
    expect(screen.getByLabelText('Prediction measurements')).toBeTruthy()
    expect(screen.getByLabelText('Image measurement overlay')).toBeTruthy()
    expect(screen.getByText(/Whole-organ coverage unverified/)).toBeTruthy()
  })

  it('withholds all volumes when geometry validation fails and never uses headline fallback numbers', async () => {
    const load = vi.fn(async () => { throw new Error('The CT and prediction grids do not match.') })
    const { result } = renderHook(() => usePredictionMeasurements({ ...context, pancreasMl: 100, lesionMl: 42 }, { load }))
    await waitFor(() => expect(result.current.status).toBe('unavailable'))
    render(<MeasurementReadout state={result.current} />)
    expect(screen.getAllByText('Unavailable')).toHaveLength(2)
    expect(screen.getByText('The CT and prediction grids do not match.')).toBeTruthy()
    expect(screen.queryByText('100.00')).toBeNull()
    expect(screen.queryByText('42.00')).toBeNull()
  })

  it('keeps the coverage guard and its diagnostics visible without exposing withheld numbers', async () => {
    const diagnostics = { cropContact: { pancreasLabel: 2, lesionLabel: 0 } }
    const error = Object.assign(new Error('The predicted outline touches the image boundary and may be cut off.'), { code: 'mask_coverage', coverageDiagnostics: diagnostics })
    const load = vi.fn(async () => { throw error })
    const { result } = renderHook(() => usePredictionMeasurements(context, { load }))
    await waitFor(() => expect(result.current.status).toBe('unavailable'))
    expect(result.current.coverageDiagnostics).toEqual(diagnostics)
    expect(result.current.measurement).toBeUndefined()
  })

  it('cancels the previous case and discards a late result even if the loader ignores abort', async () => {
    let resolveA
    const load = vi.fn().mockImplementationOnce(() => new Promise(resolve => { resolveA = resolve }))
      .mockResolvedValueOnce(measured({ contextKey: 'case-b', pancreasVoxels: 4000, pancreasMl: 96 }))
    const { result, rerender } = renderHook(({ value }) => usePredictionMeasurements(value, { load }), { initialProps: { value: context } })
    await waitFor(() => expect(load).toHaveBeenCalledTimes(1))
    const oldSignal = load.mock.calls[0][1]
    rerender({ value: { ...context, key: 'case-b', caseId: 'PanTS_00000002', files: { ct: 'PanTS_00000002/ct.nii.gz', pred: 'PanTS_00000002/pred.nii.gz' } } })
    expect(oldSignal.aborted).toBe(true)
    expect(result.current.status).toBe('loading')
    await waitFor(() => expect(result.current.measurement?.pancreasMl).toBe(96))
    await act(async () => resolveA(measured()))
    expect(result.current.measurement.pancreasMl).toBe(96)
  })

  it('masks completed values immediately when a prediction is hidden', async () => {
    const load = vi.fn(async () => measured())
    const { result, rerender } = renderHook(({ value }) => usePredictionMeasurements(value, { load }), { initialProps: { value: context } })
    await waitFor(() => expect(result.current.status).toBe('ready'))
    rerender({ value: { ...context, available: false } })
    expect(result.current.status).toBe('unavailable')
    expect(result.current.measurement).toBeUndefined()
    expect(load).toHaveBeenCalledTimes(1)
  })

  it('aborts outstanding work on unmount', async () => {
    const load = vi.fn(() => new Promise(() => {}))
    const { unmount } = renderHook(() => usePredictionMeasurements(context, { load }))
    await waitFor(() => expect(load).toHaveBeenCalledOnce())
    const signal = load.mock.calls[0][1]
    unmount()
    expect(signal.aborted).toBe(true)
  })

  it('rejects a result bound to a different prediction', async () => {
    const load = vi.fn(async () => measured({ contextKey: 'another-prediction' }))
    const { result } = renderHook(() => usePredictionMeasurements(context, { load }))
    await waitFor(() => expect(result.current.status).toBe('unavailable'))
    expect(result.current.reason).toContain('different prediction')
  })

  it('never fetches when there is no prediction to show', async () => {
    const load = vi.fn()
    const { result } = renderHook(() => usePredictionMeasurements({ ...context, available: false, files: { ct: context.files.ct } }, { load }))
    await waitFor(() => expect(result.current.status).toBe('unavailable'))
    expect(result.current.reason).toContain('No prediction mask')
    expect(load).not.toHaveBeenCalled()
  })
})

describe('measurement presentation', () => {
  it.each(['pancreasMl', 'lesionMl', 'ctSha256', 'predictionSha256', 'voxelMm3', 'pancreasVoxels', 'lesionVoxels'])(
    'does not turn missing %s into a numeric result', field => {
      const measurement = measured(); delete measurement[field]
      render(<MeasurementReadout state={{ status: 'ready', measurement }} />)
      expect(screen.getAllByText('Unavailable')).toHaveLength(2)
      expect(screen.queryByText('72.00')).toBeNull()
    })

  it('shows a valid zero lesion volume with the correct limitation', () => {
    const state = measurementState(measured({ lesionMl: 0, lesionVoxels: 0 }))
    expect(state.status).toBe('ready')
    render(<MeasurementReadout state={state} />)
    expect(screen.getByText('0.00')).toBeTruthy()
    expect(screen.getByText(/This does not establish that no lesion is present/)).toBeTruthy()
    expect(screen.queryByText(/confidence|diameter/i)).toBeNull()
  })

  it('does not round a tiny positive volume to zero', () => {
    render(<MeasurementReadout state={measurementState(measured({ lesionVoxels: 1, lesionMl: 0.001, voxelMm3: 1,
      pancreasVoxels: 72000 }))} />)
    expect(screen.getByText('<0.01')).toBeTruthy()
  })

  it('accepts preverified native measurements only for the expected CT and prediction hashes', async () => {
    const measurement = measured({ status: 'ready', schema: 'native-mask-volume-v1' })
    const expected = { ...context, source: 'native', ctSha256: measurement.ctSha256, predictionSha256: measurement.predictionSha256 }
    const load = vi.fn()
    const { result, rerender } = renderHook(({ value }) => usePredictionMeasurements(value, { measurement, load }), { initialProps: { value: expected } })
    await waitFor(() => expect(result.current.status).toBe('ready'))
    expect(load).not.toHaveBeenCalled()
    rerender({ value: { ...expected, predictionSha256: 'c'.repeat(64) } })
    await waitFor(() => expect(result.current.status).toBe('unavailable'))
    expect(result.current.reason).toContain('not bound')
    expect(result.current.measurement).toBeUndefined()
  })
})
