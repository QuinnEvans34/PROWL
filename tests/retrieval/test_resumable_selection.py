"""Synthetic transactional evaluation tests; no external catalog access."""
import json
import sqlite3
import pytest
from src.retrieval import resumable_selection as rs
from src.retrieval import streaming_corpus as sc
from test_streaming_corpus import make_source
from test_topic_selection import article, mesh_path, mesh_xml


@pytest.fixture
def case(tmp_path, mesh_path):
    source = make_source(tmp_path, [article(pmid=1)+article(pmid=2)+article(pmid=3),
        '<DeleteCitation><PMID>2</PMID><PMID>900</PMID></DeleteCitation>'])
    catalog = tmp_path/'catalog'
    sc.replay(source, catalog, free_gib=0)
    evidence = tmp_path/'evidence.txt'; evidence.write_text('invented prerequisite evidence')
    packet = tmp_path/'packet.json'
    packet.write_text(json.dumps(dict(version='selection-admission-v1', evidence={
        k:dict(path=str(evidence), sha256=sc.sha256(evidence))
        for k in ('seed_freeze', 'information_needs', 'reserve_exposure')})))
    return dict(catalog=catalog/'catalog.sqlite', mesh_path=mesh_path, output=tmp_path/'out',
                receipts=source/'receipts.jsonl', packet_path=packet, volume_id='synthetic-volume',
                mesh_sha256=sc.sha256(mesh_path), cutoff_year=2026, free_gib=0, batch_size=1, evaluation_only=True)


def rows(path):
    with sqlite3.connect(path/'selection.sqlite') as db:
        return db.execute('SELECT pmid,source_table,source_rowid,body FROM rows ORDER BY pmid').fetchall()


def test_differential_and_completed_evaluation_idempotent(case, monkeypatch):
    cp = rs.run(**case)
    assert cp['stage']=='ranking' and cp['counts']==dict(documents=2, deleted=2)
    expected = case['output'].with_name('old')
    sc.select(case['catalog'], case['mesh_path'], expected,
              mesh_sha256=case['mesh_sha256'], cutoff_year=2026, free_gib=0)
    assert sorted([json.loads(r[3]) for r in rows(case['output'])],key=lambda r:r['pmid']) == sorted(
        [json.loads(line) for line in (expected/'records.jsonl').read_text().splitlines()],key=lambda r:r['pmid'])
    monkeypatch.setattr(rs, 'metadata', lambda *_: pytest.fail('committed XML reprocessed'))
    assert rs.run(**case, resume=True)==cp
    assert not (case['output']/'summary.json').exists()


def test_partial_batch_rollback_and_gapped_cursor(case, monkeypatch):
    original = rs.evaluate
    seen=[]
    def fail(record, *args, **kwargs):
        seen.append(kwargs['pmid'])
        if len(seen)==2: raise RuntimeError('injected midbatch')
        return original(record,*args,**kwargs)
    monkeypatch.setattr(rs,'evaluate',fail)
    with pytest.raises(RuntimeError): rs.run(**dict(case,batch_size=3))
    assert rows(case['output'])==[]
    monkeypatch.setattr(rs,'evaluate',original)
    rs.run(**case,resume=True)
    assert {r[0] for r in rows(case['output'])}=={'1','3','2','900'}


def test_committed_prefix_skipped(case, monkeypatch):
    original=rs.evaluate
    seen=[]
    def fail(record,*args,**kwargs):
        seen.append(kwargs['pmid'])
        if len(seen)==2: raise KeyboardInterrupt('transport')
        return original(record,*args,**kwargs)
    monkeypatch.setattr(rs,'evaluate',fail)
    with pytest.raises(KeyboardInterrupt): rs.run(**case)
    assert len(rows(case['output']))==1
    seen.clear()
    def capture(record,*args,**kwargs):
        seen.append(kwargs['pmid']); return original(record,*args,**kwargs)
    monkeypatch.setattr(rs,'evaluate',capture)
    rs.run(**case,resume=True)
    assert '1' not in seen and len(seen)==3


@pytest.mark.parametrize('field,value', [('cutoff_year',2025),('volume_id','wrong')])
def test_identity_refuses(case,field,value):
    rs.run(**case)
    with pytest.raises(ValueError,match='identity mismatch'):
        rs.run(**dict(case,**{field:value}),resume=True)


