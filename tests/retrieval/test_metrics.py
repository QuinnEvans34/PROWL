"""Official D-085 metrics (hand oracles), ranking validation, and the provisional span-hit metric."""
from copy import deepcopy
import json

import pytest

from src.retrieval.labels import make_label_set
from src.retrieval.metrics import (TARGET_DEPTH, collapse_to_sources, evaluate, make_ranking, mean_or_none,
                                   recall_at_k, reciprocal_rank, span_hit_recall, verify_ranking)
from src.retrieval.passages import chunk_config, make_passages, make_representation
from src.retrieval.query import make_query
from src.retrieval.records import (RecordError, build_corpus, canonical_bytes, identity_digest, make_event,
                                   make_revision, make_rights, make_work, sha256_hex)

pytestmark = pytest.mark.unit
ALL = dict(retain_metadata=True, local_text_store=True, local_embedding=True, display_snippet=True,
           redistribute=False)
FINDING = dict(modality='CT', anatomy='pancreas', task='review', finding_state='candidate')
QUERY = make_query(FINDING, 'Which synthetic margin sign is described in the phases?')
REFUSED = make_query(FINDING, 'Does this patient have cancer?')
assert QUERY['state'] == 'accepted' and REFUSED['state'] == 'refused'


def test_packet_oracle_recall_and_mrr():
    gold, ranking = {'A', 'C'}, ['B', 'C', 'A']
    assert recall_at_k(ranking, gold, 1) == 0
    assert recall_at_k(ranking, gold, 2) == 0.5
    assert recall_at_k(ranking, gold, 3) == 1
    assert reciprocal_rank(ranking, gold) == 0.5
    assert reciprocal_rank(['X', 'Y'], {'A'}) == 0
    assert mean_or_none([0.5, 0.0]) == 0.25


def test_metric_input_validation():
    for k in (0, -1, True, 1.0, '3'):
        with pytest.raises(RecordError):
            recall_at_k(['A'], {'A'}, k)
    with pytest.raises(RecordError, match='duplicate'):
        recall_at_k(['A', 'A'], {'A'}, 1)
    with pytest.raises(RecordError, match='empty gold'):
        recall_at_k(['A'], set(), 1)
    with pytest.raises(RecordError, match='empty gold'):
        reciprocal_rank(['A'], [])
    assert recall_at_k(['A'], ['A', 'A'], 1) == 1  # gold is a set: duplicates cannot inflate it
    assert mean_or_none([]) is None


def test_source_collapse_first_occurrence_then_renumber():
    work = {'p1': 'w1', 'p2': 'w1', 'p3': 'w2', 'p4': 'w1', 'p5': 'w3'}
    assert collapse_to_sources(['p1', 'p2', 'p3', 'p4', 'p5'], work) == ['w1', 'w2', 'w3']
    # w2 is rank 2 after collapsing, although its passage was at position 3.
    assert reciprocal_rank(collapse_to_sources(['p1', 'p2', 'p3'], work), {'w2'}) == 0.5


# --- a small synthetic corpus with two works -----------------------------------------------------

def corpus(docs=None, max_chars=6):
    docs = docs or {'work:synthetic:m1': 'Aa bb. Cc dd. Ee ff.', 'work:synthetic:m2': 'Gg hh. Ii jj.'}
    works, revs, events, reps, rights, passages = [], [], [], [], [], []
    for i, (w, text) in enumerate(docs.items()):
        works.append(make_work(w))
        rev = make_revision(w, text.encode())
        revs.append(rev)
        events.append(make_event('base', i, 'add_or_replace', w, rev['revision_id']))
        rep = make_representation(work_id=w, revision_id=rev['revision_id'], kind='abstract',
                                  sections=[dict(section_id='s0', title='', paragraphs=[text])])
        reps.append(rep)
        rights.append(make_rights(rep['representation_id'], decision='allowed', permissions=ALL))
        passages.extend(make_passages(rep, chunk_config(max_chars=max_chars, overlap_sentences=0)))
    manifest = build_corpus(works=works, revisions=revs, events=events, file_sequence=['base'],
                            representations=reps, rights=rights, passages=passages)
    return manifest, passages, reps


