"""D-318 supervised one-shot eight-case content diagnostic; no scientific consumer promotion."""
import argparse
import gc
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import zlib
import importlib.metadata
import numpy as np
import nibabel as nib
from scripts.diagnostics import segmenter_source_verification as source
from src.data import segmenter_content_v1 as core
from src.data.segmenter_native_views_v2 import render_native

REPO=source.REPO
PROPOSAL='outputs/prowl/SEGMENTER-SOURCE-REVIEW-20261001/m3-content-scope-proposal.json'
PROPOSAL_PIN='33853ca3eb106f55858a63e1d24ab57aa7c746b57bcf48b61b2613167f0000cb'
M2=REPO/'outputs/prowl/SEGMENTER-SOURCE-M2-20261001'
M2_PIN='bec0f3b3f292d187b3bc741be6fa38b8aa355f199c1cf3375657364705421108'
DEST=REPO/'outputs/prowl/SEGMENTER-CONTENT-CONTINUATION-20261001'
PROFILE=REPO/'outputs/prowl/SEGMENTER-CONTENT-CONTINUATION-REHEARSAL-20261001'
CODES=['src/data/segmenter_content_v1.py','scripts/diagnostics/segmenter_content_continuation.py','src/data/segmenter_native_views_v2.py',
       'scripts/diagnostics/segmenter_source_verification.py','src/data/binary_label_policy.py']
CASES=['PanTS_00006110','PanTS_00002232','PanTS_00006238','PanTS_00005821','PanTS_00004965','PanTS_00002514','PanTS_00002727','PanTS_00007265']
CONTINUATION='outputs/prowl/SEGMENTER-CONTENT-PILOT-REVIEW-20261001/continuation-proposal.json'
CONTINUATION_PIN='7fb32a630e4152ebd9b2cee944f85ba212d95df32ffdd6b11c771b32236fb1e0'
PILOT_RECEIPT='2f972c5c8136c60630ba3559b7435b84c79af0cec7689c190ebfd6b28ce26d7f'


def rss():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)


def pins():return {n:source.sha((REPO/n).read_bytes()) for n in CODES}


def runtime():return source.runtime()|{n:importlib.metadata.version(n) for n in ['scipy','Pillow']}


def write_bytes(path,raw):
    with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())


def package(dest):
    members={p.name:dict(bytes=p.stat().st_size,sha256=source.sha(p.read_bytes())) for p in dest.iterdir()}
    source.put(dest/'receipt.json',dict(state='complete',files=members))
    return source.sha((dest/'receipt.json').read_bytes())


def build_request(profile_pin):
    full=json.loads(source.safe_local(PROPOSAL,PROPOSAL_PIN))
    p=json.loads(source.safe_local(CONTINUATION,CONTINUATION_PIN))
    prior=source.verify_package(M2,M2_PIN)
    pilot=source.verify_package(REPO/'outputs/prowl/SEGMENTER-CONTENT-PILOT-20261001',PILOT_RECEIPT)
    source.require(len(pilot['cases'])==4 and pilot['model_updates']==0,'Predecessor incomplete')
    source.require(p['predecessor_pilot_receipt_sha256']==PILOT_RECEIPT and p['m2_receipt_sha256']==M2_PIN and
                   p['source_scope_proposal_sha256']==PROPOSAL_PIN,'Continuation ancestry differs')
    expected=[r for r in full['files'] if r['study_id'].split(':')[-1] in CASES]
    source.require(p['files']==expected,'Continuation/full scope differs')
    profile=source.verify_package(PROFILE,profile_pin)
    source.require(profile['state']=='passed' and profile['code_pins']==pins() and profile['runtime']==runtime(),'Profile source/runtime not qualified')
    by_uri={r['uri']:r for r in prior['files']};files=[]
    for r in p['files']:
        prev=by_uri[r['uri']]
        source.require(prev['state']=='verified' and all(r[k]==prev[k] for k in ['study_id','protected_role','uri','observation','sha256','kind']),'Proposal/M2 differs')
        files.append(r|dict(geometry=prev['retained_ct_geometry']))
    validate_scope(files)
    capability=json.loads((M2/'request.json').read_bytes())['capability']|dict(operations=['full_compressed_hash','full_gzip_decode_native_arrays'],source_writes=False)
    return dict(component='segmenter-content-continuation-v1',decision='D-318',output=str(DEST),code_pins=pins(),runtime=runtime(),
                proposal_sha256=PROPOSAL_PIN,continuation_sha256=CONTINUATION_PIN,predecessor_pilot_receipt_sha256=PILOT_RECEIPT,m2_receipt_sha256=M2_PIN,profile_receipt_sha256=profile_pin,
                capability=capability,files=files,cases=CASES,
                limits=dict(hash_bytes=183291323,decode_bytes=183291323,expanded_bytes=635508776,
                            seconds=900,rss_bytes=8*1024**3,output_bytes=64*1024**2),
                component_limit=core.MAX_COMPONENTS,panel_limit=core.MAX_PLANES,binary_policy=core.APPROVED_POLICY,
                qualifications_granted=False,model_updates_allowed=False,candidate_substitution=False)


