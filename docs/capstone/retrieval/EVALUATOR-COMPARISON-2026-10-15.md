# Bounded evaluator comparison — October 15, 2026

## Frozen experiment

Quinton accepted this comparison after the failed 8B scope review. Change only the evaluator
from Qwen3:8B to the already installed Qwen3:30B, digest
`ad815644918f0eaab341c12b67837cc6dd4562342cdaf118f83d5d554cb37226`.
Keep nonreasoning mode, seed42, temperature0, context8192, output900, scope prompt/schema,
source spans and the ten development questions unchanged. Reuse immutable selections from
`outputs/prowl/development-evaluation-20261015/structured-spans-v1/`.
The recorded 8B scope run is the comparator; do not rerun it. This tests model capability on known
failures, not held-out generalization or independent verification. Selection still belongs to8B;
separate scope-model fields identify the evaluator accurately.

The runner reads saved receipts, not the live database. Their suite, corpus-manifest, question,
content hashes and resolved span identities must match before inference. Full raw text/output stays
in ignored local artifacts. Each completed model response is saved immediately, including request
hash; source snapshots and input hashes accompany the run. Total wall limit600seconds and per-API
call limit60seconds include loading; timeout/interrupt/error ends the run without retry. POSIX
alarms interrupt the HTTP client; after an interruption, confirm Ollama has canceled the request.
No claim that a client deadline alone proves server cancellation.

Predeclared success criteria: improve the previous4/7 clean complete answers; preserve the
structured selector's seven supported answers and12/14 covered aspects; reject all four known
irrelevant selections; retain all eight useful selections; no invalid assessments. Scope expansion
should recover missing CT method/nCLE result context without borrowing another study. Report the
full fixed rubric even when these criteria fail. Three saved abstentions bypass review: preservation
only, not new evidence that this evaluator recognizes unsupported questions. Review latency includes
cold loading and must be reported separately from earlier selection/retrieval. No automatic demo
promotion follows a small development result.

Before inference:19 focused tests pass, covering evaluator pins/provenance, fail-closed behavior,
source identity, actual wall-alarm expiry/nesting/cleanup and frozen receipt tamper refusal.

## Results

Completed ten cases / twelve review calls in28.427seconds; no timeout, retry, error or invalid
assessment. The owned client exited0. Ollama reported all slots idle; the answer API health check
passed. Existing demo policy/source unchanged. No live database reads or writes were needed.

| Fixed development measure | Saved8B scope | New30B scope |
| --- | ---: | ---: |
| Supported answers | 5/7 | 7/7 |
| Clean, complete answers | 4/7 | 5/7 |
| Covered answer aspects | 9/14 | 14/14 |
| Relevant / emitted excerpts | 5/6 | 8/10 |
| Exact source quotations | 6/6 | 10/10 |
| Invalid assessments | 2 | 0 |
| Preserved missing-evidence abstentions | 3/3 | 3/3 |

All eight useful original selections survive. Two of four known irrelevant selections are removed;
two survive. No quality acceptance: the predeclared rejection criterion fails. Compared with the
unreviewed structured selector, clean answers rise4→5, coverage12→14, and irrelevant excerpts4→2.
The new stage has evidence of useful improvement, but remains experimental.

- General EUS: both useful selections survive;8B previously lost the entire answer.
- CT external validation: expands the correct result to include method/cohort; removes the unrelated
  CNN study. Its reason still calls the wrong study's cohort a match, so even a correct final rejection
  does not establish accurate per-axis judgments.
- nCLE: recovers the correct35-patient/82% result and rejects the first wrong EUS selection. It also
  accepts a different EUS99.6% result, falsely describing the supplied fragment as nCLE. The fragment
  itself lacks the study identity needed to support that attribution. Quotation exactness does not
  make that attribution true.
- Radiomics definition: retains the correct workflow but accepts an application example. Its rationale
  treats an implied extraction method as sufficient despite the prompt's explicit directness rule.
- CT detection, MRI differential and PET grading controls remain clean.

Supported-case review wall time: median4.086seconds, range1.636–9.353seconds. First case includes
cold loading; this is one observed run, not a warmed or concurrent latency benchmark. Prior8B median
was4.020seconds, with fewer calls due to invalid-answer short circuits. No speed claim follows.
Reason strings sometimes end mid-sentence at the500-character schema limit; they remain untrusted
audit notes and never become answer evidence. Three negatives skipped inference entirely.

## Verification and retained evidence

56 focused checks pass, including a simulated mid-case deadline that preserves the first raw response,
marks all unfinished cases unscored, disables alarms and makes no retry. One initial broader test
command named nonexistent test files and collected nothing; corrected paths produced the56 passes.
Twenty offline receipt replays reproduce both ten-case runs (excluding newly explicit provenance
fields in the older8B receipts). All ten requests shared by the two runs match exactly after removing
only the model name; all twelve30B request hashes match saved call receipts. No replay inference.
The public hash-bound review recomputes exactly with the unchanged scoring function.

Local evidence: `outputs/prowl/development-evaluation-20261015/scope-30b-v1/` contains the frozen
pre-run plan/source snapshots, manifest, ten receipts, twelve immediate raw-response receipts,
completion, score and replay/input comparison. Public summary judgments:
`configs/evidence/evaluation/scope-30b-v1-review.json`. Article text and raw model output stay local.
The final report extends the frozen pre-run plan; the producing copy remains unchanged.

## Engineering decision / proposed next step

Do not promote30B scope review to the demo. Keep it as a measured candidate; model capacity helps
retention and context selection but does not reliably establish study identity or question relevance.
Next, build source-linked evidence records from the existing papers: preserve adjacent paragraph
context for continuation fragments and require cited source spans for study/method/cohort/result
relationships. Separate definition/workflow evidence from detection-performance evidence. Missing
study identity must remain unknown rather than being inferred from the question. Test that concrete
repair against these failures and retained positive controls before wiring the expert DAG.
This is a proposed implementation step, not evidence that such records or an independent judge exist.
No corpus expansion, full selector, training or human-hours credit in this comparison.
