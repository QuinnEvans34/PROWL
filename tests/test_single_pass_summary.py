import json
import pytest
from jsonschema import ValidationError
from src.retrieval.single_pass_summary import generate,SinglePassAnswers,MODEL,MODEL_SHA,REVIEW_PROMPT,REPAIR_PROMPT
E=[dict(rank=1,record=dict(text='The invented gland releases digestive enzymes.',citation=dict(title='Synthetic source')))]
A=dict(coverage='supported',limitation='',claims=[dict(text='It releases enzymes that help digestion.',sentence_ids=['P1S1'])])
def accepted_review(payload):
    body = json.loads(payload['messages'][1]['content'])
    return dict(safe=True, status_appropriate=True, coverage=body['draft']['coverage'],
        limitation=body['draft']['limitation'], checks=[dict(claim=c['claim'],
            explanation='The cited synthetic passage supports this complete claim.',
            supported=True, relevant=True, scope_preserved=True) for c in body['claims']])


def model_reply(answer, payload):
    value = accepted_review(payload) if payload['messages'][0]['content'] == REVIEW_PROMPT else answer
    return dict(done=True, done_reason='stop', model=MODEL, message=dict(content=json.dumps(value)))


def run(answer=A):
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        return model_reply(answer,payload)
    return generate('What does it do?',E,call),calls

def test_generation_and_separate_review_without_thinking():
    answer,calls=run();assert len(calls)==2 and all(c['think'] is False for c in calls)
    assert all(c['options']['num_predict']==512 for c in calls)
    body=json.loads(calls[0]['messages'][1]['content'])
    assert body['question']=='What does it do?' and body['passages'][0]['sentences'][0]['text']==E[0]['record']['text']
    assert answer['validation']=='citation_binding_and_model_review' and answer['review']=='accepted'
    review_body=json.loads(calls[1]['messages'][1]['content'])
    assert review_body['question']=='What does it do?'
    assert review_body['passages'][0]['text']==E[0]['record']['text']
    assert review_body['claims'][0]['citations'][0]['quote']==E[0]['record']['text']

@pytest.mark.parametrize('kind',['unknown','quote','coverage','duplicate'])
def test_bad_binding_rejected(kind):
    a=json.loads(json.dumps(A));c=a['claims'][0]
    if kind=='unknown':c['sentence_ids']=['P2S1']
    if kind=='quote':c['quote']='This supporting text is entirely invented.'
    if kind=='coverage':a['coverage']='none'
    if kind=='duplicate':c['sentence_ids'].append('P1S1')
    with pytest.raises(Exception):run(a)

def test_gap_and_partial():
    assert run(dict(coverage='none',claims=[],limitation='No supporting evidence.'))[0]['status']=='insufficient'
    a=json.loads(json.dumps(A));a.update(coverage='partial',limitation='No measurement range was found.')
    assert run(a)[0]['coverage']=='partial'

def test_boundary_never_calls_model():
    class Search:
        def search(self,r):return dict(state='not_searched',answer=None,generation='not_called')
    def forbidden(*a):raise AssertionError('Model must not run')
    assert SinglePassAnswers(Search(),forbidden).answer(dict(question='Diagnose me'))['generation']=='not_called'

def test_failure_preserves_evidence_and_releases_lock():
    class Search:
        def search(self,r):return dict(state='evidence_unassessed',record_selection=dict(status='dense_fallback'),evidence=E)
    def fail(*a):raise TimeoutError()
    service=SinglePassAnswers(Search(),fail)
    for _ in range(2):
        result=service.answer(dict(question='What does it do?'))
        assert result['generation']=='unavailable' and result['evidence']==E

def test_clarification_never_calls_model():
    class Search:
        def search(self,r):return dict(state='evidence_unassessed',record_selection=dict(status='dense_fallback',reason='comparison_groups_unspecified'),evidence=E,generation='not_called')
    def forbidden(*a):raise AssertionError('Model must not run')
    assert SinglePassAnswers(Search(),forbidden).answer(dict(question='Which is bigger?'))['generation']=='not_called'


