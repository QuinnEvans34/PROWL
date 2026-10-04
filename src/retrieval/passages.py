"""Deterministic normalization, representations and passage construction (synthetic P3 scope).

Normalization ``prowl-norm-v1`` (per paragraph):
  1. Reject C0/C1 control characters other than whitespace, and format characters (category Cf,
     e.g. zero-width or bidi controls). They are refused, not silently removed.
  2. Unicode NFC, applied per base-character cluster (a base character plus following combining
     marks). If cluster-wise NFC differs from whole-paragraph NFC (for example conjoining Hangul
     jamo), the paragraph is rejected rather than given an inexact locator map.
  3. Every maximal run of whitespace (``str.isspace``) becomes one ASCII space; leading and trailing
     whitespace is dropped. No case folding, no punctuation change, no translation, no paraphrase.
Paragraphs join with ``\\n\\n`` inside a section and sections join the same way, so paragraph
boundaries stay visible and offsets stay exact.

Offsets are half-open ``[start, end)`` Unicode code-point indices into the normalized
representation text. Each paragraph keeps an ``offset_map`` of ``[norm_start, norm_end,
orig_start, orig_end]`` segments (paragraph-local) mapping normalized text back to the original,
plus the original paragraph's length (code points) and SHA-256. All three are part of the
representation identity, so source-coordinate provenance cannot change under an old ID.

A valid offset map (checked by ``verify_offset_map``) is canonical (``_merge_segments`` leaves it
unchanged) and: covers the normalized paragraph exactly, from 0 to its length, with no gap or
overlap; has non-empty segments; maps to original coordinates that are strictly increasing and
contiguous between segments (only leading/trailing whitespace may be left unmapped); stays
within ``[0, original_length]``; and uses a length-changing segment only for one collapsed space or
one NFC cluster. Structure alone cannot prove *which* original characters each
segment came from; ``verify_representation_source`` proves that by rebuilding from the original
paragraphs and requiring an exact match (their SHA-256 is bound into the identity).

Sentence splitting ``prowl-sent-v1``: a boundary follows ``.``, ``!`` or ``?`` (plus any closing
quote or bracket) when the next character is a single space followed by a character that is not a
lowercase letter. Abbreviations such as ``e.g. A`` can split early; that only moves chunk
boundaries, never text.

Chunking ``prowl-chunk-v1``: sentences are packed greedily, in order, within one section, up to
``max_chars`` code points measured on the exact slice (which includes paragraph separators).
A single sentence longer than ``max_chars`` becomes its own passage, flagged ``oversized``; it is
never split or truncated. ``overlap_sentences`` trailing sentences of one passage start the next,
but only when the next passage can still include at least one new sentence; otherwise the next
passage starts fresh. Every passage therefore adds new text. Passages never cross sections or works.
"""
import re
import unicodedata

from src.retrieval.records import (RecordError, SCHEMA_VERSION, identity_digest, sha256_hex,
                                   validate)

NORMALIZATION_VERSION = 'prowl-norm-v1'
SENTENCE_VERSION = 'prowl-sent-v1'
CHUNKING_VERSION = 'prowl-chunk-v1'
PARAGRAPH_SEPARATOR = '\n\n'
_BOUNDARY = re.compile(r'[.!?][\"\')\]]*(?= [^\s])')


# --- normalization ----------------------------------------------------------------------------

def _clusters(text):
    start = 0
    for i in range(1, len(text) + 1):
        if i == len(text) or unicodedata.combining(text[i]) == 0:
            yield start, i
            start = i


def normalize_paragraph(original):
    """Return (normalized_text, offset_map). Raises RecordError on refused input."""
    if not isinstance(original, str):
        raise RecordError('paragraph must be a string')
    for ch in original:
        cat = unicodedata.category(ch)
        if (cat == 'Cc' and not ch.isspace()) or cat == 'Cf':
            raise RecordError(f'refused character U+{ord(ch):04X} in paragraph')
    pieces = []  # (normalized_piece, orig_start, orig_end)
    for a, b in _clusters(original):
        pieces.append((unicodedata.normalize('NFC', original[a:b]), a, b))
    if ''.join(p for p, _, _ in pieces) != unicodedata.normalize('NFC', original):
        raise RecordError('normalization interaction across clusters is not supported (paragraph refused)')
    out, segments = [], []
    pending_space = None  # (orig_start, orig_end) of a whitespace run
    for piece, a, b in pieces:
        if piece.isspace():
            pending_space = (pending_space[0], b) if pending_space else (a, b)
            continue
        if pending_space and out:
            n = len(out)
            out.append(' ')
            segments.append([n, n + 1, pending_space[0], pending_space[1]])
        pending_space = None
        n = len(out)
        out.extend(piece)
        segments.append([n, n + len(piece), a, b])
    text = ''.join(out)
    if not text:
        raise RecordError('paragraph is empty after normalization')
    return text, _merge_segments(segments)


