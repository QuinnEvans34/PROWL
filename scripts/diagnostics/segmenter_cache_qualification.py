"""D-323 synthetic cache qualification and one fresh exact seven-case source transaction."""
import argparse,gc,json,math,os,shutil,signal,sys,time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import numpy as np
from src.data import segmenter_cache_v1 as cache,segmenter_geometry_v1 as geometry,segmenter_geometry_loader_v1 as loader
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require,content_hash
from src.operations.segmenter_cache_storage_v1 import cache_store
from scripts.diagnostics import segmenter_source_verification as source,segmenter_content_pilot as prior,segmenter_geometry_qualification as old

REPO=source.REPO;ROOT=REPO/'outputs/prowl'
PROFILE=ROOT/'SEGMENTER-CACHE-SYNTHETIC-attempt02-20261002';DEST=ROOT/'SEGMENTER-CACHE-BUILD-attempt02-20261002';REPLAY=ROOT/'SEGMENTER-CACHE-REPLAY-attempt02-20261002'
METADATA=ROOT/'SEGMENTER-CACHE-METADATA-REFRESH-20261002';METADATA_PIN='b05746226f9fbd632c55151824b4f3d90fb3d530208ec1daafbd73fb4e9d9ba1'
CAP=REPO/'docs/capstone/operations/SEGMENTER-CACHE-STORAGE-CAPABILITY-2026-10-02.json';CAP_PIN='06a7220773ac5572a18c8ca3f5c995d2bce8be007cc68d90f5fb901414466087'
ACCEPT='outputs/prowl/SEGMENTER-GEOMETRY-REVIEW-20261001/accepted-geometry.json';ACCEPT_PIN='b3ff4db94b49f1ea9b44d57afd975c17f16309c9929df35fa3e0d9f7e67e7384'
OLD_DIR=ROOT/'SEGMENTER-GEOMETRY-FIDELITY-attempt02-20261001';OLD_PIN='5c958ac1877c52c2eefd55e3cfe0824428322ca72dbd12ad52043c02e1d8fe1f'
CODE=['src/data/segmenter_cache_v1.py','src/operations/segmenter_cache_storage_v1.py','scripts/diagnostics/segmenter_cache_qualification.py','tests/test_segmenter_cache.py','tests/test_segmenter_cache_qualification.py',str(CAP.relative_to(REPO))]
LIMITS=dict(seconds=1800,rss_bytes=8*1024**3,artifact_bytes=512*1024**2,output_bytes=32*1024**2,hash_bytes=145701969,decode_bytes=145701969,expanded_bytes=544986944)


def pins():
    saved=json.loads((ROOT/'segmenter-synthetic-ee61bda1-5637-4309-8d2b-4f9feb5318bc/invocation.json').read_bytes())
    fixed=json.loads(saved['controls']['source.json']);require(all(source.sha((REPO/n).read_bytes())==h for n,h in fixed.items()),'Old producing code changed')
    require(source.sha(CAP.read_bytes())==CAP_PIN,'Cache capability changed')
    return fixed|{n:source.sha((REPO/n).read_bytes()) for n in CODE}


def runtime():
    import importlib.metadata
    return source.runtime()|dict(scipy=importlib.metadata.version('scipy'),threads=2)


def refreshed_rows(rows,evidence):
    require(evidence['state']=='same_volume_volatile_device_only' and evidence['source_arrays_read']==evidence['hash_bytes']==evidence['header_bytes']==0 and evidence['retired_request_sha256']=='88568c2006b697155b735ac3504cac851b9e367733a9384a413b7beb3fcd650a','Wrong metadata-only evidence')
    require(evidence['mount_before']==evidence['mount_after'] and evidence['mount_before']['root_device']==evidence['files'][0]['current']['device'],'Metadata mount differs')
    require(len(rows)==len(evidence['files'])==21,'Exact metadata inventory differs')
    result=[]
    for row,proof in zip(rows,evidence['files']):
        require(all(row[k]==proof[k] for k in ('study_id','kind','uri')) and row['sha256']==proof['retained_sha256'] and row['observation']==proof['old'],'Metadata row ancestry differs')
        old=proof['old'];current=proof['current'];changed=[k for k in old if old[k]!=current[k]]
        require(set(old)==set(current) and set(changed)<= {'device'} and changed==proof['changed_fields'] and current['device']==evidence['mount_before']['root_device'],'Nonvolatile source change cannot be refreshed')
        result.append(row|dict(observation=current))
    return result