def _inputs_without_last_work():
    text = 'Aa bb. Cc dd. Ee ff.'
    w = 'work:synthetic:m1'
    rev = make_revision(w, text.encode())
    rep = make_representation(work_id=w, revision_id=rev['revision_id'], kind='abstract',
                              sections=[dict(section_id='s0', title='', paragraphs=[text])])
    return dict(works=[make_work(w)], revisions=[rev], events=[make_event('base', 0, 'add_or_replace', w,
                                                                          rev['revision_id'])],
                file_sequence=['base'], representations=[rep],
                rights=[make_rights(rep['representation_id'], decision='allowed', permissions=ALL)],
                passages=make_passages(rep, chunk_config(max_chars=6, overlap_sentences=0)))


def span(rep, start, end, concepts=('c:one',)):
    return dict(representation_id=rep['representation_id'], representation_sha256=rep['text_sha256'],
                start=start, end=end, grade='direct', concept_ids=list(concepts))


def ranking(manifest, question_id, order, config='cfg:syn-a', query=QUERY):
    items = [dict(passage_id=pid, score=float(len(order) - i)) for i, pid in enumerate(order)]
    return make_ranking(question_id=question_id, query_id=query['query_id'], corpus_manifest=manifest,
                        configuration_id=config, items=items)


def reid(r):
    """Re-derive a mutated ranking's ID, so the semantic checks are tested on their own."""
    r['ranking_id'] = 'rank:' + sha256_hex(canonical_bytes(
        {k: v for k, v in r.items() if k not in ('schema_version', 'ranking_id')}))
    return r


def queries(*question_ids, query=QUERY):
    return {q: query for q in question_ids}


def test_ranking_validation_rules():
    manifest, passages, _ = corpus()
    ids = [p['passage_id'] for p in passages]
    r = ranking(manifest, 'q:a', ids)
    verify_ranking(r, manifest, QUERY)
    assert r['result_count'] == r['eligible_count'] == 5 and r['shortfall_reason'] == 'eligible_pool_exhausted'
    assert r['eligibility_policy'] == 'all_corpus_members'
    with pytest.raises(RecordError, match=r'min\(50'):
        make_ranking(question_id='q:a', query_id=QUERY['query_id'], corpus_manifest=manifest,
                     configuration_id='cfg:x', items=[dict(passage_id=ids[0], score=1.0)])
    bad = deepcopy(r)
    bad['items'][0], bad['items'][1] = bad['items'][1], bad['items'][0]
    with pytest.raises(RecordError):
        verify_ranking(bad, manifest, QUERY)  # both the ID and the tie-policy order now fail
    unordered = make_ranking(question_id='q:a', query_id=QUERY['query_id'], corpus_manifest=manifest,
                             configuration_id='cfg:x',
                             items=[dict(passage_id=pid, score=float(i)) for i, pid in enumerate(ids)])
    with pytest.raises(RecordError, match='ordered'):
        verify_ranking(unordered, manifest, QUERY)
    ok = make_ranking(question_id='q:a', query_id=QUERY['query_id'], corpus_manifest=manifest,
                      configuration_id='cfg:x', items=[dict(passage_id=pid, score=1.0) for pid in sorted(ids)])
    verify_ranking(ok, manifest, QUERY)  # equal scores: passage_id ascending


@pytest.mark.failure_injection
def test_cross_corpus_duplicate_and_unknown_items_rejected():
    manifest, passages, _ = corpus()
    ids = [p['passage_id'] for p in passages]
    other = deepcopy(manifest)
    other['members'] = other['members'][:-1]
    with pytest.raises(RecordError):
        verify_ranking(ranking(manifest, 'q:a', ids), other, QUERY)  # tampered manifest / different corpus
    with pytest.raises(RecordError, match='duplicate'):
        make_ranking(question_id='q:a', query_id=QUERY['query_id'], corpus_manifest=manifest,
                     configuration_id='cfg:x', items=[dict(passage_id=ids[0], score=1.0)] * 5)
    smaller = build_corpus(**_inputs_without_last_work())
    with pytest.raises(RecordError, match='different corpus'):
        verify_ranking(ranking(manifest, 'q:a', ids), smaller, QUERY)
    unknown = ranking(manifest, 'q:a', ids)
    unknown['items'][-1]['passage_id'] = 'psg:' + 'e' * 64
    with pytest.raises(RecordError, match='outside the corpus'):
        verify_ranking(reid(unknown), manifest, QUERY)


