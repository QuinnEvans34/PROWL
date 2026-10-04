"""D-296: two-label, single-use target fidelity investigation; no CT/model access."""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
from uuid import uuid4
from scripts.diagnostics.localizer_smoke_run import capture,encoded,put,sha
from scripts.diagnostics.broad_localizer_preprocessing import CAP,RECIPE,REPO,ROOT
from src.data.source_inventory_records import require
LIMITS=dict(seconds=600,rss=8*1024**3,output_bytes=64*1024**2,internal_free=100*1024**3)
REVIEW=ROOT/'broad-preprocessing-review-20260929'
REVIEW_PIN='0894dd1edca6a128420580938a16ac81fcf88a027cee8428b3d0915baf7256e3'
CAP_PIN='29c4a48eeadbc61a23fa8e3e8cdf07211ef7a05786cdc24ab572a17703d70683'
PLAN=REPO/'docs/capstone/data/TARGET-FIDELITY-PROBE-2026-09-29.md'


def selected_reports():
    require(sha((REVIEW/'receipt.json').read_bytes())==REVIEW_PIN,'Review receipt changed')
    receipt=json.loads((REVIEW/'receipt.json').read_bytes());raw=(REVIEW/'inspection-progress.json').read_bytes()
    require(sha(raw)==receipt['files']['inspection-progress.json']['sha256'],'Review index changed')
    rows=[]
    for b in json.loads(raw):
        for c in b['cases']:
            if c['study_id'].endswith(('06110','02727')):
                raw=Path(c['path']).read_bytes();require(sha(raw)==c['record_sha256'],'Source report changed')
                rows.append(dict(batch=b['batch'],report=json.loads(raw),report_sha256=c['record_sha256']))
    require(len(rows)==2,'Exact two-label scope');return rows


def prepare():
    reports=selected_reports();require(sha(CAP.read_bytes())==CAP_PIN,'Capability changed')
    source,env=capture();out=ROOT/('target-fidelity-request-'+str(uuid4()));out.mkdir()
    members={'reports.json':encoded(reports),'capability.json':CAP.read_bytes(),'recipe.json':RECIPE.read_bytes(),'source.json':source,'environment.json':env,'plan.md':PLAN.read_bytes()}
    for n,b in members.items():put(out/n,b)
    req=dict(approval='D-296',limits=LIMITS,source_files=2,compressed_bytes=46320,expanded_bytes=10503092,files={n:sha(b) for n,b in members.items()},operation='target_only_diagnostic',optimizer_updates=0)
    put(out/'request.json',encoded(req));print(json.dumps(dict(request=str(out),sha256=sha((out/'request.json').read_bytes()))))


def checked_request(path,pin):
    require(path.parent==ROOT and path.resolve(strict=True)==path,'Request root')
    raw=(path/'request.json').read_bytes();require(sha(raw)==pin,'Request changed');r=json.loads(raw)
    require(r['approval']=='D-296' and r['limits']==LIMITS and r['source_files']==2 and r['compressed_bytes']==46320 and r['expanded_bytes']==10503092 and r['operation']=='target_only_diagnostic' and r['optimizer_updates']==0,'Wrong scope')
    require(set(r['files'])=={'reports.json','capability.json','recipe.json','source.json','environment.json','plan.md'},'Request inventory')
    for n,h in r['files'].items():require(sha((path/n).read_bytes())==h,'Changed request member')
    s,e=capture();require(s==(path/'source.json').read_bytes() and e==(path/'environment.json').read_bytes(),'Code/environment changed')
    require(json.loads((path/'reports.json').read_bytes())==selected_reports(),'Changed diagnostic inputs')
    return r


