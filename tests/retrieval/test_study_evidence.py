import copy
import json
import pytest
from src.retrieval import direct_ingestion as d, study_evidence as g, evidence_spans as s, span_answer
from src.retrieval.passages import _passage_record, chunk_config

TEXT = ('Alpha investigated EUS morphology using a CNN [1]. '
        'The Alpha cohort contained 43 participants with cystic lesions. '
        'The Alpha model reported accuracy of 99 percent. '
        'Beta investigated nCLE video frames using a CNN [2]. '
        'The Beta cohort contained 35 participants with cystic lesions. '
        'The Beta model reported accuracy of 82 percent.')
XML = '''<article xmlns:xlink="http://www.w3.org/1999/xlink"><front><article-meta>
<article-id pub-id-type="pmid">123</article-id><article-id pub-id-type="pmcid">PMC123</article-id>
<title-group><article-title>Invented evidence fixture</article-title></title-group>
<contrib-group><contrib><name><surname>Example</surname><given-names>A</given-names></name></contrib></contrib-group>
<permissions><license><ext-link xlink:href="https://creativecommons.org/licenses/by/4.0/">CC BY</ext-link></license></permissions>
</article-meta></front><body><sec><title>Studies</title><p>Earlier orientation paragraph with a different study.</p>
<p>TEXT</p></sec><sec><title>Other heading</title><p>Do not mix a different section.</p></sec></body></article>'''


@pytest.fixture
def data(tmp_path):
    path = tmp_path/'invented.xml'
    path.write_text(XML.replace('TEXT', TEXT))
    bundle = d.source_bundle(path)
    row = next(r for r in d.source_passages(bundle) if r['text'] == TEXT)
    passages = [dict(record=row)]
    spans = s.catalog(passages)[1]
    selection = dict(status='excerpts', span_ids=['P1:3-3'])
    base = dict(answer=s.resolve(selection, spans), selection=selection,
                provenance=dict(policy=span_answer.POLICY, span_catalog_sha256=d.digest(spans)),
                validation='exact_quotes_verified', model_called=True)
    source = g.packet(row, bundle, spans['P1:3-3'])
    return bundle, row, passages, base, source


def record():
    return dict(kind='study', unit=['S1','S2','S3'], study=['S1'], method=['S1'],
                cohort=['S2'], result=['S3'], explanation=[])


def install(monkeypatch, values, calls):
    values = iter(values)
    def api(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name=g.MODEL, digest=g.MODEL_SHA)])
        calls.append(payload)
        return dict(done=True, message=dict(content=json.dumps(next(values))))
    monkeypatch.setattr(g, 'api', api)


def test_parent_context_recovers_study_before_chunk_and_excludes_foreign_heading(data):
    bundle, row, _, _, source = data
    rep = bundle['representation']; a = TEXT.index('The Alpha model'); b = a+len(source['focus']['quote'])
    p = row['passage']
    narrow = dict(row, text=TEXT[a:b], passage=_passage_record(rep, p['section_id'], p['start']+a,
                  p['start']+b, chunk_config(), 0, False))
    focus = dict(passage_id=narrow['passage']['passage_id'], start=0, end=b-a, quote=narrow['text'])
    expanded = g.packet(narrow, bundle, focus)
    assert expanded == source  # identity depends on source occurrence, not chunk boundaries
    assert expanded['sentences']['S1']['text'].startswith('Alpha investigated')
    assert len(expanded['adjacent_context']) == 1
    resolved = g.resolve_record(record(), source)
    for facts in resolved['fields'].values():
        for fact in facts:
            assert rep['text'][fact['start']:fact['end']] == fact['text']


@pytest.mark.parametrize('change', ['foreign_field', 'missing_method', 'gapped_unit', 'wrong_occurrence', 'unknown_facts', 'kind_conflict'])
def test_structurally_unbound_evidence_refused(data, change):
    source = data[-1]; value = record()
    if change == 'foreign_field': value['cohort'] = ['S5']
    elif change == 'missing_method': value['method'] = []
    elif change == 'gapped_unit': value['unit'] = ['S1','S3']
    elif change == 'wrong_occurrence': value['unit'] = ['S4','S5','S6']
    elif change == 'unknown_facts': value['kind'] = 'unknown'
    else: value['kind'] = 'explanation'; value['explanation'] = ['S1']
    with pytest.raises(ValueError): g.resolve_record(value, source)