def test_resolves_exact_contiguous_span_including_qualification():
    from src.retrieval.single_pass_summary import source_sentences
    evidence=[dict(rank=2,record=dict(text='The organ is visible [1]. However, the boundary can be uncertain. This study used CT [2].',citation=dict(title='Invented')))]
    sources, lookup=source_sentences(evidence)
    assert [x['id'] for x in sources[0]['sentences']]==['P2S1','P2S2','P2S3']
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        answer=dict(claims=[dict(text='The organ is visible in this CT study.',sentence_ids=['P2S1','P2S3'])],coverage='supported',limitation='')
        return model_reply(answer,payload)
    result=generate('What was visible?',evidence,call)
    assert result['claims'][0]['citations']==[dict(rank=2,quote=evidence[0]['record']['text'])]
    assert 'sentence_ids' not in result['claims'][0]


def test_supported_answer_cannot_include_spurious_limitation():
    a=json.loads(json.dumps(A));a['limitation']='The wording differs.'
    with pytest.raises(ValidationError):run(a)


@pytest.mark.parametrize('count', [6, 7, 9, 20])
def test_reviewed_record_keeps_all_companion_passages(count):
    evidence = [dict(rank=n, record=dict(
        text=f'The invented gland releases enzymes in study group {n}.',
        citation=dict(title=f'Invented study {n}'))) for n in range(1, count + 1)]
    evidence[-1]['record']['text'] += ' This finding applies only to the study group.'
    calls = []
    def call(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name=MODEL, digest=MODEL_SHA)])
        calls.append(payload)
        if payload['messages'][0]['content'] == REVIEW_PROMPT:
            return model_reply(A,payload)
        body = json.loads(payload['messages'][1]['content'])
        assert len(body['passages']) == count
        assert [p['rank'] for p in body['passages']] == list(range(1, count + 1))
        assert body['passages'][-1]['sentences'][-1]['text'] == 'This finding applies only to the study group.'
        answer = dict(coverage='supported', limitation='', claims=[dict(
            text='In the cited study group, the invented gland releases enzymes.',
            sentence_ids=[f'P{count}S1', f'P{count}S2'])])
        return model_reply(answer,payload)
    result = generate('What does the study report?', evidence, call)
    assert len(calls) == 2
    assert result['claims'][0]['citations'] == [dict(rank=count, quote=evidence[-1]['record']['text'])]


@pytest.mark.parametrize('kind', ['passages', 'characters', 'sentences'])
def test_reviewed_record_still_rejects_context_over_budget_before_provider(kind):
    def forbidden(*args):
        pytest.fail('Over-budget evidence must not call the provider')
    if kind == 'passages':
        evidence = [dict(rank=n, record=dict(text='The invented gland releases enzymes.',
            citation=dict(title='Invented study'))) for n in range(1, 22)]
    elif kind == 'characters':
        evidence = [dict(rank=1, record=dict(text='A' * 16001,
            citation=dict(title='Invented study')))]
    else:
        evidence = [dict(rank=1, record=dict(text='The invented gland releases enzymes. ' * 101,
            citation=dict(title='Invented study')))]
    with pytest.raises(ValueError, match='budget'):
        generate('What does the study report?', evidence, forbidden)


def test_followup_keeps_current_question_and_prior_questions_separate_from_evidence():
    context = dict(previous_questions=['What does the pancreas do?'])
    calls = []
    def call(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name=MODEL, digest=MODEL_SHA)])
        calls.append(payload)
        return model_reply(A,payload)
    generate('And what about digestion?', E, call, question_context=context)
    body = json.loads(calls[0]['messages'][1]['content'])
    assert body['question'] == 'And what about digestion?'
    assert body['question_context'] == context
    assert body['passages'][0]['sentences'][0]['text'] == E[0]['record']['text']
    assert 'never evidence' in calls[0]['messages'][0]['content']
    reviewed=json.loads(calls[1]['messages'][1]['content'])
    assert reviewed['question']==body['question'] and reviewed['question_context']==context


