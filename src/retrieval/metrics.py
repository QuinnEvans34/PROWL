"""Ranked retrieval metrics on supplied rankings (P3 synthetic scope).

OFFICIAL (D-085): recall@1/3/5/10 and reciprocal rank / MRR, at source level (comparable across
chunking) and passage level (comparable only within one chunking configuration, because the
number of relevant passages per question changes with chunking).

PROVISIONAL (proposal, not official): span-hit recall@k = the fraction of a question's distinct
direct spans completely contained in at least one top-k passage. Reported separately and labelled
``proposed_provisional_not_official``; never used for selection or release unless D-085 is amended.

Conventions:
* ``recall@k = |top_k ∩ gold| / |gold|``; gold is a set, so duplicates cannot inflate it.
* ``RR = 1 / rank of the first relevant item``, 0 if none appears in the ranking.
* ``k`` must be a positive ``int`` (``bool`` is rejected).
* An answerable question with empty gold is invalid. If no passage of a configuration fully
  contains any of a question's direct spans, its passage metrics are undefined for that
  configuration: it is excluded from passage means and counted in ``n_undefined``.
* Refusal questions are excluded from answerable
  means and counted separately. With no answerable questions every mean is ``None`` (JSON null)
  with ``undefined_reason``; never NaN and never a fabricated 0.
* Source ranking: map each passage to its work, keep the first occurrence, renumber 1..n.
* Depth: a ranking returns exactly ``min(50, eligible_count)`` items. ``eligible_count`` is persisted
  in the ranking and bound to the corpus under the P3 policy ``all_corpus_members`` (every member is
  eligible; no filtering exists in P3). ``eligible_pool_exhausted`` is set iff eligible_count < 50.
* Binding: every scored ranking is verified against its question, its accepted query record, the
  configuration and the corpus; every member passage and representation is re-verified (identity
  and exact slice) against the manifest before anything is scored. Question IDs must be unique.

Supplied rankings are fixture inputs, not the output of an implemented retriever. They cannot
demonstrate retrieval quality or G6 readiness.
"""
import math

from src.retrieval.labels import contains, direct_spans, gold_passages, gold_works, verify_label_set
from src.retrieval.passages import verify_passage, verify_representation
from src.retrieval.query import verify_query
from src.retrieval.records import (RecordError, SCHEMA_VERSION, canonical_bytes, sha256_hex,
                                   validate, verify_corpus_manifest)

OFFICIAL_KS = (1, 3, 5, 10)
TARGET_DEPTH = 50
ELIGIBILITY_POLICY = 'all_corpus_members'  # P3: unfiltered; production filtering is not invented here


def _check_k(k):
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise RecordError('k must be a positive integer (bool is not accepted)')


def _check_ranked(ranked_ids):
    if len(set(ranked_ids)) != len(ranked_ids):
        raise RecordError('ranking contains duplicate IDs')


def recall_at_k(ranked_ids, gold, k):
    _check_k(k)
    _check_ranked(ranked_ids)
    gold = set(gold)
    if not gold:
        raise RecordError('empty gold set: an answerable item needs at least one relevant ID')
    return len(set(ranked_ids[:k]) & gold) / len(gold)


def reciprocal_rank(ranked_ids, gold):
    _check_ranked(ranked_ids)
    gold = set(gold)
    if not gold:
        raise RecordError('empty gold set: an answerable item needs at least one relevant ID')
    for rank, item in enumerate(ranked_ids, start=1):
        if item in gold:
            return 1.0 / rank
    return 0.0


def mean_or_none(values):
    values = list(values)
    return (math.fsum(values) / len(values)) if values else None


def collapse_to_sources(ranked_passage_ids, passage_work):
    """First occurrence of each work, renumbered 1..n."""
    seen, out = set(), []
    for pid in ranked_passage_ids:
        work = passage_work[pid]
        if work not in seen:
            seen.add(work)
            out.append(work)
    return out


# --- supplied rankings ------------------------------------------------------------------------

def _strict_int(value, what):
    if type(value) is not int or value < 0:
        raise RecordError(f'{what} must be a non-negative integer (bool and float are not accepted)')


def _ranking_id(ranking):
    payload = {k: v for k, v in ranking.items() if k not in ('schema_version', 'ranking_id')}
    return 'rank:' + sha256_hex(canonical_bytes(payload))  # scores are finite floats here


def expected_depth(eligible_count):
    _strict_int(eligible_count, 'eligible_count')
    return min(TARGET_DEPTH, eligible_count)


