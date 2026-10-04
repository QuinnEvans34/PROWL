"""D-325 one-shot original14-target scoring and independent semantic recovery."""
import argparse,gc,io,json,os,shutil,signal,sys,time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import numpy as np
from src.training import segmenter_native_scoring_v1 as core
from src.data import segmenter_content_v1 as content,segmenter_geometry_loader_v1 as loader
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require,content_hash
from src.operations.segmenter_score_storage_v1 import score_stores
from src.operations.segmenter_score_backup_v1 import backup_checkpoint,restore_backup
from src.operations.segmenter_inference_storage_v1 import inference_stores
from src.operations.segmenter_primary_read_guard_v1 import install as block_primary
from scripts.diagnostics import segmenter_source_verification as source,segmenter_content_pilot as prior
REPO=source.REPO;ROOT=REPO/'outputs/prowl'
PROFILE=ROOT/'SEGMENTER-NATIVE-SCORE-SYNTHETIC-attempt02-20261002';META=ROOT/'SEGMENTER-NATIVE-SCORE-METADATA-attempt02-20261002';DEST=ROOT/'SEGMENTER-NATIVE-SCORE-REAL-attempt02-20261002';RECOVERY=ROOT/'SEGMENTER-NATIVE-SCORE-RECOVERY-attempt02-20261002';BUDGET=ROOT/'SEGMENTER-NATIVE-SCORE-BUDGET-20261002.json'
REVIEW=ROOT/'SEGMENTER-INFERENCE-REVIEW-20261002';ACCEPT_PIN='7cb2ba5da7ce47b1bdc5e681da662cf14567c2d472871bb03e4b3f121dd14e40';REVIEW_PIN='11a11afe66baadbe8df2bce3391cb2d0b236228167183d238771dc615c0dfdae';PROPOSAL_PIN='8b462a81ada69592065b8291f8982b31bb6f8ab7ff502b6a42a43ca01ee984d9'
CAP=REPO/'docs/capstone/operations/SEGMENTER-SCORE-STORAGE-CAPABILITY-2026-10-02.json';CAP_PIN='4528cf8bbdc2a08eb8e39e5bade41fcbcffc9d799ed573949f282b4cc1a0a28c'
LIMITS=dict(seconds=1200,rss_bytes=8*1024**3,free_bytes=100*1024**3,output_bytes=32*1024**2,hash_bytes=1265220,decode_bytes=1265220,expanded_bytes=272494704)
CODE=['src/training/segmenter_native_scoring_v1.py','src/operations/segmenter_score_storage_v1.py','src/operations/segmenter_score_backup_v1.py','scripts/diagnostics/segmenter_native_scoring.py','tests/test_segmenter_native_scoring.py','tests/test_segmenter_native_score_transaction.py',str(CAP.relative_to(REPO))]


def inputs():
    raw=(REVIEW/'receipt.json').read_bytes();require(digest(raw)==REVIEW_PIN,'Inference review changed');receipt=json.loads(raw)
    require(set(p.name for p in REVIEW.iterdir())==set(receipt['files'])|{'receipt.json'},'Inference review inventory changed')
    for n,v in receipt['files'].items():
        p=REVIEW/n;require(p.resolve()==p and not p.is_symlink(),'Unsafe review member');b=p.read_bytes();require(dict(bytes=len(b),sha256=digest(b))==v,'Inference review member changed')
    raw=(REVIEW/'accepted-inference.json').read_bytes();require(digest(raw)==ACCEPT_PIN,'Inference acceptance changed');a=json.loads(raw)
    require(a['model_updates']==0 and a['optimizer_allowed'] is False and a['guarded_real_probe']['native_mask_exact'] and a['guarded_real_probe']['prediction_max_abs_difference']==0,'Unqualified step0 outputs')
    proposal=json.loads(source.safe_local(str((REVIEW/'native-reference-scope-proposal.json').relative_to(REPO)),PROPOSAL_PIN))
    old=json.loads((ROOT/'SEGMENTER-CACHE-BUILD-attempt02-20261002/request.json').read_bytes());require(digest((ROOT/'SEGMENTER-CACHE-BUILD-attempt02-20261002/request.json').read_bytes())=='d84cdcdc828410ed4603dccf1bab29ecf6d0e9154f9a4f6f3f9f9cd0bc613364','Source binding request changed')
    cases=[dict(study_id=e['descriptor']['study_id'],protected_role=e['descriptor']['protected_role'],descriptor=e['descriptor'],fidelity=e['fidelity']) for e in old['binding']['entries']]
    require(proposal['files']==[r for r in old['files'] if r['kind'] in ('pancreas','lesion')] and len(proposal['files'])==14,'Exact target proposal drift')
    return a,old,cases,proposal['files']


