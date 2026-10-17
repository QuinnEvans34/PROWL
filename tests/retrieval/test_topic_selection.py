"""Invented v0/v0.1 conformance records. No real literature or evaluation exposure."""
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

import pytest
from src.retrieval.topic_selection import MESH_NAMES, MeshIndex, evaluate, metadata, select_records, identity


def mesh_xml():
    names=sorted({n for values in MESH_NAMES.values() for n in values}|{'Animals','Humans'})
    rows=[]
    for i,name in enumerate(names):
        rows.append(f'<DescriptorRecord><DescriptorUI>TEST{i}</DescriptorUI><DescriptorName><String>{escape(name)}</String></DescriptorName><TreeNumberList><TreeNumber>T{i:03d}</TreeNumber></TreeNumberList></DescriptorRecord>')
    p=names.index('Pancreatic Neoplasms')
    for ui,tree in [('CHILD',f'T{p:03d}.001'),('NEARMISS',f'T{p:03d}0')]:
        rows.append(f'<DescriptorRecord><DescriptorUI>{ui}</DescriptorUI><DescriptorName><String>{ui}</String></DescriptorName><TreeNumberList><TreeNumber>{tree}</TreeNumber></TreeNumberList></DescriptorRecord>')
    return '<DescriptorRecordSet>'+''.join(rows)+'</DescriptorRecordSet>'


@pytest.fixture
def mesh_path(tmp_path):
    path=tmp_path/'invented-mesh-2026.xml';path.write_text(mesh_xml());return path


@pytest.fixture
def mesh(mesh_path):
    return MeshIndex.load(mesh_path,year=2026,source_kind='synthetic-test-fixture')


def article(title='Pancreatic lesion conspicuity on CT',pmid=1,lang='eng',year='2021',
            types=(),notices=(),headings='',extra='',article_extra='',abstracts=(),keywords=(),history=''):
    abstract=''.join(f'<AbstractText>{escape(text)}</AbstractText>' for text in abstracts)
    return (f'<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID>{pmid}</PMID><Article>'
            f'<ArticleTitle>{title}</ArticleTitle><Abstract>{abstract}</Abstract>'
            +(f'<Language>{lang}</Language>' if lang is not None else '')
            +(f'<Journal><JournalIssue><PubDate><Year>{year}</Year></PubDate></JournalIssue></Journal>' if year is not None else '')
            +'<PublicationTypeList>'+''.join(f'<PublicationType>{p}</PublicationType>' for p in types)+'</PublicationTypeList>'
            +article_extra+'</Article><KeywordList>'+''.join(f'<Keyword>{escape(k)}</Keyword>' for k in keywords)+'</KeywordList>'
            +f'<MeshHeadingList>{headings}</MeshHeadingList><CommentsCorrectionsList>'
            +''.join(f'<CommentsCorrections RefType="{n}"><PMID>999</PMID></CommentsCorrections>' for n in notices)
            +'</CommentsCorrectionsList>'+extra+'</MedlineCitation><PubmedData>'+history+'</PubmedData></PubmedArticle>')


def heading(mesh,name,qualifier=None,ui=None):
    ui=ui or mesh.resolved[name]['ui']
    return f'<MeshHeading><DescriptorName UI="{ui}" MajorTopicYN="Y">{escape(name)}</DescriptorName>'+(
        f'<QualifierName UI="TESTQ">{qualifier}</QualifierName>' if qualifier else '')+'</MeshHeading>'


