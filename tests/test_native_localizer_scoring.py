from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import pytest
from src.training.native_localizer_metrics import measure
from src.data.native_localizer_references import NativeReferences,ReadBudget,open_native_references
from src.data.manifest_records import digest
from test_twomm_localizer_inputs import scoped as old_scoped
from src.data import binary_label_policy

def scoped(path,operation="optimizer"):
    d,y,root=old_scoped(path,operation)
    d["mapping"]["policy_sha256"]=digest(Path(binary_label_policy.__file__).read_bytes())
    return d,y,root


def test_dense_prediction_is_measured_not_excluded():
    p=np.ones((180,180,180),np.uint8);y=np.zeros_like(p);y[0,0,0]=1
    r=measure(p,y,np.eye(4));assert r['predicted_voxels']==5832000 and r['recall']==1
    assert r['scan_fraction']==1 and not r['roi_diagnostic_pass'] and r['false_positive']==5831999


def test_96m_envelope_with_small_slabs():
    p=np.broadcast_to(np.uint8(1),(480,400,500));y=np.broadcast_to(np.uint8(1),p.shape)
    r=measure(p,y,np.eye(4));assert r['dice']==1 and r['predicted_voxels']==96000000


def test_empty_prediction_and_tiny_reference():
    p=np.zeros((20,30,40),np.uint8);y=p.copy();y[0,0,0]=1
    r=measure(p,y,np.eye(4));assert r['dice']==r['recall']==0 and r['precision'] is None
    assert r['box'] is None and not r['roi_diagnostic_pass']


def test_signed_permuted_spacing_box_and_counts():
    p=np.zeros((40,50,60),np.uint8);y=p.copy();p[20,20,20]=1;p[22,23,24]=1;y[20,20,20]=1;y[21,21,21]=1
    a=np.array([[0,-2,0,10],[3,0,0,-8],[0,0,-5,40],[0,0,0,1.]])
    r=measure(p,y,a)
    assert r['box']==[[16,15,18],[27,29,27]] and r['true_positive']==1
    assert r['false_positive']==r['false_negative']==1 and r['dice']==.5 and r['recall']==.5
    assert r['box_reference_coverage']==1 and r['scan_fraction']==11*14*9/(40*50*60)
    assert r['reference_volume_ml']==pytest.approx(.06)

@pytest.mark.parametrize('fault',['shape','nan','nonbinary','empty_reference','shear','oversize'])
def test_invalid_metrics_refused(fault):
    p=np.zeros((12,13,14),np.uint8);y=np.ones_like(p);a=np.eye(4)
    if fault=='shape':p=p[:-1]
    if fault=='nan':p=p.astype(float);p[0,0,0]=np.nan
    if fault=='nonbinary':p[0,0,0]=2
    if fault=='empty_reference':y[:]=0
    if fault=='shear':a[0,1]=.3
    if fault=='oversize':p=y=np.broadcast_to(np.uint8(1),(480,400,501))
    with pytest.raises(ValueError):measure(p,y,a)

@pytest.mark.parametrize('op',['optimizer','evaluator'])
def test_target_only_reads_and_roles(tmp_path,op):
    d,target,root=scoped(tmp_path,op)
    d['target_scope']='visible_reference_not_whole_organ'
    # Removing the CT proves this reader cannot depend on a CT load.
    (root/d['rows']['ct']['uri']).unlink()
    budget=ReadBudget([d]);ds=NativeReferences([d],root,lambda:None,budget,op)
    with pytest.raises(ValueError):ds.load(0,operation='evaluator' if op=='optimizer' else 'optimizer')
    y,a,receipt=ds.load(0,operation=op);np.testing.assert_array_equal(y,target)
    assert budget.files==1 and budget.expanded==1352 and len(budget.expected)==1
    assert receipt['scope']==('training_fit_diagnostic' if op=='optimizer' else 'development_validation')
    with pytest.raises(ValueError):ds.load(0,operation=op)

@pytest.mark.parametrize('fault',['hash','role','decoder','descriptor','expanded'])
def test_reference_mutations_refused(tmp_path,fault):
    d,_,root=scoped(tmp_path);d['target_scope']='visible_reference_not_whole_organ'
    if fault=='hash':d['target']['content_sha256']='0'*64
    if fault=='role':d['rows']['pancreas']['protected_role']='validation'
    if fault=='decoder':d['mapping']['policy_sha256']='0'*64
    if fault=='expanded':d['rows']['pancreas']['expanded_bytes']=1
    b=ReadBudget([d]);ds=NativeReferences([d],root,lambda:None,b,'optimizer')
    if fault=='descriptor':ds._items[0]['operation']='evaluator'
    with pytest.raises(ValueError):ds.load(0,operation='optimizer')


def test_old_paired_capability_rejected_before_resolution():
    raw=Path('docs/capstone/data/TWOMM-CACHE-INPUT-CAPABILITY-2026-09-30.json').read_bytes()
    with pytest.raises(ValueError,match='Unsupported read scope'):
        open_native_references(repo=Path.cwd(),capability_bytes=raw,trusted_capability_sha256=digest(raw),
            recipe_bytes=b'',trusted_recipe_sha256='',batch_id='pilot')

