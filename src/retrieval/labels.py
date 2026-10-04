"""Span-based relevance labels (P3 synthetic scope; PHASES P7 rules).

A span is ``(representation_id, representation_sha256, start, end)``: half-open Unicode code
points in the immutable normalized representation text. A representation hash that no longer
matches invalidates the label (it must be remapped into a new label version, never carried over).

* Direct support requires a passage to contain a direct span **completely**. Partial overlap is
  partial evidence, never direct support.
* ``uncertain`` spans never enter the primary binary gold set.
* An answerable question needs at least one direct span. A refusal question (``answerable`` false)
  must carry no spans or required concepts.

Schema checks do not prove that a span semantically supports a concept or that it is minimal;
real labels need Quinton's authoring and adjudication (P7).
"""
from src.retrieval.records import RecordError, SCHEMA_VERSION, validate

GRADES_PRIMARY = ('direct',)


def make_label_set(*, question_id, label_version, answerable, required_concepts=(), spans=()):
    record = dict(schema_version=SCHEMA_VERSION, question_id=question_id, label_version=label_version,
                  answerable=answerable, required_concepts=list(required_concepts),
                  spans=[dict(s, concept_ids=list(s.get('concept_ids', ()))) for s in spans])
    return validate('span-label', record)


def verify_label_set(label_set, representations):
    """Schema, bounds, current representation hashes, and concept references. Raises RecordError."""
    validate('span-label', label_set)
    reps = {r['representation_id']: r for r in representations}
    concepts = set(label_set['required_concepts'])
    if len(concepts) != len(label_set['required_concepts']):
        raise RecordError('duplicate required concept')
    keys = set()
    for span in label_set['spans']:
        rep = reps.get(span['representation_id'])
        if rep is None:
            raise RecordError('label span names an unknown representation')
        if span['representation_sha256'] != rep['text_sha256']:
            raise RecordError('stale label: representation hash changed; remap into a new label version')
        if not 0 <= span['start'] < span['end'] <= len(rep['text']):
            raise RecordError('label span outside representation text')
        unknown = set(span['concept_ids']) - concepts
        if unknown:
            raise RecordError(f'label span references undeclared concepts {sorted(unknown)}')
        key = (span['representation_id'], span['start'], span['end'])
        if key in keys:
            raise RecordError('duplicate label span')
        keys.add(key)
    if label_set['answerable']:
        if not direct_spans(label_set):
            raise RecordError('answerable question has no direct span (invalid, not a perfect score)')
        if not concepts:
            raise RecordError('answerable question declares no required concepts')
    elif label_set['spans'] or label_set['required_concepts']:
        raise RecordError('refusal/unanswerable question must not carry spans or concepts')
    return label_set


def span_key(span):
    return (span['representation_id'], span['representation_sha256'], span['start'], span['end'])


def direct_spans(label_set):
    """Distinct direct spans (primary binary gold). Uncertain and partial grades are excluded."""
    return sorted({span_key(s): s for s in label_set['spans'] if s['grade'] in GRADES_PRIMARY}.values(),
                  key=span_key)


def contains(passage, span):
    """Complete containment in the same representation version."""
    return (passage['representation_id'] == span['representation_id']
            and passage['representation_sha256'] == span['representation_sha256']
            and passage['start'] <= span['start'] and span['end'] <= passage['end'])


def overlaps(passage, span):
    return (passage['representation_id'] == span['representation_id']
            and passage['representation_sha256'] == span['representation_sha256']
            and passage['start'] < span['end'] and span['start'] < passage['end'])


def passage_grade(passage, label_set):
    """'direct' | 'partial' | 'none' for one passage under one label set (configuration-specific)."""
    grade = 'none'
    for span in label_set['spans']:
        if span['grade'] == 'uncertain':
            continue
        if span['grade'] == 'direct' and contains(passage, span):
            return 'direct'
        if overlaps(passage, span):
            grade = 'partial'
    return grade


def gold_passages(passages, label_set):
    """Passage IDs of this configuration that completely contain at least one direct span."""
    spans = direct_spans(label_set)
    return {p['passage_id'] for p in passages if any(contains(p, s) for s in spans)}


def gold_works(label_set, representations):
    """Source-level gold: works owning at least one direct span."""
    reps = {r['representation_id']: r for r in representations}
    return {reps[s['representation_id']]['work_id'] for s in direct_spans(label_set)}
