"""End-to-end synthetic chain and portability checks.

documents -> rights -> passages -> corpus -> validated query -> supplied ranking -> labels ->
ranked metrics and delivered evidence. Refusal, unavailable and insufficient-evidence outcomes are
explicit fixture states chosen by this test, not the behaviour of a working retriever or response
service (none exists in P3).
"""
from copy import deepcopy
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from src.retrieval.context import FixtureCounts, delivered_evidence
from src.retrieval.labels import make_label_set
from src.retrieval.metrics import evaluate, make_ranking, verify_ranking
from src.retrieval.passages import chunk_config, make_passages, make_representation
from src.retrieval.query import make_query
from src.retrieval.records import (RecordError, build_corpus, canonical_bytes, make_event, make_revision,
                                   make_rights, make_work)

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / 'fixtures' / 'synthetic_documents.json'
FINDING = dict(modality='CT', anatomy='pancreas', task='review', finding_state='candidate')
ALL = dict(retain_metadata=True, local_text_store=True, local_embedding=True, display_snippet=True,
           redistribute=False)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_a, **_k):
        raise AssertionError('network access attempted')
    monkeypatch.setattr(socket.socket, 'connect', refuse)
    monkeypatch.setattr(socket, 'create_connection', refuse)


def build():
    docs = json.loads(FIXTURE.read_text(encoding='utf-8'))['works']
    works, revs, events, reps, rights, passages = [], [], [], [], [], []
    for i, doc in enumerate(docs):
        retracted = doc['work_id'] == 'work:synthetic:retracted-item'
        works.append(make_work(doc['work_id'], notices=[dict(notice_type='retraction', reference='syn-1')]
                               if retracted else ()))
        rev = make_revision(doc['work_id'], canonical_bytes(doc))
        revs.append(rev)
        events.append(make_event('synthetic-base-001.jsonl', i, 'add_or_replace', doc['work_id'], rev['revision_id']))
        rep = make_representation(work_id=doc['work_id'], revision_id=rev['revision_id'], kind=doc['kind'],
                                  sections=doc['sections'])
        reps.append(rep)
        rights.append(make_rights(rep['representation_id'], decision='allowed', permissions=ALL))
        passages.extend(make_passages(rep, chunk_config(max_chars=90, overlap_sentences=1)))
    inputs = dict(works=works, revisions=revs, events=events, file_sequence=['synthetic-base-001.jsonl'],
                  representations=reps, rights=rights, passages=passages)
    return inputs, build_corpus(**inputs)


def outcome(query, ranking, manifest):
    """Fixture-level outcome states (not a response service)."""
    if query['state'] == 'refused':
        return 'out_of_scope'
    if ranking is None:
        return 'unavailable'
    try:
        verify_ranking(ranking, manifest, query)
    except RecordError:
        return 'unavailable'
    return 'insufficient_evidence' if not ranking['items'] else 'ranked_passages_available'


def run_chain():
    inputs, manifest = build()
    passages, reps = inputs['passages'], inputs['representations']
    zorbel = next(r for r in reps if r['work_id'] == 'work:synthetic:zorbel-margins')
    member = {m['passage_id'] for m in manifest['members']}
    ranked = [p for p in passages if p['passage_id'] in member]
    ranked.sort(key=lambda p: (p['work_id'] != 'work:synthetic:quintar-review', p['work_id'], p['start']))
    query = make_query(FINDING, 'Why is the zorbel margin not visible in some phases?')
    items = [dict(passage_id=p['passage_id'], score=float(100 - i)) for i, p in enumerate(ranked)]
    ranking = make_ranking(question_id='q:zorbel', query_id=query['query_id'], corpus_manifest=manifest,
                           configuration_id='cfg:syn-chunk90', items=items)
    start = zorbel['text'].index('The zorbel margin is not visible in the Vell phase.')
    span = dict(representation_id=zorbel['representation_id'], representation_sha256=zorbel['text_sha256'],
                start=start, end=start + len('The zorbel margin is not visible in the Vell phase.'),
                grade='direct', concept_ids=['c:visibility'])
    labels = make_label_set(question_id='q:zorbel', label_version='lv-syn-1', answerable=True,
                            required_concepts=['c:visibility'], spans=[span])
    report = evaluate(label_sets=[labels], rankings={'q:zorbel': ranking}, queries={'q:zorbel': query},
                      corpus_manifest=manifest, passages=passages, representations=reps,
                      configuration_id='cfg:syn-chunk90', label_version='lv-syn-1')
    context = delivered_evidence(question_label_set=labels, query=query, ranking=ranking, corpus_manifest=manifest,
                                 passages=passages, representations=reps, rights=inputs['rights'],
                                 counter=FixtureCounts({p['passage_id']: 400 for p in ranked}), budget=2000)
    return inputs, manifest, query, ranking, labels, report, context