def _merge_segments(segments):
    merged = []
    for seg in segments:
        if merged:
            last = merged[-1]
            one_to_one = (last[1] - last[0] == last[3] - last[2]) and (seg[1] - seg[0] == seg[3] - seg[2])
            if one_to_one and last[1] == seg[0] and last[3] == seg[2]:
                last[1], last[3] = seg[1], seg[3]
                continue
        merged.append(list(seg))
    return merged


def to_original(offset_map, start, end):
    """Map a paragraph-local normalized [start, end) to the original paragraph [start, end)."""
    if not 0 <= start < end:
        raise RecordError('invalid normalized range')
    covering = [s for s in offset_map if s[0] < end and s[1] > start]
    if not covering or covering[0][0] > start or covering[-1][1] < end:
        raise RecordError('range outside the paragraph')
    first, last = covering[0], covering[-1]
    o_start = first[2] + (start - first[0]) if first[1] - first[0] == first[3] - first[2] else first[2]
    o_end = last[3] - (last[1] - end) if last[1] - last[0] == last[3] - last[2] else last[3]
    return o_start, o_end


# --- representations --------------------------------------------------------------------------

def make_representation(*, work_id, revision_id, kind, sections):
    """Build a representation from explicit sections: [{"section_id", "title", "paragraphs": [str]}]."""
    if not sections:
        raise RecordError('representation needs at least one section')
    parts, sec_records, para_records, cursor = [], [], [], 0
    seen_sections = set()
    for s_index, section in enumerate(sections):
        section_id = section['section_id']
        if section_id in seen_sections:
            raise RecordError(f'duplicate section_id {section_id}')
        seen_sections.add(section_id)
        paragraphs = section['paragraphs']
        if not paragraphs:
            raise RecordError(f'section {section_id} has no paragraphs')
        if s_index:
            parts.append(PARAGRAPH_SEPARATOR)
            cursor += len(PARAGRAPH_SEPARATOR)
        sec_start = cursor
        for p_index, original in enumerate(paragraphs):
            text, offset_map = normalize_paragraph(original)
            if p_index:
                parts.append(PARAGRAPH_SEPARATOR)
                cursor += len(PARAGRAPH_SEPARATOR)
            para_records.append(dict(section_id=section_id, index=p_index, start=cursor,
                                     end=cursor + len(text), original_length=len(original),
                                     original_sha256=sha256_hex(original), offset_map=offset_map))
            parts.append(text)
            cursor += len(text)
        sec_records.append(dict(section_id=section_id, title=section.get('title', ''), start=sec_start,
                                end=cursor))
    text = ''.join(parts)
    record = dict(schema_version=SCHEMA_VERSION, representation_id=None,
                  revision_id=revision_id, work_id=work_id, kind=kind,
                  normalization_version=NORMALIZATION_VERSION, text=text, text_sha256=sha256_hex(text),
                  sections=sec_records, paragraphs=para_records)
    record['representation_id'] = representation_identity(record)
    return verify_representation(record)


def representation_identity(rep):
    """ID over revision, kind, normalization version, text hash, section/paragraph geometry, and each
    paragraph's original length, original SHA-256 and offset map (source-coordinate provenance)."""
    structure = dict(sections=[[s['section_id'], s['title'], s['start'], s['end']] for s in rep['sections']],
                     paragraphs=[[p['section_id'], p['index'], p['start'], p['end'], p['original_length'],
                                  p['original_sha256'], p['offset_map']] for p in rep['paragraphs']])
    return 'repr:' + identity_digest(dict(revision_id=rep['revision_id'], kind=rep['kind'],
                                          normalization_version=rep['normalization_version'],
                                          text_sha256=rep['text_sha256'], structure=structure))


