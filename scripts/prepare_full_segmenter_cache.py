#!/usr/bin/env python3
"""Supervised candidate content/geometry audit; never authorizes or performs training."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


def worker(config, output):
    from src.training import experiment_config as E
    from src.data.segmenter_full_inputs_v1 import Inputs
    from src.data.manifest_records import canonical
    cfg=E.load_experiment(config);full=cfg['full_segmenter']
    provider=Inputs(cfg,full['geometry'],cache_dir=full['cache_dir'],audit_only=True)
    (output/'input-control.json').write_bytes(canonical(provider.control))
    counts=dict(passed=0,failed=0);started=time.monotonic()
    with (output/'cases.jsonl').open('x') as journal:
        for role,names in [('train',provider.control['train']),('validation',provider.control['validation'])]:
            for name in names:
                try:
                    batch=provider.get(name,role=role,operation='evaluator')
                    record=dict(case_id=name,role=role,status='technical_pass',target_state=provider.states[name],
                        cache_path=str(provider.cache/(name+'.npz')),batch_sha256=batch.hashes())
                    counts['passed']+=1
                    del batch
                except (ValueError,OSError,RuntimeError) as exc:
                    counts['failed']+=1
                    record=dict(case_id=name,role=role,status='technical_failure',error=str(exc))
                record['elapsed_seconds']=time.monotonic()-started
                journal.write(json.dumps(record,allow_nan=False)+'\n');journal.flush();os.fsync(journal.fileno())
    report=dict(**counts,completed=True,optimizer_updates=0,model_forwards=0,
        cohort_accepted=False,source_weights_opened=False,cache=str(provider.cache),
        seconds=time.monotonic()-started)
    (output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',required=True)
    p.add_argument('--output',required=True);p.add_argument('--worker',action='store_true')
    args=p.parse_args();output=Path(args.output).resolve()
    if args.worker:return worker(args.experiment,output)
    from src.training import experiment_config as E
    from src.operations.segmenter_duration_dispatch_v1 import watch
    from scripts.train_full_segmenter import tree_bytes
    import shutil
    cfg=E.load_experiment(args.experiment);full=cfg['full_segmenter']
    # Validate original role separation before any patient payload is opened.
    cohort=cfg['_experiment']['cohort']
    groups={k:set(E.ids(E.resolve(cohort[k]))) for k in ('train_ids','development_ids','original_train_ids','original_development_ids','test_ids')}
    if not groups['train_ids']<=groups['original_train_ids'] or not groups['development_ids']<=groups['original_development_ids'] or groups['train_ids']&groups['development_ids'] or (groups['train_ids']|groups['development_ids'])&groups['test_ids']:
        raise ValueError('Protected role separation failed')
    known_holds={f'PanTS_{n:08d}' for n in (5641,6110,4965,2727,7265)}
    if known_holds&(groups['train_ids']|groups['development_ids']):raise ValueError('Previously held cases remain excluded')
    if output.exists():raise FileExistsError(output)
    if 'AC Power' not in subprocess.check_output(['pmset','-g','batt'],text=True):raise ValueError('AC required')
    with (ROOT/'outputs/prowl/.mps-profile.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        output.mkdir(parents=True,exist_ok=False)
        (output/'request.json').write_text(json.dumps(dict(config=cfg,seconds=7200,rss_bytes=12*1024**3,
            cache_max_bytes=full['cache_max_bytes'],purpose='candidate_geometry_content_audit_no_training'),indent=2)+'\n')
        last=[0.]
        def tick():
            if time.monotonic()-last[0]>=10:
                base=Path(full['cache_dir'])
                while not base.exists():base=base.parent
                if shutil.disk_usage(base).free<100*1024**3 or tree_bytes(full['cache_dir'])>full['cache_max_bytes']:
                    raise RuntimeError('Cache storage boundary reached')
                last[0]=time.monotonic()
        tick()
        process=subprocess.Popen(['/usr/bin/caffeinate','-dimsu',sys.executable,str(Path(__file__).resolve()),
            '--experiment',str(Path(args.experiment).resolve()),'--output',str(output),'--worker'],
            cwd=ROOT,start_new_session=True)
        try:resources=watch(process,seconds=7200,rss_bytes=12*1024**3,tick=tick)
        finally:
            if hasattr(process,'duration_resources'):
                (output/'resources.json').write_text(json.dumps(process.duration_resources,indent=2)+'\n')
        print(json.dumps(resources),flush=True)


if __name__=='__main__':main()
