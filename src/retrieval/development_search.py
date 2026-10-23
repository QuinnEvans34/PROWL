"""Ephemeral local library search, deliberately separate from clinical question answering."""
import re
import unicodedata
from threading import Lock

from .direct_ingestion import digest
from .question_routing import plan_request
from .question_interpretation import interpret_question


def search_scope(request):
    plan = plan_request(request)  # Closed input, UUID/text checks, known refusals.
    text = unicodedata.normalize('NFKC', plan['question_normalized']).casefold()
    if plan['status'] == 'refused':
        return 'out_of_scope'
    if re.search(r'\b(this|my|our)\b|\b(the|a) patient\b', text):
        return 'case_context_unavailable'
    intent = interpret_question(text)
    if intent['negated']:
        return 'clarification_negation'
    if intent['subject'] == 'unspecified' and re.fullmatch(r'how (big|large|long|wide) is it\??', text):
        return 'clarification_subject'
    # The volume router supplies the more specific study/population clarification.
    if (intent['subject'] == 'pancreas' and re.search(r'\b(size|big|large)\b', text)
            and re.search(r'\b(average|mean)\b', text)
            and not re.search(r'\b(volume|diameter|head|body|tail|tumou?r|lesion|length|width)\b', text)):
        return 'clarification_size'
    # General anatomical location is literature, not localization in an attached image.
    if (plan['required_capabilities'] == ['validated_location'] and intent['subject'] == 'pancreas'
            and intent['context'] == 'literature'
            and not re.search(r'\b(scan|image|case|patient)\b', text)):
        return None
    if plan['route'] == 'measurement':
        return 'measurement_unavailable'
    if intent['subject'] != 'pancreas':
        return 'pancreas_topic_required'
    return None


class DevelopmentSearch:
    """One bounded exact-search call; no answer catalog, labels, prompt or persistence.

    Keyword checks are a conservative convenience, not semantic privacy certification.
    Only public-literature questions belong in this opt-in local research interface.
    """
    def __init__(self, corpus, config, retrieve, *, scope_policy=search_scope):
        bounded_mode = ((config['top_k']==5 and config['query_expansion'] is False)
            or (config['top_k']==50 and config.get('retriever')=='section-cross-encoder-terminology-v1'
                and config['query_expansion'] is True))
        if (config['corpus_content_sha256'] != corpus.target['inventory']['content_sha256']
                or config['encoder_id'] != corpus.target['inventory']['encoder_id']
                or config['manifest']['sha256'] != corpus.target['manifest_sha256']
                or not bounded_mode or config['generation'] is not False):
            raise ValueError('Development search configuration mismatch')
        self.corpus, self.config, self.retrieve = corpus, dict(config), retrieve
        self.scope_policy = scope_policy
        self.lock = Lock()

    def search(self, request):
        reason = self.scope_policy(request)
        base = dict(schema_version='prowl-development-search-response-v1',
            request_id=request['request_id'], question=request['question'],
            collection=self.config['collection'], target=self.corpus.target,
            configuration_sha256=digest(self.config), generation='not_called', answer=None)
        if reason:
            return dict(base, state='not_searched', reason=reason, evidence=[])
        if not self.lock.acquire(blocking=False):
            raise OSError('Search busy')
        try:
            ticket = dict(version='prowl-development-search-ticket-v1',
                request_id=request['request_id'], request_sha256=digest(request),
                question=request['question'], target=self.corpus.target,
                configuration_sha256=digest(self.config), limit=self.config['top_k'])
            ticket['content_sha256'] = digest(ticket)
            hits = self.retrieve(request['question'])
            if not isinstance(hits, list) or len(hits) > self.config['top_k']:
                raise ValueError('Invalid search result count')
            snapshot = dict(version='prowl-literature-snapshot-v1',
                ticket_sha256=ticket['content_sha256'], state='complete', failure_code=None,
                hits=[dict(passage_id=h['record']['passage']['passage_id'],
                    record_sha256=digest(h['record']), score=h['score']) for h in hits])
            evidence = self.corpus.bind_snapshot(ticket, snapshot)
            return dict(base, state=evidence['state'], reason=None, evidence=evidence['evidence'])
        finally:
            self.lock.release()