def pins():
    a,_,_,_=inputs();fixed=a['source_pins']|a['supplemental_source_pins'];require(all(digest((REPO/n).read_bytes())==h for n,h in fixed.items()),'D-319–324 producing code changed')
    require(digest(CAP.read_bytes())==CAP_PIN,'Scoring capability changed');return fixed|{n:digest((REPO/n).read_bytes()) for n in CODE}


def runtime():
    import importlib.metadata
    return source.runtime()|dict(scipy=importlib.metadata.version('scipy'),threads=2,model_runtime_used=False)


def stores(create=False,recovery=False,ceilings=None):
    ss=score_stores(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,create=create,recovery_only=recovery)
    if ceilings:
        for s,c in zip(ss,ceilings):
            if s:s.quota_bytes=min(s.quota_bytes,c)
    return ss


def tick(dest,start,seconds=1200):
    require(time.monotonic()-start<seconds and prior.rss()<=LIMITS['rss_bytes'],'Score time/RSS ceiling');require(shutil.disk_usage(REPO).free>=LIMITS['free_bytes'],'Internal free floor');prior.check_output(dest,LIMITS['output_bytes'])


def metadata():
    pins();META.mkdir();start=time.monotonic();signal.alarm(120);_,old,_,rows=inputs();cap=old['capability']|dict(operations=['stat']);before=source.mount_guard(cap);proofs=[]
    def deny_payload(event,args):
        if event=='open' and args and isinstance(args[0],(str,bytes)) and os.fsdecode(args[0]).endswith(('.nii','.nii.gz')):raise ValueError('Stat-only scope forbids payload opens')
    sys.addaudithook(deny_payload)
    with source.directory(cap['source_root']) as fd:
        for r in rows:
            tick(META,start,120);obs=source.observe(fd,r|dict(expected_bytes=r['compressed_bytes']));require(obs['state']=='observed','Target stat hold');cur=obs['observation'];changes=[k for k in cur if cur[k]!=r['observation'][k]]
            require(set(cur)==set(r['observation']) and set(changes)<= {'device'} and cur['device']==before['root_device'],'Nonvolatile source change requires investigation')
            proofs.append(dict(study_id=r['study_id'],kind=r['kind'],uri=r['uri'],old=r['observation'],current=cur,changed_fields=changes,retained_sha256=r['sha256']))
    after=source.mount_guard(cap);require(before==after,'Source mount changed')
    source.put(META/'result.json',dict(state='stat_only_verified',decision='D-325',files=proofs,mount_before=before,mount_after=after,source_arrays_read=0,hash_bytes=0,decode_bytes=0,model_forwards=0,model_updates=0,code_pins=pins(),runtime=runtime(),seconds=time.monotonic()-start));signal.alarm(0);print(prior.package(META))


def oracle(pred,pan,les,tick=lambda:None):
    # Nine separate boolean intersections, independent of the encoded-histogram scorer.
    m=np.zeros((3,3),np.int64)
    for z in range(0,pred.shape[2],16):
        tick();ss=(slice(None),slice(None),slice(z,z+16));truth=[(pan[ss]==0)&(les[ss]==0),(pan[ss]==1)&(les[ss]==0),les[ss]==1]
        for a in range(3):
            for b in range(3):m[a,b]+=np.count_nonzero(truth[a]&(pred[ss]==b))
    return dict(state='passed',confusion_matrix=m.tolist())