def inputs():
    acceptance=json.loads(source.safe_local(ACCEPT,ACCEPT_PIN));source.verify_package(OLD_DIR,OLD_PIN)
    scope=json.loads((ROOT/'SEGMENTER-GEOMETRY-SCOPE-attempt02-20261001/result.json').read_bytes())
    # Independently recorded scope receipt covers the retained records/file inventory.
    source.verify_package(ROOT/'SEGMENTER-GEOMETRY-SCOPE-attempt02-20261001','0161966208296a3342f55f1683566c98c103cc17b88f0d1a015f8c65655ab47f')
    require(scope['cohort_completion_sha256']==loader.COMPLETION and content_hash(scope['records'])==loader.DESCRIPTORS,'Stale retained registered scope')
    entries=[]
    for p in scope['projections']:
        sid=p['study_id'];d=loader.checked_descriptor(scope['records'],loader.DESCRIPTORS,sid,p['operation'])
        saved=json.loads((OLD_DIR/(sid.split(':')[-1]+'.json')).read_bytes());f=saved['fidelity']
        require(saved['transform']==p['transform'] and content_hash(p['transform'])==acceptance['transforms'][sid] and saved['screen']['passed'],'Accepted geometry evidence differs')
        c1=f['metrics']['pancreas_parenchyma']['tensor_voxels'];c2=f['metrics']['lesion']['tensor_voxels']
        entries.append(dict(operation=p['operation'],descriptor=d,transform=p['transform'],transform_sha256=content_hash(p['transform']),fidelity=f,tensor_class_counts=[144**3-c1-c2,c1,c2]))
    binding=dict(schema_version=cache.VERSION,cohort_completion_sha256=loader.COMPLETION,descriptor_sha256=loader.DESCRIPTORS,geometry_acceptance_sha256=ACCEPT_PIN,records=scope['records'],entries=entries,model_updates_allowed=False)
    require(cache.checked_binding(binding,content_hash(binding))==104509440,'Exact cache payload differs')
    require(len(scope['files'])==21 and set(scope['cases'])==set(acceptance['cases']),'Exact source membership differs')
    for e in entries:loader.check_rows(e['descriptor'],[r for r in scope['files'] if r['study_id']==e['descriptor']['study_id']])
    require(all(sum(r[field] for r in scope['files'])==LIMITS[key] for key,field in [('hash_bytes','compressed_bytes'),('decode_bytes','compressed_bytes'),('expanded_bytes','expanded_bytes')]),'Exact source byte accounting differs')
    scope=dict(scope);scope['files']=refreshed_rows(scope['files'],source.verify_package(METADATA,METADATA_PIN))
    return binding,scope


def store(create=False):
    cap=json.loads(CAP.read_bytes());return cache_store(REPO/'configs/local/roots.yaml',CAP.read_bytes(),trusted_capability_sha256=CAP_PIN,artifact_id=cap['artifact_id'],create=create)


def tick(dest,start,limits=LIMITS):
    require(time.monotonic()-start<limits['seconds'] and prior.rss()<=limits['rss_bytes'],'Cache worker time/RSS exceeded')
    require(shutil.disk_usage(REPO).free>=100*1024**3,'Internal disk reserve')
    prior.check_output(dest,limits['output_bytes'])


def profile_worker():
    start=time.monotonic();signal.alarm(1800);binding,_=inputs();guard=lambda:tick(PROFILE,start)
    shape=(512,402,197);a=np.diag([.78,.78,1.25,1.]);x=np.zeros(shape,np.float32);p=np.zeros(shape,np.uint8);l=np.zeros(shape,np.uint8)
    p[100:281,120:261,:81]=1;l[180:182,200:202,:2]=1;l[240:242,210:212,20:22]=1
    out=geometry.preprocess(x,p,l,a,geometry.recipe(),source_identity=dict(study_id='invented-largest',ct_sha256=digest(b'invented_CT')),lesion_target_state='positive',tick=guard)
    xr=cache.encode(out['image'][None]);yr=cache.encode(out['target'].astype(np.uint8));xx=cache.decode(xr,'image');yy=cache.decode(yr,'target')
    require(np.array_equal(xx,out['image'][None]) and np.array_equal(yy,out['target']),'Largest cache reload differs')
    rows=[dict(fixture='invented_largest_boundary_disconnected',native_voxels=math.prod(shape),image_bytes=len(xr),target_bytes=len(yr),counts=np.bincount(yy.ravel(),minlength=3).tolist(),fidelity=out['fidelity'])]
    del x,p,l,out,xx,yy;gc.collect();guard()
    # Seven serialization envelopes, including negative and outside-pancreas codes; no real source.
    blobs=[]
    for k in range(7):
        im=np.full((1,144,144,144),.5,np.float32);tg=np.zeros((144,144,144),np.uint8);tg[20:60,20:60,20:60]=1
        if k!=6:tg[0:2,30:32,30:32]=2;tg[80:82,80:82,80:82]=2
        xb=cache.encode(im);yb=cache.encode(tg);require(np.array_equal(cache.decode(xb,'image'),im) and np.array_equal(cache.decode(yb,'target'),tg),'Synthetic serial roundtrip differs');blobs.extend([xb,yb]);guard()
    require(sum(map(len,blobs))<LIMITS['artifact_bytes'],'Seven-array serialization cap')
    source.put(PROFILE/'result.json',dict(state='passed',decision='D-323',code_pins=pins(),runtime=runtime(),binding_sha256=content_hash(binding),largest=rows,serialized_seven_pair_bytes=sum(map(len,blobs)),source_arrays_read=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss()))
    signal.alarm(0)


