"""Bounded additive throughput stages. No scientific training entry point."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts import train_varied_region as varied
from scripts import train_pancreas_region as parent
from src.data.manifest_records import canonical
from src.training.experiment_config import sha256
from src.operations.full_training_platform import require_ac,watch_windows,training_guard
from src.data.segmenter_fast_varied_v1 import FastVariedInputs,label_case,save_target,POLICY

SETUP=Path('E:/PROWL/readiness/region-throughput-20261022-a01')
CACHE=Path('E:/PROWL/cache/varied-targets-20261022-a01')


def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    with Path(path).open('xb') as f:f.write(canonical(value));f.flush();os.fsync(f.fileno())


def check_pins():
    for file in (parent.SETUP/'ready.json',varied.SETUP/'setup.json'):
        for name,pin in read(file)['pins'].items():
            if sha256(name)!=pin:raise ValueError('Preserved producer changed: '+name)


def resources():
    require_ac()
    if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')):raise ValueError('Disk floor')
    total=sum(p.stat().st_size for p in CACHE.parent.rglob('*') if p.is_file())
    if total>32*1024**3:raise ValueError('Combined cache cap')
    if parent.tree_bytes(parent.BACKUP_ROOT)>27917287424:raise ValueError('Backup cap')


def provider(*,pilot=False,prefetch=True):
    name='pilot-manifest.json' if pilot else 'manifest.json'
    p=FastVariedInputs(target_cache=CACHE,cache_manifest_sha256=sha256(CACHE/name),manifest_name=name,
        qualification_only=pilot,prefetch=prefetch,
        planned_counts=read(varied.SETUP/'schedule.json')['focused_counts'],manifest=parent.MANIFEST,
        review=parent.SOURCE_SETUP/'cohort-review.json',train_file=parent.TRAIN,dev_file=parent.SOURCE_SETUP/'development.txt')
    return p


def build_member(p,name,admitted):
    target,meta=label_case(p,name);expected=admitted[name]
    if not expected['coverage_pass'] or meta['region_low']!=expected['region_low'] or meta['region_high']!=expected['region_high']:
        raise ValueError('Derived region differs from complete coverage proof')
    if meta['lesion_voxels']!=expected['lesion_total'] or meta['pancreas_source_voxels']!=expected['pancreas_total']:
        raise ValueError('Derived targets differ from admitted annotations')
    if len(meta['cover'])!=expected['cover_windows']:raise ValueError('Coverage bank changed')
    return save_target(CACHE,name,target,meta)


def pilot():
    import numpy as np
    import torch
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.data.segmenter_pancreas_region_v1 import bank,window_origin
    from src.data.segmenter_varied_region_v1 import coverage_slots
    from src.training.segmenter_augmentation_v1 import augment
    from src.data.segmenter_full_batch_v1 import array_hash
    if torch.cuda.is_available():raise ValueError('CPU pilot isolation required')
    torch.set_num_threads(2);check_pins();resources()
    output=SETUP/'pilot';output.mkdir(exist_ok=False);CACHE.mkdir(exist_ok=False)
    original=varied.provider();names=read(varied.SETUP/'pilot-selection.json')['cases']
    admitted={r['case_id']:r for r in map(json.loads,(parent.COHORT/'cases.jsonl').read_text().splitlines())}
    began=time.monotonic();members={}
    for name in names:
        resources();members[name]=build_member(original,name,admitted)
    write(CACHE/'pilot-manifest.json',dict(version=1,complete=False,source_control_sha256=original.pin,members=members,
        policy=POLICY,source_cohort_sha256=sha256(parent.COHORT/'cases.jsonl'),CT_voxel_reads=0))
    candidate=provider(pilot=True,prefetch=False);rows=[]
    try:
        for index,name in enumerate(names,1):
            resources();row={};cases={}
            # Alternate reader order to reduce systematic OS-cache timing bias.
            for label,p in ([('original',original),('candidate',candidate)] if index%2 else [('candidate',candidate),('original',original)]):
                start=time.monotonic();cases[label]=p.load(name,role='train',operation='optimizer')
                row[label+'_load_seconds']=time.monotonic()-start
            a,b=cases['original'],cases['candidate']
            for key in ('image','target'):
                if not np.array_equal(a[key],b[key]):raise ValueError('Actual input mismatch: '+key)
            for key in ('geometry','parent_geometry','region_low','region_high','source_sha256','metadata_sha256'):
                if a[key]!=b[key]:raise ValueError('Actual metadata mismatch: '+key)
            record,cover=bank(a);total=original.planned_counts[name];views=[];traces=[];actual_covers=[];origins=[]
            slots=coverage_slots(total,len(cover))
            start=time.monotonic()
            for visit in range(total):
                kwargs=dict(step=4*visit,focused_visit=visit,seed=42)
                old=original.from_case(a,**kwargs);new=candidate.from_case(b,**kwargs)
                if not np.array_equal(old[0],new[0]) or not np.array_equal(old[1],new[1]) or old[2:]!=new[2:]:
                    raise ValueError('Sampled training view changed')
                x,y,transform,trace=new;traces.append(trace)
                if trace['kind']=='reserved_cover':actual_covers.append(tuple(trace['origin']))
                else:
                    if not (y==2 if b['positive'] else y>0).any():raise ValueError('Focused annotation missing')
                    origins.append(tuple(trace['origin']))
                    if len(views)<2:views.append((x[0].copy(),y.copy(),trace))
                if visit in (0,next(v for v in range(total) if v not in slots)):
                    oaug=augment(old[0],old[1],old[2],seed=42,update=4*visit+1,case_id=name)
                    naug=augment(new[0],new[1],new[2],seed=42,update=4*visit+1,case_id=name)
                    if not np.array_equal(oaug[0],naug[0]) or not np.array_equal(oaug[1],naug[1]) or oaug[2]!=naug[2]:
                        raise ValueError('Augmentation changed')
            if actual_covers!=list(map(tuple,cover)):raise ValueError('Coverage reservation changed')
            if any(n>144 for n in record['shape']) and len(set(origins))<2:raise ValueError('No varied origins')
            old=original.from_case(a,step=3,focused_visit=1,seed=42)
            new=candidate.from_case(b,step=3,focused_visit=1,seed=42)
            context,kind=window_origin(record,cover,step=3,focused_visit=1,seed=42,name=name)
            if not np.array_equal(old[0],new[0]) or not np.array_equal(old[1],new[1]) or old[2:]!=new[2:]:
                raise ValueError('Context input changed')
            if new[3]['origin']!=list(context) or new[3]['kind']!=kind:raise ValueError('Parent context changed')
            row['sampling_comparison_seconds']=time.monotonic()-start
            if len(views)!=2:raise ValueError('Missing illustrated jitter views')
            fig,axes=plt.subplots(2,3,figsize=(11,7))
            for line,(image,target,trace) in enumerate(views):
                anchor=[v-o for v,o in zip(trace['anchor'],trace['origin'])]
                for axis in range(3):
                    label=np.take(target,anchor[axis],axis=axis).T
                    axes[line,axis].imshow(np.take(image,anchor[axis],axis=axis).T,cmap='gray',vmin=0,vmax=1,origin='lower')
                    for support,color in ((label>0,'cyan'),(label==2,'red')):
                        if support.any() and not support.all():axes[line,axis].contour(support,levels=[.5],colors=[color],linewidths=.7)
                    axes[line,axis].set_title(f'Jitter {line+1}, axis {axis}');axes[line,axis].axis('off')
            fig.suptitle(f'Private training input {index}/12: lesion red, foreground cyan; annotation-anchor planes')
            fig.tight_layout();figure=f'case-{index:02d}.png';fig.savefig(output/figure,dpi=100);plt.close(fig)
            row.update(case_id=name,positive=b['positive'],passed=True,figure=figure,
                image_sha256=array_hash(b['image']),target_sha256=array_hash(b['target']),
                reserved_windows=len(cover),scheduled_focus_visits=total,distinct_jitter_origins=len(set(origins)),
                exact_region=True,exact_windows=True,exact_augmentation=True,exact_context=True,traces=traces)
            rows.append(row)
            with (output/'progress.jsonl').open('ab') as f:f.write(canonical(dict(completed=index,total=12,seconds=time.monotonic()-began)));f.flush()
            print(json.dumps(dict(completed=index,original_load=row['original_load_seconds'],candidate_load=row['candidate_load_seconds'])),flush=True)
            del cases,a,b,old,new
        write(output/'result.json',dict(passed=True,cases=rows,seconds=time.monotonic()-began,
            CT_reads=24,source_audit_replayed=False,test_reads=0,optimizer_updates=0,
            target_cache_bytes=sum(r['bytes'] for r in members.values()),limitations='12 training cases, alternating reader order; unknown/warm OS cache, no GPU throughput claim'))
    finally:candidate.close()


def supervise(stage):
    check_pins();resources();log=SETUP/(stage+'.log');receipt=SETUP/(stage+'-request.json')
    if log.exists() or receipt.exists():raise ValueError('Stage already started; inspect, never duplicate/retry')
    files=[Path(__file__),ROOT/'src/data/segmenter_fast_varied_v1.py',ROOT/'src/training/segmenter_fast_varied_session_v1.py',
        varied.SETUP/'setup.json',parent.COHORT/'cases.jsonl']
    write(receipt,dict(stage=stage,pins={str(p):sha256(p) for p in files},seconds=1200,rss_bytes=12*1024**3,scientific=False))
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'),log.open('x') as stream:
        process=subprocess.Popen([sys.executable,__file__,'--worker',stage],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_FAST_SETUP='1'))
        try:watch_windows(process,seconds=1200,rss_bytes=12*1024**3,tick=require_ac)
        finally:write(SETUP/(stage+'-resources.json'),getattr(process,'duration_resources',{}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pilot',action='store_true');parser.add_argument('--worker',choices=['pilot']);args=parser.parse_args()
    if args.worker:
        if os.environ.get('PROWL_FAST_SETUP')!='1':raise ValueError('Supervisor required')
        for name,pin in read(SETUP/(args.worker+'-request.json'))['pins'].items():
            if sha256(name)!=pin:raise ValueError('Stage pin changed')
        pilot()
    elif args.pilot:supervise('pilot')
    else:parser.error('Select bounded preparation stage')