def profile_worker():
    PROFILE.mkdir();source.put(PROFILE/'started.json',dict(code_pins=pins(),runtime=runtime()));start=time.monotonic();signal.alarm(1200);guard=lambda:tick(PROFILE,start);arrays={};dec=[]
    for kind in ('pancreas','lesion'):
        blob,row=prior.invented_file(kind,'fragmented',(512,402,197));limits=dict(hash_bytes=len(blob),decode_bytes=len(blob),expanded_bytes=row['expanded_bytes']);counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0)
        content.hash_exact(io.BytesIO(blob),row,counts,limits,guard);stored,h,r=content.decode_exact(io.BytesIO(blob),row,counts,limits,guard);mask,report=content.target_content(stored,h,guard);arrays[kind]=mask;dec.append(dict(kind=kind,counts=counts,decoding=report));del blob,stored;gc.collect()
    results=[]
    for pattern in ('empty','dense_wrong','sparse','fragmented'):
        pred=np.zeros((512,402,197),np.uint8)
        if pattern=='dense_wrong':pred[:]=2
        elif pattern=='sparse':pred[::64,::64,::32]=2
        elif pattern=='fragmented':pred[::4,::4,::4]=2
        r=core.score(pred,arrays['pancreas'],arrays['lesion'],target_state='positive',tick=guard);o=oracle(pred,arrays['pancreas'],arrays['lesion'],guard);require(o['confusion_matrix']==r['confusion_matrix'],'Synthetic independent oracle differs');results.append(dict(pattern=pattern,score=r,oracle=o));del pred;gc.collect()
    source.put(PROFILE/'result.json',dict(state='passed',decision='D-325',code_pins=pins(),runtime=runtime(),native_voxels=40547328,patterns=results,decoding=dec,source_arrays_read=0,ct_arrays_read=0,model_forwards=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss()));signal.alarm(0)


def profile():
    require(not PROFILE.exists(),'Profile consumed');report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_native_scoring','--profile-worker'],1200,LIMITS['rss_bytes'],ROOT/'SEGMENTER-NATIVE-SCORE-SYNTHETIC-attempt02-20261002.log');source.put(PROFILE/'supervision.json',report);print(prior.package(PROFILE))


def build_request(meta_pin,profile_pin):
    a,old,cases,rows=inputs();m=source.verify_package(META,meta_pin);p=source.verify_package(PROFILE,profile_pin)
    require(m['state']=='stat_only_verified' and p['state']=='passed' and m['code_pins']==p['code_pins']==pins() and m['runtime']==p['runtime']==runtime(),'Metadata/profile code/runtime unqualified')
    fresh=[]
    for r,v in zip(rows,m['files']):
        require(all(r[k]==v[k] for k in ('study_id','kind','uri')) and r['sha256']==v['retained_sha256'] and r['observation']==v['old'] and set(v['changed_fields'])<= {'device'} and all(v['old'][k]==v['current'][k] for k in v['old'] if k!='device'),'Metadata ancestry differs');fresh.append(r|dict(observation=v['current']))
    require(all(sum(r[f] for r in fresh)==LIMITS[k] for k,f in [('hash_bytes','compressed_bytes'),('decode_bytes','compressed_bytes'),('expanded_bytes','expanded_bytes')]),'Read byte totals differ')
    return dict(schema_version='segmenter-native-score-request-1',decision='D-325',task=core.TASK,stage='original_native_scoring',cases=cases,records=old['binding']['records'],cohort_completion_sha256=loader.COMPLETION,descriptor_sha256=loader.DESCRIPTORS,files=fresh,prediction_exports=a['cases'],prediction_reference=a['primary_reference'],inference_acceptance_sha256=ACCEPT_PIN,metadata_receipt_sha256=meta_pin,profile_receipt_sha256=profile_pin,capability=old['capability']|dict(operations=['full_compressed_hash','full_gzip_decode_native_targets']),storage_capability_sha256=CAP_PIN,storage_ceilings=json.loads(BUDGET.read_bytes())['ceilings'],limits=LIMITS,code_pins=pins(),runtime=runtime(),ct_reads_allowed=False,model_updates_allowed=False,qualifications_granted=False,output=str(DEST))