def profile():
    pins();PROFILE.mkdir();source.put(PROFILE/'started.json',dict(decision='D-323',code_pins=pins(),runtime=runtime()))
    try:
        report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_cache_qualification','--profile-worker'],1800,8*1024**3,PROFILE/'worker.log')
        source.put(PROFILE/'supervision.json',report);print(json.dumps(dict(profile_receipt_sha256=prior.package(PROFILE),supervision=report)))
    except BaseException as e:source.put(PROFILE/'failure.json',dict(state='incomplete',error=str(e)));raise


def build_request(profile_pin,quota):
    b,s=inputs();pr=source.verify_package(PROFILE,profile_pin)
    require(pr['state']=='passed' and pr['code_pins']==pins() and pr['runtime']==runtime() and pr['binding_sha256']==content_hash(b) and pr['source_arrays_read']==pr['model_updates']==0,'Profile binding/source/runtime differs')
    return dict(schema_version='segmenter-cache-request-1',decision='D-323',stage='segmenter_cache_build',profile_receipt_sha256=profile_pin,source_metadata_receipt_sha256=METADATA_PIN,cohort_completion_sha256=loader.COMPLETION,descriptor_sha256=loader.DESCRIPTORS,binding=b,binding_sha256=content_hash(b),cases=s['cases'],files=s['files'],capability=s['capability'],cache_capability_sha256=CAP_PIN,cache_artifact_id=json.loads(CAP.read_bytes())['artifact_id'],cache_quota_bytes=quota,limits=LIMITS,code_pins=pins(),runtime=runtime(),output=str(DEST),serial=True,workers=0,model_updates_allowed=False,source_writes=False,qualifications_granted=False)


def checked_request(pin):
    require(DEST.resolve(strict=True)==DEST,'Unsafe request directory');raw=(DEST/'request.json').read_bytes();require(digest(raw)==pin,'Independent persisted request pin differs')
    req=json.loads(raw);require(type(req['cache_quota_bytes']) is int and 0<req['cache_quota_bytes']<=1024**3,'Invalid frozen quota')
    require(req==build_request(req['profile_receipt_sha256'],req['cache_quota_bytes']),'Exact request/code/runtime differs');return req


def prepare(profile_pin):
    st=store(create=True);req=build_request(profile_pin,st.store.quota_bytes);DEST.mkdir();source.put(DEST/'request.json',req)
    print(json.dumps(dict(request_sha256=digest((DEST/'request.json').read_bytes()),binding_sha256=req['binding_sha256'],limits=LIMITS,cache_artifact_id=req['cache_artifact_id'],cache_quota_bytes=req['cache_quota_bytes'])))


