#!/usr/bin/env python3
"""Bounded 100k synthetic benchmark and separate-instance restore; never pulls/deletes.

Uses two fresh external bind directories under --trial-root. Keeps both stopped
containers and all data. 30 minutes, combined 8 GiB, existing 100/400 GiB floors.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import check_pgvector_platform as p

DOCKER = ['docker','--context','desktop-linux']
PROJECTS = ('prowl-retrieval-qualification','prowl-retrieval-restore')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--trial-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    c=json.loads(args.config.read_text())
    p.validate_config(c)
    if args.trial_root != args.trial_root.resolve() or not args.trial_root.is_relative_to(Path(c['mount'])):
        raise ValueError('Trial root must be an absolute nonsymlink path on the configured volume')
    lock=(p.ROOT/'outputs/prowl/pgvector-platform.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    report=p.preflight(c)
    # The preserved smoke instance is expected; independently verify it is stopped.
    if report['errors'] not in ([],['Existing trial container: preserve/review before a fresh run']):
        raise ValueError(report)
    running=p.command(DOCKER+['ps','-q','--filter','label=com.docker.compose.project=prowl-retrieval-smoke']).stdout.strip()
    if running: raise ValueError('Smoke instance still running')
    for project in PROJECTS:
        if p.command(DOCKER+['ps','-aq','--filter',f'label=com.docker.compose.project={project}']).stdout.strip():
            raise ValueError(f'Preserve existing {project}; no automatic retry')
    p.command(DOCKER+['image','inspect',p.IMAGE])
    password=Path(c['password_file'])
    if not password.is_file() or password.is_symlink() or password.stat().st_mode & 0o077:
        raise ValueError('Private password file required')
    args.output.mkdir(parents=True,exist_ok=False)
    args.trial_root.mkdir(exist_ok=False)
    source=args.trial_root/'source'; restore=args.trial_root/'restore'
    source.mkdir(); restore.mkdir()
    # No host ports for this qualification: all connections are container-local.
    cfg=json.loads(p.command(p.compose(c)[0]+['config','--format','json'],env=p.compose(c)[1]).stdout)
    cfg['services']['db'].pop('ports',None)
    cfg.pop('name',None)
    configs=[]
    for project,data in zip(PROJECTS,(source,restore)):
        cfg['services']['db']['volumes'][0]['source']=str(data)
        file=args.output/(project+'.json');file.write_text(json.dumps(cfg,indent=2))
        configs.append(DOCKER+['compose','-p',project,'-f',str(file)])
    runtime=dict(c,data=str(args.trial_root))
    started=time.monotonic(); result={'state':'running','admission':report,'image':p.IMAGE,'budget_seconds':p.SECONDS,'data_cap':p.DATA_CAP}
    touched=[]
    def interrupt(signum,frame): raise KeyboardInterrupt('Requested stop')
    signal.signal(signal.SIGTERM,interrupt)
    def call(label,cmd,input_file=None):
        p.sample_resources(runtime,started,args.output)
        with (args.output/(label+'.stdout')).open('wb') as out, (args.output/(label+'.stderr')).open('wb') as err:
            inp=input_file.open('rb') if input_file else subprocess.DEVNULL
            proc=None
            try:
                proc=subprocess.Popen(cmd,stdin=inp,stdout=out,stderr=err)
                while proc.poll() is None:
                    p.sample_resources(runtime,started,args.output)
                    time.sleep(1)
                if proc.returncode: raise RuntimeError(f'{label} exited {proc.returncode}')
            finally:
                if proc and proc.poll() is None:
                    proc.terminate()
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired: proc.kill();proc.wait()
                if input_file: inp.close()
        return args.output/(label+'.stdout')
    def ready(base):
        for _ in range(60):
            p.sample_resources(runtime,started,args.output)
            r=subprocess.run(base+['exec','-T','db','pg_isready','-h','127.0.0.1','-U','prowl_trial','-d','prowl_synthetic'],capture_output=True,timeout=5)
            if r.returncode==0: return
            time.sleep(1)
        raise RuntimeError('Readiness timeout')
    def sql(base,label,query):
        return call(label,base+['exec','-T','db','psql','-X','-At','-v','ON_ERROR_STOP=1','-U','prowl_trial','-d','prowl_synthetic','-c',query])
    inventory="COPY (SELECT id,bucket,permitted,md5(body),md5(embedding::text) FROM benchmark.passages ORDER BY id) TO STDOUT WITH CSV"
    try:
        touched.append(configs[0]);call('source-start',configs[0]+['up','-d','--pull','never']);ready(configs[0])
        call('benchmark',configs[0]+['exec','-T','db','psql','-X','-v','ON_ERROR_STOP=1','-U','prowl_trial','-d','prowl_synthetic'],p.ROOT/'infra/retrieval/benchmark.sql')
        measurements=sql(configs[0],'measurements',"SELECT json_agg(m) FROM benchmark.measurements m")
        rows=json.loads(measurements.read_text())
        result['default_recall_min']=min(x['default_recall'] for x in rows)
        result['iterative_recall_min']=min(x['iterative_recall'] for x in rows)
        result['measurements']=len(rows)
        original=sql(configs[0],'inventory-original',inventory)
        # Dump stays on external storage; do not put the corpus-sized dump in internal logs.
        dump=args.trial_root/'synthetic.dump'
        with dump.open('wb') as f:
            proc=subprocess.Popen(configs[0]+['exec','-T','db','pg_dump','-U','prowl_trial','-d','prowl_synthetic','-Fc'],stdout=f,stderr=subprocess.PIPE)
            try:
                while proc.poll() is None:
                    p.sample_resources(runtime,started,args.output);time.sleep(1)
                stderr=proc.stderr.read();(args.output/'dump.stderr').write_bytes(stderr)
                if proc.returncode: raise RuntimeError('Dump failed')
            finally:
                if proc.poll() is None: proc.terminate();proc.wait(timeout=5)
        result['source_stop']=p.stop_trial(configs[0],os.environ,args.output)
        if not result['source_stop']['stop_confirmed']:raise RuntimeError('Source stop unconfirmed')
        touched.append(configs[1]);call('restore-start',configs[1]+['up','-d','--pull','never']);ready(configs[1])
        call('restore',configs[1]+['exec','-T','db','pg_restore','-U','prowl_trial','-d','prowl_synthetic','--exit-on-error','--no-owner','--no-acl'],dump)
        restored=sql(configs[1],'inventory-restored',inventory)
        result['inventory_sha256']=hashlib.sha256(original.read_bytes()).hexdigest()
        result['restored_inventory_sha256']=hashlib.sha256(restored.read_bytes()).hexdigest()
        if original.read_bytes()!=restored.read_bytes():raise RuntimeError('Restored inventory differs')
        result['state']='measurements_and_restore_complete'
    except BaseException as exc:
        result.update(state='failed',error=str(exc));raise
    finally:
        result['stops']=[]
        for index,base in enumerate(touched):
            stopdir=args.output/f'stop-{index}';stopdir.mkdir(exist_ok=True)
            result['stops'].append(p.stop_trial(base,os.environ,stopdir))
        result['seconds']=time.monotonic()-started
        (args.output/'result.json').write_text(json.dumps(result,indent=2))
        if not all(x['stop_confirmed'] for x in result['stops']):raise RuntimeError('Stop not confirmed')


if __name__=='__main__':main()
