# Bounded reasoning diagnostic — October 17, 2026

## Frozen design

Quinton approved continuing the five-case reasoning diagnosis. Clean starting checkpoint afce439.
Fresh checks found Ollama and the answer API offline; only local-only Ollama was restored for this
saved-passage experiment. No database or demo API restart is needed. The current live-policy source
remains unchanged; do not describe the demo as running without verifying its services.

`reasoning-diagnostic-v1.json` freezes this order before inference: radiomics, PET neuroendocrine,
CT external validation (known failures), nCLE (positive control), randomized survival (unsupported
control). The parent ten-case suite, questions, retrieved passages and rubrics remain unchanged.
The derived five-case suite has its own hash and is never reported as a ten-case result.

Use the installed digest-pinned Qwen3:30B. Same schema, source ordering, temperature0, seed42,
context8192 and selection instructions, except `/no_think` becomes `/think`. Enable `think=true`
and raise the output cap from900 to2048 to accommodate reasoning plus final JSON. This compares
an explicit reasoning profile including its larger token allowance, not the boolean alone. No
free-form reasoning is published as an answer: only final selected source spans can be returned.
Raw outputs remain local. Original nonreasoning requests/provenance remain byte-compatible.

Limits:300seconds total,60seconds per API call, at most five model calls, no retries or extension.
Timeout interrupts the client and ends the run; confirm server cancellation if it occurs. A returned
length-limited or malformed result fails closed, counts as invalid and is retained. Every completed
request/raw response is saved immediately. Preserve the source/profile snapshot before inference.

Success for this diagnosis requires fixing all three failures while retaining the positive control
and correct unsupported abstention:4/4clean supported answers,8/8aspects,1/1correct abstention,
no irrelevant excerpts or invalid generations. The saved nonreasoning subset has2/4supported,
1/4clean,3/8aspects and1/1correct abstention. A success is permission to consider full-suite regression
verification, not automatic promotion or held-out/generalization evidence. No full corpus selector,
training, corpus writes, downloads or human-hours credit.

## Results

Completed all five cases in 113.255 seconds, five calls, no retries or timeouts. The owned
client exited successfully; this indicates completed measurement, not quality acceptance.

| Case | Reasoning profile result | Output tokens | Wall seconds |
|---|---|---:|---:|
| Radiomics | Rejected: token cap reached, empty final JSON | 2048 | 33.382 |
| PET neuroendocrine | Correct study, tracer and tumor grades | 992 | 12.795 |
| CT external | Rejected: token cap reached, empty final JSON | 2048 | 26.535 |
| nCLE positive control | Rejected: token cap reached, empty final JSON | 2048 | 28.022 |
| Randomized survival | Correct unsupported-evidence abstention | 898 | 12.515 |

All four supported cases still contain a reference hit. Compared with the identical nonreasoning
subset, supported answers fall from 2/4 to 1/4 and aspect coverage from 3/8 to 2/8. Clean answers
remain 1/4, but PET replaces the lost nCLE positive control. Unsupported abstention remains 1/1.
The single emitted excerpt is exact and relevant. Three invalid generations are separately counted;
the scorer's zero transport errors must not be interpreted as zero generation failures.

**Decision: reject this profile for promotion.** PET recovery is real but does not offset loss of
the control and other answers. This establishes failure of this specific 2048-token profile, not
that reasoning can never work or that a larger budget would succeed. No increased budget, repeat,
full-suite run or extra stage follows automatically. These are corpus-informed development cases,
judged by engineering review, not independent clinical or held-out evaluation.

## Verification and retained evidence

59 focused tests passed, including five-case dispatch, frozen-rubric/profile validation, strict
budgets, source/schema preservation and token-exhaustion rejection. Fifteen exact offline generation
replays passed: five new reasoning receipts and all ten old direct30B nonreasoning receipts. Five
old/new request comparisons differ only in the declared mode directive, think flag and output cap.
Scoring recomputes exactly from immutable receipts and the published hash-bound judgments.
No model calls were made during replay or scoring.

Public review: `configs/evidence/evaluation/reasoning-diagnostic-v1-review.json` includes the exact
baseline subset projection, its original receipt/review identities and all current judgments.
Local evidence: `outputs/prowl/reasoning-diagnostic-20261017/direct-spans-30b-reasoning-v1/` contains
the manifest, pre-run producing-source snapshots, five immediate raw call records, five receipts,
completion, baseline projection and offline verification. The pre-run report is retained separately;
this results update does not overwrite that snapshot. Raw model responses and article text stay local.

Ollama 0.40.2 reports all slots idle after the final response. Only Ollama was restored; the answer
API still refuses connections on8014. No claim that the full demo is currently running. Production
answer policy, database and corpus are unchanged; no selector continuation or training occurred.

## Next recommendation

Pause model/prompt experiments and implement the first explicit expert workflow slice using the
existing retrieval, selection, validation and immutable-save functions. Expose stage status and
preserve the distinction between unsupported evidence and invalid generation, with reuse of completed
retrieval and an explicit retry of a failed generation. Demonstrate that behavior with saved fixtures
before another quality experiment. This advances the capstone workflow while the answer-quality
criterion remains visibly open; orchestration does not repair semantic relevance. This next slice
is proposed, not delivered by this diagnostic. No new orchestration framework is needed by default.
