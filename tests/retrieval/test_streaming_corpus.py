"""Differential, recovery and failure checks on invented records only."""
import gzip
import hashlib
import json
import sqlite3
import pytest
from src.retrieval import streaming_corpus as sc
from src.retrieval.topic_selection import select_records
from test_topic_selection import article,mesh,mesh_path,mesh_xml


def make_source(tmp_path,bodies):
    root=tmp_path/'source';root.mkdir()
    members=[];receipts=[]
    for i,body in enumerate(bodies,1):
        name=f'pubmed26n{i:04d}.xml.gz'
        data=gzip.compress(('<PubmedArticleSet>'+body+'</PubmedArticleSet>').encode())
        (root/name).write_bytes(data)
        members.append({'name':name})
        receipts.append({'name':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    (root/'manifest.json').write_text(json.dumps({'version':'pubmed-raw-download-v1','files':members}))
    (root/'receipts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in receipts))
    return root


def run_selection(tmp_path,root,mesh_path,**kwargs):
    catalog=tmp_path/'catalog'
    sc.replay(root,catalog,free_gib=0)
    out=tmp_path/'selection'
    result=sc.select(catalog/'catalog.sqlite',mesh_path,out,mesh_sha256=sc.sha256(mesh_path),cutoff_year=2026,free_gib=0,**kwargs)
    return result,out,catalog


def test_streaming_matches_preview_global_cap(tmp_path,mesh_path,mesh):
    # 505 workflow records, varying years and PMID lengths; deletions and re-addition.
    body=''.join(article('AI-assisted medical imaging',pmid=i,year=str(2000+i%26)) for i in range(1,506))
    body+=article(pmid=600)+article(pmid=601,lang='fra')
    body+='<PubmedBookArticle><BookDocument><PMID>602</PMID></BookDocument></PubmedBookArticle>'
    root=make_source(tmp_path,[body,'<DeleteCitation><PMID>3</PMID><PMID>999</PMID></DeleteCitation>'+article(pmid=600,title='Revised pancreas CT')])
    result,out,cat=run_selection(tmp_path,root,mesh_path)
    with sqlite3.connect(cat/'catalog.sqlite') as db:
        cols=('pmid','xml','deleted','source_file','source_sha256','source_seq')
        items=[dict(zip(cols,r)) for r in db.execute('SELECT pmid,xml,0,source_file,source_sha256,source_seq FROM documents UNION ALL SELECT pmid,xml,1,source_file,source_sha256,source_seq FROM deleted')]
    expected=select_records(items,mesh,cutoff_year=2026)
    assert result['counts']==expected['counts']
    assert result['candidate_pmids_sha256']==expected['candidate_pmids_sha256']
    assert [json.loads(l) for l in (out/'records.jsonl').read_text().splitlines()]==expected['rows']
    assert result['counts']['workflow_capped']==500
    assert result['counts']['workflow_uncapped']==504


def test_replay_resume_and_stop_rollback(tmp_path,monkeypatch):
    root=make_source(tmp_path,[article(pmid=1),article(pmid=1,title='Replacement')+''.join(article(pmid=i) for i in range(2,301))])
    out=tmp_path/'cat'
    assert sc.replay(root,out,through=1,free_gib=0)['documents']==1
    original=sc.apply_file
    def interrupted(*args,**kwargs):
        calls=0
        def stop():
            nonlocal calls
            calls+=1
            if calls==2: raise TimeoutError('injected after 256 writes')
        return original(*args,**dict(kwargs,check_resources=stop))
    monkeypatch.setattr(sc,'apply_file',interrupted)
    with pytest.raises(TimeoutError): sc.replay(root,out,free_gib=0)
    with sqlite3.connect(out/'catalog.sqlite') as db:
        assert db.execute('SELECT count(*) FROM applied').fetchone()[0]==1
        assert db.execute('SELECT title FROM documents').fetchone()[0]!='Replacement'
    monkeypatch.setattr(sc,'apply_file',original)
    assert sc.replay(root,out,free_gib=0)['documents']==300
    # Successful rerun skips committed files (no parser called).
    monkeypatch.setattr(sc,'apply_file',lambda *a,**k: pytest.fail('replayed committed file'))
    assert sc.replay(root,out,free_gib=0)['snapshot_replayed']


def test_failure_does_not_publish_summary(tmp_path,mesh_path,monkeypatch):
    root=make_source(tmp_path,[article()]);cat=tmp_path/'cat';sc.replay(root,cat,free_gib=0)
    def fail(*args,**kwargs): raise RuntimeError('injected evaluation failure')
    monkeypatch.setattr(sc,'evaluate',fail)
    with pytest.raises(RuntimeError): sc.select(cat/'catalog.sqlite',mesh_path,tmp_path/'out',mesh_sha256=sc.sha256(mesh_path),cutoff_year=2026,free_gib=0)
    assert not (tmp_path/'out/summary.json').exists()
    assert json.loads((tmp_path/'out/selection-status.json').read_text())['state']=='stopped'


def test_identity_and_completion_refusals(tmp_path,mesh_path):
    root=make_source(tmp_path,[article(),article(pmid=2)]);cat=tmp_path/'cat';sc.replay(root,cat,through=1,free_gib=0)
    with pytest.raises(ValueError,match='MeSH differs'): sc.select(cat/'catalog.sqlite',mesh_path,tmp_path/'badmesh',mesh_sha256='0'*64,cutoff_year=2026,free_gib=0)
    with pytest.raises(ValueError,match='Complete snapshot'): sc.select(cat/'catalog.sqlite',mesh_path,tmp_path/'prefix',mesh_sha256=sc.sha256(mesh_path),cutoff_year=2026,free_gib=0)
    report=json.loads((cat/'replay-status.json').read_text());report['snapshot_replayed']=True;sc.write_json(cat/'replay-status.json',report)
    with pytest.raises(ValueError,match='Inconsistent'): sc.select(cat/'catalog.sqlite',mesh_path,tmp_path/'forged',mesh_sha256=sc.sha256(mesh_path),cutoff_year=2026,free_gib=0)
    (root/'manifest.json').write_text((root/'manifest.json').read_text()+' ')
    with pytest.raises(ValueError,match='implementation or manifest'): sc.replay(root,cat,through=1,free_gib=0)


def test_receipt_and_disk_refusals(tmp_path):
    root=make_source(tmp_path,[article()]);p=root/'receipts.jsonl'
    row=json.loads(p.read_text());row['sha256']='0'*64;p.write_text(json.dumps(row)+'\n')
    with pytest.raises(ValueError,match='SHA256'): sc.replay(root,tmp_path/'hash',free_gib=0)
    with pytest.raises(OSError,match='Free-space'): sc.replay(root,tmp_path/'space',free_gib=10**9)


def test_more_than_preview_limit(tmp_path,mesh_path):
    body=''.join(article(pmid=i,title='Unrelated term') for i in range(1,10002))
    result,out,_=run_selection(tmp_path,make_source(tmp_path,[body]),mesh_path)
    assert result['counts']['universe']==10001
    assert sum(1 for _ in (out/'records.jsonl').open())==10001


def test_single_writer_and_missing_receipt(tmp_path):
    root=make_source(tmp_path,[article(),article(pmid=2)])
    out=tmp_path/'cat'
    with sc.locked(out):
        with pytest.raises(BlockingIOError): sc.replay(root,out,free_gib=0)
    receipt=root/'receipts.jsonl'
    receipt.write_text(receipt.read_text().splitlines()[0]+'\n')
    with pytest.raises(ValueError,match='Missing or invalid'): sc.replay(root,out,free_gib=0)
    assert not (out/'catalog.sqlite').exists()


def test_configured_file_timeout_is_forwarded(tmp_path,monkeypatch):
    root=make_source(tmp_path,[article()])
    original=sc.apply_file
    seen=[]
    def capture(*args,**kwargs):
        seen.append(kwargs['file_seconds'])
        return original(*args,**kwargs)
    monkeypatch.setattr(sc,'apply_file',capture)
    assert sc.replay(root,tmp_path/'cat',free_gib=0,file_seconds=3600)['snapshot_replayed']
    assert seen==[3600]
    with pytest.raises(ValueError,match='deadline'):
        sc.replay(root,tmp_path/'bad',free_gib=0,file_seconds=0)


def test_cache_setting_keeps_durability(tmp_path):
    db=sqlite3.connect(tmp_path/'settings.sqlite')
    budget=sc.Budget(tmp_path,free_gib=0)
    before=db.execute('PRAGMA synchronous').fetchone()[0]
    sc.tune(db,budget,cache_mib=4096)
    assert db.execute('PRAGMA cache_size').fetchone()[0]==-4096*1024
    assert db.execute('PRAGMA synchronous').fetchone()[0]==before
    assert db.execute('PRAGMA journal_mode').fetchone()[0]=='delete'
    with pytest.raises(ValueError): sc.tune(db,budget,cache_mib=0)
    db.close()
