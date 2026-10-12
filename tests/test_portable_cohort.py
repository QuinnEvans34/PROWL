"""Protected consumer tests use invented metadata, never patient payloads/models."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import pytest
from src.data import protected_identity as identities
from src.data import portable_cohort as P
from src.inference.fixed_cohort_evaluation import validate_plan, run_predictions, score_predictions, prediction_request


def fixture(tmp_path, monkeypatch):
    bases = {'train': 'PanTS_00000001\n', 'validation': 'PanTS_00000002\n', 'test': 'PanTS_00009001\n'}
    monkeypatch.setattr(identities, 'BASE_INPUTS', {r: (1, P.digest(v.encode())) for r, v in bases.items()})
    members = []
    for role in ('train', 'validation'):
        name = bases[role].strip()
        members.append(dict(case_id=name, role=role, identity=asdict(identities.pants_identity(name)),
                            reference_state='positive', files={k: dict(root_alias='pants_source', uri=f'{name}/{k}.nii.gz',
                                                                       sha256='a'*64) for k in P.KINDS}))
    package = dict(version=P.VERSION, cohort_id='pants-admitted-development-v1', review_sha256='b'*64,
                   provenance={}, bases=bases, members=members, limitations=['fixture'])
    roots = {'pants_source': str(tmp_path / 'source')}
    binding = dict(package=package, sha256=P.digest(P.canonical(package)), current_review_sha256='b'*64, roots=roots)
    plan = dict(version=2, cohort_id=package['cohort_id'], cohort_binding=binding,
                cases=P.resolve_cases(package, roots, expected_sha256=binding['sha256'], current_review_sha256='b'*64),
                inference=dict(models={r: dict(path=str(tmp_path/r), sha256='c'*64) for r in ('localizer', 'segmenter')},
                               localizer_recipe={}, patch_size=[16]*3, tensor_shape=[16]*3, device='cpu'),
                limits=dict(seconds_per_case=10, total_seconds=20, rss_bytes=1000000, free_floor_bytes=1),
                limitations=['fixture'])
    return plan


def test_root_change_preserves_package_content_and_worker_boundary(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch); other = deepcopy(plan)
    other['cohort_binding']['roots']['pants_source'] = str(tmp_path/'other')
    binding = other['cohort_binding']
    other['cases'] = P.resolve_cases(binding['package'], binding['roots'], expected_sha256=binding['sha256'], current_review_sha256='b'*64)
    validate_plan(plan); validate_plan(other)
    assert plan['cohort_binding']['sha256'] == other['cohort_binding']['sha256']
    assert plan['cases'][0]['ct']['path'] != other['cases'][0]['ct']['path']
    request = prediction_request(other, other['cases'][0], tmp_path/'out')
    assert 'cohort_binding' not in request and 'references' not in request


@pytest.mark.parametrize('fault', ['case', 'ct', 'reference', 'state', 'omitted', 'duplicate', 'review', 'package', 'root'])
def test_consumer_rejects_changed_binding_before_output_or_worker(tmp_path, monkeypatch, fault):
    plan = fixture(tmp_path, monkeypatch)
    if fault == 'case': plan['cases'][0]['case_id'] = 'PanTS_00000001'
    if fault == 'ct': plan['cases'][0]['ct']['sha256'] = 'd'*64
    if fault == 'reference': del plan['cases'][0]['references']['lesion']
    if fault == 'state': plan['cases'][0]['reference_state'] = 'reference_empty'
    if fault == 'omitted': plan['cases'] = []
    if fault == 'duplicate': plan['cases'] *= 2
    if fault == 'review': plan['cohort_binding']['current_review_sha256'] = 'd'*64
    if fault == 'package': plan['cohort_binding']['package']['limitations'] = []
    if fault == 'root': plan['cohort_binding']['roots']['pants_source'] = 'relative'
    with pytest.raises((ValueError, KeyError)):
        run_predictions(plan, 'd'*64, tmp_path/'out', lambda *a: pytest.fail('Worker must not start'))
    assert not (tmp_path/'out').exists()
    with pytest.raises((ValueError, KeyError)):
        score_predictions(plan, 'd'*64, tmp_path/'missing-journal')


@pytest.mark.parametrize('fault', ['wrong_role', 'test', 'duplicate', 'assurance', 'traversal', 'missing_label'])
def test_rehashed_bad_package_still_fails_semantic_guards(tmp_path, monkeypatch, fault):
    plan = fixture(tmp_path, monkeypatch); b = plan['cohort_binding']; p = b['package']
    m = p['members'][1]
    if fault == 'wrong_role': m['role'] = 'train'
    if fault == 'test':
        m['case_id'] = 'PanTS_00009001'; m['identity'] = asdict(identities.pants_identity(m['case_id']))
    if fault == 'duplicate': p['members'].append(deepcopy(m))
    if fault == 'assurance': m['identity']['identity_assurance'] = 'verified'
    if fault == 'traversal': m['files']['ct']['uri'] = '../escape'
    if fault == 'missing_label': del m['files']['lesion']
    with pytest.raises(ValueError): P.validate(p, expected_sha256=P.digest(P.canonical(p)), current_review_sha256='b'*64)


def test_symlink_escape_refused(tmp_path, monkeypatch):
    plan=fixture(tmp_path,monkeypatch);b=plan['cohort_binding'];root=Path(b['roots']['pants_source']);root.mkdir()
    (root/'PanTS_00000002').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError,match='escapes'): validate_plan(plan)


def test_valid_plan_reaches_existing_runner_and_accounts_for_failure(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch); calls=[]
    def worker(request, *args):
        value=json.loads(request.read_text());calls.append(value)
        assert 'references' not in value and 'cohort_binding' not in value
        raise ValueError('Invented unavailable input')
    journal=run_predictions(plan, 'e'*64, tmp_path/'out', worker)
    assert len(calls)==1
    assert json.loads(journal.read_text())['case_id']=='PanTS_00000002'
    assert json.loads(journal.read_text())['status']=='failed'


def build_fixture(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch); package=plan['cohort_binding']['package']
    def write(name, raw):
        path=tmp_path/name;path.write_bytes(raw);return path
    paths={key:write(key,package['bases'][role].encode()) for key,role in
           [('original_train_ids','train'),('original_development_ids','validation'),('test_ids','test')]}
    paths.update({key:write(key,package['bases'][role].encode()) for key,role in [('train_ids','train'),('development_ids','validation')]})
    text='case_id,protected_role,ct_path,pancreas_path,lesion_path\n'
    for m in package['members']:
        text+=','.join([m['case_id'],m['role'],*[f'/source/{m["case_id"]}/{k}.nii.gz' for k in P.KINDS]])+'\n'
    paths['manifest']=write('manifest',text.encode())
    control=write('control.json',P.canonical(dict(manifest_sha256=P.digest(text.encode()))))
    metadata={}
    for m in package['members']:
        meta=dict(case_id=m['case_id'],control_sha256=P.digest(control.read_bytes()),
                  fidelity=dict(mechanical_survival_pass=True,lesion_target_state='positive'),
                  source_sha256={k:'a'*64 for k in P.KINDS})
        path=write(m['case_id']+'.json',P.canonical(meta));metadata[m['case_id']]=dict(metadata_sha256=P.digest(path.read_bytes()))
    review=dict(decision='accepted',scope='development_experiment_using_published_reference_annotations',
                empty_reference_policy='annotation_background_not_verified_healthy',
                input_sha256={k:P.digest(v.read_bytes()) for k,v in paths.items()},
                target_states={m['case_id']:'positive' for m in package['members']},
                prepared_cache=dict(control_sha256=P.digest(control.read_bytes()),members=metadata))
    path=write('review.json',P.canonical(review))
    return dict(review_path=path,review_sha256=P.digest(path.read_bytes()),source_root='/source',cache_root=tmp_path,**paths)


def test_repeated_build_and_metadata_tamper(tmp_path, monkeypatch):
    args=build_fixture(tmp_path,monkeypatch)
    first=P.canonical(P.build(**args));second=P.canonical(P.build(**args));assert first==second
    assert b'/source' not in first
    meta=tmp_path/'PanTS_00000002.json';meta.write_bytes(meta.read_bytes()+b' ')
    with pytest.raises(ValueError,match='checksum'):P.build(**args)


def test_manifest_drift_refused_without_opening_payload(tmp_path,monkeypatch):
    args=build_fixture(tmp_path,monkeypatch)
    args['manifest'].write_text(args['manifest'].read_text().replace('validation','train'))
    with pytest.raises(ValueError,match='checksum'):P.build(**args)


def test_pinned_development_spelling_retains_original_validation_role(tmp_path,monkeypatch):
    args=build_fixture(tmp_path,monkeypatch)
    manifest=args['manifest'];manifest.write_text(manifest.read_text().replace('validation','development'))
    control=tmp_path/'control.json';control.write_bytes(P.canonical(dict(manifest_sha256=P.digest(manifest.read_bytes()))))
    review=json.loads(args['review_path'].read_text())
    review['input_sha256']['manifest']=P.digest(manifest.read_bytes())
    review['prepared_cache']['control_sha256']=P.digest(control.read_bytes())
    for name,item in review['prepared_cache']['members'].items():
        path=tmp_path/(name+'.json');meta=json.loads(path.read_text());meta['control_sha256']=P.digest(control.read_bytes())
        path.write_bytes(P.canonical(meta));item['metadata_sha256']=P.digest(path.read_bytes())
    args['review_path'].write_bytes(P.canonical(review));args['review_sha256']=P.digest(args['review_path'].read_bytes())
    result=P.build(**args)
    assert [m['role'] for m in result['members']]==['train','validation']
