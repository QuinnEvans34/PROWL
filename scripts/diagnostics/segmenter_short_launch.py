"""Prepare, rehearse and separately approve one exact short segmenter transaction."""
import argparse,gc,json,os,shutil,signal,subprocess,sys,time
from pathlib import Path
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK','0');os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import numpy as np
import torch
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as data,segmenter_final_targets_v1 as targets,segmenter_cache_v1 as cache
from src.training import segmenter_training_session_v1 as core,segmenter_short_executor_v1 as executor,segmenter_trained_evidence_v1 as evidence,segmenter_inference_v1 as inverse,segmenter_native_scoring_v1 as scoring
from src.operations.segmenter_short_storage_v1 import short_stores
from src.operations.segmenter_short_backup_v1 import restore_backup
from src.operations.segmenter_primary_read_guard_v1 import install as block_primary
from src.operations.localizer_run_storage import tree_bytes
from scripts.diagnostics import segmenter_training_qualification as q,segmenter_source_verification as source,segmenter_content_pilot as prior,segmenter_native_scoring as oldscore

REPO=q.REPO;ROOT=q.ROOT;REVIEW=ROOT/'SEGMENTER-TRAINING-REVIEW-20261002'
REVIEW_PIN='2a1c24def53e42f7edc05a392e56e5eb4ea360b1016c3dae87172451640a35c2'
ACCEPT_PIN='f7a2f6d941c72ebc346b21a89492725f371ab403e095863ee4a05165df718ea8'
DATE='20261003';META=ROOT/('SEGMENTER-SHORT-TARGET-METADATA-'+DATE)
READY=ROOT/('SEGMENTER-SHORT-READINESS-'+DATE+'.json')
TESTS=ROOT/('SEGMENTER-SHORT-NATIVE-TESTS-'+DATE+'.json')
CODE=['src/data/segmenter_final_targets_v1.py','src/data/segmenter_training_views_v1.py','src/training/segmenter_short_executor_v1.py','src/training/segmenter_trained_evidence_v1.py','src/operations/segmenter_short_storage_v1.py','src/operations/segmenter_short_backup_v1.py','scripts/diagnostics/segmenter_short_launch.py','tests/test_segmenter_short_executor.py','tests/test_segmenter_trained_evidence.py','tests/test_segmenter_final_targets.py','tests/segmenter_short_fixtures.py']
CAPS={phase:REPO/('docs/capstone/operations/SEGMENTER-SHORT-'+phase.upper()+'-STORAGE-CAPABILITY-2026-10-03.json') for phase in ('rehearsal','real')}
CODE+=[str(p.relative_to(REPO)) for p in CAPS.values()]

class Stores(tuple):
    def __new__(cls,values,capability):
        s=super().__new__(cls,values);s.capability=capability;return s

def dest(phase):require(phase in CAPS,'Unknown phase');return ROOT/(('SEGMENTER-SHORT-REHEARSAL-' if phase=='rehearsal' else 'CAP-EXP-013-PREPARED-')+DATE)
def budget_path(phase):return ROOT/('SEGMENTER-SHORT-'+phase.upper()+'-BUDGET-'+DATE+'.json')
def pins():
    source.verify_package(REVIEW,REVIEW_PIN);a=json.loads((REVIEW/'acceptance.json').read_bytes());require(digest((REVIEW/'acceptance.json').read_bytes())==ACCEPT_PIN and a['real_updates_allowed'] is False,'D-326 prerequisite changed')
    fixed=q.pins()|{n:ref['sha256'] for n,ref in a['source_snapshots'].items()};require(all(digest((REPO/n).read_bytes())==h for n,h in fixed.items()),'Accepted D-326 producing/supplemental source changed');return fixed|{n:digest((REPO/n).read_bytes()) for n in CODE}
