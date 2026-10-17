#!/usr/bin/env python3
"""Run a bounded stage-1 selection preview against a v2 catalog and MeSH 2026 XML."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.retrieval.pubmed_catalog import VERSION as CATALOG_VERSION
from src.retrieval.topic_selection import MeshIndex, identity, select_records


def preview(catalog, mesh_path, output, cutoff_year, max_records=10000):
    if not 1 <= max_records <= 10000:
        raise ValueError('Preview permits at most 10,000 reconciliation records')
    mesh = MeshIndex.load(mesh_path,year=2026)
    db = sqlite3.connect(Path(catalog).resolve().as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN')  # Both tables and identities come from the same read snapshot.
        meta = dict(db.execute('SELECT key,value FROM metadata'))
        if meta.get('version') != CATALOG_VERSION:
            raise ValueError('Rebuild a new v2 catalog to retain the deleted-PMID universe')
        applied = list(db.execute('SELECT position,name,sha256,events FROM applied ORDER BY position'))
        if not applied or [r[0] for r in applied] != list(range(len(applied))):
            raise ValueError('Catalog has no contiguous applied prefix')
        count = db.execute('SELECT (SELECT count(*) FROM documents)+(SELECT count(*) FROM deleted)').fetchone()[0]
        if count > max_records:
            raise ValueError('Entire preview exceeds record limit; do not silently truncate the universe')
        columns = ('pmid','xml','deleted','source_file','source_sha256','source_seq')
        rows = db.execute('''SELECT pmid,xml,0,source_file,source_sha256,source_seq FROM documents
                            UNION ALL SELECT pmid,xml,1,source_file,source_sha256,source_seq FROM deleted''')
        result = select_records((dict(zip(columns,row)) for row in rows),mesh,cutoff_year=cutoff_year,max_records=max_records)
    finally:
        db.close()
    result['identity'] = dict(identity(mesh),catalog=meta,applied_prefix=applied,
                              cutoff_listing_year=cutoff_year,
                              adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                              catalog_code_sha256=hashlib.sha256((Path(__file__).resolve().parents[2]/'src/retrieval/pubmed_catalog.py').read_bytes()).hexdigest())
    result.update(preview=True,official_selection_frozen=False,rights_qualified=False,
                  stage=1,sampling_performed=False)
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    with (output/'records.jsonl').open('x') as stream:
        for row in result.pop('rows'):
            stream.write(json.dumps(row,sort_keys=True,ensure_ascii=False)+'\n')
    candidates = result.pop('candidate_pmids')
    (output/'candidate-pmids.txt').write_bytes(''.join(p+'\n' for p in candidates).encode('ascii'))
    (output/'summary.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--mesh-2026',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cutoff-listing-year',type=int,required=True)
    parser.add_argument('--max-records',type=int,default=10000)
    args=parser.parse_args()
    result=preview(args.catalog,args.mesh_2026,args.output,args.cutoff_listing_year,args.max_records)
    print(json.dumps({'counts':result['counts'],'preview':True,'official_selection_frozen':False},indent=2))


if __name__=='__main__': main()
