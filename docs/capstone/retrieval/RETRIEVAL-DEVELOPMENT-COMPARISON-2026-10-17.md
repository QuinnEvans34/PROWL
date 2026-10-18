# Bounded development retrieval comparison — October 17, 2026

## Plan recorded before execution

Quinton's “Great, continue on” follows the recommendation to recover relevant disease evidence
before more prompt work. This authorizes a bounded local development comparison ahead of the
formal Step 6 freeze. It does not accept the proposed v6 labels, satisfy Step 5, authorize protected
content access, or establish final retrieval selection. Existing evaluation gates remain unchanged.

Baseline: commit `30f3e740864bc04937c34c0f0a390687ddb07e96`, live dense exact top5,
14-source/1,179-passage disease-v1 corpus, existing MiniLM encoder, answer policy v6.1.
Hypothesis: lexical matching may recover disease-specific evidence that semantic similarity misses;
equal-weight reciprocal-rank fusion may preserve broader semantic coverage. No query rewriting,
new sources, model generation, expected-answer injection, source boosts or question-specific rules.

One run, all 20 answerable exposed v6 draft questions. Compare:

1. Exact cosine dense ranking, depth50 (its first5 must match the existing search implementation).
2. PostgreSQL English full-text OR of the question's normalized lexemes, `ts_rank_cd`, positive
   matches only, depth50. Parse through `plainto_tsquery` before joining terms; bind SQL parameters.
3. Equal-weight RRF of those two depth50 lists, constant60, output50.

All ties use passage ID ascending. No candidate/parameter sweep or automatic retry. Keyword
ranking can underfill; report actual depths. PostgreSQL computes text vectors at query time;
no schema, index or corpus mutations. One read-only repeatable-read transaction, existing resource
floors and 30-second SQL timeout. Up to20 query embeddings plus one baseline parity embedding.
Retain producing file hashes, all rankings, timing and failures under a new ignored output directory.

Score only after rankings exist; labels never enter a retrieval function. Use existing recall/MRR
arithmetic: source recall@1/3/5/10 and MRR after first-occurrence source deduplication over depth50;
passage recall@1/3/5/10 and MRR against passages fully containing direct spans. These are provisional
development measurements, not the formally admitted ranking contract or independent evaluation.
Also report actual top5 passage direct-hit counts and source coverage. Span-hit coverage is diagnostic
only, not a selection metric. The10 refusal/gap questions stay out of answerable means; no generation
or safety acceptance is inferred from retrieval metrics.

For even a local preview change, require higher mean source recall@5 than dense, nondecreasing
source MRR and mean passage recall@5, and more direct-hit passages within top5 for each of the two
disease questions. Primary ordering: source recall@5, then MRR, then dense/lexical/hybrid order.
This is deliberately conservative. If neither candidate qualifies, keep live dense unchanged and
report the failure/rank diagnosis. Do not change the criterion or add another candidate in this run.
Any qualifying result still needs canonical evidence binding/tests and a separate live integration
check; this comparison cannot close the answer-quality gate.

Full v6 draft and corpus identities, source/text/embedding verification and exact source offsets are
checked before scoring. Existing private-authoring and freeze validators remain unchanged.

## Recovery decision before attempt 2

Attempt1 failed during its first lexical SQL query after one query embedding and dense query;
zero complete candidate rankings or scores. Receipt and producing snapshots retained in
`outputs/prowl/retrieval-comparison-v1-20261017/`. PostgreSQL logged backend exit2 and automatically
recovered; container OOMKilled=false does not rule out all memory/host failures. Cause remains
unproven. No container restart, data deletion, migration or query-policy changes.

A synthetic parser/ranker canary, actual 1,179-row count (maximum passage600characters), full
canonical DB inventory and corpus-wide FTS match-count check all passed after recovery. Based on
these fresh checks, explicitly run one new attempt in `retrieval-comparison-v1-attempt2-20261017`
with unchanged ranking code, parameters, cases and selection criteria. This is a recorded recovery
attempt, not an automatic retry. Stop if another database failure occurs. Budget adds20embeddings
plus one parity embedding; first attempt consumed one. Runtime cause remains an operational risk.
