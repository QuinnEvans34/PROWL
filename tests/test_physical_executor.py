import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from src.training.segmenter_physical_executor_v1 import execute
from src.training.segmenter_live_tracking_v1 import Tracker


class FakeSession:
    def __init__(self, steps=4):
        self.step=0;self.config={'max_steps':steps};self.control={'validation':['positive','empty']};self.identity={'fake':True}
    def update(self,provider):
        self.step+=1
        return dict(step=self.step,loss=1/self.step,learning_rate=.0001,member_id='training-only')


def checkpoint(path,session,**kw):path.write_text(json.dumps(dict(step=session.step,**kw)))


def evaluator(session,provider,name,progress):
    progress(25,30);progress(30,30)
    positive=name=='positive';score=.4 if session.step==2 else .3
    lesion=dict(dice=score if positive else 0.,target_voxels=10 if positive else 0,
                predicted_voxels=10,true_positive=4 if positive else 0)
    return dict(case_id=name,step=session.step,metrics=dict(lesion=lesion,pancreas={'dice':.7},
        reference_positive=positive,case_detected=positive,false_alarm_any=not positive,
        reference_components=int(positive),detected_components=int(positive),predicted_volume_mm3=10.,case_alert_50mm3=False))


def records(path):return [json.loads(s) for s in path.read_text().splitlines()]


def test_native_selection_reports_progress_and_prevalidation_checkpoint(tmp_path):
    copied=[];tracked=[]
    result=execute(FakeSession(),None,tmp_path/'run',validate_every=2,checkpoint_every=1,
        evaluator=evaluator,checkpoint=checkpoint,checkpoint_hook=lambda p:copied.append(p.name),track=tracked.append)
    assert result['selected_step']==2 and result['best_development_dice']==.4
    assert json.loads((tmp_path/'run/best.pt').read_text())['step']==2
    assert json.loads((tmp_path/'run/last.pt').read_text())['step']==4
    assert json.loads((tmp_path/'run/native-selected.json').read_text())['step']==2
    assert json.loads((tmp_path/'run/native-terminal.json').read_text())['step']==4
    assert copied.index('step-000002.pt')<copied.index('native-000002.json')
    assert [r['event'] for r in tracked].count('native_completed')==2
    assert not any(r['event']=='validation' for r in tracked)  # never mislabel native as tensor
    assert all(r['elapsed_seconds']>=0 and r['utc_ms']>0 for r in tracked)
    assert tracked[-1]['event']=='completed'


def test_same_score_keeps_first_checkpoint(tmp_path):
    def tied(*args):
        row=evaluator(*args);row['metrics']['lesion']['dice']=.4;return row
    result=execute(FakeSession(),None,tmp_path/'run',validate_every=2,evaluator=tied,checkpoint=checkpoint)
    assert result['selected_step']==2


@pytest.mark.parametrize('fault',['exception','wrong_case','wrong_step','nan'])
def test_failure_preserves_journal_and_checkpoint_without_complete(tmp_path,fault):
    def bad(*args):
        if fault=='exception':raise RuntimeError('intentional failure')
        row=evaluator(*args)
        if fault=='wrong_case':row['case_id']='test-case'
        if fault=='wrong_step':row['step']=99
        if fault=='nan':row['metrics']['lesion']['dice']=float('nan')
        return row
    with pytest.raises((ValueError,RuntimeError)):
        execute(FakeSession(2),None,tmp_path/'run',validate_every=2,evaluator=bad,checkpoint=checkpoint)
    rows=records(tmp_path/'run/history.jsonl')
    assert rows[-1]['event']=='failed' and not any(r['event']=='completed' for r in rows)
    assert (tmp_path/'run/step-000002.pt').exists()


@pytest.mark.parametrize('names',[[],['positive','positive'],['protected_test']])
def test_wrong_roles_refused_before_output(tmp_path,names):
    with pytest.raises(ValueError):execute(FakeSession(),None,tmp_path/'run',validation_names=names)
    assert not (tmp_path/'run').exists()


def test_existing_output_and_resume_are_refused(tmp_path):
    path=tmp_path/'run';path.mkdir()
    with pytest.raises(FileExistsError):execute(FakeSession(),None,path)
    session=FakeSession();session.step=1
    with pytest.raises(ValueError):execute(session,None,tmp_path/'other')


def test_native_events_are_mirrored_to_mlflow_not_tensor(tmp_path):
    calls=[];client=SimpleNamespace(log_batch=lambda *args,**kw:calls.append(kw))
    tracker=Tracker('fake',tmp_path,client=client)
    execute(FakeSession(2),None,tmp_path/'run',validate_every=2,evaluator=evaluator,checkpoint=checkpoint,track=tracker)
    assert not tracker.disabled
    keys={m.key for call in calls for m in call['metrics']}
    assert 'native/dev70/raw/lesion_positive_macro_dice' in keys
    assert 'train/elapsed_seconds' in keys
    assert not any(k.startswith('tensor/') for k in keys)