def test_answer_service_searches_resolved_question_and_generates_for_current_question():
    request = dict(question='And what about digestion?')
    context = dict(previous_questions=['What does the pancreas do?'],
        resolved_question='What does the pancreas do for digestion?')
    class Search:
        def search(self, value):
            assert value == dict(question=context['resolved_question'])
            return dict(state='evidence_unassessed',
                record_selection=dict(status='dense_fallback'), evidence=E)
    def compose(question, evidence, *, question_context):
        assert question == request['question']
        assert evidence == E and question_context == context
        return dict(claims=[])
    result = SinglePassAnswers(Search(), compose).answer(request, question_context=context)
    assert result['generation'] == 'completed'
    assert result['question'] == request['question']
    assert result['context'] == context and result['context'] is not context


def test_contextual_refusal_preserves_current_question_and_never_calls_generation():
    request = dict(question='Does that mean this case has cancer?')
    context = dict(previous_questions=['What is a pancreatic lesion?'],
        resolved_question='Does that pancreatic lesion mean this case has cancer?')
    class Search:
        def search(self, value):
            assert value['question'] == context['resolved_question']
            return dict(question=value['question'], state='not_searched',
                reason='out_of_scope', generation='not_called', evidence=[], answer=None)
    def forbidden(*args, **kwargs):
        pytest.fail('A refused follow-up must not call generation')
    result = SinglePassAnswers(Search(), forbidden).answer(request, question_context=context)
    assert result['question'] == request['question']
    assert result['state'] == 'not_searched' and result['generation'] == 'not_called'


def test_twenty_passages_at_sentence_budget_keep_final_qualification():
    evidence = [dict(rank=n, record=dict(
        text='The invented study observed gland activity. ' * 4 +
            'The observation applies only to the study group.',
        citation=dict(title=f'Invented study {n}'))) for n in range(1, 21)]
    def call(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name=MODEL, digest=MODEL_SHA)])
        if payload['messages'][0]['content'] == REVIEW_PROMPT:
            return model_reply(A,payload)
        body = json.loads(payload['messages'][1]['content'])
        assert sum(len(p['sentences']) for p in body['passages']) == 100
        answer = dict(coverage='supported', limitation='', claims=[dict(
            text='The observation applies only to the study group.', sentence_ids=['P20S5'])])
        return model_reply(answer,payload)
    result = generate('To whom does the observation apply?', evidence, call)
    assert result['claims'][0]['citations'] == [dict(rank=20,
        quote='The observation applies only to the study group.')]


def test_real_citation_cannot_support_an_invented_numeric_claim():
    a = json.loads(json.dumps(A))
    a['claims'][0]['text'] = 'The invented gland releases 99 digestive enzymes.'
    with pytest.raises(ValueError, match='number absent'):
        run(a)


@pytest.mark.parametrize('claim,accepted', [
    ('In one study, gland volume ranged from 1000 to 1200 mL.', True),
    ('In one study, gland volume ranged from 1000.00 to 1200.0 mL.', True),
    ('The normal gland volume ranges from 1000 to 1500 mL.', False),
])
def test_numeric_backstop_preserves_quoted_ranges_and_decimal_formatting(claim, accepted):
    evidence = [dict(rank=1, record=dict(
        text='An invented study reported gland volumes of 1,000.0 to 1,200.00 mL.',
        citation=dict(title='Invented study')))]
    def call(path, payload=None):
        if path == 'tags':
            return dict(models=[dict(name=MODEL, digest=MODEL_SHA)])
        answer = dict(coverage='supported', limitation='', claims=[dict(
            text=claim, sentence_ids=['P1S1'])])
        return model_reply(answer,payload)
    if accepted:
        assert generate('What volume did the study report?', evidence, call)['status'] == 'summarized'
    else:
        with pytest.raises(ValueError, match='number absent'):
            generate('What is the normal gland volume?', evidence, call)