def make_ranking(*, question_id, query_id, corpus_manifest, configuration_id, items,
                 score_direction='higher_is_better'):
    """Supplied (fixture) ranking bound to one corpus. The eligible count is derived from the corpus
    under ``all_corpus_members``, never taken from the caller. Order is taken from the supplied items
    and must already satisfy the tie policy (``verify_ranking`` checks it)."""
    verify_corpus_manifest(corpus_manifest)
    items = [dict(passage_id=i['passage_id'], score=i['score']) for i in items]
    _check_ranked([i['passage_id'] for i in items])
    eligible = len(corpus_manifest['members'])
    if len(items) != expected_depth(eligible):
        raise RecordError(f'a ranking must return min(50, eligible_count) = {expected_depth(eligible)} '
                          f'items, got {len(items)}')
    record = dict(schema_version=SCHEMA_VERSION, ranking_id=None, question_id=question_id, query_id=query_id,
                  corpus_id=corpus_manifest['corpus_id'], configuration_id=configuration_id,
                  score_direction=score_direction, tie_policy='score_then_passage_id',
                  target_depth=TARGET_DEPTH, eligibility_policy=ELIGIBILITY_POLICY, eligible_count=eligible,
                  items=items, result_count=len(items),
                  shortfall_reason='eligible_pool_exhausted' if eligible < TARGET_DEPTH else None)
    record['ranking_id'] = 'rank:' + '0' * 64
    validate('supplied-ranking', record)
    record['ranking_id'] = _ranking_id(record)
    return validate('supplied-ranking', record)


def verify_ranking(ranking, corpus_manifest, query, *, question_id=None, configuration_id=None):
    """Schema, identity, accepted-query binding, corpus binding, eligible count and depth,
    duplicates, membership and tie-policy order. ``query`` is required: a ranking is only valid for a
    query record the gate accepted (a refused query can never carry an evidence ranking). If
    ``question_id`` / ``configuration_id`` are given, the ranking must name exactly those."""
    validate('supplied-ranking', ranking)
    for field in ('eligible_count', 'result_count', 'target_depth'):
        _strict_int(ranking[field], field)
    verify_query(query)
    if ranking['query_id'] != query['query_id']:
        raise RecordError('ranking names a different query')
    if query['state'] != 'accepted':
        raise RecordError('a refused query cannot carry an evidence ranking')
    if question_id is not None and ranking['question_id'] != question_id:
        raise RecordError('ranking belongs to a different question')
    if configuration_id is not None and ranking['configuration_id'] != configuration_id:
        raise RecordError('ranking from a different configuration')
    verify_corpus_manifest(corpus_manifest)
    if _ranking_id(ranking) != ranking['ranking_id']:
        raise RecordError('ranking ID does not match its content')
    if ranking['corpus_id'] != corpus_manifest['corpus_id']:
        raise RecordError('ranking belongs to a different corpus (hard failure; IDs are never coerced)')
    ids = [i['passage_id'] for i in ranking['items']]
    _check_ranked(ids)
    members = {m['passage_id'] for m in corpus_manifest['members']}
    unknown = [pid for pid in ids if pid not in members]
    if unknown:
        raise RecordError(f'ranking contains {len(unknown)} passage(s) outside the corpus')
    if ranking['eligibility_policy'] != ELIGIBILITY_POLICY or ranking['eligible_count'] != len(members):
        raise RecordError('eligible_count does not match the corpus under all_corpus_members '
                          '(claimed pool exhaustion is not verifiable)')
    if ranking['result_count'] != len(ids):
        raise RecordError('result_count does not match items')
    if len(ids) != expected_depth(ranking['eligible_count']):
        raise RecordError('a ranking must return min(50, eligible_count) items')
    if (ranking['eligible_count'] < TARGET_DEPTH) != (ranking['shortfall_reason'] is not None):
        raise RecordError('shortfall_reason must be set exactly when the eligible pool is below 50')
    sign = -1 if ranking['score_direction'] == 'higher_is_better' else 1
    keys = [(sign * i['score'], i['passage_id']) for i in ranking['items']]
    if keys != sorted(keys):
        raise RecordError('items are not ordered by score then passage_id')
    return ranking


# --- verified inputs --------------------------------------------------------------------------

def verified_corpus_records(corpus_manifest, passages, representations):
    """Verify the manifest, every supplied representation, and every member passage (identity, exact
    hash-matching slice, section bounds) against its manifest entry. Returns ``(member_passages,
    representations_by_id)``. Non-member passage records are not used for scoring."""
    verify_corpus_manifest(corpus_manifest)
    rep_by_id = {}
    for rep in representations:
        verify_representation(rep)
        if rep['representation_id'] in rep_by_id:
            raise RecordError('duplicate representation record')
        rep_by_id[rep['representation_id']] = rep
    passage_by_id = {}
    for passage in passages:
        validate('passage', passage)
        if passage['passage_id'] in passage_by_id:
            raise RecordError('duplicate passage record')
        passage_by_id[passage['passage_id']] = passage
    members = {}
    for m in corpus_manifest['members']:
        passage = passage_by_id.get(m['passage_id'])
        if passage is None:
            raise RecordError('passage records missing for corpus members')
        rep = rep_by_id.get(m['representation_id'])
        if rep is None:
            raise RecordError('representation record missing for a corpus member')
        verify_passage(passage, rep)
        if (passage['text_sha256'], passage['representation_id'], passage['work_id']) != \
                (m['text_sha256'], m['representation_id'], m['work_id']):
            raise RecordError('passage record does not match its corpus member entry')
        members[m['passage_id']] = passage
    return members, rep_by_id


