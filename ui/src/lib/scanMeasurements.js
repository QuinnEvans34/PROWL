import { readHeader } from 'nifti-reader-js'

export const MEASUREMENT_POLICY = 'prepared-mask-volume-v1'
const LIMIT = 64 * 1024 * 1024
const EPS = 1e-4
const fail = (message) => { throw new Error(message) }
const close = (a, b) => Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= EPS

// Closed question grammar: qualifiers/clinical questions must never be silently dropped.
export function scanQuestion(question) {
  const q = question.toLowerCase().trim().replace(/[?.!]+$/, '').replace(/\s+/g, ' ')
  const match = q.match(/^(?:how (?:big|large) is|what is the (?:size|volume) of) (?:this|the|my) (pancreas|lesion)(?: (?:in|on) (?:this|the|my) (?:scan|image))?$/)
  if (match) return match[1]
  if (/\b(?:this|my|current)\b/.test(q) && /\b(?:scan|pancreas|lesion|tumou?r|image)\b/.test(q)) return 'unsupported'
  return null
}

function grid(header, maxVoxels = 16000000) {
  if (!header || header.dims?.[0] !== 3 || header.dims.slice(4).some(n => n > 1)) fail('Only a single 3D mask is supported.')
  const shape = header.dims.slice(1, 4)
  const n = shape.reduce((a, b) => a * b, 1)
  if (shape.some(n => !Number.isInteger(n) || n <= 0) || n > maxVoxels) fail('Invalid or oversized measurement grid.')
  const a = header.affine
  if (!(header.sform_code > 0 || header.qform_code > 0) || !Array.isArray(a) || a.length !== 4
    || a.some(r => !Array.isArray(r) || r.length !== 4 || r.some(v => !Number.isFinite(v)))
    || a[3].some((v, i) => !close(v, i === 3 ? 1 : 0))) fail('A valid spatial transform is required.')
  const det = a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
    - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
    + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
  if (!Number.isFinite(det) || Math.abs(det) < 1e-9) fail('The spatial transform is singular.')
  return { shape, n, affine: a, voxel: Math.abs(det) }
}

// Pure calculation. No reference mask, probability score, mesh or LLM is an input.
export function measureMask(ct, pred, labels, spacingMm, { maxVoxels = 16000000, roi = null } = {}) {
  const g = grid(pred, maxVoxels); const c = grid(ct, maxVoxels)
  if (g.shape.some((n, i) => n !== c.shape[i]) || g.affine.some((r, i) => r.some((v, j) => !close(v, c.affine[i][j])))) fail('The CT and prediction grids do not match.')
  const units = [ct, pred].map(h => h.xyzt_units & 7)
  let unitsBasis = 'NIfTI millimeter units'
  if (units.some(u => u !== 2)) {
    if (units.some(u => u !== 0 && u !== 2) || !Array.isArray(spacingMm) || spacingMm.length !== 3
      || spacingMm.some((s, j) => !(s > 0) || !close(s, Math.hypot(...g.affine.slice(0, 3).map(r => r[j]))))) fail('Millimeter units could not be verified.')
    unitsBasis = 'Legacy manifest spacing_mm; NIfTI units missing'
  }
  if (labels.length !== g.n) fail('The prediction payload is incomplete.')
  if (roi && (!Array.isArray(roi) || roi.length !== 2 || roi.some(r => !Array.isArray(r) || r.length !== 3 || r.some(n => !Number.isInteger(n)))
    || roi[0].some((n, i) => n < 0 || roi[1][i] <= n || roi[1][i] > g.shape[i]))) fail('Invalid native inference region.')
  let pancreas = 0; let lesion = 0; let boundary = false; let cropBoundary = false
  const coverageDiagnostics = { schema: 'mask-boundary-counts-v1',
    cropContact: { pancreasLabel: 0, lesionLabel: 0 }, imageContact: { pancreasLabel: 0, lesionLabel: 0 },
    cropFaces: [] }
  const faceCounts = Array.from({ length: 6 }, () => ({ pancreasLabel: 0, lesionLabel: 0 }))
  const [nx, ny, nz] = g.shape
  for (let i = 0; i < labels.length; i++) {
    const v = labels[i]
    if (v !== 0 && v !== 1 && v !== 2) fail('Unexpected prediction label.')
    if (!v) continue
    pancreas++; if (v === 2) lesion++
    const x = i % nx; const y = Math.floor(i / nx) % ny; const z = Math.floor(i / (nx * ny))
    const labelKey = v === 1 ? 'pancreasLabel' : 'lesionLabel'
    if (roi) {
      const xyz = [x, y, z]
      if (xyz.some((v, j) => v < roi[0][j] || v >= roi[1][j])) fail('Predicted labels fall outside the recorded inference region.')
      let contact = false
      for (let axis = 0; axis < 3; axis++) {
        if (xyz[axis] === roi[0][axis]) { faceCounts[axis * 2][labelKey]++; contact = true }
        if (xyz[axis] === roi[1][axis] - 1) { faceCounts[axis * 2 + 1][labelKey]++; contact = true }
      }
      if (contact) { cropBoundary = true; coverageDiagnostics.cropContact[labelKey]++ }
    }
    if (x === 0 || y === 0 || z === 0 || x === nx - 1 || y === ny - 1 || z === nz - 1) {
      boundary = true; coverageDiagnostics.imageContact[labelKey]++
    }
  }
  if (!pancreas || pancreas === lesion) fail('A usable pancreas outline is not available.')
  if (boundary || cropBoundary) {
    coverageDiagnostics.cropFaces = faceCounts.flatMap((counts, i) => counts.pancreasLabel || counts.lesionLabel
      ? [{ axis: Math.floor(i / 2), side: i % 2 ? 'high' : 'low', ...counts }] : [])
    const error = new Error(`The predicted outline touches the ${cropBoundary ? 'inference crop' : 'image'} boundary and may be cut off. Its size cannot be reported reliably.`)
    error.code = 'mask_coverage'; error.coverageDiagnostics = coverageDiagnostics; throw error
  }
  return { schema: MEASUREMENT_POLICY, shape: g.shape, affine: g.affine, voxelMm3: g.voxel,
    pancreasVoxels: pancreas, lesionVoxels: lesion, pancreasMl: pancreas * g.voxel / 1000,
    lesionMl: lesion * g.voxel / 1000, unitsBasis, coverage: 'Whole-organ coverage unverified',
    hashBasis: 'Decoded NIfTI bytes after gzip or HTTP decoding',
    modelLineage: 'Saved prepared prediction; producing checkpoint hash unavailable' }
}

