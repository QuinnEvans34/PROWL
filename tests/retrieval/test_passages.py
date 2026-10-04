"""Normalization, offsets, representations and deterministic chunking (hand-computed oracles)."""
from copy import deepcopy
import re
import unicodedata

import pytest

from src.retrieval.passages import (PARAGRAPH_SEPARATOR, chunk_config, make_passages, make_representation,
                                    normalize_paragraph, passage_text, representation_identity,
                                    sentence_spans, to_original, verify_offset_map, verify_passage,
                                    verify_representation, verify_representation_source)
from src.retrieval.records import RecordError, sha256_hex

pytestmark = pytest.mark.unit
W = 'work:synthetic:x'
R = 'rev:' + 'a' * 64


def rep_of(*paragraph_lists):
    sections = [dict(section_id=f's{i}', title=f'Section {i}', paragraphs=list(ps))
                for i, ps in enumerate(paragraph_lists)]
    return make_representation(work_id=W, revision_id=R, kind='abstract', sections=sections)


def test_whitespace_collapse_and_offset_map_hand_checked():
    original = '  A  b c\n'
    text, omap = normalize_paragraph(original)
    assert text == 'A b c'
    # 'A' <- orig[2:3]; ' ' <- orig[3:5] (two spaces, 2->1); then 'b',' '(NBSP),'c' <- orig[5:8] are
    # each one-to-one and contiguous, so they merge into a single [2,5,5,8] segment.
    assert omap == [[0, 1, 2, 3], [1, 2, 3, 5], [2, 5, 5, 8]]
    assert to_original(omap, 0, 5) == (2, 8)
    assert to_original(omap, 2, 3) == (5, 6)


def test_nfc_composition_maps_back_to_original_cluster():
    original = 'Café ok'
    text, omap = normalize_paragraph(original)
    assert text == 'Café ok' and len(text) == 7
    assert to_original(omap, 3, 4) == (3, 5)  # composed é <- 'e' + combining acute
    assert original[slice(*to_original(omap, 0, 7))] == original


@pytest.mark.parametrize('bad', ['zero​width', 'bidi‮flip', 'bell\x07', '   ', ''])
def test_refused_characters_and_empty_paragraphs(bad):
    with pytest.raises(RecordError):
        normalize_paragraph(bad)


def test_cross_cluster_normalization_is_refused_not_mapped():
    jamo = '가'  # conjoining Hangul L + V compose across base-character clusters under NFC
    assert unicodedata.normalize('NFC', jamo) == '가'
    with pytest.raises(RecordError, match='cross'):
        normalize_paragraph(jamo)


def test_negation_and_wording_preserved():
    rep = rep_of(['The zorbel margin is not visible.'])
    assert rep['text'] == 'The zorbel margin is not visible.'


def test_representation_geometry_and_separator():
    rep = rep_of(['One.', 'Two.'], ['Three.'])
    assert rep['text'] == 'One.' + PARAGRAPH_SEPARATOR + 'Two.' + PARAGRAPH_SEPARATOR + 'Three.'
    assert [(p['start'], p['end']) for p in rep['paragraphs']] == [(0, 4), (6, 10), (12, 18)]
    assert [(s['start'], s['end']) for s in rep['sections']] == [(0, 10), (12, 18)]


@pytest.mark.failure_injection
def test_tampered_representation_rejected():
    rep = rep_of(['One. Two.'])
    for mutate in (lambda r: r.update(text=r['text'] + ' '),
                   lambda r: r['paragraphs'][0].update(end=r['paragraphs'][0]['end'] - 1),
                   lambda r: r['sections'][0].update(title='Changed'),
                   lambda r: r.update(normalization_version='prowl-norm-v2')):
        bad = deepcopy(rep)
        mutate(bad)
        with pytest.raises(RecordError):
            verify_representation(bad)


def test_sentence_split_hand_checked():
    rep = rep_of(['Alpha is here. beta stays. Gamma ends! "Quoted." Delta 2.5 values.'])
    got = [rep['text'][a:b] for _, a, b in sentence_spans(rep)]
    assert got == ['Alpha is here. beta stays.', 'Gamma ends!', '"Quoted."', 'Delta 2.5 values.']