@pytest.mark.parametrize('failure,question,text,quote', [
    ('relevant', 'Does the organ produce a hormone?',
     'In the disease group, organ volume decreases.',
     'In one disease group, organ volume was lower than in controls.'),
    ('scope_preserved', 'What happens if pancreatic function is lost?',
     'Loss of pancreatic function causes pancreatic cancer.',
     'Aging-related changes may predispose individuals to pancreatic cancer.'),
    ('scope_preserved', 'What are signs of disease?',
     'The signs of disease are duct changes on CT.',
     'In the selected isoattenuating tumor study, CT showed duct changes.'),
    ('supported', 'Explain organ function.',
     'The organ releases enzymes and insulin.',
     'The organ has exocrine and endocrine functions.'),
])
def test_guard_or_review_never_presents_wrong_or_generalized_prose(failure,question,text,quote):
    evidence=[dict(rank=1,record=dict(text=quote,citation=dict(title='Synthetic restricted study')))]
    draft=dict(coverage='supported',limitation='',claims=[dict(text=text,sentence_ids=['P1S1'])])
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        if payload['messages'][0]['content'] != REVIEW_PROMPT:
            return model_reply(draft,payload)
        review=accepted_review(payload)
        review['checks'][0][failure]=False
        review['status_appropriate']=False
        review['coverage']='none'
        review['limitation']='The cited study does not support that general explanation of the requested topic.'
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(review)))
    result=generate(question,evidence,call)
    assert len(calls)<=2
    if result['review']=='source_fallback':
        assert result['coverage']=='partial' and result['status']=='summarized'
        assert result['claims'][0]['text']=='Source wording from “Synthetic restricted study”: '+quote
        assert result['provenance']=='model_selected_source_fallback'
    else:
        assert result['claims']==[] and result['coverage']=='none' and result['status']=='insufficient'
    assert evidence[0]['record']['text']==quote


def test_review_can_keep_a_useful_scoped_partial_answer():
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        if payload['messages'][0]['content'] != REVIEW_PROMPT:return model_reply(A,payload)
        review=accepted_review(payload)
        review.update(coverage='partial',limitation='The retrieved source describes digestion but does not explain the endocrine function.')
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(review)))
    result=generate('Explain the gland functions.',E,call)
    assert result['review']=='accepted' and result['coverage']=='partial'
    assert result['claims'][0]['text']==A['claims'][0]['text'] and result['limitation']


@pytest.mark.parametrize('failure',['missing_check','wrong_id','blank_explanation','unsupported_coverage'])
def test_malformed_review_fails_closed(failure):
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        if payload['messages'][0]['content'] != REVIEW_PROMPT:return model_reply(A,payload)
        review=accepted_review(payload)
        if failure=='missing_check':review['checks']=[]
        if failure=='wrong_id':review['checks'][0]['claim']=2
        if failure=='blank_explanation':review['checks'][0]['explanation']=' '
        if failure=='unsupported_coverage':review.update(coverage='partial',limitation='')
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(review)))
    with pytest.raises((ValueError,ValidationError)):
        generate('What does it do?',E,call)


def test_empty_draft_is_reviewed_against_available_passages():
    draft=dict(coverage='none',claims=[],limitation='The retrieved passages contain no relevant information.')
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        if payload['messages'][0]['content'] != REVIEW_PROMPT:return model_reply(draft,payload)
        body=json.loads(payload['messages'][1]['content'])
        assert body['claims']==[] and body['passages'][0]['text']==E[0]['record']['text']
        review=accepted_review(payload)
        review.update(status_appropriate=False,coverage='none',
            limitation='The retrieved passage is relevant, but a checked answer was not produced.')
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(review)))
    result=generate('What does it secrete?',E,call)
    assert result['review']=='rejected' and result['claims']==[]
    assert 'contain no relevant' not in result['limitation']


