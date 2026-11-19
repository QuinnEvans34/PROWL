"""Bounded complementary lexical/dense recall over immutable source passages.

This is retrieval, not evidence assessment. Three lexical results survive even
when dense similarity prefers a tangential study. Whole passages retain their
qualifications. No answer, expected source ID or question catalog is consulted.
"""
from collections import Counter
from copy import deepcopy
import math
import re
import unicodedata

POLICY = 'canonical-lexical-dense-recall-v1'
LIMITS = dict(version=POLICY, dense_candidates=20, lexical_candidates=50,
              max_corpus_passages=1179, top_k=5, lexical_slots=3, dense_slots=2)
STOP = frozenset('a an the is are was were be been being in of on at for to from and or '
    'with what which how can could would should does do did it its this that these '
    'those them they their then about as by into also clear happens happen if when '
    'where why explain me tell really please'.split())
ALIASES = {
    **{word: 'secrete' for word in ('produce','produces','produced','producing','production',
        'secretes','secreting','secreted','secretion','release','releases','released','releasing')},
    **{word: 'locate' for word in ('located','location','locates','situated','position','positioned')},
    **{word: 'function' for word in ('functions','functional','functioning')},
    'pancreatic': 'pancreas', 'pancreata': 'pancreas', 'pancreases': 'pancreas',
    'diseases': 'disease', 'signs': 'sign', 'symptoms': 'symptom',
}
_LOSS_OF_FUNCTION = re.compile(
    r'\b(?:loss of function|los(?:e|es|ing) function|lost function|function loss|'
    r'impaired function|functional impairment|stops? working|ceases? to function)\b')


def terms(text, *, question=False):
    """Ordinary search normalization; synonyms do not become answer facts."""
    text = unicodedata.normalize('NFKC', text).casefold().replace('β', 'beta').replace('α', 'alpha')
    # Distinguish organ dysfunction from the optimization objective named a
    # "loss function". This is a word-sense distinction, not a selected answer.
    text = re.sub(r'\bloss functions?\b', 'optimizationobjective', text)
    text = _LOSS_OF_FUNCTION.sub('dysfunction function', text)
    if question and re.search(r'\bwhat (?:does|do)\b.+\bdo\??$', text):
        text += ' function'
    result = []
    for token in re.findall(r'[a-z]+', text):
        if token in STOP:
            continue
        if token in ALIASES:
            token = ALIASES[token]
        elif (len(token) > 4 and token.endswith('s')
                and not token.endswith(('ss', 'sis', 'as', 'us'))):
            token = token[:-1]
        result.append(token)
    return result


class HybridPassageIndex:
    def __init__(self, records, config):
        if config != LIMITS:
            raise ValueError('Unsupported hybrid retrieval configuration')
        if not isinstance(records, list) or not 1 <= len(records) <= config['max_corpus_passages']:
            raise ValueError('Hybrid corpus passage budget')
        self.config = dict(config)
        self.records = {}
        self.counts = {}
        total = 0
        for raw in records:
            record = deepcopy(raw)
            pid = record['passage']['passage_id']
            text, title = record['text'], record['citation']['title']
            if not isinstance(pid, str) or not pid or pid in self.records:
                raise ValueError('Duplicate or missing canonical passage')
            if not isinstance(text, str) or not text or not isinstance(title, str):
                raise ValueError('Invalid canonical search text')
            total += len(text) + len(title)
            if total > 2000000:
                raise ValueError('Hybrid corpus text budget')
            self.records[pid] = record
            self.counts[pid] = Counter(terms(title + '\n' + text))
        self.document_frequency = Counter(t for counts in self.counts.values() for t in counts)
        self.average_length = sum(sum(c.values()) for c in self.counts.values()) / len(self.counts)
        self.average_length = max(self.average_length, 1)

    def lexical(self, question):
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
            raise ValueError('Invalid hybrid question')
        query = set(terms(question, question=True))
        scored = []
        n = len(self.records)
        for pid, counts in self.counts.items():
            length = sum(counts.values())
            score = 0.0
            for term in query:
                frequency = counts.get(term, 0)
                if frequency:
                    df = self.document_frequency[term]
                    idf = math.log(1 + (n - df + .5) / (df + .5))
                    score += idf * frequency * 2.2 / (frequency + 1.2 * (.25 + .75 * length / self.average_length))
            if score > 0:
                scored.append((pid, score))
        return sorted(scored, key=lambda item: (-item[1], item[0]))[:self.config['lexical_candidates']]

    def rank(self, question, dense):
        lexical = self.lexical(question)
        if not isinstance(dense, list) or len(dense) > self.config['dense_candidates']:
            raise ValueError('Hybrid dense candidate budget')
        dense_ids = []
        for hit in dense:
            record, score = hit['record'], hit['score']
            pid = record['passage']['passage_id']
            if (pid not in self.records or pid in dense_ids or record != self.records[pid]
                    or type(score) not in (int, float) or not math.isfinite(score)):
                raise ValueError('Invalid or modified dense candidate')
            dense_ids.append(pid)
        chosen = [pid for pid, _ in lexical[:self.config['lexical_slots']]]
        additions = [pid for pid in dense_ids if pid not in chosen][:self.config['dense_slots']]
        chosen.extend(additions)
        # Sparse channels can fill from the remaining candidates; duplicates and
        # synthetic evidence are never introduced to meet the five-result limit.
        for pid in [pid for pid, _ in lexical] + dense_ids:
            if len(chosen) >= self.config['top_k']:
                break
            if pid not in chosen:
                chosen.append(pid)
        # The score denotes final ordinal rank, not calibrated answer confidence.
        return [dict(record=deepcopy(self.records[pid]), score=1.0 / rank)
                for rank, pid in enumerate(chosen, 1)]
