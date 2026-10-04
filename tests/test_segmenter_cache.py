from copy import deepcopy
from io import BytesIO
import json
import numpy as np
import pytest
from src.data import segmenter_cache_v1 as c,segmenter_geometry_v1 as g
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import content_hash
from src.operations.artifact_store import ArtifactStore


def fixture():
    entries=[];records=dict(optimizer=[],evaluator=[]);files={};cases=[]
    for i,(op,role,state) in enumerate([('optimizer','train','positive'),('evaluator','validation','verified_negative')]):
        sid='invented-'+str(i);geom=dict(shape_xyz=[8]*3,affine_ras=np.eye(4).ravel().tolist())
        d=dict(study_id=sid,operation=op,protected_role=role,purpose='pancreas_lesion_segmenter_'+('training' if role=='train' else 'validation'),roi_source='pancreas_only',class_precedence='lesion_over_pancreas',lesion_target_state=state,image=dict(content_sha256=digest(sid.encode())),geometry=geom)
        records[op].append(d);t=g.plan_geometry([8]*3,np.eye(4),[[0,0,0],[8,8,8]],g.recipe(),source_identity=dict(study_id=sid,ct_sha256=d['image']['content_sha256']),roi_origin='provided_pancreas_reference')
        x=np.full((1,144,144,144),.4,np.float32);y=np.zeros((144,144,144),np.uint8);y[40:100,40:100,40:100]=1
        if i==0:y[0,0,0]=2;y[80:82,80:82,80:82]=2
        counts=np.bincount(y.ravel(),minlength=3).tolist();f=dict(lesion_target_state=state,source_arrays_changed=False,metrics=dict(pancreas_parenchyma=dict(tensor_voxels=counts[1]),lesion=dict(tensor_voxels=counts[2])))
        e=dict(operation=op,descriptor=d,transform=t,transform_sha256=content_hash(t),fidelity=f,tensor_class_counts=counts);entries.append(e)
        nm=c.names(i)
        for k,a in [('image',x),('target',y)]:files[nm[k]]=c.encode(a)
        cases.append(dict(study_id=sid,protected_role=role,transform_sha256=e['transform_sha256'],tensor_class_counts=counts,files={k:dict(name=n,bytes=len(files[n]),sha256=digest(files[n])) for k,n in nm.items()}))
    b=dict(schema_version=c.VERSION,cohort_completion_sha256='a'*64,descriptor_sha256=content_hash(records),geometry_acceptance_sha256='b'*64,records=records,entries=entries,model_updates_allowed=False);pin=content_hash(b)
    files['binding.json']=canonical(b);files['production.json']=canonical(dict(schema_version=c.VERSION,binding_sha256=pin,request_sha256='c'*64,code_pins={},runtime={},source_counts=dict(hash_bytes=6,decode_bytes=6,expanded_bytes=6),cases=cases,model_updates=0,source_arrays_read=6))
    return files,b,pin


def test_roundtrip_counts_role_image_only_and_input_isolation(monkeypatch):
    files,b,pin=fixture();ca=c.InputCache(files,b,pin)
    im=ca.get('invented-0',role='train',operation='inference');assert 'target' not in im
    original=c.decode
    def checked(raw,kind):assert kind=='image';return original(raw,kind)
    monkeypatch.setattr(c,'decode',checked)
    assert ca.get('invented-1',role='validation',operation='inference')['image'].shape==(1,144,144,144)
    monkeypatch.setattr(c,'decode',original)
    ev=ca.get('invented-0',role='train',operation='evaluator');assert ev['target'][0,0,0]==2 and int((ev['target']==2).sum())==9
    assert (ca.get('invented-1',role='validation',operation='evaluator')['target']==2).sum()==0
    ev['transform']['source_shape'][0]=90;assert ca.get('invented-0',role='train',operation='inference')['transform']['source_shape']==[8]*3


@pytest.mark.parametrize('args',[('invented-0','train','optimizer'),('invented-1','validation','optimizer'),('invented-0','validation','inference'),('held','train','evaluator'),('invented-1',None,'inference')])
def test_denied_members_roles_and_operations_precede_array_decode(monkeypatch,args):
    files,b,pin=fixture();ca=c.InputCache(files,b,pin);monkeypatch.setattr(c,'decode',lambda *a:pytest.fail('Array decoded after denial'))
    with pytest.raises(ValueError):ca.get(args[0],role=args[1],operation=args[2])


