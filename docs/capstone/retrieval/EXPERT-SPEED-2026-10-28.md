# AI expert latency investigation — October 28

The main demonstrated delay is answer-model generation, not vector search. No
production configuration or answer-quality gate was changed. Teacher generation
continued throughout these CPU-only checks.

## Evidence and limits

| Check | Result | Interpretation |
| --- | --- | --- |
| Historical general-answer receipt | 52.141 s total; 0.365 s retrieval; 48.055 s model generation across two calls | Most of this answer's time was spent generating model tokens. This is one saved example, not a new benchmark. |
| Historical exact-repeat cache receipt | 0.452 s total, cache hit | Existing caching helps repeated questions; it does not accelerate new questions. |
| Verified internal database, eight public questions repeated twice | 0.392 s median retrieval; 0.009 s SQL; 0.285 s full inventory verification | Database execution is already milliseconds. |
| Internal database size | 14,341,811 bytes, 14 papers / 1,179 passages | The active literature database is small enough to keep internal. The encoder is already internal. |
| HNSW diagnostic, eight public questions | Forced HNSW plan used in all eight; 0.001 s median; exact top-five recall 1.0 on these questions | Millisecond-scale opportunity, not a solution to a minute-long answer. Small exposed sample, not general recall evidence. |

PostgreSQL naturally preferred an exact alternative on this small collection, even
after ANALYZE and index creation. The final HNSW probe disabled sequential scans,
bitmap scans and sorts only in its isolated session to verify actual index use.
These differently warmed query samples are not a controlled end-to-end speedup.
Temporary indexes were dropped. Preserve exact search in production for now.

The external literature container was stopped. Starting it failed because Docker
could not resolve the external bind mount, although macOS could access the files.
Docker was not restarted because an unrelated container was running. Instead, a
separate database on internal storage was populated from verified frozen batches;
its inventory matched the corpus. It used loopback port 55434, not production
55433. No raw PostgreSQL data directory was copied and no live service was switched.
There is therefore **no controlled external-versus-internal speed comparison**.
Internal storage is a promising availability improvement, not a demonstrated
explanation for the long answer delay. The production database outage remains open.

Local receipts: `outputs/prowl/expert-speed-20261028/{retrieval-benchmark,index-probe,index-forced-probe}.json`.
Historical receipts: `outputs/prowl/general-spans-20261023/cache-probe-{0,1}.json`.

## Next bounded comparison

`scripts/retrieval/compare_expert_reasoning_v1.py` prepares five existing public
packets: function, paraphrase, methods, focal fat and evidence gap. Compare the same
model, evidence and prompts with thinking enabled for both selection and audit
against thinking disabled only for selection, retaining the thinking audit.
Counterbalance arm order; allow two calls and 90 seconds per answer, with a
1,000-second total admission limit. Save raw outputs, failures and exact citation
checks in a fresh output directory. Manual review must assess relevance,
completeness, qualifications and refusal behavior; exact quote matching alone is
insufficient. This exposed set cannot establish independent acceptance.

Earlier nonthinking experiments selected irrelevant disease evidence, so removing
both reasoning calls is not an acceptable untested shortcut. Existing warm-cache
and model keep-alive behavior should remain. Historical model loading accounted
for about 1.8 seconds of the 52-second answer, limiting that opportunity too.

Run the comparison only after an authorized teacher pause and verified GPU release.
The runner uses the existing exclusive GPU lock and AC check. It has not been run
and cannot promote itself. Two synthetic configuration tests pass. After review,
test the better qualifying arm through both Research and Workbench, including
cancellation and new-question handling, before any promotion.

## Recommended order

1. Qualify internal database service integration and restart/recovery behavior;
   keep bulk scans, teacher outputs and literature archives external.
2. At the next teacher pause, run the bounded model comparison and manually review
   every answer and citation against the unchanged baseline.
3. Promote only a faster candidate that retains support and completeness. If it
   fails, preserve the result and identify the specific slow stage before another
   experiment. Do not add indexing complexity for a millisecond-scale benefit.

The isolated database is stopped after measurement; its files and receipts remain
available for the integration step. The teacher reached 706/1,333 completed cases
during this work, with its existing supervisor and worker still alive.
