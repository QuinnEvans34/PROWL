"""D-291 pinned 148-case header-only preflight; no arrays or qualification."""
import argparse
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import time
import zlib
from uuid import uuid4
import numpy as np
from nibabel.spatialimages import HeaderDataError
import yaml
from scripts.diagnostics.localizer_candidate_headers import header_only
from scripts.diagnostics.localizer_smoke_run import capture,put,encoded,sha
from scripts.diagnostics.storage_setup import disk_info

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'outputs/prowl'
JOB=REPO/'docs/capstone/data/LOCALIZER-EXPANSION-V2-HEADER-JOB-2026-09-29.json'
JOB_PIN='2e30e9e10e0b6b9a12ada52e1fab56f693eaf944ddbc76c840caab433a516511'
PLAN=JOB.with_suffix('.md')
SELECTION=ROOT/'localizer-candidates-v2-0d91addc-1ef8-402b-b12a-611aa78f12f9'
SELECTION_PIN='aa9a77cbcb3848b194a2e1bcb5515174dbf4aa4efa22c18e0d0d7746ec7ab3a7'


def validate_job(job,selection):
    expected=[c for group in selection['candidates'].values() for c in group if c['selection_reason']!='retained']
    if job['cases']!=expected or len(expected)!=148 or job['file_count']!=296 or job['case_count']!=148:
        raise ValueError('Job differs from selected new candidates')
    ids=set();paths=set();roles={'train':0,'validation':0}
    for c in expected:
        if c['study_id'] in ids or c['protected_role'] not in roles:raise ValueError('Duplicate or wrong-role candidate')
        ids.add(c['study_id']);roles[c['protected_role']]+=1
        if [r['kind'] for r in c['inventory_inputs']]!=['ct','pancreas']:raise ValueError('Wrong pair inventory')
        for ref in c['inventory_inputs']:
            path=Path(ref['uri'])
            if path.is_absolute() or '..' in path.parts or str(path)!=ref['uri'] or ref['uri'] in paths:
                raise ValueError('Unsafe or duplicate path')
            paths.add(ref['uri'])
            if ref['study_id']!=c['study_id'] or ref['protected_role']!=c['protected_role'] or ref['state']!='present':
                raise ValueError('Wrong inventory identity/role')
    if roles!={'train':112,'validation':36}:raise ValueError('Role counts differ')
    return expected


def controls():
    raw=JOB.read_bytes()
    if sha(raw)!=JOB_PIN:raise ValueError('Job changed')
    job=json.loads(raw)
    receipt=(SELECTION/'receipt.json').read_bytes()
    if sha(receipt)!=SELECTION_PIN or job['candidate_receipt_sha256']!=SELECTION_PIN:raise ValueError('Selection receipt changed')
    selected=(SELECTION/'selection.json').read_bytes()
    if sha(selected)!=job['selection_sha256'] or sha(selected)!=json.loads(receipt)['files']['selection.json']:raise ValueError('Selection changed')
    validate_job(job,json.loads(selected))
    return job


class CountingReader:
    def __init__(self,stream,budget,limit):self.stream=stream;self.budget=budget;self.limit=limit;self.used=0
    def read(self,n=-1):
        if n<0 or self.used+n>65536 or self.budget[0]+n>self.limit:raise RuntimeError('Header read cap')
        raw=self.stream.read(n);self.used+=len(raw);self.budget[0]+=len(raw);return raw


def verify_stat(observed,ref):
    expected=ref['observation']
    if not stat.S_ISREG(observed.st_mode) or observed.st_size!=ref['bytes'] or (
        observed.st_dev,observed.st_ino,observed.st_mtime_ns,observed.st_ctime_ns)!=(
        expected['device'],expected['inode'],expected['mtime_ns'],expected['ctime_ns']):
        raise ValueError('Inventory identity changed')


def read_one(root,ref,budget,limit):
    rel=Path(ref['uri']);path=root/rel
    if rel.is_absolute() or '..' in rel.parts or path.resolve(strict=True)!=path or not path.is_relative_to(root):
        raise ValueError('Unsafe source path')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        verify_stat(os.fstat(stream.fileno()),ref);reader=CountingReader(stream,budget,limit)
        try:
            h=header_only(reader)
            shape=h['shape'];dtype=np.dtype(h['dtype'])
            if len(shape)!=3 or any(type(n)!=int or n<=0 for n in shape) or dtype.kind not in 'iuf':
                raise ValueError('Unsupported grid/datatype')
            if not all(math.isfinite(v) and v>0 for v in h['spacing']):raise ValueError('Invalid spacing')
            h['expanded_array_bytes_estimate']=math.prod(shape)*dtype.itemsize
            result=dict(state='header_observed',**h)
        except (ValueError,EOFError,zlib.error,HeaderDataError) as exc:
            if str(exc)=='Compressed header-read cap':raise RuntimeError('Header per-file read cap') from exc
            result=dict(state='header_unresolved',error=str(exc))
        finally:
            verify_stat(os.fstat(stream.fileno()),ref)
    return dict(kind=ref['kind'],uri=ref['uri'],compressed_bytes_read=reader.used,**{k:v for k,v in result.items() if k!='compressed_bytes_read'})


