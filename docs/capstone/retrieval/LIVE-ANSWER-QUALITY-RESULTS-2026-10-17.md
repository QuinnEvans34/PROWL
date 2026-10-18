# Live answer quality: failed candidates and a bounded repair

The live preview now uses **natural-literature-answer-v6.1**: the unchanged v6 prompts/model/options
with two mechanical source-wording checks. The disease-question browser smoke now blocks a draft that fails the
source-wording check and keeps the original passages available. The function answer and source navigation
work, but unexplained jargon remains. This is a concrete repair, not answer-quality acceptance.

Quinton's request to move to live answer quality authorizes this development sequencing amendment.
It does not approve the pending v6 labels, complete protected evaluation or release retrieval tuning.
The corpus, exact dense top5, model weights and expected-answer separation are unchanged.

## What was tried and rejected

Both candidates were planned and pinned before their runs. Each used the same six retained questions
and exact old top5 evidence sets once. There was no retrieval rerun, label injection or retry. The
generation helper received only the question and canonical retrieved source text/title; its request
never contained expected answers, required concepts or review labels. Full provider request/response
traces and source text remain local, not committed.

| Case | v7 | v8 |
|---|---|---|
| Head size/disease | Insufficient retrieved evidence | Review rejection |
| Inflammation/tumor findings | Insufficient retrieved evidence | Review rejection |
| Published volume example | Summary with unsupported population wording | Review rejection |
| Ambiguous size | Incomplete generation | Review rejection |
| Function regression | Supported functional content, unexplained jargon | Review rejection |
| Duct-contour policy gap | Insufficient retrieved evidence | Review rejection |

[V7 plan](LIVE-ANSWER-QUALITY-V7-2026-10-17.md): expanded generic instruction and explicit review
dimensions (support, relevance, qualifications, readability). Eleven generation calls,213.145seconds
total; individual cases15.647–53.736seconds. The reviewer approved a “healthy control group” description
where the cited passage used an undefined NGT abbreviation. It also approved unexplained specialist
terms in the function answer. Two summaries, three insufficiencies and one truncated draft: **not
promoted**. Insufficiency on an answerable corpus question is not a completed answer or retrieval win.

[V8 plan](LIVE-ANSWER-QUALITY-V8-2026-10-17.md): compact prompts, non-reasoning draft mode and a
population-word backstop. Twelve generation calls,24.222seconds total; individual cases1.903–5.881s.
Every review returned safe=false, including empty drafts; none produced a displayed answer or checked
insufficiency. Hidden drafts retained jargon and one misread a percentage's denominator; the review
still marked those support/readability dimensions true. **Not promoted**. The shorter time therefore
does not establish a useful latency improvement. No third prompt candidate was attempted.

These are exposed engineering observations, not independent tests. Same-model review is demonstrably
fallible. The controlled evidence replay isolates policy changes from retrieval, but multiple changed
prompt/mode factors prevent attribution to one individual factor. No broad statistical claims follow.

## What actually changed live

[V6.1 repair plan](LIVE-ANSWER-QUALIFIER-REPAIR-2026-10-17.md): preserve the exact v6 prompt/schema hash
and generation options. Before model review, reject introduced mandatory wording or selected
healthy/normal-person/control-group descriptions absent from the cited passage text. Regression checks
block both retained offending drafts: v6's “requiring comparison” and v7's “healthy control group.”
The final lexical check distinguishes the verb “controls” from a control-group descriptor; a new
invented regression qualified this false-positive fix after the live smoke, followed by service reload.

These are conservative backstops, not semantic guarantees. They can reject legitimate paraphrases,
miss other overstatements and be satisfied by an unrelated matching word. Existing numerical/citation
checks and semantic review remain necessary. The UI explains the new closed failure category and
describes insufficient evidence as a limit of the returned passages, not a conclusion about the
entire library. A rejected generation remains a failure, not a successful refusal.

Final-code validation:88focused Python checks passed before the verb distinction;14affected guard
checks passed afterward, including the one new case (89distinct checks across final-code attempts).
Twenty-seven UI checks and production build passed; the existing large imaging/compression-chunk
warning remains. Earlier candidate runs had91Python/29UI checks for v7 and58affected Python checks
for v8; those counts are not additional unique final-code checks. No failed tests were hidden.

Two browser questions were submitted once each through the UI→literature API→database→Ollama path,
with no retries and at most four generation calls. The function answer appeared and its source2
button focused the corresponding paper/excerpt. The head-size question displayed the new qualifier
failure and all five passages. No new browser console errors were observed. These live provider
traces were not captured, so exact generation-call counts and response timings are not asserted.
Their visible outcomes and screenshots are retained locally. The final verb-only fix was tested
offline and the service reloaded; these two model requests were not repeated.

One API restart failed when PostgreSQL closed its connection. Retained database logs show a backend
process exited and PostgreSQL performed automatic recovery. Its cause is unproven. After recovery,
the service's full canonical inventory admission passed; no data deletion, DB restart, migration,
cache cleanup or unrelated container changes were performed. Final API health is checked separately.

## Records and next work

- [v7 pinned plan](../../../configs/evidence/evaluation/answer-quality-v7-plan.json) and
  [v8 pinned plan](../../../configs/evidence/evaluation/answer-quality-v8-plan.json).
- [Selected v6.1 policy](../../../configs/evidence/natural-answer-v6.1.json).
- [Readable local candidate outcomes](../../../outputs/prowl/live-answer-qualifier-v61-20261017/answers-and-outcomes.md).
- Local rejected candidates: `outputs/prowl/live-answer-quality-v7-20261017/` and `live-answer-quality-v8-20261017/`.
  Each retains its exact producing source snapshot. Historical plan pins describe the source at
  execution, not the final checkout; the checkpoint maps the preserved snapshots to those hashes.
- [Live result screenshot](../../../outputs/prowl/live-answer-qualifier-v61-20261017/live-source-check.jpg).

Recover relevant disease passages and source context before another answer-prompt experiment.
The previous diagnostic already showed relevant evidence exists but dense top5 misses it. Complete
the applicable development review/independent evaluation freeze, then compare lexical, dense and
hybrid rankings under the spec. Keep readability, false abstentions, qualifiers and claim support as
separate acceptance dimensions. AI-03 and AI-04 remain open; the required measurement-aware extension
still follows core acceptance. No training, full selector, protected content or human-hours credit.
