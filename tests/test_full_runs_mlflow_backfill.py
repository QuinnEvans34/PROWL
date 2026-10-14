from copy import deepcopy
from types import SimpleNamespace
import pytest
from scripts.diagnostics.backfill_full_runs_mlflow import build_metrics, import_metrics, summarize


def history():
    rows=[dict(event='update',step=1,loss=1.2,learning_rate=.001,elapsed_seconds=3)]
    for name,positive in [('a',True),('b',False),('excluded',True)]:
        rows.append(dict(event='validation_case',step=1,case_id=name,metrics=dict(
            lesion=dict(target_voxels=int(positive),true_positive=int(positive),predicted_voxels=1,dice=.4 if positive else None),
            pancreas=dict(dice=.8))))
    return rows+[dict(event='completed',step=1)]


def test_original_and_matched_cohorts_have_separate_names():
    values={(k,s):v for k,s,v in build_metrics(history(),['a','b'])}
    assert values['tensor/dev3/positive_cases',1]==2
    assert values['tensor/dev2/positive_cases',1]==1
    assert values['tensor/dev2/empty_alarm_fraction',1]==1
    assert values['train/elapsed_seconds',1]==3


@pytest.mark.parametrize('change',['incomplete','missing','duplicate','noncontiguous','nonfinite'])
def test_bad_history_refused(change):
    rows=history();retained=['a','b']
    if change=='incomplete':rows.pop()
    if change=='missing':retained.append('missing')
    if change=='duplicate':rows.insert(2,deepcopy(rows[1]))
    if change=='noncontiguous':rows[0]['step']=2
    if change=='nonfinite':rows[0]['loss']=float('nan')
    with pytest.raises(ValueError):build_metrics(rows,retained)


class FakeClient:
    def __init__(self):self.data={}
    def get_metric_history(self,run,key):return self.data.get(key,[])
    def log_batch(self,run,metrics,synchronous):
        assert synchronous
        for m in metrics:self.data.setdefault(m.key,[]).append(m)


def test_partial_import_is_resumed_and_repeat_adds_nothing():
    c=FakeClient();values=[('loss',1,.4),('loss',2,.3),('native',2,.7)]
    assert import_metrics(c,'run',values[:1],100)==(1,1)
    assert import_metrics(c,'run',values,100)==(2,3)
    assert import_metrics(c,'run',values,100)==(0,3)
    assert c.data['loss'][0].timestamp==100


@pytest.mark.parametrize('stored',[[SimpleNamespace(step=1,value=.9)],
    [SimpleNamespace(step=1,value=.4),SimpleNamespace(step=1,value=.4)]])
def test_conflicting_or_duplicate_stored_points_refused(stored):
    c=FakeClient();c.data['loss']=stored
    with pytest.raises(ValueError):import_metrics(c,'run',[('loss',1,.4)],100)


def test_native_summary_uses_native_fields():
    rows=[]
    for positive in (True,False):
        rows.append(dict(metrics=dict(reference_positive=positive,case_detected=positive,false_alarm_any=False,
            lesion={'dice':.5 if positive else None},pancreas={'dice':.8},reference_components=int(positive),
            detected_components=int(positive),predicted_volume_mm3=100 if positive else 0,case_alert_50mm3=positive)))
    result=summarize(rows,native=True)
    assert result['lesion_positive_macro_dice']==.5
    assert result['detected_components']==1 and result['empty_alerts_50mm3']==0
