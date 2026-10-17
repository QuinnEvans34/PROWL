#!/usr/bin/env python3
"""Bounded invented-data selector comparison; cannot accept a real catalog."""
import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests/retrieval'))
from src.retrieval import resumable_selection as rs
from src.retrieval import streaming_corpus as sc
from test_streaming_corpus import make_source
from test_topic_selection import article,mesh_xml


def worker(config):
    settings=json.loads(Path(config).read_text())
    args=settings['args'];variant=settings['variant'];timings={}
    area=Path(config).resolve().parent
    for key,relative in dict(catalog='catalog/catalog.sqlite',mesh_path='mesh.xml',
                             receipts='source/receipts.jsonl',packet_path='packet.json').items():
        if rs.safe(args[key]) != area/relative:
            raise ValueError('Worker requires the generated fixture layout')
    if (area/'evidence.txt').read_text() != 'INVENTED benchmark prerequisites; no real corpus permission':
        raise ValueError('Missing synthetic fixture marker')
    if rs.safe(args['output']).parent != area:
        raise ValueError('Worker output must stay in fixture directory')
    def instrument(name):
        original=getattr(rs,name)
        def measured(*a,**kw):
            start=time.perf_counter()
            try: return original(*a,**kw)
            finally: timings[name]=timings.get(name,0)+time.perf_counter()-start
        setattr(rs,name,measured)
    for name in ('metadata','evaluate','save','finish','export_attempt','verify_exports','source_identity'):
        instrument(name)
    start=time.perf_counter()
    if variant=='original':
        result=sc.select(args['catalog'],args['mesh_path'],args['output'],mesh_sha256=args['mesh_sha256'],cutoff_year=2026,free_gib=0,max_gib=1,hours=1/60)
    else:
        result=rs.run(**args)
    seconds=time.perf_counter()-start
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform!='darwin': rss*=1024
    print(json.dumps(dict(variant=variant,seconds=seconds,peak_rss_bytes=rss,timings_seconds=timings,
                         records_sha256=result['records_sha256'],candidate_pmids_sha256=result['candidate_pmids_sha256'],
                         counts=result['counts'],output_bytes=sum(p.stat().st_size for p in Path(args['output']).rglob('*') if p.is_file()))))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--worker',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker: return worker(args.worker)
    if args.output is None: parser.error('--output required')
    folder=args.output.absolute();folder.mkdir(exist_ok=False)
    pins={str(p.relative_to(ROOT)):sc.sha256(p) for p in [Path(__file__),
          ROOT/'src/retrieval/resumable_selection.py',ROOT/'src/retrieval/streaming_corpus.py',
          ROOT/'scripts/retrieval/select_pubmed_corpus.py',ROOT/'src/retrieval/topic_selection.py',
          ROOT/'tests/retrieval/test_topic_selection.py',ROOT/'tests/retrieval/test_streaming_corpus.py']}
    (folder/'start-identity.json').write_text(json.dumps(pins,indent=2)+'\n')
    started=time.monotonic();measurements=[]
    for count in (1000,10000):
        area=folder/str(count);area.mkdir()
        source=make_source(area,[''.join(article('AI-assisted medical imaging' if i%3 else 'Pancreas CT',pmid=i,year=str(2000+i%26),abstracts=('Invented synthetic abstract. '*8,)) for i in range(1,count+1))])
        cat=area/'catalog';sc.replay(source,cat,free_gib=0)
        mesh=area/'mesh.xml';mesh.write_text(mesh_xml())
        evidence=area/'evidence.txt';evidence.write_text('INVENTED benchmark prerequisites; no real corpus permission')
        packet=area/'packet.json';packet.write_text(json.dumps(dict(version='selection-admission-v1',evidence={
            k:dict(path=str(evidence),sha256=sc.sha256(evidence)) for k in ('seed_freeze','information_needs','reserve_exposure')})))
        reference=None
        for repeat in range(3):
            for variant in ('original','batch100','batch1000'):
                if time.monotonic()-started>180: raise TimeoutError('Benchmark total budget')
                config=area/f'{variant}-{repeat}.json'
                config.write_text(json.dumps(dict(variant=variant,args=dict(catalog=str(cat/'catalog.sqlite'),mesh_path=str(mesh),
                    output=str(area/f'{variant}-{repeat}'),mesh_sha256=sc.sha256(mesh),cutoff_year=2026,
                    receipts=str(source/'receipts.jsonl'),packet_path=str(packet),volume_id='invented-benchmark',
                    free_gib=0,max_gib=1,hours=1/60,batch_size=100 if variant=='batch100' else 1000))))
                child=subprocess.run([sys.executable,__file__,'--worker',str(config)],capture_output=True,text=True,timeout=60)
                (area/f'{variant}-{repeat}.stdout').write_text(child.stdout)
                (area/f'{variant}-{repeat}.stderr').write_text(child.stderr)
                if child.returncode: raise RuntimeError(child.stderr)
                row=json.loads(child.stdout);row.update(records=count,repeat=repeat,exit_code=child.returncode)
                key=[row['records_sha256'],row['candidate_pmids_sha256'],row['counts']]
                if reference is None: reference=key
                if key!=reference: raise ValueError('Differential mismatch')
                measurements.append(row)
                (folder/'measurements.json').write_text(json.dumps(measurements,indent=2)+'\n')
    (folder/'identity.json').write_text(json.dumps(dict(python=sys.version,sqlite=rs.sqlite3.sqlite_version,
        implementation={str(p.relative_to(ROOT)):sc.sha256(p) for p in [Path(__file__),ROOT/'src/retrieval/resumable_selection.py',ROOT/'src/retrieval/streaming_corpus.py']},
        synthetic_only=True,seconds=time.monotonic()-started),indent=2)+'\n')
    print(json.dumps(dict(runs=len(measurements),synthetic_only=True,output=str(folder))))


if __name__=='__main__':main()
