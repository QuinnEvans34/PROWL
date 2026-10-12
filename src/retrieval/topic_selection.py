"""Approved selection policy v0.1, stage 1 only. No rights or sampling decisions."""
from collections import Counter
from dataclasses import dataclass
from itertools import product
import hashlib
from pathlib import Path
import re
import sys
import unicodedata
from xml.etree import ElementTree as ET
from xml.parsers import expat

BASE_POLICY = Path(__file__).resolve().parents[2] / 'docs/capstone/retrieval/planning/SEARCH-AND-SELECTION.md'
POLICY = BASE_POLICY.with_name('SEARCH-AND-SELECTION-V0.1.md')
VERSION = 'prowl-topic-selection-v0.1-implementation-1'
MESH_NAMES = {
    'P': ('Pancreas', 'Pancreatic Neoplasms', 'Pancreatic Ducts', 'Pancreatic Cyst'),
    'C': ('Tomography, X-Ray Computed',),
    'A': ('Artificial Intelligence', 'Neural Networks, Computer', 'Image Processing, Computer-Assisted',
          'Radiographic Image Interpretation, Computer-Assisted', 'Diagnosis, Computer-Assisted'),
    'M': ('Observer Variation',), 'IMG': ('Diagnostic Imaging',),
}
TERMS = {
    'P': ('pancrea*',), 'C': ('computed tomograph*',),
    'A': ('segmentation', 'deep learning', 'machine learning', 'neural network*', 'convolutional',
          'U-Net', 'nnU-Net', 'artificial intelligence', 'computer-aided', 'radiomic*'),
    'M': ('interobserver', 'inter-observer', 'intraobserver', 'intra-observer', 'observer variab*',
          'annotat*', 'contour*', 'delineat*', 'manual segmentation', 'ground truth'),
    'W': ('automation bias', 'human-in-the-loop', 'reader study', 'reader studies', 'AI-assisted',
          'computer-assisted reading'),
    'IMG': ('radiolog*', 'medical imaging', 'diagnostic imaging'),
}
PUBTYPES = {'Comment', 'Editorial', 'News', 'Letter', 'Published Erratum', 'Retraction of Publication'}
HARD = {'not_candidate', 'pubtype_excluded', 'retracted', 'animal_only', 'language_non_english', 'year_out_of_range'}


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).split())


def tokens(text):
    out, word = [], []
    for char in text:
        if char.isalnum():
            word.append(char)
        elif word:
            out.append(''.join(word)); word = []
    if word:
        out.append(''.join(word))
    return out


def variants(term):
    words = term.casefold().split()
    alternatives = []
    for word in words:
        wildcard = word.endswith('*')
        stem = word.rstrip('*')
        split = tokens(stem)
        forms = [split]
        if '-' in stem:
            forms.append(tokens(stem.replace('-', '')))
        alternatives.append([[(t, wildcard and i == len(form)-1) for i,t in enumerate(form)] for form in forms])
    return [sum(parts, []) for parts in product(*alternatives)]


COMPILED = {term: variants(term) for terms in TERMS.values() for term in terms}


def matches(unit, term):
    words = tokens(normalized(unit).casefold())
    for form in COMPILED[term]:
        for i in range(len(words)-len(form)+1):
            if all(words[i+j].startswith(t) if prefix else words[i+j] == t for j,(t,prefix) in enumerate(form)):
                return True
    return False


