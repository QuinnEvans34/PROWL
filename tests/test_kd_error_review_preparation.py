from copy import deepcopy
import hashlib
import json

import pytest

from src.operations.kd_error_review_preparation_v1 import (
    MetadataReader, STEPS, collect_series, matching_designs, paired_errors, prepare, reference_signature, strict_json,
)
from src.training.native_error_review_v1 import POLICY, REGION_SCOPE

IDS = ['positive-a', 'positive-b', 'empty-a', 'empty-b']


def native(step=2000, extra=0):
    cases, side = [], []
    for i, name in enumerate(IDS):
        n, p, tp = (100, 120+extra, 40) if i < 2 else (0, 10+extra, 0)
        evidence = dict(case_id=name, target_sha256=str(i)*64, geometry_sha256='a'*64,
            components=[dict(component_id=1, voxels=n, volume_mm3=float(n), detected=tp > 0)] if n else [])
        m = dict(lesion=dict(target_voxels=n, predicted_voxels=p, true_positive=tp, dice=2*tp/(n+p)),
            pancreas=dict(target_voxels=10, predicted_voxels=10, true_positive=8, dice=.8),
            voxel_mm3=1., target_volume_mm3=float(n), predicted_volume_mm3=float(p),
            reference_positive=n > 0, case_detected=tp > 0, false_alarm_any=n == 0 and p > 0,
            case_alert_50mm3=p >= 50, reference_components=int(n > 0), detected_components=int(tp > 0),
            predicted_components=1, size_band='small' if n else 'empty')
        cases.append(dict(case_id=name, step=step, scope=REGION_SCOPE, metrics=m,
            component_evidence=evidence, reconstruction=dict(gap_voxels=0, lesion_guided_region=False, assistance='provided_pancreas_mask')))
        side.append(evidence)
    report = dict(step=step, scope=REGION_SCOPE, cases=cases, lesion_positive_macro_dice=80/(220+extra))
    raw = json.dumps(report).encode()
    return report, dict(version='native-components-1', report_sha256=hashlib.sha256(raw).hexdigest(),
                         matching=POLICY['component_matching'], cases=side)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def location(tmp_path, step=2000, *, extra=0, root_name='run'):
    root, backup = tmp_path/root_name, tmp_path/(root_name+'-backup')
    ex = root/'treatment/execution'
    report, components = native(step, extra)
    write(ex/f'native-{step:06d}.json', report)
    write(ex/f'native-{step:06d}-components.json', components)
    write(backup/f'treatment/native-{step:06d}.json', report)
    write(backup/f'treatment/native-{step:06d}-components.json', components)
    events = [dict(event='started', step=step, identity=dict(model='fixed')),
              dict(event='native_completed', step=step, lesion_positive_macro_dice=report['lesion_positive_macro_dice'])]
    (ex/'history.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
    return dict(root=str(root), backup=str(backup), checkpoint_step=step)


def test_pair_preserves_full_cohort_and_reports_extra_voxels_without_spatial_guess():
    a, _ = native()
    b, _ = native(extra=30)
    result = paired_errors(a, b, IDS, positive_cases=2)
    assert len(result['cases']) == 4
    assert result['cases'][0]['false_positive_voxel_delta'] == 30
    assert result['cases'][0]['false_negative_voxel_delta'] == 0
    assert result['cases'][2]['dice_delta'] is None
    assert result['confidence_intervals'] is result['hypothesis_decision'] is result['practical_decision'] is None
    assert 'not_inferred' in result['spatial_error_categories']


@pytest.mark.parametrize('changed', ['step', 'scope', 'target'])
def test_mismatched_pair_rejected(changed):
    a, _ = native()
    b, _ = native(4000 if changed == 'step' else 2000)
    if changed == 'scope':
        b['scope'] = 'native_development_provided_pancreas'
        for r in b['cases']: r['scope'] = b['scope']
    if changed == 'target': b['cases'][0]['metrics']['reference_components'] = 2
    with pytest.raises(ValueError): paired_errors(a, b, IDS, positive_cases=2)


def test_only_kd_weight_can_change_and_horizon_is_fixed():
    control = dict(distillation=dict(max_weight=0, temperature=2), evaluation=dict(steps=STEPS,
        terminal_required=True, selection='max_positive_patient_macro_native_Dice_earliest_tie'),
        student_configuration=dict(_experiment=dict(run=dict(checkpoint_every=500, max_updates=24000, validate_every=2000))))
    treatment = deepcopy(control);treatment['distillation']['max_weight'] = .1
    assert matching_designs([control, treatment])['changed_factor'] == 'auxiliary_teacher_loss_only'
    treatment['distillation']['temperature'] = 3
    with pytest.raises(ValueError): matching_designs([control, treatment])
    treatment = deepcopy(control);treatment['distillation']['max_weight'] = .1
    control['evaluation']['steps'] = treatment['evaluation']['steps'] = [2000]
    with pytest.raises(ValueError): matching_designs([control, treatment])


def test_pending_partial_journal_and_append_only_prefix(tmp_path):
    p = tmp_path/'history.jsonl'
    p.write_bytes(b'{"event":"started","step":0,"identity":{}}\n{"event":"update","step":1}\n{"event":')
    reader = MetadataReader();snap = reader.journal(p)
    assert snap['last_update'] == 1 and not snap['completed']
    with p.open('ab') as f: f.write(b'"update","step":2}\n')
    reader.verify()  # Prefix intact despite append; no pin to live file length.
    p.write_bytes(p.read_bytes().replace(b'"step":1', b'"step":9'))
    with pytest.raises(ValueError, match='prefix changed'): reader.verify()


def test_noncontiguous_journal_and_nonfinite_or_duplicate_json_fail(tmp_path):
    p = tmp_path/'history.jsonl'
    p.write_text('{"event":"started","step":0,"identity":{}}\n{"event":"update","step":2}\n')
    with pytest.raises(ValueError, match='Noncontiguous'): MetadataReader().journal(p)
    for raw in ('{"a":NaN}', '{"a":1e999}', '{"a":1,"a":2}'):
        with pytest.raises(ValueError): strict_json(raw)


def test_completed_series_requires_backup_and_exact_component_binding(tmp_path):
    loc = location(tmp_path)
    result = collect_series(MetadataReader(), [loc], 'treatment', IDS, positive_cases=2)
    assert list(result['reports']) == [2000]
    p = tmp_path/'run-backup/treatment/native-002000-components.json'
    p.write_text('{}')
    with pytest.raises(ValueError, match='SHA256'): collect_series(MetadataReader(), [loc], 'treatment', IDS, positive_cases=2)


def test_native_file_without_completed_event_is_not_admitted(tmp_path):
    loc = location(tmp_path)
    p = tmp_path/'run/treatment/execution/history.jsonl'
    p.write_text(p.read_text().splitlines()[0]+'\n')
    assert not collect_series(MetadataReader(), [loc], 'treatment', IDS, positive_cases=2)['reports']


def test_duplicate_segment_and_conflicting_replay_are_rejected(tmp_path):
    a = location(tmp_path)
    b = location(tmp_path, extra=5, root_name='other')
    with pytest.raises(ValueError, match='Duplicate lineage'): collect_series(MetadataReader(), [a, a], 'treatment', IDS, positive_cases=2)
    with pytest.raises(ValueError, match='Conflicting'): collect_series(MetadataReader(), [a, b], 'treatment', IDS, positive_cases=2)


def test_gap_between_continuation_checkpoints_is_rejected(tmp_path):
    a = location(tmp_path)
    b = location(tmp_path, step=4000, root_name='next')
    with pytest.raises(ValueError, match='checkpoint boundary'):
        collect_series(MetadataReader(), [a, b], 'treatment', IDS, positive_cases=2)


def test_embedded_sidecar_disagreement_is_rejected():
    report, sidecar = native()
    sidecar['cases'][0] = deepcopy(sidecar['cases'][0]);sidecar['cases'][0]['target_sha256'] = 'f'*64
    with pytest.raises(ValueError, match='Embedded/sidecar'):
        reference_signature(report, sidecar, sidecar['report_sha256'], IDS, 2)


def test_reader_refuses_images_checkpoints_and_changed_json(tmp_path):
    reader = MetadataReader()
    for name in ['scan.nii.gz', 'model.pt']:
        with pytest.raises(ValueError, match='JSON metadata'): reader.read(tmp_path/name)
    path = tmp_path/'value.json';write(path, dict(a=1));reader.read(path)
    write(path, dict(a=2))
    with pytest.raises(ValueError, match='Input metadata changed'): reader.verify()


def test_actual_cli_contract_partial_horizon_and_full_cohort(tmp_path):
    """Synthetic producer records exercise the real recipe/lineage/backup reader."""
    from src.operations.kd_error_review_preparation_v1 import sha_bytes
    original, current, control_root = tmp_path/'original', tmp_path/'current', tmp_path/'control-run'
    control_backup, treatment_backup = tmp_path/'control-backup', tmp_path/'treatment-backup'
    cohort = ['case-'+str(i) for i in range(70)]
    provider = dict(train=['training-'+str(i) for i in range(1333)], validation=cohort)
    pp = original/'admission/provider-control.json';write(pp, provider);provider_pin=sha_bytes(pp.read_bytes())
    design = dict(provider_sha256=provider_pin, distillation=dict(max_weight=0), evaluation=dict(steps=STEPS,
        terminal_required=True, selection='max_positive_patient_macro_native_Dice_earliest_tie'),
        student_configuration=dict(_experiment=dict(run=dict(checkpoint_every=500, max_updates=24000, validate_every=2000))))
    kd = deepcopy(design);kd['distillation']['max_weight'] = .1
    scientific = dict(designs=[design, kd], preparation=dict(admitted_targets=str(pp.parent), pins={str(pp):provider_pin}))
    write(original/'ready.json', scientific)
    for arm, root, backup, terminal in [('control', control_root, control_backup, 24000), ('treatment', current, treatment_backup, 14000)]:
        ex = root/arm/'execution';ex.mkdir(parents=True)
        with (ex/'history.jsonl').open('w') as stream:
            stream.write(json.dumps(dict(event='started', step=0, identity=dict(model='fixed')))+'\n')
            for step in range(1, terminal+1):
                stream.write(json.dumps(dict(event='update', step=step))+'\n')
                if step % 2000: continue
                sample, _ = native(step)
                rows = []
                for i, name in enumerate(cohort):
                    row = deepcopy(sample['cases'][0 if i < 36 else 2]);row['case_id'] = name
                    row['component_evidence']['case_id'] = name;rows.append(row)
                report = dict(step=step, scope=REGION_SCOPE, cases=rows, lesion_positive_macro_dice=80/220)
                raw = json.dumps(report).encode()
                side = dict(version='native-components-1', matching=POLICY['component_matching'],
                            report_sha256=sha_bytes(raw), cases=[r['component_evidence'] for r in rows])
                for base in (ex, backup/arm):
                    write(base/f'native-{step:06d}.json', report)
                    write(base/f'native-{step:06d}-components.json', side)
                stream.write(json.dumps(dict(event='native_completed', step=step, lesion_positive_macro_dice=80/220))+'\n')
    result = dict(completed_updates=24000, completed=True)
    resources = dict(success=False, workers_reaped=False, error="ValueError('Owned worker descendant was not reaped')")
    write(control_root/'control/result.json', result);write(control_backup/'control/result.json', result)
    write(control_root/'control/resources.json', resources)
    receipt = dict(version='mac-kd-treatment-resume-3', automatic_retry=False, scientific=scientific,
        original=str(original), original_sha256=sha_bytes((original/'ready.json').read_bytes()), backup=str(treatment_backup),
        segments=dict(control=[dict(root=str(control_root), backup=str(control_backup), checkpoint_step=24000)], treatment=[]),
        control_closeout=dict(version='reviewed-control-closeout-1', optimization_complete=True, result=result, resources=resources))
    write(current/'ready.json', receipt);pin=sha_bytes((current/'ready.json').read_bytes())
    out = tmp_path/'review'
    report = prepare(current, pin, out)
    assert report['completed_native_steps']['control'] == STEPS
    assert report['missing_native_steps']['treatment'] == [16000,18000,20000,22000,24000]
    assert report['endpoints_if_full_series']['control'] == dict(selected_step=2000, terminal_step=24000)
    assert len(report['latest_matched']['cases']) == 70
    assert report['latest_matched']['step'] == 14000
    assert report['historical_control_supervision_success'] is False
    assert report['final_comparison_authorized'] is False and report['hypothesis_decision'] is None
    assert json.loads((out/'preparation.json').read_text())['practical_decision'] is None
    with pytest.raises(ValueError, match='Fresh'): prepare(current, pin, out)
    with pytest.raises(ValueError, match='SHA256'): prepare(current, '0'*64, tmp_path/'bad')
    assert not (tmp_path/'bad').exists()
