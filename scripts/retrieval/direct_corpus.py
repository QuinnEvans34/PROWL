#!/usr/bin/env python3
"""Local batch embedding/pgvector ingestion and exact-search CLI. No generation."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.retrieval.direct_ingestion import Encoder, source_bundle, source_passages, encoder_passages, frozen_batch, write_once, initialize, load_batch, search, digest


def read_config(path):
    c=json.loads(Path(path).read_text())
    if c['host']!='127.0.0.1' or c['database']!='prowl_literature' or c['user']!='prowl_literature':
        raise ValueError('Only dedicated local literature database allowed')
    for key in ('data','password_file','model_dir','encoder_descriptor'):
        p=Path(c[key])
        if not p.is_absolute() or p.resolve()!=p:
            raise ValueError('Absolute nonsymlink paths required')
    mount=Path(c['mount'])
    if not mount.is_mount() or not Path(c['data']).is_relative_to(mount):
        raise ValueError('External data mount required')
    volume=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',str(mount)],timeout=15))
    if volume.get('VolumeUUID')!=c['volume_uuid']:
        raise ValueError('Wrong external volume')
    if Path(c['password_file']).stat().st_mode & 0o077:
        raise ValueError('Password file must be private')
    return c


def compose(c,*args):
    env=dict(os.environ,PROWL_DB_PORT=str(c['port']),PROWL_DB_DATA=c['data'],PROWL_DB_PASSWORD_FILE=c['password_file'])
    return subprocess.run(['docker','--context','desktop-linux','compose','-p','prowl-literature','-f',str(ROOT/'infra/retrieval/compose.literature.yaml'),*args],env=env,check=True,capture_output=True,timeout=90)


def limits(c):
    if shutil.disk_usage('/System/Volumes/Data').free<104*1024**3 or shutil.disk_usage(c['mount']).free<408*1024**3:
        raise OSError('Storage floor/reservation reached')
    # Data-size checks use Docker's database size during ingestion; no recursive walk of huge stores.


def connect(c):
    import psycopg
    return psycopg.connect(host=c['host'],port=c['port'],dbname=c['database'],user=c['user'],
        password=Path(c['password_file']).read_text().strip(),connect_timeout=5,autocommit=True)


def encoder(c):
    return Encoder(c['model_dir'],json.loads(Path(c['encoder_descriptor']).read_text()))


def ingest(c,args):
    limits(c)
    if not 1<=args.batch_size<=128 or not 0<args.seconds<=1800 or args.max_batches<0:
        raise ValueError('Batch limit1..128; invocation limit0..1800seconds')
    root=Path(args.artifacts);root.mkdir(parents=True,exist_ok=True)
    enc=encoder(c);start=time.monotonic();completed=[]
    with connect(c) as db:
        initialize(db)
        for path in args.sources:
            if time.monotonic()-start>args.seconds:raise TimeoutError('Ingestion time limit')
            bundle=source_bundle(path, profile=getattr(args, 'source_profile', 'legacy-v1'))
            write_once(root/(bundle['revision']['revision_id'].replace(':','-')+'.json'),bundle)
            rows=list(encoder_passages(bundle,enc))
            for offset in range(0,len(rows),args.batch_size):
                limits(c)
                if time.monotonic()-start>args.seconds:raise TimeoutError('Ingestion time limit')
                if db.execute('SELECT pg_database_size(current_database())').fetchone()[0]>8*1024**3:
                    raise OSError('Initial database8GiB cap reached')
                batch_rows=rows[offset:offset+args.batch_size]
                # Stable artifact key permits retries without recomputing completed embeddings.
                key=digest(dict(rows=batch_rows,encoder=enc.descriptor))
                target=root/(key+'.batch.json')
                if target.exists():
                    batch=json.loads(target.read_text())
                    if batch['encoder']!=enc.descriptor or [i['record'] for i in batch['items']]!=batch_rows:
                        raise ValueError('Frozen artifact differs from current source')
                else:
                    batch=frozen_batch(batch_rows,enc.encode([r['text'] for r in batch_rows]),enc.descriptor)
                    write_once(target,batch)
                result=load_batch(db,args.collection,batch)
                completed.append(result)
                print(json.dumps(dict(state='batch_published',**result)),flush=True)
                if args.max_batches and len(completed)>=args.max_batches:
                    return dict(collection=args.collection,batches=completed,seconds=time.monotonic()-start,stopped_at_batch_limit=True)
    return dict(collection=args.collection,batches=completed,seconds=time.monotonic()-start)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True)
    sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('start');sub.add_parser('stop')
    i=sub.add_parser('ingest');i.add_argument('--sources',nargs='+',required=True);i.add_argument('--artifacts',required=True)
    i.add_argument('--source-profile',choices=('legacy-v1','coverage-v1'),default='legacy-v1')
    i.add_argument('--collection',default='research-v1');i.add_argument('--batch-size',type=int,default=32)
    i.add_argument('--seconds',type=float,default=300);i.add_argument('--max-batches',type=int,default=0)
    l=sub.add_parser('load');l.add_argument('--batches',nargs='+',required=True);l.add_argument('--collection',required=True)
    s=sub.add_parser('search');s.add_argument('--collection',default='research-v1');s.add_argument('--question',required=True);s.add_argument('--k',type=int,default=5)
    a=p.parse_args();c=read_config(a.config)
    if a.action=='start':
        limits(c)
        if not Path(c['data']).is_dir():raise ValueError('Provision dedicated data directory first')
        # Existing project may be resumed; Compose never changes unrelated projects.
        info=json.loads(subprocess.check_output(['docker','--context','desktop-linux','info','--format','{{json .}}'],timeout=20))
        physical=int(subprocess.check_output(['sysctl','-n','hw.memsize']))
        if info['MemTotal']>physical*.15:raise ValueError('Docker memory exceeds15% host limit')
        compose(c,'up','-d','--wait','--wait-timeout','60')
        with connect(c) as db:initialize(db)
        print(json.dumps(dict(state='ready',port=c['port'],project='prowl-literature')))
    elif a.action=='stop':
        compose(c,'stop','-t','60');print(json.dumps(dict(state='stopped',project='prowl-literature')))
    elif a.action=='ingest':
        print(json.dumps(ingest(c,a),indent=2))
    elif a.action=='load':
        with connect(c) as db:
            initialize(db)
            for path in a.batches:
                limits(c)
                if Path(path).stat().st_size>8*1024**2:raise ValueError('Frozen batch exceeds8MiB')
                if db.execute('SELECT pg_database_size(current_database())').fetchone()[0]>8*1024**3:raise OSError('Initial database8GiB cap reached')
                print(json.dumps(load_batch(db,a.collection,json.loads(Path(path).read_text()))),flush=True)
    else:
        enc=encoder(c)
        with connect(c) as db:result=search(db,a.collection,enc,a.question,a.k)
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()
