#!/usr/bin/env python3
"""Build or search a private exploratory catalog; no vector DB or model required."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.retrieval.pubmed_catalog import build, search

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('build')
    prep.add_argument('--source',type=Path,required=True)
    prep.add_argument('--output',type=Path,required=True)
    prep.add_argument('--max-files',type=int,default=3)
    lookup=sub.add_parser('search')
    lookup.add_argument('--catalog',type=Path,required=True)
    lookup.add_argument('--query',required=True)
    lookup.add_argument('--limit',type=int,default=10)
    args=parser.parse_args()
    result=build(args.source,args.output,args.max_files) if args.action=='build' else search(args.catalog,args.query,args.limit)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