def safe_elements(stream, root_tag, child_tags, *, max_bytes, max_record=16*1024**2):
    """Bounded XML records with no entity resolution or external fetches."""
    parser = expat.ParserCreate()
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    def refuse(*_):
        raise ValueError('XML entities are forbidden')
    parser.EntityDeclHandler = parser.ExternalEntityRefHandler = parser.SkippedEntityHandler = refuse
    depth, size, total = 0, 0, 0
    builder, queue = None, []
    def start(tag, attrs):
        nonlocal depth, builder, size
        depth += 1
        if depth > 128 or (depth == 1 and tag != root_tag):
            raise ValueError('Unexpected XML structure')
        if depth == 2:
            if tag not in child_tags:
                raise ValueError('Unexpected XML record type')
            builder, size = ET.TreeBuilder(), 0
        if builder is not None:
            size += len(tag.encode()) + sum(len(k.encode()) + len(v.encode()) for k,v in attrs.items())
            if size > max_record:
                raise ValueError('XML record too large')
            builder.start(tag, attrs)
    def text(value):
        nonlocal size
        if builder is not None:
            size += len(value.encode())
            if size > max_record:
                raise ValueError('XML record too large')
            builder.data(value)
    def end(tag):
        nonlocal depth, builder
        if builder is not None:
            builder.end(tag)
            if depth == 2:
                queue.append(builder.close()); builder = None
        depth -= 1
    parser.StartElementHandler, parser.CharacterDataHandler, parser.EndElementHandler = start,text,end
    while True:
        block = stream.read(65536)
        total += len(block)
        if total > max_bytes:
            raise ValueError('XML input too large')
        parser.Parse(block, not block)
        yield from queue
        queue.clear()
        if not block:
            break


@dataclass(frozen=True)
class MeshIndex:
    groups: dict
    animals: str
    humans: str
    resolved: dict
    sha256: str
    source_kind: str

    @classmethod
    def load(cls, path, *, year, source_kind='mesh-2026-descriptors'):
        if year != 2026 or source_kind not in ('mesh-2026-descriptors', 'synthetic-test-fixture'):
            raise ValueError('Policy requires MeSH 2026 descriptor data')
        path = Path(path)
        records, names = {}, {}
        before = path.stat()
        digest = hashlib.sha256()
        class Reader:
            def read(self, size):
                data = stream.read(size); digest.update(data); return data
        with path.open('rb') as stream:
            for node in safe_elements(Reader(), 'DescriptorRecordSet', {'DescriptorRecord'}, max_bytes=512*1024**2):
                ui, name = node.findtext('DescriptorUI'), node.findtext('DescriptorName/String')
                if not ui or not name or ui in records:
                    raise ValueError('Missing or duplicate descriptor identity')
                records[ui] = tuple(n.text or '' for n in node.findall('TreeNumberList/TreeNumber'))
                names.setdefault(name, []).append(ui)
        after = path.stat()
        if (before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_ino,after.st_size,after.st_mtime_ns):
            raise ValueError('MeSH changed during read')
        required = {name for values in MESH_NAMES.values() for name in values} | {'Animals','Humans'}
        resolved = {}
        for name in sorted(required):
            if len(names.get(name, [])) != 1:
                raise ValueError(f'MeSH descriptor must resolve exactly once: {name}')
            ui = names[name][0]
            resolved[name] = {'ui':ui, 'trees':list(records[ui])}
        groups = {}
        for block, group_names in MESH_NAMES.items():
            roots = [tree for name in group_names for tree in resolved[name]['trees']]
            if any(not resolved[name]['trees'] for name in group_names):
                raise ValueError('Block descriptor has no tree numbers')
            groups[block] = frozenset(ui for ui,trees in records.items()
                                     if any(t == root or t.startswith(root+'.') for t in trees for root in roots))
        return cls(groups, resolved['Animals']['ui'], resolved['Humans']['ui'], resolved, digest.hexdigest(), source_kind)


def content(node):
    return '' if node is None else ''.join(node.itertext())