def test_chunking_hand_checked_overlap_and_no_redundant_passages():
    # Sentences: [0,6) 'Aa bb.' [7,13) 'Cc dd.' [14,20) 'Ee ff.'
    rep = rep_of(['Aa bb. Cc dd. Ee ff.'])
    got = [(p['start'], p['end']) for p in make_passages(rep, chunk_config(max_chars=13, overlap_sentences=1))]
    assert got == [(0, 13), (7, 20)]
    got = [(p['start'], p['end']) for p in make_passages(rep, chunk_config(max_chars=6, overlap_sentences=1))]
    assert got == [(0, 6), (7, 13), (14, 20)]  # overlap would add nothing new, so no repeat


def test_oversized_sentence_kept_whole_and_flagged():
    rep = rep_of(['Short one. This sentence is much longer than the limit allows. End.'])
    passages = make_passages(rep, chunk_config(max_chars=15, overlap_sentences=0))
    texts = [(passage_text(p, rep), p['oversized']) for p in passages]
    assert texts == [('Short one.', False),
                     ('This sentence is much longer than the limit allows.', True), ('End.', False)]


def test_passages_never_cross_sections_and_slices_match():
    rep = rep_of(['A one. A two.'], ['B one.'])
    for p in make_passages(rep, chunk_config(max_chars=1000, overlap_sentences=1)):
        verify_passage(p, rep)
        section = next(s for s in rep['sections'] if s['section_id'] == p['section_id'])
        assert section['start'] <= p['start'] < p['end'] <= section['end']
    assert len(make_passages(rep, chunk_config(max_chars=1000))) == 2


@pytest.mark.failure_injection
def test_broken_offsets_or_stale_hash_rejected():
    rep = rep_of(['Aa bb. Cc dd.'])
    p = make_passages(rep, chunk_config(max_chars=6, overlap_sentences=0))[0]
    for mutate in (lambda q: q.update(end=q['end'] + 1), lambda q: q.update(start=q['start'] + 1),
                   lambda q: q.update(text_sha256='0' * 64),
                   lambda q: q.update(representation_sha256='0' * 64)):
        bad = deepcopy(p)
        mutate(bad)
        with pytest.raises(RecordError):
            verify_passage(bad, rep)
    changed = rep_of(['Aa bb. Cc de.'])
    with pytest.raises(RecordError):
        verify_passage(p, changed)


def test_chunking_config_validation_and_determinism():
    rep = rep_of(['Aa bb. Cc dd.'])
    assert make_passages(rep) == make_passages(deepcopy(rep))
    for bad in (dict(max_chars=0), dict(max_chars=True), dict(overlap_sentences=-1), dict(max_chars=2.5)):
        with pytest.raises(RecordError):
            chunk_config(**bad)
    a = make_passages(rep, chunk_config(max_chars=6))
    b = make_passages(rep, chunk_config(max_chars=7))
    assert a[0]['passage_id'] != b[0]['passage_id']  # chunking config is part of passage identity


def test_unicode_offsets_are_code_points():
    rep = rep_of(['Café \U0001F600 end.'])
    (p,) = make_passages(rep)
    assert passage_text(p, rep) == 'Café \U0001F600 end.'
    assert p['end'] == len('Café \U0001F600 end.') == 11


# --- Codex P3 review R4: offset maps and original-paragraph provenance ------------------------------

WS = '  A  b c\n'          # normalized 'A b c'; original length 9
WS_MAP = [[0, 1, 2, 3], [1, 2, 3, 5], [2, 5, 5, 8]]


def reidentify(rep):
    """Recompute the ID after a mutation, so the semantic checks are tested on their own."""
    rep['representation_id'] = representation_identity(rep)
    return rep


def ws_rep():
    rep = rep_of([WS])
    assert rep['paragraphs'][0]['offset_map'] == WS_MAP
    assert rep['paragraphs'][0]['original_length'] == len(WS) == 9
    assert rep['paragraphs'][0]['original_sha256'] == sha256_hex(WS)
    return rep


@pytest.mark.failure_injection
@pytest.mark.parametrize('mutate', [
    lambda p: p.update(offset_map=[[0, 1, 9000, 9001]]),          # the Codex probe
    lambda p: p.update(offset_map=[[0, 1, 1, 2], [1, 2, 2, 5], [2, 5, 5, 8]]),  # in-bounds shift
    lambda p: p.update(original_length=10),
    lambda p: p.update(original_sha256='0' * 64),
])
def test_r4_map_and_original_are_bound_into_identity(mutate):
    bad = ws_rep()
    mutate(bad['paragraphs'][0])
    with pytest.raises(RecordError, match='representation ID does not match'):
        verify_representation(bad)


