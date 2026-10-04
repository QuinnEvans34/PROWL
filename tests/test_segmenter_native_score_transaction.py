from retained_diagnostic_metadata import metadata as retained_metadata
from copy import deepcopy
from pathlib import Path
import json
import pytest
from src.training import segmenter_native_scoring_v1 as c
from src.operations.segmenter_score_storage_v1 import score_stores
from src.data.manifest_records import canonical,digest
from scripts.diagnostics import segmenter_native_scoring as cli

@pytest.fixture
def pair():
 _,_,cases,rows=retained_metadata()['native_scoring_inputs'];d=cases[0]['descriptor'];return d,[r for r in rows if r['study_id']==d['study_id']]

@pytest.mark.parametrize('fault',['ct','missing','duplicate','role','uri','hash','grid','bytes'])
def test_target_only_descriptor_guards(pair,fault):
 d,r=deepcopy(pair)
 if fault=='ct':r[0]['kind']='ct'
 if fault=='missing':r.pop()
 if fault=='duplicate':r[1]=r[0]
 if fault=='role':r[0]['protected_role']='validation'
 if fault=='uri':r[0]['uri']='other.nii.gz'
 if fault=='hash':r[0]['sha256']='0'*64
 if fault=='grid':r[0]['geometry']['shape_xyz'][0]+=1
 if fault=='bytes':r[0]['compressed_bytes']+=1
 with pytest.raises((ValueError,KeyError)):c.check_targets(d,r)

def test_exact_pair_allows_no_ct(pair):c.check_targets(*pair)

@pytest.mark.parametrize('fault',['approval','area','operation','quota','updates'])
def test_closed_scoring_capability(fault):
 cap=json.loads(cli.CAP.read_bytes())
 if fault=='approval':cap['approval']='D-324'
 if fault=='area':cap['primary_area']='segmenter-inference-runs'
 if fault=='operation':cap['operation']='training'
 if fault=='quota':cap['max_new_bytes_per_domain']*=2
 if fault=='updates':cap['real_optimizer_updates_allowed']=True
 raw=canonical(cap)
 with pytest.raises(ValueError):score_stores(cli.REPO/'configs/local/roots.yaml',raw,trusted_capability_sha256=digest(raw))

def test_bare_records_cannot_authorize_reads():
 with pytest.raises(ValueError):cli.read_case({}, {},'x','held','optimizer',0,{},lambda:None)

def test_supplied_payload_without_required_members_refused():
 req=dict(task=c.TASK,stage='original_native_scoring',model_updates_allowed=False,ct_reads_allowed=False)
 with pytest.raises(ValueError):c.validate_payload({'request.json':canonical(req)},dict(request=req,request_sha256=digest(canonical(req))))

