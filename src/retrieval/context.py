"""Delivered-evidence prototype under a context budget (PROPOSAL; P3 synthetic scope).

Status: ``proposed_provisional_not_official``. The 2,000-token budget is a provisional experimental
setting (D-265), not a product limit.

Packing rule ``prowl-pack-v1``: walk the ranked passages in order. Add each whole passage if its
token count fits the remaining budget. Otherwise skip it (never truncate it) and continue down the
list until the budget or the list runs out.

Token counting: only a named, versioned counter injected by the caller. ``SyntheticWordCounter``
counts whitespace-separated words and is labelled ``synthetic_counter``; it is **not** a model
tokenizer. Alternatively the caller passes validated fixture counts. Production use needs a pinned
reference or generator tokenizer and re-reporting (PHASES P7 part B). Counts must be positive
integers: a passage always has at least one character, so a zero, negative, bool or non-integer
count is rejected rather than treated as free.

Scoring: a direct span counts as delivered only if it is completely contained in a passage that was
actually packed. Spans in retrieved-but-skipped passages are not delivered. Spans and concepts are
counted once each, however many packed passages contain them.

Verified inputs only: the ranked passages are taken from a ranking verified against its question,
accepted query and corpus, and every member passage/representation is re-verified (identity and
exact slice) before packing, so forged offsets cannot add credit. A text counter only ever sees the
verified slice. Display is checked separately from indexing: a ranked passage whose rights do not
permit snippet display is skipped with ``display_not_permitted`` and never delivered.
"""
from src.retrieval.labels import contains, direct_spans, verify_label_set
from src.retrieval.metrics import verified_corpus_records, verify_ranking
from src.retrieval.passages import passage_text
from src.retrieval.records import (RecordError, SCHEMA_VERSION, canonical_bytes, may_display, validate,
                                   verify_rights)

PACKING_VERSION = 'prowl-pack-v1'
PROVISIONAL_BUDGET = 2000


class SyntheticWordCounter:
    name = 'synthetic-word-counter'
    version = 'synthetic-words-v1'
    kind = 'synthetic_counter'

    def count(self, text):
        return len(text.split())


class FixtureCounts:
    """Explicit, validated per-passage counts supplied by a test fixture."""
    name = 'fixture-counts'
    kind = 'fixture_counts'

    def __init__(self, counts, version='fixture-counts-v1'):
        self.counts = dict(counts)
        self.version = version

    def count_for(self, passage_id):
        if passage_id not in self.counts:
            raise RecordError(f'no fixture count for {passage_id}')
        return self.counts[passage_id]


def _positive_int(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RecordError(f'{what} must be a positive integer, got {value!r}')
    return value


def pack(ranked_ids, counts_by_id, budget):
    """Returns (selected_ids, skipped[{passage_id, tokens, reason}], delivered_tokens)."""
    _positive_int(budget, 'budget')
    if len(set(ranked_ids)) != len(ranked_ids):
        raise RecordError('ranking contains duplicate IDs')
    selected, skipped, used = [], [], 0
    for pid in ranked_ids:
        tokens = _positive_int(counts_by_id[pid], f'token count for {pid}')
        if used + tokens <= budget:
            selected.append(pid)
            used += tokens
        else:
            skipped.append(dict(passage_id=pid, tokens=tokens, reason='exceeds_remaining_budget'))
    return selected, skipped, used


def delivered_evidence(*, question_label_set, query, ranking, corpus_manifest, passages, representations,
                       rights, counter, budget=PROVISIONAL_BUDGET):
    """Context-result record for one answerable question, from verified records only.

    ``ranking`` must verify against ``query`` (accepted), ``corpus_manifest`` and the label set's
    question. ``passages``/``representations`` are re-verified against the manifest. ``rights`` must
    include the (identity-verified) decision named by each ranked member.
    """
    members, rep_by_id = verified_corpus_records(corpus_manifest, passages, representations)
    verify_label_set(question_label_set, list(rep_by_id.values()))
    if not question_label_set['answerable']:
        raise RecordError('delivered-evidence scoring applies to answerable questions only')
    verify_ranking(ranking, corpus_manifest, query, question_id=question_label_set['question_id'])
    rights_by_id = {}
    for decision in rights:
        verify_rights(decision)
        if decision['rights_id'] in rights_by_id:
            raise RecordError('duplicate rights record')
        rights_by_id[decision['rights_id']] = decision
    entry = {m['passage_id']: m for m in corpus_manifest['members']}
    ids = [i['passage_id'] for i in ranking['items']]
    displayable, skipped = [], []
    for pid in ids:
        decision = rights_by_id.get(entry[pid]['rights_id'])
        if decision is None or decision['representation_id'] != entry[pid]['representation_id']:
            raise RecordError('rights record missing or mismatched for a ranked passage (fail closed)')
        if may_display(decision):
            displayable.append(pid)
        else:
            skipped.append(dict(passage_id=pid, tokens=None, reason='display_not_permitted'))
    if isinstance(counter, FixtureCounts):
        counts = {pid: counter.count_for(pid) for pid in displayable}
    elif getattr(counter, 'kind', None) == 'synthetic_counter':
        counts = {pid: counter.count(passage_text(members[pid], rep_by_id[members[pid]['representation_id']]))
                  for pid in displayable}
    else:
        raise RecordError('counter must be FixtureCounts or a named synthetic_counter')
    selected, budget_skipped, used = pack(displayable, counts, budget)
    rank = {pid: i for i, pid in enumerate(ids)}
    skipped = sorted(skipped + budget_skipped, key=lambda item: rank[item['passage_id']])
    packed = [members[pid] for pid in selected]
    spans = direct_spans(question_label_set)
    delivered = [s for s in spans if any(contains(p, s) for p in packed)]
    required = set(question_label_set['required_concepts'])
    concepts = {c for s in delivered for c in s['concept_ids']} & required
    record = dict(
        schema_version=SCHEMA_VERSION, status='proposed_provisional_not_official',
        question_id=question_label_set['question_id'], query_id=query['query_id'],
        ranking_id=ranking['ranking_id'], corpus_id=corpus_manifest['corpus_id'],
        counter=dict(name=counter.name, version=counter.version, kind=counter.kind), budget=budget,
        selected=selected, skipped=skipped, delivered_tokens=used, n_direct_spans=len(spans),
        n_delivered_spans=len(delivered), delivered_span_recall=len(delivered) / len(spans),
        n_required_concepts=len(required), n_delivered_concepts=len(concepts),
        concept_coverage=len(concepts) / len(required))
    validate('context-result', record)
    canonical_bytes(record)
    return record
