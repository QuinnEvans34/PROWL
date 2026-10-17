"""Draft controls with invented source text; no providers, real corpus or protected data."""
from copy import deepcopy
import pytest
from src.retrieval.direct_ingestion import digest
from src.retrieval.corpus_inventory import frozen_inventory
from src.retrieval.development_set import checked_json, development_path, validate_draft
from src.retrieval.labels import make_label_set
from tests.retrieval.test_direct_ingestion import bundle, batch


def seal(s):
    for c in s['cases']:
        c.pop('content_sha256',None);c['content_sha256']=digest(c)
    s.pop('content_sha256',None);s['content_sha256']=digest(s)
    return s


@pytest.fixture
def fixture(bundle):
    b=batch(bundle);rep=bundle['representation'];p=b['items'][0]['record']['passage']
    families=['appearance','measurement','anatomy','ai_limits','review'];cases=[]
    for i in range(30):
        q=f'q:dev2-{i+1:02}';ans=i<20;concept=f'c:invented-{i}'
        spans=[dict(representation_id=rep['representation_id'],representation_sha256=rep['text_sha256'],
            start=p['start'],end=p['end'],grade='direct',concept_ids=[concept])] if ans else []
        cases.append(dict(id=q,version=1,split='development',primary_need=f'N{i%5+1}.1',family=families[i%5],
            difficulty='easy',intent_group=f'invented-{i}',question=f'Invented question number {i}?',
            finding=dict(modality='CT',anatomy='pancreas',task='review',finding_state='candidate'),
            authorship=dict(author='Codex',basis='literature_inspection',exposed=True),
            expected=dict(status='answered' if ans else 'insufficient_evidence',reason='supported' if ans else 'missing_evidence',boundary='Invented contract only.'),
            concepts=[dict(id=concept,description='Invented concept.')] if ans else [],
            labels=make_label_set(question_id=q,label_version='invented-v1',answerable=ans,required_concepts=[concept] if ans else [],spans=spans),
            source_judgments=[dict(work_id=bundle['work']['work_id'],grade='direct',rationale='Invented fixture.')] if ans else [],
            review=dict(agent_first_pass='complete',agent_second_pass='complete',human_adjudication='pending',notes='Not human reviewed.')))
    s=seal(dict(schema_version='prowl-development-draft-v1',status='draft_pending_human_review',
        corpus_manifest_sha256='a'*64,corpus_content_sha256=frozen_inventory([b])['content_sha256'],
        baseline_regression_sha256='b'*64,authorship='Invented fixture.',review_scope='Contract only.',cases=cases))
    return s,dict(inventory=frozen_inventory([b])),[bundle],[b]


def check(f):
    return validate_draft(*f,manifest_sha256='a'*64,regression_sha256='b'*64)


def test_valid_draft_is_not_a_tuning_release(fixture):
    r=check(fixture)
    assert r['counts']=={'answered':20,'insufficient_evidence':10}
    assert r['source_recall_at_5_ceiling']==1.0
    assert len(r['human_review_pending'])==30
    assert r['ready_for_tuning'] is False and len(r['blockers'])==2


@pytest.mark.parametrize('change',[
    lambda s:s.update(status='frozen'),
    lambda s:s['cases'][0].update(split='held_out'),
    lambda s:s['cases'][0]['review'].update(human_adjudication='approved'),
    lambda s:s['cases'][0]['finding'].update(patient_id='invented-private'),
    lambda s:s['cases'][0].update(question=s['cases'][1]['question']),
    lambda s:s['cases'][0].update(family='review'),
    lambda s:s['cases'][0]['labels'].update(question_id='q:wrong'),
    lambda s:s['cases'][0]['labels']['spans'][0].update(representation_sha256='f'*64),
    lambda s:s['cases'][0]['labels']['spans'][0].update(grade='uncertain'),
    lambda s:s['cases'][0]['labels']['spans'][0].update(concept_ids=[]),
    lambda s:s['cases'][0]['expected'].update(status='insufficient_evidence'),
    lambda s:s['cases'][0]['source_judgments'][0].update(grade='not_relevant'),
    lambda s:s.update(corpus_manifest_sha256='c'*64),
    lambda s:s.update(baseline_regression_sha256='c'*64),
])
def test_tampering_refused_even_after_rehash(fixture,change):
    s,*rest=deepcopy(fixture);change(s);seal(s)
    with pytest.raises(ValueError):check((s,*rest))


def test_json_schema_errors_are_failures(fixture):
    s,*rest=deepcopy(fixture);s['cases'][0]['finding']['secret']='invented';seal(s)
    with pytest.raises(ValueError,match='^Draft schema violation$'):check((s,*rest))


def test_partial_overlap_never_counts_as_direct_support(fixture):
    s,m,bs,batches=deepcopy(fixture)
    s['cases'][0]['labels']['spans'][0]['end']+=3
    seal(s)
    with pytest.raises(ValueError,match='completely contained'):check((s,m,bs,batches))