def test_full_synthetic_chain_hand_checked():
    inputs, manifest, query, ranking, labels, report, context = run_chain()
    assert manifest['counts']['excluded'] >= 1  # retracted work never becomes answer support
    assert all(m['work_id'] != 'work:synthetic:retracted-item' for m in manifest['members'])
    assert outcome(query, ranking, manifest) == 'ranked_passages_available'
    # Ranking: quintar-review's two passages [0,68) [69,131) first, then zorbel passages in text
    # order [0,81) [83,155) [157,215) [216,290). The gold span [0,51) is inside zorbel [0,81) at
    # rank 3, so passage RR = 1/3; sources collapse to [quintar, zorbel], so source RR = 1/2.
    assert report['official']['passage']['mrr'] == pytest.approx(1 / 3)
    assert report['official']['source']['mrr'] == 0.5
    assert report['official']['source']['recall_at']['1'] == 0.0
    assert report['official']['source']['recall_at']['3'] == 1.0
    assert report['provisional']['span_hit_recall_at']['1'] == 0.0
    assert report['provisional']['span_hit_recall_at']['3'] == 1.0
    # 400 tokens each: the first five of six passages fit 2,000 exactly; the gold span (rank 3) is delivered.
    assert context['delivered_tokens'] == 2000 and context['delivered_span_recall'] == 1.0


def test_fixture_outcome_states():
    inputs, manifest, query, ranking, *_ = run_chain()
    refused = make_query(FINDING, 'Does this patient have cancer?')
    assert outcome(refused, ranking, manifest) == 'out_of_scope'
    assert outcome(query, None, manifest) == 'unavailable'
    other = deepcopy(inputs)
    other['passages'] = other['passages'][1:]  # drop a member passage: a different corpus
    assert outcome(query, ranking, build_corpus(**other)) == 'unavailable'  # corpus mismatch, never coerced
    none_indexable = deepcopy(inputs)  # every representation refused for indexing: an empty corpus
    none_indexable['rights'] = [make_rights(r['representation_id'], decision='metadata_only', permissions=ALL)
                                for r in none_indexable['representations']]
    empty_corpus = build_corpus(**none_indexable)
    assert empty_corpus['members'] == []
    empty = make_ranking(question_id='q:zorbel', query_id=query['query_id'], corpus_manifest=empty_corpus,
                         configuration_id='cfg:syn-chunk90', items=[])
    assert outcome(query, empty, empty_corpus) == 'insufficient_evidence'
    assert outcome(query, empty, manifest) == 'unavailable'  # an empty ranking is not valid for a full pool


def test_deterministic_rebuild_and_inputs_not_mutated():
    first = run_chain()
    second = run_chain()
    assert [canonical_bytes(x) for x in first[1:]] == [canonical_bytes(x) for x in second[1:]]
    inputs, _ = build()
    before = deepcopy(inputs)
    build_corpus(**inputs)
    assert inputs == before


def test_records_are_portable_no_absolute_paths_or_secrets():
    blob = b''.join(canonical_bytes(x) for x in run_chain()[1:]).decode()
    for marker in ('/Users/', '/Volumes/', '/home/', 'C:\\', 'file:', 'PROWL-Data'):
        assert marker not in blob
    source = ''.join(p.read_text() for p in (ROOT / 'src' / 'retrieval').glob('*.py'))
    for marker in ('/Users/', '/Volumes/', 'PROWL-Data', 'api_key', 'password=', 'requests', 'urllib', 'socket'):
        assert marker not in source


def test_import_has_no_side_effects(tmp_path):
    code = ('import sys; sys.path.insert(0, %r); import src.retrieval, src.retrieval.records, '
            'src.retrieval.passages, src.retrieval.query, src.retrieval.labels, src.retrieval.metrics, '
            'src.retrieval.context' % str(ROOT))
    subprocess.run([sys.executable, '-B', '-c', code], cwd=tmp_path, check=True,
                   env={'PYTHONDONTWRITEBYTECODE': '1', 'PATH': ''})
    assert list(tmp_path.iterdir()) == []


def test_ranking_bound_to_accepted_query_and_evaluation_permutation_invariant():
    inputs, manifest, query, ranking, labels, report, _ = run_chain()
    verify_ranking(ranking, manifest, query=query)
    refused = make_query(FINDING, 'Does this patient have cancer?')
    with pytest.raises(RecordError):
        verify_ranking(ranking, manifest, query=refused)
    refusal_labels = make_label_set(question_id='q:refuse', label_version='lv-syn-1', answerable=False)
    before = deepcopy([labels, refusal_labels])
    args = dict(rankings={'q:zorbel': ranking}, queries={'q:zorbel': query, 'q:refuse': refused},
                corpus_manifest=manifest, passages=inputs['passages'],
                representations=inputs['representations'], configuration_id='cfg:syn-chunk90',
                label_version='lv-syn-1')
    a = evaluate(label_sets=[labels, refusal_labels], **args)
    b = evaluate(label_sets=[refusal_labels, labels],
                 **dict(args, passages=list(reversed(inputs['passages'])),
                        representations=list(reversed(inputs['representations']))))
    assert a == b and [labels, refusal_labels] == before