def metadata(xml):
    """Extract journal fields; book identity alone suffices for the v0.1 exclusion."""
    import io
    raw = xml.encode('utf-8') if isinstance(xml,str) else xml
    if len(raw) > 16*1024**2:
        raise ValueError('Record too large')
    nodes = list(safe_elements(io.BytesIO(b'<records>'+raw+b'</records>'), 'records', {'PubmedArticle','PubmedBookArticle'}, max_bytes=17*1024**2))
    if len(nodes) != 1:
        raise ValueError('Expected one PubMed article or book record')
    node = nodes[0]
    if node.tag == 'PubmedBookArticle':
        pmid = node.findtext('BookDocument/PMID','')
        if not re.fullmatch(r'[1-9][0-9]*',pmid):
            raise ValueError('Invalid book PMID')
        return dict(pmid=pmid,record_type=node.tag)
    citation = node.find('MedlineCitation')
    if citation is None:
        raise ValueError('Missing MedlineCitation')
    pmid = citation.findtext('PMID', '')
    if not re.fullmatch(r'[1-9][0-9]*',pmid):
        raise ValueError('Invalid PMID')
    def values(path):
        return [content(n) for n in node.findall(path)]
    base = 'MedlineCitation/Article/'
    abstract_nodes = node.findall(base+'Abstract/AbstractText')
    headings = [dict(ui=h.find('DescriptorName').get('UI','') if h.find('DescriptorName') is not None else '',
                     major=h.find('DescriptorName').get('MajorTopicYN') if h.find('DescriptorName') is not None else None,
                     qualifiers=[dict(ui=q.get('UI',''),text=content(q),major=q.get('MajorTopicYN')) for q in h.findall('QualifierName')])
                for h in citation.findall('MeshHeadingList/MeshHeading')]
    dates = {key: values(path) for key,path in (
        ('journal_year',base+'Journal/JournalIssue/PubDate/Year'),
        ('medline_date',base+'Journal/JournalIssue/PubDate/MedlineDate'),
        ('article_year',base+'ArticleDate/Year'),
        ('pubmed_year','PubmedData/History/PubMedPubDate[@PubStatus="pubmed"]/Year'))}
    year, source = None, None
    for key, candidates in dates.items():
        for value in candidates:
            match = re.search(r'(?<![0-9])[0-9]{4}(?![0-9])',value) if key == 'medline_date' else re.fullmatch(r'[0-9]{4}',value)
            if match:
                year, source = int(match[0]), key; break
        if year is not None:
            break
    ids = node.findall('PubmedData/ArticleIdList/ArticleId') + node.findall(base+'ELocationID')
    return dict(pmid=pmid, record_type=node.tag, title=content(node.find(base+'ArticleTitle')),
                abstracts=[dict(text=content(n),label=n.get('Label')) for n in abstract_nodes],
                keywords=values('MedlineCitation/KeywordList/Keyword'), mesh=headings,
                pubtypes=[dict(text=content(n),ui=n.get('UI')) for n in node.findall(base+'PublicationTypeList/PublicationType')],
                languages=values(base+'Language'), dates=dates, year=year, year_source=source,
                indexing_status=citation.get('Status'),
                ids={kind:sorted({content(n).casefold() if kind == 'doi' else content(n) for n in ids if (n.get('IdType') or n.get('EIdType')) == kind}) for kind in ('pmc','doi')},
                notices=[dict(type=n.get('RefType'),pmid=n.findtext('PMID'),source=n.findtext('RefSource')) for n in citation.findall('CommentsCorrectionsList/CommentsCorrections')],
                has_other_abstract=citation.find('OtherAbstract') is not None,
                has_vernacular_title=node.find(base+'VernacularTitle') is not None)


