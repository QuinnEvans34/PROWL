// @vitest-environment node
import { it, expect, vi } from 'vitest'
import { NIFTI1 } from 'nifti-reader-js'
import { gzipSync } from 'node:zlib'
import { sha } from '../src/lib/scanMeasurements.js'
import { validateNativeEvidence } from '../src/lib/nativeMeasurements.js'
import { loadSavedPrediction } from '../src/lib/savedPrediction.js'

const geometry = { shape: [9,9,9], affine: [[2,0,0,7],[0,3,0,5],[0,0,4,-3],[0,0,0,1]], units: 'mm' }
function nifti({ boundary = false, outside = false, units = 2, shifted = false } = {}) {
  const h = new NIFTI1()
  Object.assign(h, { dims: [3,9,9,9,1,1,1,1], affine: structuredClone(geometry.affine), sform_code: 1,
    xyzt_units: units, littleEndian: true, datatypeCode: 2, numBitsPerVoxel: 8, vox_offset: 352, magic: 'n+1' })
  if (shifted) h.affine[0][3] += 1
  const b = new Uint8Array(352+729); b.set(new Uint8Array(h.toArrayBuffer()))
  b[352+4+9*4+81*4] = 1; b[352+5+9*4+81*4] = 2
  if (boundary) b[352+2+9*4+81*4] = 1
  if (outside) b[352+1+9*4+81*4] = 1
  return gzipSync(b)
}
async function fixture(options = {}) {
  const files = { ct: nifti(), pred: nifti(options) }
  const m = { schema_version: 'saved-prediction-view-v2', case_id: 'synthetic', status: 'completed_with_warnings',
    prediction_mode: 'autonomous', reference_inputs_used: false, model_sha256: { localizer: 'a'.repeat(64), segmenter: 'b'.repeat(64) },
    geometry, labels: {'0':'background','1':'pancreas','2':'lesion'}, ct_window: [-100,300], warnings: [], files: {} }
  const source = { study_id: m.case_id, ct_sha256: await sha(files.ct) }
  const transform = { source_identity: source, source_shape: geometry.shape, source_affine: geometry.affine, roi_origin: 'predicted_region', native_box: [[2,2,2],[7,7,7]] }
  const e = { component: 'autonomous-cascade-v1', reference_inputs_used: false, source_identity: source, model_sha256: m.model_sha256,
    localizer_transform: transform, region_plan: { component: 'segmenter-predicted-roi-v2', transform,
      prediction_record: { full_volume: true, units: 'mm', source_identity: source, model_sha256: m.model_sha256.localizer, native_shape: geometry.shape, native_affine: geometry.affine } } }
  const r = { case_id: m.case_id, status: 'complete', reference_inputs_used: false, prediction_sha256: await sha(files.pred), evidence: e }
  files.result = new TextEncoder().encode(JSON.stringify(r)); files.evidence = new TextEncoder().encode(JSON.stringify(e))
  for (const [k, b] of Object.entries(files)) m.files[k] = { uri: k === 'ct' ? 'ct.nii.gz' : k === 'pred' ? 'prediction.nii.gz' : `${k}.json`, bytes: b.byteLength, content_sha256: await sha(b) }
  m.result_sha256 = m.files.result.content_sha256; m.inference_evidence_sha256 = m.files.evidence.content_sha256
  return { m, r, e, files }
}
function serve(f, mutate) {
  const fetcher = vi.fn(async url => {
    if (url.endsWith('manifest.json')) return new Response(JSON.stringify(f.m))
    const k = Object.keys(f.m.files).find(k => url.endsWith('/'+f.m.files[k].uri))
    return new Response(mutate ? mutate(k,f.files[k]) : f.files[k])
  })
  vi.stubGlobal('fetch', fetcher); return fetcher
}
it('verifies all four files, binds provenance, and measures native volumes without a model', async () => {
  const f = await fixture(); const fetcher = serve(f)
  const loaded = await loadSavedPrediction('/saved')
  try {
    expect(loaded.measurement.pancreasMl).toBe(0.048); expect(loaded.measurement.lesionMl).toBe(0.024)
    expect(loaded.measurement.modelSha256).toEqual(f.m.model_sha256)
    expect(loaded.measurement.coverage).toContain('completeness remains unverified')
    expect(fetcher.mock.calls.map(c => c[0])).toEqual(['/saved/manifest.json','/saved/ct.nii.gz','/saved/prediction.nii.gz','/saved/result.json','/saved/evidence.json'])
  } finally { loaded.release() }
})
it.each(['ct','pred','result','evidence'])('rejects %s byte substitution', async key => {
  const f = await fixture(); serve(f,(k,b) => k === key ? new Uint8Array(b.byteLength) : b)
  await expect(loadSavedPrediction('/saved')).rejects.toThrow('identity mismatch')
})
it.each(['model','ct','prediction','reference','geometry','roi','localizer','evidence'])('rejects contradictory %s provenance', async fault => {
  const f = await fixture(); const e = structuredClone(f.e); const r = structuredClone(f.r)
  if (fault === 'model') e.model_sha256.segmenter = 'c'.repeat(64)
  if (fault === 'ct') e.source_identity.ct_sha256 = 'c'.repeat(64)
  if (fault === 'prediction') r.prediction_sha256 = 'c'.repeat(64)
  if (fault === 'reference') e.reference_inputs_used = true
  if (fault === 'geometry') e.region_plan.transform.source_affine[0][3] += 2
  if (fault === 'roi') e.region_plan.transform.native_box = [[-1,2,2],[7,7,7]]
  if (fault === 'localizer') e.region_plan.prediction_record.full_volume = false
  if (fault !== 'evidence') r.evidence = e
  else e.extra = 'different'
  expect(() => validateNativeEvidence(f.m,r,e)).toThrow()
})
it('withholds volume at an internal inference boundary even when CT boundary is clear', async () => {
  const f = await fixture({boundary:true}); serve(f); const loaded = await loadSavedPrediction('/saved')
  try {
    const m = loaded.measurement
    expect(m.status).toBe('unavailable'); expect(m.reason).toContain('inference crop'); expect(m.pancreasMl).toBeUndefined()
    expect(m.lesionMl).toBeUndefined()
    expect(m.coverageDiagnostics.cropContact).toEqual({pancreasLabel:1,lesionLabel:0})
    expect(m.coverageDiagnostics.imageContact).toEqual({pancreasLabel:0,lesionLabel:0})
    expect(m.predictionSha256).toBe(f.m.files.pred.content_sha256)
    expect(m.modelSha256).toEqual(f.m.model_sha256)
  }
  finally { loaded.release() }
})
it.each([{outside:true},{units:0},{shifted:true}])('rejects invalid native data %j', async options => {
  serve(await fixture(options)); await expect(loadSavedPrediction('/saved')).rejects.toThrow()
})
it('refuses missing provenance and oversized metadata declarations', async () => {
  const f = await fixture(); delete f.m.files.result; serve(f)
  await expect(loadSavedPrediction('/saved')).rejects.toThrow('provenance')
  f.m.files.result = { uri: 'result.json', bytes: 1024*1024+1, content_sha256:f.m.result_sha256 }
  await expect(loadSavedPrediction('/saved')).rejects.toThrow('provenance')
})
it('checks cancellation before a package can become ready', async () => {
  serve(await fixture()); const c = new AbortController(); c.abort()
  await expect(loadSavedPrediction('/saved',c.signal)).rejects.toThrow()
})

