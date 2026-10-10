"""Offline exploratory PubMed catalog. Not a selected/rights-qualified RAG corpus.

Retains complete record XML so subsequent selection can inspect fields not displayed by
search. Uses disk-backed SQLite, file-level transactions, ordered replay and source hashes.
"""
import gzip
import fcntl
import shutil
import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.parsers import expat

VERSION = 'prowl-pubmed-catalog-preview-v1'
NAME = re.compile(r'pubmed26n(\d{4})\.xml\.gz')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def events(path, *, max_expanded=8 * 1024**3, max_record=16 * 1024**2,
           seconds=600):
    """Stream gzip XML without fetching DTDs or permitting entity declarations.

    Each yielded event preserves its XML and position. Memory is bounded by the input
    chunk and one capped record, rather than by file or corpus size.
    """
    if expat.version_info < (2, 4, 1):
        raise ValueError('Unsupported Expat version')
    parser = expat.ParserCreate()
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    def refuse(*args):
        raise ValueError('XML entities are forbidden')
    parser.EntityDeclHandler = refuse
    parser.ExternalEntityRefHandler = refuse
    parser.SkippedEntityHandler = refuse
    depth = 0
    builder = None
    record_size = 0
    queue = []
    def start(tag, attrs):
        nonlocal depth, builder, record_size
        depth += 1
        if depth == 1 and tag != 'PubmedArticleSet':
            raise ValueError('Unexpected XML root')
        if depth > 128:
            raise ValueError('XML nesting limit exceeded')
        if depth == 2:
            if tag not in ('PubmedArticle', 'PubmedBookArticle', 'DeleteCitation'):
                raise ValueError(f'Unsupported record: {tag}')
            builder = ET.TreeBuilder()
            record_size = 0
        if builder is not None:
            record_size += len(tag) + sum(len(k)+len(v) for k,v in attrs.items())
            if record_size > max_record:
                raise ValueError('Record size limit exceeded')
            builder.start(tag, attrs)
    def text(value):
        nonlocal record_size
        if builder is not None:
            record_size += len(value.encode('utf-8'))
            if record_size > max_record:
                raise ValueError('Record size limit exceeded')
            builder.data(value)
    def end(tag):
        nonlocal depth, builder
        if builder is not None:
            builder.end(tag)
            if depth == 2:
                queue.append(builder.close())
                builder = None
        depth -= 1
    parser.StartElementHandler, parser.CharacterDataHandler, parser.EndElementHandler = start,text,end
    deadline = time.monotonic()+seconds
    total = 0
    seq = 0
    with gzip.open(path, 'rb') as stream:
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError('Per-file parse deadline reached')
            block = stream.read(64*1024)
            total += len(block)
            if total > max_expanded:
                raise ValueError('Expanded byte limit exceeded')
            parser.Parse(block, not block)
            for node in queue:
                pmids = node.findall('PMID') if node.tag == 'DeleteCitation' else [
                    node.find('MedlineCitation/PMID') if node.tag == 'PubmedArticle'
                    else node.find('BookDocument/PMID')]
                if not pmids:
                    raise ValueError('Missing PMID')
                for pmid_node in pmids:
                    pmid = '' if pmid_node is None else (pmid_node.text or '').strip()
                    if not re.fullmatch(r'[1-9]\d*', pmid):
                        raise ValueError('Invalid PMID')
                    yield seq, pmid, node
                    seq += 1
            queue.clear()
            if not block:
                break


def connect(path):
    db = sqlite3.connect(path)
    db.execute('PRAGMA journal_mode=DELETE')
    db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS applied (position INTEGER PRIMARY KEY, name TEXT UNIQUE, sha256 TEXT, events INTEGER)')
    db.execute('''CREATE TABLE IF NOT EXISTS documents
        (pmid TEXT PRIMARY KEY, title TEXT, abstract TEXT, source_file TEXT,
         source_sha256 TEXT, source_seq INTEGER, xml TEXT)''')
    db.commit()
    return db


def bind(db, manifest_bytes):
    expected = {'version':VERSION, 'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest()}
    current = dict(db.execute('SELECT key,value FROM metadata'))
    if current and current != expected:
        raise ValueError('Catalog version or snapshot identity differs')
    with db:
        for key,value in expected.items():
            db.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)',(key,value))


