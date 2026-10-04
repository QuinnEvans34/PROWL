"""Delivered-evidence prototype (PROPOSAL): whole-passage packing and delivered-span scoring."""
from copy import deepcopy
import json

import pytest

from src.retrieval.context import (PROVISIONAL_BUDGET, FixtureCounts, SyntheticWordCounter,
                                   delivered_evidence, pack)
from src.retrieval.labels import make_label_set
from src.retrieval.metrics import make_ranking
from src.retrieval.passages import chunk_config, make_passages, make_representation, passage_text
from src.retrieval.query import make_query
from src.retrieval.records import (RecordError, build_corpus, make_event, make_revision, make_rights,
                                   make_work, may_display, may_index, sha256_hex)

pytestmark = pytest.mark.unit
ALL = dict(retain_metadata=True, local_text_store=True, local_embedding=True, display_snippet=True,
           redistribute=False)
FINDING = dict(modality='CT', anatomy='pancreas', task='review', finding_state='candidate')
QUERY = make_query(FINDING, 'Which synthetic margin sign is described in the phases?')


def test_packet_oracle_skip_large_then_fit_small():
    selected, skipped, used = pack(['A', 'B', 'C'], {'A': 8, 'B': 7, 'C': 2}, 10)
    assert selected == ['A', 'C'] and used == 10
    assert skipped == [dict(passage_id='B', tokens=7, reason='exceeds_remaining_budget')]


def test_exact_fit_and_everything_after_exhaustion_is_skipped():
    selected, skipped, used = pack(['A', 'B', 'C'], {'A': 5, 'B': 5, 'C': 1}, 10)
    assert selected == ['A', 'B'] and used == 10 and [s['passage_id'] for s in skipped] == ['C']


@pytest.mark.parametrize('budget', [0, -5, True, 2.0, None])
def test_budget_must_be_positive_integer(budget):
    with pytest.raises(RecordError):
        pack(['A'], {'A': 1}, budget)


@pytest.mark.parametrize('count', [0, -1, False, 1.5, float('nan')])
def test_counts_must_be_positive_integers(count):
    with pytest.raises(RecordError):
        pack(['A'], {'A': count}, 10)


def test_duplicate_ids_rejected_and_provisional_budget_value():
    with pytest.raises(RecordError, match='duplicate'):
        pack(['A', 'A'], {'A': 1}, 10)
    assert PROVISIONAL_BUDGET == 2000


def setup(display=True, max_chars=6, overlap=0, question_id='q:ctx'):
    """One synthetic work, its verified corpus and a label set.

    Sentences: A=[0,6) 'Aa bb.'  B=[7,13) 'Cc dd.'  C=[14,20) 'Ee ff.'
    """
    w, text = 'work:synthetic:x', 'Aa bb. Cc dd. Ee ff.'
    rev = make_revision(w, text.encode())
    rep = make_representation(work_id=w, revision_id=rev['revision_id'], kind='abstract',
                              sections=[dict(section_id='s0', title='', paragraphs=[text])])
    passages = make_passages(rep, chunk_config(max_chars=max_chars, overlap_sentences=overlap))
    rights = [make_rights(rep['representation_id'], decision='allowed', permissions={**ALL, 'display_snippet': display})]
    manifest = build_corpus(works=[make_work(w)], revisions=[rev],
                            events=[make_event('base', 0, 'add_or_replace', w, rev['revision_id'])],
                            file_sequence=['base'], representations=[rep], rights=rights, passages=passages)

    def span(start, end, concepts):
        return dict(representation_id=rep['representation_id'], representation_sha256=rep['text_sha256'],
                    start=start, end=end, grade='direct', concept_ids=list(concepts))
    labels = make_label_set(question_id=question_id, label_version='lv1', answerable=True,
                            required_concepts=['c:one', 'c:two', 'c:three'],
                            spans=[span(0, 6, ['c:one']), span(7, 13, ['c:two']), span(14, 20, ['c:one'])])
    return dict(rep=rep, passages=passages, rights=rights, manifest=manifest, labels=labels)


def rank(ctx, order, question_id='q:ctx', query=QUERY, manifest=None):
    return make_ranking(question_id=question_id, query_id=query['query_id'],
                        corpus_manifest=manifest or ctx['manifest'], configuration_id='cfg:ctx',
                        items=[dict(passage_id=p['passage_id'], score=float(len(order) - i))
                               for i, p in enumerate(order)])


