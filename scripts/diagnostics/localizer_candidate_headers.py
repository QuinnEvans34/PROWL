"""D-280 bounded header-only candidate preflight; no qualification or array reads."""
import zlib
import io
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import time
from uuid import uuid4
import nibabel as nib
import numpy as np
import yaml
from scripts.diagnostics.localizer_smoke_run import put,encoded,sha,capture
from scripts.diagnostics.storage_setup import disk_info

REPO=Path(__file__).resolve().parents[2]
SELECTION=REPO/'outputs/prowl/localizer-candidates-f1f88917-7aa0-4cd5-a4e7-e8a84897421c'
PIN='3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1'


class LimitedReader:
    def __init__(self,stream):self.stream=stream;self.used=0
    def read(self,n=-1):
        if n<0 or self.used+n>65536:raise ValueError('Compressed header-read cap')
        data=self.stream.read(n);self.used+=len(data);return data


def header_only(stream):
    limited=LimitedReader(stream)
    decoder=zlib.decompressobj(16+zlib.MAX_WBITS);raw=b''
    while len(raw)<348:
        chunk=limited.read(4096)
        if not chunk:break
        raw+=decoder.decompress(chunk,348-len(raw))
    if len(raw)!=348:raise ValueError('Truncated NIfTI header')
    h=nib.Nifti1Header.from_fileobj(io.BytesIO(raw),check=True)
    shape=tuple(int(x) for x in h.get_data_shape());affine=h.get_best_affine()
    if len(shape)!=3 or not all(shape) or not np.isfinite(affine).all():raise ValueError('Unsupported header grid')
    slope,inter=h.get_slope_inter()
    return dict(shape=list(shape),spacing=list(map(float,h.get_zooms())),units=list(h.get_xyzt_units()),
        affine=affine.tolist(),dtype=str(h.get_data_dtype()),qform_code=int(h['qform_code']),
        sform_code=int(h['sform_code']),slope=slope,intercept=inter,compressed_bytes_read=limited.used,
        decompressed_header_sha256=sha(raw),voxel_count=int(np.prod(shape,dtype=np.int64)))


def run():
    start=time.monotonic();dest=REPO/'outputs/prowl'/('localizer-candidate-headers-'+str(uuid4()));dest.mkdir()
    def timeout(*_):raise TimeoutError('Header preflight time cap')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(300)
    try:
        raw=(SELECTION/'receipt.json').read_bytes()
        if sha(raw)!=PIN:raise ValueError('Candidate receipt changed')
        for n,r in json.loads(raw)['files'].items():
            if Path(n).name!=n:raise ValueError('Unsafe package member')
            b=(SELECTION/n).read_bytes()
            if {'bytes':len(b),'sha256':sha(b)}!=r:raise ValueError('Candidate bytes changed')
        selection=json.loads((SELECTION/'selection.json').read_bytes())
        registry_raw=(REPO/'configs/local/roots.yaml').read_bytes()
        if sha(registry_raw)!='46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788':raise ValueError('Registry changed')
        registry=yaml.safe_load(registry_raw);domain=registry['failure_domains']['external_primary'];mount=Path(domain['mount_path'])
        root=Path(registry['roots']['pants_source']['acquisition_parent'])/'extraction-3b1cd6110811-20260922'
        def guard():
            if not mount.is_mount() or mount.is_symlink() or root.resolve(strict=True)!=root:raise ValueError('Unsafe source root')
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>512*1024**2 or shutil.disk_usage(REPO).free<100*1024**3:raise RuntimeError('Memory/free-space cap')
        guard();info=disk_info(mount)
        if info.get('VolumeUUID')!=domain['volume_uuid'] or info.get('MountPoint')!=str(mount):raise ValueError('Wrong mounted source')
        source,env=capture();put(dest/'source.json',source);put(dest/'environment.json',env)
        put(dest/'request.json',encoded(dict(candidate_receipt_sha256=PIN,decision='D-280',plan_sha256=sha((REPO/'docs/capstone/data/LOCALIZER-CANDIDATE-HEADER-JOB-2026-09-29.md').read_bytes()),registry_sha256=sha(registry_raw),qualification_granted=False)))
        rows=[];total=0
        for role,group in selection['candidates'].items():
            if role not in ('train','validation'):raise ValueError('Wrong source role')
            for c in group:
                pair=[]
                for ref in c['inventory_inputs']:
                    guard();rel=Path(ref['uri']);path=root/rel
                    if rel.is_absolute() or '..' in rel.parts or path.resolve(strict=True)!=path or not path.is_relative_to(root) or ref['protected_role']!=role or ref['kind'] not in ('ct','pancreas'):raise ValueError('Unsafe selected input')
                    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
                    with os.fdopen(fd,'rb') as stream:
                        before=os.fstat(stream.fileno());obs=ref['observation']
                        if not stat.S_ISREG(before.st_mode) or before.st_size!=ref['bytes'] or (before.st_dev,before.st_ino,before.st_mtime_ns,before.st_ctime_ns)!=(obs['device'],obs['inode'],obs['mtime_ns'],obs['ctime_ns']):raise ValueError('Inventory identity changed')
                        h=header_only(stream);after=os.fstat(stream.fileno())
                        if any(getattr(before,k)!=getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')):raise ValueError('Source changed during header read')
                    total+=h['compressed_bytes_read']
                    if total>4*1024**2:raise RuntimeError('Read budget exceeded')
                    pair.append(dict(kind=ref['kind'],uri=ref['uri'],**h))
                a,b=pair
                concerns=[]
                if a['shape']!=b['shape'] or not np.allclose(a['affine'],b['affine'],rtol=0,atol=1e-5):concerns.append('header_geometry_mismatch')
                if any(x['units'][0]!='mm' for x in pair):concerns.append('physical_units_need_evidence')
                rows.append(dict(study_id=c['study_id'],protected_role=role,headers=pair,concerns=concerns,status='header_only_not_qualified'))
                put(dest/('case-'+c['study_id'].split(':')[-1]+'.json'),encoded(rows[-1]))
        guard()
        if disk_info(mount).get('VolumeUUID')!=domain['volume_uuid']:raise ValueError('Mount changed')
        put(dest/'result.json',encoded(dict(state='header_preflight_complete_not_qualification',cases=rows,source_arrays_read=0,compressed_bytes_read=total,elapsed_seconds=time.monotonic()-start,peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
        if sum(p.stat().st_size for p in dest.iterdir())>4*1024**2:raise RuntimeError('Output cap')
        put(dest/'receipt.json',encoded(dict(state='complete',files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in dest.iterdir()})))
        print(dest);print('receipt_sha256='+sha((dest/'receipt.json').read_bytes()))
    except BaseException as e:
        put(dest/'failure.json',encoded(dict(state='incomplete',error=str(e),elapsed_seconds=time.monotonic()-start)));print(dest);raise
    finally:signal.alarm(0)


if __name__=='__main__':run()