def validate_scope(files):
    source.require(len(files)==24 and len({r['uri'] for r in files})==24 and
                   sum(r['compressed_bytes'] for r in files)==183291323 and
                   sum(r['expanded_bytes'] for r in files)==635508776,'Continuation scope differs')
    source.require({r['study_id'].split(':')[-1] for r in files}==set(CASES),'Continuation membership differs')
    for i,sid in enumerate(CASES):
        group=[r for r in files if r['study_id']== 'pants:study:'+sid]
        role='train' if i<5 else 'validation'
        source.require(len(group)==3 and {r['kind'] for r in group}=={'ct','pancreas','lesion'} and
                       all(r['protected_role']==role for r in group),'Continuation role/three-input binding')


def checked_request(path,pin):
    source.require(path==DEST/'request.json' and DEST.resolve(strict=True)==DEST,'Wrong fixed request/output path')
    raw=path.read_bytes();source.require(source.sha(raw)==pin,'Request bytes changed');req=json.loads(raw)
    source.require(req==build_request(req['profile_receipt_sha256']),'Request source/runtime/scope changed')
    return req


def check_output(dest,limit,additional=0):
    if sum(p.stat().st_size for p in dest.iterdir())+additional>limit:raise core.BudgetError('Output ceiling')


def worker(path,pin):
    req=checked_request(path,pin);start=time.monotonic();counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);results=[]
    claimed=json.loads((DEST/'consumed.json').read_bytes());source.require(claimed['request_sha256']==pin,'No exact parent claim')
    source.put(DEST/'worker-started.json',dict(request_sha256=pin,state='started'))
    def tick():
        if time.monotonic()-start>req['limits']['seconds'] or rss()>req['limits']['rss_bytes']:raise core.BudgetError('Time/RSS ceiling')
        check_output(DEST,req['limits']['output_bytes'])
    def interrupted(signum,frame):raise InterruptedError('Worker interrupted')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    signal.signal(signal.SIGALRM,interrupted);signal.alarm(req['limits']['seconds'])
    try:
        before=source.mount_guard(req['capability'])
        with source.directory(req['capability']['source_root']) as rootfd:
            source.require(os.fstat(rootfd).st_dev==before['root_device'] and os.fstat(rootfd).st_ino==before['root_inode'],'Source root replaced')
            for sid in req['cases']:
                tick();rows=[r for r in req['files'] if r['study_id'].split(':')[-1]==sid];arrays={};headers={};file_reports=[]
                record=dict(study_id=rows[0]['study_id'],protected_role=rows[0]['protected_role'],holds=[],files=file_reports,eligibility='not_assessed')
                try:
                    for row in rows:
                        tick();base=sid+'-'+row['kind']
                        source.put(DEST/(base+'-read-started.json'),dict(uri=row['uri'],reserved_hash_bytes=row['compressed_bytes'],reserved_decode_bytes=row['compressed_bytes'],reserved_expanded_bytes=row['expanded_bytes']))
                        with source.source_stream(rootfd,row) as stream:core.hash_exact(stream,row,counts,req['limits'],tick)
                        with source.source_stream(rootfd,row) as stream:arrays[row['kind']],headers[row['kind']],read=core.decode_exact(stream,row,counts,req['limits'],tick)
                        file_reports.append(dict(uri=row['uri'],kind=row['kind'],header=headers[row['kind']],**read))
                        source.put(DEST/(base+'-read-complete.json'),dict(**read,cumulative_counts=dict(counts)))
                    ct,pancreas,lesion,metrics=core.analyze(arrays,headers,tick);record.update(metrics);record['holds']+=metrics['technical_holds']
                    png,views=render_native(ct,pancreas,lesion,headers['ct']['affine'],sid+' '+record['protected_role'],metrics['components'],tick)
                    check_output(DEST,req['limits']['output_bytes'],len(png));write_bytes(DEST/(sid+'.png'),png);record['views']=views
                    record['visual_review']='pending';del ct,pancreas,lesion
                except (ValueError,OSError,zlib.error) as e:
                    record['holds'].append('content_or_alignment_rejected');record['error']=str(e)
                results.append(record);source.put(DEST/(sid+'.json'),record)
                del arrays,headers;gc.collect();tick();print(json.dumps(dict(case=sid,holds=record['holds'],lesion_voxels=record.get('lesion_voxels'))),flush=True)
        after=source.mount_guard(req['capability']);source.require(before==after,'Source mount/root changed');tick()
        result=dict(state='content_evidence_complete_not_qualification',request_sha256=pin,cases=results,counts=counts,
                    requested_cases=8,requested_files=24,mount_before=before,mount_after=after,seconds=time.monotonic()-start,
                    peak_rss_bytes=rss(),real_qualifications=0,model_updates=0,visual_review='pending')
        source.put(DEST/'result.json',result)
    except BaseException as e:
        source.put(DEST/'worker-failure.json',dict(state='incomplete_consumed',error=str(e),counts=counts,completed_cases=results,seconds=time.monotonic()-start,peak_rss_bytes=rss()))
        raise
    finally:signal.alarm(0)