def test_source_mutation_refuses(case):
    rs.run(**case)
    with sqlite3.connect(case['catalog']) as db:
        db.execute("UPDATE documents SET title='changed'")
    with pytest.raises(ValueError,match='identity mismatch'): rs.run(**case,resume=True)


def test_checkpoint_tamper_refuses(case):
    rs.run(**case)
    with sqlite3.connect(case['output']/'selection.sqlite') as db:
        cp=rs.checkpoint(db); cp['cursors']['documents']=100
        db.execute('UPDATE checkpoint SET body=?',(json.dumps(cp),))
    with pytest.raises(ValueError,match='Checkpoint/ledger'): rs.run(**case,resume=True)


def test_lock_refusals(case):
    with sc.locked(case['catalog'].parent):
        with pytest.raises(BlockingIOError): rs.run(**case)
    assert not case['output'].exists()
    rs.run(**case)
    with sc.locked(case['output']):
        with pytest.raises(BlockingIOError): rs.run(**case,resume=True)


def test_receipt_refuses(case):
    data=case['receipts'].read_text().replace('"sha256": "','"sha256": "bad')
    case['receipts'].write_text(data)
    with pytest.raises(ValueError,match='ledger and receipts'): rs.run(**case)


def test_space_and_foreign_output_refuse(case):
    with pytest.raises(OSError,match='Free-space'): rs.run(**dict(case,free_gib=10**9))
    with pytest.raises(ValueError,match='ledger missing'): rs.run(**case,resume=True)


def test_empty_tables(case):
    with sqlite3.connect(case['catalog']) as db:
        db.execute('DELETE FROM documents'); db.execute('DELETE FROM deleted')
    report_path=case['catalog'].parent/'replay-status.json'
    report=json.loads(report_path.read_text()); report.update(documents=0,deleted_pmids=0)
    report_path.write_text(json.dumps(report))
    cp=rs.run(**case)
    assert cp['stage']=='ranking' and cp['counts']==dict(documents=0,deleted=0)
    assert rs.run(**case,resume=True)==cp


def test_commit_then_status_failure_recovers(case,monkeypatch):
    original=rs.write_json
    def fail(path, value):
        if value.get('state') == 'evaluating_documents':
            raise OSError('disk status failure')
        return original(path, value)
    monkeypatch.setattr(rs,'write_json',fail)
    with pytest.raises(OSError): rs.run(**case)
    assert len(rows(case['output']))==1
    monkeypatch.setattr(rs,'write_json',original)
    assert rs.run(**case,resume=True)['stage']=='ranking'


def test_table_transition_commit_survives(case,monkeypatch):
    original=rs.save
    def fail_after_commit(db,cp):
        original(db,cp)
        if cp['stage']=='evaluating_deleted': raise RuntimeError('after stage commit')
    monkeypatch.setattr(rs,'save',fail_after_commit)
    with pytest.raises(RuntimeError): rs.run(**case)
    monkeypatch.setattr(rs,'save',original)
    original_eval=rs.evaluate
    def only_deleted(*args,**kwargs):
        assert kwargs['deleted']; return original_eval(*args,**kwargs)
    monkeypatch.setattr(rs,'evaluate',only_deleted)
    assert rs.run(**case,resume=True)['stage']=='ranking'


def test_float_budget_and_durability(case):
    rs.run(**dict(case,max_gib=1.0))
    with sqlite3.connect(case['output']/'selection.sqlite') as db:
        assert db.execute('PRAGMA journal_mode').fetchone()[0]=='delete'
        assert db.execute('PRAGMA synchronous').fetchone()[0]==2


def test_malformed_record_stops_without_skip(case):
    with sqlite3.connect(case['catalog']) as db:
        db.execute("UPDATE documents SET xml='<broken' WHERE pmid='3'")
    with pytest.raises(Exception): rs.run(**case)
    assert [r[0] for r in rows(case['output'])]==['1']
    with pytest.raises(Exception): rs.run(**case,resume=True)
    assert [r[0] for r in rows(case['output'])]==['1']


def test_evidence_change_refuses(case):
    rs.run(**case)
    evidence=json.loads(case['packet_path'].read_text())['evidence']['seed_freeze']
    from pathlib import Path
    Path(evidence['path']).write_text('changed')
    with pytest.raises(ValueError,match='evidence mismatch'): rs.run(**case,resume=True)


