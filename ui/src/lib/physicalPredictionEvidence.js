import { canonicalValue } from './nativeMeasurements.js'
const REQUEST = 'f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd'
const CASES = ['PanTS_00002028','PanTS_00000909','PanTS_00004681','PanTS_00006755']
const same = (a,b) => canonicalValue(a) === canonicalValue(b)
const require = (ok, message) => { if (!ok) throw new Error(message) }
const close = (a,b) => Array.isArray(a) && a.length === 4 && a.every((r,i) => Array.isArray(r) && r.length === 4
  && r.every((v,j) => Number.isFinite(v) && Math.abs(v-b[i][j]) <= 1e-4))

// Caller verifies original request/result/volume bytes. This does not qualify model accuracy.
export function validatePhysicalEvidence(m, result, request) {
  require(m.schema_version === 'physical-prediction-view-v1' && m.request_identity === REQUEST
    && m.inference_evidence_sha256 === REQUEST && m.probability_equivalence === 'UNQUALIFIED'
    && m.evaluation_scope === 'four-case-exploratory-20261102' && m.case_role === 'exposed_development', 'Unrecognized physical evaluation scope.')
  require(request.version === 'four-case-exception-1' && request.probability_equivalence === 'UNQUALIFIED'
    && same(request.cases?.map(c => c.case_id), CASES), 'Physical request cohort differs.')
  const c = request.cases.find(c => c.case_id === m.case_id)
  require(c && c.identity?.source_sha256?.ct === m.files.ct.content_sha256
    && ['localizer','segmenter'].every(k => request.models?.[k]?.sha256 === m.model_sha256[k]), 'Physical source or model identity differs.')
  const g = m.geometry
  require(result.status === 'COMPLETED' && result.case_id === m.case_id && result.arm === 'autonomous'
    && result.reference_inputs_used === false && result.optimizer_updates === 0 && result.request_sha256 === REQUEST
    && result.artifacts?.['prediction.nii.gz'] === m.files.pred.content_sha256
    && same(result.source_shape,g.shape) && close(result.source_affine,g.affine) && result.units === 'mm'
    && same(c.header?.ct?.shape,g.shape) && close(c.header?.ct?.affine,g.affine) && c.header.ct.units === 'mm', 'Physical result identity or geometry differs.')
  const e = result.evidence; const p = e?.parent_geometry; const f = p?.forward
  require(e?.component === 'predicted-physical-region-v1' && e.reference_inputs_used === false
    && e.localizer_policy === 'all_support' && e.reconstruction?.gap_voxels === 0
    && e.reconstruction.output_decision === 'native_center_probability_blend_then_argmax'
    && same(p?.source_shape,g.shape) && close(p?.source_affine,g.affine), 'Physical reconstruction differs.')
  require(Array.isArray(f) && f.length === 3 && f.every(r => Array.isArray(r) && r.length === 2
    && Number.isInteger(r[0]) && [1,-1].includes(r[1]))
    && same(f.map(r=>r[0]).sort(),[0,1,2]), 'Invalid physical orientation.')
  const shape = [0,0,0]
  const affine = g.affine.map(r=>[0,0,0,r[3]])
  f.forEach(([axis,sign],i)=>{
    shape[axis]=g.shape[i]
    for(let row=0;row<4;row++) {
      affine[row][axis]=g.affine[row][i]*sign
      if(sign===-1) affine[row][3]+=g.affine[row][i]*(g.shape[i]-1)
    }
  })
  require(same(shape,p.shape) && close(p.affine,affine), 'Physical orientation affine differs.')
  const low=e.region_low, high=e.region_high
  require(Array.isArray(low) && Array.isArray(high) && low.length===3 && high.length===3
    && low.every((v,i)=>Number.isInteger(v) && Number.isInteger(high[i]) && v>=0 && high[i]>v && high[i]<=shape[i]), 'Invalid physical region.')
  const box=[[],[]]
  f.forEach(([axis,sign],i)=>{
    box[0].push(sign===1?low[axis]:g.shape[i]-high[axis])
    box[1].push(sign===1?high[axis]:g.shape[i]-low[axis])
  })
  require(same(box,m.native_region), 'Physical native region differs.')
  return box
}