def test_review_failure_preserves_evidence_and_releases_answer_lock():
    class Search:
        def search(self,r):return dict(state='evidence_unassessed',record_selection=dict(status='dense_fallback'),evidence=E)
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        if payload['messages'][0]['content']==REVIEW_PROMPT:raise TimeoutError('Review deadline')
        return model_reply(A,payload)
    service=SinglePassAnswers(Search(),lambda q,e:generate(q,e,call))
    for _ in range(2):
        result=service.answer(dict(question='What does it do?'))
        assert result['generation']=='unavailable' and result['answer'] is None
        assert result['evidence']==E and not service.lock.locked()


def test_review_shares_the_original_total_deadline(monkeypatch):
    from src.retrieval import single_pass_summary as summary
    now=[0.0]
    monkeypatch.setattr(summary,'monotonic',lambda:now[0])
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        now[0]=61.0 if payload['messages'][0]['content']==REVIEW_PROMPT else 40.0
        return model_reply(A,payload)
    with pytest.raises(TimeoutError,match='Summary deadline'):
        generate('What does it do?',E,call)
    assert len(calls)==2


@pytest.mark.parametrize('claim,quote,title,question', [
    ('The pancreas releases insulin and digestive enzymes.',
     'The pancreas secretes digestive enzymes and hormones.', 'Organ physiology', 'What does the pancreas do?'),
    ('Pancreatic failure causes autodigestion and tissue injury.',
     'Acute pancreatitis is an inflammatory disorder in which autodigestion injures pancreatic tissue and leads to dysfunction.',
     'Acute pancreatitis research', 'What happens if pancreatic function is lost?'),
    ('Clear signs of pancreatic disease include swelling and enhanced ducts.',
     'Typical features include swelling and enhanced ducts.',
     'Imaging diagnosis of autoimmune pancreatitis', 'What are clear signs of pancreatic disease?'),
])
def test_deterministic_guard_cannot_be_overridden_by_a_model_acceptance(claim,quote,title,question):
    evidence=[dict(rank=1,record=dict(text=quote,citation=dict(title=title)))]
    draft=dict(coverage='supported',limitation='',claims=[dict(text=claim,sentence_ids=['P1S1'])])
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        if payload['messages'][0]['content']==REVIEW_PROMPT:
            pytest.fail('A model acceptance cannot override the deterministic guard')
        return model_reply(draft,payload)
    result=generate(question,evidence,call)
    assert len(calls)==2 and result['review']=='source_fallback'
    assert result['coverage']=='partial' and result['validation']=='exact_citations_and_source_title'
    assert result['provenance']=='model_selected_source_fallback'
    assert result['claims'][0]['text']==f'Source wording from “{title}”: {quote}'
    assert result['claims'][0]['citations']==[dict(rank=1,quote=quote)]
    assert result['limitation']=='These are source excerpts from the cited articles, not a complete answer to your question.'


@pytest.mark.parametrize('term',['insulin','blood sugar','glucagon','diabetes','pancreatitis','cancer','amylase','lipase','malabsorption'])
def test_new_biomedical_content_must_be_present_in_cited_quotations(term):
    from src.retrieval.single_pass_summary import support_backstop
    evidence=[dict(rank=1,record=dict(text='The organ has endocrine functions.',citation=dict(title='Organ physiology')))]
    answer=dict(claims=[dict(text='The organ regulates '+term+'.',citations=[dict(rank=1,quote=evidence[0]['record']['text'])])])
    assert support_backstop('Explain organ function.',evidence,answer)=='entity_not_quoted'