def test_symlink_refused(case):
    alias=case['catalog'].with_name('alias.sqlite'); alias.symlink_to(case['catalog'])
    with pytest.raises(ValueError,match='Symlink'): rs.run(**dict(case,catalog=alias))


def test_deadline_cause_preserved(case,monkeypatch):
    original=rs.SelectionBudget.check
    calls=0
    def check(self,*a,**k):
        nonlocal calls
        calls+=1
        if calls>2: raise TimeoutError('injected deadline')
        return original(self,*a,**k)
    monkeypatch.setattr(rs.SelectionBudget,'check',check)
    with pytest.raises(TimeoutError): rs.run(**case)
    status=json.loads((case['output']/'selection-status.json').read_text())
    assert status['error_type']=='TimeoutError'


@pytest.mark.parametrize('field', ['hours','max_gib','free_gib'])
def test_nonfinite_limits(case,field):
    with pytest.raises(ValueError,match='Nonfinite'): rs.run(**dict(case,**{field:float('nan')}))


def test_cli_help_is_explicit():
    import subprocess
    import sys
    result=subprocess.run([sys.executable,str(rs.ROOT/'scripts/retrieval/select_pubmed_corpus.py'),'--help'],capture_output=True,text=True)
    assert result.returncode==0
    assert 'global ranking' in ' '.join(result.stdout.split())
    assert '--resume' in result.stdout and '--expected-volume-uuid' in result.stdout


def full(case):
    return dict(case,evaluation_only=False)


@pytest.mark.parametrize('workers',[1,4])
def test_full_ranking_byte_equivalence(case,workers):
    # Enlarge the invented catalog before binding: cap, ties, huge PMIDs and a book.
    with sqlite3.connect(case['catalog']) as db:
        template=db.execute('SELECT source_file,source_sha256,source_seq FROM documents LIMIT 1').fetchone()
        for i in range(10,520):
            db.execute('INSERT INTO documents(pmid,xml,source_file,source_sha256,source_seq) VALUES (?,?,?,?,?)',
                       (str(i),article('AI-assisted medical imaging',pmid=i,year=str(2000+i%26)),*template))
        for pmid,xml in [('999999999999999999999999999',article(pmid='999999999999999999999999999')),
                         ('600','<PubmedBookArticle><BookDocument><PMID>600</PMID></BookDocument></PubmedBookArticle>')]:
            db.execute('INSERT INTO documents(pmid,xml,source_file,source_sha256,source_seq) VALUES (?,?,?,?,?)',(pmid,xml,*template))
    report_path=case['catalog'].parent/'replay-status.json'
    report=json.loads(report_path.read_text());report['documents']=514
    report_path.write_text(json.dumps(report))
    expected=case['output'].with_name('reference')
    reference=sc.select(case['catalog'],case['mesh_path'],expected,mesh_sha256=case['mesh_sha256'],cutoff_year=2026,free_gib=0)
    result=rs.run(**dict(full(case),workers=workers))
    assert result['counts']==reference['counts']
    assert result['counts']['workflow_capped']==500
    for name in ('records.jsonl','candidate-pmids.txt'):
        assert (case['output']/name).read_bytes()==(expected/name).read_bytes()
    assert rs.run(**full(case),resume=True)==result


def test_partial_export_restarts_without_xml(case,monkeypatch):
    original=rs.record_bytes
    calls=0
    def fail(row):
        nonlocal calls
        calls+=1
        if calls==2: raise OSError('injected export failure')
        return original(row)
    monkeypatch.setattr(rs,'record_bytes',fail)
    with pytest.raises(OSError): rs.run(**full(case))
    assert not (case['output']/'summary.json').exists()
    old=(case['output']/'attempts/1/records.jsonl.partial').read_bytes()
    monkeypatch.setattr(rs,'record_bytes',original)
    monkeypatch.setattr(rs,'metadata',lambda *_: pytest.fail('reparsed XML'))
    result=rs.run(**full(case),resume=True)
    assert result['export_attempt']==2
    assert (case['output']/'attempts/1/records.jsonl.partial').read_bytes()==old


@pytest.mark.parametrize('where',['candidate-pmids.txt','summary.json'])
def test_publication_rename_fault_recovers(case,monkeypatch,where):
    original=rs.os.replace
    def fail(src,dst):
        if str(dst).endswith('/'+where): raise OSError('injected rename failure')
        original(src,dst)
    monkeypatch.setattr(rs.os,'replace',fail)
    with pytest.raises(OSError): rs.run(**full(case))
    assert not (case['output']/'summary.json').exists()
    monkeypatch.setattr(rs.os,'replace',original)
    monkeypatch.setattr(rs,'metadata',lambda *_: pytest.fail('reparsed XML'))
    result=rs.run(**full(case),resume=True)
    assert result['export_attempt']==1
    assert json.loads((case['output']/'summary.json').read_text())==result