@pytest.mark.failure_injection
@pytest.mark.parametrize('omap,original_length,message', [
    ([[0, 1, 9000, 9001]], 9, 'cover'),                                         # probe, re-identified
    ([[0, 1, 2, 3], [1, 2, 3, 5], [2, 5, 5, 9000]], 9, 'outside'),               # out of bounds
    (WS_MAP, 7, 'outside'),                                                      # original too short
    ([[0, 1, 2, 3], [2, 5, 5, 8]], 9, 'gap or overlap in normalized'),           # normalized gap
    ([[0, 1, 2, 3], [0, 2, 3, 5], [2, 5, 5, 8]], 9, 'gap or overlap in normalized'),  # normalized overlap
    ([[0, 1, 2, 3], [1, 2, 4, 5], [2, 5, 5, 8]], 9, 'original coordinates have a gap'),  # original gap
    ([[0, 1, 2, 4], [1, 2, 3, 5], [2, 5, 5, 8]], 9, 'original coordinates have a gap'),  # original overlap
    ([[0, 1, 2, 3], [1, 2, 3, 5], [2, 3, 5, 6], [3, 5, 6, 8]], 9, 'canonical'),  # unmerged one-to-one
    ([[0, 1, 2, 3], [1, 1, 3, 5], [1, 5, 5, 8]], 9, 'empty or inverted'),        # empty segment
    ([[0, 1, 3, 2], [1, 2, 3, 5], [2, 5, 5, 8]], 9, 'empty or inverted'),        # inverted segment
    ([[0, 1, 2, 3], [1, 5, 3, 8]], 9, 'more than one space or cluster'),       # 'b c' as one lump
])
def test_r4_forged_maps_rejected_even_when_reidentified(omap, original_length, message):
    bad = ws_rep()
    bad['paragraphs'][0].update(offset_map=omap, original_length=original_length)
    reidentify(bad)
    with pytest.raises(RecordError, match=message):
        verify_representation(bad)


def test_r4_structurally_valid_but_wrong_provenance_needs_source_check():
    sections = [dict(section_id='s0', title='Section 0', paragraphs=[WS])]
    rep = ws_rep()
    verify_representation_source(rep, sections)
    shifted = deepcopy(rep)
    shifted['paragraphs'][0]['offset_map'] = [[0, 1, 1, 2], [1, 2, 2, 5], [2, 5, 5, 8]]
    reidentify(shifted)
    verify_representation(shifted)  # coverage/order/bounds alone cannot see this
    with pytest.raises(RecordError, match='original paragraphs'):
        verify_representation_source(shifted, sections)
    other = reidentify(deepcopy(rep))
    other['paragraphs'][0]['original_sha256'] = sha256_hex('  A  b c\t')
    reidentify(other)
    with pytest.raises(RecordError, match='original paragraphs'):
        verify_representation_source(other, sections)
    with pytest.raises(RecordError, match='original paragraphs'):
        verify_representation_source(rep, [dict(section_id='s0', title='Section 0', paragraphs=[' A b c'])])


@pytest.mark.parametrize('original', ['Cafe\u0301 ok', ' \tLead and trail \n', 'a\u00a0\u2003b',
                                      'Emoji \U0001F600 x', 'x  \n\n  y', '\u00e9\u0301 stacked'])
def test_r4_unicode_and_whitespace_maps_verify_and_round_trip(original):
    rep = rep_of([original])
    para = rep['paragraphs'][0]
    assert para['original_length'] == len(original) and para['original_sha256'] == sha256_hex(original)
    verify_offset_map(para['offset_map'], rep['text'], len(original))
    verify_representation_source(rep, [dict(section_id='s0', title='Section 0', paragraphs=[original])])
    lo, hi = to_original(para['offset_map'], 0, len(rep['text']))
    assert unicodedata.normalize('NFC', ' '.join(original[lo:hi].split())) == rep['text']
    for norm_start, norm_end, orig_start, orig_end in para['offset_map']:
        piece = original[orig_start:orig_end]
        expected = unicodedata.normalize('NFC', re.sub(r'\s+', ' ', piece))
        assert rep['text'][norm_start:norm_end] == expected


@pytest.mark.failure_injection
def test_r4_paragraph_order_and_indices_checked():
    rep = rep_of(['One.', 'Two.'], ['Three.'])
    bad = deepcopy(rep)
    bad['paragraphs'][1]['index'] = 5
    with pytest.raises(RecordError, match='indices'):
        verify_representation(reidentify(bad))
    bad = deepcopy(rep)
    bad['paragraphs'][2]['section_id'] = 's0'
    with pytest.raises(RecordError):
        verify_representation(reidentify(bad))
