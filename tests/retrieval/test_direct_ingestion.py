import copy
import json
import math
import os
from pathlib import Path
import uuid
import pytest
from src.retrieval import direct_ingestion as d

XML='''<article article-type="review-article" xmlns:xlink="http://www.w3.org/1999/xlink"><front><article-meta>
<article-id pub-id-type="pmid">123</article-id><article-id pub-id-type="pmcid">PMC123</article-id>
<title-group><article-title>Test research</article-title></title-group><contrib-group><contrib><name><surname>Example</surname><given-names>A</given-names></name></contrib></contrib-group>
<permissions><copyright-statement>Test authors</copyright-statement><license><license-p><ext-link xlink:href="https://creativecommons.org/licenses/by/4.0/">CC BY</ext-link></license-p></license></permissions>
<abstract><p>Research methods are described here.</p></abstract></article-meta></front>
<body><sec><title>Methods</title><p>Pancreatic imaging research uses CT images. Results require independent evaluation.</p><fig><p>Excluded figure caption.</p></fig></sec></body></article>'''

@pytest.fixture
def bundle(tmp_path):
    p=tmp_path/'article.xml';p.write_text(XML)
    return d.source_bundle(p)


def vector(i=0):
    v=[0.0]*384;v[i]=1.0;return v


def batch(bundle):
    rows=list(d.source_passages(bundle))
    return d.frozen_batch(rows,[vector(i) for i in range(len(rows))],{'dimensions':384,'test':'invented'})


def test_traceable_passages_and_licence(bundle):
    rows=list(d.source_passages(bundle))
    assert len(rows)==2
    assert rows[0]['citation']['pmid']=='123'
    for row in rows:
        assert d.validate_row(row)==row
        p=row['passage'];assert row['text']==bundle['representation']['text'][p['start']:p['end']]
    assert 'Excluded figure' not in bundle['representation']['text']


@pytest.mark.parametrize('replacement',[
    XML.replace('https://creativecommons.org/licenses/by/4.0/','https://example.com/unknown'),
    XML.replace('review-article','retraction'),
    '<!DOCTYPE article [<!ENTITY x "oops">]>'+XML,
    XML.replace('<article-id pub-id-type="pmid">123</article-id>',''),
])
def test_bad_source_refused(tmp_path,replacement):
    p=tmp_path/'bad.xml';p.write_text(replacement)
    with pytest.raises(ValueError):d.source_bundle(p)


def test_source_and_artifact_tampering_refused(bundle):
    b=batch(bundle);b['items'][0]['record']['text']='tampered'
    with pytest.raises(ValueError):d.verify_batch(b)
    bundle['original_sections'][0]['paragraphs'][0]='tampered source'
    with pytest.raises(ValueError):list(d.source_passages(bundle))


@pytest.mark.parametrize('value',[float('nan'),float('inf'),0.5])
def test_bad_vector_refused(value):
    v=vector();v[0]=value
    with pytest.raises(ValueError):d.vector_values(v)


def test_duplicate_and_changed_checksum_refused(bundle):
    b=batch(bundle)
    b['items'][0]['vector_sha256']='bad'
    with pytest.raises(ValueError):d.verify_batch(b)
    row=list(d.source_passages(bundle))[0]
    with pytest.raises(ValueError,match='Duplicate'):d.frozen_batch([row,row],[vector(),vector()],{})


def test_write_once_preserves_existing(tmp_path):
    p=tmp_path/'batch.json';d.write_once(p,{'a':1});d.write_once(p,{'a':1})
    with pytest.raises(ValueError):d.write_once(p,{'a':2})
    assert json.loads(p.read_text())=={'a':1}


def test_long_sentence_preserves_all_text(tmp_path):
    p=tmp_path/'long.xml';p.write_text(XML.replace('Research methods are described here.','X'*1100))
    bundle=d.source_bundle(p)
    class FakeTokenizer:
        def encode(self,s,**kw):return list(range(len(s)+2))
    class FakeEncoder:
        tokenizer=FakeTokenizer();descriptor={'max_tokens':256}
    rows=list(d.encoder_passages(bundle,FakeEncoder()))
    parts=[r for r in rows if r['passage']['section_id']=='abstract-0']
    assert ''.join(r['text'] for r in parts)=='X'*1100
    assert all(len(r['text'])<=200 for r in parts)
    assert len({r['passage']['passage_id'] for r in rows})==len(rows)