def run(ctx, order, counter, budget=PROVISIONAL_BUDGET, **override):
    args = dict(question_label_set=ctx['labels'], query=QUERY, ranking=rank(ctx, order),
                corpus_manifest=ctx['manifest'], passages=ctx['passages'], representations=[ctx['rep']],
                rights=ctx['rights'], counter=counter, budget=budget)
    args.update(override)
    return delivered_evidence(**args)


def test_packet_oracle_spans_only_in_skipped_passage_are_not_delivered():
    ctx = setup()
    a, b, c = ctx['passages']
    counts = FixtureCounts({a['passage_id']: 8, b['passage_id']: 7, c['passage_id']: 2})
    result = run(ctx, [a, b, c], counts, budget=10)
    assert result['selected'] == [a['passage_id'], c['passage_id']]
    assert result['skipped'] == [dict(passage_id=b['passage_id'], tokens=7, reason='exceeds_remaining_budget')]
    assert result['n_direct_spans'] == 3 and result['n_delivered_spans'] == 2
    assert result['delivered_span_recall'] == pytest.approx(2 / 3)
    # c:one delivered via A and C (counted once); c:two only in skipped B; c:three in no span.
    assert result['n_delivered_concepts'] == 1 and result['concept_coverage'] == pytest.approx(1 / 3)
    assert result['status'] == 'proposed_provisional_not_official'
    assert result['counter'] == dict(name='fixture-counts', version='fixture-counts-v1', kind='fixture_counts')
    json.dumps(result, allow_nan=False)


def test_retrieved_but_not_packed_gets_no_credit_even_when_ranked_first():
    ctx = setup()
    a, b, c = ctx['passages']
    result = run(ctx, [a, b, c], FixtureCounts({a['passage_id']: 11, b['passage_id']: 3, c['passage_id']: 3}),
                 budget=10)
    assert result['selected'] == [b['passage_id'], c['passage_id']]
    assert result['n_delivered_spans'] == 2 and result['n_delivered_concepts'] == 2


def test_overlapping_passages_do_not_double_count():
    ctx = setup(max_chars=13, overlap=1)  # [0,13) [7,20)
    result = run(ctx, ctx['passages'], FixtureCounts({p['passage_id']: 1 for p in ctx['passages']}), budget=10)
    assert result['n_delivered_spans'] == 3 and result['delivered_span_recall'] == 1.0


def test_synthetic_word_counter_is_labelled_and_counts_verified_slices():
    ctx = setup()
    result = run(ctx, ctx['passages'], SyntheticWordCounter(), budget=4)
    assert result['counter']['kind'] == 'synthetic_counter' and result['delivered_tokens'] == 4
    assert SyntheticWordCounter().count('   ') == 0  # would be rejected by pack as a zero count


def test_refusal_question_and_missing_fixture_count_rejected():
    ctx = setup()
    a, b, _ = ctx['passages']
    refusal = make_label_set(question_id='q:ctx', label_version='lv1', answerable=False)
    with pytest.raises(RecordError, match='answerable'):
        run(ctx, ctx['passages'], FixtureCounts({a['passage_id']: 1}), question_label_set=refusal)
    with pytest.raises(RecordError, match='no fixture count'):
        run(ctx, ctx['passages'], FixtureCounts({a['passage_id']: 1, b['passage_id']: 1}))


# --- Codex P3 review R3: verified geometry, verified counted text, display permission ------------

class RecordingCounter(SyntheticWordCounter):
    def __init__(self):
        self.seen = []

    def count(self, text):
        self.seen.append(text)
        return super().count(text)


@pytest.mark.failure_injection
def test_r3_forged_passage_end_offset_rejected():
    ctx = setup()
    counts = FixtureCounts({p['passage_id']: 1 for p in ctx['passages']})
    assert run(ctx, ctx['passages'], counts)['delivered_span_recall'] == 1.0  # all three fit
    only_a = run(ctx, ctx['passages'], FixtureCounts({p['passage_id']: 1 for p in ctx['passages']}), budget=1)
    assert only_a['delivered_span_recall'] == pytest.approx(1 / 3)
    forged = deepcopy(ctx['passages'])
    forged[0]['end'] = len(ctx['rep']['text'])  # Codex probe: same ID and count, wider span
    with pytest.raises(RecordError, match='hash'):
        run(ctx, ctx['passages'], counts, budget=1, passages=forged)
    forged[0]['text_sha256'] = sha256_hex(ctx['rep']['text'][forged[0]['start']:forged[0]['end']])
    with pytest.raises(RecordError, match='passage ID does not match'):
        run(ctx, ctx['passages'], counts, budget=1, passages=forged)


