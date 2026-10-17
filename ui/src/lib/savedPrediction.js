const HASH = /^[a-f0-9]{64}$/
export function validateSavedPrediction(data) {
  if (data?.schema_version !== 'saved-prediction-view-v1' || !/^[A-Za-z0-9_-]+$/.test(data.case_id || '')) throw new Error('Unsupported saved prediction package.')
  if (!['completed', 'completed_with_warnings'].includes(data.status)) throw new Error('Prediction failed or is incomplete.')
  if (data.prediction_mode !== 'autonomous' || data.reference_inputs_used !== false) throw new Error('Expected a CT-only autonomous prediction.')
  for (const key of ['ct', 'pred']) {
    const f = data.files?.[key]
    if (!f || !/^[A-Za-z0-9_-]+\.nii\.gz$/.test(f.uri) || !HASH.test(f.content_sha256) || !Number.isSafeInteger(f.bytes) || f.bytes <= 0 || f.bytes > 512 * 1024 * 1024) throw new Error(`Missing or invalid ${key} file identity.`)
  }
  if (!['localizer', 'segmenter'].every(k => HASH.test(data.model_sha256?.[k])) || !HASH.test(data.result_sha256) || !HASH.test(data.inference_evidence_sha256)) throw new Error('Missing model or result identity.')
  const g = data.geometry
  if (g?.units !== 'mm' || g.shape?.length !== 3 || !g.shape.every(n => Number.isSafeInteger(n) && n > 0) || g.affine?.length !== 4 || !g.affine.every(r => r.length === 4 && r.every(Number.isFinite))) throw new Error('Invalid native geometry.')
  if (JSON.stringify(data.ct_window) !== '[-100,300]' || !Array.isArray(data.warnings) || !data.warnings.every(s => typeof s === 'string')) throw new Error('Invalid display settings.')
  return data
}

export async function loadSavedPrediction(base, signal) {
  const response = await fetch(`${base}/manifest.json`, { signal, cache: 'no-store' })
  if (!response.ok) throw new Error(`Saved package unavailable (${response.status}).`)
  const manifest = validateSavedPrediction(await response.json())
  const urls = {}
  try {
    for (const key of ['ct', 'pred']) {
      const file = manifest.files[key]
      const res = await fetch(`${base}/${file.uri}`, { signal, cache: 'no-store' })
      if (!res.ok) throw new Error(`Missing ${key} file (${res.status}).`)
      const bytes = await res.arrayBuffer()
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('')
      if (bytes.byteLength !== file.bytes || hash !== file.content_sha256) throw new Error(`${key} file identity mismatch.`)
      urls[key] = URL.createObjectURL(new Blob([bytes], { type: 'application/gzip' }))
    }
    return { manifest, urls, release: () => Object.values(urls).forEach(url => URL.revokeObjectURL(url)) }
  } catch (error) {
    Object.values(urls).forEach(url => URL.revokeObjectURL(url))
    throw error
  }
}
