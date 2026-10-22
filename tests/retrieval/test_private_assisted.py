"""Invented payloads only; never inspect QUESTIONS.md or protected inputs."""
from copy import deepcopy
import json
import pytest
from src.retrieval.private_evaluation import (seal_authored, validate_private,
    prepare_assisted_quotes, PrivateValidationError)
from tests.retrieval.test_private_evaluation import private_fixture, check
from tests.retrieval.test_development_set import fixture
from tests.retrieval.test_direct_ingestion import bundle


@pytest.fixture
def assisted(private_fixture):
    suite,m,bs,batches,bindings=deepcopy(private_fixture)
    human=dict(kind='human',identity='Quinton Evans',model_version='not_applicable')
    ai=dict(kind='ai_assistant',identity='Invented separate assistant',model_version='unknown')
    suite.update(schema_version='prowl-private-evaluation-v2',source_draft_sha256='1'*64,
        reviewed_draft_sha256='1'*64,candidate_freeze_sha256='2'*64,
        roles=dict(question_author=ai,label_preparer=deepcopy(ai),semantic_reviewer=human,
            consistency_reviewer=deepcopy(human),private_operator=deepcopy(human)))
    bindings['candidate_freeze_sha256']='2'*64
    for c in suite['cases']:
        c['authorship'].update(author='question_author',basis='separate_ai_draft_human_reviewed')
    return seal_authored(suite),m,bs,batches,bindings


def test_ai_authorship_is_truthful_and_not_execution_admission(assisted):
    report=check(assisted)
    assert report['ai_assisted'] and report['question_count']==30
    assert not report['backup_verified'] and not report['protected_storage_verified']
    assert not report['ready_for_tuning']


@pytest.mark.parametrize('change',['human_author','ai_reviewer','draft','freeze','binding','human_version','basis','uncertain','exposure'])
def test_bad_roles_and_unresolved_evidence_refused(assisted,change):
    s,m,bs,batches,b=deepcopy(assisted)
    if change=='human_author':s['cases'][0]['authorship']['author']='Quinton Evans'
    if change=='ai_reviewer':s['roles']['semantic_reviewer']['kind']='ai_assistant'
    if change=='draft':s['reviewed_draft_sha256']='3'*64
    if change=='freeze':s['candidate_freeze_sha256']='3'*64
    if change=='binding':b.pop('candidate_freeze_sha256')
    if change=='human_version':s['roles']['private_operator']['model_version']='SECRET_CANARY'
    if change=='basis':s['cases'][0]['authorship']['basis']='literature_inspection'
    if change=='uncertain':s['cases'][0]['labels']['spans'][0]['grade']='uncertain'
    if change=='exposure':s['cases'][0]['authorship']['exposed']=True
    with pytest.raises(PrivateValidationError) as e:check((seal_authored(s),m,bs,batches,b))
    assert 'SECRET_CANARY' not in str(e.value)


def transcription(suite,bundles,batches):
    result=deepcopy(suite)
    reps={b['representation']['representation_id']:b['representation'] for b in bundles}
    passages=[i['record']['passage'] for b in batches for i in b['items']]
    for c in result['cases']:
        labels=c.pop('labels');c['quote_evidence']=[]
        for span in labels['spans']:
            p=next(p for p in passages if p['representation_id']==span['representation_id']
                   and p['start']<=span['start'] and p['end']>=span['end'])
            c['quote_evidence'].append(dict(passage_id=p['passage_id'],
                quote=reps[p['representation_id']]['text'][span['start']:span['end']],
                grade=span['grade'],concept_ids=span['concept_ids']))
    return result


def test_exact_quotes_reconstruct_offsets_without_mutating_draft(assisted):
    s,m,bs,batches,b=assisted; raw=transcription(s,bs,batches); before=deepcopy(raw)
    prepared=prepare_assisted_quotes(raw,batches)
    assert raw==before
    for old,new in zip(s['cases'],prepared['cases']):
        assert old['labels']['spans']==new['labels']['spans']
    assert check((prepared,m,bs,batches,b))['question_count']==30


@pytest.mark.parametrize('change',['missing','ambiguous','foreign','offset','labels','version'])
def test_bad_quote_transcription_never_guesses_or_echoes(assisted,change):
    s,m,bs,batches,b=deepcopy(assisted);raw=transcription(s,bs,batches)
    q=raw['cases'][0]['quote_evidence'][0]
    if change=='missing':q['quote']='SECRET_CANARY'
    if change=='ambiguous':
        q['quote']='a'
        for batch in batches:
            for i in batch['items']:
                if i['record']['passage']['passage_id']==q['passage_id']:i['record']['text']='a a'
    if change=='foreign':q['passage_id']='SECRET_CANARY'
    if change=='offset':q['start']=0
    if change=='labels':raw['cases'][0]['labels']={}
    if change=='version':raw['schema_version']='prowl-private-evaluation-v1'
    with pytest.raises(PrivateValidationError) as e:prepare_assisted_quotes(raw,batches)
    assert 'SECRET_CANARY' not in str(e.value)


def test_redirected_private_preparation_stops_before_path_prompt(monkeypatch):
    from src.retrieval import private_evaluation as p
    import sys
    monkeypatch.setattr(sys,'argv',['private_evaluation','--prepare-assisted'])
    monkeypatch.setattr(p,'load_assisted_public_inputs',lambda root:(None,None,None,None,None,None))
    monkeypatch.setattr(sys.stdin,'isatty',lambda:False)
    monkeypatch.setattr('builtins.input',lambda *a:pytest.fail('Private prompt reached'))
    with pytest.raises(SystemExit,match='private terminal'):p.main()


@pytest.mark.parametrize('mismatch',[False,True])
def test_operator_preparation_binds_original_and_saves_only_privately(assisted,tmp_path,monkeypatch,mismatch,capsys):
    from src.retrieval import private_evaluation as p
    from src.retrieval.records import sha256_hex
    import sys
    s,m,bs,batches,b=deepcopy(assisted)
    draft=tmp_path/'invented-reviewed.md';draft.write_text('Invented source draft, no real questions.')
    s['source_draft_sha256']=s['reviewed_draft_sha256']=sha256_hex(draft.read_bytes())
    raw=transcription(s,bs,batches)
    if mismatch:raw['reviewed_draft_sha256']='0'*64
    path=tmp_path/'invented-transcription.json';path.write_text(json.dumps(raw))
    monkeypatch.setattr(sys,'argv',['private_evaluation','--prepare-assisted'])
    monkeypatch.setattr(p,'load_assisted_public_inputs',lambda root:(m,bs,batches,b,[],[]))
    monkeypatch.setattr(sys.stdin,'isatty',lambda:True)
    answers=iter(['PRIVATE','REVIEWED'])
    monkeypatch.setattr('builtins.input',lambda *a:next(answers))
    import getpass
    paths=iter([str(path),str(draft)])
    monkeypatch.setattr(getpass,'getpass',lambda *a:next(paths))
    if mismatch:
        with pytest.raises(SystemExit,match='draft identity'):p.main()
        assert not (tmp_path/'invented-transcription.validated').exists()
    else:
        p.main()
        saved=json.loads((tmp_path/'invented-transcription.validated/validation.json').read_text())
        assert saved['original_draft_hash_verified'] and not saved['ready_for_evaluation']
        assert (tmp_path/'invented-transcription.validated/validated-set.json').stat().st_mode&0o777==0o600
    assert 'Invented source draft' not in capsys.readouterr().out
