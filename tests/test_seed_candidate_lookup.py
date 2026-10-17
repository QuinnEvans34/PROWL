import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('seeds',Path(__file__).resolve().parents[1]/'scripts/retrieval/verify_seed_candidates.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


def test_title_normalization():
    assert s.normalize('Ｍulti-atlas: CT')==s.normalize('multi atlas ct')


def test_venue_prefix_and_parentheses():
    c=dict(title='Example',year=2020,venue='The Diagnostics (Basel)')
    r=dict(title='EXAMPLE.',year=2021,venues=['Diagnostics'])
    assert s.citation_matches(c,r)
    r['year']=2022
    assert not s.citation_matches(c,r)
    r['year']=None
    assert s.citation_matches(c,r)
    r['venues']=['Other Diagnostics']
    assert not s.citation_matches(c,r)


def test_pinned_working_inventory():
    rows=s.candidates((Path(__file__).resolve().parents[1]/'docs/capstone/retrieval/planning/SEED-CANDIDATES.md').read_text())
    assert len(rows)==23
    assert sum(not r['conditional'] for r in rows)==21
    assert rows[0]['title'].startswith('Quality gaps')


def test_missing_inventory_refused():
    with pytest.raises(ValueError):s.candidates('')


def test_metadata_does_not_export_abstract():
    r=s.record('<PubmedArticle><MedlineCitation Status="MEDLINE"><Article><ArticleTitle>Example</ArticleTitle><Abstract><AbstractText>Not exported</AbstractText></Abstract><Journal><Title>Venue</Title><JournalIssue><PubDate><Year>2020</Year></PubDate></JournalIssue></Journal></Article><MeshHeadingList/></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.X/ABC</ArticleId></ArticleIdList></PubmedData></PubmedArticle>')
    assert not r['mesh_present']
    assert r['dois']==['10.x/abc']
    assert r['year']==2020
    assert 'abstract' not in str(r).lower()


def test_resume_matches_uninterrupted_with_rowid_gaps(tmp_path):
    import sqlite3
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE documents(pmid TEXT,title TEXT)')
    db.executemany('INSERT INTO documents(rowid,pmid,title) VALUES(?,?,?)',[(1,'11','Example'),(3,'13','Other'),(9,'19','Example'),(12,'22','Example')])
    initial=dict(identity={'input':'fixed'},last_rowid=0,records_scanned=0,matched={'S':[]})
    path=tmp_path/'checkpoint.json'
    def stop(state):
        s.atomic_json(path,state)
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):s.scan_titles(db,{'example':['S']},initial,stop,batch_size=2)
    resumed=s.scan_titles(db,{'example':['S']},s.load_checkpoint(path,initial['identity']),lambda state:None,batch_size=2)
    full=s.scan_titles(db,{'example':['S']},initial,lambda state:None,batch_size=2)
    assert resumed==full
    assert resumed['matched']['S']==['11','19','22']
    assert resumed['records_scanned']==4
    with pytest.raises(ValueError):s.load_checkpoint(path,{'input':'changed'})
