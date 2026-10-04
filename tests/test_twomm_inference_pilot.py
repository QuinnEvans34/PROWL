from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import time
import numpy as np
import nibabel as nib
import pytest
import torch
from scripts.diagnostics import twomm_inference_pilot as pilot
from src.data.manifest_records import canonical,digest
from src.data.localizer_preprocessing_v4 import preprocess
from src.training.twomm_inference_export import export_prediction,verify_export
from src.training.twomm_adapter import pad_image,remove_padding
from test_twomm_cache_adapter import config

@pytest.fixture
def export_fixture():
    torch.set_num_threads(2)
    recipe=json.loads(Path('configs/capstone/localizer-preprocessing-v4.json').read_bytes())
    y=np.zeros((15,19,17),np.uint8);y[3:12,4:15,5:13]=1
    affine=np.array([[-1.5,0,0,20],[0,2.5,0,-10],[0,0,3.5,8],[0,0,0,1.]])
    a=preprocess(y.astype(np.float32)*300-100,affine,recipe,target=y)
    b=preprocess(y.astype(np.float32)*300-100,affine,recipe)
    assert torch.equal(a['image'],b['image']) and a['transform_record']==b['transform_record']
    label=a['label'].as_tensor().float();return torch.cat([1-label,label]),a['transform_record']


def test_anisotropic_flipped_export_roundtrip(tmp_path,export_fixture):
    probability,record=export_fixture;p=tmp_path/'mask.nii.gz'
    row=export_prediction(p,probability,record)
    assert row['foreground']>0 and row['shape']==[15,19,17]
    assert np.array_equal(nib.load(p).affine,record['source_affine'])
    with pytest.raises(ValueError,match='Fresh'):export_prediction(p,probability,record)

@pytest.mark.parametrize('fault',['bytes','affine','shape','foreground','units'])
def test_export_corruption_refused(tmp_path,export_fixture,fault):
    probability,record=export_fixture;p=tmp_path/'mask.nii.gz';row=export_prediction(p,probability,record)
    if fault=='bytes':p.write_bytes(b'bad')
    if fault=='affine':record['source_affine'][0][3]+=1
    if fault=='shape':record['source_shape'][0]+=1
    if fault=='foreground':row['foreground']+=1
    if fault=='units':
        im=nib.load(p);im.header.set_xyzt_units('meter');nib.save(im,p);row['sha256']=digest(p.read_bytes())
    with pytest.raises(ValueError):verify_export(p,record,expected_sha256=row['sha256'],expected_foreground=row['foreground'])

@pytest.mark.parametrize('fault',['nan','sum','shape'])
def test_invalid_probabilities_before_export(tmp_path,export_fixture,fault):
    p,r=export_fixture;p=p.clone()
    if fault=='nan':p[0,0,0,0]=float('nan')
    if fault=='sum':p.zero_()
    if fault=='shape':p=p[:,:-1]
    with pytest.raises(ValueError):export_prediction(tmp_path/'mask.nii.gz',p,r)
    assert not list(tmp_path.iterdir())


def test_asymmetric_patch_unpadding_does_not_shift_prediction():
    x=torch.zeros((1,97,146,101));x[:,4,33,8]=1
    padded,trace=pad_image(x,config())
    assert trace['padding']==[21,22,0,0,23,24]
    p=torch.cat([1-padded,padded]);restored=remove_padding(p,trace)
    assert torch.equal(restored[1],x[0])

@pytest.fixture
def pilot_request(tmp_path,monkeypatch):
    monkeypatch.setattr(pilot,'ROOT',tmp_path)
    dest=tmp_path/'twomm-session-pilot-test';dest.mkdir()
    roles={r:[{'descriptor':{'study_id':f'other-{r}-{i}'}} for i in range(113 if r=='optimizer' else 40)] for r in ('optimizer','evaluator')}
    for c in pilot.CASES:
        roles[c['role']][c['index']]={'descriptor':dict(study_id=c['study_id'],operation=c['role'],protected_role='train' if c['role']=='optimizer' else 'validation')}
    inputs=canonical(dict(roles=roles));monkeypatch.setattr(pilot,'BINDING_PIN',digest(inputs))
    controls={'inputs.json':inputs,'source.json':b'source','environment.json':b'env'}
    for n,b in controls.items():(dest/n).write_bytes(b)
    r=dict(schema_version='twomm-pilot-1',approval='D-302',operation='eight-case-zero-update-inference',
        cache=str(pilot.CACHE),cache_pin=pilot.CACHE_PIN,binding_pin=pilot.BINDING_PIN,cases=deepcopy(pilot.CASES),
        limits=deepcopy(pilot.LIMITS),config=pilot.config(),files={n:digest(b) for n,b in controls.items()},
        storage_ceilings=[100,200],run_id=dest.name)
    monkeypatch.setattr(pilot,'capture',lambda:(b'source',b'env'))
    (dest/'request.json').write_bytes(canonical(r));return dest,r


