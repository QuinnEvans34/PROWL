"""Versioned, explicit query facets for the fixed reviewer question catalog."""
import json
from pathlib import Path
from .direct_ingestion import search, digest

POLICY = 'guided-facets-v1'
CATALOG = json.loads((Path(__file__).resolve().parents[2] / 'configs/evidence/research-questions-v1.json').read_text())


def plan(question):
    entry = next((q for q in CATALOG if q['label'] == question), None)
    return list(dict.fromkeys((entry or {}).get('retrieval_queries', []) + [question]))


def merge(rankings, k=5):
    """Reserve one top result per facet, then reciprocal-rank fusion; IDs never invented."""
    scores, rows, origins = {}, {}, {}
    for query, hits in rankings:
        for rank, hit in enumerate(hits, 1):
            pid = hit['record']['passage']['passage_id']
            scores[pid] = scores.get(pid, 0) + 1 / (60 + rank)
            rows.setdefault(pid, hit)
            origins.setdefault(pid, []).append(dict(query=query, rank=rank, cosine_score=hit['score']))
    selected = []
    # Exact duplicates and strongly overlapping snippets should not consume the context twice.
    def add(pid):
        text = rows[pid]['record']['text']
        words = set(text.lower().split())
        if pid in selected:
            return
        for old in selected:
            other = set(rows[old]['record']['text'].lower().split())
            if len(words & other) / max(1, len(words | other)) > .8:
                return
        selected.append(pid)
    for _, hits in rankings:
        if hits and len(selected) < k:
            add(hits[0]['record']['passage']['passage_id'])
    for pid in sorted(rows, key=lambda p: (-scores[p], p)):
        if len(selected) >= k:
            break
        add(pid)
    return [dict(rows[pid], retrieval=dict(policy=POLICY, fusion_score=scores[pid], matches=origins[pid])) for pid in selected]


def guided_search(db, collection, encoder, question, k=5):
    queries = plan(question)
    if not 1 <= k <= 20:
        raise ValueError('Invalid result limit')
    results = merge([(q, search(db, collection, encoder, q, k)) for q in queries], k)
    for hit in results:
        hit['retrieval']['plan_sha256'] = digest(dict(policy=POLICY, queries=queries))
    return results
