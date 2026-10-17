"""Direct, batch-published passage embeddings. No global topic-selection gate.

Canonical source bundles and frozen batch files remain authoritative. PostgreSQL is
rebuildable. The initial adapter accepts explicit CC BY 4.0 JATS article snapshots;
it does not infer permissions for arbitrary PubMed abstracts or resolve new versions.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
from xml.etree import ElementTree as ET

from .passages import make_representation, make_passages, chunk_config, passage_text, verify_passage, verify_representation_source
from .records import canonical_bytes, make_revision, make_work, make_rights, may_index, verify_rights

LICENSE = 'https://creativecommons.org/licenses/by/4.0/'
XLINK = '{http://www.w3.org/1999/xlink}href'
DIMENSIONS = 384
SOURCE_PROFILES = ('legacy-v1', 'coverage-v1')
JATS_HEADER = b'<!DOCTYPE article\n  PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Archiving and Interchange DTD with MathML3 v1.4 20241031//EN" "JATS-archivearticle1-4-mathml3.dtd">'
ADMIN_SECTIONS = {'acknowledgments', 'acknowledgements', 'author contributions', 'funding',
    'institutional review board statement', 'informed consent statement', 'conflicts of interest',
    'conflict of interest statement', 'ethics statement', 'contributor information',
    'data availability statement', 'footnotes'}
NON_PROSE = {'table-wrap', 'fig', 'supplementary-material', 'ref-list'}


def prose_text(node):
    """Exclude embedded non-prose while retaining the surrounding paragraph text."""
    parts = [node.text or '']
    for child in node:
        if child.tag not in NON_PROSE:
            parts.append(prose_text(child))
        else:
            parts.append(' ')
        parts.append(child.tail or '')
    return ''.join(parts)


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def text(element):
    return ''.join(element.itertext()).strip() if element is not None else ''


def source_bundle(path, *, profile='legacy-v1'):
    raw = Path(path).read_bytes()
    if profile not in SOURCE_PROFILES:
        raise ValueError('Unknown source extraction profile')
    parsed = raw
    if profile == 'coverage-v1' and parsed.lstrip().startswith(JATS_HEADER):
        # Exact declaration only; never fetch a DTD or resolve an entity. Identity uses raw bytes.
        parsed = parsed.lstrip()[len(JATS_HEADER):]
    if len(raw) > 32 * 1024**2 or b'<!DOCTYPE' in parsed.upper() or b'<!ENTITY' in parsed.upper():
        raise ValueError('Oversized or entity-bearing XML refused')
    root = ET.fromstring(parsed)
    meta = root.find('./front/article-meta')
    if meta is None or root.get('article-type') in ('retraction', 'correction', 'expression-of-concern'):
        raise ValueError('Unsupported or notice article')
    if meta.findall('related-article'):
        raise ValueError('Related-article notices require review')
    links = [e.get(XLINK, '') for e in meta.findall('./permissions/license//ext-link')]
    if profile == 'coverage-v1':
        links.extend(e.get(XLINK, '') for e in meta.findall('./permissions/license'))
        links.extend(text(e) for e in meta.findall(
            './permissions/license/{http://www.niso.org/schemas/ali/1.0/}license_ref'))
    # Older publisher JATS uses HTTP for this same exact licence identifier.
    # Opt in only for coverage extraction; preserve legacy acceptance behavior.
    accepted_licenses = {LICENSE}
    if profile == 'coverage-v1':
        accepted_licenses.add('http://creativecommons.org/licenses/by/4.0/')
    if not accepted_licenses.intersection(links):
        raise ValueError('Explicit CC BY 4.0 licence required')
    ids = {e.get('pub-id-type'): text(e) for e in meta.findall('article-id')}
    pmid, pmcid = ids.get('pmid', ''), ids.get('pmcid', '')
    if not re.fullmatch(r'[1-9][0-9]{0,9}', pmid) or not re.fullmatch(r'PMC[0-9]+', pmcid):
        raise ValueError('PMID and PMCID required')
    title = text(meta.find('./title-group/article-title'))
    authors = [text(e.find('surname')) + ', ' + text(e.find('given-names')) for e in meta.findall('./contrib-group/contrib/name')]
    if not title or not authors:
        raise ValueError('Citation title and authors required')
    sections = []
    # Only article prose; figures, tables, supplementary material and references are excluded.
    for region, parent in [('abstract', meta.find('abstract')), ('body', root.find('body'))]:
        if parent is None:
            continue
        def walk(node, heading):
            if node.tag in NON_PROSE:
                return
            if profile == 'coverage-v1' and node.tag in ('ack', 'fn-group', 'fn', 'bio', 'contrib-group', 'notes'):
                return
            if node.tag == 'sec':
                heading = text(node.find('title')) or heading
                if profile == 'coverage-v1' and heading.strip().lower() in ADMIN_SECTIONS:
                    return
            if node.tag == 'p':
                value = prose_text(node).strip() if profile == 'coverage-v1' else text(node)
                if value:
                    sections.append(dict(section_id=f'{region}-{len(sections)}', title=heading, paragraphs=[value]))
                return
            for child in node:
                walk(child, heading)
        walk(parent, region.title())
    work = make_work('work:pmid:' + pmid, origin='pmc_cloud')
    revision = make_revision(work['work_id'], raw)
    rep = make_representation(work_id=work['work_id'], revision_id=revision['revision_id'], kind='full_text', sections=sections)
    rights = make_rights(rep['representation_id'], decision='allowed',
        permissions=dict(retain_metadata=True, local_text_store=True, local_embedding=True, display_snippet=True, redistribute=False),
        policy_version='jats-cc-by-4.0-v1', reason='Explicit CC BY 4.0 in retained JATS snapshot; attribution retained; local use only.')
    citation = dict(pmid=pmid, pmcid=pmcid, doi=ids.get('doi'), title=title, authors=authors,
        year=text(meta.find('./pub-date/year')), url=f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/',
        license_url=LICENSE, attribution=text(meta.find('./permissions/copyright-statement')),
        notice_scope='retained_source_snapshot_only')
    result = dict(work=work, revision=revision, representation=rep, rights=rights, citation=citation,
                source_sha256=hashlib.sha256(raw).hexdigest(), original_sections=sections)
    if profile != 'legacy-v1':
        result['extraction_profile'] = profile
    return result


def source_passages(bundle):
    rep = bundle['representation']
    verify_representation_source(rep, bundle['original_sections'])
    if not may_index(bundle['rights']) or not bundle['rights']['permissions']['display_snippet']:
        raise ValueError('Passage permissions refused')
    for p in make_passages(rep, chunk_config(max_chars=600, overlap_sentences=1)):
        verify_passage(p, rep)
        yield dict(passage=p, text=passage_text(p, rep), citation=bundle['citation'],
                   revision_id=bundle['revision']['revision_id'], source_sha256=bundle['source_sha256'],
                   rights=bundle['rights'])


def encoder_passages(bundle, encoder):
    """Preserve exact locators; split overlong sentences into 200-character windows.

    This explicit fallback avoids silent model truncation. A window still exceeding
    the token limit is rejected by Encoder.encode, never silently shortened.
    """
    from .records import identity_digest, sha256_hex
    ordinal = 0
    rep = bundle['representation']
    for row in source_passages(bundle):
        p = row['passage']
        n = len(encoder.tokenizer.encode(row['text'], add_special_tokens=True, truncation=False))
        if n <= encoder.descriptor['max_tokens']:
            row['passage'] = dict(p, ordinal=ordinal)
            ordinal += 1
            yield row
            continue
        config = dict(version='prowl-char-fallback-v1', max_chars=200, overlap_sentences=0)
        for start in range(p['start'], p['end'], 200):
            end = min(start+200,p['end'])
            part = dict(p, start=start, end=end, chunking=config, ordinal=ordinal, oversized=False,
                        text_sha256=sha256_hex(rep['text'][start:end]))
            part['passage_id'] = 'psg:' + identity_digest(dict(representation_id=rep['representation_id'],
                representation_sha256=rep['text_sha256'],start=start,end=end,chunking=config))
            verify_passage(part,rep)
            ordinal += 1
            yield dict(row,passage=part,text=rep['text'][start:end])


def validate_row(row):
    from .records import validate, sha256_hex
    p = row['passage']
    validate('passage', p)
    verify_rights(row['rights'])
    if (not may_index(row['rights']) or not row['rights']['permissions']['display_snippet']
            or row['rights']['representation_id'] != p['representation_id']
            or sha256_hex(row['text']) != p['text_sha256']
            or len(row['text']) != p['end']-p['start']):
        raise ValueError('Passage content or permissions mismatch')
    if p['work_id'] != 'work:pmid:' + row['citation']['pmid']:
        raise ValueError('Citation work mismatch')
    return row


def vector_values(values):
    import math
    if len(values) != DIMENSIONS or any(not math.isfinite(float(v)) for v in values):
        raise ValueError('Invalid embedding dimension or values')
    packed = struct.pack('<' + 'f' * DIMENSIONS, *values)
    result = list(struct.unpack('<' + 'f' * DIMENSIONS, packed))
    if abs(sum(v*v for v in result)-1) > 1e-3:
        raise ValueError('Embedding must be unit normalized')
    return result, hashlib.sha256(packed).hexdigest()


class Encoder:
    def __init__(self, folder, descriptor):
        import torch
        from transformers import AutoTokenizer, AutoModel
        self.descriptor = descriptor
        if (descriptor['dimensions'] != DIMENSIONS or descriptor['max_tokens'] != 256
                or descriptor['pooling'] != 'attention-masked-mean' or descriptor['normalize'] is not True):
            raise ValueError('Unsupported encoder configuration')
        for name, expected in descriptor['files'].items():
            if hashlib.sha256((Path(folder)/name).read_bytes()).hexdigest() != expected:
                raise ValueError('Encoder file hash mismatch')
        self.tokenizer = AutoTokenizer.from_pretrained(folder, local_files_only=True, trust_remote_code=False)
        self.model = AutoModel.from_pretrained(folder, local_files_only=True, trust_remote_code=False, use_safetensors=True).eval()
        torch.set_num_threads(4)
        self.id = digest(descriptor)

    def encode(self, texts):
        import torch
        lengths = [len(self.tokenizer.encode(s, add_special_tokens=True, truncation=False)) for s in texts]
        if any(n > self.descriptor['max_tokens'] for n in lengths):
            raise ValueError(f'Passage exceeds encoder token limit; no silent truncation: max={max(lengths)}')
        inputs = self.tokenizer(texts, padding=True, truncation=False, return_tensors='pt')
        with torch.inference_mode():
            hidden = self.model(**inputs).last_hidden_state
            mask = inputs['attention_mask'].unsqueeze(-1).to(hidden.dtype)
            pooled = (hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
            vectors = torch.nn.functional.normalize(pooled, p=2, dim=1).float().cpu().tolist()
        return [vector_values(v)[0] for v in vectors]


def frozen_batch(rows, vectors, descriptor):
    if not rows or len(rows) != len(vectors):
        raise ValueError('Batch rows/vector count mismatch')
    if len({r['passage']['passage_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate passage in batch')
    items=[]
    for row, vector in zip(rows, vectors):
        validate_row(row)
        vector, checksum = vector_values(vector)
        items.append(dict(record=row, vector=vector, vector_sha256=checksum))
    payload=dict(version='prowl-vector-batch-v1', encoder=descriptor, items=items)
    return dict(batch_id=digest(payload), **payload)


def verify_batch(batch):
    expected = frozen_batch([i['record'] for i in batch['items']], [i['vector'] for i in batch['items']], batch['encoder'])
    if expected != batch:
        raise ValueError('Frozen batch hash/content mismatch')
    return batch


def write_once(path, value):
    data=canonical_bytes(value)
    path=Path(path)
    if path.exists():
        if path.read_bytes()!=data:
            raise ValueError('Existing artifact differs')
        return
    import os
    import uuid
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.partial')
    with tmp.open('xb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    try:
        os.link(tmp,path)  # Create-if-absent: never overwrite another writer's artifact.
    except FileExistsError:
        if path.read_bytes()!=data:
            raise ValueError('Concurrent artifact differs')
    tmp.unlink()
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


DDL = '''
CREATE SCHEMA IF NOT EXISTS literature;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS literature.collections (
 id text PRIMARY KEY, encoder_id text NOT NULL, encoder jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS literature.sources (
 collection_id text REFERENCES literature.collections(id), work_id text NOT NULL,
 revision_id text NOT NULL, source_sha256 text NOT NULL,
 PRIMARY KEY(collection_id,work_id));
CREATE TABLE IF NOT EXISTS literature.batches (
 collection_id text REFERENCES literature.collections(id), batch_id text NOT NULL,
 row_count integer NOT NULL CHECK(row_count>0), PRIMARY KEY(collection_id,batch_id));
CREATE TABLE IF NOT EXISTS literature.passages (
 collection_id text NOT NULL, passage_id text NOT NULL, batch_id text NOT NULL,
 work_id text NOT NULL, record jsonb NOT NULL, text text NOT NULL,
 embedding vector(384) NOT NULL, vector_sha256 text NOT NULL,
 PRIMARY KEY(collection_id,passage_id),
 FOREIGN KEY(collection_id,work_id) REFERENCES literature.sources(collection_id,work_id),
 FOREIGN KEY(collection_id,batch_id) REFERENCES literature.batches(collection_id,batch_id));
'''


def initialize(db):
    with db.transaction():
        db.execute(DDL)


def vector_sql(values):
    return '[' + ','.join(format(v,'.9g') for v in vector_values(values)[0]) + ']'


def load_batch(db, collection, batch):
    """One transaction publishes one immutable batch; retry verifies saved values."""
    from psycopg.types.json import Jsonb
    verify_batch(batch)
    encoder_id=digest(batch['encoder']);bid=batch['batch_id']
    with db.transaction():
        db.execute("SET LOCAL statement_timeout='30s'")
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(collection,))
        db.execute('INSERT INTO literature.collections VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
                   (collection,encoder_id,Jsonb(batch['encoder'])))
        actual=db.execute('SELECT encoder_id,encoder FROM literature.collections WHERE id=%s',(collection,)).fetchone()
        if actual != (encoder_id,batch['encoder']):
            raise ValueError('Collection encoder mismatch')
        exists=db.execute('SELECT row_count FROM literature.batches WHERE collection_id=%s AND batch_id=%s',(collection,bid)).fetchone()
        if not exists:
            db.execute('INSERT INTO literature.batches VALUES (%s,%s,%s)',(collection,bid,len(batch['items'])))
            for item in batch['items']:
                row=item['record'];work=row['passage']['work_id']
                identity=(row['revision_id'],row['source_sha256'])
                db.execute('INSERT INTO literature.sources VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING',(collection,work,*identity))
                actual=db.execute('SELECT revision_id,source_sha256 FROM literature.sources WHERE collection_id=%s AND work_id=%s',(collection,work)).fetchone()
                if actual != identity:
                    raise ValueError('Source revision differs; use a new collection')
                db.execute('INSERT INTO literature.passages VALUES (%s,%s,%s,%s,%s,%s,%s::vector,%s)',
                    (collection,row['passage']['passage_id'],bid,work,Jsonb(row),row['text'],vector_sql(item['vector']),item['vector_sha256']))
        elif exists[0] != len(batch['items']):
            raise ValueError('Published batch count mismatch')
        saved=db.execute('SELECT passage_id,record,text,embedding::text,vector_sha256 FROM literature.passages WHERE collection_id=%s AND batch_id=%s',(collection,bid)).fetchall()
        by_id={r[0]:r[1:] for r in saved}
        if len(saved)!=len(batch['items']):
            raise ValueError('Stored batch inventory mismatch')
        for item in batch['items']:
            row=item['record'];record,body,vec,checksum=by_id[row['passage']['passage_id']]
            if record!=row or body!=row['text'] or checksum!=item['vector_sha256'] or vector_values(json.loads(vec))[1]!=checksum:
                raise ValueError('Stored batch content mismatch')
    return dict(batch_id=bid,rows=len(batch['items']),already_published=bool(exists))


def search(db, collection, encoder, question, k=5):
    if not isinstance(question,str) or not question.strip() or len(question)>2000 or type(k) is not int or not 1<=k<=20:
        raise ValueError('Invalid search request')
    q=vector_sql(encoder.encode([question])[0])
    with db.transaction():
        db.execute("SET LOCAL statement_timeout='30s'")
        bound=db.execute('SELECT encoder_id FROM literature.collections WHERE id=%s',(collection,)).fetchone()
        if bound!=(encoder.id,):
            raise ValueError('Missing collection or incompatible query encoder')
        rows=db.execute('SELECT record,1-(embedding <=> %s::vector) AS score FROM literature.passages WHERE collection_id=%s ORDER BY embedding <=> %s::vector,passage_id LIMIT %s',(q,collection,q,k)).fetchall()
    return [dict(record=validate_row(row),score=float(score)) for row,score in rows]