def read_case(session,req,pin,sid,operation,rootfd,counts,guard):
    require(type(session) is loader.ResolvedInputs and digest(source.encoded(req))==pin,'Exact replayed request required')
    require(req['stage']=='segmenter_cache_build' and req['model_updates_allowed'] is False and req['source_writes'] is False and req['capability']['operations']==['full_compressed_hash','full_gzip_decode_native_arrays'] and req['capability']['source_writes'] is False and req['capability']['global_activation'] is False,'Wrong cache stage/permissions')
    b=req['binding'];cache.checked_binding(b,req['binding_sha256']);require(session.records==b['records'] and req['cohort_completion_sha256']==loader.COMPLETION and req['descriptor_sha256']==loader.DESCRIPTORS,'Wrong cohort lineage')
    expected=[e['descriptor']['study_id'] for e in b['entries']];require(req['cases']==expected and len(req['files'])==21 and len(set(expected))==7 and {(r['study_id'],r['kind']) for r in req['files']}=={(s,k) for s in expected for k in ('ct','pancreas','lesion')},'Exact triple inventory differs')
    d=session.select(sid,operation);rows=[r for r in req['files'] if r['study_id']==sid];loader.check_rows(d,rows)
    m=source.mount_guard(req['capability']);s=os.fstat(rootfd);require((s.st_dev,s.st_ino)==(m['root_device'],m['root_inode']),'Wrong held source root')
    return loader.read_triple(rootfd,d,rows,counts,req['limits'],guard)


def validate_production(files,req,pin):
    value=cache.validate(files,req['binding'],req['binding_sha256']);p=json.loads(files['production.json'])
    require(p['request_sha256']==pin and p['code_pins']==req['code_pins'] and p['runtime']==req['runtime'] and p['source_counts']=={k:req['limits'][k] for k in ('hash_bytes','decode_bytes','expanded_bytes')},'Cache production/request/source accounting differs')
    return value


def worker(pin):
    req=checked_request(pin);start=time.monotonic();signal.alarm(1800);guard=lambda:tick(DEST,start);counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);files={'binding.json':canonical(req['binding'])};case_records=[]
    session=loader.resolve_registered();require(session.records==req['binding']['records'],'Fresh registered ancestry differs');guard();before=source.mount_guard(req['capability'])
    with source.directory(req['capability']['source_root']) as rootfd:
        for i,e in enumerate(req['binding']['entries']):
            d=e['descriptor'];sid=d['study_id'];stem=sid.split(':')[-1]
            source.put(DEST/(stem+'-reservation.json'),dict(request_sha256=pin,study_id=sid,counts_before=counts.copy(),upper_counts=req['limits']))
            ct,p,l,a,dec=read_case(session,req,pin,sid,e['operation'],rootfd,counts,guard)
            out=geometry.preprocess(ct,p,l,a,geometry.recipe(),source_identity=dict(study_id=sid,ct_sha256=d['image']['content_sha256']),lesion_target_state=d['lesion_target_state'],tick=guard)
            require(out['transform']==e['transform'] and out['fidelity']==e['fidelity'],'Fresh source transform/fidelity differs from accepted evidence')
            x,y=cache.arrays(out['image'][None],out['target'].astype(np.uint8),e);nm=cache.names(i)
            for kind,value in [('image',x),('target',y)]:files[nm[kind]]=cache.encode(value)
            row=dict(study_id=sid,protected_role=d['protected_role'],transform_sha256=e['transform_sha256'],tensor_class_counts=e['tensor_class_counts'],files={k:dict(name=n,bytes=len(files[n]),sha256=digest(files[n])) for k,n in nm.items()});case_records.append(row)
            source.put(DEST/(stem+'.json'),dict(**row,fidelity=out['fidelity'],decoding=dec,counts_after=counts.copy(),model_updates=0));print(json.dumps(dict(case=stem,counts=e['tensor_class_counts'])),flush=True)
            del ct,p,l,out,x,y;gc.collect();guard()
    after=source.mount_guard(req['capability']);require(before==after and counts=={k:LIMITS[k] for k in counts},'Incomplete read/mount accounting')
    production=dict(schema_version=cache.VERSION,binding_sha256=req['binding_sha256'],request_sha256=pin,code_pins=pins(),runtime=runtime(),source_counts=counts,cases=case_records,model_updates=0,source_arrays_read=21)
    files['production.json']=canonical(production);validation=validate_production(files,req,pin);st=store();st.store.quota_bytes=min(st.store.quota_bytes,req['cache_quota_bytes'])
    metadata=dict(artifact_type='segmenter-input-cache',schema_version='1.0.0',component=cache.VERSION,code_sha256=content_hash(req['code_pins']),parents=[loader.COMPLETION,ACCEPT_PIN],retention='derived_local_scratch_rebuild_only',sensitivity='research_derived_inputs',run_id='D-323',stage_id='qualified_cache_build',capability_sha256=CAP_PIN)
    receipt,status=st.publish(req['cache_artifact_id'],derivation_sha256=pin,files=files,metadata=metadata,validate=lambda f:validate_production(f,req,pin))
    loaded,_=st.resolve(req['cache_artifact_id'],receipt_sha256=receipt,expected_derivation=pin,validate=lambda f:validate_production(f,req,pin));consumer=cache.InputCache(loaded,req['binding'],req['binding_sha256'])
    for e in req['binding']['entries']:
        d=e['descriptor'];v=consumer.get(d['study_id'],role=d['protected_role'],operation='evaluator');require(np.bincount(v['target'].ravel(),minlength=3).tolist()==e['tensor_class_counts'] and v['transform']==e['transform'],'Postpublication reload differs')
    require(pins()==req['code_pins'] and runtime()==req['runtime'],'Final code/runtime changed');guard()
    source.put(DEST/'result.json',dict(state='cache_complete',decision='D-323',request_sha256=pin,binding_sha256=req['binding_sha256'],cache_artifact_id=req['cache_artifact_id'],cache_completion_sha256=receipt,cache_status=status,artifact_members=len(files),artifact_bytes=sum(map(len,files.values())),validation=validation,counts=counts,mount_before=before,mount_after=after,cases=case_records,source_arrays_read=21,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),independent_keeper=False))
    signal.alarm(0)


