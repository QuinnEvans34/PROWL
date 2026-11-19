"""Request-local context for the pancreatic expert, with no server-side chat storage.

The frozen request and scope policies stay intact. Only this opt-in adapter supplies
the application's subject and previous literature questions to retrieval. Previous
questions are never evidence, and assistant answers are never carried forward.
"""
import re

from .development_search import search_scope
from .question_interpretation import interpret_question
from .question_routing import plan_request

POLICY = 'pancreatic-conversation-v1'
TOPIC = 'pancreatic research'
MAX_HISTORY = 3
_OTHER_SUBJECT = re.compile(
    r'\b(liver|hepatic|kidneys?|renal|lungs?|pulmonary|prostate|brain|breast|'
    r'heart|cardiac|thyroid|spleen|splenic|ovary|ovarian|uterus|uterine)\b', re.I)
_DOMAIN = re.compile(
    r'\b(pancrea\w*|pdac|mfcp|aip|ipmn|lesions?|tumou?rs?|cancers?|carcinomas?|'
    r'cysts?|ducts?|insulin|enzymes?|digest\w*|diabetes|inflamm\w*|atrophy|'
    r'diseases?|signs?|symptoms?|function|'
    r'ct|mri|mrcp|eus|ultrasound|radiomics|isoattenuat\w*|'
    r'segment\w*|contours?|outlines?|outlining|delineat\w*|annotations?|'
    r'volume|diameters?|dimensions?|size|enlarge\w*|head|tail|tags)\b', re.I)
_FOLLOWUP = re.compile(
    r'\b(it|its|they|them|their|that|those|these)\b|'
    r'\bthis\s+(study|paper|method|result|comparison|topic)\b|'
    r'^(and\b|also\b|what about\b|why\??$|how so\??$)|'
    r'\b(limitations?|caveats?|explain|simpler|elaborate|mean|measured)\b', re.I)
_CASE = re.compile(
    r'\b(my|our|your)\b|'
    r'\b(this|current|attached|loaded)\s+(?:\w+\s+){0,2}'
    r'(scan|image|patient|case|lesion|tumou?r|mass|pancreas|mask|outline)\b', re.I)
_DEFAULT_FUNCTION = re.compile(
    r'^(what does it do|how does it work|what is it|where is it(?: located)?|'
    r'does it (produce|release|secrete) (insulin|enzymes?|hormones?))\??$', re.I)
_DISEASE_SUBJECT = re.compile(
    r'\b(lesions?|tumou?rs?|cancers?|carcinomas?|pdac|mfcp|aip|ipmn|'
    r'pancreatitis|cysts?|masses?|stud(?:y|ies)|papers?|tags)\b', re.I)


def _organ_referent(history):
    """Resolve the organ only when a recent question actually identifies it."""
    for question in reversed(history):
        if _DISEASE_SUBJECT.search(question) or _OTHER_SUBJECT.search(question):
            return False
        if (interpret_question(question)['subject'] == 'pancreas'
                or _DEFAULT_FUNCTION.fullmatch(question.strip())):
            return True
    return False


def unpack_request(payload):
    """Accept the original closed request or a separately closed chat envelope."""
    conversation = []
    request = payload
    if isinstance(payload, dict) and 'request' in payload:
        if set(payload) != {'request', 'conversation'}:
            raise ValueError('Unknown expert conversation field')
        request, conversation = payload['request'], payload['conversation']
    plan_request(request)
    if not isinstance(conversation, list) or len(conversation) > MAX_HISTORY:
        raise ValueError('Invalid expert conversation length')
    for turn in conversation:
        if not isinstance(turn, dict) or set(turn) != {'question'}:
            raise ValueError('Conversation accepts questions only')
        prior = {**request, 'question': turn['question']}
        plan = plan_request(prior)
        if (plan['status'] == 'refused' or _CASE.search(turn['question'])
                or (_OTHER_SUBJECT.search(turn['question'])
                    and interpret_question(turn['question'])['subject'] != 'pancreas')):
            raise ValueError('Conversation must contain general pancreatic literature questions')
    return request, conversation


