"""Invented private-format cases only; no actual protected content is read or authored."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from src.retrieval.private_evaluation import (validate_private,seal_authored,private_path,
    write_private_result,PrivateValidationError)
from src.retrieval.direct_ingestion import source_bundle
from src.retrieval.corpus_inventory import frozen_inventory
from tests.retrieval.test_development_set import fixture
from tests.retrieval.test_direct_ingestion import bundle,XML,batch


@pytest.fixture
def private_fixture(fixture,tmp_path):
    old,_,bundles,batches=deepcopy(fixture)
    p=tmp_path/'second.xml';p.write_text(XML.replace('123','124'))
    second=source_bundle(p);bundles.append(second);batches.append(batch(second))
    suite=old;suite.pop('baseline_regression_sha256')
    bindings=dict(corpus_manifest_sha256='a'*64,corpus_content_sha256=frozen_inventory(batches)['content_sha256'],
        final_development_content_sha256='b'*64,public_exposure_manifest_sha256='c'*64,
        information_needs_sha256='d'*64,information_needs_base_sha256='e'*64)
    suite.update(bindings,schema_version='prowl-private-evaluation-v1',status='ready_for_private_validation',
        cross_split_near_duplicate_review_complete=True,regression_exposure_review_complete=True,
        source_concentration_review_complete=True)
    for i,c in enumerate(suite['cases']):
        c['id']=f'q:heldout-{i+1:02}';c['labels']['question_id']=c['id'];c['split']='held_out'
        c['authorship'].update(author='Quinton Evans',exposed=False)
        c['review']=dict(reviewer='Quinton Evans',reviewed_at='2026-10-17T23:00:00Z',human_adjudication='complete',second_consistency='complete',notes='Invented test assertion, not human review.')
        c['difficulty']=['easy','paraphrase','multi_passage','limiting'][i%4]
        if i<20:
            chosen=bundles[i%2];rep=chosen['representation']
            for span in c['labels']['spans']:
                span.update(representation_id=rep['representation_id'],representation_sha256=rep['text_sha256'])
            c['source_judgments']=[dict(work_id=b['work']['work_id'],grade='direct' if b is chosen else 'not_relevant',rationale='Invented.') for b in bundles]
    return seal_authored(suite),dict(inventory=frozen_inventory(batches)),bundles,batches,bindings


def check(data,**kw):
    s,m,bs,batches,bindings=data
    return validate_private(s,m,bs,batches,bindings=bindings,exposed_questions=kw.get('questions',[]),exposed_intents=kw.get('intents',set()))


def test_valid_invented_set_proves_only_mechanics(private_fixture):
    report=check(private_fixture)
    assert report['question_count']==30 and report['maximum_single_gold_source_question_count']==10
    assert not report['ready_for_tuning'] and not report['backup_verified']
    assert not report['protected_storage_verified']
    assert 'cases' not in report and 'gold_works' not in report


@pytest.mark.parametrize('mutate',[
    lambda s:s['cases'][0]['authorship'].update(author='Codex'),
    lambda s:s['cases'][0]['authorship'].update(exposed=True),
    lambda s:s['cases'][0].update(split='development'),
    lambda s:s['cases'][0]['finding'].update(patient_id='SECRET_CANARY'),
    lambda s:s['cases'][0]['review'].update(second_consistency='pending'),
    lambda s:s['cases'][0]['review'].update(reviewed_at='invalid'),
    lambda s:s.update(cross_split_near_duplicate_review_complete=False),
    lambda s:s.update(corpus_content_sha256='f'*64),
    lambda s:s['cases'][0]['labels']['spans'][0].update(representation_sha256='f'*64),
    lambda s:s['cases'][0]['labels']['spans'][0].update(end=999999),
    lambda s:s['cases'][0]['labels']['spans'][0].update(grade='uncertain'),
    lambda s:s['cases'][0]['labels']['spans'][0].update(concept_ids=[]),
    lambda s:s['cases'][0]['labels'].update(question_id='q:wrong'),
    lambda s:s['cases'][0].update(source_judgments=[]),
    lambda s:s['cases'][0]['expected'].update(reason='RF1_diagnosis'),
    lambda s:s['cases'][0].update(family='review'),
    lambda s:s['cases'][0].update(question=s['cases'][1]['question']),
    lambda s:s['cases'][0].update(intent_group=s['cases'][1]['intent_group']),
    lambda s:s['cases'][20].update(source_judgments=[dict(work_id='work:foreign',grade='not_relevant',rationale='SECRET_CANARY')]),
])
def test_bad_private_records_refused_without_content_echo(private_fixture,mutate):
    s,*rest=deepcopy(private_fixture);mutate(s);s=seal_authored(s)
    with pytest.raises(PrivateValidationError) as err:check((s,*rest))
    assert 'SECRET_CANARY' not in str(err.value)


def test_hashes_do_not_silently_repair_in_validate(private_fixture):
    s,*rest=deepcopy(private_fixture);s['cases'][0]['question']='Changed SECRET_CANARY'
    with pytest.raises(PrivateValidationError,match='hash mismatch'):check((s,*rest))
    before=deepcopy(s);sealed=seal_authored(s);assert s==before
    assert sealed['cases'][0]['question']==s['cases'][0]['question']


def test_exact_exposure_and_intent_collision(private_fixture):
    s=private_fixture[0]
    with pytest.raises(PrivateValidationError,match='exposed'):check(private_fixture,questions=[s['cases'][0]['question'].upper()])
    with pytest.raises(PrivateValidationError,match='exposed'):check(private_fixture,intents={s['cases'][0]['intent_group']})


def test_partial_overlap_is_not_direct(private_fixture):
    s,*rest=deepcopy(private_fixture);s['cases'][0]['labels']['spans'][0]['end']+=1
    with pytest.raises(PrivateValidationError,match='fully contained'):check((seal_authored(s),*rest))


def test_difficulty_balance_enforced(private_fixture):
    s,*rest=deepcopy(private_fixture)
    for c in s['cases']:c['difficulty']='easy'
    with pytest.raises(PrivateValidationError,match='difficulty'):check((seal_authored(s),*rest))


def test_sole_source_concentration_enforced(private_fixture):
    s,m,bs,batches,bindings=deepcopy(private_fixture);rep=bs[0]['representation']
    c=s['cases'][1]
    for v in c['labels']['spans']:v.update(representation_id=rep['representation_id'],representation_sha256=rep['text_sha256'])
    for j in c['source_judgments']:j['grade']='direct' if j['work_id']==bs[0]['work']['work_id'] else 'not_relevant'
    with pytest.raises(PrivateValidationError,match='half'):check((seal_authored(s),m,bs,batches,bindings))


def test_private_path_refuses_repo_symlink_and_large_file(tmp_path):
    repo=tmp_path/'repo';repo.mkdir();p=repo/'private.json';p.write_text('{}')
    with pytest.raises(PrivateValidationError):private_path(p,repo)
    outside=tmp_path/'invented.json';outside.write_text('{}')
    assert private_path(outside,repo)==outside
    symlink=tmp_path/'link.json';symlink.symlink_to(outside)
    with pytest.raises(PrivateValidationError):private_path(symlink,repo)
    outside.write_bytes(b' '*(2*1024**2+1))
    with pytest.raises(PrivateValidationError):private_path(outside,repo)


def test_private_outputs_exclusive_and_owner_only(tmp_path):
    out=tmp_path/'invented-result';write_private_result(out,{'invented':True},{'mechanical':True})
    assert out.stat().st_mode & 0o777==0o700
    assert (out/'validated-set.json').stat().st_mode & 0o777==0o600
    with pytest.raises(FileExistsError):write_private_result(out,{}, {})
    assert json.loads((out/'validated-set.json').read_text())=={'invented':True}


def test_public_development_validator_still_refuses_private_format(private_fixture):
    from src.retrieval.development_set import validate_draft
    with pytest.raises(ValueError,match='Unsupported development'):
        validate_draft(*private_fixture[:4],manifest_sha256='a'*64,regression_sha256='b'*64)