def run(pin):
    req=checked_request(pin);source.put(DEST/'consumed.json',dict(state='consumed_no_retry',decision='D-323',request_sha256=pin))
    try:
        report=prior.supervise([sys.executable,'-m','scripts.diagnostics.segmenter_cache_qualification','--worker','--request-sha256',pin],1800,8*1024**3,DEST/'worker.log');checked_request(pin);source.put(DEST/'supervision.json',report)
        print(json.dumps(dict(receipt_sha256=prior.package(DEST),result=json.loads((DEST/'result.json').read_bytes()))))
    except BaseException as e:source.put(DEST/'failure.json',dict(state='incomplete_consumed',error=str(e),read_upper_bounds=LIMITS));raise


def replay(pin,receipt):
    req=checked_request(pin);oldresult=source.verify_package(DEST,receipt);REPLAY.mkdir();start=time.monotonic();signal.alarm(1800)
    session=loader.resolve_registered();require(session.records==req['binding']['records'],'Fresh replay cohort differs');st=store()
    files,r=st.resolve(req['cache_artifact_id'],receipt_sha256=oldresult['cache_completion_sha256'],expected_derivation=pin,validate=lambda f:validate_production(f,req,pin));c=cache.InputCache(files,req['binding'],req['binding_sha256'])
    rows=[]
    for e in req['binding']['entries']:
        d=e['descriptor'];item=c.get(d['study_id'],role=d['protected_role'],operation='evaluator');im=c.get(d['study_id'],role=d['protected_role'],operation='inference');require('target' not in im and np.array_equal(im['image'],item['image']),'Image-only replay differs')
        rows.append(dict(study_id=d['study_id'],role=d['protected_role'],target_counts=np.bincount(item['target'].ravel(),minlength=3).tolist(),transform_sha256=item['transform_sha256']));tick(REPLAY,start)
    for args in [(e['descriptor']['study_id'],e['descriptor']['protected_role'],'optimizer') for e in req['binding']['entries']]+[('pants:study:PanTS_00005641','validation','inference')]:
        try:c.get(args[0],role=args[1],operation=args[2]);raise AssertionError('Closed consumer accepted')
        except ValueError:pass
    source.put(REPLAY/'result.json',dict(state='passed',decision='D-323',request_sha256=pin,cache_completion_sha256=oldresult['cache_completion_sha256'],cases=rows,members=len(r['members']),source_arrays_read=0,model_updates=0,seconds=time.monotonic()-start,peak_rss_bytes=prior.rss(),code_pins=pins(),runtime=runtime()));signal.alarm(0)


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for name in ('profile','profile-worker','prepare','run','worker','replay-worker'):g.add_argument('--'+name,action='store_true')
    p.add_argument('--profile-sha256');p.add_argument('--request-sha256');p.add_argument('--receipt-sha256');a=p.parse_args()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Cache deadline')))
    if a.profile:profile()
    elif a.profile_worker:profile_worker()
    elif a.prepare:prepare(a.profile_sha256)
    elif a.run:run(a.request_sha256)
    elif a.worker:
        require(json.loads((DEST/'consumed.json').read_bytes())['request_sha256']==a.request_sha256,'Worker requires exact consumed launch');source.put(DEST/'worker-consumed.json',dict(request_sha256=a.request_sha256));worker(a.request_sha256)
    else:replay(a.request_sha256,a.receipt_sha256)

if __name__=='__main__':main()