@pytest.mark.parametrize('fault',['stale_pin','role','purpose','unknown','duplicate','transform_pin','wrong_head','class_counts','noninteger_counts','extra_field','wrong_source','recipe','lineage'])
def test_binding_faults_refused(fault):
    _,b,pin=fixture();d=b['entries'][0]['descriptor'];e=b['entries'][0]
    if fault=='stale_pin':b['cohort_completion_sha256']='d'*64
    if fault=='role':d['protected_role']='validation'
    if fault=='purpose':d['purpose']='pancreas_localizer_training'
    if fault=='unknown':d['lesion_target_state']='unknown'
    if fault=='duplicate':b['entries'].append(deepcopy(e))
    if fault=='transform_pin':e['transform_sha256']='d'*64
    if fault=='wrong_head':b['schema_version']='localizer-cache-1'
    if fault=='class_counts':e['tensor_class_counts'][1]+=1;e['tensor_class_counts'][0]-=1
    if fault=='noninteger_counts':e['tensor_class_counts'][0]=float(e['tensor_class_counts'][0])
    if fault=='extra_field':b['allow_optimizer']=True
    if fault=='wrong_source':e['transform']['source_identity']['study_id']='another';e['transform_sha256']=content_hash(e['transform'])
    if fault=='recipe':e['transform']['recipe']['margin_mm']=5;e['transform_sha256']=content_hash(e['transform'])
    if fault=='lineage':b['geometry_acceptance_sha256']='bad'
    if fault!='stale_pin':b['descriptor_sha256']=content_hash(b['records']);pin=content_hash(b)
    with pytest.raises(ValueError):c.checked_binding(b,pin)


@pytest.mark.parametrize('fault',['missing','extra','image_nan','target_code','wrong_shape','wrong_dtype','trailing','target_swap','wrong_production','wrong_binding'])
def test_payload_faults_refused(fault):
    files,b,pin=fixture();n='case-00-image.npy'
    if fault=='missing':files.pop(n)
    if fault=='extra':files['weights.pt']=b'unapproved'
    if fault=='image_nan':a=c.decode(files[n],'image');a[0,0,0,0]=np.nan;files[n]=c.encode(a)
    if fault=='target_code':a=c.decode(files['case-00-target.npy'],'target');a[0,0,0]=3;files['case-00-target.npy']=c.encode(a)
    if fault=='wrong_shape':files[n]=c.encode(np.zeros((1,1,1,1),np.float32))
    if fault=='wrong_dtype':files[n]=c.encode(np.zeros((1,144,144,144),np.float64))
    if fault=='trailing':files[n]+=b'ignored bytes'
    if fault=='target_swap':files['case-00-target.npy']=files['case-01-target.npy']
    if fault=='wrong_production':p=json.loads(files['production.json']);p['model_updates']=1;files['production.json']=canonical(p)
    if fault=='wrong_binding':files['binding.json']=b'{}'
    with pytest.raises(ValueError):c.validate(files,b,pin)


@pytest.mark.parametrize('shape,dtype', [((1,10**9,10**9,10**9),np.dtype('float32')),((1,144,144,144),np.dtype('O'))])
def test_header_checked_before_load_or_allocation(monkeypatch,shape,dtype):
    s=BytesIO();np.lib.format.write_array_header_1_0(s,dict(shape=shape,fortran_order=False,descr=np.lib.format.dtype_to_descr(dtype)))
    monkeypatch.setattr(np,'load',lambda *a,**k:pytest.fail('Unsafe header reached loader'))
    with pytest.raises(ValueError):c.decode(s.getvalue(),'image')


def test_completion_last_and_cold_semantic_replay(tmp_path):
    files,b,pin=fixture();st=ArtifactStore(tmp_path,check_root=lambda:None,max_bytes=64*1024**2,minimum_free_bytes=0)
    meta=dict(artifact_type='segmenter-input-cache',schema_version='1.0.0',component=c.VERSION,code_sha256='a'*64,parents=[],retention='scratch',sensitivity='invented',run_id='invented',stage_id='publish')
    validator=lambda f:c.validate(f,b,pin)
    receipt,status=st.publish('invented-cache',derivation_sha256=pin,files=files,metadata=meta,validate=validator);assert status=='published'
    loaded,r=st.resolve('invented-cache',receipt_sha256=receipt,expected_derivation=pin,validate=validator);assert loaded==files and len(r['members'])==6
    directory=tmp_path/digest(b'invented-cache');(directory/'case-00-target.npy').write_bytes(files['case-01-target.npy'])
    with pytest.raises(ValueError):st.resolve('invented-cache',receipt_sha256=receipt,validate=validator)


def test_failed_publication_never_becomes_resolvable(tmp_path):
    files,b,pin=fixture();st=ArtifactStore(tmp_path,check_root=lambda:None,max_bytes=64*1024**2,minimum_free_bytes=0);calls=0
    def validation(f):
        nonlocal calls
        calls+=1
        if calls==2:raise ValueError('injected persisted validation fault')
        return c.validate(f,b,pin)
    meta=dict(artifact_type='segmenter-input-cache',schema_version='1.0.0',component=c.VERSION,code_sha256='a'*64,parents=[],retention='scratch',sensitivity='invented',run_id='invented',stage_id='publish')
    with pytest.raises(ValueError):st.publish('invented-cache',derivation_sha256=pin,files=files,metadata=meta,validate=validation)
    assert not (tmp_path/digest(b'invented-cache')).exists() and list(tmp_path.glob('.attempt-*'))


def test_consumer_rejects_modified_cached_bytes():
    files,b,pin=fixture();ca=c.InputCache(files,b,pin);ca._files['case-00-image.npy']=files['case-01-image.npy']+b'x'
    with pytest.raises(ValueError):ca.get('invented-0',role='train',operation='inference')
