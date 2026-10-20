"""Bounded lexical search over reviewed source relations; no prepared-question lookup.

The explicit topic grammar is a development convenience, not general semantic understanding.
Record retrieval is separate from the legacy dense/model-answer path.
"""
from collections import Counter
from copy import deepcopy
import math
import re
import unicodedata

from .disease_fact_records import DiseaseFactCatalog
from .direct_ingestion import digest

POLICY = 'source-linked-record-search-v1'


def route_question(question):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        raise ValueError('Invalid question')
    q = unicodedata.normalize('NFKC', question).casefold().replace('’', "'")
    def has(pattern): return re.search(pattern, q) is not None
    def no(reason): return dict(status='unmatched', reason=reason, intents=[])
    if has(r"\b(this|my|our|patient|case|diagnos\w*|treat\w*|biopsy|prognos\w*|survival|risk|probability|odds|chance)\b|\d"):
        return no('individual_or_quantitative_request')
    if has(r"\b(no|not|never|without|except|exclude|instead|ignore|prompt|database|secrets?)\b|\b(don't|doesn't|isn't|can't)\b"):
        return no('negated_or_instruction_request')
    if has(r'\b(liver|kidney|renal|spleen|lung|neuroendocrine|pnet|ipmn|cysts?|cystic|metasta\w*|diabetes|metformin|acute)\b'):
        return no('unrepresented_comparison')
    if not has(r'\b(pancrea\w*|pdac|mfcp)\b'):
        return no('pancreatic_topic_required')
    if has(r'\b(volume|average|normal|reference|percentile|threshold|cutoff|cut-off|measure\w*|how (large|big|long|wide))\b'):
        return no('measurement_or_reference_request')
    aip = has(r'\b(autoimmune|aip)\b')
    chronic = has(r'\b(chronic|mfcp)\b')
    inflammatory = has(r'\b(inflamm\w*|pancreatitis|swelling|swollen)\b')
    cancer = has(r'\b(cancer|tumou?r\w*|pdac|adenocarcinoma|malignan\w*)\b')
    comparison = has(r'\b(distinguish\w*|differentiat\w*|differen\w*|compar\w*|versus|vs|tell\b.{0,45}\bapart)\b')
    findings = has(r'\b(imag\w*|findings?|features?|signs?|appear\w*|enhanc\w*|duct\w*|calcific\w*|mrcp|ct|mri)\b')
    head = has(r'\bhead\b') and has(r'\b(size|enlarg\w*|swelling|swollen|mass\w*)\b')
    disease = has(r'\b(diseases?|conditions?|indicat\w*|caus\w*|associat\w*)\b')
    if head and (disease or comparison or inflammatory and cancer):
        # The curated head record is about MFCP; do not redirect explicit AIP to that record.
        if aip: return no('unrepresented_head_comparison')
        pairs = [['MFCP','PDAC']]; topic = 'focal_head_mass'
    elif (comparison and (inflammatory or cancer or aip or chronic)) or (findings and (aip or chronic or inflammatory and cancer)):
        pairs = ([['focal_AIP','PDAC']] if aip and not chronic else [['MFCP','PDAC']] if chronic and not aip
                 else [['MFCP','PDAC'],['focal_AIP','PDAC']])
        topic = 'imaging_differentiation'
    else: return no('topic_not_resolved')
    return dict(status='candidate', reason='literature_examples_not_exhaustive', intents=[
        dict(organ='pancreas', comparison=pair, topic=topic, use='literature_comparison') for pair in pairs])


STOP = set('a an the is are be in of on for to from and or with what which how can could would does do it its this that help additional specific between than as usually'.split())
SYNONYMS = {'inflammation':'pancreatitis','inflammatory':'pancreatitis','cancer':'pdac',
            'tumor':'pdac','tumour':'pdac','adenocarcinoma':'pdac','enlargement':'enlarge',
            'enlarged':'enlarge','swelling':'enlarge','swollen':'enlarge','size':'enlarge',
            'autoimmune':'aip','imaging':'image','images':'image','findings':'feature','features':'feature'}


def terms(text):
    words=re.findall(r'[a-z]+',unicodedata.normalize('NFKC',text).casefold())
    return [SYNONYMS.get(w,w) for w in words if w not in STOP]