@pytest.fixture
def evidence():
 # Invented64-voxel evidence with the same closed fields, never real file provenance.
 import numpy as np
 from src.data.segmenter_content_v1 import APPROVED_POLICY
 pan=np.zeros((4,4,4),np.uint8);pan[1:3,1:3,1:3]=1;les=np.zeros_like(pan);les[1,1,1]=les[3,3,3]=1;pred=np.zeros_like(pan);pred[1,1,1]=pred[0,0,0]=2;pred[1,1,2]=pred[1,2,1]=1
 base=c.score(pred,pan,les,target_state='positive');cases=[];exports=[];rows=[];refs=[];scores=[]
 for i in range(7):
  sid=f'invented-{i}';role='validation' if i==6 else 'train';g=dict(shape_xyz=[4]*3,affine_ras=np.eye(4).ravel().tolist(),spacing_mm_xyz=[1]*3)
  cases.append(dict(study_id=sid,protected_role=role,descriptor={'geometry':g},fidelity=dict(metrics={n:dict(native_voxels=v['target_voxels']) for n,v in base['metrics'].items()},outside_pancreas_voxels=1,source_component_count=2,components=[{'native_voxels':1},{'native_voxels':1}])))
  exports.append(dict(native_sha256=digest(sid.encode()),class_counts=[60,2,2]));scores.append(dict(study_id=sid,protected_role=role,source_shape=[4]*3,source_affine=np.eye(4).tolist(),prediction_sha256=digest(sid.encode()),**deepcopy(base),oracle=dict(state='passed',confusion_matrix=base['confusion_matrix'])))
  for kind,n in [('pancreas',8),('lesion',2)]:
   scaling=dict(effective_slope=1.,effective_intercept=0.,units=['unknown','unknown'],decompressed_header_sha256=digest((sid+kind).encode())) if kind=='lesion' else dict(effective_scaling=dict(slope=1.,intercept=0.),units=['unknown','unknown'])
   e=dict(study_id=sid,protected_role=role,kind=kind,uri=sid+'/'+kind,compressed_bytes=3,expanded_bytes=416,sha256=digest((sid+kind).encode()),geometry=g,dtype='int8',**({'header':scaling} if kind=='lesion' else {'retained_content':scaling}));rows.append(e)
   refs.append(dict(study_id=sid,protected_role=role,kind=kind,uri=e['uri'],header=dict(shape=[4]*3,affine=np.eye(4).tolist(),spacing=[1]*3,slope=1.,intercept=0.,units=['unknown','unknown'],offset=352,dtype='|i1',header_sha256=e['sha256']),read=dict(compressed_bytes=3,expanded_bytes=416,sha256=e['sha256'],gzip_eof_crc_verified=True),decoding=dict(policy=APPROVED_POLICY,max_endpoint_residual=0,semantic_value_counts=[dict(stored=0.,semantic=0.,count=64-n),dict(stored=1.,semantic=1.,count=n)],foreground_voxels=n),decoded_sha256=digest(b'invented_reference')))
 req=dict(task=c.TASK,stage='original_native_scoring',model_updates_allowed=False,ct_reads_allowed=False,cases=cases,files=rows,prediction_exports=exports,limits=dict(hash_bytes=42,decode_bytes=42,expanded_bytes=5824),code_pins={'invented':'source'},runtime={'invented':'environment'})
 pin=digest(canonical(req));production=dict(request_sha256=pin,source_counts=req['limits'],source_arrays_read=14,ct_arrays_read=0,model_forwards=0,model_updates=0,code_pins=req['code_pins'],runtime=req['runtime'],mount_before={'invented':'volume'},mount_after={'invented':'volume'})
 return {n:canonical(v) for n,v in {'request.json':req,'scores.json':scores,'references.json':refs,'aggregates.json':c.aggregates(scores),'production.json':production}.items()},dict(request=req,request_sha256=pin)

def test_complete_closed_evidence_valid(evidence):
 assert c.validate_payload(*evidence)['references']==14

@pytest.mark.parametrize('fault',['dice','confusion','prediction','role','affine','outside','missing_component','component_hits','bounds','decoded_foreground','header_type','header_units','source_hash','source_budget','aggregate','model_forward','extra'])
def test_closed_evidence_refuses_forgery(evidence,fault):
 files,identity=deepcopy(evidence);s=json.loads(files['scores.json']);r=json.loads(files['references.json']);p=json.loads(files['production.json']);a=json.loads(files['aggregates.json'])
 if fault=='dice':s[0]['metrics']['lesion']['dice']=1.
 if fault=='confusion':s[0]['confusion_matrix'][0][0]+=1
 if fault=='prediction':s[0]['prediction_sha256']='0'*64
 if fault=='role':s[0]['protected_role']='validation'
 if fault=='affine':s[0]['source_affine'][0][0]=2
 if fault=='outside':s[0]['outside_pancreas_voxels']=0
 if fault=='missing_component':s[0]['components'].pop()
 if fault=='component_hits':s[0]['components'][0]['true_positive']=0
 if fault=='bounds':s[0]['components'][0]['bounds_xyz_half_open'][0][1]=5
 if fault=='decoded_foreground':r[0]['decoding']['foreground_voxels']=0
 if fault=='header_type':r[0]['header']['dtype']='float32'
 if fault=='header_units':r[0]['header']['units']=['meter','unknown']
 if fault=='source_hash':r[0]['read']['sha256']='0'*64
 if fault=='source_budget':p['source_counts']['hash_bytes']+=1
 if fault=='aggregate':a['train']['macro']['lesion']['dice']=1
 if fault=='model_forward':p['model_forwards']=1
 if fault=='extra':files['unknown']=b'x'
 files.update({'scores.json':canonical(s),'references.json':canonical(r),'production.json':canonical(p),'aggregates.json':canonical(a)})
 with pytest.raises(ValueError):c.validate_payload(files,identity)


