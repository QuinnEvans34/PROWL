import csv
import json
from pathlib import Path
import nibabel as nib
import numpy as np
import pytest
from src.data.manifest_records import canonical
from src.data.segmenter_full_inputs_v1 import Inputs
from src.data.segmenter_geometry_v2 import recipe
from src.data.segmenter_cache_continuation import validate_parent
from scripts.prepare_full_segmenter_cache import worker


@pytest.fixture
def interrupted(tmp_path):
    rows=[]
    for name in ('t','v'):
        row=dict(case_id=name,historical_has_lesion='True')
        pancreas=np.zeros((24,)*3,np.uint8);pancreas[4:20,4:20,4:20]=1
        lesion=np.zeros_like(pancreas);lesion[10:14,10:14,10:14]=1
        for kind,data in [('ct',pancreas.astype(np.float32)*100),('pancreas',pancreas),('lesion',lesion)]:
            path=tmp_path/(name+'-'+kind+'.nii.gz');nib.save(nib.Nifti1Image(data,np.eye(4)),path)
            row[kind+'_path']=str(path)
        rows.append(row)
    manifest=tmp_path/'manifest.csv'
    with manifest.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    train=tmp_path/'train.txt';train.write_text('t\n');dev=tmp_path/'dev.txt';dev.write_text('v\n')
    geometry=recipe(tensor_shape=(16,16,16));cache=tmp_path/'cache'
    cfg=dict(_experiment=dict(cohort=dict(manifest=str(manifest),train_ids=str(train),
        development_ids=str(dev),review=None)),full_segmenter=dict(geometry=geometry,cache_dir=str(cache)))
    provider=Inputs(cfg,geometry,cache_dir=cache,audit_only=True)
    batch=provider.get('t',role='train',operation='evaluator')
    parent=tmp_path/'parent';parent.mkdir()
    (parent/'input-control.json').write_bytes(canonical(provider.control))
    (parent/'request.json').write_text(json.dumps(dict(config=cfg)))
    (parent/'resources.json').write_text(json.dumps(dict(workers_reaped=True)))
    row=dict(case_id='t',role='train',status='technical_pass',target_state='positive',
             cache_path=str(provider.cache/'t.npz'),batch_sha256=batch.hashes(),elapsed_seconds=1)
    (parent/'cases.jsonl').write_text(json.dumps(row)+'\n')
    return cfg,provider,parent


def test_continuation_reuses_without_preprocessing_and_preserves_parent(interrupted,tmp_path,monkeypatch):
    cfg,p,parent=interrupted
    before={f.name:f.read_bytes() for f in parent.iterdir()}
    payload=(p.cache/'t.npz').read_bytes();meta=(p.cache/'t.json').read_bytes()
    original=Inputs.prepare;seen=[]
    def tracked(self,name):
        assert name!='t','Completed source was decoded again'
        seen.append(name);return original(self,name)
    monkeypatch.setattr(Inputs,'prepare',tracked)
    monkeypatch.setattr('src.training.experiment_config.load_experiment',lambda _:cfg)
    output=tmp_path/'continued';output.mkdir();worker('unused',output,parent)
    assert seen==['v']
    assert json.loads((output/'summary.json').read_text())['passed']==2
    assert {f.name:f.read_bytes() for f in parent.iterdir()}==before
    assert (p.cache/'t.npz').read_bytes()==payload and (p.cache/'t.json').read_bytes()==meta


@pytest.mark.parametrize('fault',['reaped','config','control','duplicate','failure','missing','orphan','completed'])
def test_parent_fault_refused(interrupted,fault):
    cfg,p,parent=interrupted
    if fault=='reaped':(parent/'resources.json').write_text('{"workers_reaped":false}')
    elif fault=='config':(parent/'request.json').write_text('{"config":{}}')
    elif fault=='control':(parent/'input-control.json').write_text('{}')
    elif fault=='duplicate':
        f=parent/'cases.jsonl';f.write_text(f.read_text()*2)
    elif fault=='failure':
        f=parent/'cases.jsonl';r=json.loads(f.read_text());r['status']='technical_failure';f.write_text(json.dumps(r)+'\n')
    elif fault=='missing':(p.cache/'t.npz').unlink()
    elif fault=='orphan':(p.cache/'unknown.tmp').write_bytes(b'partial')
    elif fault=='completed':(parent/'summary.json').write_text('{}')
    with pytest.raises(ValueError):validate_parent(parent,p,cfg)


def test_changed_observation_cannot_continue(interrupted):
    cfg,p,parent=interrupted
    Path(p.rows['t']['ct_path']).touch()
    with pytest.raises((ValueError,FileNotFoundError)):
        Inputs(cfg,p.recipe,cache_dir=p.cache.parent,audit_only=True,resume_cache=True)


def test_corrupt_reused_cache_never_recomputed(interrupted,tmp_path,monkeypatch):
    cfg,p,parent=interrupted
    with (p.cache/'t.npz').open('ab') as f:f.write(b'corruption')
    monkeypatch.setattr(Inputs,'prepare',lambda *a:pytest.fail('No recomputation allowed'))
    monkeypatch.setattr('src.training.experiment_config.load_experiment',lambda _:cfg)
    output=tmp_path/'failed';output.mkdir()
    with pytest.raises(ValueError,match='Continuation failed'):worker('unused',output,parent)
    assert not (output/'summary.json').exists()
