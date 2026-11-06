"""Bind one new exploratory request to a verified, completed Mac KD report.

This is a receipt writer, not a scheduler or launcher. The executor must still
enforce a fresh one-shot dispatch, resource gates and exclusive GPU ownership.
"""
import json
from pathlib import Path
import re

from src.operations.universal_swin_candidate_v1 import digest


def issue(report_path, report_sha256, ready_path, ready_sha256,
          trial_request_sha256, specification_path, specification_sha256, output):
    paths = [Path(p).resolve() for p in (report_path, ready_path, specification_path)]
    for value in (report_sha256, ready_sha256, trial_request_sha256, specification_sha256):
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
            raise ValueError('Exact SHA256 identities required')
    for path, pin in zip(paths, (report_sha256, ready_sha256, specification_sha256)):
        if digest(path) != pin:
            raise ValueError('Bound permit input changed')
    report = json.loads(paths[0].read_text())
    if (report.get('schema') != 'prowl.mac-kd.result-report.v1'
            or report.get('status') != 'CLOSED_DESCRIPTIVE_ONLY'
            or report.get('execution_closeout_verified') is not True
            or report.get('pending_terminal_receipts')):
        raise ValueError('Verified complete KD closeout required')
    expected = list(range(2000, 24001, 2000))
    if (report.get('completed_native_steps') != dict(control=expected, treatment=expected)
            or report.get('missing_native_steps') != dict(control=[], treatment=[])):
        raise ValueError('Complete matched validation series required')
    if report.get('metadata_pins', {}).get(str(paths[1])) != ready_sha256:
        raise ValueError('Closeout belongs to a different KD continuation')
    treatment = report.get('closeout', {}).get('treatment', {})
    if (treatment.get('current_process_absence_verified') is not True
            or treatment.get('historical_supervision_success') is not True
            or treatment.get('tracking', {}).get('status') != 'FINISHED'):
        raise ValueError('Clean treatment/tracking closeout required')
    result = dict(schema='prowl.post-kd-trial-permit.v1',
                  action='one_fresh_exploratory_universal_swin_trial',
                  trial_request_sha256=trial_request_sha256,
                  specification_sha256=specification_sha256,
                  kd_ready_sha256=ready_sha256, kd_report_sha256=report_sha256,
                  kd_execution_closeout_verified=True, automatic_retry=False,
                  authorizes_additional_experiments=False, maximum_dispatches=1,
                  executor_still_requires=['fresh_dispatch_marker', 'AC', 'storage',
                                           'memory', 'geometry', 'integrity', 'exclusive_GPU'])
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    return result
