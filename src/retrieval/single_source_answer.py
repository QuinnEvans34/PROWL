"""An explicit paper-scoped candidate; retrieval and original rank identities stay intact."""
from .isolated_answer import generate_isolated,fingerprint as base_fingerprint
from .direct_ingestion import digest
POLICY='natural-literature-answer-v17'


def fingerprint():
    return digest([base_fingerprint(),'top-ranked-paper-canonical-context-v1'])


def focus_evidence(evidence):
    if not evidence:raise ValueError('No evidence')
    work=evidence[0]['record']['passage']['work_id']
    return work,[e for e in evidence if e['record']['passage']['work_id']==work]


def generate_focused(question,evidence,call=None,*,deadline=None):
    work,selected=focus_evidence(evidence)
    answer=generate_isolated(question,selected,call,deadline=deadline)
    return dict(answer,policy=POLICY,prompt_sha256=fingerprint(),source_scope='top_ranked_paper',source_work_id=work)
