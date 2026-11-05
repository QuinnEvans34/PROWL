"""Prepare matched error evidence while Mac KD runs; no final verdict or jobs."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.operations.kd_error_review_preparation_v1 import prepare

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--ready-sha256', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = prepare(args.root, args.ready_sha256, args.output)
    print(json.dumps(dict(status=result['status'], steps=result['completed_native_steps'],
                          latest_matched_step=result['latest_matched']['step'],
                          hypothesis_decision=None, practical_decision=None)))
