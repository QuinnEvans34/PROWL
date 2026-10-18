"""Fixed exposed-development candidates; not the live or protected-evaluation retriever.

Only question text, collection and encoder reach SQL. No labels or expected answers.
The caller owns the read-only transaction and canonical corpus inventory check.
"""
import math

from .direct_ingestion import vector_sql

DEPTH = 50
RRF_CONSTANT = 60


def fuse(dense, lexical):
    """Equal reciprocal-rank contributions; input order is rank, not raw score scale."""
    scores = {}
    for ranking in (dense, lexical):
        if len(ranking) > DEPTH:
            raise ValueError('Candidate depth exceeded')
        seen = set()
        for rank, item in enumerate(ranking, 1):
            pid = item['passage_id']
            if not isinstance(pid, str) or not pid or pid in seen or not math.isfinite(item['score']):
                raise ValueError('Invalid candidate ranking')
            seen.add(pid)
            scores[pid] = scores.get(pid, 0.0) + 1 / (RRF_CONSTANT + rank)
    return [dict(passage_id=pid, score=score) for pid, score in
            sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))[:DEPTH]]


def rank_candidates(db, collection, encoder, question):
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise ValueError('Invalid search question')
    if db.execute('SELECT encoder_id FROM literature.collections WHERE id=%s',
                  (collection,)).fetchone() != (encoder.id,):
        raise ValueError('Missing collection or incompatible encoder')
    q = vector_sql(encoder.encode([question])[0])
    dense_rows = db.execute(
        'SELECT passage_id, 1-(embedding <=> %s::vector) FROM literature.passages '
        'WHERE collection_id=%s ORDER BY embedding <=> %s::vector, passage_id LIMIT %s',
        (q, collection, q, DEPTH)).fetchall()
    # PostgreSQL quotes/stems user lexemes before operators are changed. User input never
    # becomes SQL syntax; punctuation/operators in the question are plain text to the parser.
    lexical_rows = db.execute("""
        WITH query AS (
          SELECT to_tsquery('english', replace(plainto_tsquery('english', %s)::text,
                                               ' & ', ' | ')) AS q
        ), scored AS (
          SELECT passage_id, to_tsvector('english', text) AS terms
          FROM literature.passages WHERE collection_id=%s
        )
        SELECT passage_id, ts_rank_cd(terms, q) AS score FROM scored CROSS JOIN query
        WHERE terms @@ q ORDER BY score DESC, passage_id LIMIT %s
        """, (question, collection, DEPTH)).fetchall()
    dense = [dict(passage_id=pid, score=float(score)) for pid, score in dense_rows]
    lexical = [dict(passage_id=pid, score=float(score)) for pid, score in lexical_rows]
    return dict(dense=dense, lexical=lexical, hybrid=fuse(dense, lexical))