def test_summary_published_before_checkpoint_recovers(case,monkeypatch):
    original=rs.save
    def fail(db,cp):
        if cp['stage']=='complete': raise RuntimeError('before completion checkpoint')
        original(db,cp)
    monkeypatch.setattr(rs,'save',fail)
    with pytest.raises(RuntimeError): rs.run(**full(case))
    summary=(case['output']/'summary.json').read_bytes()
    monkeypatch.setattr(rs,'save',original)
    rs.run(**full(case),resume=True)
    assert (case['output']/'summary.json').read_bytes()==summary


@pytest.mark.parametrize('name',['records.jsonl','candidate-pmids.txt','summary.json'])
def test_completed_tamper_refused(case,name):
    rs.run(**full(case))
    path=case['output']/name
    if name=='summary.json':
        data=json.loads(path.read_text());data['rights_qualified']=True;path.write_text(json.dumps(data))
    else: path.write_bytes(path.read_bytes()+b'x')
    with pytest.raises(ValueError): rs.run(**full(case),resume=True)


def test_rank_transaction_failure_recovers(case,monkeypatch):
    original=rs.save
    def fail(db,cp):
        if cp['stage']=='exporting': raise RuntimeError('rank not committed')
        original(db,cp)
    monkeypatch.setattr(rs,'save',fail)
    with pytest.raises(RuntimeError): rs.run(**full(case))
    with sqlite3.connect(case['output']/'selection.sqlite') as db:
        assert rs.checkpoint(db)['stage']=='ranking'
        assert db.execute('SELECT count(*) FROM winners').fetchone()[0]==0
    monkeypatch.setattr(rs,'save',original)
    rs.run(**full(case),resume=True)


def test_verify_tamper_before_publish_refused(case,monkeypatch):
    original=rs.verify_exports
    def tamper(db,receipt,folder,budget):
        path=folder/'attempts/1/records.jsonl.partial';path.write_bytes(b'broken')
        return original(db,receipt,folder,budget)
    monkeypatch.setattr(rs,'verify_exports',tamper)
    with pytest.raises(ValueError): rs.run(**full(case))
    assert not (case['output']/'summary.json').exists()


def test_nested_attempts_count_against_budget(tmp_path):
    nested=tmp_path/'attempts/1';nested.mkdir(parents=True)
    (nested/'partial').write_bytes(b'x'*2048)
    with pytest.raises(OSError,match='directory budget'):
        rs.SelectionBudget(tmp_path,max_gib=1024/(1024**3),free_gib=0)


def test_final_source_recheck_refuses_changed_receipt(case,monkeypatch):
    original=rs.verify_exports
    def change_after_verification(*args,**kwargs):
        result=original(*args,**kwargs)
        case['receipts'].write_text(' '+case['receipts'].read_text())
        return result
    monkeypatch.setattr(rs,'verify_exports',change_after_verification)
    with pytest.raises(ValueError,match='identity changed'): rs.run(**full(case))
    assert not (case['output']/'summary.json').exists()


def test_full_empty_exports(case):
    with sqlite3.connect(case['catalog']) as db:
        db.execute('DELETE FROM documents'); db.execute('DELETE FROM deleted')
    report_path=case['catalog'].parent/'replay-status.json'
    report=json.loads(report_path.read_text());report.update(documents=0,deleted_pmids=0)
    report_path.write_text(json.dumps(report))
    result=rs.run(**full(case))
    assert result['counts']['universe']==0
    assert (case['output']/'records.jsonl').read_bytes()==b''
    assert rs.run(**full(case),resume=True)==result


def test_saved_winners_tamper_refused(case,monkeypatch):
    original=rs.export_attempt
    monkeypatch.setattr(rs,'export_attempt',lambda *a,**k: (_ for _ in ()).throw(RuntimeError('stop after rank')))
    with pytest.raises(RuntimeError): rs.run(**full(case))
    with sqlite3.connect(case['output']/'selection.sqlite') as db:
        db.execute("INSERT INTO winners VALUES ('invented-extra')")
    monkeypatch.setattr(rs,'export_attempt',original)
    with pytest.raises(ValueError,match='ranking mismatch'): rs.run(**full(case),resume=True)


