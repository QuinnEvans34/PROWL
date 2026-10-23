"""Bounded six-training-case CPU timing; no model, updates, data audit or cache writes."""
import argparse
import cProfile
import gc
import json
import os
from pathlib import Path
import pstats
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=Path('E:/PROWL/readiness/pancreas-region-review-20261022-a01')

def worker():
    import numpy as np
    import torch
    from scripts.train_pancreas_region import provider,configuration
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.data.segmenter_pancreas_region_v1 import bank,window_origin
    from src.data.segmenter_physical_windows_v1 import sample_window
    from src.training.segmenter_augmentation_v1 import augment
    from src.data.segmenter_full_batch_v1 import array_hash
    from src.training.experiment_config import sha256
    torch.set_num_threads(2)
    if torch.cuda.is_available():raise ValueError('CPU-only diagnostic required')
    result=json.loads((OUT/'results.json').read_text());p=provider();config=configuration()
    old=PreparedInputs(config,config['full_segmenter']['geometry'])
    means=result['timing']['current']['case_mean_seconds'];selected=[]
    for positive in (True,False):
        group=sorted((n for n in p.control['train'] if (p.review['target_states'][n]=='positive')==positive),key=lambda n:means[n])
        for percentile in (.1,.5,.9):selected.append((group[round((len(group)-1)*percentile)],positive,percentile))
    records=[];combined=cProfile.Profile();started=time.perf_counter()
    for name,positive,quantile in selected:
        start=time.perf_counter();combined.enable()
        case=p.load(name,role='train',operation='optimizer')
        combined.disable();load_seconds=time.perf_counter()-start
        start=time.perf_counter();record,cover=bank(case)
        origin,kind=window_origin(record,cover,step=0,focused_visit=0,seed=42,name=name)
        x,transform=sample_window(case['image'],record,origin,order=1)
        y,_=sample_window(case['target'],record,origin,order=0)
        patch_seconds=time.perf_counter()-start
        start=time.perf_counter();augx,augy,trace=augment(x[None],y,transform,seed=42,update=1,case_id=name)
        augmentation_seconds=time.perf_counter()-start
        start=time.perf_counter();prior=old.get(name,role='train',operation='optimizer')
        prior_seconds=time.perf_counter()-start
        # Estimate native-region array storage WITHOUT building any new on-disk cache.
        region_bytes=case['image'].nbytes+case['target'].nbytes
        records.append(dict(case_id=name,positive=positive,historical_runtime_quantile=quantile,
            historical_mean_update_seconds=means[name],source_shape=case['parent_geometry']['source_shape'],
            region_shape=list(case['image'].shape),factors=record['factors'],region_array_bytes=region_bytes,
            original_ct_suffix=Path(p.rows[name]['ct_path']).suffixes,
            source_ct_bytes=Path(p.rows[name]['ct_path']).stat().st_size,
            region_load_seconds=load_seconds,patch_sampling_seconds=patch_seconds,
            augmentation_seconds=augmentation_seconds,old_prepared_batch_seconds=prior_seconds,
            image_sha256=array_hash(x),target_sha256=array_hash(y)))
        print(json.dumps({k:v for k,v in records[-1].items() if k not in ('image_sha256','target_sha256','source_shape','region_shape')}),flush=True)
        del case,x,y,augx,augy,prior;gc.collect()
    stats=pstats.Stats(combined)
    entries=[dict(file=key[0],line=key[1],function=key[2],calls=value[1],self_seconds=value[2],cumulative_seconds=value[3]) for key,value in stats.stats.items()]
    source_labels=[e for e in entries if e['function'] in ('anchors','coverage_origins','crop_case','source_box','get_fdata','get_unscaled','sha256','target_content','label','decompress','decompressobj','read')]
    source_labels.sort(key=lambda r:r['cumulative_seconds'],reverse=True)
    value=dict(cases=records,load_profile_top=sorted(entries,key=lambda r:r['cumulative_seconds'],reverse=True)[:35],
        load_profile_selected=source_labels[:50],seconds=time.perf_counter()-started,
        CT_reads=6,protected_test_reads=0,optimizer_updates=0,inference_calls=0,cache_written=False,
        source_code_sha256=sha256(__file__),limitations='Six stratified training cases, CPU-only warm/unknown OS cache; not a cold-disk benchmark or GPU timing. Profile subcalls are nested, not additive.')
    with (OUT/'input-profile.json').open('x') as f:json.dump(value,f,indent=2,allow_nan=False)

def main():
    from src.operations.full_training_platform import watch_windows,require_ac
    require_ac()
    if (OUT/'profile-resources.json').exists() or (OUT/'profile.log').exists():raise ValueError('Existing profile; do not repeat')
    with (OUT/'profile.log').open('x') as log:
        process=subprocess.Popen([sys.executable,__file__,'--worker'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',PROWL_PROFILE_SUPERVISED='1'))
        try:watch_windows(process,seconds=600,rss_bytes=12*1024**3,tick=require_ac)
        finally:
            with (OUT/'profile-resources.json').open('x') as f:json.dump(getattr(process,'duration_resources',{}),f)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:
        if os.environ.get('PROWL_PROFILE_SUPERVISED')!='1':raise ValueError('Use supervisor')
        worker()
    else:main()
