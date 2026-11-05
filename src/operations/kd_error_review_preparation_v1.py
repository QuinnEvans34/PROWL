"""Metadata-only preparation for matched Mac KD error review.

Uses the existing native report/component contracts. Never loads images, models,
checkpoints or a training session; never issues a final statistical verdict.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from src.training.native_error_review_v1 import (
    POLICY, REGION_SCOPE, case_error, check_pair, close, component_table,
    fingerprint, require, select_complete_series, summarize, validate_report,
)

STEPS = list(range(2000, 24001, 2000))
MAX_JSON_BYTES = 16 * 1024**2
MAX_JOURNAL_BYTES = 128 * 1024**2


def strict_json(raw):
    def number(value):
        parsed = float(value)
        require(math.isfinite(parsed), 'Nonfinite metadata number')
        return parsed
    def constant(value):
        raise ValueError('Nonfinite metadata constant: ' + value)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate metadata key')
            result[key] = value
        return result
    return json.loads(raw, parse_float=number, parse_constant=constant, object_pairs_hook=unique)


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


class MetadataReader:
    def __init__(self):
        self.pins = {}
        self.prefixes = {}

    def read(self, path, expected=None):
        path = Path(path).resolve()
        require(path.suffix == '.json', 'JSON metadata only')
        with path.open('rb') as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
        require(len(raw) <= MAX_JSON_BYTES, 'Metadata allocation limit')
        pin = sha_bytes(raw)
        require(expected is None or pin == expected, 'Metadata SHA256 mismatch: ' + str(path))
        require(str(path) not in self.pins or self.pins[str(path)] == pin, 'Metadata changed during preparation')
        self.pins[str(path)] = pin
        return strict_json(raw), pin

    def journal(self, path):
        """Admit a complete-line prefix; append-only progress may continue."""
        path = Path(path).resolve()
        require(path.suffix == '.jsonl', 'Journal metadata only')
        length = 0
        digest = hashlib.sha256()
        first = None
        last = None
        completed = {}
        counter = None
        with path.open('rb') as stream:
            for raw in stream:
                if not raw.endswith(b'\n'):
                    break
                length += len(raw)
                require(length <= MAX_JOURNAL_BYTES, 'Journal allocation limit')
                row = strict_json(raw)
                if first is None:
                    require(row['event'] == 'started' and type(row.get('step', 0)) is int, 'Journal start required')
                    first = dict(step=row.get('step', 0), identity_sha256=fingerprint(row['identity']))
                    counter = first['step']
                if row['event'] == 'update':
                    require(type(row['step']) is int and row['step'] == counter + 1, 'Noncontiguous journal updates')
                    counter = row['step']
                if row['event'] == 'native_completed':
                    require(row['step'] in STEPS and row['step'] <= counter and row['step'] not in completed,
                            'Invalid/duplicate completed native step')
                    completed[row['step']] = row['lesion_positive_macro_dice']
                last = dict(event=row['event'], step=row.get('step'))
                digest.update(raw)
        require(first is not None, 'Empty journal')
        self.prefixes[str(path)] = dict(bytes=length, sha256=digest.hexdigest())
        return dict(first=first, last=last, last_update=counter, completed=completed)

    def verify(self):
        for path, pin in self.pins.items():
            with Path(path).open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == pin, 'Input metadata changed')
        for path, record in self.prefixes.items():
            with Path(path).open('rb') as stream:
                raw = stream.read(record['bytes'])
            require(len(raw) == record['bytes'] and sha_bytes(raw) == record['sha256'], 'Journal prefix changed')


def matching_designs(designs):
    require(len(designs) == 2, 'Two matched designs required')
    control, treatment = designs
    expected = deepcopy(control)
    require(control['distillation']['max_weight'] == 0, 'Zero-KD control required')
    expected['distillation']['max_weight'] = .1
    require(expected == treatment, 'Only auxiliary KD weight may differ')
    require(control['evaluation']['steps'] == STEPS and control['evaluation']['terminal_required'] is True
            and control['evaluation']['selection'] == 'max_positive_patient_macro_native_Dice_earliest_tie',
            'Frozen horizon and endpoint selection required')
    require(control['student_configuration']['_experiment']['run'] ==
            dict(checkpoint_every=500, max_updates=24000, validate_every=2000), 'Frozen training cadence')
    return dict(changed_factor='auxiliary_teacher_loss_only', control_weight=0, treatment_weight=.1,
                design_sha256=[fingerprint(x) for x in designs], policy=deepcopy(POLICY))


def reference_signature(report, sidecar, report_sha256, expected, positive_cases):
    rows = validate_report(report, expected, positive_cases=positive_cases)
    components = component_table(sidecar, report, report_sha256)
    signature = {}
    for name in expected:
        row, comp = rows[name], components[name]
        require(row.get('component_evidence') == comp, 'Embedded/sidecar component evidence differs')
        signature[name] = dict(target_sha256=comp['target_sha256'], geometry_sha256=comp['geometry_sha256'],
            reference_components=[{k: c[k] for k in ('component_id', 'voxels', 'volume_mm3')} for c in comp['components']])
    return signature


def collect_series(reader, locations, arm, expected, *, positive_cases=36):
    """Read only validations committed in a journal and recoverable at its bound."""
    require(1 <= len(locations) <= 16, 'Bounded continuation lineage required')
    roots = [str(Path(x['root']).resolve()) for x in locations]
    require(len(roots) == len(set(roots)), 'Duplicate lineage segment')
    reports, signatures, sources, journals = {}, {}, {}, []
    previous_cap = None
    for location in locations:
        root, backup = Path(location['root']), Path(location['backup'])
        require(root.is_absolute() and backup.is_absolute() and root.resolve() != backup.resolve(), 'Separate absolute evidence/backup roots')
        journal = reader.journal(root / arm / 'execution/history.jsonl')
        require(previous_cap is None or journal['first']['step'] == previous_cap, 'Continuation checkpoint boundary differs')
        journals.append(dict(root=str(root), **journal))
        cap = location.get('checkpoint_step', journal['last_update'])
        require(type(cap) is int and journal['first']['step'] <= cap <= journal['last_update'], 'Invalid recoverable segment bound')
        previous_cap = cap
        for step, score in journal['completed'].items():
            if step > cap:
                continue
            path = root / arm / f'execution/native-{step:06d}.json'
            report, pin = reader.read(path)
            reader.read(backup / arm / path.name, pin)
            sidecar, component_pin = reader.read(path.with_name(path.stem + '-components.json'))
            reader.read(backup / arm / (path.stem + '-components.json'), component_pin)
            require(report['step'] == step and report['scope'] == REGION_SCOPE, 'Native step/scope mismatch')
            require([x['case_id'] for x in report['cases']] == list(expected), 'Native cohort order mismatch')
            require(close(report['lesion_positive_macro_dice'], score), 'Journal/report score mismatch')
            signature = reference_signature(report, sidecar, pin, expected, positive_cases)
            if signatures:
                require(signature == next(iter(signatures.values())), 'Native reference identity changed across validations')
                check_pair(validate_report(next(iter(reports.values())), expected, positive_cases=positive_cases),
                           validate_report(report, expected, positive_cases=positive_cases))
            if step in reports:
                require(pin == sources[step]['report_sha256'], 'Conflicting completed validation copies')
            reports[step], signatures[step] = report, signature
            sources[step] = dict(report_path=str(path), report_sha256=pin,
                                 components_path=str(path.with_name(path.stem + '-components.json')),
                                 components_sha256=component_pin)
    return dict(reports=reports, signatures=signatures, sources=sources, journals=journals)


def paired_errors(control, treatment, expected, *, positive_cases=36):
    a = validate_report(control, expected, positive_cases=positive_cases)
    b = validate_report(treatment, expected, positive_cases=positive_cases)
    require(control['scope'] == treatment['scope'] == REGION_SCOPE, 'Matched inference scope required')
    require(control['step'] == treatment['step'], 'Same-update diagnostic required')
    check_pair(a, b)
    rows = []
    for name in expected:
        old, new = case_error(a[name]), case_error(b[name])
        rows.append(dict(case_id=name, reference_positive=old['target_voxels'] > 0,
            control=old, treatment=new,
            dice_delta=None if old['target_voxels'] == 0 else new['dice'] - old['dice'],
            false_positive_voxel_delta=new['false_positive'] - old['false_positive'],
            false_negative_voxel_delta=new['false_negative'] - old['false_negative'],
            missed_component_delta=(new['components'] - new['components_detected']) -
                                   (old['components'] - old['components_detected'])))
    return dict(scope='same_update_descriptive_only', step=control['step'],
        control=summarize(control, expected, positive_cases=positive_cases),
        treatment=summarize(treatment, expected, positive_cases=positive_cases), cases=rows,
        confidence_intervals=None, hypothesis_decision=None, practical_decision=None,
        spatial_error_categories='not_inferred_from_aggregate_counts',
        limitations=['Selected visual examples are not a quantitative acceptance subset.',
                     'Raw native reports do not locate false-positive components or attached spillover.',
                     'Spatial categories require separately bound predictions/visual review under the same inference scope.'])


def prepare(root, ready_sha256, output):
    reader = MetadataReader()
    root, output = Path(root).resolve(), Path(output)
    require(not output.exists(), 'Fresh analysis output required')
    receipt, _ = reader.read(root / 'ready.json', ready_sha256)
    require(receipt['version'] == 'mac-kd-treatment-resume-3' and receipt['automatic_retry'] is False,
            'Explicit resumed Mac treatment receipt required')
    scientific, _ = reader.read(Path(receipt['original']) / 'ready.json', receipt['original_sha256'])
    require(scientific == receipt['scientific'], 'Original scientific receipt differs')
    match = matching_designs(scientific['designs'])
    provider_path = Path(scientific['preparation']['admitted_targets']) / 'provider-control.json'
    provider, provider_pin = reader.read(provider_path, scientific['preparation']['pins'][str(provider_path)])
    require(all(x['provider_sha256'] == provider_pin for x in scientific['designs']), 'Matched provider binding')
    expected = provider['validation']
    require(len(expected) == len(set(expected)) == 70 and len(provider['train']) == len(set(provider['train'])) == 1333
            and not set(expected) & set(provider['train']), 'Frozen train/development roles required')
    arms = {}
    for arm in ('control', 'treatment'):
        locations = list(receipt['segments'][arm])
        if arm == 'treatment':
            locations.append(dict(root=str(root), backup=receipt['backup']))
        arms[arm] = collect_series(reader, locations, arm, expected)
    common = sorted(set(arms['control']['reports']) & set(arms['treatment']['reports']))
    require(common, 'At least one complete matched validation required')
    for step in common:
        require(arms['control']['signatures'][step] == arms['treatment']['signatures'][step], 'Cross-arm native reference identities differ')
    step = common[-1]
    diagnostic = paired_errors(arms['control']['reports'][step], arms['treatment']['reports'][step], expected)
    closeout = receipt['control_closeout']
    require(closeout['optimization_complete'] is True and closeout['version'] == 'reviewed-control-closeout-1', 'Reviewed control closeout required')
    control_root = Path(receipt['segments']['control'][-1]['root'])
    result, result_pin = reader.read(control_root / 'control/result.json')
    reader.read(Path(receipt['segments']['control'][-1]['backup']) / 'control/result.json', result_pin)
    resources, _ = reader.read(control_root / 'control/resources.json')
    require(result == closeout['result'] and resources == closeout['resources'], 'Reviewed control evidence changed')
    require(result['completed_updates'] == 24000 and result['completed'] is True
            and resources['success'] is False and resources['workers_reaped'] is False
            and resources['error'] == "ValueError('Owned worker descendant was not reaped')", 'Historical control outcome must remain explicit')
    endpoints = {}
    for arm in arms:
        series = list(arms[arm]['reports'].values())
        if sorted(arms[arm]['reports']) == STEPS:
            selected, terminal = select_complete_series(series, expected)
            endpoints[arm] = dict(selected_step=selected['step'], terminal_step=terminal['step'])
    missing = {arm: sorted(set(STEPS) - set(arms[arm]['reports'])) for arm in arms}
    report = dict(schema='prowl.mac-kd.error-review-preparation.v1', status='PREPARATION_ONLY_NO_FINAL_VERDICT',
        matching=match, scope='teacher_assisted_exploratory_provided_pancreas_region', cohort=expected,
        completed_native_steps={arm: sorted(arms[arm]['reports']) for arm in arms}, missing_native_steps=missing,
        endpoints_if_full_series=endpoints, latest_matched=diagnostic,
        series_sources={arm: arms[arm]['sources'] for arm in arms},
        journal_observations={arm: arms[arm]['journals'] for arm in arms},
        historical_control_supervision_success=False,
        required_before_final_verdict=['Both full twelve-validation series and selected/terminal endpoint verification.',
            'Terminal results, independent backups, actual worker cleanup and read-only MLflow closeout for both arms.',
            'Explicit treatment of preserved control cleanup failure; never rewrite it as healthy supervision.',
            'Review patient-independence/provenance before using the patient bootstrap; case IDs alone do not establish independence.',
            'Reuse existing POLICY/component guard and comparison math; no changed threshold or selected-example acceptance.'],
        uncertainty_status='Patient-bootstrap interpretation withheld pending provenance review; paired case point estimates only.',
        final_comparison_authorized=False, hypothesis_decision=None, practical_decision=None,
        inference_calls=0, optimizer_updates=0, image_or_checkpoint_reads=0)
    reader.verify()
    report['metadata_pins'], report['journal_prefixes'] = reader.pins, reader.prefixes
    output.mkdir(parents=True, exist_ok=False)
    (output / 'preparation.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report
