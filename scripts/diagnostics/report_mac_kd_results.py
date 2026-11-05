"""Report current KD evidence or verify completed Mac closeout; never launch work."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.operations.mac_kd_result_report_v1 import report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = report(args.root, args.ready_sha256, args.output)
    print(json.dumps({k: result[k] for k in ('status', 'missing_native_steps', 'execution_closeout_verified',
                                            'hypothesis_decision', 'practical_decision')}))
