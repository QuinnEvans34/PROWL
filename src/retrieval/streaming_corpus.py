"""Disk-backed PubMed replay and stage-1 selection; no evaluation or rights decisions."""
from collections import Counter
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import time

from .pubmed_catalog import NAME, VERSION, apply_file, bind, connect, sha256
from .topic_selection import MeshIndex, evaluate, identity, metadata

ENGINE = 'prowl-streaming-corpus-v1'


def write_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
    temp.replace(path)


class Budget:
    """Cooperative time/disk checks, including SQLite work; not a hard RSS watchdog."""
    def __init__(self, folder, *, hours=12, max_gib=512, free_gib=400):
        if hours <= 0 or max_gib <= 0 or free_gib < 0:
            raise ValueError('Invalid resource budget')
        self.folder = Path(folder)
        self.deadline = time.monotonic()+hours*3600
        self.maximum = max_gib*1024**3
        self.floor = free_gib*1024**3
        self.last = 0
        self.check(force=True)

    def check(self, force=False):
        now = time.monotonic()
        if now > self.deadline:
            raise TimeoutError('Processing time budget reached; committed files remain resumable')
        if force or now-self.last >= 1:
            self.last = now
            if shutil.disk_usage(self.folder).free < self.floor:
                raise OSError('Free-space floor reached')
            if sum(p.stat().st_size for p in self.folder.iterdir() if p.is_file()) > self.maximum:
                raise OSError('Output directory budget reached')

    def sqlite_progress(self):
        try:
            self.check()
            return 0
        except (OSError, TimeoutError):
            return 1


def tune(db, budget, cache_mib=32):
    if type(cache_mib) is not int or not 32 <= cache_mib <= 8192:
        raise ValueError('Cache must be 32..8192 MiB')
    db.execute(f'PRAGMA cache_size={-cache_mib*1024}')
    db.execute('PRAGMA temp_store=FILE')
    db.execute('PRAGMA mmap_size=0')
    pagesize = db.execute('PRAGMA page_size').fetchone()[0]
    db.execute(f'PRAGMA max_page_count={int(budget.maximum)//pagesize}')
    db.set_progress_handler(budget.sqlite_progress, 10000)


@contextmanager
def locked(folder):
    folder = Path(folder)
    if folder.is_symlink():
        raise ValueError('Symlink output refused')
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield folder


