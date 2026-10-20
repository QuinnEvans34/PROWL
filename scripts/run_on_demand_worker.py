"""Supervised adapter launcher; input identities are checked before and after work."""
import json
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.inference.on_demand import checked_ref

if __name__ == '__main__':
    worker, request_path, output = sys.argv[1:]
    request = json.loads(Path(request_path).read_bytes())
    refs = request['code'] + [request['checkpoint'], request['case']['ct'], request['case']['pancreas']]
    for ref in refs:
        checked_ref(ref)
    sys.argv = [worker, request_path, output]
    runpy.run_path(worker, run_name='__main__')
    for ref in refs:
        checked_ref(ref)
