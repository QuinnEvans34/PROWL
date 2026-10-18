# Instruction-model answer quality checkpoint

The new instruction model and narrower evidence boundaries improve some answers, but fluent prose
and a positive model review remain insufficient evidence of correctness. All runs below use exposed
development questions; none is an independent test. The corpus and original evidence labels are
unchanged. No candidate in this report has been deployed at this checkpoint.

## Model and provenance

Qwen2.5:14b runs on an isolated loopback server and external model store. Registry manifest SHA256
`7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6` is pinned.
The initial pull completed but its verification assertion failed because Ollama adds an original-
manifest provenance layer. That failure is retained. A separate verification checked the exact
registry config/four layers, the additional provenance layer, all blob hashes and sizes, and API
identity. Local manifest SHA256 is `6cc76debadf2078edb12cb46b2da3ecf32334b5636f95221da8512e76b36e2a5`.
Store size is 8,988,130,944 bytes. No original model, source or cache was deleted.

## Retained outcomes

| Version | Observed outcome | Engineering assessment |
|---|---|---|
| V15 | Two summaries; four generation responses; 46.450s | Rejected: anatomical and disease associations broadened, study mean presented without enough qualification. |
| V16 | One summary, one withheld; five responses; 49.278s | Citation-isolated review still approves an unsupported CP age association. Rejected. |
| V17 | One summary, one withheld; four responses; 24.834s | First-paper focus produces a supported but technical head-enlargement statement. Volume repair receives incomplete validation feedback. Not qualified. |
| V18 | One volume regression; two actual calls; 14.415s | Reuses the retained initial draft; fixes simultaneous study-boundary/uncertainty feedback. Adds counts/method but retains excessive and ambiguous MRI sequence detail. Not an end-to-end pass. |
| V19 | Two rendering regressions; four calls; 13.699s combined case time | Writer sees only original statements; code retains citation bindings. Head and volume rewrites are clearer and source-faithful in these two cases. Not a pipeline qualification. |
| V20 | Three summaries, three withheld, four scope blocks; 23 generation responses and six unloads; 123.504s | Rejected. Findings rewrite broadens named cancer to any tumor and omits modality; average-size rewrite drops study qualification; function reviewer incorrectly demands numerical-study details; source-absence draft is rejected. |

V18's initial draft stub is explicitly marked as reused and excluded from actual model-call counts.
V19 timing excludes earlier drafting and cannot be compared with end-to-end latency. V20 includes
per-request unloads; its supervisor completed in 125.196s with peak sampled owned RSS13,724,745,728
bytes and worker reaped. V20 literature requests took9.682–33.118s; this is not a percentile guarantee.
All four scope refusals made zero generation calls. Failed raw drafts remain local and are not answers.

V21 completed and is rejected: zero summaries, five withheld, one empty result and four scope blocks.
It received 21 generation responses and six unload responses in 111.424s. Supervisor:113.085s,
13,611,171,840 bytes peak sampled owned RSS, worker reaped, no resource stop. The empty result means
no supported answer was produced, not a verified absence across the literature. No raw draft displayed.
The reviewer marks qualification false with empty feedback on head/findings/function answers;
revision repeats the draft. Volume feedback short-circuits at an unrequested percentage before
reaching the study checks. The preservation rule rejects omission of the MRI field strength even
though the basic method remains: a false refusal illustrates the cost of broad lexical rules.
The model did not reliably follow the conditional-qualification requirement. No promotion and no
further candidate expansion in this checkpoint. All19 new focused boundary checks and24 restored
live search/HTTP checks pass; unit correctness does not establish answer quality.

The initial attempted HTTP test path did not exist and ran zero tests; the correct module then
passed24. No successful run is substituted for the retained failed command. Producing source
snapshots match their pre-run hashes for V15–V21. Original source/evaluation identities are fixed.
The isolated server87026/session31824 was unloaded and stopped successfully; its external store is
retained. The original model server and live API/UI are unchanged. The unused preview server edits
were removed so no rejected candidate can be selected accidentally through that unfinished flag.

## What this establishes

A paper-focused answer can be easier to verify than a model merging unrelated retrieved papers, but
it can omit relevant evidence from other papers. The explicit top-ranked-paper scope is a limitation,
not full literature synthesis. Exact citations establish identity; they do not prove entailment.
A same-model reviewer has repeatedly approved unsupported scope changes. Numerical-token and disease-
term preservation checks are narrow safeguards, not general semantic verification.

The original full-concept rubric is still open: the head answer lacks the broader differential and
limits; a single-study mean is not a population norm; imaging comparisons must preserve modality and
specific disease context. Formal retrieval evaluation, independent labels/review and the required
pancreas/lesion measurement extension remain incomplete. No user acceptance or human hours is inferred.

## Next implementation decision

Do not continue model/prompt sweeps on the same exposed ten questions. The offline feedback collector is now repaired in `src/retrieval/answer_feedback.py`:
independent mechanical failures are collected together, failed drafts return no partial claims,
and unexplained negative reviewer flags stay rejected instead of triggering an uninformative rewrite.
Seven focused tests pass. Two retained V21 traces confirm percentage + study-boundary + uncertainty
feedback together and explicit rejection of the blank qualification reason, with zero model calls.
Receipt: `outputs/prowl/answer-feedback-offline-20261018/receipt.json`. This helper is not wired into
the live or historical candidate policies; no answer-quality improvement is claimed from offline tests.
Next integrate explicit per-criterion review reasons rather than one shared qualification boolean. Separate content support from
style and from task-specific completeness; do not require every answer to carry every qualifier.
Revisit numerical preservation by semantic role: a scanner field strength is not a participant
count. Qualify these mechanics against retained failures and invented counterexamples before any
new bounded generation run. Source-aware retrieval still needs the unchanged label/gate review.
No claim of system-wide confidence, clinical readiness or final capstone completion follows.