@pytest.mark.component
def test_evaluate_hand_computed_report():
    manifest, passages, reps = corpus()
    m1, m2 = reps
    by = {(p['work_id'], p['start']): p['passage_id'] for p in passages}
    a1, a2, a3 = by[(m1['work_id'], 0)], by[(m1['work_id'], 7)], by[(m1['work_id'], 14)]
    b1, b2 = by[(m2['work_id'], 0)], by[(m2['work_id'], 7)]
    q1 = make_label_set(question_id='q:one', label_version='lv1', answerable=True, required_concepts=['c:one'],
                        spans=[span(m1, 0, 6), span(m1, 14, 20)])          # gold passages {a1, a3}; works {m1}
    q2 = make_label_set(question_id='q:two', label_version='lv1', answerable=True, required_concepts=['c:one'],
                        spans=[span(m2, 7, 13)])                           # gold {b2}; works {m2}
    q3 = make_label_set(question_id='q:refuse', label_version='lv1', answerable=False)
    rankings = {'q:one': ranking(manifest, 'q:one', [a2, a3, b1, a1, b2]),
                'q:two': ranking(manifest, 'q:two', [a1, a2, a3, b1, b2])}
    report = evaluate(label_sets=[q1, q2, q3], rankings=rankings, queries=queries('q:one', 'q:two'),
                      corpus_manifest=manifest, passages=passages, representations=reps,
                      configuration_id='cfg:syn-a', label_version='lv1')
    off = report['official']
    assert off['n_answerable'] == 2 and off['n_refusal_excluded'] == 1 and off['undefined_reason'] is None
    # Passage level. q1: gold {a1,a3}; ranks a2,a3,b1,a1,b2 -> r@1=0, r@3=1/2, r@5=1, RR=1/2.
    #                q2: gold {b2}; b2 at rank 5 -> r@1=r@3=0, r@5=1, RR=1/5.
    assert off['passage']['recall_at'] == {'1': 0.0, '3': 0.25, '5': 1.0, '10': 1.0}
    assert off['passage']['mrr'] == pytest.approx((0.5 + 0.2) / 2)
    # Source level. q1 sources [m1, m2]: m1 at rank 1 -> r@k=1, RR=1. q2 sources [m1, m2]: m2 rank 2.
    assert off['source']['recall_at'] == {'1': 0.5, '3': 1.0, '5': 1.0, '10': 1.0}
    assert off['source']['mrr'] == pytest.approx((1 + 0.5) / 2)
    prov = report['provisional']
    assert prov['status'] == 'proposed_provisional_not_official' and prov['n_direct_spans'] == 3
    assert prov['span_hit_recall_at']['3'] == pytest.approx((0.5 + 0) / 2)
    json.dumps(report, allow_nan=False)
    assert canonical_bytes(report)


def test_empty_answerable_set_is_explicitly_undefined():
    manifest, passages, reps = corpus()
    q = make_label_set(question_id='q:refuse', label_version='lv1', answerable=False)
    report = evaluate(label_sets=[q], rankings={}, queries={}, corpus_manifest=manifest, passages=passages,
                      representations=reps, configuration_id='cfg:syn-a', label_version='lv1')
    assert report['official']['undefined_reason'] == 'no_answerable_questions'
    assert report['official']['source']['mrr'] is None
    assert set(report['official']['passage']['recall_at'].values()) == {None}
    assert 'NaN' not in json.dumps(report)


def test_passage_metric_undefined_when_no_passage_contains_span():
    manifest, passages, reps = corpus()
    m1 = reps[0]
    q = make_label_set(question_id='q:one', label_version='lv1', answerable=True, required_concepts=['c:one'],
                       spans=[span(m1, 4, 10)])  # crosses two one-sentence passages
    ids = [p['passage_id'] for p in passages]
    report = evaluate(label_sets=[q], rankings={'q:one': ranking(manifest, 'q:one', ids)}, queries=queries('q:one'),
                      corpus_manifest=manifest, passages=passages, representations=reps,
                      configuration_id='cfg:syn-a', label_version='lv1')
    assert report['official']['passage']['n_undefined'] == 1
    assert report['official']['passage']['mrr'] is None
    assert report['official']['source']['mrr'] == 1.0  # source-level still defined
    assert report['provisional']['span_hit_recall_at']['10'] == 0.0


