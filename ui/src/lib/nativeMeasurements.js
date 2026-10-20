import { decodeMeasurementFile, labelsFrom, measureMask } from './scanMeasurements.js'
import { verifyNativeVolumes } from './nativeGeometry.js'
const require = (ok, message) => { if (!ok) throw new Error(message) }
// Comparison of parsed JSON, not a substitute for hashing the original evidence bytes.
export const canonicalValue = value => JSON.stringify(sort(value))
function sort(value) {
  if (Array.isArray(value)) return value.map(sort)
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, sort(value[k])]))
  return value
}
function matchesGeometry(t, g) {
  return canonicalValue(t?.source_shape) === canonicalValue(g.shape)
    && Array.isArray(t?.source_affine) && t.source_affine.length === 4
    && t.source_affine.every((r, i) => Array.isArray(r) && r.length === 4
      && r.every((n, j) => Number.isFinite(n) && Math.abs(n - g.affine[i][j]) <= 1e-4))
}
// Caller verifies exact file hashes first. These checks bind the recorded claims together.
export function validateNativeEvidence(manifest, result, evidence) {
  const same = (a, b) => canonicalValue(a) === canonicalValue(b)
  require(manifest.schema_version === 'saved-prediction-view-v2', 'A v2 measurement package is required.')
  require(result?.status === 'complete' && result.reference_inputs_used === false
    && result.case_id === manifest.case_id && result.prediction_sha256 === manifest.files.pred.content_sha256,
    'Result identity differs from the saved package.')
  require(same(result.evidence, evidence), 'Result and inference evidence differ.')
  const source = { study_id: manifest.case_id, ct_sha256: manifest.files.ct.content_sha256 }
  require(evidence?.component === 'autonomous-cascade-v1' && evidence.reference_inputs_used === false
    && same(evidence.source_identity, source) && same(evidence.model_sha256, manifest.model_sha256),
    'Inference source or model identity differs.')
  const plan = evidence.region_plan; const t = plan?.transform; const p = plan?.prediction_record
  require(plan?.component === 'segmenter-predicted-roi-v2' && t?.roi_origin === 'predicted_region'
    && same(t.source_identity, source) && matchesGeometry(t, manifest.geometry)
    && matchesGeometry(evidence.localizer_transform, manifest.geometry), 'Native inference geometry differs.')
  require(p?.full_volume === true && p.units === 'mm' && same(p.source_identity, source)
    && p.model_sha256 === manifest.model_sha256.localizer
    && matchesGeometry({ source_shape: p.native_shape, source_affine: p.native_affine }, manifest.geometry),
    'Localizer source or model identity differs.')
  const box = t.native_box
  require(Array.isArray(box) && box.length === 2 && box.every(r => Array.isArray(r) && r.length === 3 && r.every(Number.isInteger))
    && box[0].every((lo, i) => lo >= 0 && box[1][i] > lo && box[1][i] <= manifest.geometry.shape[i]), 'Invalid native inference region.')
  return box
}

export function validateAssistedEvidence(m, result, e) {
  const same = (a, b) => canonicalValue(a) === canonicalValue(b)
  require(m.schema_version === 'assisted-prediction-view-v1' && result?.status === 'complete'
    && result.reference_inputs_used === true && result.case_id === m.case_id
    && result.prediction_sha256 === m.files.pred.content_sha256 && same(result.evidence, e), 'Assisted result identity differs.')
  require(e?.component === 'assisted-native-inference-v1' && e.reference_inputs_used === true
    && e.request_identity === m.request_identity && e.prediction_id === m.prediction_id
    && e.recipe_sha256 === m.recipe_sha256 && same(e.model_sha256, m.model_sha256)
    && same(e.source_identity, { study_id: m.case_id, ct_sha256: m.files.ct.content_sha256 }), 'Assisted source or model identity differs.')
  require(e.assistance?.kind === 'provided_pancreas' && e.assistance.sha256 === m.assistance_sha256
    && e.assistance.lesion_reference_used_for_prediction === false, 'Assisted input roles are missing or incompatible.')
  require(matchesGeometry(e.transform, m.geometry) && e.transform.units === 'mm'
    && e.reconstruction?.uncovered_region_voxels === 0 && e.reconstruction.outside_region === 'background', 'Assisted reconstruction is incomplete.')
  const box = e.transform.native_box
  require(Array.isArray(box) && box.length === 2 && box.every(r => Array.isArray(r) && r.length === 3 && r.every(Number.isInteger))
    && box[0].every((lo, i) => lo >= 0 && box[1][i] > lo && box[1][i] <= m.geometry.shape[i]), 'Invalid assisted inference region.')
  return box
}

export async function measureNativePackage(manifest, buffers, roi, signal) {
  const limits = { maxVoxels: 32000000, decodedLimit: 128 * 1024 * 1024 }
  // Sequential decoding avoids keeping the full decoded CT after its geometry is inspected.
  const ctHeader = (await decodeMeasurementFile(buffers.ct, signal, limits)).header
  const prediction = await decodeMeasurementFile(buffers.pred, signal, limits)
  verifyNativeVolumes([{ hdr: ctHeader }, { hdr: prediction.header }], manifest.geometry)
  const labels = labelsFrom(prediction)
  let measurement
  try { measurement = measureMask(ctHeader, prediction.header, labels, undefined, { maxVoxels: limits.maxVoxels, roi }) }
  catch (error) {
    if (error.code !== 'mask_coverage') throw error
    return { status: 'unavailable', reason: error.message }
  }
  signal?.throwIfAborted()
  return { status: 'ready', ...measurement, schema: 'native-mask-volume-v1',
    assisted: manifest.schema_version === 'assisted-prediction-view-v1',
    ctSha256: manifest.files.ct.content_sha256, predictionSha256: manifest.files.pred.content_sha256,
    hashBasis: 'Original package files; SHA-256 verified against the manifest',
    modelLineage: 'Model hashes agree with the retained inference record; weights and training history were not re-audited',
    modelSha256: manifest.model_sha256, resultSha256: manifest.result_sha256,
    inferenceSha256: manifest.inference_evidence_sha256, nativeRegion: roi,
    coverage: 'Native CT and inference grids agree. No predicted label touches the recorded crop edge. Anatomical completeness remains unverified' }
}
