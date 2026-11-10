"""One authorized restoration; preserves failed stage and reuses its complete case results."""
import argparse,json,os,sys,time,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.training.train_stunet_longer_20261110 import write,backup,save,summary,Inputs,Session,PARENT_SHA,make_model,predict,sha,compare
from src.operations.stunet_recovery_20261110 import CHECKPOINT_SHA,reusable_cases

def run(request,mode,output):
    import torch,numpy as np
    r=json.loads(Path(request).read_text());out=Path(output);out.mkdir(exist_ok=False);started=time.monotonic();journal=out/'history.jsonl'
    def event(kind,**fields):
        with journal.open('a') as f:f.write(json.dumps(dict(event=kind,elapsed_seconds=time.monotonic()-started,utc_ms=int(time.time()*1000),**fields))+'\n');f.flush();os.fsync(f.fileno())
    try:
        torch.set_num_threads(2);random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.cuda.manual_seed_all(42)
        torch.cuda.set_per_process_memory_fraction(6*1024**3/torch.cuda.get_device_properties(0).total_memory)
        torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        provider=Inputs(r['inputs']);model=make_model(r['source'],pools=[[2,2,2]]*4+[[1,1,2]])
        identity=dict(input_sha256=provider.identity,train=sorted(provider.train),nonpromotable=False,precision='fp32',parent_checkpoint_sha256=PARENT_SHA,phase='longer-36k-20261110')
        session=Session(model,identity);event('started',mode=mode,scientific_updates=0)
        if sha(r['restore_checkpoint'])!=CHECKPOINT_SHA or sha(r['restore_backup'])!=CHECKPOINT_SHA:raise ValueError('Checkpoint copies changed')
        state=torch.load(r['restore_backup'],map_location='cpu',weights_only=True)
        if state['step']!=26000:raise ValueError('Wrong restoration step')
        session.restore(state);proof=compare(state,session.state());del state
        original=[json.loads(s) for s in Path(r['failed_journal']).read_text().splitlines()]
        reused=reusable_cases(original,provider.dev,provider.config['native_profile'])
        event('checkpoint_restored',step=26000,proof=proof,sha256=CHECKPOINT_SHA)
        if mode=='restore':
            write(out/'result.json',dict(status='PASS',scientific_updates=0,restored_step=session.step,state_comparison=proof,reusable_cases=len(reused),reserved_peak=torch.cuda.max_memory_reserved()));event('diagnostic_completed');return
        back=Path(r['scientific_backup']);checkpoints=[dict(path=r['restore_checkpoint'],backup=r['restore_backup'],sha256=CHECKPOINT_SHA,bytes=Path(r['restore_checkpoint']).stat().st_size)];best=None
        event('parent_checkpoint_reference',step=26000,**checkpoints[0])
        def validate(saved):
            nonlocal best
            rows=list(saved);done=sum(x['tiles'] for x in rows);total=sum(x['tiles'] for x in provider.config['native_profile'].values())
            event('native_started',step=session.step,completed_cases=len(rows),total_cases=70,tiles_done=done,total_tiles=total)
            for row in saved:event('native_case_reused',step=session.step,variant='raw',**row)
            for name in sorted(provider.dev)[len(rows):]:
                case=provider.development(name)
                def progress(**kw):
                    if kw['tile']%10==0:event('native_progress',step=session.step,completed_cases=len(rows),total_cases=70,tiles_done=done+kw['tile'],total_tiles=total)
                row=predict(model,case,progress=progress);del case;rows.append(row);done+=row['tiles'];event('native_case',step=session.step,variant='raw',**row)
            if len(rows)!=70 or {x['case_id'] for x in rows}!=provider.dev or done!=total:raise ValueError('Incomplete native cohort')
            scores=summary(rows)
            if scores['positive']!=36 or scores['empty']!=34:raise ValueError('Denominator changed')
            path=out/f'native-{session.step:05d}.json';write(path,dict(step=session.step,cases=rows,summary=scores));backup(path,back/path.name)
            event('native_completed',step=session.step,variant='raw',**scores)
            if best is None or scores['lesion_dice']>best['lesion_dice']:best=dict(step=session.step,**scores,checkpoint=checkpoints[-1],report=str(path))
        validate(reused)
        for _ in range(10000):
            result=session.update(provider);event('update',step=result['step'],phase_step=session.step-26000,loss=result['loss'],learning_rate=result['lr'],input=result['input'],diagnostics=result['diagnostics'])
            if session.step%2000==0:
                name=f'checkpoint-{session.step:05d}.pt';checkpoints.append(save(session,out/name,back/name));event('checkpoint',step=session.step,**checkpoints[-1]);validate([])
        write(out/'selected.json',best);backup(out/'selected.json',back/'selected.json')
        report=dict(status='PASS',mode=mode,scientific_updates=10000,global_step=session.step,selected=best,checkpoints=checkpoints,exposure=session.exposure,seconds=time.monotonic()-started,reserved_peak=torch.cuda.max_memory_reserved())
        write(out/'result.json',report);backup(out/'result.json',back/'result.json');event('completed',step=session.step);backup(journal,back/'history.jsonl')
    except BaseException as e:event('failed',error=repr(e));write(out/'failure.json',dict(error=repr(e)));raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--mode',choices=['restore','science'],required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.request,a.mode,a.output)
