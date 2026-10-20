import hashlib
from copy import deepcopy

import pytest

from src.retrieval.assisted_labeling import (
    LabelPreparationError, prepare_requests, assemble_proposal, render_review,
)


def example(text='Invented α finding. A separate limitation.'):
    source=dict(id='invented:1',title='Invented source',text=text,
                sha256=hashlib.sha256(text.encode()).hexdigest())
    response=dict(source_id=source['id'],source_sha256=source['sha256'], judgment='direct',
        rationale='Invented proposal, not a real source judgment.',
        spans=[dict(quote='Invented α finding.',grade='direct',concept_ids=['c1'])])
    return source,response


def test_requests_only_use_question_concepts_sources():
    s,r=example(); req=prepare_requests('Invented research question?',{'c1':'Invented concept'},[s],[])
    assert len(req)==1 and req[0]['source_sha256']==s['sha256']
    assert 'candidate-system answers' in req[0]['messages'][0]['content']


def test_unicode_quote_offsets_and_no_automatic_acceptance():
    s,r=example(); out=assemble_proposal({'c1':'Meaning'},[s],[r]); span=out['rows'][0]['spans'][0]
    assert s['text'][span['start']:span['end']]==span['quote']
    assert not out['human_accepted'] and not out['ready_for_evaluation']


@pytest.mark.parametrize('mutation', ['invented_quote','ambiguous','unknown_concept','changed_source',
    'duplicate_source','extra_field','missing_source','model_offsets'])
def test_invalid_proposals_rejected_without_content_in_error(mutation):
    s,r=example(); sources=[s]; responses=[r]
    if mutation=='invented_quote':r['spans'][0]['quote']='PRIVATE SECRET invented by model'
    if mutation=='ambiguous':
        s,r=example('Invented α finding. Invented α finding.');sources=[s];responses=[r]
    if mutation=='unknown_concept':r['spans'][0]['concept_ids']=['unknown']
    if mutation=='changed_source':s['text']+=' changed'
    if mutation=='duplicate_source':sources=[s,deepcopy(s)];responses=[r,deepcopy(r)]
    if mutation=='extra_field':r['accepted']=True
    if mutation=='missing_source':responses=[]
    if mutation=='model_offsets':r['spans'][0]['start']=0
    with pytest.raises(LabelPreparationError) as e:assemble_proposal({'c1':'Meaning'},sources,responses)
    assert 'SECRET' not in str(e.value) and 'Invented' not in str(e.value)


def test_missing_and_conflicting_evidence_stay_visible():
    s,r=example();r['spans'].append(dict(quote='A separate limitation.',grade='contradicting_or_limiting',concept_ids=['c1']))
    out=assemble_proposal({'c1':'Meaning','c2':'Absent'},[s],[r])
    assert out['missing_direct_concepts']==['c2'] and out['unresolved']
    assert not out['ready_for_evaluation']


def test_exposed_wording_rejected_before_request():
    s,_=example()
    with pytest.raises(LabelPreparationError):prepare_requests('EXPOSED?',{'c1':'Meaning'},[s],['exposed?'])


def test_review_escapes_question_and_source_instructions():
    s,r=example();s['title']='<script>alert(1)</script>'
    page=render_review('<img src="https://example.test">',assemble_proposal({'c1':'Meaning'},[s],[r]))
    assert '<script>' not in page and '<img' not in page
    assert '&lt;script&gt;' in page and 'human review required' in page


@pytest.mark.parametrize('mutation', ['source_type','judgment_type','grade_type','concepts_type'])
def test_malformed_types_fail_with_fixed_safe_error(mutation):
    s,r=example(); concepts={'c1':'Meaning'}; sources=[s]
    if mutation=='source_type':sources=[None]
    if mutation=='judgment_type':r['judgment']=['PRIVATE SECRET']
    if mutation=='grade_type':r['spans'][0]['grade']={'PRIVATE SECRET':True}
    if mutation=='concepts_type':concepts=[]
    with pytest.raises(LabelPreparationError) as e:assemble_proposal(concepts,sources,[r])
    assert str(e.value)=='Label preparation failed; review privately. No acceptance recorded.'