@pytest.mark.failure_injection
def test_r3_counted_text_is_the_verified_slice_and_altered_text_is_refused():
    ctx = setup()
    counter = RecordingCounter()
    run(ctx, ctx['passages'], counter)
    assert counter.seen == ['Aa bb.', 'Cc dd.', 'Ee ff.'] == [passage_text(p, ctx['rep']) for p in ctx['passages']]
    altered = deepcopy(ctx['rep'])
    altered['text'] = altered['text'].replace('Cc dd.', 'Cc dd dd dd.')
    altered['text_sha256'] = sha256_hex(altered['text'])
    counter = RecordingCounter()
    with pytest.raises(RecordError):
        run(ctx, ctx['passages'], counter, representations=[altered])
    assert counter.seen == []  # nothing is counted from unverified text
    remapped = deepcopy(ctx['rep'])  # text intact, provenance map forged under the old ID
    remapped['paragraphs'][0]['offset_map'] = [[0, 1, 9000, 9001]]
    with pytest.raises(RecordError, match='representation ID'):
        run(ctx, ctx['passages'], RecordingCounter(), representations=[remapped])


@pytest.mark.failure_injection
def test_r3_display_permission_enforced_independently_of_indexing():
    ctx = setup(display=False)
    assert may_index(ctx['rights'][0]) and not may_display(ctx['rights'][0])
    assert len(ctx['manifest']['members']) == 3  # indexable, so ranked...
    result = run(ctx, ctx['passages'], FixtureCounts({}))
    assert result['selected'] == [] and result['delivered_tokens'] == 0  # ...but never delivered
    assert [s['reason'] for s in result['skipped']] == ['display_not_permitted'] * 3
    assert all(s['tokens'] is None for s in result['skipped'])
    assert result['n_delivered_spans'] == 0 and result['delivered_span_recall'] == 0.0
    escalated = deepcopy(ctx['rights'])
    escalated[0]['permissions']['display_snippet'] = True  # stale rights_id
    with pytest.raises(RecordError, match='rights ID'):
        run(ctx, ctx['passages'], FixtureCounts({}), rights=escalated)
    with pytest.raises(RecordError, match='rights record missing'):
        run(setup(), setup()['passages'], FixtureCounts({}), rights=[])


@pytest.mark.failure_injection
def test_r3_bound_to_verified_ranking_question_query_and_corpus():
    ctx = setup()
    counts = FixtureCounts({p['passage_id']: 1 for p in ctx['passages']})
    result = run(ctx, ctx['passages'], counts)
    ranking = rank(ctx, ctx['passages'])
    assert (result['ranking_id'], result['query_id'], result['corpus_id']) == \
        (ranking['ranking_id'], QUERY['query_id'], ctx['manifest']['corpus_id'])
    with pytest.raises(RecordError, match='different question'):
        run(ctx, ctx['passages'], counts, ranking=rank(ctx, ctx['passages'], question_id='q:other'))
    refused = make_query(FINDING, 'Does this patient have cancer?')
    with pytest.raises(RecordError, match='refused query'):
        run(ctx, ctx['passages'], counts, query=refused,
            ranking=rank(ctx, ctx['passages'], query=refused))
    other = setup(max_chars=13, overlap=1)
    with pytest.raises(RecordError, match='different corpus'):
        run(ctx, ctx['passages'], counts, ranking=rank(other, other['passages']))
    reordered = deepcopy(ranking)
    reordered['items'].reverse()
    with pytest.raises(RecordError):
        run(ctx, ctx['passages'], counts, ranking=reordered)


def test_r3_counter_must_be_named_synthetic_or_fixture():
    ctx = setup()

    class Unlabelled:
        name, version, kind = 'model-tokenizer', 'tok-v1', 'model_tokenizer'
        calls = 0

        def count(self, text):
            Unlabelled.calls += 1
            return 1
    with pytest.raises(RecordError, match='counter must be'):
        run(ctx, ctx['passages'], Unlabelled())
    assert Unlabelled.calls == 0  # refused before any text reaches it (the schema is a second line)
