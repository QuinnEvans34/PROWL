import { boundedStream, sha } from './scanMeasurements.js'
import { validateNativeEvidence, validateAssistedEvidence, measureNativePackage } from './nativeMeasurements.js'
const HASH = /^[a-f0-9]{64}$/
export function validateSavedPrediction(data) {
  const assisted = data?.schema_version === 'assisted-prediction-view-v1'
  if (!['saved-prediction-view-v1', 'saved-prediction-view-v2', 'assisted-prediction-view-v1'].includes(data?.schema_version) || !/^[A-Za-z0-9_-]+$/.test(data.case_id || '')) throw new Error('Unsupported saved prediction package.')
  if (!['completed', 'completed_with_warnings'].includes(data.status)) throw new Error('Prediction failed or is incomplete.')
  if (assisted) {
    if (data.prediction_mode !== 'pancreas_assisted' || data.reference_inputs_used !== true
      || !HASH.test(data.request_identity) || !HASH.test(data.assistance_sha256) || !HASH.test(data.recipe_sha256)
      || !/^[a-f0-9]{32}$/.test(data.prediction_id)) throw new Error('Invalid assisted prediction identity.')
  } else if (data.prediction_mode !== 'autonomous' || data.reference_inputs_used !== false) throw new Error('Expected a CT-only autonomous prediction.')
  for (const key of ['ct', 'pred']) {
    const f = data.files?.[key]
    if (!f || !/^[A-Za-z0-9_-]+\.nii\.gz$/.test(f.uri) || !HASH.test(f.content_sha256) || !Number.isSafeInteger(f.bytes) || f.bytes <= 0 || f.bytes > 512 * 1024 * 1024) throw new Error(`Missing or invalid ${key} file identity.`)
  }
  if (!(assisted ? ['segmenter'] : ['localizer', 'segmenter']).every(k => HASH.test(data.model_sha256?.[k])) || !HASH.test(data.result_sha256) || !HASH.test(data.inference_evidence_sha256)) throw new Error('Missing model or result identity.')
  const g = data.geometry
  if (g?.units !== 'mm' || g.shape?.length !== 3 || !g.shape.every(n => Number.isSafeInteger(n) && n > 0) || g.affine?.length !== 4 || !g.affine.every(r => r.length === 4 && r.every(Number.isFinite))) throw new Error('Invalid native geometry.')
  if (JSON.stringify(data.ct_window) !== '[-100,300]' || !Array.isArray(data.warnings) || !data.warnings.every(s => typeof s === 'string')) throw new Error('Invalid display settings.')
  if (data.schema_version === 'saved-prediction-view-v2' || assisted) {
    if (data.files.ct.uri !== 'ct.nii.gz' || data.files.pred.uri !== 'prediction.nii.gz' || g.shape.reduce((a, b) => a*b, 1) > 32000000 || ['ct', 'pred'].some(k => data.files[k].bytes > 64*1024*1024)
      || JSON.stringify(data.labels) !== JSON.stringify({ '0': 'background', '1': 'pancreas', '2': 'lesion' })) throw new Error('Unsupported native measurement package.')
    for (const [key, expected] of [['result', data.result_sha256], ['evidence', data.inference_evidence_sha256]]) {
      const f = data.files[key]
      if (f?.uri !== `${key}.json` || f.content_sha256 !== expected || !Number.isSafeInteger(f.bytes) || f.bytes <= 0 || f.bytes > 1024*1024) throw new Error('Invalid provenance file identity.')
    }
  }
  return data
}

export async function loadSavedPrediction(base, signal, expected = null) {
  const response = await fetch(`${base}/manifest.json`, { signal, cache: 'no-store' })
  if (!response.ok) throw new Error(`Saved package unavailable (${response.status}).`)
  const manifest = validateSavedPrediction(JSON.parse(new TextDecoder().decode(await boundedStream(response.body, signal, 1024*1024))))
  if (expected && (manifest.case_id !== expected.case_id || manifest.prediction_id !== expected.job_id
    || manifest.request_identity !== expected.request_identity)) throw new Error('Prediction belongs to a different request.')
  const urls = {}; const buffers = {}
  const native = manifest.schema_version !== 'saved-prediction-view-v1'
  try {
    for (const key of (native ? ['ct', 'pred', 'result', 'evidence'] : ['ct', 'pred'])) {
      const file = manifest.files[key]
      const res = await fetch(`${base}/${file.uri}`, { signal, cache: 'no-store' })
      if (!res.ok) throw new Error(`Missing ${key} file (${res.status}).`)
      const bytes = await boundedStream(res.body, signal, file.bytes)
      const hash = await sha(bytes)
      if (bytes.byteLength !== file.bytes || hash !== file.content_sha256) throw new Error(`${key} file identity mismatch.`)
      if (native) buffers[key] = bytes
      if (key === 'ct' || key === 'pred') urls[key] = URL.createObjectURL(new Blob([bytes], { type: 'application/gzip' }))
    }
    let measurement = null
    if (native) {
      const parse = bytes => JSON.parse(new TextDecoder().decode(bytes))
      const roi = (manifest.schema_version === 'assisted-prediction-view-v1' ? validateAssistedEvidence : validateNativeEvidence)(manifest, parse(buffers.result), parse(buffers.evidence))
      measurement = await measureNativePackage(manifest, buffers, roi, signal)
    }
    signal?.throwIfAborted()
    return { manifest, urls, measurement, release: () => Object.values(urls).forEach(url => URL.revokeObjectURL(url)) }
  } catch (error) {
    Object.values(urls).forEach(url => URL.revokeObjectURL(url))
    throw error
  }
}
