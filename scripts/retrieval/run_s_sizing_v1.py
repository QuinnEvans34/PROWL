"""Run S sizing tool CLI (sizing_v1). Readiness check only; live execution is refused.

    python scripts/retrieval/run_s_sizing_v1.py --check CONFIG.json --signed-copy RUN-S-SIGNED-<date>.md
    python scripts/retrieval/run_s_sizing_v1.py --execute ...   # always refused in sizing_v1

``--check`` validates a machine-readable sidecar against the signed Markdown copy and prints a
readiness report. Every unmet requirement is listed. Nothing is fetched, created or written.

``--execute`` refuses. Even with every requirement met, sizing_v1 has no live S1 storage binding
(the volume probe and controlled writer belong to Codex's S1 adapter). The binding is a separate,
reviewed integration step, and the S2 dispatch does not authorize executing the network branch.
"""
import argparse
import hashlib
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from src.retrieval.sizing_v1 import RunRefused  # noqa: E402
from src.retrieval.sizing_v1.runner import code_identity, validate_config  # noqa: E402

S1_BINDING_NOTE = 'S1 live storage binding (volume probe + controlled writer) is not integrated in sizing_v1'


def readiness(config, signed_copy_path, repo_root=REPO_ROOT):
    unmet = []
    try:
        validate_config(config)
    except RunRefused as exc:
        unmet.append(f'config: {exc}')
    if not signed_copy_path or not os.path.isfile(signed_copy_path):
        unmet.append('signed copy file not found (S4)')
    else:
        with open(signed_copy_path, 'rb') as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        if digest != config.get('signed_copy_sha256'):
            unmet.append('signed copy SHA-256 does not match the config')
    try:
        if code_identity(repo_root) != config.get('tool_code_hash'):
            unmet.append('tool code hash does not match the tested packet')
    except OSError as exc:
        unmet.append(f'tool code identity unavailable: {exc}')
    s3 = config.get('s3_capacity_reading') or {}
    if not all(s3.get(k) is not None for k in ('volume_uuid', 'free_bytes', 'headroom_floor_bytes')):
        unmet.append('S3 capacity reading at signing is missing')
    executor = str(config.get('executor', '')).lower()
    if not executor or 'claude' in executor:
        unmet.append('executor must be named (Codex or Quinton on Quinton\'s Mac), not Claude')
    unmet.append(S1_BINDING_NOTE)
    return unmet


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', metavar='CONFIG')
    ap.add_argument('--signed-copy')
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    if not args.check:
        ap.error('--check CONFIG is required')
    with open(args.check, encoding='utf-8') as fh:
        config = json.load(fh)
    unmet = readiness(config, args.signed_copy)
    print(json.dumps(dict(ready=not unmet, unmet=unmet), indent=2))
    if args.execute:
        print('REFUSED: live execution is not available in sizing_v1.', file=sys.stderr)
        return 2
    return 0 if not unmet else 1


if __name__ == '__main__':
    sys.exit(main())
