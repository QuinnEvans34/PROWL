import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { validateSavedPrediction, loadSavedPrediction } from '../src/lib/savedPrediction.js'
import { verifyNativeVolumes } from '../src/lib/nativeGeometry.js'
import SavedPredictionView from '../src/components/SavedPredictionView.jsx'
vi.mock('../src/components/NiivueViewer.jsx', () => ({ default: ({ caseData }) => <div>Rendered {caseData.case_id}</div> }))
const hash = 'a'.repeat(64)
const geometry = { shape: [2, 3, 4], affine: [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], units: 'mm' }
const fixture = () => ({ schema_version: 'saved-prediction-view-v1', case_id: 'case_A', status: 'completed', prediction_mode: 'autonomous', reference_inputs_used: false,
  files: { ct: { uri: 'ct.nii.gz', bytes: 10, content_sha256: hash }, pred: { uri: 'prediction.nii.gz', bytes: 10, content_sha256: hash } }, geometry,
  model_sha256: { localizer: hash, segmenter: hash }, result_sha256: hash, inference_evidence_sha256: hash, ct_window: [-100, 300], warnings: [] })
describe('saved prediction admission', () => {
  it('accepts complete identity', () => expect(validateSavedPrediction(fixture()).case_id).toBe('case_A'))
  for (const [name, change] of [
    ['failed', d => d.status = 'failed'], ['missing', d => delete d.files.pred],
    ['traversal', d => d.files.ct.uri = '../ct.nii.gz'], ['external', d => d.files.ct.uri = 'https://example.org/ct.nii.gz'],
    ['model identity', d => d.model_sha256.segmenter = 'bad'], ['reference path', d => d.reference_inputs_used = true],
    ['units', d => d.geometry = { ...geometry, units: 'unknown' }],
  ]) it(`refuses ${name}`, () => { const data = fixture(); change(data); expect(() => validateSavedPrediction(data)).toThrow() })
  it('refuses missing package', async () => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 })); await expect(loadSavedPrediction('/saved')).rejects.toThrow('unavailable') })
  it('refuses changed payload', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(fixture()))).mockResolvedValueOnce(new Response(new ArrayBuffer(10))))
    vi.stubGlobal('crypto', { subtle: { digest: async () => new Uint8Array(32).buffer } })
    await expect(loadSavedPrediction('/saved')).rejects.toThrow('identity mismatch')
  })
  it('requires both volumes and matching native affine/units', () => {
    const v = () => ({ hdr: { dims: [3,2,3,4], affine: structuredClone(geometry.affine), xyzt_units: 2 } })
    expect(() => verifyNativeVolumes([v(),v()], geometry)).not.toThrow()
    expect(() => verifyNativeVolumes([v()], geometry)).toThrow()
    const moved = v(); moved.hdr.affine[0][3] = 5
    expect(() => verifyNativeVolumes([v(),moved], geometry)).toThrow()
    const units = v(); units.hdr.xyzt_units = 0
    expect(() => verifyNativeVolumes([v(),units], geometry)).toThrow()
  })
  it('ignores a late package response after switching cases', async () => {
    let finishA
    vi.stubGlobal('fetch', vi.fn(url => url.startsWith('/a/') ? new Promise(resolve => { finishA = resolve }) : Promise.resolve({ ok: false, status: 404 })))
    const { rerender } = render(<SavedPredictionView base="/a" />)
    expect(screen.getByRole('status').textContent).toContain('Loading')
    rerender(<SavedPredictionView base="/b" />)
    await screen.findByRole('alert')
    finishA({ ok: false, status: 500 })
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('404'))
    expect(screen.queryByText(/Rendered/)).toBeNull()
  })
})
