// @vitest-environment node
import { it, expect } from 'vitest'
import { validatePhysicalEvidence } from '../src/lib/physicalPredictionEvidence.js'
import { validateSavedPrediction } from '../src/lib/savedPrediction.js'
const pin='f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd'
function fixture(){
 const shape=[9,10,11], affine=[[0,-3,0,27],[2,0,0,0],[0,0,-4,40],[0,0,0,1]]
 const m={schema_version:'physical-prediction-view-v1',case_id:'PanTS_00002028',status:'completed_with_warnings',prediction_mode:'autonomous',reference_inputs_used:false,
   request_identity:pin,inference_evidence_sha256:pin,result_sha256:'d'.repeat(64),evaluation_scope:'four-case-exploratory-20261102',case_role:'exposed_development',probability_equivalence:'UNQUALIFIED',
   native_region:[[1,2,2],[7,8,8]],model_sha256:{localizer:'a'.repeat(64),segmenter:'b'.repeat(64)},geometry:{shape,affine,units:'mm'},ct_window:[-100,300],labels:{'0':'background','1':'pancreas','2':'lesion'},warnings:[],
   files:Object.fromEntries([['ct','ct.nii.gz','c'.repeat(64)],['pred','prediction.nii.gz','e'.repeat(64)],['result','result.json','d'.repeat(64)],['evidence','evidence.json',pin]].map(([k,uri,hash])=>[k,{uri,bytes:100,content_sha256:hash}]))}
 const q={version:'four-case-exception-1',probability_equivalence:'UNQUALIFIED',models:{localizer:{sha256:m.model_sha256.localizer},segmenter:{sha256:m.model_sha256.segmenter}},
   cases:['PanTS_00002028','PanTS_00000909','PanTS_00004681','PanTS_00006755'].map(case_id=>({case_id,identity:{source_sha256:{ct:m.files.ct.content_sha256}},header:{ct:{shape,affine,units:'mm'}}}))}
 const r={status:'COMPLETED',case_id:m.case_id,arm:'autonomous',reference_inputs_used:false,optimizer_updates:0,request_sha256:pin,artifacts:{'prediction.nii.gz':m.files.pred.content_sha256},source_shape:shape,source_affine:affine,units:'mm',
   evidence:{component:'predicted-physical-region-v1',reference_inputs_used:false,localizer_policy:'all_support',reconstruction:{gap_voxels:0,output_decision:'native_center_probability_blend_then_argmax'},
   parent_geometry:{source_shape:shape,source_affine:affine,shape:[10,9,11],affine:[[3,0,0,0],[0,2,0,0],[0,0,4,0],[0,0,0,1]],forward:[[1,1],[0,-1],[2,-1]]},region_low:[2,1,3],region_high:[8,7,9]}}
 return structuredClone({m,q,r})
}
it('keeps original physical records and maps an oblique-capable permutation/flip to native bounds',()=>{
 const {m,q,r}=fixture();expect(validateSavedPrediction(m)).toBe(m)
 expect(validatePhysicalEvidence(m,r,q)).toEqual([[1,2,2],[7,8,8]])
})
it.each(['case','model','ct','pred','arm','reference','cohort','equivalence','request','geometry','orientation','parent','region','gap','native'])('rejects physical %s contradiction',fault=>{
 const {m,q,r}=fixture()
 if(fault==='case')r.case_id='other'
 if(fault==='model')q.models.segmenter.sha256='0'.repeat(64)
 if(fault==='ct')q.cases[0].identity.source_sha256.ct='0'.repeat(64)
 if(fault==='pred')r.artifacts['prediction.nii.gz']='0'.repeat(64)
 if(fault==='arm')r.arm='provided_region'
 if(fault==='reference')r.evidence.reference_inputs_used=true
 if(fault==='cohort')q.cases.pop()
 if(fault==='equivalence')m.probability_equivalence='QUALIFIED'
 if(fault==='request')r.request_sha256='0'.repeat(64)
 if(fault==='geometry')r.source_affine[0][3]+=1
 if(fault==='orientation')r.evidence.parent_geometry.forward[0][0]=2
 if(fault==='parent')r.evidence.parent_geometry.affine[0][3]+=1
 if(fault==='region')r.evidence.region_low[0]=-1
 if(fault==='gap')r.evidence.reconstruction.gap_voxels=1
 if(fault==='native')m.native_region[0][0]=0
 expect(()=>validatePhysicalEvidence(m,r,q)).toThrow()
})