@pytest.mark.parametrize('label,title,branches',[
    ('E1','Pancreatic lesion conspicuity on CT',['CORE']),
    ('E2','Pancreatic lesion conspicuity on MRI',[]),
    ('E3','Deep learning for pancreas segmentation',['AI']),
    ('E4','Interobserver variability of pancreas contours',['MEASURE']),
    ('E5','Automation bias when radiologists review deep learning output',['WORKFLOW']),
    ('E12','PET/CT of pancreatic cancer',['CORE']),
    ('E13','A UNet for pancreas delineation',['AI','MEASURE']),
    ('E14','pancreatic ct findings',[]),
    ('E17','pancreatic neural networks on CT',['CORE','AI']),
    ('E22','Computer assisted reading of deep learning output in radiology',['WORKFLOW']),
    ('E5c','Automation bias in AI-assisted CT reading',['WORKFLOW']),
    ('E28','ai-assisted ct reading with automation bias',[]),
    ('E29','AIDS and XAI in pancreatic CT',['CORE']),
    ('E30','AI for pancreatic CT',['CORE','AI']),
    ('E31a','Intra-observer agreement of pancreas volume',['MEASURE']),
    ('E31b','intra observer agreement of pancreas volume',['MEASURE']),
    ('E32','Reader studies of deep learning in radiology',['WORKFLOW']),
])
def test_section12_text_oracles(mesh,label,title,branches):
    row=evaluate(metadata(article(title)),mesh,cutoff_year=2026)
    assert row['branches']==branches,label
    assert row['disposition']==('candidate' if branches else 'excluded')
    assert ('not_candidate' in row['reasons']) == (not branches)


@pytest.mark.parametrize('changes,code',[
    ({'types':['Editorial']},'pubtype_excluded'), # E6
    ({'notices':['RetractionIn']},'retracted'), # E7
    ({'lang':'ger'},'language_non_english'), # E10
    ({'year':'1998'},'year_out_of_range'), # E11
    ({'types':['Journal Article','Comment']},'pubtype_excluded'), # E21
    ({'types':['Retracted Publication']},'retracted'),
])
def test_hard_exclusions_preserve_branches(mesh,changes,code):
    row=evaluate(metadata(article(**changes)),mesh,cutoff_year=2026)
    assert row['branches']==['CORE'] and row['disposition']=='excluded' and code in row['reasons']


def test_mesh_oracles_and_qualifier_scope(mesh):
    for human in (False,True): # E8/E20
        hs=heading(mesh,'Animals')+(heading(mesh,'Humans') if human else '')
        row=evaluate(metadata(article(headings=hs)),mesh,cutoff_year=2026)
        assert ('animal_only' in row['reasons']) == (not human)
    row=evaluate(metadata(article('Organ phantom',headings=heading(mesh,'Pancreas','diagnostic imaging'))),mesh,cutoff_year=2026)
    assert row['branches']==[] and 'has_dx_imaging_qualifier' not in row['reasons'] # E18
    for ui,expected in [('CHILD',['CORE']),('NEARMISS',[])]: # E19/dot boundary
        row=evaluate(metadata(article('Study on CT',headings=heading(mesh,'child',ui=ui))),mesh,cutoff_year=2026)
        assert row['branches']==expected
    row=evaluate(metadata(article('Study on CT',headings=heading(mesh,'Pancreas','diagnostic imaging'))),mesh,cutoff_year=2026)
    assert row['has_dx_imaging_qualifier'] is True


def test_missing_fields_and_nonmatched_fields(mesh):
    row=evaluate(metadata(article(lang=None,year=None)),mesh,cutoff_year=2026)
    assert row['disposition']=='candidate' and {'no_mesh','language_missing','date_missing'} <= set(row['reasons']) # E9-11
    xml=article('Tumour imaging',extra='<OtherAbstract><AbstractText>pancreatic CT</AbstractText></OtherAbstract>',article_extra='<VernacularTitle>pancreatic CT</VernacularTitle>')
    row=evaluate(metadata(xml),mesh,cutoff_year=2026)
    assert row['disposition']=='excluded' and {'has_other_abstract','has_vernacular_title'} <= set(row['reasons']) # E16