def verify_offset_map(offset_map, normalized_text, original_length):
    """Coverage, order, bounds and canonical form of one paragraph's offset map (see module doc).

    A segment whose normalized and original lengths differ can only come from a collapsed whitespace
    run (normalized to exactly one space) or from NFC of one base-character cluster, so its
    normalized text must be a single space or a single cluster.
    """
    normalized_length = len(normalized_text)
    if not offset_map:
        raise RecordError('offset map is empty')
    for seg in offset_map:
        if len(seg) != 4 or any(type(v) is not int for v in seg):
            raise RecordError('offset map segments must be four integers')
        if not (seg[0] < seg[1] and seg[2] < seg[3]):
            raise RecordError('offset map has an empty or inverted segment')
    if offset_map[0][0] != 0 or offset_map[-1][1] != normalized_length:
        raise RecordError('offset map does not cover the normalized paragraph exactly')
    for prev, seg in zip(offset_map, offset_map[1:]):
        if seg[0] != prev[1]:
            raise RecordError('offset map has a gap or overlap in normalized coordinates')
        if seg[2] != prev[3]:
            raise RecordError('offset map original coordinates have a gap, overlap or reversal')
    if offset_map[0][2] < 0 or offset_map[-1][3] > original_length:
        raise RecordError('offset map original coordinates outside the original paragraph')
    if _merge_segments(offset_map) != offset_map:
        raise RecordError('offset map is not in canonical merged form')
    for n0, n1, o0, o1 in offset_map:
        piece = normalized_text[n0:n1]
        if n1 - n0 != o1 - o0 and piece != ' ' and len(list(_clusters(piece))) != 1:
            raise RecordError('offset map merges more than one space or cluster into a length-changing segment')
    return offset_map


def verify_representation_source(rep, sections):
    """Full provenance check: rebuilding from the original ``sections`` must reproduce ``rep`` exactly
    (text, geometry, original hashes and offset maps). Use wherever the originals are available."""
    verify_representation(rep)
    rebuilt = make_representation(work_id=rep['work_id'], revision_id=rep['revision_id'], kind=rep['kind'],
                                  sections=sections)
    if rebuilt != rep:
        raise RecordError('representation does not match its original paragraphs')
    return rep


def verify_representation(rep):
    """Schema, text hash, identity, section/paragraph geometry and offset maps. Raises RecordError."""
    validate('representation', rep)
    if rep['normalization_version'] != NORMALIZATION_VERSION:
        raise RecordError('unsupported normalization version')
    if sha256_hex(rep['text']) != rep['text_sha256']:
        raise RecordError('representation text hash mismatch')
    if representation_identity(rep) != rep['representation_id']:
        raise RecordError('representation ID does not match its content')
    n = len(rep['text'])
    sections = {s['section_id']: s for s in rep['sections']}
    if len(sections) != len(rep['sections']):
        raise RecordError('duplicate section in representation')
    for s in rep['sections']:
        if not 0 <= s['start'] < s['end'] <= n:
            raise RecordError('section range outside text')
    for p in rep['paragraphs']:
        sec = sections.get(p['section_id'])
        if sec is None or not sec['start'] <= p['start'] < p['end'] <= sec['end']:
            raise RecordError('paragraph outside its section')
        piece = rep['text'][p['start']:p['end']]
        if normalize_paragraph(piece)[0] != piece:
            raise RecordError('paragraph text is not in normalized form')
        verify_offset_map(p['offset_map'], piece, p['original_length'])
    groups = []  # paragraphs must be in text order, grouped by section in section order
    for p in rep['paragraphs']:
        if groups and groups[-1][0] == p['section_id']:
            groups[-1][1].append(p)
        else:
            groups.append((p['section_id'], [p]))
    if [g[0] for g in groups] != [s['section_id'] for s in rep['sections']]:
        raise RecordError('paragraphs are not grouped by section in section order')
    for section_id, paras in groups:
        if [q['index'] for q in paras] != list(range(len(paras))):
            raise RecordError('paragraph indices are not 0..n-1 within their section')
        sec = sections[section_id]
        if (paras[0]['start'], paras[-1]['end']) != (sec['start'], sec['end']):
            raise RecordError('section range does not match its paragraphs')
    rebuilt, cursor = [], 0
    for p in rep['paragraphs']:
        if p['start'] != cursor + (len(PARAGRAPH_SEPARATOR) if rebuilt else 0):
            raise RecordError('paragraphs are not contiguous with the fixed separator')
        rebuilt.append(rep['text'][p['start']:p['end']])
        cursor = p['end']
    if PARAGRAPH_SEPARATOR.join(rebuilt) != rep['text']:
        raise RecordError('representation text does not match its paragraph structure')
    return rep