def runtime():require(os.environ.get('PYTORCH_ENABLE_MPS_FALLBACK')=='0','MPS fallback must be disabled');return q.runtime()
def stores(phase,*,create=False,recovery=False,ceilings=None):
    raw=CAPS[phase].read_bytes();ss=short_stores(REPO/'configs/local/roots.yaml',raw,trusted_capability_sha256=digest(raw),create=create,recovery_only=recovery)
    if ceilings:
        for s,c in zip(ss,ceilings):
            if s:s.quota_bytes=min(s.quota_bytes,c)
    return Stores(ss,json.loads(raw))
def freeze_budget(phase):
    ss=stores(phase,create=True);p=budget_path(phase);cap=digest(CAPS[phase].read_bytes())
    if not p.exists():source.put(p,dict(decision='D-327',phase=phase,capability_sha256=cap,ceilings=[s.quota_bytes for s in ss]))
    r=json.loads(p.read_bytes());require(r['decision']=='D-327' and r['phase']==phase and r['capability_sha256']==cap and len(r['ceilings'])==3 and all(type(v) is int and 0<v<=s.quota_bytes for v,s in zip(r['ceilings'],ss)),'Frozen budget drift');return r['ceilings']

def real_inputs():
    raw=q.BASELINE.read_bytes();require(digest(raw)==q.BASELINE_PIN,'Original before baseline changed');baseline=json.loads(raw)
    a,old,cases,files=oldscore.inputs();entries=old['binding']['entries'];require([c['study_id'] for c in cases]==[e['descriptor']['study_id'] for e in entries],'Original/cached case order')
    cases=[c|dict(transform=e['transform'],transform_sha256=e['transform_sha256'],image_sha256=old['binding']['entries'][n]['descriptor']['image']['content_sha256']) for n,(c,e) in enumerate(zip(cases,entries))]
    production=json.loads((ROOT/'SEGMENTER-CACHE-BUILD-attempt02-20261002/result.json').read_bytes())
    # Image hashes are normalized cached NPY bytes, never original CT bytes.
    req=json.loads((ROOT/'SEGMENTER-CACHE-BUILD-attempt02-20261002/request.json').read_bytes())
    cache_accept=json.loads((ROOT/'SEGMENTER-CACHE-REVIEW-20261002/accepted-cache.json').read_bytes())
    from scripts.diagnostics import segmenter_cache_qualification as ccli
    payload,_=ccli.store().resolve(cache_accept['cache_artifact_id'],receipt_sha256=cache_accept['cache_completion_sha256'],expected_derivation=cache_accept['request_sha256'],validate=lambda f:ccli.validate_production(f,req,cache_accept['request_sha256']))
    for n,c in enumerate(cases):
        c['image_sha256']=digest(payload[cache.names(n)['image']]);old_components=next(r for r in baseline['cases'] if r['study_id']==c['study_id'])['components'];c['reference_components']=[{k:v[k] for k in ('component_id','native_voxels','bounds_xyz_half_open','source_boundary_contact')} for v in old_components]
    return baseline,old,cases,files

def metadata():
    fixed=pins();baseline,old,cases,rows=real_inputs();META.mkdir();start=time.monotonic();cap=old['capability']|dict(operations=['stat']);before=source.mount_guard(cap);proofs=[]
    def deny(event,args):
        if event=='open' and args and isinstance(args[0],(str,bytes)) and os.fsdecode(args[0]).endswith(('.nii','.nii.gz')):raise ValueError('Stat-only target preparation forbids payload opens')
    sys.addaudithook(deny)
    with source.directory(cap['source_root']) as fd:
        for row in rows:
            require(time.monotonic()-start<120,'Target metadata time envelope');r=source.observe(fd,row|dict(expected_bytes=row['compressed_bytes']));require(r['state']=='observed','Target metadata hold');cur=r['observation'];changes=[k for k in cur if cur[k]!=row['observation'][k]];require(set(cur)==set(row['observation']) and set(changes)<={'device'} and cur['device']==before['root_device'],'Original target nonvolatile change requires investigation');proofs.append(dict(study_id=row['study_id'],kind=row['kind'],uri=row['uri'],old=row['observation'],current=cur,changed_fields=changes,retained_sha256=row['sha256']))
    after=source.mount_guard(cap);require(before==after,'Stat source mount changed');source.put(META/'result.json',dict(state='stat_only_verified',decision='D-327',source_pins=fixed,runtime=runtime(),files=proofs,mount_before=before,mount_after=after,source_arrays_read=0,hash_bytes=0,decode_bytes=0,seconds=time.monotonic()-start));print(prior.package(META))