def apply_file(db, path, expected_sha, position):
    """Commit all events from one verified source, or roll back the entire file."""
    path = Path(path)
    if path.is_symlink() or not NAME.fullmatch(path.name):
        raise ValueError('Invalid source path')
    prior = db.execute('SELECT name,sha256 FROM applied WHERE position=?',(position,)).fetchone()
    if prior:
        if prior != (path.name,expected_sha):
            raise ValueError('Applied source identity differs')
        return False
    if position != db.execute('SELECT count(*) FROM applied').fetchone()[0]:
        raise ValueError('Sources must be applied in manifest order')
    before = path.stat()
    if sha256(path) != expected_sha:
        raise ValueError('Source SHA256 mismatch')
    count = 0
    with db:
        for seq,pmid,node in events(path):
            count += 1
            if node.tag == 'DeleteCitation':
                db.execute('DELETE FROM documents WHERE pmid=?',(pmid,))
                continue
            article = node.find('MedlineCitation/Article') if node.tag == 'PubmedArticle' else node.find('BookDocument')
            def content(n):
                return '' if n is None else ''.join(n.itertext())
            title = content(article.find('ArticleTitle')) if article is not None else ''
            sections = article.findall('Abstract/AbstractText') if article is not None else []
            abstract = '\n'.join(content(n) for n in sections)
            db.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?)',
                (pmid,title,abstract,path.name,expected_sha,seq,ET.tostring(node,encoding='unicode')))
        after = path.stat()
        if (before.st_size,before.st_mtime_ns,before.st_ino) != (after.st_size,after.st_mtime_ns,after.st_ino):
            raise ValueError('Source changed during parsing')
        db.execute('INSERT INTO applied VALUES (?,?,?,?)',(position,path.name,expected_sha,count))
    return True


def _build(source, output, max_files=3):
    source, output = Path(source),Path(output)
    if max_files < 1:
        raise ValueError('max_files must be positive')
    raw = (source/'manifest.json').read_bytes()
    manifest = json.loads(raw)
    if manifest.get('version') != 'pubmed-raw-download-v1':
        raise ValueError('Unsupported download manifest')
    members = manifest['files']
    if not members or any(not NAME.fullmatch(m['name']) for m in members):
        raise ValueError('Invalid manifest source names')
    numbers = [int(NAME.fullmatch(m['name'])[1]) for m in members]
    if numbers != list(range(1,len(numbers)+1)):
        raise ValueError('Snapshot must be a contiguous ordered baseline/update sequence')
    receipts = {}
    for line in (source/'receipts.jsonl').read_text().splitlines():
        row = json.loads(line)
        old = receipts.get(row['name'])
        if old and (old['sha256'],old['bytes']) != (row['sha256'],row['bytes']):
            raise ValueError('Conflicting download receipts')
        receipts[row['name']] = row
    output.parent.mkdir(parents=True,exist_ok=True)
    db = connect(output)
    db.execute('PRAGMA max_page_count=524288')  # 2 GiB at default 4096-byte pages
    try:
        bind(db,raw)
        for i,member in enumerate(members[:max_files]):
            name = member['name']
            if name not in receipts:
                raise ValueError(f'No verified download receipt: {name}')
            path = source/name
            if path.stat().st_size != receipts[name]['bytes']:
                raise ValueError('Source size differs from receipt')
            apply_file(db,path,receipts[name]['sha256'],i)
        applied = db.execute('SELECT count(*) FROM applied').fetchone()[0]
        return dict(version=VERSION,applied_files=applied,total_files=len(members),
                    documents=db.execute('SELECT count(*) FROM documents').fetchone()[0],
                    snapshot_replayed=applied==len(members),
                    selected_corpus=False,rights_qualified=False)
    finally:
        db.close()


def build(source, output, max_files=3):
    """Single-writer preview: at most ten input files, never a full corpus by accident."""
    if not 1 <= max_files <= 10:
        raise ValueError('Preview accepts max_files 1..10; full-scale loading is separate')
    output = Path(output)
    if output.is_symlink():
        raise ValueError('Symlink output refused')
    output.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output.parent).free < 10*1024**3:
        raise ValueError('Need at least 10 GiB free for the bounded preview')
    with output.with_suffix(output.suffix+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        return _build(source,output,max_files)


def search(path, query, limit=10):
    """Literal title/abstract substring search: exploratory, not ranked retrieval."""
    if not query.strip() or not 1 <= limit <= 100:
        raise ValueError('Supply a nonempty query and limit 1..100')
    db = sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    try:
        if dict(db.execute('SELECT key,value FROM metadata')).get('version') != VERSION:
            raise ValueError('Unsupported catalog')
        pattern = '%'+query.replace('!', '!!').replace('%','!%').replace('_','!_')+'%'
        rows = db.execute("SELECT pmid,title,abstract,source_file,source_sha256,source_seq FROM documents WHERE title LIKE ? ESCAPE '!' OR abstract LIKE ? ESCAPE '!' ORDER BY length(pmid),pmid LIMIT ?",(pattern,pattern,limit)).fetchall()
        return [dict(zip(('pmid','title','abstract','source_file','source_sha256','source_seq'),r),
                     url='https://pubmed.ncbi.nlm.nih.gov/'+r[0]+'/', exploratory=True) for r in rows]
    finally:
        db.close()