def evaluate(record, mesh, *, cutoff_year, deleted=False, pmid=None):
    if type(cutoff_year) is not int or not 1000 <= cutoff_year <= 9999:
        raise ValueError('Supply the calendar year of the cutoff listing date')
    if record is None:
        if not deleted or not pmid or not re.fullmatch(r'[1-9][0-9]*', pmid):
            raise ValueError('Only a deleted PMID may lack retained metadata')
        return dict(pmid=pmid, record_type='unknown', blocks=[], branches=[], reasons=['deleted_by_update'], disposition='deleted',
                    w_concepts=[], year=None, primary_stratum=None, metadata=None, has_abstract=False)
    if record['record_type'] == 'PubmedBookArticle':
        return dict(pmid=record['pmid'],record_type=record['record_type'],blocks=[],branches=[],
                    reasons=(['deleted_by_update'] if deleted else [])+['record_type_excluded'],
                    disposition='deleted' if deleted else 'excluded',w_concepts=[],year=None,
                    primary_stratum=None,metadata=record,has_abstract=None,
                    text_matches={},mesh_matches={},has_dx_imaging_qualifier=None)
    if record['record_type'] != 'PubmedArticle':
        raise ValueError('Unsupported record type')
    units = [record['title']] + [a['text'] for a in record['abstracts']] + record['keywords']
    hits = {block:[term for term in terms if any(matches(unit,term) for unit in units)] for block,terms in TERMS.items()}
    original_tokens = {t for unit in units for t in tokens(normalized(unit))}
    hits['C'] += sorted(original_tokens & {'CT','MDCT','CECT'})
    hits['A'] += sorted(original_tokens & {'AI'})
    mesh_uis = {h['ui'] for h in record['mesh']}
    mesh_hits = {block:sorted(mesh_uis & group) for block,group in mesh.groups.items()}
    blocks = {block for block in TERMS if hits[block] or mesh_hits.get(block)}
    if 'C' in blocks:
        blocks.add('IMG')
    branches = []
    for branch, needed in [('CORE',{'P','C'}),('AI',{'P','A'}),('MEASURE',{'P','M'})]:
        if needed <= blocks:
            branches.append(branch)
    if not branches and {'W','A','IMG'} <= blocks:
        branches.append('WORKFLOW')
    w = sorted({'reader study' if t == 'reader studies' else t for t in hits['W']})
    reasons = []
    if deleted: reasons.append('deleted_by_update')
    if not branches: reasons.append('not_candidate')
    types = {p['text'] for p in record['pubtypes']}
    notices = {n['type'] for n in record['notices']}
    if types & PUBTYPES: reasons.append('pubtype_excluded')
    if 'Retracted Publication' in types or 'RetractionIn' in notices: reasons.append('retracted')
    if record['mesh'] and mesh.animals in mesh_uis and mesh.humans not in mesh_uis: reasons.append('animal_only')
    if not record['languages']: reasons.append('language_missing')
    elif 'eng' not in record['languages']: reasons.append('language_non_english')
    if record['year'] is None: reasons.append('date_missing')
    elif record['year'] < 2000: reasons.append('year_out_of_range')
    elif record['year'] > cutoff_year: reasons.append('date_after_cutoff_year')
    if not record['mesh']: reasons.append('no_mesh')
    if record['indexing_status'] is not None: reasons.append('indexing_status_'+record['indexing_status'])
    for kind,reason in [('ErratumIn','erratum_linked'),('ExpressionOfConcernIn','concern_linked')]:
        if kind in notices: reasons.append(reason)
    for key in ('has_other_abstract','has_vernacular_title'):
        if record[key]: reasons.append(key)
    qualifier = None
    if 'CORE' in branches and record['mesh']:
        qualifier = any(h['ui'] in mesh.groups['P'] and any(q['text']=='diagnostic imaging' for q in h['qualifiers']) for h in record['mesh'])
        if qualifier: reasons.append('has_dx_imaging_qualifier')
    disposition = 'deleted' if deleted else 'excluded' if HARD & set(reasons) else 'candidate'
    return dict(pmid=record['pmid'],record_type=record['record_type'],blocks=sorted(blocks),branches=branches,reasons=reasons,
                disposition=disposition,w_concepts=w,year=record['year'],metadata=record,
                text_matches=hits,mesh_matches=mesh_hits,has_dx_imaging_qualifier=qualifier,
                has_abstract=any(normalized(a['text']) for a in record['abstracts']),
                primary_stratum=branches[0] if disposition == 'candidate' else None)


