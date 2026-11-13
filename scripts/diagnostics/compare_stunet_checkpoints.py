"""Print a paired STU-Net review from saved JSON evidence only."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.training.stunet_checkpoint_review import (  # noqa: E402
    FIXED_5MM, RAW, case_index, compare_checkpoints, require,
)

ARMS = ('baseline', 'trim', 'replace')
POLICY_FILE = ROOT / 'configs/inference/segmentation-postprocessing-v1.json'


def read(path):
    content = path.read_bytes()
    return json.loads(content), hashlib.sha256(content).hexdigest()


def bundle_arm(path, step, policy):
    bundle, digest = read(path)
    matching = []
    for entry in bundle['reports']:
        if 'report' in entry:
            report, report_sha = entry['report'], entry['sha256']
        else:
            require(entry['independent_report_backup_matches'] is True, 'Legacy report backup is unverified')
            report = dict(step=entry['step'], cases=entry['cases_as_saved'], summary=entry['summary_as_saved'])
            report_sha = entry['report_sha256']
        if report['step'] == step and report.get('policy', RAW) == policy:
            matching.append((entry, report, report_sha))
    require(len(matching) == 1, f'Expected exactly one {policy} report at step {step}')
    entry, report, report_sha = matching[0]
    require(isinstance(report_sha, str) and re.fullmatch('[0-9a-f]{64}', report_sha),
            'Missing declared original report SHA-256')
    if 'independent_sha256' in entry:
        require(entry['independent_sha256'] == report_sha, 'Independent report SHA-256 differs')
    if any(key in entry for key in ('primary_sha256', 'independent_backup_sha256', 'backup_match')):
        require(entry.get('primary_sha256') == entry.get('independent_backup_sha256') == report_sha
                and entry.get('backup_match') is True, 'Report and independent backup attestations differ')
    if policy == FIXED_5MM:
        require(entry.get('policy_sha256', bundle.get('policy_sha256')) == read(POLICY_FILE)[1],
                'Fixed 5 mm config hash differs or is absent')
    identities = entry.get('case_identities_from_frozen_inputs', bundle.get('case_identities_from_frozen_inputs'))
    require(isinstance(identities, list), 'Frozen input identities are required')
    return report, identities, dict(bundle_sha256=digest, declared_original_sha256=report_sha)


def outliner_arms(replay, outliner, baseline_arm, candidate_arm, policy):
    manifest, manifest_sha = read(replay / 'manifest.json')
    report, report_sha = read(replay / 'mac-native-32000.json')
    closeout, _ = read(replay / 'closeout.json')
    original, original_sha = read(replay / 'native-32000.json')
    result, result_sha = read(outliner / 'result.json')
    scoring, _ = read(outliner / 'closeout.json')
    request, request_sha = read(outliner / 'request.json')
    require(closeout['status'] == scoring['status'] == 'VERIFIED_COMPLETE'
            and closeout['manifest_sha256'] == manifest_sha
            and manifest['mac_report_sha256'] == report_sha and manifest['report_sha256'] == original_sha
            and scoring['result_sha256'] == result_sha
            and scoring['request_sha256'] == result['request_sha256'] == request_sha,
            'Replay or scoring closeout does not bind its files')
    step = manifest['step']
    require(step == report['step'] == original['step'] == result['step'] == request['step']
            and manifest['checkpoint_sha256'] == result['checkpoint_sha256']
            and manifest['schema'] == result['baseline_source'], 'Outliner checkpoint binding differs')
    pins = {Path(name).name: digest for name, digest in request['pins'].items()}
    require(pins.get('manifest.json') == manifest_sha and pins.get('native-32000.json') == original_sha
            and pins.get(POLICY_FILE.name) == read(POLICY_FILE)[1]
            and request['raw_and_fixed_5mm'] is True, 'Frozen outliner inputs or policy differ')
    replay_rows = case_index(report['cases'])
    scored_rows = case_index(result['rows'])
    require(replay_rows.keys() == scored_rows.keys(), 'Outliner and replay cohorts differ')
    for name, row in scored_rows.items():
        raw = row['arms']['baseline_raw']
        require({key: value for key, value in raw.items() if key not in ('hit_ids', 'policy_applied')}
                == replay_rows[name]['metrics'], 'Outliner raw baseline does not replay')

    def arm_report(arm):
        suffix = 'raw' if policy == RAW else 'near5'
        rows = [dict(replay_rows[name], metrics=row['arms'][f'{arm}_{suffix}'], small_ids=row['small_ids'])
                for name, row in scored_rows.items()]
        return dict(step=step, cases=rows, policy=policy)

    return arm_report(baseline_arm), arm_report(candidate_arm), manifest['cases'], dict(
        manifest_sha256=manifest_sha, baseline_report_sha256=report_sha, outliner_result_sha256=result_sha,
        baseline_arm=baseline_arm, candidate_arm=candidate_arm)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', choices=(RAW, FIXED_5MM), default=RAW)
    modes = parser.add_subparsers(dest='mode', required=True)
    bundle = modes.add_parser('bundle', help='Compare two steps in one or two metadata bundles')
    bundle.add_argument('baseline_bundle', type=Path)
    bundle.add_argument('baseline_step', type=int)
    bundle.add_argument('candidate_step', type=int)
    bundle.add_argument('--candidate-bundle', type=Path)
    outliner = modes.add_parser('outliner', help='Verify and compare saved arms from the Mac outliner run')
    outliner.add_argument('replay', type=Path)
    outliner.add_argument('result', type=Path)
    outliner.add_argument('--baseline-arm', choices=ARMS, default='baseline')
    outliner.add_argument('--candidate-arm', choices=ARMS, default='trim')
    args = parser.parse_args()
    try:
        if args.mode == 'bundle':
            a, ai, a_source = bundle_arm(args.baseline_bundle, args.baseline_step, args.policy)
            b, bi, b_source = bundle_arm(args.candidate_bundle or args.baseline_bundle, args.candidate_step, args.policy)
            evidence = dict(baseline=a_source, candidate=b_source)
        else:
            a, b, ai, evidence = outliner_arms(args.replay, args.result, args.baseline_arm,
                                              args.candidate_arm, args.policy)
            bi = ai
        result = compare_checkpoints(a, b, ai, bi, policy=args.policy)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f'Checkpoint review rejected: {error}\n')
    print(json.dumps(dict(result, evidence=evidence), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
