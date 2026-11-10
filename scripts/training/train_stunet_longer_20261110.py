"""One-shot STU-Net worker: diagnostic recovery and the same scientific update path."""
import argparse,json,os,random,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.stunet_longer_inputs_20261110 import Inputs
from src.data.stunet_inputs_20261106 import predict,sha
from src.training.stunet_transfer_20261106 import make_model
from src.training.stunet_longer_session_20261110 import Session,PARENT_SHA
from src.training.stunet_session_20261106 import compare


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2);f.flush();os.fsync(f.fileno())


def backup(path,destination):
    path=Path(path);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with path.open('rb') as src,destination.open('xb') as dst:
        shutil.copyfileobj(src,dst,4*1024**2);dst.flush();os.fsync(dst.fileno())
    digest=sha(path)
    if sha(destination)!=digest:raise ValueError('Independent backup mismatch')
    return dict(path=str(path),backup=str(destination),sha256=digest,bytes=path.stat().st_size)


def save(session,path,destination=None):
    import torch
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:
        torch.save(session.state(),f);f.flush();os.fsync(f.fileno())
    return backup(path,destination) if destination else dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size)


def summary(rows):
    positive=[r['metrics'] for r in rows if r['metrics']['reference_positive']]
    empty=[r['metrics'] for r in rows if not r['metrics']['reference_positive']]
    return dict(lesion_dice=sum(m['lesion']['dice'] for m in positive)/len(positive),
        positive=len(positive),empty=len(empty),detected=sum(m['case_detected'] for m in positive),
        alarms=sum(m['false_alarm_any'] for m in empty))