def supervise(command,seconds,memory,log_path):
    """Monitor even while native C extensions allocate or compute."""
    started=time.monotonic();proc=subprocess.Popen(command,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output=b'';peak=0
    try:
        while True:
            if time.monotonic()-started>seconds:raise core.BudgetError('Supervisor timeout')
            try:output,_=proc.communicate(timeout=.5);break
            except subprocess.TimeoutExpired:
                observed=subprocess.run(['/bin/ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True,timeout=2)
                if proc.poll() is None:
                    if observed.returncode or not observed.stdout.strip():raise RuntimeError('Cannot monitor worker RSS')
                    peak=max(peak,int(observed.stdout.strip())*1024)
                    if peak>memory:raise core.BudgetError('Supervisor memory ceiling')
        if proc.returncode:raise RuntimeError('Worker failed with exit '+str(proc.returncode))
        return dict(seconds=time.monotonic()-started,observed_peak_rss_bytes=peak)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:output,_=proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();output,_=proc.communicate()
        write_bytes(log_path,output)


def run(path,pin):
    req=checked_request(path,pin);source.put(DEST/'consumed.json',dict(request_sha256=pin,state='consumed_no_retry'))
    try:
        monitoring=supervise([sys.executable,'-m','scripts.diagnostics.segmenter_content_continuation','--worker','--request',str(path),'--sha256',pin],req['limits']['seconds'],req['limits']['rss_bytes'],DEST/'worker.log')
        result=json.loads((DEST/'result.json').read_bytes());source.require(result['request_sha256']==pin and len(result['cases'])==8,'Incomplete worker ledger')
        source.require(req==checked_request(path,pin),'Code/runtime changed')
        source.put(DEST/'supervision.json',monitoring);check_output(DEST,req['limits']['output_bytes'],4096)
        receipt_pin=package(DEST);print('receipt_sha256='+receipt_pin);print(json.dumps({k:result[k] for k in ['counts','seconds','peak_rss_bytes']}))
    except BaseException as e:
        source.put(DEST/'failure.json',dict(state='incomplete_consumed',error=str(e),partial_counts='See worker-failure or per-file reservations/completions; killed reads may have only upper bounds'))
        raise


def invented_file(kind,pattern,shape):
    dtype=np.int16 if kind=='ct' else np.int8
    data=np.zeros(shape,dtype=dtype,order='F')
    scaled=kind=='lesion';data[:]= -128 if scaled else 0
    if kind=='pancreas':data[shape[0]//4:3*shape[0]//4,shape[1]//4:3*shape[1]//4,shape[2]//4:3*shape[2]//4]=1
    if kind=='lesion':
        if pattern=='dense':data[:]=127
        if pattern=='fragmented':data[::64,::64,::32]=127
        if pattern=='boundary':data[:,0,:]=127
    h=nib.Nifti1Header();h.set_data_shape(shape);h.set_data_dtype(dtype);h.set_sform(np.diag([1.,1.,2.,1.]),code=1);h.set_zooms((1.,1.,2.));h['vox_offset']=352;h.set_xyzt_units('mm')
    h['scl_slope']=np.float32(1/255) if scaled else 1.;h['scl_inter']=np.float32(128/255) if scaled else 0.
    compressor=zlib.compressobj(level=1,wbits=16+zlib.MAX_WBITS);parts=[compressor.compress(h.binaryblock+b'\x00'*4)]
    flat=data.ravel(order='F')
    for i in range(0,flat.size,core.CHUNK):parts.append(compressor.compress(flat[i:i+core.CHUNK].tobytes()))
    parts.append(compressor.flush());blob=b''.join(parts)
    slope,inter=h.get_slope_inter();header=dict(decompressed_header_sha256=source.sha(h.binaryblock),effective_slope=slope,effective_intercept=inter,units=['mm','unknown'])
    row=dict(kind=kind,dtype=np.dtype(dtype).str,expanded_bytes=352+data.nbytes,compressed_bytes=len(blob),sha256=source.sha(blob),
             geometry=dict(shape_xyz=list(shape),affine_ras=h.get_best_affine().ravel().tolist(),spacing_mm_xyz=[1.,1.,2.]))
    if kind=='lesion':row['header']=header
    else:row['retained_content']=dict(effective_scaling=dict(slope=slope,intercept=inter),units=['mm','unknown'])
    return blob,row


def profile_worker():
    start=time.monotonic();shape=(512,434,208);source.put(PROFILE/'worker-started.json',dict(state='started',shape=list(shape)));results=[]
    initial_pins=pins();env=runtime()
    def tick():
        if rss()>8*1024**3 or time.monotonic()-start>900:raise core.BudgetError('Synthetic time/RSS ceiling')
    try:
        for pattern in ['dense','empty','fragmented','boundary']:
            arrays={};headers={};counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);limits=dict(hash_bytes=512*1024**2,decode_bytes=512*1024**2,expanded_bytes=184878112)
            for kind in ['ct','pancreas','lesion']:
                tick();blob,row=invented_file(kind,pattern,shape)
                core.hash_exact(io.BytesIO(blob),row,counts,limits,tick)
                arrays[kind],headers[kind],_=core.decode_exact(io.BytesIO(blob),row,counts,limits,tick);del blob;gc.collect()
            ct,pancreas,lesion,metrics=core.analyze(arrays,headers,tick)
            expected={'dense':math_prod(shape),'empty':0,'fragmented':8*7*7,'boundary':512*208}[pattern]
            source.require(metrics['lesion_voxels']==expected,'Synthetic foreground oracle')
            if pattern=='fragmented':source.require(metrics['component_count']==392,'Fragmentation oracle')
            png,views=render_native(ct,pancreas,lesion,headers['ct']['affine'],'Synthetic '+pattern,metrics['components'],tick)
            write_bytes(PROFILE/(pattern+'.png'),png);source.put(PROFILE/(pattern+'.json'),dict(metrics=metrics,views=views,counts=counts))
            results.append(dict(pattern=pattern,lesion_voxels=metrics['lesion_voxels'],components=metrics['component_count'],counts=counts))
            del arrays,headers,ct,pancreas,lesion,png,metrics;gc.collect();tick()
        source.require(pins()==initial_pins and runtime()==env,'Synthetic source/runtime changed')
        source.put(PROFILE/'result.json',dict(state='passed',shape=list(shape),results=results,code_pins=initial_pins,runtime=env,
                   seconds=time.monotonic()-start,peak_rss_bytes=rss(),source_arrays_read=0,model_updates=0))
    except BaseException as e:
        source.put(PROFILE/'worker-failure.json',dict(error=str(e),state='incomplete',results=results));raise


def math_prod(shape):return int(np.prod(shape))


def profile():
    PROFILE.mkdir();source.put(PROFILE/'started.json',dict(state='started',decision='D-318',code_pins=pins(),runtime=runtime()))
    try:
        result=supervise([sys.executable,'-m','scripts.diagnostics.segmenter_content_continuation','--profile-worker'],900,8*1024**3,PROFILE/'worker.log')
        source.put(PROFILE/'supervision.json',result);check_output(PROFILE,64*1024**2,4096);pin=package(PROFILE)
        print('profile_receipt_sha256='+pin);print((PROFILE/'result.json').read_text())
    except BaseException as e:source.put(PROFILE/'failure.json',dict(state='incomplete',error=str(e)));raise


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--profile',action='store_true')
    ap.add_argument('--profile-worker',action='store_true');ap.add_argument('--worker',action='store_true')
    ap.add_argument('--profile-sha256');ap.add_argument('--request',type=Path);ap.add_argument('--sha256');args=ap.parse_args()
    if args.profile:profile()
    elif args.profile_worker:profile_worker()
    elif args.prepare:
        req=build_request(args.profile_sha256);DEST.mkdir();source.put(DEST/'request.json',req);print('request_sha256='+source.sha((DEST/'request.json').read_bytes()))
    elif args.worker:worker(args.request.absolute(),args.sha256)
    else:run(args.request.absolute(),args.sha256)

if __name__=='__main__':main()