def request_for(provider,scope,phase,ceilings):
    ctx=q.context();ctx['source.json']=canonical(pins());ctx['environment.json']=canonical(runtime());ctx['geometry.json']=canonical(dict(baseline_sha256=q.BASELINE_PIN,geometry='provided_pancreas_reference_zero_jitter',target_scope_sha256=digest(canonical(scope)),stage=targets.STAGE))
    run='segmenter-training-D327-MPS' if phase=='rehearsal' else 'segmenter-training-CAP-EXP-013';identity,controls=core.make_identity(core.config(),provider,ctx,run_id=run,device='mps');cap=json.loads(CAPS[phase].read_bytes());baseline=dict(kind='invented_tensor_diagnostics_no_real_baseline')
    if phase=='real':
        b=json.loads(q.BASELINE.read_bytes());baseline=dict(kind='D325_original_native',acceptance_sha256=q.BASELINE_PIN,aggregate=b['aggregate'],cases=b['cases'])
    readiness=dict(kind='D326_transaction_qualification',acceptance_sha256=ACCEPT_PIN)
    if phase=='real':
        ready=json.loads(READY.read_bytes());require(ready['state']=='qualified_short_executor' and ready['source_pins']==pins() and ready['runtime']==runtime(),'Short executor not accepted for exact sources/runtime');readiness=dict(kind='qualified_short_executor_rehearsal',acceptance_sha256=digest(READY.read_bytes()),producer_receipt_sha256=ready['producer_receipt_sha256'],recovery_receipt_sha256=ready['recovery_receipt_sha256'],tests_sha256=ready['tests_sha256'])
    r=dict(schema_version='1.0.0',task=executor.TASK,preparation_decision='D-327',experiment_id='D327-INVENTED-REHEARSAL' if phase=='rehearsal' else 'CAP-EXP-013',identity=identity,controls={n:v.decode() for n,v in controls.items()},checkpoint_steps=[0,6,24,48],evaluation_steps=[0,6,24,48],targets=scope,baseline=baseline,source_pins=pins(),runtime=runtime(),storage_capability_sha256=digest(canonical(cap)),storage_capability=cap,storage_ceilings=ceilings,limits=executor.LIMITS,initial_weights_sha256=core.INITIAL,weight_imports_allowed=False,continuation_allowed=False,recovery_policy=dict(primary_denied=True,replay_images=7,next_update='invented_only',original_target_reads=0,real_optimizer_calls=0),readiness=readiness);executor.validate_request(r);return r

def prepare(phase,meta_pin=None):
    ceilings=freeze_budget(phase)
    if phase=='rehearsal':provider=data.InventedInputs(144);reader=targets.InventedTargets(provider);scope=reader.scope
    else:
        require(isinstance(meta_pin,str),'Fresh metadata receipt required');m=source.verify_package(META,meta_pin);require(m['state']=='stat_only_verified' and m['source_pins']==pins() and m['runtime']==runtime(),'Metadata/code/runtime drift')
        _,old,cases,rows=real_inputs();fresh=[]
        for r,v in zip(rows,m['files']):
            require(all(r[k]==v[k] for k in ('study_id','kind','uri')) and r['sha256']==v['retained_sha256'] and r['observation']==v['old'] and set(v['changed_fields'])<={'device'},'Metadata target identity changed');fresh.append(r|dict(observation=v['current']))
        provider=data.resolve_qualified();scope=targets.original_scope(cases,fresh,old['capability']|dict(operations=['full_compressed_hash','full_gzip_decode_native_targets']),meta_pin)
        require(scope['limits']==dict(hash_bytes=1265220,decode_bytes=1265220,expanded_bytes=272494704),'Original14 scope totals changed')
    r=request_for(provider,scope,phase,ceilings);d=dest(phase);d.mkdir();executor.put(d/'request.json',canonical(r));print(digest(canonical(r)))

