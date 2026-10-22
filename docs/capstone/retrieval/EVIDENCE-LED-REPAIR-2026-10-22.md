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