def test_changed_source_or_focus_refused(data):
    bundle, row, passages, base, source = data
    focus = s.catalog(passages)[1]['P1:3-3']
    tampered = copy.deepcopy(bundle)
    tampered['original_sections'][1]['paragraphs'][0] += ' Changed.'
    with pytest.raises(ValueError): g.packet(row, tampered, focus)
    with pytest.raises(ValueError, match='bundle identity'):
        g.packet(dict(row, source_sha256='0'*64), bundle, focus)
    with pytest.raises(ValueError, match='Focus offsets'):
        g.packet(row, bundle, dict(focus, start=0))


def test_extraction_has_no_question_and_cache_reused_for_different_questions(data, monkeypatch):
    bundle, _, passages, base, source = data
    calls = []; saved = []; cache = {}
    match = dict(intent='study', choices=['R1/P1:1-3'])
    install(monkeypatch, [record(), match, dict(intent='study',choices=[])], calls)
    bundles = {bundle['representation']['representation_id']: bundle}
    first = g.verify_answer('Alpha results?', passages, base, bundles, cache,
                            save_record=lambda *value: saved.append(value))
    second = g.verify_answer('Beta results?', passages, base, bundles, cache)
    assert len(calls) == 3 and len(saved) == 1
    extraction = json.loads(calls[0]['messages'][1]['content'])
    assert extraction == source and 'question' not in extraction
    assert first['answer']['extracts'][0]['quote'] == TEXT[:TEXT.index('Beta')].rstrip()
    assert first['evidence_records'][0]['reused'] is False
    assert second['evidence_records'][0]['reused'] is True
    assert second['answer']['extracts'] == []
    assert calls[1]['messages'][1]['content'] != calls[2]['messages'][1]['content']


def test_kind_mismatch_rejects_answer_and_cache_tampering_cannot_bypass(data, monkeypatch):
    bundle, _, passages, base, source = data
    bundles = {bundle['representation']['representation_id']: bundle}; calls = []; cache = {}
    install(monkeypatch, [record(), dict(intent='explanation',choices=['R1/P1:1-3'])], calls)
    result = g.verify_answer('Definition?', passages, base, bundles, cache)
    assert result['validation'] == 'generation_rejected' and result['answer']['extracts'] == []
    cache[source['packet_id']]['record']['fields']['method'][0]['text'] = 'Invented nCLE'
    result = g.verify_answer('nCLE?', passages, base, bundles, cache)
    assert result['validation'] == 'generation_rejected' and len(calls) == 2


def test_unknown_skips_matching_and_never_falls_back(data, monkeypatch):
    bundle, _, passages, base, _ = data
    calls = []
    install(monkeypatch, [dict(kind='unknown', unit=[], **{f: [] for f in g.FIELDS})], calls)
    result = g.verify_answer('Study?', passages, base, {bundle['representation']['representation_id']:bundle}, {})
    assert len(calls) == 1 and result['answer']['extracts'] == [] and result['match'] is None


def test_backend_failure_propagates_without_unchecked_answer(data, monkeypatch):
    bundle, _, passages, base, _ = data
    def api(path, payload=None):
        if path == 'tags': return dict(models=[dict(name=g.MODEL,digest=g.MODEL_SHA)])
        raise OSError('unavailable')
    monkeypatch.setattr(g, 'api', api)
    with pytest.raises(OSError):
        g.verify_answer('Study?', passages, base, {bundle['representation']['representation_id']:bundle}, {})


def test_matching_cannot_expand_outside_record_unit(data, monkeypatch):
    bundle, _, passages, base, _ = data
    narrow = dict(kind='study',unit=['S3'],study=['S3'],method=['S3'],cohort=[],result=['S3'],explanation=[])
    calls = []
    install(monkeypatch, [narrow, dict(intent='study', choices=['R1/P1:1-3'])], calls)
    result = g.verify_answer('Study?', passages, base, {bundle['representation']['representation_id']:bundle}, {})
    offered = calls[1]['format']['properties']['choices']['items']['enum']
    assert offered == ['R1/P1:3-3']
    assert result['validation'] == 'generation_rejected' and result['answer']['extracts'] == []


def test_repeated_sentence_cannot_rebind_evidence_unit(data):
    source = copy.deepcopy(data[-1])
    source['sentences']['S6']['text'] = source['sentences']['S3']['text']
    source['focus'] = dict(source['sentences']['S6'])
    source['focus']['quote'] = source['focus'].pop('text')
    with pytest.raises(ValueError, match='selected occurrence'):
        g.resolve_record(record(), source)