def checked(pin):
    raw=(DEST/'request.json').read_bytes();require(digest(raw)==pin,'Request transport changed');r=json.loads(raw);require(r==build_request(r['metadata_receipt_sha256'],r['profile_receipt_sha256']),'Exact request/code/runtime changed');return r


def prepare(meta_pin,profile_pin):
    ss=stores(create=True)
    if BUDGET.exists():
        budget=json.loads(BUDGET.read_bytes());require(budget['decision']=='D-325' and budget['capability_sha256']==CAP_PIN and len(budget['ceilings'])==3 and all(type(c) is int and c>0 and c<=s.quota_bytes for c,s in zip(budget['ceilings'],ss)), 'Original frozen scoring budget differs')
    else:source.put(BUDGET,dict(decision='D-325',capability_sha256=CAP_PIN,ceilings=[s.quota_bytes for s in ss]))
    r=build_request(meta_pin,profile_pin);DEST.mkdir()
    # Transport, source-read guard and protected payload use the same exact canonical bytes.
    with (DEST/'request.json').open('xb') as stream:
        stream.write(canonical(r));stream.flush();os.fsync(stream.fileno())
    print(digest((DEST/'request.json').read_bytes()))


def inference_validation(files,identity):
    require(files['identity.json']==canonical(identity),'Accepted inference identity differs')
    require(set(files)=={'identity.json','state.pt','probe-image.npy','probe-probabilities.npy','exports.json'}|{f'case-{i:02d}-native.npy' for i in range(7)},'Accepted prediction inventory differs')
    require(identity['task']=='pancreas_lesion_segmenter_step0_inference_v1' and identity['config']['completed_updates']==0 and identity['config']['architecture']['out_channels']==3,'Wrong accepted prediction task')
    return dict(task=identity['task'],completed_updates=0,identity_sha256=content_hash(identity),initial_weight_sha256=identity['initial_weight_sha256'],members={n:dict(bytes=len(v),sha256=digest(v)) for n,v in files.items()})


def predictions(req):
    cap=REPO/'docs/capstone/operations/SEGMENTER-INFERENCE-STORAGE-CAPABILITY-2026-10-02.json';ss=inference_stores(REPO/'configs/local/roots.yaml',cap.read_bytes(),trusted_capability_sha256='35ccc397c163b91b5e4f4accedf85653519d53534a996b24b81f3e29c702731f')
    raw=(ROOT/'SEGMENTER-INFERENCE-REAL-20261002/request.json').read_bytes();require(digest(raw)=='cfac9e1afd8e4324713557f5e816a62e8d09c477fed756dc4760d42a22850f50','Inference source request changed');identity=json.loads(raw)['identity'];ref=req['prediction_reference']
    files,_=ss[0].resolve(ref['artifact_id'],receipt_sha256=ref['receipt_sha256'],expected_derivation=ref['derivation_sha256'],validate=lambda f:inference_validation(f,identity));require(json.loads(files['exports.json'])==req['prediction_exports'],'Prediction export records differ');return files


