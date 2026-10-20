# Week 3 wording and answer quality — frozen development check

October 20, 2026. W03-04 and W03-05, authorized autonomous sequence after the demo.

Freeze `configs/evidence/week3-quality-matrix-v1.json` before baseline execution: 12 disease
and eight MRI study-volume questions, plus ten scope/ambiguity/instruction boundaries.
Intended record sets derive from the five reviewed source records, not observed model outputs.
General inflammation comparisons require both represented chronic/autoimmune examples;
head-enlargement questions require the focal-head record. General volume questions may use
the explicitly qualified normal-glucose-tolerance study example; type-two questions use the
diabetes record. Comparisons require both. These are exposed development questions, including
two demo questions. They are not independent test questions or formal split denominators.

Run the current service construction with the same database, encoder, model and HTTP handler
in an isolated loopback server on an OS-assigned port. Leave the live demo unchanged during
evaluation. Capture requests, responses, model plans, source/configuration hashes and timings
privately. One sequential attempt per case, no model retry. Maximum 20 chat calls per batch,
30-second model deadline, 40-second request deadline, 20-minute batch watchdog, 50 MiB retained
output ceiling. No imaging inference in parallel. An unexpected service failure stops the batch.
Retain failed attempts. Before/after use identical questions and expected record sets.

Classify a supported-case failure as routing (incorrect/no record selection despite available
facts), missing evidence (required relation/context absent from admitted sources), composition
(selected facts but invalid/incomplete model plan), or refusal (an erroneous scope denial).
Boundary cases must make zero model calls and provide no purported composed answer; clarification
and explicitly unassessed passages are acceptable. Do not count a fallback as model success.

Score separately: exact intended selection; source identity and claim support; mandatory facts
and qualifications; readable ordering/paragraphs; exact citations/locators; end-to-end latency;
model composition versus reviewed fallback. Manually inspect all distinct emitted wording and
its source links and check each response's binding. The original pre-demo V01 fallback remains
recorded even if a new run succeeds. Raw-plan capture is needed to explain new failures.

Engineering promotion requires at least 18/20 directly composed, complete supported responses,
10/10 safe boundaries, no unsupported claim or invalid citation, and each matched response under
40 seconds. Inspect remaining failures explicitly; do not broaden coverage without source review.
This threshold does not close formal retrieval/independent acceptance. Quinton's walkthrough
decision remains a separate human item; an engineering pass cannot substitute for it.

After baseline, repair the largest demonstrated problem, version changed policies, run relevant
regressions, and execute one candidate batch. A further attempt requires a concrete new observed
failure and documented change. Deliver readable questions, answers, linked source locators and
dimension-by-dimension results. Only then promote a passing candidate to the demo.

Next measurement work freezes a development subset from the current checkpoint's admitted split
before inference/reference comparison. Compare unchanged raw masks and the already frozen CP01
method across cases, including annotation-empty examples when available. Do not select another
cleanup from the single-case residual. Current cohort metadata must be verified first; old split
files cannot establish current membership. No training or protected-case access is authorized.