def checked(phase,pin):
    path=dest(phase)/'request.json';raw=path.read_bytes();require(path.resolve(strict=True)==path and digest(raw)==pin,'Exact launch transport changed');r=json.loads(raw);executor.validate_request(r)
    require(r['source_pins']==pins() and r['runtime']==runtime() and r['storage_capability']==json.loads(CAPS[phase].read_bytes()) and r['storage_ceilings']==json.loads(budget_path(phase).read_bytes())['ceilings'] and r['identity']['domain']==('invented_arrays_only' if phase=='rehearsal' else 'qualified_real_cache'),'Launch source/runtime/capability/phase drift')
    if phase=='real':
        m=source.verify_package(META,r['targets']['metadata_receipt_sha256']);require(m['source_pins']==pins() and [v['current'] for v in m['files']]==[v['observation'] for v in r['targets']['files']],'Fresh target stat proof drift')
        raw=READY.read_bytes();ready=json.loads(raw);require(digest(raw)==r['readiness']['acceptance_sha256'] and ready['state']=='qualified_short_executor' and ready['source_pins']==pins() and ready['runtime']==runtime() and all(ready[k]==r['readiness'][k] for k in ('producer_receipt_sha256','recovery_receipt_sha256','tests_sha256')),'Readiness acceptance drift')
    return r

def accept_readiness(producer_pin,recovery_pin,tests_pin):
    producer=source.verify_package(dest('rehearsal'),producer_pin);recovery=source.verify_package(ROOT/(dest('rehearsal').name+'-RECOVERY'),recovery_pin);raw=TESTS.read_bytes();require(digest(raw)==tests_pin,'Native test record changed');tests=json.loads(raw)
    require(producer['state']=='producer_complete' and producer['phase']=='rehearsal' and producer['optimizer_calls']==48 and producer['real_optimizer_calls']==producer['original_target_arrays']==0 and producer['source_pins']==pins() and producer['runtime']==runtime(),'Incomplete invented producer qualification')
    t=producer['transaction'];require(t['completed_steps']==48 and [p['primary']['step'] for p in t['checkpoints']]==[0,6,24,48] and sorted(t['exposure'].values())==[8]*6 and len(t['exports'])==7,'Incomplete epoch/checkpoint/export qualification')
    require(recovery['state']=='passed' and recovery['phase']=='rehearsal' and recovery['request_sha256']==producer['request_sha256'] and recovery['source_pins']==pins() and recovery['runtime']==runtime() and recovery['primary_reads_blocked'] and len(recovery['restores'])==14 and len(recovery['native_checks'])==7 and all(c['prediction_exact'] for c in recovery['native_checks']) and recovery['probability_max_difference']<=1e-6 and recovery['next_weight_max_difference']<=1e-6 and recovery['optimizer_calls']==1 and recovery['real_optimizer_calls']==recovery['original_target_arrays']==recovery['original_ct_arrays']==0,'Incomplete independent recovery qualification')
    require(tests['state']=='passed' and tests['source_pins']==pins() and tests['runtime']==runtime() and tests['native_passes']>=2574 and tests['focused_passes']>=119,'Native tests not qualified for exact source/runtime')
    source.put(READY,dict(state='qualified_short_executor',decision='D-327',producer_receipt_sha256=producer_pin,recovery_receipt_sha256=recovery_pin,tests_sha256=tests_pin,source_pins=pins(),runtime=runtime(),real_updates_allowed=False,real_launch_pending_approval=True));print(digest(READY.read_bytes()))

def approved(phase,r,approval_path=None,approval_pin=None):
    if phase=='rehearsal':require(approval_path is None and approval_pin is None,'Rehearsal cannot use real approval');return None
    require(approval_path is not None and approval_pin is not None,'Prepared real run lacks exact launch approval')
    path=Path(approval_path);require(path==REPO/'configs/local/segmenter-short-launch-approval.json' and path.resolve(strict=True)==path and not path.is_symlink(),'Wrong exact launch authority record');return executor.authorize(r,path.read_bytes(),trusted_approval_sha256=approval_pin)

