"""Explicit full-cohort target publication; no inference or training launch."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.teacher_target_publication_v1 import publish, read_bound


def main(argv=None, *, provider_factory=None, preflight=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    for name in ('request', 'result', 'resources', 'provider'):
        parser.add_argument(f'--{name}-sha256', required=True)
    args = parser.parse_args(argv)
    # Reject an unfinished generation before expensive provider construction.
    result = read_bound(args.targets / 'result.json', args.result_sha256)
    resources = read_bound(args.targets / 'resources.json', args.resources_sha256)
    if (result.get('success') is not True or result.get('complete') is not True
            or resources.get('success') is not True or resources.get('workers_reaped') is not True
            or type(resources.get('exit_code')) is not int or resources['exit_code'] != 0):
        raise ValueError('Successful complete, reaped generation required')
    if preflight is None:
        from scripts.diagnostics.qualify_distillation_mac import storage_preflight
        preflight = storage_preflight
    preflight()
    if provider_factory is None:
        from scripts.diagnostics.prepare_rsuper_full_provider import provider
        provider_factory = lambda: provider()[0]
    bound = provider_factory()
    if len(bound.control['train']) != 1333 or len(bound.control['validation']) != 70:
        raise ValueError('Full 1333/70 provider required')
    answer = publish(args.targets, args.output, bound,
        request_sha256=args.request_sha256, result_sha256=args.result_sha256,
        resources_sha256=args.resources_sha256, provider_sha256=args.provider_sha256)
    print(json.dumps(answer, sort_keys=True))
    return answer


if __name__ == '__main__':
    main()
