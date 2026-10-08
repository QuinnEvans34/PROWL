"""Full-cohort mechanics on invented CPU data only; no actual source qualification."""
import csv
import json
from copy import deepcopy
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
import torch

from src.data import segmenter_training_inputs_v1 as boundary
from src.data.manifest_records import canonical, digest
from src.data.segmenter_geometry_v2 import recipe
from src.data.segmenter_full_inputs_v1 import Inputs
from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
from src.training.experiment_config import sha256
from src.training.segmenter_full_session_v1 import Session, validate_config
from src.training.segmenter_full_executor_v1 import execute
from scripts.prepare_full_segmenter_inputs import prepare


def config(steps=4):
    return dict(max_steps=steps, tensor_shape=[16]*3, seed=42, learning_rate=.0001,
                weight_decay=.00001, warmup_steps=0, lr_schedule='warmup_cosine')


class Invented:
    def __init__(self):
        self.control = dict(train=[f't{i}' for i in range(9)], validation=['v0', 'v1'])
        self.x = np.zeros((1, 16, 16, 16), np.float32)
        self.y = np.zeros((16, 16, 16), np.uint8)
        self.y[3:13, 3:13, 3:13] = 1; self.y[6:9, 6:9, 6:9] = 2
        self.x[0] = self.y / 2

    def get(self, name, *, role, operation):
        return boundary.Batch(boundary._TOKEN, study_id=name, role=role, operation=operation,
            image=self.x, target=self.y, control_sha256=digest(canonical(self.control)))


def session(provider, steps=4):
    return Session(config(steps), provider.control, device='cpu', initialization={'kind':'scratch'})


@pytest.mark.parametrize('steps', [24000, 72000, 100000])
def test_long_horizon(steps):
    validate_config(config(steps))


def test_full_epoch_and_role_guards():
    p = Invented(); s = session(p, 20)
    observed = []
    for step in range(9):
        s.step = step; observed.append(s.next_member())
    assert set(observed) == set(p.control['train']) and len(set(observed)) == 9
    with pytest.raises(ValueError, match='role'): s._batch(p, 'v0', 'train', 'optimizer')
    p.control['train'].append('injected')
    with pytest.raises(ValueError, match='cohort'): s._batch(p, 't0', 'train', 'optimizer')


def test_updates_checkpoint_recovery_and_executor(tmp_path):
    torch.set_num_threads(2)
    p = Invented(); s = session(p)
    s.update(p)
    restored = Session.restore(deepcopy(s.state()), s.identity)
    left, right = s.update(p), restored.update(p)
    assert left == right
    assert all(torch.equal(a, restored.model.state_dict()[k]) for k, a in s.model.state_dict().items())
    result = execute(s, p, tmp_path / 'run', validate_every=3, checkpoint_every=1)
    assert result['completed_updates'] == 4
    records = [json.loads(l) for l in (tmp_path/'run/history.jsonl').read_text().splitlines()]
    assert [r['step'] for r in records if r['event']=='validation'] == [3, 4]
    for name in ('initial.pt', 'best.pt', 'last.pt'):
        state = torch.load(tmp_path/'run'/name, weights_only=True)
        recovered = Session.restore(state['session'], s.identity)
        assert recovered.step >= 2
    with pytest.raises(FileExistsError): execute(s, p, tmp_path/'run', validate_every=1, checkpoint_every=1)


def test_dirty_session_cannot_checkpoint_or_advance():
    p = Invented(); s = session(p); s.dirty = True
    with pytest.raises(ValueError, match='Dirty'): s.state()
    with pytest.raises(ValueError, match='Dirty'): s.update(p)


def test_incomplete_optimizer_restore_refused():
    p=Invented();s=session(p);s.update(p)
    state=s.state();state['optimizer']['state'].pop(next(iter(state['optimizer']['state'])))
    with pytest.raises(ValueError,match='Incomplete optimizer'):Session.restore(state,s.identity)


