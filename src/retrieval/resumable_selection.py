"""Resumable stage-1 evaluation, global ranking and verified publication."""
from contextlib import contextmanager
import fcntl
import errno
import stat
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
import platform
import sqlite3
import time
import uuid
from xml.parsers import expat

from .pubmed_catalog import VERSION, sha256
from .streaming_corpus import Budget, count_rows, write_json
from .topic_selection import MeshIndex, evaluate, identity, metadata

ENGINE = 'prowl-resumable-selection-v1'
def unlinked_file_bytes(device):
    """Count this process's open, unlinked regular files once per inode.

    Include all devices conservatively: unexpected spill placement must still count.
    The device argument is retained for the visible-output accounting interface.
    """
    directory = '/proc/self/fd' if Path('/proc/self/fd').is_dir() else '/dev/fd'
    found = {}
    for name in os.listdir(directory):
        try:
            info = os.fstat(int(name))
        except OSError as exc:
            # Directory enumeration may expose its own already-closed descriptor.
            if exc.errno == errno.EBADF:
                continue
            raise
        if stat.S_ISREG(info.st_mode) and info.st_nlink == 0:
            found[(info.st_dev, info.st_ino)] = info.st_size
    return sum(found.values())


class SelectionBudget(Budget):
    """Preserve the underlying resource cause when SQLite reports interrupted."""
    failure = None

    def check(self, force=False):
        now = time.monotonic()
        if now > self.deadline:
            raise TimeoutError('Selection invocation deadline reached')
        if force or now-self.last >= 1:
            self.last = now
            if shutil.disk_usage(self.folder).free < self.floor:
                raise OSError('Free-space floor reached')
            size = 0
            for path in self.folder.rglob('*'):
                if path.is_symlink():
                    raise ValueError('Symlink output member refused')
                if path.is_file():
                    size += path.stat().st_size
            hidden = unlinked_file_bytes(self.folder.stat().st_dev)
            self.peak_unlinked_bytes = max(getattr(self, 'peak_unlinked_bytes', 0), hidden)
            self.peak_accounted_bytes = max(getattr(self, 'peak_accounted_bytes', 0), size+hidden)
            if size+hidden > self.maximum:
                raise OSError('Output directory budget reached')

    def sqlite_progress(self):
        try:
            self.check()
            return 0
        except (OSError, TimeoutError) as exc:
            self.failure = exc
            return 1