def worker(dest,request,pin):
    import numpy as np
    import torch
    from src.data.broad_localizer_inputs import open_expanded_inputs
    from src.data.bounded_nifti_audit import read_file
    from src.data.binary_label_policy import decode_binary,APPROVED_POLICY
    from src.data.target_fidelity_diagnostic import compare
    checked_request(request,pin);torch.set_num_threads(2)
    cap=(request/'capability.json').read_bytes();recipe=(request/'recipe.json').read_bytes();reports=json.loads((request/'reports.json').read_bytes());results=[];reads=[]
    for item in reports:
        old=item['report'];views,_=open_expanded_inputs(repo=REPO,capability_bytes=cap,trusted_capability_sha256=CAP_PIN,recipe_bytes=recipe,trusted_recipe_sha256=sha(recipe),batch_id=item['batch'])
        ds=views[old['operation']];matches=[ds.descriptor(i) for i in range(len(ds)) if ds.descriptor(i)['study_id']==old['study_id']];require(len(matches)==1,'Qualified descriptor missing')
        d=matches[0];require(d==old['provenance']['descriptor'],'Descriptor changed')
        # Narrow new authority: only this label, never Dataset.load_native (which also reads CT).
        row=d['rows']['pancreas'];ds._check()
        im,receipt=read_file(ds._root,row,compressed_cap=row['bytes'],expanded_cap=row['expanded_bytes'],voxel_cap=6_000_000,tick=ds._check)
        require(receipt['content_sha256']==d['target']['content_sha256'] and receipt['compressed_bytes']==row['bytes'] and receipt['expanded_bytes']==row['expanded_bytes'],'Label differs')
        require(list(im.shape)==old['source_shape'] and np.allclose(im.affine,old['transform_record']['source_affine'],rtol=0,atol=1e-6),'Source grid changed')
        target,decode=decode_binary(im.get_fdata(dtype=np.float64),policy=APPROVED_POLICY);require(int(target.sum())==old['source_foreground'],'Foreground changed')
        r=compare(target,im.affine,json.loads(recipe));baseline=r['comparisons'][0]
        require(abs(baseline['recall']-old['roundtrip_recall'])<1e-12 and abs(baseline['dice']-old['roundtrip_dice'])<1e-12,'D-295 baseline not reproduced')
        r.update(study_id=old['study_id'],operation=old['operation'],label_receipt=receipt,decode=decode,prior_report_sha256=item['report_sha256'])
        put(dest/(old['study_id'].split(':')[-1]+'.json'),encoded(r));results.append(r);reads.append(receipt);ds._check()
    require(sum(x['compressed_bytes'] for x in reads)==46320 and sum(x['expanded_bytes'] for x in reads)==10503092,'Total reads differ')
    put(dest/'results.json',encoded(dict(state='complete',source_files=2,ct_files=0,optimizer_updates=0,cases=results)))


def run(request,pin):
    req=checked_request(request,pin);require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Free floor')
    dest=ROOT/('target-fidelity-'+str(uuid4()));dest.mkdir();put(ROOT/'target-fidelity-D296-attempt01-claim.json',encoded(dict(request_sha256=pin,result=dest.name)))
    for n in ('request.json',*req['files']):put(dest/n,(request/n).read_bytes())
    start=time.monotonic();peak=0;reason=None;proc=None;print(dest,flush=True)
    try:
        with (dest/'worker.log').open('xb') as log:
            proc=subprocess.Popen([sys.executable,'-m','scripts.diagnostics.target_fidelity_probe','--worker',str(dest),'--request',str(request),'--pin',pin],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTORCH_ENABLE_MPS_FALLBACK':'0'})
            while proc.poll() is None:
                require(time.monotonic()-start<=LIMITS['seconds'],'Time cap');require(shutil.disk_usage(REPO).free>=LIMITS['internal_free'],'Free floor')
                require(sum(p.stat().st_size for p in dest.iterdir())<=LIMITS['output_bytes'],'Output cap')
                p=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=5)
                if p.returncode==0 and p.stdout.strip():peak=max(peak,int(p.stdout.strip())*1024);require(peak<=LIMITS['rss'],'RSS cap')
                elif proc.poll() is None:raise RuntimeError('Memory monitor unavailable')
                time.sleep(.25)
            require(proc.returncode==0,'Worker failed; preserve evidence');checked_request(request,pin)
    except BaseException as exc:reason=str(exc);raise
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        put(dest/'supervisor.json',encoded(dict(exit_code=None if proc is None else proc.returncode,stop_reason=reason,peak_worker_rss=peak,elapsed_seconds=time.monotonic()-start)))
    put(dest/'receipt.json',encoded(dict(files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in dest.iterdir()},state='complete')))
    print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--prepare',action='store_true');a.add_argument('--request',type=Path);a.add_argument('--pin');a.add_argument('--worker',type=Path);args=a.parse_args()
    if args.prepare:prepare()
    elif args.worker:worker(args.worker,args.request,args.pin)
    else:run(args.request,args.pin)