def test_real_provider_on_invented_nifti(tmp_path):
    p = Invented(); rows = []
    for name in ('t', 'v'):
        row = {'case_id':name,'historical_has_lesion':'True'}
        for kind, data in [('ct', p.x[0]*100), ('pancreas', (p.y>0).astype(np.uint8)),
                           ('lesion', (p.y==2).astype(np.uint8))]:
            path=tmp_path/f'{name}-{kind}.nii.gz'; nib.save(nib.Nifti1Image(data, np.eye(4)),path)
            row[kind+'_path']=str(path)
        rows.append(row)
    manifest=tmp_path/'manifest.csv'
    with manifest.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    train=tmp_path/'train.txt';train.write_text('t\n')
    dev=tmp_path/'dev.txt';dev.write_text('v\n')
    review=tmp_path/'review.json'; review.write_text(json.dumps({'target_states':{'t':'positive','v':'positive'}}))
    cfg={'_experiment':{'cohort':dict(review=str(review),manifest=str(manifest),train_ids=str(train),development_ids=str(dev))}}
    provider=Inputs(cfg,recipe(tensor_shape=(16,16,16)),cache_dir=tmp_path/'cache')
    a=provider.get('t',role='train',operation='optimizer'); b=provider.get('t',role='train',operation='optimizer')
    assert a.hashes()==b.hashes() and a.image.shape==(1,16,16,16) and (a.target==2).any()
    with pytest.raises(ValueError,match='role'):provider.get('v',role='validation',operation='optimizer')
    candidate=Inputs(cfg,recipe(tensor_shape=(16,16,16)),audit_only=True,cache_dir=tmp_path/'audit-cache')
    with pytest.raises(ValueError,match='audit'):candidate.get('t',role='train',operation='optimizer')
    for name,role in [('t','train'),('v','validation')]:candidate.get(name,role=role,operation='evaluator')
    reviewed=dict(decision='accepted',evidence=['invented fixture content'],target_states={'t':'positive','v':'positive'},
        prepared_cache=dict(root=str(candidate.cache),control_sha256=sha256(candidate.cache/'control.json'),
            members={n:dict(cache_sha256=sha256(candidate.cache/(n+'.npz')),
                           metadata_sha256=sha256(candidate.cache/(n+'.json'))) for n in ('t','v')}))
    review.write_text(json.dumps(reviewed))
    prepared=PreparedInputs(cfg,recipe(tensor_shape=(16,16,16)))
    assert prepared.get('t',role='train',operation='optimizer').hashes()==a.hashes()
    with pytest.raises(ValueError,match='role'):prepared.get('v',role='validation',operation='optimizer')
    with (candidate.cache/'t.npz').open('ab') as stream:stream.write(b'corruption')
    with pytest.raises(ValueError,match='cache changed'):prepared.get('t',role='train',operation='optimizer')
    Path(rows[0]['ct_path']).touch()
    with pytest.raises(ValueError,match='changed'):provider.get('t',role='train',operation='optimizer')


def test_manifest_preparation_preserves_unknown_and_roles(tmp_path):
    names=['PanTS_00000001','PanTS_00000002','PanTS_00009001']
    files=[]
    for index,name in enumerate(names):
        p=tmp_path/f'ids{index}';p.write_text(name+'\n');files.append(p)
    hist=tmp_path/'historical.csv';hist.write_text('case_id,has_lesion\n'+names[0]+',False\n'+names[1]+',True\n')
    report=prepare(tmp_path/'source',hist,files[0],files[1],files[0],files[1],files[2],tmp_path/'out')
    assert len(report['missing'])==6 and report['payloads_decoded']==0
    assert 'unreviewed' in (tmp_path/'out/manifest.csv').read_text()
    with pytest.raises(ValueError,match='Development'):
        prepare(tmp_path/'source',hist,files[0],files[0],files[0],files[1],files[2],tmp_path/'bad')