def test_date_oracles_precedence_and_invalid_years(mesh):
    for value,year,disposition in [('2019 Nov-Dec',2019,'candidate'),('Winter 1998-1999',1998,'excluded')]: # E23
        extra=f'<Journal><JournalIssue><PubDate><MedlineDate>{value}</MedlineDate></PubDate></JournalIssue></Journal>'
        row=evaluate(metadata(article(year=None,article_extra=extra)),mesh,cutoff_year=2026)
        assert row['year']==year and row['disposition']==disposition
    row=evaluate(metadata(article(year='2027')),mesh,cutoff_year=2026) # E24
    assert row['disposition']=='candidate' and 'date_after_cutoff_year' in row['reasons']
    extra='<ArticleDate><Year>2020</Year></ArticleDate>'
    m=metadata(article(year='２０１９',article_extra=extra))
    assert m['year']==2020 and m['year_source']=='article_year' and m['dates']['journal_year']==['２０１９']
    assert metadata(article(year='1998',article_extra=extra))['year']==1998
    assert metadata(article(year=None,history='<History><PubMedPubDate PubStatus="pubmed"><Year>2018</Year></PubMedPubDate></History>'))['year']==2018


def item(pmid,xml=None,deleted=False):
    return dict(pmid=str(pmid),xml=xml,deleted=deleted)


def test_workflow_cap_after_exclusions_concepts_and_order(mesh):
    # E25/E26/E33/E34: duplicates of reader-study forms cannot buy a cap slot.
    strong='Reader study and automation bias in deep learning radiology'
    rows=[item(i,article(strong,pmid=i,year='2020')) for i in range(1,501)]
    rows += [item(501,article('Reader study and reader studies in deep learning radiology',pmid=501,year='2026'))]
    rows += [item(502,article(strong,pmid=502,types=['Editorial'],year='2026'))]
    rows += [item(503,article(strong,pmid=503,year=None))]
    report=select_records(reversed(rows),mesh,cutoff_year=2026)
    assert report['candidate_pmids']==[str(i) for i in range(1,501)]
    assert report['counts']['workflow_uncapped']==502 and report['counts']['workflow_capped']==500
    capped=report['rows'][500]
    assert len(capped['w_concepts'])==1 and 'workflow_capped_out' in capped['reasons'] and 'not_candidate' not in capped['reasons']
    assert 'workflow_capped_out' not in report['rows'][501]['reasons']
    # Numerical PMID tie-break at the exact cap boundary, regardless of iteration order.
    tied=[item(i,article(strong,pmid=i)) for i in range(501,0,-1)]
    assert select_records(tied,mesh,cutoff_year=2026)['candidate_pmids']==[str(i) for i in range(1,501)]


def test_deleted_precedence_all_reasons_no_abstract_and_reconciliation(mesh):
    rows=[item(1,article(types=['Comment'],lang='ger',year='1998'),True),item(2,None,True),item(10,article(pmid=10,abstracts=[]))]
    report=select_records(rows,mesh,cutoff_year=2026)
    assert report['rows'][0]['disposition']=='deleted' # E15
    assert {'deleted_by_update','pubtype_excluded','language_non_english','year_out_of_range'} <= set(report['rows'][0]['reasons'])
    assert report['rows'][2]['disposition']=='candidate' and not report['rows'][2]['has_abstract']
    # E27's stage-1 invariant; rights-based stage 2 is intentionally not executed here.
    assert report['counts']['universe']==3 and report['counts']['deleted_pmids']==2
    assert report['candidate_pmids_sha256']==hashlib.sha256(b'10\n').hexdigest()


def test_token_boundaries_units_markup_and_exact_spellings(mesh):
    for title in ('pancreatic Ct','pancreatic CTs','pancreatic interrater','pancreatic XAI'):
        assert evaluate(metadata(article(title)),mesh,cutoff_year=2026)['disposition']=='excluded'
    m=metadata(article('pancreas computed',abstracts=['tomography'],keywords=['deep','learning']))
    assert evaluate(m,mesh,cutoff_year=2026)['disposition']=='excluded'
    m=metadata(article('Ｐａｎｃｒｅａｓ <i>CT</i>',abstracts=[' \t ']))
    row=evaluate(m,mesh,cutoff_year=2026)
    assert row['branches']==['CORE'] and not row['has_abstract']
    m=metadata(article('pancreas',article_extra='<Abstract><AbstractText Label="CT">irrelevant</AbstractText></Abstract>'))
    assert evaluate(m,mesh,cutoff_year=2026)['branches']==[]
    for phrase in ('computerassisted reading','computer-assisted reading','computer assisted reading'):
        assert evaluate(metadata(article(phrase+' of deep learning in radiology')),mesh,cutoff_year=2026)['branches']==['WORKFLOW']