it('cleans up CT and prediction object URLs when provenance verification fails', async () => {
  const f=await fixture();serve(f,(k,b)=>k==='result'?new Uint8Array(b.byteLength):b)
  const revoke=vi.spyOn(URL,'revokeObjectURL')
  try {await expect(loadSavedPrediction('/saved')).rejects.toThrow('identity mismatch');expect(revoke).toHaveBeenCalledTimes(2)}
  finally {revoke.mockRestore()}
})
it('enforces a declared byte cap while streaming',async()=>{
  const f=await fixture();serve(f,(k,b)=>k==='ct'?new Uint8Array(b.byteLength+1):b)
  await expect(loadSavedPrediction('/saved')).rejects.toThrow('size limit')
})

async function assistedFixture() {
  const f=await fixture();const m=f.m
  Object.assign(m,{schema_version:'assisted-prediction-view-v1',prediction_mode:'pancreas_assisted',reference_inputs_used:true,
    prediction_id:'1'.repeat(32),request_identity:'2'.repeat(64),recipe_sha256:'3'.repeat(64),assistance_sha256:'4'.repeat(64),model_sha256:{segmenter:'b'.repeat(64)}})
  f.e={component:'assisted-native-inference-v1',reference_inputs_used:true,prediction_id:m.prediction_id,request_identity:m.request_identity,
    recipe_sha256:m.recipe_sha256,model_sha256:m.model_sha256,source_identity:{study_id:m.case_id,ct_sha256:m.files.ct.content_sha256},
    assistance:{kind:'provided_pancreas',sha256:m.assistance_sha256,lesion_reference_used_for_prediction:false},
    transform:{source_shape:geometry.shape,source_affine:geometry.affine,units:'mm',native_box:[[2,2,2],[7,7,7]]},
    reconstruction:{uncovered_region_voxels:0,outside_region:'background'}}
  f.r={...f.r,reference_inputs_used:true,evidence:f.e}
  f.files.result=new TextEncoder().encode(JSON.stringify(f.r));f.files.evidence=new TextEncoder().encode(JSON.stringify(f.e))
  for(const k of ['result','evidence'])m.files[k]={uri:`${k}.json`,bytes:f.files[k].byteLength,content_sha256:await sha(f.files[k])}
  m.result_sha256=m.files.result.content_sha256;m.inference_evidence_sha256=m.files.evidence.content_sha256
  return f
}
it('measures an assisted result bound to the requested job without using the provided mask',async()=>{
  const f=await assistedFixture();serve(f)
  const loaded=await loadSavedPrediction('/job',undefined,{case_id:f.m.case_id,job_id:f.m.prediction_id,request_identity:f.m.request_identity})
  try{expect(loaded.measurement.assisted).toBe(true);expect(loaded.measurement.pancreasMl).toBe(.048)}finally{loaded.release()}
})
it('rejects a valid result belonging to a different job before downloading volumes',async()=>{
  const f=await assistedFixture();const fetcher=serve(f)
  await expect(loadSavedPrediction('/job',undefined,{case_id:f.m.case_id,job_id:'9'.repeat(32),request_identity:f.m.request_identity})).rejects.toThrow('different request')
  expect(fetcher).toHaveBeenCalledTimes(1)
})
it.each(['source','model','assistance','reference','gap','geometry','region','recipe','request'])('rejects assisted %s contradictions',async fault=>{
  const {validateAssistedEvidence}=await import('../src/lib/nativeMeasurements.js');const f=await assistedFixture()
  if(fault==='source')f.e.source_identity.ct_sha256='0'.repeat(64)
  if(fault==='model')f.e.model_sha256={segmenter:'0'.repeat(64)}
  if(fault==='assistance')f.e.assistance.sha256='0'.repeat(64)
  if(fault==='reference')f.e.assistance.lesion_reference_used_for_prediction=true
  if(fault==='gap')f.e.reconstruction.uncovered_region_voxels=1
  if(fault==='geometry')f.e.transform.source_shape=[1,2,3]
  if(fault==='region')f.e.transform.native_box=[[0,0,0],[20,20,20]]
  if(fault==='recipe')f.e.recipe_sha256='0'.repeat(64)
  if(fault==='request')f.e.request_identity='0'.repeat(64)
  expect(()=>validateAssistedEvidence(f.m,f.r,f.e)).toThrow()
})
it('does not admit assisted evidence through the autonomous v2 validator',async()=>{
  const f=await assistedFixture();expect(()=>validateNativeEvidence(f.m,f.r,f.e)).toThrow()
})
