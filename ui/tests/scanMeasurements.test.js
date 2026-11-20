// @vitest-environment node
import { describe, it, expect, vi } from 'vitest'
import { NIFTI1 } from 'nifti-reader-js'
import { gzipSync, gunzipSync } from 'node:zlib'
import { measureMask, scanQuestion, loadScanMeasurements, measurementText } from '../src/lib/scanMeasurements.js'
import { lesionComponentAtWorld } from '../src/lib/lesionDimensions.js'

function header() {
  return { dims: [3, 5, 5, 5, 1, 1, 1, 1], affine: [[2, 0, 0, -9], [0, 3, 0, 4], [0, 0, 4, 2], [0, 0, 0, 1]], xyzt_units: 2, sform_code: 1 }
}
function labels() { const a = new Uint8Array(125); a[31] = 1; a[32] = 1; a[62] = 2; return a }
const calculate = (h = header(), a = labels(), spacing) => measureMask(h, structuredClone(h), a, spacing)

describe('slice calipers derived from the verified prediction', () => {
  it('separates face-connected lesions, picks the largest slice and measures rotated anisotropic voxels', () => {
    const h = { ...header(), dims: [3, 8, 8, 8, 1, 1, 1, 1],
      affine: [[0, -3, 0, -9], [2, 0, 0, 4], [0, 0, 4, 2], [0, 0, 0, 1]] }
    const a = new Uint8Array(8 ** 3)
    const set = (x, y, z, label = 2) => { a[x + 8 * y + 64 * z] = label }
    for (let y = 2; y <= 4; y++) for (let x = 2; x <= 5; x++) set(x, y, 3)
    set(3, 3, 4)
    set(6, 5, 3) // Diagonally adjacent only; do not merge it.
    set(1, 1, 1, 1)
    const m = calculate(h, a)
    const [first, second] = m.lesionDimensions.components
    expect([first.voxelCount, second.voxelCount]).toEqual([13, 1])
    expect(first.volumeMl + second.volumeMl).toBeCloseTo(m.lesionMl, 12)
    expect(first.superiorInferiorMm).toBe(8)
    expect(first.calipers).toEqual({
      nativeSlice: 3, plane: 'axial', anchorVoxel: [3, 3, 3], anchorWorldMm: [-18, 10, 14],
      axes: [
        { lengthMm: 8, voxelEndpoints: [[1.5, 3, 3], [5.5, 3, 3]], worldEndpointsMm: [[-18, 7, 14], [-18, 15, 14]] },
        { lengthMm: 9, voxelEndpoints: [[3, 1.5, 3], [3, 4.5, 3]], worldEndpointsMm: [[-13.5, 10, 14], [-22.5, 10, 14]] },
      ],
    })
    expect(lesionComponentAtWorld(m, [-18, 10, 14])).toBe(first)
    expect(lesionComponentAtWorld(m, [-24, 16, 14])).toBe(second)
    expect(lesionComponentAtWorld(m, [-13.5, 10, 14])).toBe(first) // On the outline's exact face.
    expect(lesionComponentAtWorld(m, [-22.5, 15, 14])).toBeNull() // Edge shared by separate components.
    expect(lesionComponentAtWorld(m, [-13.49, 10, 14])).toBeNull() // Background, no snapping.
    expect(lesionComponentAtWorld(m, [-99, 10, 14])).toBeNull()
    expect(lesionComponentAtWorld(m, [NaN, 10, 14])).toBeNull()
    expect(lesionComponentAtWorld(structuredClone(m), first.focusWorldMm)).toBeNull()
  })

  it('keeps both calipers inside a concave outline by stopping at the first gap', () => {
    const a = new Uint8Array(125)
    a[31] = 1
    for (let y = 1; y <= 3; y++) for (let x = 1; x <= 3; x++) {
      if (x !== 2 || y !== 2) a[x + 5 * y + 50] = 2
    }
    const m = calculate(header(), a)
    const [{ calipers }] = m.lesionDimensions.components
    expect(calipers.anchorVoxel).toEqual([1, 2, 2])
    expect(calipers.axes.map(axis => axis.lengthMm)).toEqual([2, 9])
    expect(calipers.axes[0].voxelEndpoints).toEqual([[0.5, 2, 2], [1.5, 2, 2]])
    expect(lesionComponentAtWorld(m, [-5, 10, 10])).toBeNull() // Hole inside the component's bounds.
  })

  it('retains volume and head-to-foot extent but does not claim perpendicular calipers on a sheared slice', () => {
    const h = header()
    h.affine[0][1] = 1
    h.affine[2][0] = 0.5
    const m = calculate(h)
    expect(m.lesionDimensions.components[0]).toMatchObject({
      calipers: null, focusWorldMm: [-3, 10, 11], superiorInferiorMm: 4.5, volumeMl: m.lesionMl,
    })
    expect(lesionComponentAtWorld(m, m.lesionDimensions.components[0].focusWorldMm)).toBe(m.lesionDimensions.components[0])
  })

  it.each([
    ['sagittal', [[0, 0, -4, 10], [2, 0, 0, 1], [0, 3, 0, -2], [0, 0, 0, 1]]],
    ['coronal', [[2, 0, 0, 1], [0, 0, -4, 10], [0, 3, 0, -2], [0, 0, 0, 1]]],
    ['axial', [[Math.SQRT2, -Math.SQRT2, 0, 1], [Math.SQRT2, Math.SQRT2, 0, 10], [0, 0, 4, -2], [0, 0, 0, 1]]],
    [null, [[2, 0, 1, 1], [0, 3, 0, 10], [0, 0, 4, -2], [0, 0, 0, 1]]], // Skewed k axis.
    [null, [[2, 0, 0, 1], [0, Math.SQRT2, -Math.SQRT2, 10], [0, Math.SQRT2, Math.SQRT2, -2], [0, 0, 0, 1]]], // Oblique plane.
  ])('binds the native measurement to viewer plane %s only when exact', (plane, affine) => {
    const m = calculate({ ...header(), affine })
    const [component] = m.lesionDimensions.components
    expect(component.calipers.plane).toBe(plane)
    expect(lesionComponentAtWorld(m, component.focusWorldMm)).toBe(component)
  })
})

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
  it('retains per-label edge counts, counting corners once, without allowing volume', () => {
    const h = header(); const a = labels(); a[0] = 1; a[124] = 2
    let failure
    try { measureMask(h, h, a, undefined, { roi: [[0,0,0],[5,5,5]] }) } catch (e) { failure = e }
    expect(failure.code).toBe('mask_coverage')
    const d = failure.coverageDiagnostics
    expect(d.cropContact).toEqual({ pancreasLabel: 1, lesionLabel: 1 })
    expect(d.imageContact).toEqual(d.cropContact)
    expect(d.cropFaces).toHaveLength(6)
    expect(d.cropFaces.find(f => f.axis === 2 && f.side === 'high').lesionLabel).toBe(1)
    expect(failure.pancreasMl).toBeUndefined(); expect(failure.lesionMl).toBeUndefined()
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
it.each(['How big is it?', 'How large is it?'])('resolves the saved-scan follow-up %s with a bounded referent', q => {
  expect(scanQuestion(q)).toBe('pancreas')
  expect(scanQuestion(q, { subject: 'lesion' })).toBe('lesion')
  expect(scanQuestion(q, { subject: 'unknown' })).toBe('unsupported')
})
it.each(['How big is it and is it cancer?', 'How big is it without the lesion?'])('does not discard qualifiers in a bare follow-up: %s', q => expect(scanQuestion(q)).toBeNull())
it.each(['How large is this pancreas and is it cancer?', 'What is the size of this pancreas head?', 'Is this lesion malignant?'])('does not discard qualifiers in %s', q => expect(scanQuestion(q)).toBe('unsupported'))
it.each(['What is the average pancreas volume?', 'What is the pancreas volume in adults?'])('keeps literature separate for %s', q => expect(scanQuestion(q)).toBe(null))
it('accepts direct lesion volume wording in scan context', () => expect(scanQuestion('What is the lesion volume on this scan?')).toBe('lesion'))
it('keeps compound volume requests outside the measurement grammar', () => expect(scanQuestion('What is the lesion volume on this scan and is it cancer?')).toBe('unsupported'))

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

 it.each(['Is this pancreas big or small?', 'Is this pancreas larger than average?', 'Compare my pancreas to average', 'How does the size of this pancreas compare to the average?'])('routes a bounded scan comparison: %s', q => expect(scanQuestion(q)).toBe('pancreas_comparison'))
it.each(['Is this pancreas big or small and is it cancer?', 'Is this pancreas not larger than average?', 'Is this lesion larger than average?'])('does not silently drop comparison qualifiers: %s', q => expect(scanQuestion(q)).toBe('unsupported'))
it('compares a mask with a study mean without declaring clinical normality', () => {
  const text = measurementText({pancreasMl: 100}, 'pancreas_comparison')
  expect(text).toContain('17.4 mL (21.1%) above')
  expect(text).toContain('14 participants')
  expect(text).toContain('MRI')
  expect(text).toContain('not an individual normal range')
  expect(text).toContain('coverage and model accuracy are unverified')
})