export async function boundedStream(stream, signal, limit = LIMIT) {
  const reader = stream.getReader(); const chunks = []; let size = 0
  const abort = () => { void reader.cancel().catch(() => {}) }
  signal?.addEventListener('abort', abort, { once: true })
  try {
    while (true) {
      signal?.throwIfAborted()
      const { done, value } = await reader.read()
      if (done) break
      size += value.byteLength
      if (size > limit) fail('Measurement file exceeds the preview size limit.')
      chunks.push(value)
    }
    signal?.throwIfAborted()
    const bytes = new Uint8Array(size); let offset = 0
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength }
    return bytes.buffer
  } finally {
    signal?.removeEventListener('abort', abort)
    await reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}

export async function decodeMeasurementFile(raw, signal, { maxVoxels = 16000000, decodedLimit = LIMIT } = {}) {
  if (raw.byteLength > LIMIT) fail('Measurement file exceeds the preview size limit.')
  const prefix = new Uint8Array(raw, 0, Math.min(2, raw.byteLength))
  const data = prefix[0] === 31 && prefix[1] === 139
    ? await boundedStream(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip')), signal, decodedLimit) : raw
  signal?.throwIfAborted()
  if (data.byteLength > decodedLimit) fail('Decoded image exceeds the preview size limit.')
  const header = readHeader(data)
  const g = grid(header, maxVoxels)
  const bytes = header.numBitsPerVoxel / 8
  if (!Number.isInteger(header.vox_offset) || header.vox_offset < 352 || header.vox_offset + g.n * bytes > data.byteLength) fail('The image payload is incomplete.')
  return { header, data }
}

export function labelsFrom({ header: h, data }) {
  if (!((h.scl_slope === 0) || (h.scl_slope === 1 && h.scl_inter === 0))) fail('Scaled prediction labels are unsupported.')
  const getter = { 2: ['getUint8', 1], 4: ['getInt16', 2], 512: ['getUint16', 2], 8: ['getInt32', 4] }[h.datatypeCode]
  if (!getter || getter[1] * 8 !== h.numBitsPerVoxel) fail('Unsupported prediction data type.')
  const n = h.dims.slice(1, 4).reduce((a, b) => a * b, 1)
  const view = new DataView(data); const labels = new Uint8Array(n)
  for (let i = 0; i < n; i++) {
    const v = view[getter[0]](h.vox_offset + i * getter[1], h.littleEndian)
    if (v !== 0 && v !== 1 && v !== 2) fail('Unexpected prediction label.')
    labels[i] = v
  }
  return labels
}
export const sha = async raw => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)), b => b.toString(16).padStart(2, '0')).join('')

export async function loadScanMeasurements(context, signal) {
  if (!context?.available) fail('Show a saved prediction for this study before asking for its volume.')
  if (context.source !== 'saved') fail('This analysis has no verified link to a prediction mask. Show the saved prediction to measure that outline.')
  const { caseId, files } = context
  if (!/^PanTS_\d{8}$/.test(caseId) || files?.ct !== `${caseId}/ct.nii.gz` || files?.pred !== `${caseId}/pred.nii.gz`) fail('The saved prediction paths are not bound to this study.')
  const loaded = []
  // Sequential bounded reads limit peak memory; both files are local assets, never API input.
  for (const kind of ['ct', 'pred']) {
    const response = await fetch(`/cases/${files[kind]}`, { signal, cache: 'no-store' })
    if (!response.ok || !response.body) fail('The saved CT or prediction file is unavailable.')
    const raw = await boundedStream(response.body, signal)
    const decoded = await decodeMeasurementFile(raw, signal)
    // HTTP Content-Encoding may already remove gzip. Hash canonical decoded NIfTI bytes.
    const digest = await sha(decoded.data)
    loaded.push({ header: decoded.header, labels: kind === 'pred' ? labelsFrom(decoded) : null, digest })
  }
  signal?.throwIfAborted()
  return { ...measureMask(loaded[0].header, loaded[1].header, loaded[1].labels, context.spacingMm),
    contextKey: context.key, ctSha256: loaded[0].digest, predictionSha256: loaded[1].digest }
}

export function measurementText(measurement, target) {
  const volume = target === 'pancreas' ? measurement.pancreasMl : measurement.lesionMl
  if (target === 'lesion' && measurement.lesionVoxels === 0) return 'The saved prediction contains no lesion-labeled voxels. This does not establish that no lesion is present.'
  const amount = volume < 0.01 ? 'less than 0.01' : `about ${volume.toFixed(2)}`
  return target === 'pancreas'
    ? `The pancreas outline in this saved prediction occupies ${amount} mL (cm³), including any lesion-labeled regions. This measures the loaded outline; the scan may be cropped, so it is not a verified whole-pancreas volume.`
    : `The suspected-lesion regions in this saved prediction occupy ${amount} mL (cm³) in total. This combines all lesion-labeled regions; it is not an individual lesion diameter or a diagnosis.`
}