def select_records(records, mesh, *, cutoff_year, max_records=10000, max_xml_bytes=64*1024**2):
    """Bounded stage-1 preview. Records contain xml/deleted/pmid and source provenance."""
    if type(cutoff_year) is not int or not 1000 <= cutoff_year <= 9999:
        raise ValueError('Supply the calendar year of the cutoff listing date')
    rows, seen, xml_bytes = [], set(), 0
    for item in records:
        if len(rows) >= max_records:
            raise ValueError('Selection preview record limit exceeded; no partial result is returned')
        if item['xml'] is not None:
            xml_bytes += len(item['xml'].encode('utf-8')) if isinstance(item['xml'],str) else len(item['xml'])
        if xml_bytes > max_xml_bytes:
            raise ValueError('Selection preview XML byte limit exceeded; no partial result is returned')
        record = metadata(item['xml']) if item['xml'] is not None else None
        if record is not None and record['pmid'] != item['pmid']:
            raise ValueError('XML and catalog PMID differ')
        row = evaluate(record,mesh,cutoff_year=cutoff_year,deleted=item['deleted'],pmid=item['pmid'])
        if row['pmid'] in seen:
            raise ValueError('Duplicate PMID in reconciliation universe')
        seen.add(row['pmid'])
        row['provenance'] = {k:item[k] for k in ('source_file','source_sha256','source_seq') if k in item}
        rows.append(row)
    workflow = sorted((r for r in rows if r['disposition']=='candidate' and r['branches']==['WORKFLOW']),
                      key=lambda r:(-len(r['w_concepts']),-(r['year'] if r['year'] is not None else -1),int(r['pmid'])))
    for row in workflow[500:]:
        row['reasons'].append('workflow_capped_out'); row['disposition']='excluded'; row['primary_stratum']=None
    rows.sort(key=lambda r:int(r['pmid']))
    candidates = [r['pmid'] for r in rows if r['disposition']=='candidate']
    candidate_bytes = ''.join(p+'\n' for p in candidates).encode('ascii')
    counts = dict(universe=len(rows),final_records=sum(r['disposition']!='deleted' for r in rows),
                  deleted_pmids=sum(r['disposition']=='deleted' for r in rows),
                  dispositions=dict(Counter(r['disposition'] for r in rows)),
                  blocks=dict(Counter(b for r in rows for b in r['blocks'])),
                  branches=dict(Counter(b for r in rows for b in r['branches'])),
                  overlaps=dict(Counter('+'.join(r['branches']) for r in rows if len(r['branches'])>1)),
                  reasons=dict(Counter(code for r in rows for code in r['reasons'])),
                  record_types=dict(Counter(r['record_type'] for r in rows)),
                  book_records=sum(r['record_type']=='PubmedBookArticle' for r in rows),
                  excluded_books=sum(r['record_type']=='PubmedBookArticle' and r['disposition']=='excluded' for r in rows),
                  deleted_books=sum(r['record_type']=='PubmedBookArticle' and r['disposition']=='deleted' for r in rows),
                  publication_types=dict(Counter(p['text'] for r in rows if r['metadata'] for p in r['metadata'].get('pubtypes',[]))),
                  no_mesh_candidates_by_status=dict(Counter(r['metadata']['indexing_status'] or 'missing' for r in rows if r['disposition']=='candidate' and 'no_mesh' in r['reasons'])),
                  core_qualifier=dict(Counter('no_mesh' if 'no_mesh' in r['reasons'] else 'present' if r.get('has_dx_imaging_qualifier') else 'absent' for r in rows if 'CORE' in r['branches'])),
                  workflow_uncapped=len(workflow),workflow_capped=min(500,len(workflow)))
    return dict(rows=rows,candidate_pmids=candidates,candidate_pmids_sha256=hashlib.sha256(candidate_bytes).hexdigest(),counts=counts)


def identity(mesh):
    return dict(implementation=VERSION,policy_version='v0.1',
                policy_sha256=hashlib.sha256(POLICY.read_bytes()).hexdigest(),
                base_policy_sha256=hashlib.sha256(BASE_POLICY.read_bytes()).hexdigest(),
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                mesh_year=2026,mesh_sha256=mesh.sha256,mesh_source_kind=mesh.source_kind,
                resolved_descriptors=mesh.resolved,python=sys.version,unicode=unicodedata.unidata_version)
