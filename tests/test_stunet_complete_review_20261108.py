"""Completion cannot be inferred from a last score or an unbound peer summary."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.diagnostics.review_stunet_complete_20261108 import review

ROOT = Path(__file__).resolve().parents[1]
PATHS = [
    'docs/capstone/coordination/LENOVO-STUNET-COMPLETE-NATIVE-METADATA-20261108.json',
    'docs/capstone/operations/STUNET-COMPLETION-20261108.json',
    'docs/capstone/coordination/LENOVO-STUNET-COMPLETED-LOG-ANALYSIS-20261108.json',
]


def packet():
    return [json.loads((ROOT / p).read_bytes()) for p in PATHS]


def run(values):
    args = []
    for value in values:
        raw = json.dumps(value, indent=2).encode() + b'\n'
        args.extend([raw, hashlib.sha256(raw).hexdigest()])
    # Rebind serialization only; the source identity being checked is unchanged.
    values[2]['source_hashes']['completed_export'] = args[1]
    raw = json.dumps(values[2], indent=2).encode() + b'\n'
    args[-2:] = [raw, hashlib.sha256(raw).hexdigest()]
    return review(*args)


def test_complete_six_reports_reproduce_selected_and_terminal_errors():
    args = []
    for path in PATHS:
        raw = (ROOT / path).read_bytes()
        args.extend([raw, hashlib.sha256(raw).hexdigest()])
    result = review(*args)
    assert result['selected_step'] == result['terminal_step'] == 12000
    assert result['status'] == 'COMPLETED_EXPLORATORY_DESCRIPTIVE_ONLY'
    final = result['series'][-1]['summary']
    assert final['positive_macro_dice'] == pytest.approx(.37163303848917034)
    assert final['positive_cases_recall_below_half'] == 15
    assert final['empty_alarm_cases'] == 27
    assert result['launch_authorized'] is False


@pytest.mark.parametrize('mutation,reason', [
    (lambda p: p[0]['reports'].pop(), 'Six complete'),
    (lambda p: p[1].update(workers_absent=False), 'Incomplete peer closure'),
    (lambda p: p[1].update(mlflow_status='RUNNING'), 'Incomplete peer closure'),
    (lambda p: p[1]['resources'].update(exit_code=1), 'Failed or unreaped'),
    (lambda p: p[1].update(selected_step=6000), 'Selection mismatch'),
    (lambda p: p[1]['backup_pairs'].pop(), 'Incomplete backup'),
    (lambda p: p[0]['completion'].update(journal_sha256='0' * 64), 'Completion source'),
    (lambda p: p[2]['source_hashes'].update(**{'inputs.json': '0' * 64}), 'Log input binding'),
    (lambda p: p[2]['blocks_2000'][-1].update(lr_last=1e-4), 'Learning rate'),
    (lambda p: p[2]['blocks_2000'][-1].update(mean_loss=float('nan')), 'Invalid loss'),
    (lambda p: p[2]['timing'].update(validation_seconds_total=0), 'Timing partition'),
    (lambda p: p[2]['exposure'].update(coverage_observed_unique=2977), 'Training exposure'),
])
def test_incomplete_or_conflicting_evidence_is_rejected(mutation, reason):
    values = packet()
    mutation(values)
    with pytest.raises(ValueError, match=reason):
        run(values)


def test_bytes_must_match_supplied_hash_before_parsing():
    args = []
    for path in PATHS:
        raw = (ROOT / path).read_bytes()
        args.extend([raw, hashlib.sha256(raw).hexdigest()])
    args[2] += b' '
    with pytest.raises(ValueError, match='SHA256'):
        review(*args)