class RecordSearchIndex:
    def __init__(self, catalog, review, canonical):
        self.engine=DiseaseFactCatalog(catalog,review,canonical)
        self.records=deepcopy(catalog['records'])
        self.canonical={s['passage_id']:deepcopy(s['record']) for s in canonical.values()}
        # Search documents derive only from source relations and their canonical anchor passages.
        self.documents={r['id']:Counter(terms(' '.join(
            [f['subject']+' '+f['object']+' '+(f['method'] or '')+' '+(f['phase'] or '') for f in r['facts']]
            +[self.canonical[p]['text'] for p in r['retrieval_anchors']]))) for r in self.records}
        self.df=Counter(t for doc in self.documents.values() for t in doc)

    def search(self, question):
        route=route_question(question); ranked=[];query=set(terms(question))
        for r in self.records:
            intent=next((i for i in route['intents'] if all(i[k]==r[k] for k in ('organ','comparison','topic'))),None)
            if intent is None: continue
            doc=self.documents[r['id']]
            score=sum(math.log(1+len(self.documents)/(1+self.df[t]))*(1+math.log(doc[t]))
                      for t in query.intersection(doc))
            if score <= 0: continue
            # Anchors come from searching the reviewed record, not from injected evaluation IDs.
            anchors=[self.canonical[p] for p in r['retrieval_anchors']]
            if r['id'] not in self.engine.select(anchors,intent)['record_ids']:
                raise ValueError('Selected record failed source admission')
            answer=self.engine.render(r['id']);self.engine.verify_answer(answer,record_id=r['id'])
            ranked.append(dict(record_id=r['id'],comparison=r['comparison'],topic=r['topic'],score=score,
                anchor_passage_ids=r['retrieval_anchors'],
                evidence_passage_ids=[c['passage_id'] for c in answer['citations']]))
        ranked.sort(key=lambda r:(-r['score'],r['record_id']))
        hits=[];seen=set()
        for r in ranked:
            for pid in r['anchor_passage_ids']+r['evidence_passage_ids']:
                if pid not in seen:
                    hits.append(dict(record=deepcopy(self.canonical[pid]),score=r['score']));seen.add(pid)
        if len(hits)>20: raise ValueError('Record evidence budget exceeded')
        return dict(route=route,matches=ranked,hits=hits)


class RecordAwareSearch:
    """Source-only service: exact reviewed-record retrieval, otherwise unchanged dense fallback."""
    policy = POLICY

    def __init__(self, baseline, index, config):
        if (config['retriever'] != self.policy or config['top_k'] != 20 or config['generation'] is not False
                or config['manifest'] != baseline.config['manifest']
                or config['corpus_content_sha256'] != baseline.config['corpus_content_sha256']):
            raise ValueError('Record search configuration mismatch')
        self.baseline=baseline;self.index=index;self.config=deepcopy(config)

    def search(self, request):
        # Retains input/privacy/scope gates, DB identity and storage checks on every request.
        base=self.baseline.search(request)
        result=dict(base,configuration_sha256=digest(self.config),retrieval_policy=self.policy)
        selection=dict(policy=self.policy,status='not_searched',reason=base['reason'],matches=[])
        if base['state']!='not_searched':
            found=self.index.search(request['question'])
            selection.update(status='matched' if found['matches'] else 'dense_fallback',
                             reason=found['route']['reason'],matches=found['matches'])
            if found['hits']:
                ticket=dict(target=self.baseline.corpus.target,limit=20,request_id=request['request_id'],
                            request_sha256=digest(request),configuration_sha256=digest(self.config))
                ticket['content_sha256']=digest(ticket)
                snapshot=dict(version='prowl-literature-snapshot-v1',ticket_sha256=ticket['content_sha256'],
                    state='complete',failure_code=None,hits=[dict(passage_id=h['record']['passage']['passage_id'],
                    record_sha256=digest(h['record']),score=h['score']) for h in found['hits']])
                bound=self.baseline.corpus.bind_snapshot(ticket,snapshot)
                result.update(state=bound['state'],evidence=bound['evidence'])
        result['record_selection']=deepcopy(selection)
        return result
