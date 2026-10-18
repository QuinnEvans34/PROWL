# R3 — terminology and source context

R2 completed all20 cases:9/20 have a labeled direct top5 passage, same count as dense;
mean source recall@5=.93, MRR=.8433, passage recall@5=.2294. Median5.375s/max5.763s.
It fails coverage/disease criteria and is not promoted. It does retrieve some useful comparative
text outside the existing labeled spans, but this is not grounds to rewrite labels or call it passed.

R3 is one deliberately specified pipeline, with two changed inputs to the same cross-encoder:
(1) a concise scientific search reformulation from the already installed Qwen3:8b, and
(2) the canonical paper title prefixed to each unchanged passage. This addresses lay/technical
terminology and paragraphs that lose their named-study context. Effects cannot be attributed to
one of these factors separately. No source/question-specific rules or gold/reference inputs.

Rewrite every question once: pinned model digest500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41,
think=false, temperature0, seed42, num_ctx4096, num_predict512, deadline20seconds. Return a single
query≤500characters and retain the original question for final answering and audit. Reformulations
are search aids only, never evidence. The prompt preserves modality, named study, anatomy, comparisons
and uncertainty; forbids numeric answers or unsupported patient conclusions. Retain all rewrites for
engineering semantic review. Scope checking must precede any future live rewrite call.

Run all20 exposed answerable questions, unchanged labels/corpus/model batch/limits and top50/top5.
Maximum20rewritecalls, no answer generation, retries or sweeps.15minute run cap. Compare R2 and
original dense; retain all regressions. Same quality promotion criteria as R2, plus no material
rewrite intent drift. Retrieval latency target here explicitly includes the extra query-model call:
median≤15seconds, max≤30seconds. This prospective adjustment reflects the newly added stage;
R2 latency and failure remain unchanged. Pin exact prompt/settings/producing files before execution.

If incomplete/failed, preserve evidence and do not silently fall back to a different configuration.
Only after qualification consider versioned live integration and the unchanged answer-policy batch.
