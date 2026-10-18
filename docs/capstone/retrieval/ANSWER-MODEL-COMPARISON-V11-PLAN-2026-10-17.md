# V11 — compare the already installed 8B model on the fixed v9 task

The 30B model repeatedly loses explicit qualifications and reproduces jargon despite usable
retrieved evidence. V10 additionally shows that a writer receiving original passages escapes the
selected-fact boundary, and native reasoning in review can exhaust the 60-second deadline. Its
full attempt is retained; no concurrent model experiment or live promotion follows.

Before adding more prompts, test one controlled model change: use installed qwen3:8b, digest
500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41, with the exact v9 prompts,
source package, schema and options. This is two calls (draft reasoning/review without reasoning),
16384 context, temperature0/seed42, shared60s budget, no retries, no new downloads or weight changes.
Use the same ten exposed cases, at most12 generation calls/15minutes, after v10 finishes.
This comparison changes model only; do not attribute any difference to retrieval or prompt quality.

Require five useful, supported, readable answers, correct gap/four scope blocks, no unsupported
claims and no provider failures for preview consideration. Record concept completeness separately,
including any unmet original rubric requirements. Source review is engineering review, not an
independent clinical assessment or formal Step5–7 acceptance. Preserve every failure and raw trace.