def test_prepared_request_transport_equals_protected_canonical(tmp_path,monkeypatch,capsys):
 from types import SimpleNamespace
 req={'task':c.TASK,'stage':'original_native_scoring','ct_reads_allowed':False,'model_updates_allowed':False,'metadata_receipt_sha256':'m','profile_receipt_sha256':'p','unicode':'é'}
 budget=tmp_path/'budget.json';budget.write_bytes(canonical(dict(decision='D-325',capability_sha256=cli.CAP_PIN,ceilings=[10,20,20])))
 before=budget.read_bytes();dest=tmp_path/'request'
 monkeypatch.setattr(cli,'BUDGET',budget);monkeypatch.setattr(cli,'DEST',dest)
 monkeypatch.setattr(cli,'stores',lambda **kw:[SimpleNamespace(quota_bytes=v) for v in [30,40,40]])
 monkeypatch.setattr(cli,'build_request',lambda m,p:req)
 cli.prepare('m','p');pin=capsys.readouterr().out.strip()
 assert (dest/'request.json').read_bytes()==canonical(req)
 assert pin==digest(canonical(req)) and cli.checked(pin)==req and budget.read_bytes()==before


@pytest.mark.parametrize('fault',[None,'transport','pin','stage','ct','updates'])
def test_request_identity_checked_before_target_open(pair,tmp_path,monkeypatch,fault):
 from types import SimpleNamespace
 import os
 _,old,cases,rows=retained_metadata()['native_scoring_inputs'];d=pair[0]
 req=dict(task=c.TASK,stage='original_native_scoring',ct_reads_allowed=False,model_updates_allowed=False,records=old['binding']['records'],cohort_completion_sha256=cli.loader.COMPLETION,descriptor_sha256=cli.loader.DESCRIPTORS,cases=cases,files=rows,capability=old['capability']|dict(operations=['full_compressed_hash','full_gzip_decode_native_targets']),limits={})
 if fault=='stage':req['stage']='other'
 if fault=='ct':req['ct_reads_allowed']=True
 if fault=='updates':req['model_updates_allowed']=True
 pin=digest(canonical(req))
 if fault=='transport':pin=digest(cli.source.encoded(req))
 if fault=='pin':pin='0'*64
 class Session:
  records=req['records']
  def select(self,*args):return d
 monkeypatch.setattr(cli.loader,'ResolvedInputs',Session)
 calls=[];monkeypatch.setattr(c,'read_targets',lambda *args:calls.append(args) or 'read')
 fd=os.open(tmp_path,os.O_RDONLY)
 try:
  st=os.fstat(fd);monkeypatch.setattr(cli.source,'mount_guard',lambda cap:dict(root_device=st.st_dev,root_inode=st.st_ino))
  if fault is None:assert cli.read_case(Session(),req,pin,d['study_id'],'optimizer',fd,{},lambda:None)=='read' and len(calls)==1
  else:
   with pytest.raises(ValueError):cli.read_case(Session(),req,pin,d['study_id'],'optimizer',fd,{},lambda:None)
   assert calls==[]
 finally:os.close(fd)
