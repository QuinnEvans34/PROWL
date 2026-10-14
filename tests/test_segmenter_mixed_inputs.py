import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest

from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import content_hash
from src.data.segmenter_geometry_v2 import recipe
from src.training.experiment_config import sha256
from src.data import segmenter_full_batch_v1 as B
from src.data import segmenter_mixed_inputs_v1 as M
from scripts.diagnostics.audit_panorama_setup import observation


def fixture(tmp_path, monkeypatch, mutate=lambda r:None):
    geometry=recipe(tensor_shape=(16,16,16))
    x=np.zeros((1,16,16,16),np.float32); y=np.zeros((16,16,16),np.uint8);y[2,2,2]=1;y[3,3,3]=2
    parent_control=dict(train=['pants-positive','pants-empty'], validation=['dev-positive','dev-empty']+sorted(M.EXCLUDED),
        target_states={n:'positive' for n in ['pants-positive','pants-empty','dev-positive','dev-empty']+sorted(M.EXCLUDED)})
    pin=digest(canonical(parent_control)); calls=[]
    def get(n,*,role,operation):
        calls.append((n,role,operation))
        return B.Batch(B._TOKEN,study_id=n,role=role,operation=operation,image=x,target=y,control_sha256=pin)
    fake=SimpleNamespace(control=parent_control,pin=pin,get=get,root=tmp_path,rows={},source={})
    import src.data.segmenter_prepared_inputs_v1 as P
    monkeypatch.setattr(P,'PreparedInputs',lambda cfg,r:fake)
    monkeypatch.setattr(M,'load_experiment',lambda p:{'full_segmenter':{'geometry':geometry}})
    name='panorama:study:100_1';cache=tmp_path/'100_1.npz'
    np.savez_compressed(cache,image=x,target=y)
    source=tmp_path/'source';source.write_bytes(b'unchanged')
    row=dict(study_id=name,subject_id='panorama:subject:100',reference_standard='histopathology',
        lesion_method='human_manual',pdac='positive',protected_role='unassigned',training_ready=False,
        disposition='expert_pdac_candidate_pending_qc_and_duplicates',ct={'path':str(source)})
    mutate(row)
    union=dict(geometry,roi_selection='pancreas_lesion_union')
    g=dict(transform=dict(recipe=union,roi_origin='provided_panorama_pancreas_lesion_union'))
    metadata=dict(study_id=name,subject_id=row['subject_id'],source=row,observations={'ct':list(observation(source))},
        cache=str(cache),cache_sha256=sha256(cache),geometry=g,geometry_sha256=content_hash(g),
        mechanical_survival_pass=True,tensor_lesion_voxels=1,tensor_pancreas_voxels=1,
        mapping='panorama_union_1_to_lesion_4_to_pancreas')
    meta=tmp_path/'100_1.json';meta.write_text(json.dumps(metadata))
    members={name:dict(cache=str(cache),cache_sha256=sha256(cache),metadata=str(meta),metadata_sha256=sha256(meta),subject_id=row['subject_id'])}
    train=tmp_path/'train.txt';train.write_text('\n'.join(parent_control['train']+[name]))
    dev=tmp_path/'dev.txt';dev.write_text('dev-positive\ndev-empty\n')
    manifest=tmp_path/'manifest.csv';manifest.write_text('case_id\n')
    states={n:parent_control['target_states'][n] for n in parent_control['train']+['dev-positive','dev-empty']};states[name]='positive'
    review=dict(domain=M.DOMAIN,decision='accepted',policy='declared_imports_excluded_five_dev_holds_exploratory',
        excluded_development=sorted(M.EXCLUDED),panorama_cache={'members':members},target_states=states,
        pants_parent={'experiment':'unused','file_sha256':{},'control_sha256':pin})
    rp=tmp_path/'review.json';rp.write_text(json.dumps(review))
    cfg={'_experiment':{'cohort':dict(review=str(rp),train_ids=str(train),development_ids=str(dev),manifest=str(manifest))}}
    return cfg,geometry,name,calls,x,y,source,cache,rp


def test_mixed_arrays_and_parent_identity_unchanged(tmp_path,monkeypatch):
    c,g,n,calls,x,y,*_=fixture(tmp_path,monkeypatch);p=M.MixedInputs(c,g)
    for name,role,operation in [('pants-positive','train','optimizer'),(n,'train','optimizer'),('dev-positive','validation','evaluator')]:
        a,b=p.get(name,role=role,operation=operation).checked(p.pin,operation,name)
        assert np.array_equal(a,x) and np.array_equal(b,y)
    assert calls==[('pants-positive','train','optimizer'),('dev-positive','validation','evaluator')]


@pytest.mark.parametrize('kind,value',[('reference_standard','MSD_dataset'),('reference_standard','NIH_dataset'),
    ('lesion_method','machine_generated'),('pdac','negative'),('protected_role','test'),('training_ready',True)])
def test_ineligible_panorama_rejected(tmp_path,monkeypatch,kind,value):
    c,g,*_=fixture(tmp_path,monkeypatch,lambda r:r.update({kind:value}))
    with pytest.raises(ValueError):M.MixedInputs(c,g)


@pytest.mark.parametrize('role,op',[('validation','evaluator'),('train','evaluator'),('validation','optimizer')])
def test_panorama_never_evaluates(tmp_path,monkeypatch,role,op):
    c,g,n,*_=fixture(tmp_path,monkeypatch);p=M.MixedInputs(c,g)
    with pytest.raises(ValueError):p.get(n,role=role,operation=op)


@pytest.mark.parametrize('name',sorted(M.EXCLUDED))
def test_five_holds_unreachable(tmp_path,monkeypatch,name):
    c,g,*_=fixture(tmp_path,monkeypatch);p=M.MixedInputs(c,g)
    for role,op in [('train','optimizer'),('validation','evaluator')]:
        with pytest.raises(ValueError):p.get(name,role=role,operation=op)


@pytest.mark.parametrize('which',[6,7])
def test_source_or_cache_change_refused(tmp_path,monkeypatch,which):
    f=fixture(tmp_path,monkeypatch);c,g,n=f[:3];p=M.MixedInputs(c,g)
    f[which].write_bytes(b'changed')
    with pytest.raises(ValueError):p.get(n,role='train',operation='optimizer')


def test_development_membership_change_refused(tmp_path,monkeypatch):
    c,g,*_=fixture(tmp_path,monkeypatch)
    Path(c['_experiment']['cohort']['development_ids']).write_text('dev-positive\n'+sorted(M.EXCLUDED)[0])
    with pytest.raises(ValueError):M.MixedInputs(c,g)


def test_unapproved_domain_cannot_extend_roles():
    assert M.extra_training({'domain':'other'})==set()
    with pytest.raises(ValueError):M.extra_training({'domain':M.DOMAIN})
