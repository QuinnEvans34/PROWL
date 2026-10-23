import json
from pathlib import Path
import pytest
from scripts.diagnostics import setup_panorama_positive_training as S


def arrange(tmp_path,monkeypatch,*,reaped=True,complete=True):
    from src.operations import full_training_platform as P
    from contextlib import nullcontext
    root=tmp_path/'repo';out=tmp_path/'out';root.mkdir();out.mkdir()
    for d in ('src','scripts'):(root/d).mkdir()
    spec=root/'spec.json';spec.write_text('{}')
    for f in ('selection.json','parent-reduced-comparison.json'):(out/f).write_text('{}')
    (out/'development.txt').write_text('dev')
    (out/'cache-resources.json').write_text(json.dumps({'workers_reaped':reaped}))
    if complete:(out/'cache-complete.json').write_text('{}')
    for k,v in dict(ROOT=root,OUT=out,SPEC=spec,SMOKE=out/'smoke',SMOKE_BACKUP=tmp_path/'backup',CONFIG=out/'config.yaml').items():
        monkeypatch.setattr(S,k,v)
    monkeypatch.setattr(P,'training_guard',lambda p:nullcontext())
    monkeypatch.setattr(P,'require_ac',lambda:None)
    return out


@pytest.mark.parametrize('reaped,complete',[(False,True),(True,False)])
def test_no_training_without_complete_reaped_cache(tmp_path,monkeypatch,reaped,complete):
    out=arrange(tmp_path,monkeypatch,reaped=reaped,complete=complete);calls=[]
    monkeypatch.setattr(S.subprocess,'run',lambda *a,**k:calls.append(a))
    with pytest.raises(ValueError):S.pipeline()
    assert not calls and 'failed' in (out/'pipeline.jsonl').read_text()


def test_failed_production_binding_never_launches(tmp_path,monkeypatch):
    out=arrange(tmp_path,monkeypatch);calls=[]
    def fail(stage,seconds):raise ValueError('injected binding failure')
    monkeypatch.setattr(S,'supervised',fail)
    monkeypatch.setattr(S.subprocess,'run',lambda *a,**k:calls.append(a))
    with pytest.raises(ValueError,match='injected'):S.pipeline()
    assert not calls and 'injected binding failure' in (out/'pipeline.jsonl').read_text()


def test_changed_code_stops_before_binding(tmp_path,monkeypatch):
    out=arrange(tmp_path,monkeypatch);calls=[]
    original=S.read
    def changed(p):
        result=original(p)
        if Path(p).name=='cache-resources.json':S.SPEC.write_text('changed')
        return result
    monkeypatch.setattr(S,'read',changed)
    monkeypatch.setattr(S,'supervised',lambda *a:calls.append(a))
    with pytest.raises(ValueError,match='Producing code'):S.pipeline()
    assert not calls


def test_cache_construction_matches_audited_geometry(tmp_path,monkeypatch):
    import nibabel as nib
    import numpy as np
    from scripts.diagnostics import prepare_panorama_positive_run as P
    from src.data.panorama_geometry import preprocess
    from src.data.segmenter_geometry_v2 import recipe
    out=tmp_path/'out';cache=tmp_path/'cache';base=tmp_path/'base'
    out.mkdir();cache.mkdir();(base/'panorama-ct-union-a01').mkdir(parents=True)
    for k,v in dict(OUT=out,CACHE=cache,BASE=base).items():monkeypatch.setattr(P,k,v)
    geometry=recipe(tensor_shape=(16,16,16));image=np.zeros((16,16,16),np.float32)
    target=np.zeros((16,16,16),np.uint8);target[3:13,3:13,3:13]=4;target[6:10,6:10,6:10]=1
    ct=tmp_path/'ct.nii.gz';label=tmp_path/'label.nii.gz'
    nib.save(nib.Nifti1Image(image,np.eye(4)),ct);nib.save(nib.Nifti1Image(target,np.eye(4)),label)
    name='panorama:study:1_1'
    row=dict(study_id=name,subject_id='panorama:subject:1',publisher_study_id='1_1',
        ct={'path':str(ct),'expected_sha256':P.sha(ct)},label={'path':str(label),'expected_sha256':P.sha(label)})
    derived=preprocess(image,target,np.eye(4),geometry,source_identity={'study_id':name,'ct_sha256':P.sha(ct)},diagnosis='PDAC')
    P.save(out/'selection.json',{'rows':[row],'geometry':geometry})
    (base/'panorama-ct-union-a01/cases.jsonl').write_text(json.dumps({'study_id':name,'geometry_sha256':derived['geometry_sha256']})+'\n')
    P.worker()
    complete=P.read(out/'cache-complete.json')
    assert complete['completed'] and complete['cases']==1
    with np.load(cache/'1_1.npz') as data:
        assert np.array_equal(data['image'],derived['image'][None])
        assert np.array_equal(data['target'],derived['target'])


def test_native_parent_exclusions_leave_old_reports_unchanged():
    # Explicit list is provenance based; it must not silently grow in an outcome-driven edit.
    from src.data.segmenter_mixed_inputs_v1 import EXCLUDED
    from scripts.diagnostics.prepare_panorama_positive_run import EXCLUDED as preparation
    assert set(preparation)==EXCLUDED and len(EXCLUDED)==5
