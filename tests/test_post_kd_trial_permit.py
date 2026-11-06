import json
from pathlib import Path
import pytest
from src.operations.post_kd_trial_permit_v1 import issue
from src.operations.universal_swin_candidate_v1 import digest


def inputs(tmp_path):
    (tmp_path/'run').mkdir()
    ready, spec = tmp_path/'run/ready.json', tmp_path/'spec.md'
    ready.write_text('{}'); spec.write_text('frozen trial')
    steps = list(range(2000, 24001, 2000))
    body = dict(schema='prowl.mac-kd.result-report.v1', status='CLOSED_DESCRIPTIVE_ONLY',
                execution_closeout_verified=True, pending_terminal_receipts=[],
                completed_native_steps=dict(control=steps, treatment=steps),
                missing_native_steps=dict(control=[], treatment=[]),
                metadata_pins={str(ready): digest(ready)},
                closeout=dict(treatment=dict(current_process_absence_verified=True,
                             historical_supervision_success=True, tracking=dict(status='FINISHED'))))
    report = tmp_path/'report.json'
    report.write_text(json.dumps(body))
    return report, ready, spec, body


def call(report, ready, spec, out):
    return issue(report, digest(report), ready, digest(ready), 'a'*64, spec, digest(spec), out)


def test_verified_completion_binds_one_request_and_cannot_overwrite(tmp_path):
    report, ready, spec, _ = inputs(tmp_path)
    out = tmp_path/'permit.json'
    p = call(report, ready, spec, out)
    assert p['trial_request_sha256'] == 'a'*64
    assert p['maximum_dispatches'] == 1 and not p['automatic_retry']
    with pytest.raises(FileExistsError): call(report, ready, spec, out)


@pytest.mark.parametrize('damage', ['pending','failed','live','tracking','series','identity','receipts'])
def test_no_permit_before_complete_verified_cleanup(tmp_path, damage):
    report, ready, spec, body = inputs(tmp_path)
    if damage == 'pending': body['execution_closeout_verified'] = False
    if damage == 'failed': body['status'] = 'FAILED_EXECUTION_REVIEW_REQUIRED'
    if damage == 'live': body['closeout']['treatment']['current_process_absence_verified'] = False
    if damage == 'tracking': body['closeout']['treatment']['tracking']['status'] = 'RUNNING'
    if damage == 'series': body['missing_native_steps']['treatment'] = [24000]
    if damage == 'identity': body['metadata_pins'][str(ready)] = 'b'*64
    if damage == 'receipts': body['pending_terminal_receipts'] = ['complete.json']
    report.write_text(json.dumps(body)); out = tmp_path/'refused.json'
    with pytest.raises(ValueError): call(report, ready, spec, out)
    assert not out.exists()


def test_changed_report_hash_and_malformed_request_are_rejected(tmp_path):
    report, ready, spec, _ = inputs(tmp_path)
    with pytest.raises(ValueError, match='input changed'):
        issue(report, 'b'*64, ready, digest(ready), 'a'*64, spec, digest(spec), tmp_path/'bad')
    with pytest.raises(ValueError, match='SHA256'):
        issue(report, digest(report), ready, digest(ready), 'unbound', spec, digest(spec), tmp_path/'bad2')


def test_permit_never_writes_inside_a_producing_attempt(tmp_path):
    report, ready, spec, _ = inputs(tmp_path)
    out = ready.parent/'permit.json'
    with pytest.raises(ValueError, match='outside producing'): call(report, ready, spec, out)
    assert not out.exists()