@pytest.fixture
def live_db():
    config=os.environ.get('PROWL_TEST_INGESTION_CONFIG')
    if not config:pytest.skip('explicit dedicated integration config required')
    import importlib.util
    spec=importlib.util.spec_from_file_location('direct_cli',Path(__file__).resolve().parents[2]/'scripts/retrieval/direct_corpus.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    c=mod.read_config(config)
    with mod.connect(c) as db:
        d.initialize(db)
        yield db


def test_live_atomic_retry_and_exact_vectors(live_db,bundle):
    collection='test-'+uuid.uuid4().hex;b=batch(bundle)
    assert not d.load_batch(live_db,collection,b)['already_published']
    assert d.load_batch(live_db,collection,b)['already_published']
    assert live_db.execute('SELECT count(*) FROM literature.passages WHERE collection_id=%s',(collection,)).fetchone()[0]==2
    b2=copy.deepcopy(b);b2['encoder']['test']='different'
    b2=d.frozen_batch([x['record'] for x in b2['items']],[x['vector'] for x in b2['items']],b2['encoder'])
    with pytest.raises(ValueError,match='encoder'):d.load_batch(live_db,collection,b2)
    assert live_db.execute('SELECT count(*) FROM literature.batches WHERE collection_id=%s',(collection,)).fetchone()[0]==1


def test_live_failure_rolls_back_entire_batch(live_db,bundle):
    collection='test-'+uuid.uuid4().hex;b=batch(bundle)
    # Conflict discovered only after the first row has been inserted.
    b['items'][1]['record']['revision_id']='rev:'+'a'*64
    b=d.frozen_batch([x['record'] for x in b['items']],[x['vector'] for x in b['items']],b['encoder'])
    with pytest.raises(ValueError,match='revision'):d.load_batch(live_db,collection,b)
    assert live_db.execute('SELECT count(*) FROM literature.batches WHERE collection_id=%s',(collection,)).fetchone()[0]==0
    assert live_db.execute('SELECT count(*) FROM literature.passages WHERE collection_id=%s',(collection,)).fetchone()[0]==0


def test_live_query_encoder_isolation(live_db,bundle):
    collection='test-'+uuid.uuid4().hex;b=batch(bundle);d.load_batch(live_db,collection,b)
    class FakeEncoder:
        id=d.digest(b['encoder'])
        def encode(self,q):return [vector()]
    hits=d.search(live_db,collection,FakeEncoder(),'research',2)
    assert hits[0]['score']==pytest.approx(1)
    assert hits[0]['record']['passage']['passage_id']==b['items'][0]['record']['passage']['passage_id']
    FakeEncoder.id='wrong'
    with pytest.raises(ValueError,match='incompatible'):d.search(live_db,collection,FakeEncoder(),'research')


def test_partial_artifact_does_not_block_retry(tmp_path):
    p=tmp_path/'batch.json';partial=tmp_path/'batch.json.old.partial';partial.write_text('interrupted')
    d.write_once(p,{'a':1})
    assert json.loads(p.read_text())=={'a':1}
    assert partial.read_text()=='interrupted'


def test_live_retry_detects_database_vector_tamper(live_db,bundle):
    collection='test-'+uuid.uuid4().hex;b=batch(bundle);d.load_batch(live_db,collection,b)
    live_db.execute('UPDATE literature.passages SET embedding=%s::vector WHERE collection_id=%s AND passage_id=%s',
                    (d.vector_sql(vector(5)),collection,b['items'][0]['record']['passage']['passage_id']))
    with pytest.raises(ValueError,match='content mismatch'):d.load_batch(live_db,collection,b)


def test_coverage_accepts_exact_http_license_without_rewriting_source(tmp_path):
    raw = XML.replace('https://creativecommons.org/licenses/by/4.0/',
                      'http://creativecommons.org/licenses/by/4.0/')
    p = tmp_path / 'http-license.xml'; p.write_text(raw)
    b = d.source_bundle(p, profile='coverage-v1')
    assert b['source_sha256'] == d.hashlib.sha256(raw.encode()).hexdigest()
    assert b['citation']['license_url'] == d.LICENSE
    with pytest.raises(ValueError, match='licence'):
        d.source_bundle(p)


@pytest.mark.parametrize('url', [
    'http://creativecommons.org/licenses/by-nc/4.0/',
    'http://creativecommons.org/licenses/by/3.0/',
    'http://creativecommons.org.evil.test/licenses/by/4.0/',
    'http://creativecommons.org/licenses/by/4.0/?redirect=other',
])
def test_coverage_license_alias_does_not_broaden_rights(tmp_path, url):
    p = tmp_path / 'other-license.xml'; p.write_text(XML.replace(d.LICENSE, url))
    with pytest.raises(ValueError, match='licence'):
        d.source_bundle(p, profile='coverage-v1')


@pytest.mark.parametrize('declaration', [
    '<license xlink:href="http://creativecommons.org/licenses/by/4.0/">',
    '<license><ali:license_ref xmlns:ali="http://www.niso.org/schemas/ali/1.0/">https://creativecommons.org/licenses/by/4.0/</ali:license_ref>',
])
def test_coverage_publisher_license_locations(tmp_path, declaration):
    raw = XML.replace('<license>', declaration).replace(
        '<ext-link xlink:href="https://creativecommons.org/licenses/by/4.0/">CC BY</ext-link>', '')
    p = tmp_path / 'publisher.xml'; p.write_text(raw)
    assert d.source_bundle(p, profile='coverage-v1')['citation']['license_url'] == d.LICENSE
    p.write_text(raw.replace('/by/4.0/', '/by-nc/4.0/'))
    with pytest.raises(ValueError, match='licence'):
        d.source_bundle(p, profile='coverage-v1')


def test_license_in_body_does_not_grant_article_rights(tmp_path):
    raw = XML.replace('<permissions>', '<untrusted>').replace('</permissions>', '</untrusted>')
    p = tmp_path / 'not-permissions.xml'; p.write_text(raw)
    with pytest.raises(ValueError, match='licence'):
        d.source_bundle(p, profile='coverage-v1')
