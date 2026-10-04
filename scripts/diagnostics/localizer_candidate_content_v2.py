"""D-292 versioned batch content evidence; batch-01 pilot only, no qualification."""
import argparse
import gc
import io
import json
import os
from pathlib import Path
import shutil
import signal
import time
from uuid import uuid4
import nibabel as nib
import numpy as np
import yaml
from scripts.diagnostics.localizer_smoke_run import put,encoded,sha,capture
from scripts.diagnostics.localizer_candidate_headers_v2 import REPO,SELECTION,SELECTION_PIN as PIN,controls as candidate_controls
from scripts.diagnostics.localizer_content_verify import peak_rss
from scripts.diagnostics.localizer_alignment_review import render
from scripts.diagnostics.storage_setup import disk_info
from src.data.bounded_nifti_audit import read_file
from src.data.binary_label_policy import decode_binary,APPROVED_POLICY

PLAN=REPO/'docs/capstone/data/LOCALIZER-EXPANSION-V2-CONTENT-PILOT-2026-09-29.md'
BATCH_PLAN=REPO/'docs/capstone/data/LOCALIZER-EXPANSION-V2-CONTENT-BATCHES-2026-09-29.json'
BATCH_PIN='52eee153491981d57a3820536c7ea5c90c1f1fa8fdf6bda50ff12d1e7b837483'
HEADERS=REPO/'outputs/prowl/candidate-headers-v2-551775cb-f388-44e0-9453-b49b181c9621'
HEADER_PIN='8c9538785427e54ffce6334425ee0a8cccf9a720aa933c69ab8a25b27446f828'
LIMITS=dict(compressed_bytes=1024**3,expanded_bytes=4*1024**3,per_file_compressed=128*1024**2,
            per_file_expanded=512*1024**2,voxel_count=64_000_000,rss=16*1024**3,
            seconds=1200,output_bytes=256*1024**2)


def validate_batch(batch,candidates,headers):
    if batch['batch_id']!='batch-01' or batch['category']!='standard' or batch['role']!='train' or len(batch['cases'])!=16:
        raise ValueError('Only first standard pilot is active')
    expected=dict(LIMITS);expected['rss_bytes']=expected.pop('rss')
    if batch['limits']!=expected:raise ValueError('Batch limits differ')
    by_case={c['study_id']:c for c in candidates};by_header={r['study_id']:r for r in headers}
    seen=set()
    for row in batch['cases']:
        c=row['candidate'];sid=c['study_id']
        if sid in seen or c!=by_case.get(sid) or c['protected_role']!=batch['role'] or row['header_evidence']!=by_header.get(sid):
            raise ValueError('Substituted candidate/header/role or duplicate')
        seen.add(sid)
        if c['selection_reason']=='retained':raise ValueError('Retained candidate outside new batch')
        if any(h['state']!='header_observed' or h['voxel_count']>LIMITS['voxel_count'] for h in row['header_evidence']['headers']):
            raise ValueError('Unsupported header/array allocation')
    return batch


def checked_selection():
    job=candidate_controls()
    raw=BATCH_PLAN.read_bytes()
    if sha(raw)!=BATCH_PIN:raise ValueError('Batch plan changed')
    plan=json.loads(raw)
    receipt=(HEADERS/'receipt.json').read_bytes()
    if sha(receipt)!=HEADER_PIN or plan['header_receipt_sha256']!=HEADER_PIN:raise ValueError('Header receipt changed')
    for name,ref in json.loads(receipt)['files'].items():
        if Path(name).name!=name:raise ValueError('Unsafe evidence member')
        b=(HEADERS/name).read_bytes()
        if {'bytes':len(b),'sha256':sha(b)}!=ref:raise ValueError('Header evidence changed')
    headers=json.loads((HEADERS/'result.json').read_bytes())['cases']
    batch=validate_batch(plan['batches'][0],job['cases'],headers)
    return dict(batch_id=batch['batch_id'],batch_plan_sha256=BATCH_PIN,header_receipt_sha256=HEADER_PIN,
        candidates={'train':[dict(r['candidate'],header_evidence=r['header_evidence']) for r in batch['cases']]})


def validate_decoded_header(image,header):
    if list(image.shape)!=header['shape'] or str(image.get_data_dtype())!=header['dtype'] or list(image.header.get_xyzt_units())!=header['units'] or not np.allclose(image.affine,header['affine'],rtol=0,atol=1e-5):
        raise ValueError('Decoded geometry/type/units differ from pinned header')