# --- sentences and chunking -------------------------------------------------------------------

def sentence_spans(rep):
    """Sentence spans [(section_id, start, end)] in representation coordinates, in text order."""
    spans = []
    for p in rep['paragraphs']:
        text = rep['text'][p['start']:p['end']]
        cut = 0
        for m in _BOUNDARY.finditer(text):
            nxt = m.end() + 1
            if nxt < len(text) and text[nxt].islower():
                continue
            spans.append((p['section_id'], p['start'] + cut, p['start'] + m.end()))
            cut = m.end() + 1
        if cut < len(text):
            spans.append((p['section_id'], p['start'] + cut, p['end']))
    return spans


def chunk_config(max_chars=1200, overlap_sentences=1):
    for name, value, low in (('max_chars', max_chars, 1), ('overlap_sentences', overlap_sentences, 0)):
        if isinstance(value, bool) or not isinstance(value, int) or value < low:
            raise RecordError(f'{name} must be an integer >= {low}')
    return dict(version=CHUNKING_VERSION, max_chars=max_chars, overlap_sentences=overlap_sentences)


def _passage_record(rep, section_id, start, end, config, ordinal, oversized):
    passage_id = 'psg:' + identity_digest(dict(representation_id=rep['representation_id'],
                                               representation_sha256=rep['text_sha256'],
                                               start=start, end=end, chunking=config))
    return validate('passage', dict(
        schema_version=SCHEMA_VERSION, passage_id=passage_id, representation_id=rep['representation_id'],
        representation_sha256=rep['text_sha256'], work_id=rep['work_id'], section_id=section_id,
        start=start, end=end, text_sha256=sha256_hex(rep['text'][start:end]), chunking=config,
        ordinal=ordinal, oversized=oversized))


def make_passages(rep, config=None):
    """Deterministic passages for one representation. See module docstring for the rules."""
    verify_representation(rep)
    config = config or chunk_config()
    chunk_config(config['max_chars'], config['overlap_sentences'])
    if config.get('version') != CHUNKING_VERSION:
        raise RecordError('unsupported chunking version')
    by_section = {}
    for sec_id, a, b in sentence_spans(rep):
        by_section.setdefault(sec_id, []).append((a, b))
    passages, ordinal = [], 0
    for section in rep['sections']:
        sents = by_section.get(section['section_id'], [])
        i = 0
        while i < len(sents):
            j = i + 1
            while j < len(sents) and sents[j][1] - sents[i][0] <= config['max_chars']:
                j += 1
            start, end = sents[i][0], sents[j - 1][1]
            oversized = (j - i == 1) and (end - start > config['max_chars'])
            passages.append(_passage_record(rep, section['section_id'], start, end, config, ordinal, oversized))
            ordinal += 1
            if j >= len(sents):
                break
            nxt = max(i + 1, j - config['overlap_sentences'])
            # Overlap only if the next passage can still add the first new sentence; a passage made
            # only of already-covered sentences would be redundant, so start fresh instead.
            if nxt < j and sents[j][1] - sents[nxt][0] > config['max_chars']:
                nxt = j
            i = nxt
    return passages


def passage_text(passage, rep):
    return rep['text'][passage['start']:passage['end']]


def verify_passage(passage, rep):
    """The passage must be an exact, hash-matching slice of this representation."""
    validate('passage', passage)
    if passage['representation_id'] != rep['representation_id']:
        raise RecordError('passage belongs to a different representation')
    if passage['representation_sha256'] != rep['text_sha256']:
        raise RecordError('passage refers to a stale representation hash')
    if not 0 <= passage['start'] < passage['end'] <= len(rep['text']):
        raise RecordError('passage offsets outside representation text')
    if sha256_hex(passage_text(passage, rep)) != passage['text_sha256']:
        raise RecordError('passage text hash does not match its slice')
    if passage['work_id'] != rep['work_id']:
        raise RecordError('passage work does not match its representation')
    section = next((s for s in rep['sections'] if s['section_id'] == passage['section_id']), None)
    if section is None or not section['start'] <= passage['start'] < passage['end'] <= section['end']:
        raise RecordError('passage crosses or leaves its section')
    expected = 'psg:' + identity_digest(dict(representation_id=rep['representation_id'],
                                             representation_sha256=rep['text_sha256'],
                                             start=passage['start'], end=passage['end'],
                                             chunking=passage['chunking']))
    if expected != passage['passage_id']:
        raise RecordError('passage ID does not match its content')
    return passage
