"""Strict CPU-only load audit; never starts the overnight experiment."""
import argparse
import json
from src.operations.universal_swin_candidate_v1 import audit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = audit(args.checkpoint, args.source, args.output)
    print(json.dumps({k: v for k, v in result.items() if k != 'source_pins'}, indent=2))
