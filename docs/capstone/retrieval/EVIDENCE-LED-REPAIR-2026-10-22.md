# Evidence-led answer repair — October 22

Quinton authorized repair until the test cases work. The failed frozen evaluation remains **0/20**;
its 30 cases are now exposed regression material. The original requests, responses, scoring and
closed-image backup remain unchanged. Passing these cases cannot establish held-out generalization.
The runtime never reads the evaluation suite, expected answers, concepts or evidence labels.

The candidate `--evidence-answers` removes the curated-record prerequisite. It combines the existing
dense results with lexical source-section navigation, lets the pinned local Qwen3:8b select relevant
sections, binds their complete canonical passages, and composes an answer. It distinguishes ordinary
negative/general clinical research wording from individual diagnosis, treatment and private-data
requests. Specific refusals explain the boundary; evidence gaps remain distinct from service errors.
No source corpus, embedding model, expected label or training run changes.

Support, completeness and readability are separate review criteria. One revision receives every
reported issue. Its review receives the original question/evidence and revised draft only, not the
previous critique. Each paragraph's citations collectively support its clauses; each citation need
not independently support the entire paragraph. Canonical identity checks are mechanical integrity
checks, not proof of factual correctness. Same-model review still requires manual citation inspection.

Initial diagnostics are retained in the encrypted regression workspace. Attempt 1 stopped on a
missing request ID in the trusted adapter ticket; invented-source tests reproduced and fixed it.
Attempt 2 retrieved relevant sections, but the reviewer listed positive support as errors, expanded
questions into unrelated tasks and reused stale feedback. Two later requests had transient database
connection errors; database readiness subsequently passed. No failed draft was promoted to the UI.
The narrower task/review contract and compressed source menu are undergoing the next bounded check.

The UI accepts a separate evidence-answer contract and reuses its existing answer/source tabs.
Invented-source tests cover altered records, unknown citations, client-injected labels, complete
feedback repair, failure withholding and source-only operation. Frontend tests verify response
identity, corpus/model/citation binding, readable display and source navigation. Backend deadline
is 120 seconds; browser cancellation is 150 seconds to allow transport overhead. This is a ceiling,
not an acceptable typical-latency target. Actual useful-answer latency will be reported separately.

Candidate promotion requires manual support/completeness/citation/boundary checks, comparison with
existing public development cases, and UI validation. The frozen record-based service stays live
on port 8016 while the candidate is tested on 8019. Results are pending; no 20/20 claim is made.

## Subsequent repair probes (not promotion)

The encrypted workspace retains each attempted configuration and its responses. The section-menu
selector, both fast models, and a 30B reasoning variant did not qualify. Failures included unrelated
section selection, false evidence gaps, unsupported morphology, missing qualifications, contradictory
review feedback, token exhaustion and database interruptions. The separate database repair is recorded
in RELIABILITY-CLOSEOUT-2026-10-20.md (commit68161f0); it does not establish answer quality.

A lexical+dense retrieval diagnostic initially overlapped61/74 required concept spans in12/20 complete
sets; the existing cross-encoder overlapped54/74 in10/20. These are permissive **span-delivery checks**,
not Recall@k, complete conceptual support or answer accuracy. Adding adjacent canonical context changed
the six-section result to60/74 in11/20; bounded budgets of8/10/12 sections yielded62/68/69 spans and
12/15/16 complete sets respectively. No expected label or corpus changed. Query reformulation was also
probed; it did not resolve several missing-evidence cases and is not integrated.

The candidate now selects exact source sentences, removes duplicate sentences, requests one required
rewritten unit per selected fact, and binds citations in code. It checks numeric preservation separately
from the model's support/completeness/readability review. Reference and figure/table numbers are excluded
from that mechanical check. This catches some dropped qualifications but is not semantic proof: selecting
irrelevant facts still produces an irrelevant answer. Additional context is restricted to selected source
section parts. The original whole-library selection experiment remains available only as a nondefault
constructor option; default selection is lexical+dense.

A demonstrated gap-review defect is repaired: when no facts are selected, the reviewer now receives the
retrieved original passages, rather than an empty source list. It must distinguish a correctly explained
missing fact from an incomplete answer to an available fact. Drafts/selection traces are excluded from
ordinary responses; explicit `--evidence-trace` is for the private local regression harness only. The
candidate on8019 remains separate from the live8016 service. No broader answer-accuracy claim follows
from schema, UI or source-integrity tests.