def snapshot(source):
    source = Path(source)
    raw = (source/'manifest.json').read_bytes()
    manifest = json.loads(raw)
    members = manifest['files']
    if manifest.get('version') != 'pubmed-raw-download-v1' or not members:
        raise ValueError('Unsupported or empty snapshot')
    names = [m['name'] for m in members]
    if names != [f'pubmed26n{i:04d}.xml.gz' for i in range(1,len(names)+1)]:
        raise ValueError('Snapshot must be a contiguous ordered sequence')
    receipts = {}
    with (source/'receipts.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            name = row['name']
            if name not in names or not re.fullmatch('[0-9a-f]{64}',row['sha256']):
                raise ValueError('Invalid download receipt')
            if name in receipts and (receipts[name]['sha256'],receipts[name]['bytes']) != (row['sha256'],row['bytes']):
                raise ValueError('Conflicting download receipts')
            receipts[name] = row
    return raw, members, receipts


def replay(source, output, *, through=None, hours=12, max_gib=512, free_gib=400, file_seconds=600, cache_mib=32):
    """Resume an exact manifest prefix; omission of through requires every source receipt."""
    if type(file_seconds) is not int or not 1 <= file_seconds <= 7200:
        raise ValueError("Per-file deadline must be 1..7200 seconds")
    if type(cache_mib) is not int or not 32 <= cache_mib <= 8192:
        raise ValueError('Cache must be 32..8192 MiB')
    source = Path(source)
    raw, members, receipts = snapshot(source)
    limit = len(members) if through is None else through
    if type(limit) is not int or not 1 <= limit <= len(members):
        raise ValueError('Invalid file prefix')
    for member in members[:limit]:
        name = member['name']
        if name not in receipts or (source/name).is_symlink() or (source/name).stat().st_size != receipts[name]['bytes']:
            raise ValueError(f'Missing or invalid verified source: {name}')
    started = time.monotonic()
    with locked(output) as folder:
        budget = Budget(folder,hours=hours,max_gib=max_gib,free_gib=free_gib)
        path = folder/'catalog.sqlite'
        if path.is_symlink():
            raise ValueError('Symlink catalog refused')
        expected = {'engine':ENGINE,'engine_sha256':sha256(__file__),'catalog_code_sha256':sha256(Path(__file__).with_name('pubmed_catalog.py')),'manifest_sha256':hashlib.sha256(raw).hexdigest()}
        binding = folder/'replay-identity.json'
        if binding.exists() and json.loads(binding.read_text()) != expected:
            raise ValueError('Replay implementation or manifest changed; use a new output')
        if path.exists() and not binding.exists():
            raise ValueError('Existing catalog lacks streaming replay identity')
        write_json(binding,expected)
        (folder/'manifest.json').write_bytes(raw)
        db = connect(path)
        try:
            tune(db,budget,cache_mib=cache_mib)
            bind(db,raw)
            applied = list(db.execute('SELECT position,name,sha256 FROM applied ORDER BY position'))
            if len(applied) > limit or any(row != (i,members[i]['name'],receipts.get(members[i]['name'],{}).get('sha256')) for i,row in enumerate(applied)):
                raise ValueError('Applied prefix or receipt identity differs')
            for i in range(len(applied),limit):
                member = members[i]
                file_started = time.monotonic()
                write_json(folder/'replay-status.json',dict(state='running',applied_files=i,total_files=len(members),current_file=member['name'],file_seconds=file_seconds,cache_mib=cache_mib))
                budget.check(force=True)
                apply_file(db,source/member['name'],receipts[member['name']]['sha256'],i,check_resources=budget.check,file_seconds=file_seconds)
                metric = dict(file=member['name'],seconds=round(time.monotonic()-file_started,3),cache_mib=cache_mib,events=db.execute('SELECT events FROM applied WHERE position=?',(i,)).fetchone()[0])
                with (folder/'replay-metrics.jsonl').open('a') as stream:
                    stream.write(json.dumps(metric)+'\n')
                write_json(folder/'replay-status.json',dict(state='running',applied_files=i+1,total_files=len(members),last_file=metric))
            result = dict(engine=ENGINE,version=VERSION,manifest_sha256=hashlib.sha256(raw).hexdigest(),
                          applied_files=limit,total_files=len(members),snapshot_replayed=limit==len(members),
                          documents=db.execute('SELECT count(*) FROM documents').fetchone()[0],
                          deleted_pmids=db.execute('SELECT count(*) FROM deleted').fetchone()[0],
                          elapsed_seconds=round(time.monotonic()-started,3),database_bytes=path.stat().st_size,
                          selected_corpus=False,rights_qualified=False)
            write_json(folder/'replay-status.json',dict(result,state='complete' if result['snapshot_replayed'] else 'prefix_complete'))
            return result
        except BaseException as exc:
            db.set_progress_handler(None,0)
            db.rollback()
            write_json(folder/'replay-status.json',dict(state='stopped',error=str(exc),applied_files=db.execute('SELECT count(*) FROM applied').fetchone()[0],total_files=len(members)))
            raise
        finally:
            db.close()


def count_rows(rows):
    """Single-pass equivalent of the bounded preview's reconciliation counts."""
    scalar = dict(universe=0,final_records=0,deleted_pmids=0,book_records=0,excluded_books=0,deleted_books=0,workflow_uncapped=0,workflow_capped=0)
    counters = {k:Counter() for k in ('dispositions','blocks','branches','overlaps','reasons','record_types','publication_types','no_mesh_candidates_by_status','core_qualifier')}
    for r in rows:
        scalar['universe'] += 1
        deleted = r['disposition']=='deleted'
        scalar['deleted_pmids' if deleted else 'final_records'] += 1
        for key,values in [('dispositions',[r['disposition']]),('blocks',r['blocks']),('branches',r['branches']),('reasons',r['reasons']),('record_types',[r['record_type']])]:
            counters[key].update(values)
        if len(r['branches'])>1: counters['overlaps'].update(['+'.join(r['branches'])])
        if r['record_type']=='PubmedBookArticle':
            scalar['book_records'] += 1
            if deleted: scalar['deleted_books'] += 1
            if r['disposition']=='excluded': scalar['excluded_books'] += 1
        if r['metadata']:
            counters['publication_types'].update(p['text'] for p in r['metadata'].get('pubtypes',[]))
        if r['disposition']=='candidate' and 'no_mesh' in r['reasons']:
            counters['no_mesh_candidates_by_status'].update([r['metadata']['indexing_status'] or 'missing'])
        if 'CORE' in r['branches']:
            counters['core_qualifier'].update(['no_mesh' if 'no_mesh' in r['reasons'] else 'present' if r.get('has_dx_imaging_qualifier') else 'absent'])
        if r['branches']==['WORKFLOW']:
            scalar['workflow_uncapped'] += r['disposition']=='candidate' or 'workflow_capped_out' in r['reasons']
            scalar['workflow_capped'] += r['disposition']=='candidate'
    return dict(scalar,**{k:dict(v) for k,v in counters.items()})


def select(catalog, mesh_path, output, *, mesh_sha256, cutoff_year, hours=12, max_gib=256, free_gib=400, allow_prefix=False):
    """Stream to a disk ledger, rank globally, and export. New output per attempt."""
    if type(cutoff_year) is not int or not 1000 <= cutoff_year <= 9999:
        raise ValueError('Invalid cutoff listing year')
    mesh = MeshIndex.load(mesh_path,year=2026)
    if mesh.sha256 != mesh_sha256:
        raise ValueError('MeSH differs from verified asset')
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    started = time.monotonic()
    with locked(output) as folder:
        budget = Budget(folder,hours=hours,max_gib=max_gib,free_gib=free_gib)
        src = sqlite3.connect(Path(catalog).resolve().as_uri()+'?mode=ro',uri=True)
        db = sqlite3.connect(folder/'selection.sqlite')
        try:
            src.execute('PRAGMA cache_size=-32768')
            src.execute('PRAGMA mmap_size=0')
            src.set_progress_handler(budget.sqlite_progress,10000)
            tune(db,budget)
            src.execute('BEGIN')
            meta = dict(src.execute('SELECT key,value FROM metadata'))
            if meta.get('version') != VERSION: raise ValueError('Requires v2 catalog')
            applied = list(src.execute('SELECT position,name,sha256,events FROM applied ORDER BY position'))
            if not applied or [r[0] for r in applied] != list(range(len(applied))): raise ValueError('Invalid catalog prefix')
            # Replay receipt is a claim checked against the transaction's actual applied prefix.
            report = json.loads(Path(catalog).with_name('replay-status.json').read_text())
            if report.get('manifest_sha256') != meta['manifest_sha256'] or report.get('applied_files') != len(applied):
                raise ValueError('Replay receipt does not match catalog')
            raw = Path(catalog).with_name('manifest.json').read_bytes()
            members = json.loads(raw)['files']
            if hashlib.sha256(raw).hexdigest() != meta['manifest_sha256'] or len(applied)>len(members) or any(r[1]!=members[i]['name'] for i,r in enumerate(applied)):
                raise ValueError('Catalog manifest mismatch')
            complete = len(applied)==len(members)
            if bool(report.get('snapshot_replayed')) != complete:
                raise ValueError('Inconsistent completion receipt')
            if not allow_prefix and not complete: raise ValueError('Complete snapshot required')
            db.execute('CREATE TABLE rows (pmid TEXT PRIMARY KEY, n INTEGER, w INTEGER, year INTEGER, workflow INTEGER, body TEXT)')
            db.execute('CREATE INDEX numeric_order ON rows(n,pmid)')
            db.execute('CREATE INDEX ranking ON rows(workflow,w DESC,year DESC,n,pmid)')
            columns = ('pmid','xml','deleted','source_file','source_sha256','source_seq')
            sql = '''SELECT pmid,xml,0,source_file,source_sha256,source_seq FROM documents
                     UNION ALL SELECT pmid,xml,1,source_file,source_sha256,source_seq FROM deleted'''
            total = 0
            for values in src.execute(sql):
                budget.check()
                item = dict(zip(columns,values))
                record = metadata(item['xml']) if item['xml'] is not None else None
                if record and record['pmid'] != item['pmid']: raise ValueError('XML and catalog PMID differ')
                row = evaluate(record,mesh,cutoff_year=cutoff_year,deleted=item['deleted'],pmid=item['pmid'])
                row['provenance'] = {k:item[k] for k in columns[3:]}
                # Numeric PMID ordering without SQLite integer-width assumptions.
                db.execute('INSERT INTO rows VALUES (?,?,?,?,?,?)',(row['pmid'],len(row['pmid']),len(row['w_concepts']),row['year'] if row['year'] is not None else -1,int(row['disposition']=='candidate' and row['branches']==['WORKFLOW']),json.dumps(row,ensure_ascii=False)))
                total += 1
                if total % 1000 == 0:
                    db.commit()
                    write_json(folder/'selection-status.json',dict(state='evaluating',records=total))
            src.close(); src = None
            db.commit()
            winners = {r[0] for r in db.execute('SELECT pmid FROM rows WHERE workflow=1 ORDER BY w DESC,year DESC,n,pmid LIMIT 500')}
            digest, rows_digest = hashlib.sha256(),hashlib.sha256()
            def export():
                with (folder/'records.jsonl').open('xb') as out, (folder/'candidate-pmids.txt').open('xb') as ids:
                    for pmid,workflow,body in db.execute('SELECT pmid,workflow,body FROM rows ORDER BY n,pmid'):
                        budget.check()
                        row = json.loads(body)
                        if workflow and pmid not in winners:
                            row['reasons'].append('workflow_capped_out'); row['disposition']='excluded'; row['primary_stratum']=None
                        data = (json.dumps(row,sort_keys=True,ensure_ascii=False)+'\n').encode()
                        out.write(data); rows_digest.update(data)
                        if row['disposition']=='candidate':
                            data = (pmid+'\n').encode('ascii'); ids.write(data); digest.update(data)
                        yield row
            counts = count_rows(export())
            budget.check(force=True)
            result = dict(engine=ENGINE,identity=identity(mesh),catalog=meta,applied_prefix=applied,
                          cutoff_listing_year=cutoff_year,counts=counts,candidate_pmids_sha256=digest.hexdigest(),
                          records_sha256=rows_digest.hexdigest(),snapshot_replayed=bool(report['snapshot_replayed']),
                          official_selection_frozen=False,rights_qualified=False,sampling_performed=False,stage=1,
                          elapsed_seconds=round(time.monotonic()-started,3),engine_sha256=sha256(__file__))
            # Written last: partial ledgers/exports are never complete results.
            write_json(folder/'selection-status.json',dict(state='complete',records=total))
            write_json(folder/'summary.json',result)
            return result
        except BaseException as exc:
            write_json(folder/'selection-status.json',dict(state='stopped',error=str(exc)))
            raise
        finally:
            if src is not None: src.close()
            db.close()
