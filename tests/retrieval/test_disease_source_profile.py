"""New source headings must not enter evidence or alter older representations."""
import pytest
from src.retrieval import direct_ingestion as d
from tests.retrieval.test_direct_ingestion import XML


@pytest.mark.parametrize('heading', sorted(d.DISEASE_ADMIN_SECTIONS - d.ADMIN_SECTIONS))
def test_new_administrative_sections_are_excluded_only_in_new_profile(tmp_path, heading):
    raw = XML.replace('</body>', f'<sec><title>{heading}</title><p>ADMIN_CANARY</p></sec></body>')
    p = tmp_path / 'article.xml'; p.write_text(raw)
    old = d.source_bundle(p, profile='coverage-v1')
    new = d.source_bundle(p, profile='disease-v1')
    assert 'ADMIN_CANARY' in old['representation']['text']
    assert 'ADMIN_CANARY' not in new['representation']['text']
    assert 'Pancreatic imaging research' in new['representation']['text']
    assert old['source_sha256'] == new['source_sha256']
    assert old['representation']['representation_id'] != new['representation']['representation_id']
    assert new['extraction_profile'] == 'disease-v1'
    assert all('ADMIN_CANARY' not in r['text'] for r in d.source_passages(new))


@pytest.mark.parametrize('url', [
    'https://creativecommons.org/licenses/by-nc/4.0/',
    'https://creativecommons.org/licenses/by-nc-nd/4.0/',
    'https://creativecommons.org.evil.test/licenses/by/4.0/',
])
def test_disease_profile_preserves_rights_restriction(tmp_path, url):
    p = tmp_path / 'article.xml'; p.write_text(XML.replace(d.LICENSE, url))
    with pytest.raises(ValueError, match='licence'):
        d.source_bundle(p, profile='disease-v1')


def test_disease_profile_preserves_entity_and_notice_refusals(tmp_path):
    p = tmp_path / 'article.xml'
    for raw in ['<!DOCTYPE article [<!ENTITY x "no">]>' + XML,
                XML.replace('review-article', 'retraction'),
                XML.replace('</article-meta>', '<related-article/></article-meta>')]:
        p.write_text(raw)
        with pytest.raises(ValueError): d.source_bundle(p, profile='disease-v1')


def test_disease_profile_keeps_medical_prose_but_not_embedded_figures(tmp_path):
    raw = XML.replace('Results require independent evaluation.',
        'Results require independent evaluation.<fig><p>FIGURE_CANARY</p></fig> Clinical limitations remain.')
    p = tmp_path / 'article.xml'; p.write_text(raw)
    new = d.source_bundle(p, profile='disease-v1')
    assert 'Clinical limitations remain.' in new['representation']['text']
    assert 'FIGURE_CANARY' not in new['representation']['text']