def test_missing_concept_and_stale_question_hash_refused(fixture):
    s,*rest=deepcopy(fixture)
    s['cases'][0]['question']='Different wording'
    with pytest.raises(ValueError,match='hash mismatch'):check((s,*rest))
    seal(s)
    s['cases'][0]['concepts'].append(dict(id='c:missing',description='No source support.'))
    s['cases'][0]['labels']['required_concepts'].append('c:missing');seal(s)
    with pytest.raises(ValueError,match='Every concept'):check((s,*rest))


def test_pinned_input_hash_and_repository_boundary(tmp_path):
    from src.retrieval.records import sha256_hex
    path=tmp_path/'input.json';path.write_bytes(b'{"invented":true}')
    pin=dict(path='input.json',sha256=sha256_hex(path.read_bytes()))
    assert checked_json(pin,tmp_path)=={'invented':True}
    path.write_bytes(b'{"invented":false}')
    with pytest.raises(ValueError,match='hash mismatch'):checked_json(pin,tmp_path)
    with pytest.raises(ValueError,match='repository-local'):
        checked_json(dict(path='../outside.json',sha256='a'*64),tmp_path)


def test_actual_corpus_missing_batch_refused(fixture):
    s,m,bs,batches=deepcopy(fixture)
    with pytest.raises(ValueError):check((s,m,bs,[]))


def test_external_question_path_refused_before_open(tmp_path):
    # No file exists: refusal must happen without opening content.
    with pytest.raises(ValueError,match='repository development'):
        development_path(tmp_path/'private/development-secret.json',tmp_path)


def test_question_symlink_escape_and_heldout_name_refused(tmp_path):
    folder=tmp_path/'configs/evidence/evaluation';folder.mkdir(parents=True)
    path=folder/'development-invented.json';path.symlink_to(tmp_path/'private.json')
    with pytest.raises(ValueError,match='repository development'):
        development_path(path,tmp_path)
    with pytest.raises(ValueError,match='repository development'):
        development_path(folder/'heldout.json',tmp_path)


def revised_fixture(fixture):
    s, *rest = deepcopy(fixture)
    s['schema_version'] = 'prowl-development-draft-v2'
    s['information_needs_sha256'] = 'c' * 64
    s['information_needs_base_sha256'] = 'e' * 64
    s['cases'][0]['version'] = 2
    s['cases'][0]['question'] = 'Revised invented wording?'
    seal(s)
    return s, *rest


def test_v2_revision_requires_matching_needs_pin_and_stays_draft(fixture):
    f = revised_fixture(fixture)
    r = validate_draft(*f, manifest_sha256='a'*64, regression_sha256='b'*64,
                       information_needs_sha256='c'*64, information_needs_base_sha256='e'*64)
    assert r['ready_for_tuning'] is False
    assert len(r['human_review_pending']) == 30
    for pin in (None, 'd'*64):
        with pytest.raises(ValueError, match='information-needs binding mismatch'):
            validate_draft(*f, manifest_sha256='a'*64, regression_sha256='b'*64,
                           information_needs_sha256=pin, information_needs_base_sha256='e'*64)


@pytest.mark.parametrize('version', [0, -1, True, '2'])
def test_v2_rejects_invalid_question_versions(fixture, version):
    s, *rest = revised_fixture(fixture)
    s['cases'][0]['version'] = version
    seal(s)
    with pytest.raises(ValueError, match='Draft schema violation'):
        validate_draft(s, *rest, manifest_sha256='a'*64, regression_sha256='b'*64,
                       information_needs_sha256='c'*64, information_needs_base_sha256='e'*64)


@pytest.mark.parametrize('change', [
    lambda s: s.update(status='frozen'),
    lambda s: s['cases'][0].update(split='held_out'),
    lambda s: s['cases'][0]['review'].update(human_adjudication='approved'),
    lambda s: s['cases'][0]['finding'].update(patient_id='invented'),
])
def test_v2_does_not_relax_privacy_or_release_guards(fixture, change):
    s, *rest = revised_fixture(fixture)
    change(s); seal(s)
    with pytest.raises(ValueError, match='Draft schema violation'):
        validate_draft(s, *rest, manifest_sha256='a'*64, regression_sha256='b'*64,
                       information_needs_sha256='c'*64, information_needs_base_sha256='e'*64)


def test_v1_remains_closed_and_unknown_schema_rejected(fixture):
    s, *rest = deepcopy(fixture)
    s['cases'][0]['version'] = 2
    seal(s)
    with pytest.raises(ValueError, match='Draft schema violation'):
        check((s, *rest))
    for version in ('prowl-heldout-v2', '../../private', ['invalid']):
        s['schema_version'] = version
        seal(s)
        with pytest.raises(ValueError, match='Unsupported development draft schema'):
            check((s, *rest))


def test_v2_rejects_changed_or_missing_inherited_needs(fixture):
    f = revised_fixture(fixture)
    for pin in (None, 'f'*64):
        with pytest.raises(ValueError, match='information-needs binding mismatch'):
            validate_draft(*f, manifest_sha256='a'*64, regression_sha256='b'*64,
                           information_needs_sha256='c'*64,
                           information_needs_base_sha256=pin)
