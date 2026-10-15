"""Exact, request-local source spans; IDs are meaningful only with their catalog hash."""
import re

POLICY = 'source-spans-v1'
BOUNDARY = re.compile(r'''[.!?]["')\]]*(?=\s+[A-Z])''')
ABBREVIATION = re.compile(r'(?:\b(?:Dr|Mr|Ms|Prof|Fig|Figs|No|vs|al)|e\.g|i\.e|\b[A-Z])\.$')


def sentence_offsets(text):
    """Conservative boundaries, not a linguistic-completeness guarantee for truncated chunks."""
    cuts = [0]
    for match in BOUNDARY.finditer(text):
        if not ABBREVIATION.search(text[:match.end()]):
            cuts.append(match.end())
    cuts.append(len(text))
    result = []
    for start, end in zip(cuts, cuts[1:]):
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end-1].isspace():
            end -= 1
        if start < end:
            result.append((start, end))
    return result


def catalog(passages):
    """Offer contiguous ranges of up to three sentences; never combine different passages."""
    if len(passages) > 20:
        raise ValueError('Too many source passages')
    sources, spans, seen = [], {}, set()
    for index, hit in enumerate(passages, 1):
        record = hit['record']
        pid, text = record['passage']['passage_id'], record['text']
        if pid in seen:
            raise ValueError('Duplicate source passage')
        seen.add(pid)
        offsets = sentence_offsets(text)
        if len(offsets) > 20 or len(text) > 4000:
            raise ValueError('Source passage exceeds selection bounds')
        source = dict(source_id=f'P{index}', sentences=[
            dict(number=n, text=text[start:end]) for n, (start, end) in enumerate(offsets, 1)],
            selectable_spans=[])
        for first, (start, _) in enumerate(offsets):
            for last in range(first, min(first+3, len(offsets))):
                end = offsets[last][1]
                if 40 <= end-start <= 1600:
                    identifier = f'P{index}:{first+1}-{last+1}'
                    spans[identifier] = dict(passage_id=pid, start=start, end=end, quote=text[start:end])
                    source['selectable_spans'].append(identifier)
        sources.append(source)
    return sources, spans


def selection_schema(spans):
    if not spans:
        raise ValueError('No selectable spans')
    return {'type': 'object', 'additionalProperties': False, 'required': ['status', 'span_ids'],
            'properties': {'status': {'type': 'string', 'enum': ['excerpts', 'insufficient_evidence']},
                           'span_ids': {'type': 'array', 'maxItems': 3, 'uniqueItems': True,
                                        'items': {'type': 'string', 'enum': list(spans)}}}}


def resolve(selection, spans):
    """Validate again server-side even if the model ignores the constrained schema."""
    if not isinstance(selection, dict) or set(selection) != {'status', 'span_ids'}:
        raise ValueError('Invalid span selection')
    ids = selection['span_ids']
    if (not isinstance(ids, list) or len(ids) > 3 or any(not isinstance(i, str) for i in ids)
            or len(set(ids)) != len(ids) or any(i not in spans for i in ids)
            or selection['status'] not in ('excerpts', 'insufficient_evidence')
            or (selection['status'] == 'excerpts') != bool(ids)):
        raise ValueError('Invalid span IDs/status')
    return dict(status=selection['status'], extracts=[
        dict(passage_id=spans[i]['passage_id'], quote=spans[i]['quote']) for i in ids])