def test_sqlite_temp_directory_restored(case):
    with sqlite3.connect(':memory:') as db:
        before=db.execute('PRAGMA temp_store_directory').fetchone()
    rs.run(**full(case))
    with sqlite3.connect(':memory:') as db:
        assert db.execute('PRAGMA temp_store_directory').fetchone()==before


@pytest.mark.parametrize('change',['code','runtime','policy','mesh','admission'])
def test_more_resume_identities(case,monkeypatch,change):
    rs.run(**case)
    if change=='code':
        original=rs.sha256
        monkeypatch.setattr(rs,'sha256',lambda p:'0'*64 if str(p).endswith('resumable_selection.py') else original(p))
    elif change=='policy':
        original=rs.identity
        monkeypatch.setattr(rs,'identity',lambda mesh:dict(original(mesh),policy_sha256='0'*64))
    elif change=='runtime':
        monkeypatch.setattr(rs.platform,'python_version',lambda:'changed-runtime')
    elif change=='mesh':
        case['mesh_path'].write_text(case['mesh_path'].read_text()+' ')
    else:
        case['packet_path'].write_text(case['packet_path'].read_text()+' ')
    with pytest.raises(ValueError):rs.run(**case,resume=True)


def test_resource_failure_in_sqlite_callback_propagates(case,monkeypatch):
    original=rs.SelectionBudget.check
    def fail(self,*a,**kw):
        if getattr(self,'trip',False):raise OSError('injected storage unavailable')
        return original(self,*a,**kw)
    monkeypatch.setattr(rs.SelectionBudget,'check',fail)
    b=rs.SelectionBudget(case['catalog'].parent,free_gib=0)
    b.trip=True
    assert b.sqlite_progress()==1
    assert 'storage unavailable' in str(b.failure)


def test_enospc_before_batch_commit_rolls_back(case,monkeypatch):
    import errno
    original=rs.save
    calls=0
    def fail(db,cp):
        nonlocal calls
        calls+=1
        if calls==2:raise OSError(errno.ENOSPC,'injected full volume')
        original(db,cp)
    monkeypatch.setattr(rs,'save',fail)
    with pytest.raises(OSError):rs.run(**case)
    assert len(rows(case['output']))==1
    monkeypatch.setattr(rs,'save',original)
    assert rs.run(**case,resume=True)['stage']=='ranking'


@pytest.mark.parametrize('workers', [2, 4])
def test_parallel_output_exact_and_resume(case,tmp_path,workers):
    args=full(case)
    baseline=rs.run(**args)
    parallel=rs.run(**dict(args,output=tmp_path/'parallel',workers=workers))
    assert parallel['counts']==baseline['counts']
    for name in ('records.jsonl','candidate-pmids.txt'):
        assert (args['output']/name).read_bytes()==(tmp_path/'parallel'/name).read_bytes()
    assert rs.run(**dict(args,output=tmp_path/'parallel',workers=workers),resume=True)==parallel


@pytest.mark.parametrize('delta', [-1, 1])
def test_bad_replay_count_cannot_publish(case,delta):
    path=case['catalog'].parent/'replay-status.json'
    report=json.loads(path.read_text());report['documents']+=delta;path.write_text(json.dumps(report))
    with pytest.raises(ValueError,match='Source count mismatch'):
        rs.run(**full(case))
    assert not (case['output']/'summary.json').exists()
    assert not (case['output']/'records.jsonl').exists()


def test_source_identity_does_not_recount_index(case):
    original=sqlite3.connect
    statements=[]
    # Source identity should use only max(rowid); output checkpoint validation still counts its own ledger.
    with original(case['catalog']) as src:
        src.set_trace_callback(statements.append)
        mesh=rs.MeshIndex.load(case['mesh_path'],year=2026)
        bound=rs.source_identity(src,case['catalog'],case['receipts'],mesh,2026,{},'synthetic-volume')
    assert bound['tables']['documents']['count']==2
    assert not any('count(' in q.lower() for q in statements)


@pytest.mark.parametrize('workers',[0,13,True,1.5])
def test_invalid_workers_refused(case,workers):
    with pytest.raises(ValueError,match='Workers'):
        rs.run(**case,workers=workers)