def test_notice_ids_and_metadata_retention(mesh):
    m=metadata(article(notices=['ErratumIn','ExpressionOfConcernIn'],history='<ArticleIdList><ArticleId IdType="pmc">PMC999</ArticleId><ArticleId IdType="doi">10.X/ABC</ArticleId></ArticleIdList>',article_extra='<ELocationID EIdType="doi">10.x/abc</ELocationID><Language>ger</Language>',abstracts=['CT findings']))
    row=evaluate(m,mesh,cutoff_year=2026)
    assert row['disposition']=='candidate' and {'erratum_linked','concern_linked'} <= set(row['reasons'])
    assert m['ids']=={'pmc':['PMC999'],'doi':['10.x/abc']}


def test_mesh_fail_closed_and_identity(mesh_path,mesh):
    original=mesh_path.read_text()
    for changed in [original.replace('Pancreas','pancreas'),original.replace('</DescriptorRecordSet>',original.split('<DescriptorRecordSet>')[1])]:
        mesh_path.write_text(changed)
        with pytest.raises(ValueError): MeshIndex.load(mesh_path,year=2026)
    mesh_path.write_text(original)
    with pytest.raises(ValueError): MeshIndex.load(mesh_path,year=2025)
    details=identity(mesh)
    assert details['unicode'] and details['python'] and details['mesh_source_kind']=='synthetic-test-fixture'
    assert details['mesh_sha256']==hashlib.sha256(original.encode()).hexdigest()


def test_unknown_book_entities_duplicates_and_limits(mesh):
    for xml in ['<PubmedBookArticle/>','<!DOCTYPE x [<!ENTITY e "text">]><PubmedArticle/>']:
        with pytest.raises(Exception): metadata(xml)
    one=item(1,article())
    with pytest.raises(ValueError,match='Duplicate'): select_records([one,one],mesh,cutoff_year=2026)
    with pytest.raises(ValueError,match='limit'): select_records([one],mesh,cutoff_year=2026,max_records=0)
    with pytest.raises(ValueError,match='differ'): select_records([item(2,article())],mesh,cutoff_year=2026)
    with pytest.raises(ValueError,match='byte limit'): select_records([one],mesh,cutoff_year=2026,max_xml_bytes=10)
    with pytest.raises(ValueError,match='calendar year'): select_records([],mesh,cutoff_year=None)