STAGES = ('evaluating_documents', 'evaluating_deleted', 'ranking', 'exporting', 'verifying', 'complete')
ROOT = Path(__file__).resolve().parents[2]


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def safe(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlink path refused')
    return path


@contextmanager
def locks(catalog, output, resume):
    # Do not create a missing source lock: this must be a replay-produced catalog.
    with safe(catalog.parent/'writer.lock').open('r') as source_lock:
        fcntl.flock(source_lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        if resume:
            if not output.is_dir():
                raise ValueError('Resume output missing')
            if any(p.is_symlink() for p in output.iterdir()):
                raise ValueError('Symlink output member refused')
            allowed = {'writer.lock', 'selection.sqlite', 'selection.sqlite-journal',
                       'selection-status.json', 'selection-status.json.tmp', 'attempts', 'tmp',
                       'records.jsonl', 'candidate-pmids.txt', 'summary.json', 'summary.json.tmp'}
            if any(p.name not in allowed for p in output.iterdir()):
                raise ValueError('Foreign output member')
            if any(p.is_symlink() for p in output.rglob('*')):
                raise ValueError('Symlink output descendant refused')
            if not (output/'selection.sqlite').is_file():
                raise ValueError('Resume ledger missing')
        else:
            output.mkdir(exist_ok=False)
        with (output/'writer.lock').open('a') as output_lock:
            fcntl.flock(output_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield


def source_identity(src, catalog, receipts, mesh, cutoff_year, packet, volume_id):
    stat = catalog.stat()
    meta = dict(src.execute('SELECT key,value FROM metadata'))
    if meta.get('version') != VERSION:
        raise ValueError('Unsupported catalog schema')
    manifest_path = safe(catalog.parent/'manifest.json')
    manifest = json.loads(manifest_path.read_text())
    members = manifest['files']
    applied = list(src.execute('SELECT position,name,sha256,events FROM applied ORDER BY position'))
    receipt_rows = {}
    for line in safe(receipts).read_text().splitlines():
        r = json.loads(line)
        if r['name'] in receipt_rows and receipt_rows[r['name']] != r['sha256']:
            raise ValueError('Conflicting download receipt')
        receipt_rows[r['name']] = r['sha256']
    if (manifest.get('version') != 'pubmed-raw-download-v1' or not applied
            or len(applied) != len(members)
            or any(r[:3] != (i, m['name'], receipt_rows.get(m['name']))
                   for i, (r, m) in enumerate(zip(applied, members)))):
        raise ValueError('Complete contiguous applied ledger and receipts required')
    report = json.loads(safe(catalog.parent/'replay-status.json').read_text())
    manifest_hash = sha256(manifest_path)
    if (meta.get('manifest_sha256') != manifest_hash
            or report.get('manifest_sha256') != manifest_hash
            or report.get('applied_files') != len(applied)
            or report.get('state') != 'complete' or report.get('snapshot_replayed') is not True):
        raise ValueError('Completion receipt mismatch')
    replay_binding = json.loads(safe(catalog.parent/'replay-identity.json').read_text())
    if replay_binding.get('manifest_sha256') != manifest_hash:
        raise ValueError('Replay identity manifest mismatch')
    tables = {}
    for table in ('documents', 'deleted'):
        count, maximum = src.execute(f'SELECT count(*),max(rowid) FROM {table}').fetchone()
        tables[table] = {'count': count, 'max_rowid': maximum}
    # Runtime and all local imported behavior bytes are bound; no source rehash.
    paths = ['src/retrieval/resumable_selection.py', 'src/retrieval/topic_selection.py',
             'src/retrieval/streaming_corpus.py', 'src/retrieval/pubmed_catalog.py',
             'scripts/retrieval/select_pubmed_corpus.py']
    return dict(engine=ENGINE, catalog=dict(path=str(catalog), inode=stat.st_ino,
                bytes=stat.st_size, mtime_ns=stat.st_mtime_ns, volume_id=volume_id,
                metadata=meta, schema=list(src.execute("SELECT type,name,sql FROM sqlite_master ORDER BY type,name"))),
                applied_sha256=digest(applied), manifest_sha256=manifest_hash,
                receipts_sha256=sha256(receipts), replay_identity_sha256=sha256(safe(catalog.parent/'replay-identity.json')),
                completion_sha256=sha256(catalog.parent/'replay-status.json'), tables=tables,
                policy=identity(mesh), cutoff_year=cutoff_year,
                implementation={p:sha256(ROOT/p) for p in paths},
                runtime=[platform.python_version(), sqlite3.sqlite_version, expat.EXPAT_VERSION],
                admission=packet)


def admission(packet_path):
    """Bind reviewed prerequisite evidence; never infer a seed freeze from lookup progress."""
    path = safe(packet_path)
    packet = json.loads(path.read_text())
    if packet.get('version') != 'selection-admission-v1':
        raise ValueError('Unsupported admission packet')
    evidence = packet.get('evidence', {})
    for name in ('seed_freeze', 'information_needs', 'reserve_exposure'):
        item = evidence.get(name, {})
        if sha256(safe(item.get('path', ''))) != item.get('sha256'):
            raise ValueError(f'Admission evidence mismatch: {name}')
    return dict(packet_sha256=sha256(path), packet=packet)


def checkpoint(db):
    return json.loads(db.execute('SELECT body FROM checkpoint WHERE id=1').fetchone()[0])


def save(db, cp):
    cp['committed_total'] = sum(cp['counts'].values())
    cp['commit_sequence'] += 1
    cp['committed_at'] = time.time()
    db.execute('UPDATE checkpoint SET body=? WHERE id=1', (encoded(cp),))
    db.commit()


def validate_checkpoint(db, bound):
    if db.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
        raise ValueError('Ledger integrity failure')
    if db.execute('SELECT body FROM binding').fetchall() != [(encoded(bound),)]:
        raise ValueError('Resume identity mismatch')
    cp = checkpoint(db)
    if cp['schema_version'] != 1 or cp['stage'] not in STAGES or cp['identity_sha256'] != digest(bound):
        raise ValueError('Invalid checkpoint schema or identity')
    if cp.get('committed_total') != sum(cp['counts'].values()):
        raise ValueError('Checkpoint total mismatch')
    for table in ('documents', 'deleted'):
        n, last = db.execute('SELECT count(*),max(source_rowid) FROM rows WHERE source_table=?', (table,)).fetchone()
        if n != cp['counts'][table] or last != cp['cursors'][table] or n > bound['tables'][table]['count']:
            raise ValueError('Checkpoint/ledger mismatch')
    if cp['stage'] != STAGES[0] and cp['counts']['documents'] != bound['tables']['documents']['count']:
        raise ValueError('Premature stage transition')
    if STAGES.index(cp['stage']) >= STAGES.index('ranking') and cp['counts']['deleted'] != bound['tables']['deleted']['count']:
        raise ValueError('Premature ranking')
    if cp['stage'] == STAGES[0] and cp['counts']['deleted']:
        raise ValueError('Unexpected deleted rows')
    return cp


def run(catalog, mesh_path, output, *, receipts, packet_path, volume_id,
        mesh_sha256, cutoff_year, resume=False, hours=12, max_gib=256,
        free_gib=400, cache_mib=32, batch_size=1000, commit_seconds=10,
        evaluation_only=False):
    """Run all stages; evaluation_only is an explicit development boundary."""
    if type(cutoff_year) is not int or not 1000 <= cutoff_year <= 9999:
        raise ValueError('Invalid cutoff year')
    if type(batch_size) is not int or not 1 <= batch_size <= 10000 or not 0 < commit_seconds <= 60:
        raise ValueError('Invalid batch bounds')
    if type(cache_mib) is not int or not 32 <= cache_mib <= 8192:
        raise ValueError('Invalid cache')
    if not all(math.isfinite(v) for v in (hours, max_gib, free_gib)):
        raise ValueError('Nonfinite resource limit')
    catalog, output = safe(catalog), safe(output)
    mesh = MeshIndex.load(safe(mesh_path), year=2026)
    if mesh.sha256 != mesh_sha256:
        raise ValueError('MeSH differs')
    packet = admission(packet_path)
    with locks(catalog, output, resume):
        for suffix in ('-wal', '-journal'):
            p = safe(str(catalog)+suffix)
            if p.exists() and p.stat().st_size:
                raise ValueError('Source recovery or WAL requires separate review')
        budget = SelectionBudget(output, hours=hours, max_gib=max_gib, free_gib=free_gib)
        src = sqlite3.connect(catalog.as_uri()+'?mode=ro', uri=True)
        db = None
        prior_temp = None
        try:
            src.execute('PRAGMA mmap_size=0')
            src.execute(f'PRAGMA cache_size={-cache_mib*1024}')
            src.set_progress_handler(budget.sqlite_progress, 10000)
            src.execute('BEGIN')
            bound = source_identity(src, catalog, receipts, mesh, cutoff_year, packet, volume_id)
            db = sqlite3.connect(output/'selection.sqlite')
            db.execute('PRAGMA synchronous=FULL')
            db.execute('PRAGMA journal_mode=DELETE')
            db.execute('PRAGMA mmap_size=0')
            # SQLite exposes this process-global setting; this CLI is single-worker.
            # Keep sorting spill on the accounted output volume, and restore on exit.
            temp_folder = output/'tmp'
            temp_folder.mkdir(exist_ok=True)
            prior = db.execute('PRAGMA temp_store_directory').fetchone()
            prior_temp = prior[0] if prior else ''
            temp_sql = str(temp_folder).replace("'", "''")
            db.execute(f"PRAGMA temp_store_directory='{temp_sql}'")
            if db.execute('PRAGMA temp_store_directory').fetchone() != (str(temp_folder),):
                raise ValueError('SQLite temporary directory control unavailable')
            db.execute('PRAGMA temp_store=FILE')
            db.execute('PRAGMA threads=0')
            db.execute(f'PRAGMA cache_size={-cache_mib*1024}')
            db.execute(f'PRAGMA max_page_count={int(budget.maximum)//db.execute("PRAGMA page_size").fetchone()[0]}')
            db.set_progress_handler(budget.sqlite_progress, 10000)
            if not resume:
                db.executescript('''BEGIN;
                    CREATE TABLE binding(body TEXT NOT NULL);
                    CREATE TABLE checkpoint(id INTEGER PRIMARY KEY CHECK(id=1),body TEXT NOT NULL);
                    CREATE TABLE rows(pmid TEXT PRIMARY KEY,source_table TEXT NOT NULL,
                      source_rowid INTEGER NOT NULL,body TEXT NOT NULL,
                      UNIQUE(source_table,source_rowid));
                    CREATE TABLE winners(pmid TEXT PRIMARY KEY);
                    CREATE TABLE attempts(id INTEGER PRIMARY KEY, receipt TEXT, summary TEXT);''')
                db.execute('INSERT INTO binding VALUES (?)', (encoded(bound),))
                cp = dict(schema_version=1, run_id=str(uuid.uuid4()), committed_processing_seconds=0.0, identity_sha256=digest(bound), stage=STAGES[0],
                          commit_sequence=0, committed_total=0, cursors=dict(documents=None, deleted=None),
                          counts=dict(documents=0, deleted=0))
                db.execute('INSERT INTO checkpoint VALUES (1,?)', (encoded(cp),))
                db.commit()
            cp = validate_checkpoint(db, bound)
            for table in ('documents', 'deleted'):
                if cp['stage'] != 'evaluating_'+table:
                    continue
                last = cp['cursors'][table]
                query = f'SELECT rowid,pmid,xml,source_file,source_sha256,source_seq FROM {table}'
                cursor = src.execute(query + (' WHERE rowid>?' if last is not None else '')+' ORDER BY rowid', () if last is None else (last,))
                pending, since = 0, time.monotonic()
                for rowid, pmid, xml, file, source_hash, seq in cursor:
                    budget.check()
                    record = metadata(xml) if xml is not None else None
                    if record and record['pmid'] != pmid:
                        raise ValueError(f'XML/PMID mismatch at {table}:{rowid}')
                    row = evaluate(record, mesh, cutoff_year=cutoff_year, deleted=table=='deleted', pmid=pmid)
                    row['provenance'] = dict(source_file=file, source_sha256=source_hash, source_seq=seq)
                    db.execute('INSERT INTO rows VALUES (?,?,?,?)', (pmid, table, rowid, encoded(row)))
                    cp['counts'][table] += 1
                    cp['cursors'][table] = rowid
                    pending += 1
                    if pending >= batch_size or time.monotonic()-since >= commit_seconds:
                        cp['committed_processing_seconds'] += time.monotonic()-since
                        save(db, cp)
                        write_json(output/'selection-status.json', dict(state=cp['stage'], checkpoint=cp))
                        pending, since = 0, time.monotonic()
                if cp['counts'][table] != bound['tables'][table]['count']:
                    raise ValueError('Source count mismatch')
                cp['committed_processing_seconds'] += time.monotonic()-since
                cp['stage'] = STAGES[STAGES.index(cp['stage'])+1]
                save(db, cp)
            if evaluation_only:
                write_json(output/'selection-status.json', dict(state='evaluation_complete_ranking_pending', checkpoint=cp))
                return cp
            def recheck():
                current = source_identity(src, catalog, receipts, mesh, cutoff_year,
                                          admission(packet_path), volume_id)
                # Reload the asset so replacing MeSH during execution is detected too.
                if sha256(mesh_path) != mesh_sha256 or encoded(current) != encoded(bound):
                    raise ValueError('Source identity changed during selection')
            return finish(db, cp, bound, output, budget, recheck)
        except BaseException as exc:
            if db is not None:
                db.set_progress_handler(None, 0)
                db.rollback()
            cause = budget.failure or exc
            try:
                write_json(output/'selection-status.json', dict(state='stopped', error_type=type(cause).__name__, error=str(cause)))
            except OSError:
                pass
            if cause is not exc:
                raise cause from exc
            raise
        finally:
            src.close()
            if db is not None:
                try:
                    db.set_progress_handler(None, 0)
                    if prior_temp is not None:
                        prior_sql = prior_temp.replace("'", "''")
                        db.execute(f"PRAGMA temp_store_directory='{prior_sql}'")
                finally:
                    db.close()


# Expression indexes avoid an extra corpus-wide denormalization update.
WORKFLOW = "json_extract(body,'$.disposition')='candidate' AND json_extract(body,'$.branches')='[\"WORKFLOW\"]'"
RANK_ORDER = "json_array_length(body,'$.w_concepts') DESC,coalesce(json_extract(body,'$.year'),-1) DESC,length(pmid),pmid"


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_json(path, value):
    temp = path.with_name(path.name+'.tmp')
    with temp.open('w') as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    sync_directory(path.parent)


def ranked_rows(db, budget):
    winners = {r[0] for r in db.execute('SELECT pmid FROM winners')}
    for pmid, body in db.execute('SELECT pmid,body FROM rows ORDER BY length(pmid),pmid'):
        budget.check()
        row = json.loads(body)
        if row['disposition']=='candidate' and row['branches']==['WORKFLOW'] and pmid not in winners:
            row['reasons'].append('workflow_capped_out')
            row['disposition']='excluded'
            row['primary_stratum']=None
        yield row


def record_bytes(row):
    # Match the original selector's exact public bytes, including spaces and newline.
    return (json.dumps(row, sort_keys=True, ensure_ascii=False)+'\n').encode()


def export_attempt(db, cp, folder, budget):
    # Allocate the attempt before files; a failed attempt is preserved and never reused.
    attempt = db.execute('INSERT INTO attempts DEFAULT VALUES').lastrowid
    cp['export_attempt'] = attempt
    save(db, cp)
    root = folder/'attempts'
    root.mkdir(exist_ok=True)
    directory = root/str(attempt)
    directory.mkdir()
    sync_directory(root)
    hashes = {name:hashlib.sha256() for name in ('records.jsonl','candidate-pmids.txt')}
    with (directory/'records.jsonl.partial').open('xb') as records, (directory/'candidate-pmids.txt.partial').open('xb') as ids:
        def emit():
            for row in ranked_rows(db,budget):
                data = record_bytes(row)
                records.write(data); hashes['records.jsonl'].update(data)
                if row['disposition']=='candidate':
                    data = (row['pmid']+'\n').encode('ascii')
                    ids.write(data); hashes['candidate-pmids.txt'].update(data)
                yield row
        counts = count_rows(emit())
        for stream in (records,ids):
            stream.flush(); os.fsync(stream.fileno())
    sync_directory(directory)
    receipt = dict(attempt=attempt, counts=counts, files={name:dict(
        sha256=h.hexdigest(), bytes=(directory/(name+'.partial')).stat().st_size)
        for name,h in hashes.items()})
    budget.check(force=True)
    db.execute('UPDATE attempts SET receipt=? WHERE id=?',(encoded(receipt),attempt))
    cp['stage']='verifying'
    save(db,cp)


def verify_exports(db, receipt, folder, budget):
    """Verify complete bytes against the ledger, accepting a partially published pair."""
    paths = {}
    for name, expected in receipt['files'].items():
        final, partial = folder/name, folder/'attempts'/str(receipt['attempt'])/(name+'.partial')
        if final.exists() and partial.exists():
            raise ValueError('Conflicting final and attempt files')
        path = final if final.exists() else partial
        if not path.is_file() or path.stat().st_size != expected['bytes']:
            raise ValueError('Missing or truncated export')
        paths[name]=path
    hashes = {name:hashlib.sha256() for name in paths}
    with paths['records.jsonl'].open('rb') as records, paths['candidate-pmids.txt'].open('rb') as ids:
        def compare():
            for row in ranked_rows(db,budget):
                expected = record_bytes(row)
                data = records.read(len(expected))
                if data != expected:
                    raise ValueError('Export record differs from ledger')
                hashes['records.jsonl'].update(data)
                if row['disposition']=='candidate':
                    expected=(row['pmid']+'\n').encode('ascii')
                    data=ids.read(len(expected))
                    if data != expected:
                        raise ValueError('Export candidate differs from ledger')
                    hashes['candidate-pmids.txt'].update(data)
                yield row
        counts=count_rows(compare())
        if records.read(1) or ids.read(1) or counts != receipt['counts']:
            raise ValueError('Export reconciliation mismatch')
    if any(h.hexdigest()!=receipt['files'][name]['sha256'] for name,h in hashes.items()):
        raise ValueError('Export hash mismatch')
    return paths


def finish(db, cp, bound, folder, budget, recheck):
    write_json(folder/'selection-status.json',dict(state=cp['stage'],checkpoint=cp))
    if cp['stage']=='ranking':
        db.execute('BEGIN')
        db.execute('CREATE INDEX IF NOT EXISTS numeric_order ON rows(length(pmid),pmid)')
        db.execute(f'CREATE INDEX IF NOT EXISTS workflow_rank ON rows({RANK_ORDER}) WHERE {WORKFLOW}')
        db.execute('DELETE FROM winners')
        db.execute(f'INSERT INTO winners SELECT pmid FROM rows WHERE {WORKFLOW} ORDER BY {RANK_ORDER} LIMIT 500')
        cp['winner_count']=db.execute('SELECT count(*) FROM winners').fetchone()[0]
        cp['ranking_version']=1
        cp['stage']='exporting'
        save(db,cp)
    # Validate saved winners rather than trusting a stage label after resume.
    expected=[r[0] for r in db.execute(f'SELECT pmid FROM rows WHERE {WORKFLOW} ORDER BY {RANK_ORDER} LIMIT 500')]
    actual={r[0] for r in db.execute('SELECT pmid FROM winners')}
    if actual != set(expected) or cp.get('winner_count') != len(actual):
        raise ValueError('Saved ranking mismatch')
    if cp['stage']=='exporting':
        write_json(folder/'selection-status.json',dict(state='exporting',checkpoint=cp))
        if any((folder/n).exists() for n in ('summary.json','records.jsonl','candidate-pmids.txt')):
            raise ValueError('Premature final output')
        export_attempt(db,cp,folder,budget)
    write_json(folder/'selection-status.json',dict(state=cp['stage'],checkpoint=cp))
    attempt = cp['export_attempt']
    receipt_text, summary_text = db.execute('SELECT receipt,summary FROM attempts WHERE id=?',(attempt,)).fetchone()
    receipt=json.loads(receipt_text)
    paths=verify_exports(db,receipt,folder,budget)
    recheck()
    budget.check(force=True)
    if summary_text is None:
        if (folder/'summary.json').exists():
            raise ValueError('Unexplained completion summary')
        summary=dict(engine=ENGINE, identity=bound['policy'], catalog=bound['catalog']['metadata'],
                     run_id=cp['run_id'], identity_sha256=cp['identity_sha256'],
                     applied_ledger_sha256=bound['applied_sha256'], cutoff_listing_year=bound['cutoff_year'],
                     counts=receipt['counts'], files=receipt['files'], export_attempt=attempt,
                     attempt_count=db.execute('SELECT count(*) FROM attempts').fetchone()[0],
                     attempt_history=[dict(id=i, export_finished=r is not None) for i,r in
                                      db.execute('SELECT id,receipt FROM attempts ORDER BY id')],
                     resources=dict(output_cap_bytes=budget.maximum, free_floor_bytes=budget.floor,
                                    sqlite_cache_kib=-db.execute('PRAGMA cache_size').fetchone()[0],
                                    peak_accounted_bytes=budget.peak_accounted_bytes,
                                    peak_unlinked_bytes=budget.peak_unlinked_bytes,
                                    cooperative_checks=True, hard_rss_limit=False),
                     records_sha256=receipt['files']['records.jsonl']['sha256'],
                     candidate_pmids_sha256=receipt['files']['candidate-pmids.txt']['sha256'],
                     snapshot_replayed=True, official_selection_frozen=False,
                     rights_qualified=False, sampling_performed=False, stage=1)
        db.execute('UPDATE attempts SET summary=? WHERE id=?',(encoded(summary),attempt))
        db.commit()
    else:
        summary=json.loads(summary_text)
    if (folder/'summary.json').exists():
        if json.loads((folder/'summary.json').read_text()) != summary:
            raise ValueError('Completion summary mismatch')
        if any(path.parent != folder for path in paths.values()):
            raise ValueError('Summary precedes published pair')
    else:
        if cp['stage']=='complete':
            raise ValueError('Completed summary missing')
        for name,path in paths.items():
            if path != folder/name:
                os.replace(path,folder/name)
                sync_directory(path.parent)
                sync_directory(folder)
        durable_json(folder/'summary.json',summary)
    if cp['stage']!='complete':
        cp['stage']='complete'
        save(db,cp)
    write_json(folder/'selection-status.json',dict(state='complete',checkpoint=cp))
    return summary