@pytest.mark.parametrize('fault',['affine','shape','source_bytes'])
def test_bad_native_reference_geometry_or_source(tmp_path,fault):
    d,_,root=scoped(tmp_path);d['target_scope']='visible_reference_not_whole_organ'
    if fault=='affine':d['geometry']['affine_ras'][3]+=1
    if fault=='shape':d['geometry']['shape_xyz'][0]+=1
    if fault=='source_bytes':(root/'pancreas.nii.gz').write_bytes(b'bad')
    ds=NativeReferences([d],root,lambda:None,ReadBudget([d]),'optimizer')
    with pytest.raises(ValueError):ds.load(0,operation='optimizer')


def test_job_summary_counts_empty_predictions():
    from scripts.diagnostics.native_localizer_scoring import summarize
    z=np.zeros((10,10,10),np.uint8);y=np.ones_like(z)
    rows=[dict(role=r,metrics=measure(p,y,np.eye(4))) for r in ('optimizer','evaluator') for p in (z,y)]
    s=summarize(rows)
    assert s['evaluator']['mean_recall']==.5 and s['evaluator']['empty_predictions']==1
    assert s['optimizer']['mean_box_reference_coverage_empty_as_zero']==.5


def test_prior_package_changed_or_incomplete_refused(tmp_path,monkeypatch):
    from scripts.diagnostics import native_localizer_scoring as job
    monkeypatch.setattr(job,'ROOT',tmp_path);p=tmp_path/'package';p.mkdir();(p/'x').write_bytes(b'xx')
    raw=json.dumps(dict(state='complete',files={'x':dict(bytes=2,sha256=digest(b'xx'))})).encode()
    (p/'receipt.json').write_bytes(raw);job.checked_package(p,digest(raw));(p/'x').write_bytes(b'changed')
    with pytest.raises(ValueError):job.checked_package(p,digest(raw))

@pytest.mark.parametrize('fault',[None,'scope','binding','capability','source','prior'])
def test_scoring_request_contract(tmp_path,monkeypatch,fault):
    from scripts.diagnostics import native_localizer_scoring as job
    from src.data.manifest_records import canonical
    monkeypatch.setattr(job,'ROOT',tmp_path);p=tmp_path/'request';p.mkdir()
    cap=canonical(dict(recipe_sha256=digest(b'recipe'),batches=[dict(batch_id='pilot',study_ids=[str(i) for i in range(8)])]))
    controls={'binding.json':b'binding','capability.json':cap,'recipe.json':b'recipe','source.json':b'source','environment.json':b'env'}
    monkeypatch.setattr(job,'BINDING_PIN',digest(b'binding'));monkeypatch.setattr(job,'CAP_PIN',digest(cap))
    monkeypatch.setattr(job,'capture',lambda:(b'source',b'env'))
    for n,b in controls.items():(p/n).write_bytes(b)
    r=dict(schema_version='native-score-1',approval='D-304',batch='pilot',limits=deepcopy(job.LIMITS),files={n:digest(b) for n,b in controls.items()},prior=None)
    if fault=='scope':r['approval']='D-300'
    if fault=='binding':r['files']['binding.json']='0'*64
    if fault=='capability':r['files']['capability.json']='0'*64
    if fault=='source':monkeypatch.setattr(job,'capture',lambda:(b'new',b'env'))
    if fault=='prior':r['prior']={}
    raw=canonical(r);(p/'request.json').write_bytes(raw)
    if fault:
        with pytest.raises(ValueError):job.checked_request(p,digest(raw))
    else:assert job.checked_request(p,digest(raw))==r


def test_scoring_consumed_batch_cannot_restart(tmp_path,monkeypatch):
    from scripts.diagnostics import native_localizer_scoring as job
    monkeypatch.setattr(job,'ROOT',tmp_path);monkeypatch.setattr(job,'checked_request',lambda *a:{'batch':'pilot'})
    monkeypatch.setattr(job,'power',lambda:(True,''))
    from types import SimpleNamespace
    monkeypatch.setattr(job.shutil,'disk_usage',lambda p:SimpleNamespace(free=200*1024**3))
    (tmp_path/('native-score-claim-'+job.CAP_PIN+'-pilot.json')).write_bytes(b'consumed')
    with pytest.raises(FileExistsError):job.run(tmp_path,'a'*64)


def test_scoring_worker_stage_cannot_restart(tmp_path,monkeypatch):
    from scripts.diagnostics import native_localizer_scoring as job
    monkeypatch.setattr(job,'checked_request',lambda *a:{'batch':'pilot'})
    (tmp_path/'consumed.json').write_text(json.dumps(dict(request_sha256='a'*64)))
    (tmp_path/'worker-started.json').write_bytes(b'old')
    with pytest.raises(FileExistsError):job.worker(tmp_path,'a'*64)
