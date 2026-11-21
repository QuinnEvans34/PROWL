"""Explicit bounded image-candidate audit; never issues patient independence clearance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.stunet_audit.overlap import fingerprint_file, FingerprintIndex


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--manifest-sha256",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--allow-image-reads",action="store_true")
    p.add_argument("--max-cases",type=int,required=True)
    p.add_argument("--max-seconds",type=int,required=True)
    p.add_argument("--appearance-only-unknown-units",action="store_true")
    a=p.parse_args()
    if not a.allow_image_reads:raise ValueError("Image access must be separately scoped/authorized")
    raw=a.manifest.read_bytes()
    if len(raw)>2*1024**2 or hashlib.sha256(raw).hexdigest()!=a.manifest_sha256:raise ValueError("Manifest identity")
    d=json.loads(raw);rows=d["references"]+d["queries"]
    if not 1<=len(rows)<=a.max_cases<=1500 or not 1<=a.max_seconds<=3600:raise ValueError("Run bound")
    if any(r["role"] not in ("train","development","pretraining_reference") for r in rows):raise ValueError("Protected role")
    if len({r["case_id"] for r in rows})!=len(rows):raise ValueError("Duplicate case IDs")
    if a.output.exists():raise FileExistsError(a.output)
    a.output.mkdir();start=time.monotonic()
    def read(r):
        if time.monotonic()-start>a.max_seconds:raise RuntimeError("Elapsed bound")
        path=Path(r["path"])
        # Bind bytes before deriving fingerprints. Do not infer identity from filesystem metadata.
        f=fingerprint_file(path,appearance_only_unknown_units=a.appearance_only_unknown_units)
        if f["file_sha256"]!=r["sha256"]:raise ValueError("Source bytes changed")
        with (a.output/(hashlib.sha256(r["case_id"].encode()).hexdigest()+".json")).open("x") as s:json.dump(f,s)
        return dict(case_id=r["case_id"],fingerprint=f)
    refs=[];failures=[]
    for r in d['references']:
        try:refs.append(read(r))
        except ValueError as e:
            if str(e)=='Source bytes changed':raise
            failures.append(dict(case_id=r['case_id'],error=str(e)))
        with (a.output/'progress.jsonl').open('a') as log:log.write(json.dumps(dict(stage='reference',case_id=r['case_id'],seconds=time.monotonic()-start))+'\n')
    index=FingerprintIndex(refs)
    results=[]
    for r in d["queries"]:
        try:
            q=read(r);row=dict(case_id=r['case_id'],candidates=index.rank(q['fingerprint']),
                              classification='UNRESOLVED',clearance_issued=False)
        except ValueError as e:
            if str(e)=='Source bytes changed':raise
            row=dict(case_id=r['case_id'],candidates=[],classification='UNRESOLVED',error=str(e),clearance_issued=False)
        results.append(row)
        with (a.output/'progress.jsonl').open('a') as log:log.write(json.dumps(dict(stage='query',case_id=r['case_id'],seconds=time.monotonic()-start))+'\n')
    with (a.output/"candidates.json").open("x") as f:json.dump(results,f,indent=2)
    summary=dict(cases=len(rows),references_fingerprinted=len(refs),reference_failures=failures,
                 queries=len(results),query_failures=sum('error' in r for r in results),
                 seconds=time.monotonic()-start,clearance_issued=False)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))


if __name__=="__main__":main()
