import json,sqlite3
from pathlib import Path
import pytest
from scripts.collect_training_hours import summarize,entry,journal,collect


def test_copies_do_not_add_time_and_distinct_recovery_attempts_do():
    a=entry('one','Mac','one',10,'training','counter',aliases=['mlflow:a'])
    b=entry('two','Mac','replayed updates in a separate attempt',6,'training','counter',aliases=['mlflow:b'])
    rows,total=summarize([a,dict(a),b])
    assert len(rows)==2 and total['recorded_training_seconds']==16


def test_same_mlflow_execution_cannot_be_added_again_from_another_machine():
    a=entry('one','Mac','one',10,'training','counter',aliases=['mlflow:a'])
    b=entry('copy','Lenovo','copy',10,'training','export',aliases=['mlflow:a'])
    with pytest.raises(ValueError,match='Overlapping'):summarize([a,b])


@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1])
def test_refuses_invalid_durations(value):
    with pytest.raises(ValueError):entry('bad','Mac','bad',value,'training','counter')


def test_estimates_and_teacher_are_separate_from_elapsed_counters():
    rows,t=summarize([entry('a','Mac','a',10,'training','counter'),entry('b','Mac','b',20,'legacy_estimate','span'),entry('c','Mac','c',30,'teacher_targets','worker')])
    assert t['training_seconds']==10 and t['legacy_estimated_seconds']==20
    assert t['recorded_training_seconds']==30 and t['recorded_model_work_seconds']==60


def test_live_journal_excludes_partial_tail_and_rejects_hidden_reset(tmp_path):
    p=tmp_path/'history.jsonl';p.write_bytes(b'{"elapsed_seconds":2}\n{"elapsed_seconds":5}\n{"elap')
    seconds,_,rows,size=journal(p);assert seconds==5 and len(rows)==2 and size==44
    p.write_text('{"elapsed_seconds":5}\n{"elapsed_seconds":2}\n')
    with pytest.raises(ValueError,match='reset'):journal(p)


def test_stale_running_mlflow_stops_at_last_metric_and_registration_is_excluded(tmp_path):
    p=tmp_path/'mlflow.db';c=sqlite3.connect(p)
    c.executescript('create table runs(run_uuid,name,status,start_time,end_time,artifact_uri);create table tags(run_uuid,key,value);create table metrics(run_uuid,key,timestamp,step);')
    c.execute('insert into runs values(?,?,?,?,?,?)',('old','old','RUNNING',1000,None,'/Users/quintonevans/old/artifacts'))
    c.execute('insert into tags values(?,?,?)',('old','mlflow.source.name','scripts/train.py'))
    c.execute('insert into metrics values(?,?,?,?)',('old','train/loss',3000,1))
    c.execute('insert into runs values(?,?,?,?,?,?)',('registration','register','FINISHED',1000,4000,'/Users/quintonevans/old/artifacts'))
    c.commit();c.close()
    root=tmp_path/'kd';(root/'treatment/execution').mkdir(parents=True)
    (root/'ready.json').write_text(json.dumps({'segments':{'control':[],'treatment':[]}}))
    (root/'treatment/dispatch.json').write_text(json.dumps({'run_id':'current'}))
    (root/'treatment/execution/history.jsonl').write_text('{"event":"update","step":5,"elapsed_seconds":4,"utc_ms":5000}\n')
    w=tmp_path/'windows.json';w.write_text(json.dumps({'runs':[],'as_of_utc':'2026-11-03T00:00:00Z'}))
    d=collect(dict(legacy_db=str(p),older_mac_journals=[],current_kd_root=str(root),teacher_resources=[],lenovo_snapshot=str(w)))
    assert d['totals']['legacy_estimated_seconds']==2
    assert d['totals']['training_seconds']==4
    assert d['sources'][0]['excluded_without_training_duration']==1
    assert not any('registration' in e['execution_id'] for e in d['entries'])
