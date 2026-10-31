import json
import shutil
import pytest
import torch
from test_distillation_integration_v1 import Provider,store,same,isolated_cpu
from test_errata_kd_session_v1 import session
from test_kd_evidence_executor_v1 import evaluate
from src.training.segmenter_distillation_session_v1 import BoundDistillationSession
from src.training.segmenter_errata_kd_session_v1 import ErrataKDSession
from src.training.segmenter_kd_continuation_executor_v1 import execute
from src.training.segmenter_kd_evidence_executor_v1 import execute as original_execute
from src.operations.kd_continuation_v1 import inspect_checkpoint


def native(s,p,name,progress):
    row=evaluate(s,p,'positive',progress)
    row['case_id']=row['component_evidence']['case_id']=name
    return row


def backup_to(root):
    root.mkdir()
    return lambda p:shutil.copyfile(p,root/p.name)


@pytest.mark.parametrize('weight',[0.,.1])
@pytest.mark.parametrize('pause_step',[3,4,5])
def test_paused_resume_matches_uninterrupted_state_and_selection(tmp_path,weight,pause_step):
    target=tmp_path/'targets';target.mkdir();p=Provider();targets=store(target,p)
    full=session(p,targets.pin,weight)
    expected=original_execute(BoundDistillationSession(full,targets),p,tmp_path/'reference',
        checkpoint_hook=backup_to(tmp_path/'ref-backup'),validate_every=4,checkpoint_every=2,evaluator=native)
    first=session(p,targets.pin,weight)
    result=execute(BoundDistillationSession(first,targets),p,tmp_path/'first',
        checkpoint_hook=backup_to(tmp_path/'first-backup'),validate_every=4,checkpoint_every=2,evaluator=native,
        pause_requested=lambda:first.step>=pause_step)
    assert result['status']=='paused' and first.step==pause_step
    context=inspect_checkpoint(tmp_path/'first',tmp_path/'first-backup','pause.pt',validate_every=4)
    saved=torch.load(context['checkpoint'],weights_only=True,map_location='cpu')
    restored=ErrataKDSession.restore(saved['session'],context['identity'])
    actual=execute(BoundDistillationSession(restored,targets),Provider(),tmp_path/'continued',
        checkpoint_hook=backup_to(tmp_path/'continued-backup'),continuation=context,
        validate_every=4,checkpoint_every=2,evaluator=native)
    assert same(full.state(),restored.state())
    assert actual['completed_updates']==8 and actual['selected_step']==expected['selected_step']==4
    assert json.loads((tmp_path/'continued/native-selected.json').read_text())['step']==4
    updates=[json.loads(l) for l in (tmp_path/'continued/history.jsonl').read_text().splitlines()]
    assert [r['step'] for r in updates if r['event']=='update']==list(range(pause_step+1,9))


def test_resume_before_validation_replays_validation_before_update(tmp_path):
    target=tmp_path/'targets';target.mkdir();p=Provider();targets=store(target,p)
    first=session(p,targets.pin,.1)
    def fail(*args):raise OSError('interrupted native evaluation')
    with pytest.raises(OSError):
        original_execute(BoundDistillationSession(first,targets),p,tmp_path/'first',
            checkpoint_hook=backup_to(tmp_path/'backup'),validate_every=4,checkpoint_every=2,evaluator=fail)
    context=inspect_checkpoint(tmp_path/'first',tmp_path/'backup','step-000004.pt',validate_every=4)
    assert context['pending_validation']
    saved=torch.load(context['checkpoint'],weights_only=True,map_location='cpu')
    restored=ErrataKDSession.restore(saved['session'],context['identity'])
    execute(BoundDistillationSession(restored,targets),Provider(),tmp_path/'continued',
        checkpoint_hook=backup_to(tmp_path/'next-backup'),continuation=context,
        validate_every=4,checkpoint_every=2,evaluator=native)
    rows=[json.loads(l) for l in (tmp_path/'continued/history.jsonl').read_text().splitlines()]
    events=[(r['event'],r.get('step')) for r in rows]
    assert events.index(('native_completed',4))<events.index(('update',5))


def test_failed_pause_backup_never_reports_paused(tmp_path):
    target=tmp_path/'targets';target.mkdir();p=Provider();targets=store(target,p);s=session(p,targets.pin,.1)
    def hook(path):
        if path.name=='pause.pt':raise OSError('backup failed')
    with pytest.raises(OSError):execute(BoundDistillationSession(s,targets),p,tmp_path/'run',
        checkpoint_hook=hook,pause_requested=lambda:s.step==1,evaluator=native)
    rows=[json.loads(l) for l in (tmp_path/'run/history.jsonl').read_text().splitlines()]
    assert rows[-1]['event']=='failed' and not any(r['event']=='paused' for r in rows)