def guard(d,start,r,*,recovery=False):
    require(time.monotonic()-start<r['limits']['recovery_seconds' if recovery else 'producer_seconds'] and prior.rss()<=r['limits']['rss_bytes'] and shutil.disk_usage(REPO).free>=r['limits']['free_bytes'],'Worker time/RSS/free envelope');prior.check_output(d,r['limits']['output_bytes']);torch.mps.synchronize();require(torch.mps.driver_allocated_memory()<=r['limits']['driver_bytes'] and q.power()[0],'Worker driver/power envelope')

def worker(phase,pin,approval_path=None,approval_pin=None):
    r=checked(phase,pin);grant=approved(phase,r,approval_path,approval_pin);d=dest(phase);source.put(d/'worker-consumed.json',dict(request_sha256=pin));start=time.monotonic();torch.set_num_threads(2);torch.mps.set_per_process_memory_fraction(min(1.,r['limits']['driver_bytes']/torch.mps.recommended_max_memory()));signal.alarm(r['limits']['producer_seconds']);memory=[]
    def interrupted(sig,frame):raise InterruptedError('Worker signal '+str(sig))
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGALRM):signal.signal(sig,interrupted)
    def tick():
        guard(d,start,r);memory.append(dict(seconds=time.monotonic()-start,rss_bytes=prior.rss(),driver_bytes=torch.mps.driver_allocated_memory(),allocated_bytes=torch.mps.current_allocated_memory()))
    try:
        provider=data.InventedInputs(144) if phase=='rehearsal' else data.resolve_qualified();tick();reader=targets.InventedTargets(provider) if phase=='rehearsal' else targets.RealTargets(provider,r,grant);require(reader.scope==r['targets'] if phase=='rehearsal' else canonical(provider.control)==r['controls']['inputs.json'].encode(),'Consumed input/reference scope differs');ss=stores(phase,ceilings=r['storage_ceilings'])
        def write_view(sid,png,view):executor.put(d/(sid.split(':')[-1]+'-view.png'),png);source.put(d/(sid.split(':')[-1]+'-view.json'),view)
        def finish(s,refs,prob,next_weights,event,check):return executor.finalize(r,s,provider,ss,reader,refs,prob,next_weights,event,check,write_view=write_view)
        protect=lambda files,i:executor.keep(ss,i,files,i['run_id']+':summary','segmenter-short-run-summary',lambda f,j:evidence.validate_summary(f,r),derivation=pin)
        result=executor.execute(r,provider,d,save_checkpoint=lambda s:executor.checkpoint(ss,s),finish=finish,protect_summary=protect,grant=grant,guard=tick,verify_source=lambda:checked(phase,pin))
        checked(phase,pin);tick();source.put(d/'result.json',dict(state='producer_complete',decision='D-327',phase=phase,request_sha256=pin,transaction=result,optimizer_calls=48,real_optimizer_calls=48 if phase=='real' else 0,original_target_arrays=14 if phase=='real' else 0,original_ct_arrays=0,source_counts=reader.counts,memory=memory,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),source_pins=pins(),runtime=runtime()))
    except BaseException as exc:source.put(d/'worker-failure.json',dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),source_counts=reader.counts if 'reader' in locals() else None,attempted_target_cases=sorted(reader.used) if 'reader' in locals() else [],transaction_failure=json.loads((d/'transaction-failure.json').read_bytes()) if (d/'transaction-failure.json').exists() else None));raise
    finally:signal.alarm(0)