def test_quoted_biomedical_synonyms_preserve_a_valid_claim():
    from src.retrieval.single_pass_summary import support_backstop
    quote='Insulin regulates glucose levels.'
    evidence=[dict(rank=1,record=dict(text=quote,citation=dict(title='Organ physiology')))]
    answer=dict(claims=[dict(text='Insulin regulates blood sugar levels.',citations=[dict(rank=1,quote=quote)])])
    assert support_backstop('What does insulin regulate?',evidence,answer) is None


@pytest.mark.parametrize('kind',['characters','words','irrelevant'])
def test_source_wording_never_clips_or_shows_an_unrelated_excerpt(kind):
    from src.retrieval.single_pass_summary import source_wording_fallback
    quote=('function '+('A'*1800) if kind=='characters' else
           'function '+('a '*810).strip() if kind=='words' else
           'In one study, the organ volume decreased in the disease group.')
    question='Explain organ function.' if kind!='irrelevant' else 'Does the organ produce insulin?'
    evidence=[dict(rank=1,record=dict(text=quote,citation=dict(title='Synthetic study')))]
    answer=dict(claims=[dict(text='An unsupported synthesis.',citations=[dict(rank=1,quote=quote)])])
    result=source_wording_fallback(question,evidence,answer)
    assert result['coverage']=='none' and result['claims']==[] and result['review']=='rejected'
    assert evidence[0]['record']['text']==quote


def test_source_wording_preserves_all_selected_quotes_and_titles():
    from src.retrieval.single_pass_summary import source_wording_fallback
    quotes=['The gland releases digestive enzymes.', 'The gland also releases hormones.']
    evidence=[dict(rank=n,record=dict(text=quote,citation=dict(title=f'Study {n}'))) for n,quote in enumerate(quotes,1)]
    citations=[dict(rank=n,quote=quote) for n,quote in enumerate(quotes,1)]
    answer=dict(claims=[dict(text='The gland releases enzymes and insulin.',citations=citations)])
    result=source_wording_fallback('What does the gland do?',evidence,answer)
    assert result['claims'][0]['citations']==citations
    assert result['claims'][0]['text']=='\n\n'.join(f'Source wording from “Study {n}”: {quote}' for n,quote in enumerate(quotes,1))


@pytest.mark.parametrize('failure',['unsafe','irrelevant'])
def test_model_review_never_turns_an_unsafe_or_irrelevant_draft_into_a_fallback(failure):
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        if payload['messages'][0]['content'] != REVIEW_PROMPT:return model_reply(A,payload)
        review=accepted_review(payload)
        if failure=='unsafe':review['safe']=False
        else:review['checks'][0]['relevant']=False
        review.update(coverage='none',status_appropriate=False,limitation='The draft does not provide an appropriate answer.')
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(review)))
    result=generate('What does it do?',E,call)
    assert result['coverage']=='none' and result['claims']==[] and result['review']=='rejected'


def test_failed_support_review_can_offer_exact_relevant_source_wording():
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        if payload['messages'][0]['content'] != REVIEW_PROMPT:return model_reply(A,payload)
        review=accepted_review(payload)
        review['checks'][0]['supported']=False
        review.update(coverage='none',status_appropriate=False,limitation='The complete draft is not supported by its citation.')
        return dict(done=True,done_reason='stop',model=MODEL,message=dict(content=json.dumps(review)))
    result=generate('What does it do?',E,call)
    assert result['review']=='source_fallback' and result['coverage']=='partial'
    assert result['claims'][0]['text']=='Source wording from “Synthetic source”: '+E[0]['record']['text']


def test_browser_prompt_identity_matches_running_summary_pipeline():
    from pathlib import Path
    from src.retrieval.single_pass_summary import FINGERPRINT
    config = json.loads((Path(__file__).resolve().parents[1] / "configs/evidence/single-summary-candidate-v1.json").read_text())
    assert config["prompt_sha256"] == FINGERPRINT



