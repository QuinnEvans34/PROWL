from copy import deepcopy
import json
import numpy as np
import pytest
from scripts.diagnostics import segmenter_geometry_qualification as q
from src.data import segmenter_geometry_v1 as g
from src.data.source_inventory_records import content_hash


def out():
    ct=np.zeros((9,11,7),np.float32);p=np.ones_like(ct,np.uint8);l=np.zeros_like(p);l[3:5,4:6,3]=1
    r=g.preprocess(ct,p,l,np.eye(4),g.recipe(tensor_shape=(9,11,7),margin_mm=0),
        source_identity=dict(study_id='invented',ct_sha256='a'*64),lesion_target_state='positive')
    return r,p,l


def test_probability_probe_and_fixed_prospective_screen():
    r,p,l=out();mask,probe=q.probability_check(r,lambda:None);error=q.landmark_check(r['transform'])
    assert mask.shape==p.shape and probe['source_grid_exact'] and error<1e-5
    assert q.screen(r['fidelity'],mask,p,l,error)['passed']
    bad=deepcopy(r['fidelity']);bad['components'][0]['roundtrip_recall']=.89
    assert not q.screen(bad,mask,p,l,error)['passed']
    assert not q.screen(r['fidelity'],np.zeros_like(mask),p,l,error)['passed']
    assert not q.screen(r['fidelity'],mask,p,l,.1)['passed']


@pytest.mark.parametrize('field',['tensor_affine','pad_low','effective_spacing_mm','roi_world_low_edge_mm'])
def test_independent_landmark_oracle_catches_geometry_faults(field):
    r,_,_=out();t=deepcopy(r['transform'])
    if field=='tensor_affine':t[field][0][3]+=1
    else:t[field][0]+=1
    with pytest.raises(ValueError,match='landmark'):q.landmark_check(t)


def test_tiny_target_erased_at_coarse_resolution_remains_an_accounted_recipe_failure():
    shape=(30,30,30);ct=np.zeros(shape,np.float32);p=np.ones(shape,np.uint8);l=np.zeros_like(p);l[1,1,1]=1
    result=g.preprocess(ct,p,l,np.eye(4),g.recipe(tensor_shape=(2,2,2),margin_mm=0),
        source_identity=dict(study_id='invented',ct_sha256='a'*64),lesion_target_state='positive')
    f=result['fidelity'];assert f['metrics']['lesion']['native_voxels']==1 and f['source_component_count']==1
    assert not f['mechanical_survival_pass'] and f['lost_or_displaced_component_ids']==[1]
    assert f['lesion_target_state']=='positive' and f['components'][0]['tensor_voxels']==0


@pytest.mark.parametrize('fault',['wrong_role','missing_file','extra_case','changed_code','changed_recipe','wrong_profile'])
def test_scope_changed_request_fails_before_claim_or_source_open(tmp_path,monkeypatch,fault):
    dest=tmp_path/'fixed';dest.mkdir();good=dict(scope_receipt_sha256='scope',profile_receipt_sha256='profile',
        cases=['a','b'],files=[dict(role='train'),dict(role='validation')],code_pins={'x':'original'},recipe={'shape':144})
    bad=deepcopy(good)
    if fault=='wrong_role':bad['files'][0]['role']='test'
    if fault=='missing_file':bad['files'].pop()
    if fault=='extra_case':bad['cases'].append('held')
    if fault=='changed_code':bad['code_pins']['x']='new'
    if fault=='changed_recipe':bad['recipe']['shape']=192
    if fault=='wrong_profile':bad['profile_receipt_sha256']='other'
    monkeypatch.setattr(q,'DEST',dest);monkeypatch.setattr(q,'build_request',lambda *args:good)
    q.source.put(dest/'request.json',bad)
    with pytest.raises(ValueError):q.run(q.source.sha((dest/'request.json').read_bytes()))
    assert not (dest/'consumed.json').exists()


def test_consumed_request_refuses_repeat_launch_before_supervisor(tmp_path,monkeypatch):
    monkeypatch.setattr(q,'DEST',tmp_path);(tmp_path/'consumed.json').write_text('{}')
    monkeypatch.setattr(q,'checked_request',lambda _:dict(limits={}))
    monkeypatch.setattr(q.prior,'supervise',lambda *args:pytest.fail('Rerun after consumed marker'))
    with pytest.raises(FileExistsError):q.run('already-consumed')


def test_reported_request_pin_is_exact_persisted_transport_bytes(tmp_path,monkeypatch,capsys):
    dest=tmp_path/'new';monkeypatch.setattr(q,'DEST',dest)
    request=dict(cases=['invented'],limits={'seconds':1},code_pins={'invented':'a'*64},scope_receipt_sha256='scope',profile_receipt_sha256='profile')
    monkeypatch.setattr(q,'build_request',lambda *args:request)
    q.prepare('scope','profile');report=json.loads(capsys.readouterr().out)
    assert report['request_sha256']==q.source.sha((dest/'request.json').read_bytes())
    assert report['request_sha256']!=content_hash(request) # compact transport has no canonical newline
    assert q.checked_request(report['request_sha256'])==request