@pytest.mark.failure_injection
def test_evaluate_rejects_mixed_versions_and_configurations():
    manifest, passages, reps = corpus()
    m1 = reps[0]
    q = make_label_set(question_id='q:one', label_version='lv1', answerable=True, required_concepts=['c:one'],
                       spans=[span(m1, 0, 6)])
    ids = [p['passage_id'] for p in passages]
    common = dict(queries=queries('q:one'), corpus_manifest=manifest, passages=passages, representations=reps,
                  configuration_id='cfg:syn-a')
    with pytest.raises(RecordError, match='mixed label versions'):
        evaluate(label_sets=[q], rankings={'q:one': ranking(manifest, 'q:one', ids)}, label_version='lv2', **common)
    with pytest.raises(RecordError, match='different configuration'):
        evaluate(label_sets=[q], rankings={'q:one': ranking(manifest, 'q:one', ids, config='cfg:other')},
                 label_version='lv1', **common)
    with pytest.raises(RecordError, match='no ranking'):
        evaluate(label_sets=[q], rankings={}, label_version='lv1', **common)


def test_span_hit_counts_each_span_once_across_overlapping_passages():
    rep = make_representation(work_id='work:synthetic:x', revision_id='rev:' + 'c' * 64, kind='abstract',
                              sections=[dict(section_id='s0', title='', paragraphs=['Aa bb. Cc dd. Ee ff.'])])
    overlapping = make_passages(rep, chunk_config(max_chars=13, overlap_sentences=1))  # [0,13) [7,20)
    by_id = {p['passage_id']: p for p in overlapping}
    spans = [span(rep, 7, 13), span(rep, 14, 20)]
    ids = [p['passage_id'] for p in overlapping]
    assert span_hit_recall(ids, by_id, spans, 1) == 0.5   # first passage holds [7,13) only
    assert span_hit_recall(ids, by_id, spans, 2) == 1.0   # [7,13) counted once, not twice
    assert span_hit_recall(ids, by_id, spans + [dict(spans[0])], 2) == 1.0


def test_span_hit_duplicate_containment_does_not_inflate_partial_recall():
    # Sentences [0,6) [7,13) [14,20) [21,27); overlapping passages [0,13) [7,20) [14,27).
    rep = make_representation(work_id='work:synthetic:x', revision_id='rev:' + 'c' * 64, kind='abstract',
                              sections=[dict(section_id='s0', title='', paragraphs=['Aa bb. Cc dd. Ee ff. Gg hh.'])])
    passages = make_passages(rep, chunk_config(max_chars=13, overlap_sentences=1))
    assert [(p['start'], p['end']) for p in passages] == [(0, 13), (7, 20), (14, 27)]
    by_id = {p['passage_id']: p for p in passages}
    spans = [span(rep, 7, 13), span(rep, 21, 27)]  # first span sits in both top-2 passages
    assert span_hit_recall([p['passage_id'] for p in passages], by_id, spans, 2) == 0.5


# --- Codex P3 review R5: verifiable eligible pool and min(50, eligible) depth -----------------------

@pytest.mark.failure_injection
def test_r5_false_exhaustion_rejected():
    manifest, passages, _ = corpus()
    ids = [p['passage_id'] for p in passages]
    with pytest.raises(RecordError, match=r'min\(50'):
        ranking(manifest, 'q:one', ids[:1])  # the Codex probe: 1 of 5 members claiming exhaustion
    forged = ranking(manifest, 'q:one', ids)
    forged['items'], forged['result_count'], forged['eligible_count'] = forged['items'][:1], 1, 1
    with pytest.raises(RecordError, match='eligible_count does not match'):
        verify_ranking(reid(forged), manifest, QUERY)
    short = ranking(manifest, 'q:one', ids)
    short['items'], short['result_count'] = short['items'][:1], 1  # truthful count, too few results
    with pytest.raises(RecordError, match=r'min\(50'):
        verify_ranking(reid(short), manifest, QUERY)