def test_single_use_consumed_before_work(pilot_request):
    dest,r=pilot_request;pin=digest(canonical(r));pilot.checked_request(dest,pin);pilot.claim(dest,pin)
    with pytest.raises(FileExistsError):pilot.claim(dest,pin)

@pytest.mark.parametrize('fault',['role','index','member','cache','config','limits','binding','source','env','pin'])
def test_changed_request_or_controls_refused(pilot_request,fault):
    dest,r=pilot_request;pin=digest(canonical(r))
    if fault=='role':r['cases'][0]['role']='evaluator'
    if fault=='index':r['cases'][0]['index']=0
    if fault=='member':r['cases'][0]['study_id']='other'
    if fault=='cache':r['cache_pin']='0'*64
    if fault=='config':r['config']['patch_size']=[96]*3
    if fault=='limits':r['limits']['rss_bytes']*=2
    if fault=='binding':r['binding_pin']='0'*64
    if fault=='source':(dest/'source.json').write_bytes(b'changed')
    if fault=='env':(dest/'environment.json').write_bytes(b'changed')
    (dest/'request.json').write_bytes(canonical(r))
    if fault!='pin':pin=digest(canonical(r))
    else:pin='0'*64
    with pytest.raises(ValueError):pilot.checked_request(dest,pin)

@pytest.mark.parametrize('kwargs,reason',[
    ({'elapsed':1200},'time_cap'),({'rss':17*1024**3},'rss_cap'),({'output':2*1024**3},'output_cap'),
    ({'free':0},'free_floor'),({'ac':False},'AC_lost')])
def test_resource_stop(kwargs,reason):
    args=dict(elapsed=0,rss=0,output=0,free=200*1024**3,ac=True);args.update(kwargs)
    assert pilot.stop_reason(**args)==reason


def test_interrupted_supervisor_terminates_and_preserves_failure(tmp_path,monkeypatch):
    class Process:
        pid=123;returncode=None;terminated=False
        def poll(self):return self.returncode
        def terminate(self):self.terminated=True;self.returncode=-15
        def wait(self,timeout):return self.returncode
    proc=Process();monkeypatch.setattr(pilot.subprocess,'Popen',lambda *a,**k:proc)
    monkeypatch.setattr(pilot.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='10'))
    monkeypatch.setattr(pilot,'power',lambda:(True,''))
    monkeypatch.setattr(pilot.shutil,'disk_usage',lambda p:SimpleNamespace(free=200*1024**3))
    def interrupted(n):raise KeyboardInterrupt()
    monkeypatch.setattr(pilot.time,'sleep',interrupted)
    with pytest.raises(KeyboardInterrupt):pilot.supervise(tmp_path,'a'*64,'profile',deadline=time.monotonic()+1200)
    assert proc.terminated and not (tmp_path/'receipt.json').exists()
    assert json.loads((tmp_path/'profile-supervisor.json').read_bytes())['reason']=='KeyboardInterrupt'



def test_changed_current_code_refused(pilot_request,monkeypatch):
    dest,r=pilot_request
    monkeypatch.setattr(pilot,'capture',lambda:(b'new source',b'env'))
    with pytest.raises(ValueError,match='drift'):pilot.checked_request(dest,digest(canonical(r)))


def test_binding_role_disagreement_refused_even_with_new_pins(pilot_request,monkeypatch):
    dest,r=pilot_request;b=json.loads((dest/'inputs.json').read_bytes())
    c=pilot.CASES[0];b['roles'][c['role']][c['index']]['descriptor']['protected_role']='validation'
    raw=canonical(b);pin=digest(raw);(dest/'inputs.json').write_bytes(raw)
    monkeypatch.setattr(pilot,'BINDING_PIN',pin);r['binding_pin']=pin;r['files']['inputs.json']=pin
    (dest/'request.json').write_bytes(canonical(r))
    with pytest.raises(ValueError,match='role/index'):pilot.checked_request(dest,digest(canonical(r)))


def test_consumed_worker_stage_cannot_reexecute(pilot_request):
    dest,r=pilot_request;pin=digest(canonical(r));pilot.claim(dest,pin)
    (dest/'profile-started.json').write_bytes(b'prior attempt')
    with pytest.raises(FileExistsError):pilot.worker(dest,pin,'profile')


def test_raw_sources_blocked():
    with pytest.raises(ValueError,match='Raw source'):pilot.no_raw_reads('open',('/Volumes/PROWL-Data/PROWL/sources/pants/anything',))
    pilot.no_raw_reads('open',('/tmp/fixture',))
