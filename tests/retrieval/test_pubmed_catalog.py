import gzip
import hashlib
import json
import pytest
from src.retrieval.pubmed_catalog import apply_file,bind,build,connect,events,search

def article(pmid,title='Pancreas CT',abstract='A synthetic abstract.'):
    return f'<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID>{pmid}</PMID><Article><ArticleTitle>{title}</ArticleTitle><Abstract><AbstractText Label="RESULTS">{abstract}</AbstractText></Abstract></Article><CommentsCorrectionsList><CommentsCorrections RefType="ErratumIn"><PMID>9</PMID></CommentsCorrections></CommentsCorrectionsList></MedlineCitation></PubmedArticle>'

def source(root,n,body,wrap=True):
    p=root/f'pubmed26n{n:04d}.xml.gz'
    p.write_bytes(gzip.compress((f'<PubmedArticleSet>{body}</PubmedArticleSet>' if wrap else body).encode()))
    return p,hashlib.sha256(p.read_bytes()).hexdigest()

def test_replacement_delete_resume_and_provenance(tmp_path):
    db=connect(tmp_path/'catalog.sqlite');bind(db,b'identity')
    a,ha=source(tmp_path,1,article(1)+article(2))
    b,hb=source(tmp_path,2,article(1,'Revised <i>pancreas</i> title')+'<DeleteCitation><PMID>2</PMID></DeleteCitation>')
    assert apply_file(db,a,ha,0)
    assert apply_file(db,b,hb,1)
    assert not apply_file(db,b,hb,1)
    db.close()
    rows=search(tmp_path/'catalog.sqlite','pancreas')
    assert len(rows)==1 and rows[0]['title']=='Revised pancreas title'
    assert rows[0]['source_sha256']==hb and rows[0]['source_seq']==0
    db=connect(tmp_path/'catalog.sqlite')
    assert 'CommentsCorrectionsList' in db.execute('SELECT xml FROM documents').fetchone()[0]
    db.close()

def test_bad_late_xml_rolls_back_entire_file(tmp_path):
    db=connect(tmp_path/'c');bind(db,b'x')
    a,h=source(tmp_path,1,article(1));apply_file(db,a,h,0)
    b,h=source(tmp_path,2,'<PubmedArticleSet>'+article(1,'Changed')+'<broken>',False)
    with pytest.raises(Exception): apply_file(db,b,h,1)
    assert db.execute('SELECT title FROM documents').fetchone()[0]=='Pancreas CT'
    assert db.execute('SELECT count(*) FROM applied').fetchone()[0]==1
    db.close()

@pytest.mark.parametrize('body',[
 '<!DOCTYPE PubmedArticleSet [<!ENTITY x "expanded">]><PubmedArticleSet/>',
 '<wrong/>', '<PubmedArticleSet><Unknown/></PubmedArticleSet>',
 '<PubmedArticleSet>'+article('abc')+'</PubmedArticleSet>',
 '<PubmedArticleSet><DeleteCitation/></PubmedArticleSet>',
])
def test_reject_unsafe_or_unsupported_xml(tmp_path,body):
    p,_=source(tmp_path,1,body,False)
    with pytest.raises(Exception): list(events(p))

def test_external_doctype_no_fetch_and_caps(tmp_path):
    p,_=source(tmp_path,1,'<!DOCTYPE PubmedArticleSet SYSTEM "https://invalid.example/dtd"><PubmedArticleSet>'+article(1)+'</PubmedArticleSet>',False)
    assert len(list(events(p)))==1
    with pytest.raises(ValueError): list(events(p,max_expanded=10))
    with pytest.raises(ValueError): list(events(p,max_record=10))
    with pytest.raises(TimeoutError): list(events(p,seconds=-1))

def test_gzip_corruption(tmp_path):
    p,_=source(tmp_path,1,article(1));p.write_bytes(p.read_bytes()[:-6])
    with pytest.raises(EOFError): list(events(p))

def test_identity_order_and_source_hash(tmp_path):
    db=connect(tmp_path/'c');bind(db,b'x')
    with pytest.raises(ValueError): bind(db,b'y')
    p,h=source(tmp_path,1,article(1))
    with pytest.raises(ValueError): apply_file(db,p,h,1)
    with pytest.raises(ValueError): apply_file(db,p,'0'*64,0)
    assert db.execute('SELECT count(*) FROM documents').fetchone()[0]==0
    db.close()

def test_manifest_receipts_and_incremental_build(tmp_path):
    root=tmp_path/'source';root.mkdir()
    a,ha=source(root,1,article(1));b,hb=source(root,2,article(2,'100% actual'))
    m={'version':'pubmed-raw-download-v1','files':[{'name':a.name},{'name':b.name}]}
    (root/'manifest.json').write_text(json.dumps(m))
    receipts=[{'name':p.name,'bytes':p.stat().st_size,'sha256':h} for p,h in ((a,ha),(b,hb))]
    (root/'receipts.jsonl').write_text('\n'.join(map(json.dumps,receipts)))
    out=tmp_path/'out.sqlite'
    assert build(root,out,1)['snapshot_replayed'] is False
    assert build(root,out,2)['snapshot_replayed'] is True
    assert build(root,out,2)['documents']==2
    assert len(search(out,'%'))==1
    assert search(out,"' OR 1=1 --")==[]
    receipts[1]['sha256']='0'*64
    (root/'receipts.jsonl').write_text('\n'.join(map(json.dumps,receipts)))
    with pytest.raises(ValueError): build(root,out,2)

def test_missing_receipt_and_preview_limit(tmp_path):
    root=tmp_path/'raw';root.mkdir()
    p,h=source(root,1,article(1))
    (root/'manifest.json').write_text(json.dumps({'version':'pubmed-raw-download-v1','files':[{'name':p.name}]}))
    (root/'receipts.jsonl').write_text('')
    with pytest.raises(ValueError,match='No verified'): build(root,tmp_path/'c',1)
    with pytest.raises(ValueError,match='1..10'): build(root,tmp_path/'c',11)

def test_single_writer_lock(tmp_path):
    import fcntl
    out=tmp_path/'c.sqlite'
    with out.with_suffix('.sqlite.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError): build(tmp_path,out,1)
