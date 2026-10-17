#!/usr/bin/env python3
"""Resumable ordered replay and streaming stage-1 selection of a pinned PubMed snapshot."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.retrieval.streaming_corpus import replay,select


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    build=sub.add_parser('replay')
    build.add_argument('--source',type=Path,required=True)
    build.add_argument('--through',type=int,help='Explicit development prefix; omitted means entire snapshot')
    build.add_argument('--file-seconds',type=int,default=600,help='Per-file processing deadline, 1..7200 seconds')
    build.add_argument('--cache-mib',type=int,default=32,help='SQLite suggested cache, 32..8192 MiB')
    selection=sub.add_parser('select')
    selection.add_argument('--catalog',type=Path,required=True)
    selection.add_argument('--mesh-path',type=Path,required=True)
    selection.add_argument('--mesh-sha256',required=True)
    selection.add_argument('--cutoff-year',type=int,required=True)
    selection.add_argument('--allow-prefix',action='store_true')
    for child in (build,selection):
        child.add_argument('--output',type=Path,required=True)
        child.add_argument('--hours',type=float,default=12)
        child.add_argument('--max-gib',type=float,default=512)
        child.add_argument('--free-gib',type=float,default=400)
    args=vars(parser.parse_args()); action=args.pop('action')
    result=(replay if action=='replay' else select)(**args)
    # No article text is printed; evidence exposure remains a separate workflow.
    print(json.dumps({k:v for k,v in result.items() if k not in ('identity','applied_prefix')},indent=2))

if __name__=='__main__': main()
