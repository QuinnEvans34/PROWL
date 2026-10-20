// @vitest-environment node
import { describe, it, expect, vi } from 'vitest'
import { NIFTI1 } from 'nifti-reader-js'
import { gzipSync, gunzipSync } from 'node:zlib'
import { measureMask, scanQuestion, loadScanMeasurements, measurementText } from '../src/lib/scanMeasurements.js'

function header() {
  return { dims: [3, 5, 5, 5, 1, 1, 1, 1], affine: [[2, 0, 0, -9], [0, 3, 0, 4], [0, 0, 4, 2], [0, 0, 0, 1]], xyzt_units: 2, sform_code: 1 }
}
function labels() { const a = new Uint8Array(125); a[31] = 1; a[32] = 1; a[62] = 2; return a }
const calculate = (h = header(), a = labels(), spacing) => measureMask(h, structuredClone(h), a, spacing)

describe('deterministic mask arithmetic and validity', () => {
  it('counts pancreas union and all lesion components using physical voxel volume', () => {
    const m = calculate(); expect(m.pancreasVoxels).toBe(3); expect(m.lesionVoxels).toBe(1)
    expect(m.pancreasMl).toBeCloseTo(0.072, 12); expect(m.lesionMl).toBeCloseTo(0.024, 12)
    expect(m.coverage).toContain('unverified')
  })
  it('uses determinant rather than spacing product for shear and reflection', () => {
    const h = header(); h.affine = [[-2, 1, 0, 15], [0, 3, 0, 0], [0, 0, 4, 0], [0, 0, 0, 1]]
    expect(calculate(h).pancreasMl).toBeCloseTo(0.072, 12)
  })
  it('rotated anisotropic geometry preserves volume', () => {
    const h = header(); const r = Math.PI / 7
    h.affine = [[2*Math.cos(r), -3*Math.sin(r), 0, 1], [2*Math.sin(r), 3*Math.cos(r), 0, 2], [0,0,4,3],[0,0,0,1]]
    expect(Math.abs(calculate(h).pancreasMl / 0.072 - 1)).toBeLessThan(1e-9)
  })
  it('refuses mismatched CT transforms', () => {
    const ct = header(); ct.affine[0][3] += 1
    expect(() => measureMask(ct, header(), labels())).toThrow(/grids/)
  })
  it.each(['empty', 'all-lesion', 'edge', 'fraction', 'short', 'NaN'])('rejects %s masks', kind => {
    let a = Array.from(labels())
    if (kind === 'empty') a.fill(0)
    if (kind === 'all-lesion') a = a.map(v => v ? 2 : 0)
    if (kind === 'edge') a[0] = 1
    if (kind === 'fraction') a[31] = 0.5
    if (kind === 'short') a.pop()
    if (kind === 'NaN') a[31] = NaN
    expect(() => calculate(header(), a)).toThrow()
  })
  it.each(['singular', '4d', 'units', 'missing-transform', 'nonfinite'])('rejects %s geometry', kind => {
    const h = header()
    if (kind === 'singular') h.affine[0][0] = 0
    if (kind === '4d') h.dims[0] = 4
    if (kind === 'units') h.xyzt_units = 1
    if (kind === 'missing-transform') h.sform_code = 0
    if (kind === 'nonfinite') h.affine[0][0] = NaN
    expect(() => calculate(h)).toThrow()
  })
  it('only permits legacy unknown units with explicit matching millimeter declaration', () => {
    const h = header(); h.xyzt_units = 0
    expect(() => calculate(h)).toThrow(/units/)
    expect(() => calculate(h, labels(), [2, 3, 5])).toThrow(/units/)
    expect(calculate(h, labels(), [2, 3, 4]).unitsBasis).toContain('Legacy')
  })
  it('does not interpret empty lesion labels as absence of disease', () => {
    const a = labels(); a[62] = 0
    expect(measurementText(calculate(header(), a), 'lesion')).toContain('does not establish')
  })
  it('does not round tiny volumes to zero', () => {
    const h = header(); h.affine[0][0] = 0.1
    expect(measurementText(calculate(h), 'lesion')).toContain('less than 0.01')
  })
})