def grounded_repair_run(repaired, *, now=None, monkeypatch=None):
    from src.retrieval import single_pass_summary as summary
    if now is not None:
        monkeypatch.setattr(summary,'monotonic',lambda:now[0])
    quote='The gland releases digestive enzymes and hormones.'
    evidence=[dict(rank=1,record=dict(text=quote,citation=dict(title='Gland physiology'))),
        dict(rank=2,record=dict(text='The gland also releases insulin.',citation=dict(title='Unselected source')))]
    draft=dict(coverage='supported',limitation='',claims=[dict(
        text='The gland releases digestive enzymes, hormones and insulin.',sentence_ids=['P1S1'])])
    calls=[]
    def call(path,payload=None):
        if path=='tags':return dict(models=[dict(name=MODEL,digest=MODEL_SHA)])
        calls.append(payload)
        system=payload['messages'][0]['content']
        if system==REPAIR_PROMPT:
            body=json.loads(payload['messages'][1]['content'])
            assert body['question']=='What does the gland do?'
            assert body['failed_check']=='entity_not_quoted'
            assert [p['rank'] for p in body['passages']]==[1]
            assert body['selected_quotations']==[dict(rank=1,quote=quote)]
            assert 'P2S1' not in json.dumps(payload['format'])
            if now is not None:now[0]=50.0
            return model_reply(repaired,payload)
        if system==REVIEW_PROMPT:
            assert len(calls)==3
            if now is not None:now[0]=61.0
            return model_reply(repaired,payload)
        assert len(calls)==1
        if now is not None:now[0]=20.0
        return model_reply(draft,payload)
    return generate('What does the gland do?',evidence,call),calls,quote


def test_one_grounded_repair_produces_a_concise_reviewed_answer():
    repaired=dict(coverage='supported',limitation='',claims=[dict(
        text='The gland releases digestive enzymes and hormones.',sentence_ids=['P1S1'])])
    result,calls,quote=grounded_repair_run(repaired)
    assert len(calls)==3 and result['repair']=='accepted' and result['review']=='accepted'
    assert result['provenance']=='model_synthesized_passages'
    assert result['validation']=='citation_binding_and_model_review'
    assert result['claims'][0]['text']==repaired['claims'][0]['text']
    assert len(result['claims'][0]['text'].split())<=65
    assert result['claims'][0]['citations']==[dict(rank=1,quote=quote)]
    assert all(c['think'] is False and c['options']['num_predict']==512 for c in calls)


@pytest.mark.parametrize('failure',['new_number','second_guard','unselected_source','word_budget','empty'])
def test_bad_repair_falls_back_to_original_quotes_without_another_attempt(failure):
    text='The gland releases digestive enzymes and hormones.'
    ids=['P1S1']
    if failure=='new_number':text='The gland releases 99 digestive enzymes.'
    if failure=='second_guard':text='The gland releases enzymes and insulin.'
    if failure=='unselected_source':ids=['P2S1']
    if failure=='word_budget':text='The gland releases enzymes. '+('gland '*70)
    repaired=dict(coverage='supported',limitation='',claims=[dict(text=text,sentence_ids=ids)])
    if failure=='empty':repaired=dict(coverage='none',limitation='No checked correction is available.',claims=[])
    result,calls,quote=grounded_repair_run(repaired)
    assert len(calls)==2 and result['repair']=='fallback' and result['review']=='source_fallback'
    assert result['coverage']=='partial'
    assert result['claims'][0]['text']=='Source wording from “Gland physiology”: '+quote
    assert result['claims'][0]['citations']==[dict(rank=1,quote=quote)]


def test_draft_repair_and_review_share_one_total_deadline(monkeypatch):
    repaired=dict(coverage='supported',limitation='',claims=[dict(
        text='The gland releases digestive enzymes and hormones.',sentence_ids=['P1S1'])])
    with pytest.raises(TimeoutError,match='Summary deadline'):
        grounded_repair_run(repaired,now=[0.0],monkeypatch=monkeypatch)