def test_catalog_selection_preview_outputs_and_no_silent_truncation(tmp_path,mesh_path):
    import gzip
    import importlib.util
    from src.retrieval.pubmed_catalog import connect,bind,apply_file
    script=Path(__file__).resolve().parents[2]/'scripts/retrieval/preview_topic_selection.py'
    spec=importlib.util.spec_from_file_location('selection_preview',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    catalog=tmp_path/'catalog.sqlite'
    db=connect(catalog);bind(db,b'invented-manifest')
    path=tmp_path/'pubmed26n0001.xml.gz'
    path.write_bytes(gzip.compress(('<PubmedArticleSet>'+article(pmid=10)+article(pmid=2)+'<DeleteCitation><PMID>2</PMID><PMID>3</PMID></DeleteCitation></PubmedArticleSet>').encode()))
    apply_file(db,path,hashlib.sha256(path.read_bytes()).hexdigest(),0);db.close()
    output=tmp_path/'selection'
    with pytest.raises(ValueError,match='limit'): module.preview(catalog,mesh_path,output,2026,max_records=2)
    assert not output.exists()
    result=module.preview(catalog,mesh_path,output,2026)
    assert result['counts']['universe']==3 and result['counts']['deleted_pmids']==2
    assert result['preview'] and not result['official_selection_frozen'] and not result['rights_qualified']
    assert (output/'candidate-pmids.txt').read_bytes()==b'10\n'
    rows=[json.loads(line) for line in (output/'records.jsonl').read_text().splitlines()]
    assert [r['pmid'] for r in rows]==['2','3','10']
    assert rows[0]['provenance']['source_seq']==2
    assert result['identity']['catalog']['manifest_sha256']==hashlib.sha256(b'invented-manifest').hexdigest()
    with pytest.raises(FileExistsError): module.preview(catalog,mesh_path,output,2026)


def book(pmid):
    return (f'<PubmedBookArticle><BookDocument><PMID>{pmid}</PMID>'
            '<ArticleTitle>Pancreas CT segmentation</ArticleTitle>'
            '<Language>eng</Language><Abstract><AbstractText>Pancreatic CT</AbstractText></Abstract>'
            '</BookDocument></PubmedBookArticle>')


def test_v01_books_excluded_without_journal_field_assumptions(mesh):
    report=select_records([item(1,book(1)),item(2,book(2),True),item(3,None,True),item(4,article(pmid=4))],mesh,cutoff_year=2026)
    live,deleted,unknown,journal=report['rows']
    assert live['disposition']=='excluded' and live['reasons']==['record_type_excluded']
    assert live['blocks']==live['branches']==[] and live['has_abstract'] is None
    assert deleted['disposition']=='deleted' and deleted['reasons']==['deleted_by_update','record_type_excluded']
    assert unknown['record_type']=='unknown' and unknown['reasons']==['deleted_by_update']
    assert journal['disposition']=='candidate' and report['candidate_pmids']==['4']
    assert report['counts']['book_records']==2
    assert report['counts']['excluded_books']==report['counts']['deleted_books']==1
    assert sum(report['counts']['dispositions'].values())==report['counts']['universe']==4
    assert identity(mesh)['policy_version']=='v0.1' and identity(mesh)['base_policy_sha256']


@pytest.mark.parametrize('xml',[
    '<PubmedBookArticle><BookDocument><PMID>wrong</PMID></BookDocument></PubmedBookArticle>',
    '<PubmedBookArticle><BookDocument/></PubmedBookArticle>',
    '<UnknownRecord><PMID>1</PMID></UnknownRecord>',
])
def test_v01_unknown_types_and_invalid_book_identity_still_stop(xml):
    with pytest.raises(ValueError): metadata(xml)


def test_v01_catalog_book_delete_and_record_type_replacement(tmp_path,mesh):
    import gzip
    from src.retrieval.pubmed_catalog import connect,bind,apply_file
    db=connect(tmp_path/'catalog.sqlite');bind(db,b'invented-v01')
    bodies=[book(1)+book(2)+article(pmid=3),
            '<DeleteCitation><PMID>1</PMID><PMID>2</PMID></DeleteCitation>'+article(pmid=2)+book(3)]
    for i,body in enumerate(bodies,1):
        path=tmp_path/f'pubmed26n{i:04d}.xml.gz'
        path.write_bytes(gzip.compress(('<PubmedArticleSet>'+body+'</PubmedArticleSet>').encode()))
        apply_file(db,path,hashlib.sha256(path.read_bytes()).hexdigest(),i-1)
    rows=db.execute('SELECT pmid,xml,0 FROM documents UNION ALL SELECT pmid,xml,1 FROM deleted').fetchall()
    report=select_records([item(pmid,xml,bool(deleted)) for pmid,xml,deleted in rows],mesh,cutoff_year=2026)
    assert [(r['pmid'],r['record_type'],r['disposition']) for r in report['rows']]==[
        ('1','PubmedBookArticle','deleted'),('2','PubmedArticle','candidate'),('3','PubmedBookArticle','excluded')]
    assert 'Pancreas CT segmentation' in db.execute('SELECT xml FROM deleted WHERE pmid="1"').fetchone()[0]
    assert report['candidate_pmids']==['2'] and report['counts']['universe']==3
    db.close()