def read_case(session,req,pin,sid,operation,rootfd,counts,guard):
    require(type(session) is loader.ResolvedInputs and digest(canonical(req))==pin and req['task']==core.TASK and req['stage']=='original_native_scoring' and req['ct_reads_allowed'] is False and req['model_updates_allowed'] is False,'Unreplayed/wrong-stage scoring request')
    require(req['records']==session.records and req['cohort_completion_sha256']==loader.COMPLETION and req['descriptor_sha256']==loader.DESCRIPTORS and len(req['cases'])==7 and len(req['files'])==14 and {(r['study_id'],r['kind']) for r in req['files']}=={(c['study_id'],k) for c in req['cases'] for k in ('pancreas','lesion')},'Exact target inventory/ancestry differs')
    require(req['capability']['operations']==['full_compressed_hash','full_gzip_decode_native_targets'] and req['capability']['source_writes'] is False and req['capability']['global_activation'] is False,'Wrong source capability')
    d=session.select(sid,operation);m=source.mount_guard(req['capability']);s=os.fstat(rootfd);require((s.st_dev,s.st_ino)==(m['root_device'],m['root_inode']),'Wrong held source root')
    return core.read_targets(rootfd,d,[r for r in req['files'] if r['study_id']==sid],counts,req['limits'],guard)


def worker(pin):
    req=checked(pin);require(json.loads((DEST/'consumed.json').read_bytes())['request_sha256']==pin,'No parent claim');source.put(DEST/'worker-consumed.json',dict(request_sha256=pin));start=time.monotonic();signal.alarm(1200);guard=lambda:tick(DEST,start);counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);session=loader.resolve_registered();require(session.records==req['records'],'Registered roles/purposes drift');guard();pred=predictions(req);before=source.mount_guard(req['capability']);scores=[];refs=[]
    with source.directory(req['capability']['source_root']) as fd:
        for i,c in enumerate(req['cases']):
            sid=c['study_id'];source.put(DEST/(sid.split(':')[-1]+'-reservation.json'),dict(request_sha256=pin,study_id=sid,counts_before=counts.copy(),upper_counts={k:req['limits'][k] for k in counts}))
            pan,les,rr=read_case(session,req,pin,sid,c['descriptor']['operation'],fd,counts,guard);x=core.decode_prediction(pred[f'case-{i:02d}-native.npy'],c['descriptor']['geometry']['shape_xyz']);require(digest(pred[f'case-{i:02d}-native.npy'])==req['prediction_exports'][i]['native_sha256'],'Prediction bytes differ')
            score=core.score(x,pan,les,target_state=c['descriptor']['lesion_target_state'],tick=guard);o=oracle(x,pan,les,guard);require(o['confusion_matrix']==score['confusion_matrix'],'Independent native confusion oracle differs')
            record=dict(study_id=sid,protected_role=c['protected_role'],source_shape=list(x.shape),source_affine=np.asarray(c['descriptor']['geometry']['affine_ras']).reshape(4,4).tolist(),prediction_sha256=req['prediction_exports'][i]['native_sha256'],**score,oracle=o);scores.append(record);refs.extend(rr)
            source.put(DEST/(sid.split(':')[-1]+'.json'),dict(score=record,references=rr,counts_after=counts.copy()));print(json.dumps(dict(case=sid,metrics=score['metrics'])),flush=True);del pan,les,x;gc.collect();guard()
    after=source.mount_guard(req['capability']);require(before==after and counts=={k:req['limits'][k] for k in counts},'Incomplete source/mount accounting')
    production=dict(request_sha256=pin,source_counts=counts,source_arrays_read=14,ct_arrays_read=0,model_forwards=0,model_updates=0,code_pins=pins(),runtime=runtime(),mount_before=before,mount_after=after)
    files={'request.json':canonical(req),'scores.json':canonical(scores),'references.json':canonical(refs),'aggregates.json':canonical(core.aggregates(scores)),'production.json':canonical(production)};identity=dict(request=req,request_sha256=pin,source_sha256=content_hash(req['code_pins']),run_id='D-325');validation=core.validate_payload(files,identity);ss=stores(ceilings=req['storage_ceilings']);artifact_id='segmenter-native-score:D325:step0';metadata=dict(artifact_type='segmenter-native-score',schema_version='1.0.0',component=core.TASK,code_sha256=identity['source_sha256'],parents=[ACCEPT_PIN,loader.COMPLETION],retention='required_native_baseline_keeper',sensitivity='private_research',run_id='D-325',stage_id='native_reference_scoring')
    receipt,status=ss[0].publish(artifact_id,derivation_sha256=pin,files=files,metadata=metadata,validate=lambda f:core.validate_payload(f,identity));ref=dict(artifact_id=artifact_id,receipt_sha256=receipt,derivation_sha256=pin);cap=json.loads(CAP.read_bytes());back=backup_checkpoint(ss[0],ss[1],ref,identity,source_domain=cap['primary_volume_uuid'],destination_domain=cap['backup_volume_uuid']);guard()
    source.put(DEST/'result.json',dict(state='native_scoring_complete',decision='D-325',request_sha256=pin,primary_reference=ref,backup_reference=back,artifact_members=len(files),artifact_bytes=sum(map(len,files.values())),validation=validation,aggregate=core.aggregates(scores),counts=counts,source_arrays_read=14,ct_arrays_read=0,model_forwards=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),code_pins=pins(),runtime=runtime()));signal.alarm(0)


