"""Check peer completion bindings and derive STU-Net errors from saved JSON only."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from scripts.diagnostics.review_stunet_interim_20261107 import (
    MAX_BYTES, READY, close, digest, require, summarize,
)


def checked_json(raw, expected):
    require(len(raw) <= MAX_BYTES, "Metadata exceeds byte limit")
    require(digest(expected) and hashlib.sha256(raw).hexdigest() == expected,
            "Metadata SHA256 mismatch")
    return json.loads(raw)


def review(native_raw, native_sha, completion_raw, completion_sha, log_raw, log_sha):
    native = checked_json(native_raw, native_sha)
    completion = checked_json(completion_raw, completion_sha)
    log = checked_json(log_raw, log_sha)
    result = summarize(native_raw, native_sha)
    require([x['step'] for x in result['series']] == list(range(2000, 12001, 2000)),
            "Six complete validations required")
    c = native['completion']
    require(c['status'] == completion['status'] == 'VERIFIED_COMPLETE'
            and c['terminal_step'] == completion['updates'] == 12000
            and completion['ready_sha256'] == READY, "Wrong completed experiment")
    require(completion['mlflow_status'] == 'FINISHED'
            and completion['stored_mlflow_losses_exact'] == 12000
            and completion['pins_verified'] == 237
            and completion['workers_absent'] is True
            and completion['no_successor_launched'] is True, "Incomplete peer closure")
    resources = completion['resources']
    require(resources['workers_reaped'] is True and resources['success'] is True
            and resources['exit_code'] == 0, "Failed or unreaped worker")
    backups = {x['name']: x for x in completion['backup_pairs']}
    expected_names = {f'checkpoint-{s:05d}.pt' for s in range(0, 12001, 500)}
    expected_names |= {f'native-{s:05d}.json' for s in range(2000, 12001, 2000)}
    expected_names |= {'history.jsonl', 'result.json', 'selected.json'}
    require(set(backups) == expected_names and len(completion['backup_pairs']) == 34
            and all(digest(x['sha256']) and type(x['bytes']) is int and x['bytes'] > 0
                    for x in backups.values()), "Incomplete backup inventory")
    for report in native['reports']:
        require(backups[report['report_name']]['sha256'] == report['report_sha256']
                and backups[report['checkpoint']['name']]['sha256']
                    == report['checkpoint']['sha256_from_saved_journal'], "Report/checkpoint backup mismatch")
    best = max(result['series'], key=lambda x: (x['summary']['positive_macro_dice'], -x['step']))
    require(c['selected_step'] == completion['selected_step'] == best['step']
            and c['selected_checkpoint_sha256'] == completion['selected_checkpoint_sha256']
                == best['checkpoint_sha256_from_peer_journal']
            and c['selected_report_sha256'] == best['report_sha256'], "Selection mismatch")
    for field, name in [('selected_receipt_sha256', 'selected.json'),
                        ('result_sha256', 'result.json'), ('journal_sha256', 'history.jsonl')]:
        require(c[field] == backups[name]['sha256'], "Completion source mismatch")
    require(native['journal_prefix']['complete'] is True
            and native['journal_prefix']['sha256'] == c['journal_sha256']
            and native['journal_prefix']['bytes'] == backups['history.jsonl']['bytes'],
            "Incomplete journal binding")
    require(completion['curve'] == [r['summary_as_saved'] | {'step': r['step']}
                                   for r in native['reports']], "Completion curve mismatch")
    require(completion['final_reference_components'] == best['summary']['reference_components']
            and completion['final_detected_components'] == best['summary']['overlapped_reference_components'],
            "Final component summary mismatch")
    require(log['schema'] == 'prowl-stunet-completed-log-analysis-v1'
            and log['analysis_only'] is True, "Wrong log analysis")
    sources = log['source_hashes']
    for name in ['ready.json', 'inputs.json']:
        require(sources[name] == native['source_json_sha256'][name], "Log input binding mismatch")
    for name, field in [('history.jsonl', 'journal_sha256'), ('result.json', 'result_sha256'),
                        ('completion.json', 'receipt_sha256')]:
        require(sources[name] == c[field], "Log completion binding mismatch")
    # Windows working-tree bytes and Git's LF bytes differ. Accept only these exact
    # two serializations, never rewrite an embedded peer hash to make it match.
    crlf_sha = hashlib.sha256(native_raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')).hexdigest()
    require(sources['completed_export'] in {native_sha, crlf_sha}, "Log native packet binding mismatch")
    blocks = log['blocks_2000']
    require(len(blocks) == 6, "Incomplete loss blocks")
    for i, block in enumerate(blocks):
        require((block['start_step'], block['end_step'], block['loss_count'])
                == (i * 2000 + 1, (i + 1) * 2000, 2000), "Loss block mismatch")
        require(all(type(block[k]) in (int, float) and math.isfinite(block[k]) and block[k] >= 0
                    for k in ['mean_loss', 'median_loss', 'update_path_seconds',
                              'checkpoint_seconds', 'validation_seconds']), "Invalid loss/timing")
        for step, key in [(block['start_step'], 'lr_first'), (block['end_step'], 'lr_last')]:
            expected = 1e-4 * step / 500 if step <= 500 else 1e-4 * .5 * (1 + math.cos(
                math.pi * (step - 500) / 11500))
            require(close(block[key], expected), "Learning rate does not reproduce")
        require(sum(block['view_counts'].values()) == 2000, "Block exposure mismatch")
    t = log['timing']
    require(close(t['elapsed_seconds'], completion['training_elapsed_seconds'])
            and close(t['update_path_seconds'], sum(b['update_path_seconds'] for b in blocks))
            and close(t['validation_seconds_total'], sum(b['validation_seconds'] for b in blocks))
            and close(t['elapsed_seconds'], sum(t[k] for k in ['update_path_seconds',
                'validation_seconds_total', 'checkpoint_seconds_including_initial',
                'unattributed_load_and_bookkeeping_seconds'])), "Timing partition mismatch")
    e = log['exposure']
    visits = e['visits_by_case']
    require(len(visits) == e['cases'] == 1333 and sum(visits.values()) == 12000
            and all(type(v) is int and v > 0 for v in visits.values())
            and {str(k): v for k, v in Counter(visits.values()).items()} == e['visits_histogram']
            and e['positive_cases'] + e['empty_cases'] == 1333
            and e['positive_case_updates'] + e['empty_case_updates'] == 12000
            and 0 <= e['patches_with_lesion_voxels'] <= e['positive_case_updates']
            and e['all_planned_coverage_origins_observed'] is True
            and e['coverage_observed_unique'] == e['coverage_required_unique'] == 2978,
            "Training exposure mismatch")
    require(dict(sum((Counter(b['view_counts']) for b in blocks), Counter())) == e['view_counts'],
            "Training view summary mismatch")
    result.update(schema='prowl.stunet.completed-error-review.v1',
                  status='COMPLETED_EXPLORATORY_DESCRIPTIVE_ONLY',
                  selected_step=best['step'], terminal_step=12000,
                  completion_source_sha256=completion_sha, log_source_sha256=log_sha,
                  closure_evidence='Peer saved-JSON attestation with local consistency checks; no live process, MLflow or backup-byte recheck on Mac',
                  training_loss_blocks=blocks, timing=t,
                  training_exposure={k: v for k, v in e.items() if k != 'visits_by_case'},
                  runtime_estimates=log['runtime_estimates'],
                  loss_diagnostics_missing=log['missing_evidence'],
                  launch_authorized=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['native', 'completion', 'log']:
        parser.add_argument(f'--{name}', type=Path, required=True)
        parser.add_argument(f'--{name}-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = []
    for name in ['native', 'completion', 'log']:
        path = getattr(args, name)
        with path.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        inputs.extend([raw, getattr(args, name + '_sha256')])
    result = review(*inputs)
    for index, name in enumerate(['native', 'completion', 'log']):
        require(getattr(args, name).read_bytes() == inputs[index * 2], 'Input changed during review')
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'validations': len(result['series']),
                      'selected_step': result['selected_step'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
