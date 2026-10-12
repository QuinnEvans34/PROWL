#!/usr/bin/env python3
"""Build a metadata-only portable admission or bind it to the existing evaluator."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.portable_cohort import build, canonical, digest, pinned, resolve_cases
from src.inference.fixed_cohort_evaluation import validate_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('build')
    for name in ('review-path', 'review-sha256', 'manifest', 'train-ids', 'development-ids',
                 'original-train-ids', 'original-development-ids', 'test-ids', 'source-root', 'cache-root'):
        command.add_argument('--' + name, required=True)
    command.add_argument('--output', required=True)
    command = commands.add_parser('plan')
    for name in ('package', 'package-sha256', 'current-review-sha256', 'roots', 'settings', 'output'):
        command.add_argument('--' + name, required=True)
    args = vars(parser.parse_args()); mode = args.pop('command'); output = Path(args.pop('output'))
    if output.exists(): parser.error('Output exists; choose a new artifact path')
    if mode == 'build':
        value = build(**args)
    else:
        package = json.loads(pinned(args['package'], args['package_sha256']))
        roots = json.loads(Path(args['roots']).read_text())
        settings = json.loads(Path(args['settings']).read_text())
        if set(settings) != {'inference', 'limits'}:
            parser.error('Settings must contain exactly inference and limits')
        value = dict(version=2, cohort_id=package['cohort_id'], **settings,
                     cases=resolve_cases(package, roots, expected_sha256=args['package_sha256'],
                                         current_review_sha256=args['current_review_sha256']),
                     limitations=package['limitations'],
                     cohort_binding=dict(package=package, sha256=args['package_sha256'], roots=roots,
                                         current_review_sha256=args['current_review_sha256']))
        validate_plan(value)
    raw = canonical(value)
    with output.open('xb') as stream: stream.write(raw)
    print(json.dumps(dict(path=str(output.resolve()), sha256=digest(raw))))


if __name__ == '__main__': main()