def resolve_question(request, conversation=()):
    """Return explicit retrieval context, or leave an unsafe/unclear question gated.

    Topic changes naming another organ are never relabelled as pancreatic. A bare
    plural referent and an unidentified study require clarification. Current-case
    questions retain their existing scope handling, even after a literature turn.
    """
    request, conversation = unpack_request(
        dict(request=request, conversation=list(conversation)))
    question = request['question']
    history = [turn['question'] for turn in conversation]
    plan = plan_request(request)
    context = dict(policy=POLICY, topic=TOPIC, resolved_question=question,
                   previous_questions=history)
    if plan['status'] == 'refused':
        return context, None
    if _CASE.search(question):
        return context, search_scope(request) or 'case_context_unavailable'
    intent = interpret_question(question)
    # A specifically named foreign organ may be a valid pancreatic comparison;
    # only reject implicit reassignment when the current question has no pancreas.
    if _OTHER_SUBJECT.search(question) and intent['subject'] != 'pancreas':
        return context, 'pancreas_topic_required'
    followup = bool(_FOLLOWUP.search(question))
    reference = re.search(r'\b(it|its|they|them|their|that|those|these|this)\b', question, re.I)
    if history and followup and (intent['subject'] == 'unspecified' or reference):
        if re.search(r'\bit\b', question, re.I) and _OTHER_SUBJECT.search(history[-1]):
            return context, 'clarification_subject'
        # A change of task about the same organ should search that task directly,
        # rather than repeatedly retrieve an earlier function/disease answer.
        direct = _organ_referent(history) and re.search(r'\bit\b', question, re.I)
        if direct:
            resolved = re.sub(r'\bit\b', 'the pancreas', question, flags=re.I)
        else:
            # Carry the latest bounded chain, so "Why?" after a prior follow-up
            # retains its antecedent. Never truncate a question's qualifications.
            anchor = 0
            for index, prior in enumerate(history):
                if (interpret_question(prior)['subject'] == 'pancreas'
                        and not re.search(r'\b(it|its|that|this|those|these)\b', prior, re.I)):
                    anchor = index
            prefix = 'Pancreatic literature context: ' + ' / '.join(history[anchor:]) + '. Follow-up: '
            resolved = prefix + question
        if len(resolved) > 500:
            return context, 'clarification_subject'
        # These are literature referents, not an attached patient or scan. Current
        # case references were screened above; retain all other current wording.
        resolved = re.sub(r'\bthis\b', 'that', resolved, flags=re.I)
        context['resolved_question'] = resolved
    elif intent['subject'] != 'pancreas':
        if _DEFAULT_FUNCTION.fullmatch(question.strip()):
            context['resolved_question'] = re.sub(r'\bit\b', 'the pancreas', question, flags=re.I)
        elif re.search(r'\b(it|its|they|them|their|that|those|these|this)\b', question, re.I):
            return context, 'clarification_subject'
        elif _DOMAIN.search(question):
            resolved = 'In pancreatic research: ' + question
            if len(resolved) > 500:
                return context, 'clarification_subject'
            context['resolved_question'] = resolved
        else:
            return context, 'clarification_subject'
    # Apply every existing input, privacy and clinical gate to the contextual query
    # as well. Context cannot turn a refused request into an executable one.
    effective = {**request, 'question': context['resolved_question']}
    if search_scope(effective) in ('out_of_scope', 'case_context_unavailable'):
        context['resolved_question'] = question
    return context, None


class ExpertConversation:
    """Opt-in facade shared by source-only and live-summary HTTP services."""
    supports_conversation = True

    def __init__(self, sources, answers=None):
        self.sources, self.answers = sources, answers
        self.config = sources.config
        self.policy = answers.policy if answers is not None else 'sources-only'

    def _sources(self, request, context, reason):
        effective = {**request, 'question': context['resolved_question']}
        result = (self.sources.not_searched(request, reason) if reason
                  else self.sources.search(effective))
        result.update(question=request['question'], context=context)
        return result

    def search(self, request, *, conversation=()):
        context, reason = resolve_question(request, conversation)
        return self._sources(request, context, reason)

    def answer(self, request, *, conversation=()):
        context, reason = resolve_question(request, conversation)
        if reason or self.answers is None:
            return self._sources(request, context, reason)
        return self.answers.answer(request, question_context=context)
