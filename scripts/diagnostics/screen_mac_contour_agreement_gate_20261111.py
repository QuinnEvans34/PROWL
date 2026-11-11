"""Exploratory second-lesion admission using a pre-existing agreed lesion core."""
import argparse
import gc
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

import numpy as np
from scipy import ndimage

from scripts.diagnostics import screen_mac_refiner_contour_precision_20261111 as trim
from src.operations.mac_teacher_supervision_v3 import run

read,sha,write = trim.read,trim.sha,trim.write
ARM = trim.previous.ARM
CONTROL = ('p65_r3_near5_swap1','p65_r3_near5_swap2')
ANCHOR_MM3 = 50.0
CAP = 180


def largest_agreed_core(base, old, current, shape, voxel_mm3):
    """Shared 12k >=0.60 and 24k -0.50-margin voxels inside the existing mask."""
    shared = base[(old.reshape(-1)[base]>=8)&(current.reshape(-1)[base]>=8)]
    if not len(shared):
        return 0.0
    xyz = trim.spatial_points(shared,shape)
    xyz -= xyz.min(0)
    support = np.zeros(xyz.max(0)+1,dtype=bool)
    support[tuple(xyz.T)] = True
    labels,_ = ndimage.label(support,structure=trim.replay.saved.STRUCTURE)
    return int(np.bincount(labels[support])[1:].max())*voxel_mm3


def worker(source, directory):
    request = read(directory/'request.json')
    close = read(source/'closeout.json')
    if close['status']!='VERIFIED_COMPLETE' or sha(source/'result.json')!=request['contour_result_sha256']:
        raise ValueError('Contour evidence changed')
    result = read(source/'result.json')
    frozen = read(trim.previous.FROZEN)
    cases, receipts = trim.replay.saved.admitted_cases()
    by_case = {c['case_id']:c for c in cases}
    details,rows = {},[]
    for original in result['rows']:
        row = dict(original,arms=dict(original['arms']))
        name = row['case_id']
        if any(row['arms'][key]['added'] for key in CONTROL):
            trim.replay.safety()
            case = by_case[name]
            shape = case['native_shape']
            file = name+'.json'
            old_receipt = trim.replay.saved.OLDER/file
            if sha(old_receipt)!=sha(trim.replay.saved.OLDER_BACKUP/file):
                raise ValueError('Older case receipt changed')
            old = trim.replay.saved.archive(read(old_receipt)['artifact'],trim.replay.saved.unpack_12k,shape)
            cur = trim.replay.saved.archive(receipts[name]['artifact'],trim.replay.saved.unpack_24k,shape)
            idx,tier,distance,shell = trim.replay.saved.core_support(cur,case['native_affine'],
                                                                   trim_levels=[2,3],grow_radii=[1.5])
            base = np.concatenate((idx[(tier>3)|(distance<=4)],shell[1.5]))
            if len(base)!=row['arms']['baseline']['p']:
                raise ValueError('Baseline changed')
            volume = largest_agreed_core(base,old,cur,shape,row['voxel_mm3'])
            del cur,old
            details[name] = dict(shared_core_mm3=volume, accepted=bool(volume>=ANCHOR_MM3))
        admitted = details.get(name,{}).get('accepted',False)
        for key in CONTROL:
            row['arms'][key+'_agreed'] = row['arms'][key] if admitted else row['arms']['baseline']
        rows.append(row)
        gc.collect()
    paired = trim.summarize(rows,frozen)
    write(directory/'result.json',dict(request_sha256=sha(directory/'request.json'),
          analysis='adaptive exploratory check on the same 70 development scans',
          anchor_mm3=ANCHOR_MM3,details=details,
          controls={k:paired[k] for k in CONTROL},gated={k:paired[k+'_agreed'] for k in CONTROL},
          source_result_sha256=request['contour_result_sha256'],rows=rows))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('directory',type=Path)
    p.add_argument('--worker',action='store_true')
    a=p.parse_args()
    if a.worker:
        worker(a.source,a.directory)
        return
    trim.replay.safety()
    a.directory.mkdir()
    close=read(a.source/'closeout.json')
    write(a.directory/'request.json',dict(source_sha256=sha(__file__),contour_result_sha256=close['result_sha256'],
                                          anchor_mm3=ANCHOR_MM3,controls=list(CONTROL),
                                          scope='exploratory follow-up; no refiner forwards or reference reads'))
    if not run([sys.executable,__file__,str(a.source),str(a.directory),'--worker'],a.directory,
               seconds=CAP,rss_bytes=4*trim.replay.GIB,tick=trim.replay.safety):
        raise SystemExit('Agreement check stopped; preserve evidence')
    if sha(__file__)!=read(a.directory/'request.json')['source_sha256']:
        raise ValueError('Agreement check source changed')


if __name__=='__main__':
    main()