def prepare():
    controls();source,env=capture();dest=ROOT/('candidate-headers-v2-request-'+str(uuid4()));dest.mkdir()
    files={'source.json':source,'environment.json':env,'job.json':JOB.read_bytes(),'design.md':PLAN.read_bytes()}
    for n,b in files.items():put(dest/n,b)
    put(dest/'request.json',encoded(dict(decision='D-291',files={n:sha(b) for n,b in files.items()},source_arrays_read=0,qualification_granted=False)))
    print(dest);print('request_sha256='+sha((dest/'request.json').read_bytes()))


def checked(request,pin):
    if request.parent!=ROOT or request.resolve(strict=True)!=request:raise ValueError('Unsafe request')
    raw=(request/'request.json').read_bytes()
    if sha(raw)!=pin:raise ValueError('Request changed')
    req=json.loads(raw)
    if req['decision']!='D-291' or req['source_arrays_read']!=0 or req['qualification_granted'] is not False or set(req['files'])!={'source.json','environment.json','job.json','design.md'}:raise ValueError('Wrong request scope')
    for n,h in req['files'].items():
        if sha((request/n).read_bytes())!=h:raise ValueError('Frozen control changed')
    if (request/'job.json').read_bytes()!=JOB.read_bytes() or (request/'design.md').read_bytes()!=PLAN.read_bytes():raise ValueError('Plan changed')
    if capture()!=((request/'source.json').read_bytes(),(request/'environment.json').read_bytes()):raise ValueError('Code/environment changed')
    return controls()


def run(request,pin):
    job=checked(request,pin);dest=ROOT/('candidate-headers-v2-'+str(uuid4()));dest.mkdir()
    put(ROOT/('candidate-headers-v2-claim-'+pin+'.json'),encoded(dict(result=dest.name)))
    put(dest/'invocation.json',encoded(dict(request=str(request),request_sha256=pin)))
    print(dest,flush=True);start=time.monotonic();rows=[];budget=[0];limits=job['limits']
    def timeout(*_):raise TimeoutError('Header wall-time cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(limits['seconds'])
    try:
        registry_raw=(REPO/'configs/local/roots.yaml').read_bytes()
        if sha(registry_raw)!=job['registry_sha256']:raise ValueError('Registry changed')
        registry=yaml.safe_load(registry_raw);domain=registry['failure_domains']['external_primary'];mount=Path(domain['mount_path'])
        root=Path(registry['roots']['pants_source']['acquisition_parent'])/'extraction-3b1cd6110811-20260922'
        def guard():
            if not mount.is_mount() or mount.is_symlink() or root.resolve(strict=True)!=root:raise ValueError('Unsafe source root')
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>limits['rss_bytes'] or shutil.disk_usage(REPO).free<limits['internal_free_floor']:raise RuntimeError('Memory/free-space cap')
            if time.monotonic()-start>limits['seconds'] or sum(p.stat().st_size for p in dest.iterdir())>limits['output_bytes']:raise RuntimeError('Time/output cap')
        guard();info=disk_info(mount)
        if info.get('VolumeUUID')!=domain['volume_uuid'] or info.get('MountPoint')!=str(mount):raise ValueError('Wrong mounted volume')
        for c in job['cases']:
            pair=[]
            for ref in c['inventory_inputs']:
                guard();pair.append(read_one(root,ref,budget,limits['compressed_bytes_total']))
            concerns=[]
            if any(h['state']!='header_observed' for h in pair):concerns.append('unresolved_header')
            else:
                a,b=pair
                if a['shape']!=b['shape'] or not np.allclose(a['affine'],b['affine'],rtol=0,atol=1e-5):concerns.append('header_geometry_mismatch')
                if any(h['units'][0]!='mm' for h in pair):concerns.append('physical_units_need_evidence')
            row=dict(study_id=c['study_id'],protected_role=c['protected_role'],descriptive_stratum=c['descriptive_stratum'],headers=pair,concerns=concerns,status='header_only_not_qualified')
            rows.append(row);put(dest/(c['study_id'].split(':')[-1]+'.json'),encoded(row))
        guard();info=disk_info(mount)
        if info.get('VolumeUUID')!=domain['volume_uuid'] or info.get('MountPoint')!=str(mount):raise ValueError('Mount changed')
        checked(request,pin)
        put(dest/'result.json',encoded(dict(state='header_preflight_complete_not_qualification',cases=rows,source_arrays_read=0,compressed_bytes_read=budget[0],elapsed_seconds=time.monotonic()-start,peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
        guard();put(dest/'receipt.json',encoded(dict(state='complete',files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in dest.iterdir()})))
        print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()))
    except BaseException as exc:
        put(dest/'failure.json',encoded(dict(state='incomplete',error=str(exc),completed_cases=len(rows),compressed_bytes_read=budget[0],elapsed_seconds=time.monotonic()-start)));raise
    finally:signal.alarm(0)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--request',type=Path);p.add_argument('--pin');a=p.parse_args()
    if a.prepare:prepare()
    elif a.request and a.pin:run(a.request,a.pin)
    else:p.error('Choose prepare or pinned run')
