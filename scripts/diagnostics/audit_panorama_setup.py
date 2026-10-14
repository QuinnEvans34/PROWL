"""Bounded PANORAMA label/hash/header audit. No CT voxels, models or admission.

Declared imports are not decoded. Other technical holds remain visible in the
ledger; no cohort is published and no case is silently removed from the catalog.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()


def observation(path):
    s=Path(path).stat()
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)


def label_frequencies(path, image):
    """Stream exact stored values with bounded memory; consume/check gzip trailer."""
    import math
    import numpy as np
    dtype=image.get_data_dtype()
    if dtype.kind not in 'iuf' or dtype.itemsize>8:
        raise ValueError('Unsupported source label dtype')
    offset=int(image.dataobj.offset)
    if not 352<=offset<=16*1024**2:
        raise ValueError('Unsupported NIfTI payload offset')
    left=math.prod(image.shape)*dtype.itemsize
    frequencies={str(v):0 for v in range(7)}
    with gzip.open(path,'rb') as stream:
        if len(stream.read(offset))!=offset:raise ValueError('Truncated NIfTI header')
        while left:
            expected=min(left,1024**2)
            block=stream.read(expected)
            if len(block)!=expected:raise ValueError('Truncated label payload')
            values=np.frombuffer(block,dtype=dtype)
            counts={str(v):int(np.count_nonzero(values==v)) for v in range(7)}
            if sum(counts.values())!=values.size:
                raise ValueError('Nonfinite, fractional or unknown source label value')
            for value,count in counts.items():frequencies[value]+=count
            left-=len(block)
        if stream.read(1):raise ValueError('Unexpected trailing label payload')
    return frequencies


def worker(catalog,output):
    import nibabel as nib
    import numpy as np
    from src.data.segmenter_geometry_v2 import canonical_geometry,recipe
    rows=[json.loads(line) for line in catalog.read_text().splitlines()]
    counts=Counter();started=time.monotonic()
    with (output/'cases.jsonl').open('x') as journal:
        for r in rows:
            result=dict(study_id=r['study_id'],disposition=r['disposition'],training_ready=False)
            if r['disposition']=='excluded_declared_import':
                result.update(status='excluded_declared_import',payloads_opened=False)
            else:
                image,label=Path(r['ct']['path']),Path(r['label']['path'])
                before=[observation(image),observation(label)]
                if before[0][2]!=r['ct']['bytes'] or before[1][2]!=r['label']['bytes']:
                    raise ValueError('Source size changed')
                actual=sha(label)
                if actual!=r['label']['expected_sha256']:
                    raise ValueError('Label transfer SHA256 mismatch: '+r['study_id'])
                result.update(label_sha256=actual,ct_sha256_basis='transfer_manifest_not_locally_rehashed')
                try:
                    ct=nib.load(image);mask=nib.load(label)
                    result.update(ct_shape=list(ct.shape),label_shape=list(mask.shape),
                        max_affine_difference=float(np.abs(ct.affine-mask.affine).max()))
                    canonical_geometry(list(ct.shape),ct.affine,recipe())
                    canonical_geometry(list(mask.shape),mask.affine,recipe())
                    if ct.shape!=mask.shape or not np.allclose(ct.affine,mask.affine,rtol=0,atol=1e-5):
                        raise ValueError('CT/label grid mismatch at production tolerance')
                    if float(mask.dataobj.slope)!=1 or float(mask.dataobj.inter)!=0:
                        raise ValueError('Nonidentity label scaling')
                    result['source_label_dtype']=str(mask.get_data_dtype())
                    frequencies=label_frequencies(label,mask)
                    result['voxel_counts']=frequencies
                    if not frequencies['4']:
                        raise ValueError('Empty pancreas')
                    if bool(frequencies['1'])!=(r['pdac']=='positive'):
                        raise ValueError('Source outcome/lesion mask conflict')
                    result.update(status='technical_pass_not_admitted',
                        pancreas_method='machine_generated',lesion_method=r['lesion_method'])
                except (ValueError,OSError) as exc:
                    result.update(status='technical_hold',reason=str(exc))
                if before!=[observation(image),observation(label)]:
                    raise ValueError('Source changed during audit')
            counts[result['status']]+=1
            result['elapsed_seconds']=time.monotonic()-started
            journal.write(json.dumps(result,allow_nan=False)+'\n');journal.flush();os.fsync(journal.fileno())
            if sum(counts.values())%100==0:print(json.dumps(dict(checked=sum(counts.values()),counts=counts)),flush=True)
    summary=dict(completed=True,counts=counts,seconds=time.monotonic()-started,ct_voxel_reads=0,
        model_updates=0,training_ready=False,scope='label_content_and_headers_not_CT_content_or_duplicate_clearance')
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--worker',action='store_true');a=p.parse_args()
    a.catalog=a.catalog.resolve();a.output=a.output.resolve()
    if a.worker:return worker(a.catalog,a.output)
    if os.name!='nt':raise RuntimeError('Windows-only supervisor')
    from src.operations.full_training_platform import training_guard,watch_windows,require_ac
    if a.output.exists():raise FileExistsError(a.output)
    original_catalog_hash=sha(a.catalog)
    device=a.output.parent.stat().st_dev
    def tick():
        require_ac()
        if a.output.stat().st_dev!=device or shutil.disk_usage(a.output).free<100*1024**3:
            raise RuntimeError('Output volume or space changed')
    with training_guard(ROOT/'outputs/prowl/.panorama-setup-audit.lock'):
        a.output.mkdir()
        tick()
        (a.output/'request.json').write_text(json.dumps(dict(catalog=str(a.catalog),
            catalog_sha256=original_catalog_hash,script_sha256=sha(__file__),seconds=3600,
            rss_bytes=4*1024**3,no_training=True,no_CT_voxel_reads=True),indent=2)+'\n')
        with (a.output/'worker.log').open('x') as log:
            child=subprocess.Popen([sys.executable,__file__,'--catalog',str(a.catalog),
                '--output',str(a.output),'--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:
                watch_windows(child,seconds=3600,rss_bytes=4*1024**3,tick=tick)
                if sha(a.catalog)!=original_catalog_hash:raise RuntimeError('Catalog changed')
            finally:
                (a.output/'resources.json').write_text(json.dumps(getattr(child,'duration_resources',{}),indent=2)+'\n')
        print((a.output/'summary.json').read_text(),flush=True)


if __name__=='__main__':main()