@pytest.mark.failure_injection
@pytest.mark.parametrize('value', [True, 5.0, '5', -1, None])
def test_r5_eligible_count_must_be_a_plain_integer(value):
    manifest, passages, _ = corpus()
    r = ranking(manifest, 'q:one', [p['passage_id'] for p in passages])
    r['eligible_count'] = value
    with pytest.raises(RecordError):
        verify_ranking(reid(r), manifest, QUERY)


def test_r5_valid_small_and_empty_pools():
    manifest, passages, _ = corpus()
    r = ranking(manifest, 'q:one', [p['passage_id'] for p in passages])
    assert verify_ranking(r, manifest, QUERY)['shortfall_reason'] == 'eligible_pool_exhausted'
    no_shortfall = reid(dict(deepcopy(r), shortfall_reason=None))
    with pytest.raises(RecordError, match='shortfall_reason'):
        verify_ranking(no_shortfall, manifest, QUERY)
    empty_corpus = dict(manifest, members=[], excluded=[],
                        counts=dict(input_passages=0, members=0, excluded=0))
    empty_corpus['corpus_id'] = 'corpus:' + identity_digest(dict(allowed_origins=manifest['allowed_origins'],
                                                                 members=[]))
    empty = ranking(empty_corpus, 'q:one', [])
    assert empty['eligible_count'] == 0 and verify_ranking(empty, empty_corpus, QUERY)['result_count'] == 0


@pytest.mark.component
def test_r5_depth_fifty_when_pool_is_larger():
    text = ' '.join(f'Item{i} here.' for i in range(60))  # 60 one-sentence passages
    manifest, passages, _ = corpus({'work:synthetic:big': text}, max_chars=1)
    assert len(manifest['members']) == 60
    ids = sorted(m['passage_id'] for m in manifest['members'])
    full = make_ranking(question_id='q:one', query_id=QUERY['query_id'], corpus_manifest=manifest,
                        configuration_id='cfg:x', items=[dict(passage_id=pid, score=1.0) for pid in ids[:TARGET_DEPTH]])
    verify_ranking(full, manifest, QUERY)
    assert full['result_count'] == 50 and full['eligible_count'] == 60 and full['shortfall_reason'] is None
    with pytest.raises(RecordError, match=r'min\(50'):
        make_ranking(question_id='q:one', query_id=QUERY['query_id'], corpus_manifest=manifest,
                     configuration_id='cfg:x', items=[dict(passage_id=pid, score=1.0) for pid in ids[:49]])
    claimed = reid(dict(deepcopy(full), shortfall_reason='eligible_pool_exhausted'))
    with pytest.raises(RecordError, match='shortfall_reason'):
        verify_ranking(claimed, manifest, QUERY)


# --- Codex P3 review R2: evaluation bound to question, accepted query and verified records ---------

def _r2_inputs():
    manifest, passages, reps = corpus()
    q = make_label_set(question_id='q:one', label_version='lv1', answerable=True, required_concepts=['c:one'],
                       spans=[span(reps[0], 0, 6)])
    ids = [p['passage_id'] for p in passages]
    kwargs = dict(label_sets=[q], rankings={'q:one': ranking(manifest, 'q:one', ids)}, queries=queries('q:one'),
                  corpus_manifest=manifest, passages=passages, representations=reps,
                  configuration_id='cfg:syn-a', label_version='lv1')
    return kwargs, q, ids


@pytest.mark.failure_injection
def test_r2_ranking_filed_under_the_wrong_question_rejected():
    kwargs, _, ids = _r2_inputs()
    kwargs['rankings'] = {'q:one': ranking(kwargs['corpus_manifest'], 'q:wrong', ids)}  # Codex probe
    with pytest.raises(RecordError, match='different question'):
        evaluate(**kwargs)
    kwargs['rankings'] = {'q:one': ranking(kwargs['corpus_manifest'], 'q:one', ids),
                          'q:extra': ranking(kwargs['corpus_manifest'], 'q:extra', ids)}
    with pytest.raises(RecordError, match='no label set'):
        evaluate(**kwargs)