it.each(['how big is this pancreas?', 'What is the volume of my pancreas?', 'What is the size of the pancreas in this scan?'])('routes %s', q => expect(scanQuestion(q)).toBe('pancreas'))
it.each(['How large is this pancreas and is it cancer?', 'What is the size of this pancreas head?', 'Is this lesion malignant?', 'Compare my pancreas to average'])('does not discard qualifiers in %s', q => expect(scanQuestion(q)).toBe('unsupported'))
it('keeps general literature separate', () => expect(scanQuestion('What is the average pancreas volume?')).toBe(null))

function nifti({ invalidLabel = false, slope = 0 } = {}) {
  const h = new NIFTI1(); Object.assign(h, header(), { littleEndian: true, datatypeCode: 4, numBitsPerVoxel: 16, vox_offset: 352, scl_slope: slope, scl_inter: 0, magic: 'n+1' })
  const b = new Uint8Array(352 + 250); b.set(new Uint8Array(h.toArrayBuffer()))
  const v = new DataView(b.buffer); const a = labels()
  for (let i = 0; i < a.length; i++) v.setInt16(352 + 2*i, invalidLabel && i === 31 ? 256 : a[i], true)
  return gzipSync(b)
}
const context = { available: true, source: 'saved', key: 'demo:1', caseId: 'PanTS_00000001', files: { ct: 'PanTS_00000001/ct.nii.gz', pred: 'PanTS_00000001/pred.nii.gz' } }
it('decodes gzip NIfTI end to end, hashes files, and only reads the selected CT/pred', async () => {
  const fetcher = vi.fn(async () => new Response(nifti()))
  vi.stubGlobal('fetch', fetcher)
  try {
    const m = await loadScanMeasurements(context, new AbortController().signal)
    expect(m.pancreasMl).toBe(0.072); expect(m.contextKey).toBe(context.key)
    expect(m.predictionSha256).toMatch(/^[a-f0-9]{64}$/)
    expect(fetcher.mock.calls.map(c => c[0])).toEqual(['/cases/PanTS_00000001/ct.nii.gz', '/cases/PanTS_00000001/pred.nii.gz'])
  } finally { vi.unstubAllGlobals() }
})
it.each([{ invalidLabel: true }, { slope: 2 }])('rejects invalid decoded labels/scaling %j', async options => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(nifti(options))))
  try { await expect(loadScanMeasurements(context)).rejects.toThrow() } finally { vi.unstubAllGlobals() }
})
it.each([{ available: false }, { source: 'live' }, { files: { ct: '../ct.nii.gz', pred: 'x' } }])('rejects unbound inputs before any fetch: %j', async change => {
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher)
  try { await expect(loadScanMeasurements({ ...context, ...change })).rejects.toThrow(); expect(fetcher).not.toHaveBeenCalled() } finally { vi.unstubAllGlobals() }
})
it('aborts asset reads without emitting a measurement', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(nifti())))
  const c = new AbortController(); c.abort()
  try { await expect(loadScanMeasurements(context, c.signal)).rejects.toThrow() } finally { vi.unstubAllGlobals() }
})

it('gzip transport and HTTP-decoded NIfTI yield the same content identity', async () => {
  let compressed = true
  vi.stubGlobal('fetch', vi.fn(async () => new Response(compressed ? nifti() : gunzipSync(nifti()))))
  try {
    const a = await loadScanMeasurements(context); compressed = false
    const b = await loadScanMeasurements(context)
    expect(a.predictionSha256).toBe(b.predictionSha256)
    expect(a.ctSha256).toBe(b.ctSha256)
  } finally { vi.unstubAllGlobals() }
})