def run(request,mode,output):
    import torch,numpy as np
    r=json.loads(Path(request).read_text());out=Path(output);out.mkdir(exist_ok=False)
    started=time.monotonic();stage='load';journal=out/'history.jsonl'
    def event(kind,**fields):
        row=dict(event=kind,elapsed_seconds=time.monotonic()-started,utc_ms=int(time.time()*1000),**fields)
        with journal.open('a',encoding='utf-8') as f:
            f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
    try:
        torch.set_num_threads(2);random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.cuda.manual_seed_all(42)
        torch.cuda.set_per_process_memory_fraction(6*1024**3/torch.cuda.get_device_properties(0).total_memory)
        torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        provider=Inputs(r['inputs']);model=make_model(r['source'],pools=[[2,2,2]]*4+[[1,1,2]])
        identity=dict(input_sha256=provider.identity,train=sorted(provider.train),nonpromotable=mode!='science',precision='fp32',parent_checkpoint_sha256=PARENT_SHA,phase='longer-36k-20261110')
        session=Session(model,identity);event('started',mode=mode,scientific_updates=0)
        if mode!='cold':
            if sha(r['parent_checkpoint'])!=PARENT_SHA or sha(r['parent_backup'])!=PARENT_SHA:raise ValueError('Parent independent hashes')
            parent=torch.load(r['parent_checkpoint'],map_location='cpu',weights_only=True)
            proof=session.import_parent(parent,r['parent_identity'],PARENT_SHA);del parent
            event('parent_import',step=24000,proof=proof,checkpoint_sha256=PARENT_SHA)
        else:proof=None
        if mode=='cold':
            stage='cold_restore';producer=Path(r['producer']);receipt=json.loads((producer/'result.json').read_text())
            checkpoint=receipt['step4'];expected_path=Path(receipt['step5']['backup'])
            if sha(checkpoint['backup'])!=checkpoint['sha256'] or sha(expected_path)!=receipt['step5']['sha256']:
                raise ValueError('Cold checkpoint identity')
            state=torch.load(checkpoint['backup'],map_location='cpu',weights_only=True)
            session.restore(state);before=compare(state,session.state());del state
            result=session.update(provider)
            if result['input']!=receipt['updates'][-1]['input']:raise ValueError('Cold next input mismatch')
            expected=torch.load(expected_path,map_location='cpu',weights_only=True)
            after=compare(expected,session.state(),atol=r['cold_atol'],rtol=r['cold_rtol']);del expected
            report=dict(status='PASS',mode=mode,exact_restored_state=before,next_update_state=after,update=result,scientific_updates=0)
        elif mode=='producer':
            stage='producer';updates=[];step4=None
            for _ in range(5):
                result=session.update(provider);updates.append(result);event('diagnostic_update',**result)
                if session.step==24004:step4=save(session,out/'step4.pt',Path(r['qualification_backup'])/'step4.pt')
            step5=save(session,out/'expected-step5.pt',Path(r['qualification_backup'])/'expected-step5.pt')
            native=[]
            for name in r['native_qualification']:
                case=provider.development(name);native.append(predict(model,case));del case
            if len(native)!=2 or sorted(x['metrics']['reference_positive'] for x in native)!=[False,True] or any(x['gaps'] for x in native):raise ValueError('Native qualification cohort/coverage')
            report=dict(status='PASS',mode=mode,parent_import=proof,native_qualification=native,step4=step4,step5=step5,updates=updates,scientific_updates=0)
        elif mode=='science':
            stage='scientific_training';back=Path(r['scientific_backup']);checkpoints=[]
            event('parent_checkpoint_reference',step=24000,path=r['parent_checkpoint'],backup=r['parent_backup'],sha256=PARENT_SHA);best=None
            for _ in range(12000):
                result=session.update(provider)
                event('update',step=result['step'],loss=result['loss'],learning_rate=result['lr'],input=result['input'],phase_step=result['phase_step'],diagnostics=result['diagnostics'])
                if session.step%2000==0:
                    name=f'checkpoint-{session.step:05d}.pt';checkpoints.append(save(session,out/name,back/name))
                    event('checkpoint',step=session.step,**checkpoints[-1])
                if session.step%2000==0:
                    stage='native_validation';rows=[];total=sum(x['tiles'] for x in provider.config['native_profile'].values());done=0
                    event('native_started',step=session.step,completed_cases=0,total_cases=70,tiles_done=0,total_tiles=total)
                    for name in sorted(provider.dev):
                        case=provider.development(name)
                        def progress(**kw):
                            if kw['tile']%10==0:
                                event('native_progress',step=session.step,completed_cases=len(rows),total_cases=70,tiles_done=done+kw['tile'],total_tiles=total)
                        row=predict(model,case,progress=progress);del case;rows.append(row);done+=row['tiles']
                        event('native_case',step=session.step,variant='raw',**row)
                    if len(rows)!=70 or {x['case_id'] for x in rows}!=provider.dev or done!=total:raise ValueError('Incomplete native cohort')
                    scores=summary(rows)
                    if scores['positive']!=36 or scores['empty']!=34:raise ValueError('Native denominator changed')
                    report_path=out/f'native-{session.step:05d}.json';write(report_path,dict(step=session.step,cases=rows,summary=scores))
                    backup(report_path,back/report_path.name)
                    event('native_completed',step=session.step,variant='raw',**scores)
                    if best is None or scores['lesion_dice']>best['lesion_dice']:
                        best=dict(step=session.step,**scores,checkpoint=checkpoints[-1],report=str(report_path))
                    stage='scientific_training'
            write(out/'selected.json',best);backup(out/'selected.json',back/'selected.json')
            report=dict(status='PASS',mode=mode,scientific_updates=session.step-24000,global_step=session.step,parent_checkpoint_sha256=PARENT_SHA,selected=best,checkpoints=checkpoints,exposure=session.exposure)
            event('training_completed',step=session.step)
        else:raise ValueError('Unknown mode')
        report.update(seconds=time.monotonic()-started,allocated_peak=torch.cuda.max_memory_allocated(),reserved_peak=torch.cuda.max_memory_reserved())
        if max(report['allocated_peak'],report['reserved_peak'])>6*1024**3:raise RuntimeError('CUDA cap')
        write(out/'result.json',report)
        if mode=='science':
            backup(out/'result.json',back/'result.json');event('completed',step=session.step)
            backup(journal,back/'history.jsonl')
        else:event('diagnostic_completed')
    except BaseException as e:
        event('failed',stage=stage,error=repr(e));write(out/'failure.json',dict(stage=stage,error=repr(e)));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--mode',choices=['producer','cold','science'],required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.request,a.mode,a.output)