def _unique_question_ids(label_sets):
    ids = []
    for label_set in label_sets:
        validate('span-label', label_set)
        ids.append(label_set['question_id'])
    if len(set(ids)) != len(ids):
        raise RecordError('duplicate question_id in label sets (each question counts once)')
    return set(ids)


# --- evaluation -------------------------------------------------------------------------------

def _rates(per_question, key):
    return {str(k): mean_or_none(q[key][k] for q in per_question) for k in OFFICIAL_KS}


def evaluate(*, label_sets, rankings, queries, corpus_manifest, passages, representations, configuration_id,
             label_version):
    """Metric report for one configuration.

    ``rankings`` and ``queries`` map question_id -> supplied ranking / query record. Every ranking is
    verified against its label set's question, its accepted query, the configuration and the corpus;
    member passages and representations are verified before scoring. Rankings supplied for
    refusal-labelled questions are verified but not scored.
    """
    config_by_id, rep_by_id = verified_corpus_records(corpus_manifest, passages, representations)
    reps = list(rep_by_id.values())
    config_passages = [config_by_id[pid] for pid in sorted(config_by_id)]
    passage_work = {p['passage_id']: p['work_id'] for p in config_passages}
    question_ids = _unique_question_ids(label_sets)
    for name, mapping in (('ranking', rankings), ('query', queries)):
        stray = sorted(set(mapping) - question_ids)
        if stray:
            raise RecordError(f'{name} supplied for question(s) with no label set: {stray}')
    answerable, n_refusal, direct_total = [], 0, 0
    for label_set in label_sets:
        verify_label_set(label_set, reps)
        if label_set['label_version'] != label_version:
            raise RecordError('mixed label versions in one report')
        qid = label_set['question_id']
        ranking = rankings.get(qid)
        if ranking is None and label_set['answerable']:
            raise RecordError(f'no ranking supplied for answerable {qid}')
        if ranking is not None:
            if qid not in queries:
                raise RecordError(f'no query record supplied for {qid}')
            verify_ranking(ranking, corpus_manifest, queries[qid], question_id=qid,
                           configuration_id=configuration_id)
        if not label_set['answerable']:
            n_refusal += 1
            continue
        ids = [i['passage_id'] for i in ranking['items']]
        p_gold = gold_passages(config_passages, label_set)
        s_gold = gold_works(label_set, reps)
        sources = collapse_to_sources(ids, passage_work)
        spans = direct_spans(label_set)
        direct_total += len(spans)
        row = dict(question_id=qid,
                   passage_recall={k: recall_at_k(ids, p_gold, k) for k in OFFICIAL_KS} if p_gold else None,
                   passage_rr=reciprocal_rank(ids, p_gold) if p_gold else None,
                   source_recall={k: recall_at_k(sources, s_gold, k) for k in OFFICIAL_KS},
                   source_rr=reciprocal_rank(sources, s_gold),
                   span_hit={k: span_hit_recall(ids, config_by_id, spans, k) for k in OFFICIAL_KS})
        answerable.append(row)  # passage metrics may be undefined for this configuration (counted)
    none = {str(k): None for k in OFFICIAL_KS}
    defined = [q for q in answerable if q['passage_recall'] is not None]
    report = dict(
        schema_version=SCHEMA_VERSION, configuration_id=configuration_id,
        corpus_id=corpus_manifest['corpus_id'], label_version=label_version,
        official=dict(status='official_D-085', n_answerable=len(answerable), n_refusal_excluded=n_refusal,
                      undefined_reason=None if answerable else 'no_answerable_questions',
                      source=dict(recall_at=_rates(answerable, 'source_recall') if answerable else none,
                                  mrr=mean_or_none(q['source_rr'] for q in answerable)),
                      passage=dict(recall_at=_rates(defined, 'passage_recall') if defined else none,
                                   mrr=mean_or_none(q['passage_rr'] for q in defined),
                                   n_undefined=len(answerable) - len(defined),
                                   comparability='within_configuration_only')),
        provisional=dict(status='proposed_provisional_not_official',
                         span_hit_recall_at=_rates(answerable, 'span_hit') if answerable else none,
                         n_direct_spans=direct_total))
    validate('metric-result', report)
    canonical_bytes(report)  # strict JSON: no NaN
    return report


def span_hit_recall(ranked_ids, passage_by_id, spans, k):
    """PROVISIONAL. Distinct direct spans fully contained in >=1 top-k passage / distinct spans."""
    _check_k(k)
    _check_ranked(ranked_ids)
    if not spans:
        raise RecordError('no direct spans')
    top = [passage_by_id[pid] for pid in ranked_ids[:k]]
    hit = {(s['representation_id'], s['start'], s['end']) for s in spans if any(contains(p, s) for p in top)}
    return len(hit) / len({(s['representation_id'], s['start'], s['end']) for s in spans})
