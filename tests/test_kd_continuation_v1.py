import json
import shutil
import pytest
import torch
from src.operations.kd_continuation_v1 import inspect_checkpoint, remaining_budget
from src.data.manifest_records import canonical


def fixture(tmp_path):
    run=tmp_path/'run';backup=tmp_path/'backup';run.mkdir();backup.mkdir()
    identity={'invented':True}
    rows=[dict(event='started',step=0,identity=identity)]+[dict(event='update',step=i) for i in range(1,5)]
    prefix=b''.join(canonical(r) for r in rows)
    (run/'history.jsonl').write_bytes(prefix)
    saved=dict(session=dict(identity=identity,student={'raw':{'step':4}}),best_score=None,history_bytes=len(prefix))
    torch.save(saved,run/'last.pt');shutil.copyfile(run/'last.pt',backup/'last.pt')
    return run,backup


def test_pending_validation_and_suffix_are_distinguished(tmp_path):
    run,backup=fixture(tmp_path)
    with (run/'history.jsonl').open('ab') as f:f.write(canonical(dict(event='failed',step=5)))
    r=inspect_checkpoint(run,backup,'last.pt',validate_every=4)
    assert r['step']==4 and r['pending_validation'] and r['selected_step'] is None
    assert r['scientific_ready'] is False


@pytest.mark.parametrize('fault',['checkpoint','journal','sequence'])
def test_bad_checkpoint_or_prefix_rejected(tmp_path,fault):
    run,backup=fixture(tmp_path)
    if fault=='checkpoint':(backup/'last.pt').write_bytes(b'wrong')
    elif fault=='journal':(run/'history.jsonl').write_bytes(b'partial')
    else:
        raw=(run/'history.jsonl').read_bytes().replace(b'"step":2',b'"step":9');(run/'history.jsonl').write_bytes(raw)
    with pytest.raises(ValueError):inspect_checkpoint(run,backup,'last.pt',validate_every=4)


def test_budget_charges_failed_and_successful_attempts():
    assert remaining_budget(100,[dict(seconds=10.1,workers_reaped=True),dict(seconds=20,workers_reaped=True)])['remaining_seconds']==69
    for rows in ([],[dict(seconds=1,workers_reaped=False)],[dict(seconds=float('nan'),workers_reaped=True)],[dict(seconds=100,workers_reaped=True)]):
        with pytest.raises(ValueError):remaining_budget(100,rows)
