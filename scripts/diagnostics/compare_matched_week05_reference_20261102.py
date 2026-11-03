"""One CPU comparison of the authorized matched-runtime diagnostic; no inference."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.inference.matched_cascade_comparison_v1 import compare,digest,RULE
WIN=Path('E:/PROWL/readiness/week05-matched-qualification-20261102-a01')
MAC=Path('E:/PROWL/transfer/week05-mac-reference-20261102-a01/extracted/week05-mac-reference')
OUT=Path('E:/PROWL/readiness/week05-matched-comparison-20261102-a01')


def main():
    p=argparse.ArgumentParser();p.add_argument('--request-sha256',required=True);a=p.parse_args()
    if OUT.exists():raise FileExistsError('Comparison already started; no overwrite')
    OUT.mkdir()
    (OUT/'comparison-request.json').write_text(json.dumps(dict(rule=RULE,windows_request=a.request_sha256,
        source_pins={str(x):digest(x) for x in (Path(__file__),ROOT/'src/inference/matched_cascade_comparison_v1.py')},
        inference=False),indent=2))
    try:
        result=compare(WIN,MAC,source_root=ROOT,windows_request_sha256=a.request_sha256)
    except BaseException as exc:
        (OUT/'failure.json').write_text(json.dumps(dict(error=repr(exc),rule=RULE),indent=2));raise
    (OUT/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(status=result['status'],comparison=result['comparison'],sha256=digest(OUT/'comparison.json'))))


if __name__=='__main__':main()
