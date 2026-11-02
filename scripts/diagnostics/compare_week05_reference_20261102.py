"""Compare retained CUDA/MPS outputs once; failures preserved, no inference."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.inference.physical_cascade_comparison_v1 import compare,digest,RULE


def main():
    p=argparse.ArgumentParser();p.add_argument('--mac-root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output)
    if out.exists():raise FileExistsError('Comparison already started; preserve evidence')
    out.mkdir(parents=True)
    (out/'comparison-request.json').write_text(json.dumps(dict(rule=RULE,mac_root=str(Path(a.mac_root).resolve()),
        producing_pins={str(p):digest(p) for p in (Path(__file__),ROOT/'src/inference/physical_cascade_comparison_v1.py')},
        tolerance_review_commit='c35cd2b',inference=False),indent=2))
    try:
        result=compare('E:/PROWL/readiness/week05-physical-qualification-20261102-a01',a.mac_root,source_root=ROOT)
    except BaseException as exc:
        (out/'failure.json').write_text(json.dumps(dict(status='ADMISSION_FAILURE',rule=RULE,error=repr(exc)),indent=2));raise
    (out/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(status=result['status'],result_sha256=digest(out/'comparison.json'))))


if __name__=='__main__':main()