def recovery_worker(phase,pin,producer_pin):
    r=checked(phase,pin);producer=source.verify_package(dest(phase),producer_pin);require(producer['state']=='producer_complete' and producer['request_sha256']==pin and producer['source_pins']==pins(),'Wrong/unpinned producing transaction');d=ROOT/(dest(phase).name+'-RECOVERY');source.put(d/'worker-consumed.json',dict(request_sha256=pin,producer_receipt_sha256=producer_pin));start=time.monotonic();signal.alarm(r['limits']['recovery_seconds']);torch.set_num_threads(2);block_primary()
    with source.directory('/Volumes') as fd:
        try:os.open('PROWL-Data',os.O_RDONLY|os.O_DIRECTORY,dir_fd=fd);raise AssertionError('Primary guard inactive')
        except ValueError:pass
    guard_fn=lambda:guard(d,start,r,recovery=True);ss=stores(phase,recovery=True,ceilings=r['storage_ceilings']);t=producer['transaction'];i=r['identity'];restores=[];deltas=[]
    def restore(pair,validator):
        files,ref=restore_backup(ss[1],ss[2],pair['backup'],pair['primary'],i,validator=validator);restores.append(dict(primary=pair['primary'],backup=pair['backup'],restore=ref,members=len(files),bytes=sum(map(len,files.values()))));guard_fn();return files
    summary=restore(t['summary_reference'],lambda f,j:evidence.validate_summary(f,r));evidence.validate_summary(summary,r);require(json.loads(summary['completion.json'])=={k:v for k,v in t.items() if k!='summary_reference'},'Protected summary differs from pinned producer');images=restore(t['images_reference'],lambda f,j:evidence.validate_images(f,r));probes=restore(t['probe_reference'],lambda f,j:evidence.validate_probes(f,j,r));manifest=json.loads(probes['manifest.json']);require(manifest['checkpoints']==t['checkpoints'] and manifest['exports']==t['exports'],'Probe references differ from complete summary');x=inverse.decode_array(probes['image.npy'],[1,144,144,144],'float32');selected=None;terminal=None
    for pair in t['checkpoints']:
        files=restore(pair,core.validate_payload);s=core.restore_payload(files,i);p=s.predict(x);expected=inverse.decode_array(probes[f'prob-{s.step}.npy'],[3,144,144,144],'float32');delta=float(np.max(np.abs(p-expected)));require(delta<=1e-6,'Cold checkpoint probability drift');deltas.append(delta)
        if s.step==6:selected=s
        elif s.step==48:terminal=s
        else:del s
        del files,p,expected;guard_fn()
    require(terminal is not None and selected is not None,'Required cold checkpoints missing');native_scores=json.loads(summary['scores.json']);native_checks=[]
    for n,(case,pair) in enumerate(zip(r['targets']['cases'],t['exports'])):
        context=dict(identity=i,case=case,step=48,weights_sha256=t['weights_sha256']);files=restore(pair,lambda f,j,context=context:evidence.validate_export(f,context));image=inverse.decode_array(images[f'image-{n:02d}.npy'],[1,144,144,144],'float32');p=terminal.predict(image);mask,report=inverse.export(p,case,tick=guard_fn);require(inverse.array_bytes(mask)==files['mask.npy'] and digest(inverse.array_bytes(p))==pair['report']['probability_sha256'],'Cold native/probability export drift')
        if phase=='rehearsal':
            negative=case['descriptor']['lesion_target_state']=='verified_negative';pan,les=targets.invented_arrays(negative);score=scoring.score(mask,pan,les,target_state=case['descriptor']['lesion_target_state'],tick=guard_fn);require(all(score[k]==native_scores[n][k] for k in score),'Cold invented native metrics differ');del pan,les
        native_checks.append(dict(study_id=case['study_id'],native_sha256=digest(files['mask.npy']),prediction_exact=True));del files,image,p,mask;gc.collect();guard_fn()
    next_delta=None;calls=0
    if phase=='rehearsal':
        selected.update(data.InventedInputs(144));calls=1;expected=torch.load(evidence.codec.BytesIO(probes['next-weights.pt']),map_location='cpu',weights_only=True);next_delta=max(float((v.detach().cpu()-expected[n]).abs().max()) for n,v in selected.model.state_dict().items());require(next_delta<=1e-6,'Cold next-update drift')
    guard_fn();source.put(d/'result.json',dict(state='passed',decision='D-327',phase=phase,request_sha256=pin,restores=restores,primary_reads_blocked=True,probability_max_difference=max(deltas),native_checks=native_checks,next_weight_max_difference=next_delta,optimizer_calls=calls,real_optimizer_calls=0,original_target_arrays=0,original_ct_arrays=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),driver_bytes=torch.mps.driver_allocated_memory(),source_pins=pins(),runtime=runtime()));signal.alarm(0)