@pytest.mark.failure_injection
def test_r2_duplicate_question_label_sets_rejected():
    kwargs, q, _ = _r2_inputs()
    assert evaluate(**kwargs)['official']['n_answerable'] == 1
    with pytest.raises(RecordError, match='duplicate question_id'):
        evaluate(**dict(kwargs, label_sets=[q, q]))  # Codex probe: previously counted twice
    other_version = dict(q, spans=[dict(q['spans'][0], concept_ids=['c:one'])])
    with pytest.raises(RecordError, match='duplicate question_id'):
        evaluate(**dict(kwargs, label_sets=[q, other_version]))


@pytest.mark.failure_injection
def test_r2_refused_missing_or_mismatched_query_rejected():
    kwargs, _, ids = _r2_inputs()
    with pytest.raises(RecordError, match='different query'):
        evaluate(**dict(kwargs, queries={'q:one': REFUSED}))
    refused_ranking = ranking(kwargs['corpus_manifest'], 'q:one', ids, query=REFUSED)
    with pytest.raises(RecordError, match='refused query'):
        evaluate(**dict(kwargs, rankings={'q:one': refused_ranking}, queries={'q:one': REFUSED}))
    other = make_query(FINDING, 'Which synthetic sign differs between the phases?')
    with pytest.raises(RecordError, match='different query'):
        evaluate(**dict(kwargs, queries={'q:one': other}))
    with pytest.raises(RecordError, match='no query record'):
        evaluate(**dict(kwargs, queries={}))
    tampered = dict(QUERY, question_original='Something else entirely?')
    with pytest.raises(RecordError):
        evaluate(**dict(kwargs, queries={'q:one': tampered}))


@pytest.mark.failure_injection
def test_r2_changed_passage_or_representation_content_rejected():
    kwargs, _, _ = _r2_inputs()
    forged = deepcopy(kwargs['passages'])
    forged[0]['end'] = len(kwargs['representations'][0]['text'])  # widen the passage, keep its ID
    with pytest.raises(RecordError, match='hash'):
        evaluate(**dict(kwargs, passages=forged))
    rep0 = kwargs['representations'][0]
    forged[0]['text_sha256'] = sha256_hex(rep0['text'][forged[0]['start']:forged[0]['end']])
    with pytest.raises(RecordError, match='passage ID does not match'):
        evaluate(**dict(kwargs, passages=forged))  # consistent hash, stale identity
    reps = deepcopy(kwargs['representations'])
    reps[0]['text'] = reps[0]['text'].replace('Cc', 'Zz')
    with pytest.raises(RecordError, match='hash'):
        evaluate(**dict(kwargs, representations=reps))
    remapped = deepcopy(kwargs['representations'])  # text intact, provenance map forged under the old ID
    remapped[0]['paragraphs'][0]['offset_map'] = [[0, 1, 9000, 9001]]
    with pytest.raises(RecordError, match='representation ID'):
        evaluate(**dict(kwargs, representations=remapped))
    with pytest.raises(RecordError, match='duplicate representation'):
        evaluate(**dict(kwargs, representations=kwargs['representations'] + kwargs['representations'][:1]))
    with pytest.raises(RecordError, match='duplicate passage'):
        evaluate(**dict(kwargs, passages=kwargs['passages'] + kwargs['passages'][:1]))
    with pytest.raises(RecordError, match='missing'):
        evaluate(**dict(kwargs, passages=kwargs['passages'][1:]))


@pytest.mark.failure_injection
def test_r2_manifest_entry_must_match_the_passage_record():
    kwargs, _, _ = _r2_inputs()
    manifest = deepcopy(kwargs['corpus_manifest'])
    manifest['members'][0]['text_sha256'] = '0' * 64
    manifest['corpus_id'] = 'corpus:' + identity_digest(dict(allowed_origins=manifest['allowed_origins'],
                                                             members=manifest['members']))
    with pytest.raises(RecordError, match='corpus member entry'):
        evaluate(**dict(kwargs, corpus_manifest=manifest,
                        rankings={'q:one': ranking(manifest, 'q:one', [m['passage_id'] for m in manifest['members']])}))
