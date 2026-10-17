import hashlib
import pytest
from src.retrieval.direct_ingestion import source_bundle, JATS_HEADER
from tests.retrieval.test_direct_ingestion import XML


def test_known_header_is_not_loaded_and_original_identity_retained(tmp_path):
    raw=JATS_HEADER+b'\n'+XML.encode(); p=tmp_path/'source.xml';p.write_bytes(raw)
    with pytest.raises(ValueError): source_bundle(p)
    result=source_bundle(p,profile='coverage-v1')
    assert result['source_sha256']==hashlib.sha256(raw).hexdigest()
    assert result['extraction_profile']=='coverage-v1'
    assert result['citation']['pmid']=='123'


@pytest.mark.parametrize('header',[
    b'<!DOCTYPE article SYSTEM "https://example.com/evil.dtd">',
    b'<!DOCTYPE article [<!ENTITY x "boom">]>',
    JATS_HEADER+b'<!DOCTYPE article SYSTEM "file:///etc/passwd">',
    JATS_HEADER.replace(b'JATS-archivearticle1-4-mathml3.dtd',b'other.dtd'),
])
def test_other_dtd_and_entities_remain_refused(tmp_path,header):
    p=tmp_path/'source.xml';p.write_bytes(header+XML.encode())
    with pytest.raises(ValueError): source_bundle(p,profile='coverage-v1')


def test_profile_excludes_administration_preserves_protocol_appendix_and_legacy(tmp_path):
    extra='<sec><title>Author Contributions</title><p>Administrative names.</p></sec><sec><title>Data Availability Statement</title><p>Author contact.</p></sec><app><title>Protocol appendix</title><p>Specific annotation protocol.</p></app>'
    p=tmp_path/'source.xml';p.write_text(XML.replace('</body>',extra+'</body>'))
    old=source_bundle(p);new=source_bundle(p,profile='coverage-v1')
    assert 'Administrative names' in old['representation']['text']
    assert 'Administrative names' not in new['representation']['text']
    assert 'Author contact' not in new['representation']['text']
    assert 'Specific annotation protocol' in new['representation']['text']
    assert 'extraction_profile' not in old
    assert old['source_sha256']==new['source_sha256']


def test_embedded_nonprose_removed_without_losing_tail_or_inline_words(tmp_path):
    extra='<p>Before <italic>inline</italic> words.<fig><caption><p>Figure caption.</p></caption></fig> After figure.<table-wrap><p>Table cells.</p></table-wrap> Final words.</p>'
    p=tmp_path/'source.xml';p.write_text(XML.replace('</body>',extra+'</body>'))
    old=source_bundle(p);new=source_bundle(p,profile='coverage-v1')
    assert 'Figure caption.' in old['representation']['text']
    assert 'Figure caption.' not in new['representation']['text']
    assert 'Table cells.' not in new['representation']['text']
    assert 'Before inline words.' in new['representation']['text']
    assert 'After figure.' in new['representation']['text']
    assert 'Final words.' in new['representation']['text']