def recovery(pin):
    req=checked(pin);RECOVERY.mkdir();source.put(RECOVERY/'consumed.json',dict(request_sha256=pin));block_primary();start=time.monotonic();signal.alarm(1200)
    try:os.open('PROWL-Data',os.O_RDONLY);raise AssertionError('Primary component guard failed')
    except ValueError:pass
    identity=dict(request=req,request_sha256=pin,source_sha256=content_hash(req['code_pins']),run_id='D-325');r=json.loads((DEST/'result.json').read_bytes());_,back,restore=stores(recovery=True,ceilings=req['storage_ceilings']);files,ref=restore_backup(back,restore,r['backup_reference'],r['primary_reference'],identity);result=core.validate_payload(files,identity);tick(RECOVERY,start)
    source.put(RECOVERY/'result.json',dict(state='passed',decision='D-325',restore_reference=ref,validation=result,members=len(files),bytes=sum(map(len,files.values())),primary_reads_blocked=True,source_arrays_read=0,ct_arrays_read=0,model_forwards=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),code_pins=pins(),runtime=runtime()));signal.alarm(0)


def run(pin):
    checked(pin);source.put(DEST/'consumed.json',dict(state='consumed_no_retry',request_sha256=pin))
    try:
        report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_native_scoring','--worker','--request-sha256',pin],1200,LIMITS['rss_bytes'],DEST/'worker.log');checked(pin);source.put(DEST/'supervision.json',report);print(prior.package(DEST))
    except BaseException as e:source.put(DEST/'failure.json',dict(state='incomplete_consumed',error=str(e)));raise


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for n in ('metadata','profile','profile-worker','prepare','run','worker','recover','recovery-worker'):g.add_argument('--'+n,action='store_true')
    p.add_argument('--request-sha256');p.add_argument('--metadata-sha256');p.add_argument('--profile-sha256');a=p.parse_args();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Scoring deadline')))
    if a.metadata:metadata()
    elif a.profile:profile()
    elif a.profile_worker:profile_worker()
    elif a.prepare:prepare(a.metadata_sha256,a.profile_sha256)
    elif a.run:run(a.request_sha256)
    elif a.worker:worker(a.request_sha256)
    elif a.recovery_worker:recovery(a.request_sha256)
    else:
        checked(a.request_sha256);require(not RECOVERY.exists(),'Recovery consumed');report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_native_scoring','--recovery-worker','--request-sha256',a.request_sha256],1200,LIMITS['rss_bytes'],ROOT/'SEGMENTER-NATIVE-SCORE-RECOVERY-attempt02-20261002.log');source.put(RECOVERY/'supervision.json',report);print(prior.package(RECOVERY))

if __name__=='__main__':main()