def supervise(phase,pin,*,recover=False,approval_path=None,approval_pin=None,producer_pin=None):
    r=checked(phase,pin)
    if not recover:approved(phase,r,approval_path,approval_pin)
    else:require(isinstance(producer_pin,str) and len(producer_pin)==64,'Independent producing receipt required for recovery');source.verify_package(dest(phase),producer_pin)
    d=dest(phase) if not recover else ROOT/(dest(phase).name+'-RECOVERY')
    if recover:d.mkdir()
    source.put(d/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry',approval_sha256=approval_pin));command=[sys.executable,'-m','scripts.diagnostics.segmenter_short_launch','--recovery-worker' if recover else '--worker','--phase',phase,'--request-sha256',pin]
    if approval_path is not None and not recover:command+=['--approval-path',str(approval_path),'--approval-sha256',approval_pin]
    if recover:command+=['--producer-sha256',producer_pin]
    start=time.monotonic();peak=0;child=None;seconds=r['limits']['recovery_seconds' if recover else 'producer_seconds'];previous_seconds=json.loads((dest(phase)/'supervision.json').read_bytes())['seconds'] if recover else 0.
    try:
        with (d/'worker.log').open('xb') as log:
            child=subprocess.Popen(command,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            while child.poll() is None:
                observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(child.pid)],capture_output=True,text=True,timeout=5)
                if child.poll() is None:require(observed.returncode==0 and observed.stdout.strip(),'RSS monitor unavailable');peak=max(peak,int(observed.stdout.strip())*1024)
                require(time.monotonic()-start<seconds and previous_seconds+time.monotonic()-start<r['limits']['total_seconds'] and peak<=r['limits']['rss_bytes'] and shutil.disk_usage(REPO).free>=r['limits']['free_bytes'] and q.power()[0],'Native supervisor resource/power envelope');time.sleep(.25)
            require(child.returncode==0,'Worker exit '+str(child.returncode))
        checked(phase,pin);source.put(d/'supervision.json',dict(seconds=time.monotonic()-start,observed_peak_rss_bytes=peak,exit_code=0));print(prior.package(d))
    except BaseException as exc:
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
        source.put(d/'failure.json',dict(state='consumed_incomplete',error_type=type(exc).__name__,message=str(exc),seconds=time.monotonic()-start));print('preserved_failed_job',prior.package(d));raise
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)

if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    for name in ('metadata','prepare','run','recover','worker','recovery-worker','accept-readiness'):g.add_argument('--'+name,action='store_true')
    parser.add_argument('--phase',choices=['rehearsal','real']);parser.add_argument('--request-sha256');parser.add_argument('--metadata-sha256');parser.add_argument('--approval-path',type=Path);parser.add_argument('--approval-sha256');parser.add_argument('--producer-sha256');parser.add_argument('--recovery-sha256');parser.add_argument('--tests-sha256');a=parser.parse_args()
    if a.accept_readiness:accept_readiness(a.producer_sha256,a.recovery_sha256,a.tests_sha256)
    elif a.metadata:metadata()
    elif a.prepare:prepare(a.phase,a.metadata_sha256)
    elif a.worker:worker(a.phase,a.request_sha256,a.approval_path,a.approval_sha256)
    elif a.recovery_worker:recovery_worker(a.phase,a.request_sha256,a.producer_sha256)
    else:supervise(a.phase,a.request_sha256,recover=a.recover,approval_path=a.approval_path,approval_pin=a.approval_sha256,producer_pin=a.producer_sha256)
