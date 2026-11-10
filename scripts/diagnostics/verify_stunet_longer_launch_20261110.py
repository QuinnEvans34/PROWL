"""Read-only launch verification; saved evidence is new and never overwrites."""
import json,sys,urllib.request,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import psutil
from mlflow.tracking import MlflowClient
R=Path('E:/PROWL/readiness/stunet-longer-scientific-launch-20261110-a01')
A=Path('E:/PROWL/artifacts/pants_stunet_longer_continuation_12k_20261110_launch01')
def main():
    ready=json.loads((R/'ready.json').read_text());owner=json.loads((R/'run/owner.json').read_text())
    rows=[json.loads(s) for s in (A/'execution/history.jsonl').read_text().splitlines()];updates=[r for r in rows if r['event']=='update']
    assert len(updates)>=5 and [r['step'] for r in updates]==list(range(24001,24001+len(updates)))
    assert any(r['event']=='parent_checkpoint_reference' and r['sha256']==ready['parent_checkpoint_sha256'] for r in rows)
    proof=next(r for r in rows if r['event']=='parent_import')['proof'];assert all(v['max_abs_difference']==0 for v in proof.values())
    processes=[]
    for pid in (owner['supervisor'],owner['worker']):
        proc=psutil.Process(pid);command=proc.cmdline();assert any('stunet_longer_20261110.py' in x for x in command)
        processes.append(dict(pid=pid,command=command,created=proc.create_time()))
    worker=psutil.Process(owner['worker']);processes.extend(dict(pid=p.pid,command=p.cmdline(),created=p.create_time()) for p in worker.children(recursive=True))
    runid=json.loads((R/'run/mlflow.json').read_text())['run_id'];client=MlflowClient(tracking_uri='sqlite:///C:/Users/quinn/PROWL-Tracking/mlflow.db')
    run=client.get_run(runid);metrics=client.get_metric_history(runid,'train/loss');assert run.info.status=='RUNNING' and len(metrics)>=5
    lookup={r['step']:r['loss'] for r in updates};assert len({m.step for m in metrics})==len(metrics)
    # A new update may arrive after the journal snapshot; only compare its captured prefix.
    matched=[m for m in metrics if m.step in lookup];assert len(matched)>=5 and all(m.value==lookup[m.step] for m in matched)
    apis={}
    for label,url in [('local','http://127.0.0.1:8765/api/experiments'),('phone','http://quinns-laptop.tailcbc356.ts.net/api/experiments')]:
        data=json.load(urllib.request.urlopen(url,timeout=20));card=next(x for x in data['runs'] if x['id']==ready['run_id'])
        assert card['steps']>0 and card['target_steps']==12000 and card['global_steps']==card['steps']+24000
        assert len(data['runs'])==12 and data['totals_complete'] and abs(data['total_seconds']-sum(x['seconds'] for x in data['runs']))<0.01
        apis[label]=dict(card=card,total_seconds=data['total_seconds'],total_steps=data['total_steps'],history_count=len(data['runs']))
    report=dict(status='PASS_LAUNCH_VERIFIED',ready_sha256=hashlib.sha256((R/'ready.json').read_bytes()).hexdigest(),pins=len(ready['pins']),observed_updates=len(updates),first_step=updates[0]['step'],last_step=updates[-1]['step'],mlflow_run_id=runid,stored_loss_count=len(metrics),matched_loss_count=len(matched),parent_import=proof,processes=processes,apis=apis)
    dest=R/'launch-verification.json'
    with dest.open('x') as f:json.dump(report,f,indent=2)
    backup=Path('C:/Users/quinn/PROWL-Backups/stunet-longer-readiness-20261110-a01/launch-verification.json')
    with backup.open('xb') as f:f.write(dest.read_bytes())
    assert backup.read_bytes()==dest.read_bytes()
    print(json.dumps({k:v for k,v in report.items() if k not in ['processes','apis','parent_import']}),flush=True)
if __name__=='__main__':main()
