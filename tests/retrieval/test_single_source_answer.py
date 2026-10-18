from copy import deepcopy
from src.retrieval.single_source_answer import focus_evidence


def test_focus_preserves_original_ranks_and_excludes_other_papers():
    hits=[dict(rank=rank,record=dict(passage=dict(work_id=work))) for rank,work in [(1,'a'),(2,'b'),(3,'a'),(9,'a')]]
    original=deepcopy(hits)
    work,selected=focus_evidence(hits)
    assert work=='a' and [e['rank'] for e in selected]==[1,3,9]
    assert hits==original