def prepare():
    selection=checked_selection();p=REPO/'outputs/prowl'/('localizer-content-v2-request-'+str(uuid4()));p.mkdir()
    source,env=capture()
    for name,b in [('source.json',source),('environment.json',env),('plan.md',PLAN.read_bytes()),('selection.json',encoded(selection))]:put(p/name,b)
    request=dict(decision='D-292',batch_id='batch-01',candidate_receipt_sha256=PIN,limits=LIMITS,files={x.name:sha(x.read_bytes()) for x in p.iterdir()},optimizer_updates_allowed=False,qualification_granted=False)
    put(p/'request.json',encoded(request));print(p);print('request_sha256='+sha((p/'request.json').read_bytes()))


def run(request,pin):
    if request.parent!=REPO/'outputs/prowl' or request.resolve(strict=True)!=request:raise ValueError('Unsafe request')
    raw=(request/'request.json').read_bytes()
    if sha(raw)!=pin:raise ValueError('Request pin changed')
    req=json.loads(raw)
    if req.get('decision')!='D-292' or req.get('batch_id')!='batch-01' or req.get('optimizer_updates_allowed') is not False or req.get('qualification_granted') is not False or req['limits']!=LIMITS or req['candidate_receipt_sha256']!=PIN:raise ValueError('Request scope changed')
    if set(req['files'])!={'source.json','environment.json','plan.md','selection.json'}:raise ValueError('Wrong request file inventory')
    if PLAN.read_bytes()!=(request/'plan.md').read_bytes():raise ValueError('Pilot plan changed')
    for name,h in req['files'].items():
        if Path(name).name!=name or sha((request/name).read_bytes())!=h:raise ValueError('Request member changed')
    source,env=capture()
    if source!=(request/'source.json').read_bytes() or env!=(request/'environment.json').read_bytes():raise ValueError('Source/environment changed')
    selection=checked_selection()
    if encoded(selection)!=(request/'selection.json').read_bytes():raise ValueError('Selection differs')
    dest=REPO/'outputs/prowl'/('localizer-content-v2-'+str(uuid4()));dest.mkdir()
    put(REPO/'outputs/prowl'/('content-v2-claim-'+pin+'.json'),encoded(dict(request_sha256=pin,result_directory=dest.name)))
    start=time.monotonic();counts=dict(compressed=0,expanded=0);results=[]
    def timeout(*_):raise TimeoutError('Overall content deadline')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(LIMITS['seconds'])
    try:
        regraw=(REPO/'configs/local/roots.yaml').read_bytes()
        if sha(regraw)!='46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788':raise ValueError('Registry changed')
        reg=yaml.safe_load(regraw);domain=reg['failure_domains']['external_primary'];mount=Path(domain['mount_path'])
        root=Path(reg['roots']['pants_source']['acquisition_parent'])/'extraction-3b1cd6110811-20260922'
        info=disk_info(mount)
        if not mount.is_mount() or mount.resolve()!=mount or info.get('VolumeUUID')!=domain['volume_uuid'] or not root.is_relative_to(mount):raise ValueError('Wrong source mount')
        device=mount.stat().st_dev
        def tick():
            if time.monotonic()-start>LIMITS['seconds'] or peak_rss()>LIMITS['rss']:raise RuntimeError('Time/memory cap')
            if not mount.is_mount() or mount.stat().st_dev!=device or shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Mount/free-space changed')
            if sum(x.stat().st_size for x in dest.iterdir())>LIMITS['output_bytes']:raise RuntimeError('Output cap')
        for name in ('source.json','environment.json','plan.md','selection.json','request.json'):put(dest/name,(request/name).read_bytes())
        print(dest,flush=True)
        for role,group in selection['candidates'].items():
            for candidate in group:
                tick();images={};files=[];sid=candidate['study_id'];code=sid.split(':')[-1]
                for row in candidate['inventory_inputs']:
                    if row['study_id']!=sid or row['protected_role']!=role:raise ValueError('Candidate row binding')
                    if counts['compressed']+row['bytes']>LIMITS['compressed_bytes']:raise ValueError('Cumulative compressed cap')
                    im,receipt=read_file(root,row,compressed_cap=LIMITS['per_file_compressed'],expanded_cap=min(LIMITS['per_file_expanded'],LIMITS['expanded_bytes']-counts['expanded']),voxel_cap=LIMITS['voxel_count'],tick=tick)
                    validate_decoded_header(im,next(h for h in candidate['header_evidence']['headers'] if h['kind']==row['kind']))
                    counts['compressed']+=receipt['compressed_bytes'];counts['expanded']+=receipt['expanded_bytes'];images[row['kind']]=im
                    files.append(dict(kind=row['kind'],source=row,**receipt,dtype=str(im.get_data_dtype()),shape=list(im.shape),affine=im.affine.tolist(),units=list(im.header.get_xyzt_units()),effective_scaling=dict(slope=float(im.dataobj.slope),intercept=float(im.dataobj.inter))))
                ctimg,maskimg=images['ct'],images['pancreas'];holds=[]
                geometry=ctimg.shape==maskimg.shape and np.allclose(ctimg.affine,maskimg.affine,rtol=0,atol=1e-5)
                if not geometry:holds.append('geometry_mismatch')
                if ctimg.header.get_xyzt_units()[0]!='mm':holds.append('physical_units_unresolved')
                ct=nib.as_closest_canonical(ctimg).get_fdata(dtype=np.float32);mimg=nib.as_closest_canonical(maskimg);semantic=mimg.get_fdata(dtype=np.float64)
                finite=bool(np.isfinite(ct).all());report=dict(study_id=sid,protected_role=role,files=files,geometry_matches=geometry,ct_finite=finite,ct_range=[float(ct.min()),float(ct.max())] if finite else None,holds=holds,eligibility='not_assessed')
                if not finite:holds.append('nonfinite_ct')
                unique,count=np.unique(semantic,return_counts=True)
                report['semantic_values']=[dict(value=float(v),count=int(n)) for v,n in zip(unique,count)] if len(unique)<=16 and np.isfinite(unique).all() else None
                try:mask,decode=decode_binary(semantic,policy=APPROVED_POLICY)
                except ValueError as e:holds.append('binary_encoding_unresolved');report['decode_error']=str(e);mask=None
                if mask is not None:
                    report['decode']=decode
                    if not mask.any():holds.append('empty_pancreas_reference')
                    elif geometry and finite:
                        coords=np.nonzero(mask);mid=[int(np.median(x)) for x in coords];z=np.unique(coords[2]);views=[(2,int(z[0])),(2,int(z[len(z)//2])),(2,int(z[-1])),(1,mid[1]),(0,mid[0])]
                        panels=[(a,i,o) for o in (False,True) for a,i in views]
                        # Physical scaling is display-only where units are unresolved; never a qualification assertion.
                        im=render(ct,mask,nib.affines.voxel_sizes(mimg.affine),panels,code+' candidate alignment');b=io.BytesIO();im.save(b,format='PNG');put(dest/(code+'.png'),b.getvalue())
                        report.update(mask_bounds=[[int(x.min()),int(x.max())] for x in coords],canonical_affine=mimg.affine.tolist(),review_planes=views)
                put(dest/(code+'.json'),encoded(report));results.append(report);print(json.dumps(dict(case=code,holds=holds)),flush=True)
                del images,ctimg,maskimg,ct,mimg,semantic,mask,unique,count;gc.collect();tick()
        ct_by_hash={};duplicates=[]
        for r in results:
            h=next(f['content_sha256'] for f in r['files'] if f['kind']=='ct');ct_by_hash.setdefault(h,[]).append(dict(study_id=r['study_id'],role=r['protected_role']))
        duplicates=[dict(sha256=h,members=v) for h,v in ct_by_hash.items() if len(v)>1]
        source2,env2=capture()
        if source2!=source or env2!=env:raise ValueError('Executing source changed')
        if disk_info(mount).get('VolumeUUID')!=domain['volume_uuid']:raise ValueError('Mount changed')
        put(dest/'result.json',encoded(dict(state='content_evidence_complete_not_qualification',case_count=len(results),file_count=sum(len(r['files']) for r in results),batch_id='batch-01',source_bytes=counts,duplicate_ct_groups=duplicates,elapsed_seconds=time.monotonic()-start,peak_rss=peak_rss(),visual_review='pending',qualification_granted=False)))
        tick();put(dest/'receipt.json',encoded(dict(state='complete',files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in dest.iterdir()})));print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()),flush=True)
    except BaseException as e:
        put(dest/'failure.json',encoded(dict(state='incomplete',error=str(e),source_bytes=counts,elapsed_seconds=time.monotonic()-start)));raise
    finally:signal.alarm(0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--request',type=Path);parser.add_argument('--pin');args=parser.parse_args()
    if args.prepare:prepare()
    elif args.request and args.pin:run(args.request,args.pin)
    else:parser.error('Choose prepare or exact pinned request')
