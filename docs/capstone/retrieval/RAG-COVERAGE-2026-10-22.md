# October 22 continuation: close demonstrated answer-coverage gaps

Quinton explicitly requested further improvement after the 9/20 checkpoint. This is
new continuation authority; the earlier two-round limit is preserved as history.
Keep the same 20 public answerable questions, 10 boundaries, ≥18/20 complete-answer
criterion and independent evaluation requirements. No hidden questions, model change,
corpus expansion, training or patient inference.

The existing papers contain the missing information. Version 3 of the source-bound
study catalog adds eleven reusable topics: TAGS reader reliability, reference masks,
prompting/comparison limitations, center transfer and unmeasured workflow benefit;
pancreas subregion assumptions, whole-organ localization limits, label reconciliation
and head/duodenum anatomy; prostate reviewer consistency versus reference accuracy and
possible explanations for acceptance of AI contours. Facts and both prose variants
were checked against the canonical passages, independently of expected-answer text.
This is a single engineering source review, not independent or human acceptance.

Typed routing admits one covered research task. A narrow study scope adapter handles
research questions lacking the word pancreas and the explicit negative benchmark
comparison, while retaining input, privacy, patient and instruction-refusal gates.
Different tasks, organs and modalities are not treated as interchangeable. The same
local model selects reviewed wording and paragraph layout; exact citations and all
required facts/qualifications remain code-checked. This is constrained composition,
not an unrestricted answer generator or proof of general language understanding.

Before changing the implementation, the 40-case public
`rag-study-coverage-development-v1.json` matrix froze 22 natural paraphrases and 18
unsupported, mixed-task, patient, modality and instruction boundaries. These are
exposed development material. Expected labels stay in the evaluator, never the model
request or search index. Original corpus and prior record versions remain unchanged.

Implementation checkpoint: 288 focused Python checks passed, including every new
record's two wording variants, missing qualifications, exact citations, the frozen
paraphrases and refusal precedence. Candidate runs on 8019; the live answer server
and UI remain on the earlier qualified version until end-to-end checks and source
inspection pass. Retained run evidence: `outputs/prowl/rag-coverage-20261022/`.

Actual results and promotion decision will be appended here.

## Retained first attempt and focused repair

The first candidate produced text for all 20 answerable questions, but only 17 were
complete under the existing concepts: the subregion input needed reference-guided
cropping and zero masking; the TAGS workflow example needed explicit zero-shot versus
SAM-TAGS/MSD-TAGS attribution; the reviewer example needed the 0.78→0.89 comparison.
All10 boundaries remained unanswered. Three answers separately used the explicitly
labeled fallback (anatomy, subregion limitations and localization); these are not
counted as successful model composition. Version3 and its full HTTP results remain.

A single captured diagnostic reproduced the model returning both wording variants
for each of two units. The study composer now requests a closed object with one
required 0/1 choice per source unit. It rejects missing/extra/duplicate keys and
noninteger choices before the existing complete-fact, qualification and citation
checks. Code already owned layout; no omitted model choice is invented or repaired.
Disease, volume and measurement composers retain their previous plan protocol.
The study prompt/config pin changes explicitly. One actual same-case diagnostic
passes after repair. No retries were added to runtime generation.

Version4 adds the missing details from canonical passages 35877639:39/59,
42738357:50/77 and 41414851:2/70. No expected answer is supplied to the application.
All289 focused Python checks pass. One intermediate test invocation used a stale
version3 review fixture with version4 records and correctly rejected it; the fixture
was corrected, with integrity checks unchanged. Final real replays remain pending.

## Final source-reviewed result and activation

| Check | Result |
| --- | --- |
| Same public20 answerable questions | **20/20 complete, supported answers**, up from9/20 |
| Same public10 boundaries | **10/10** no composed answer |
| Frozen new wording/boundary matrix | **22/22** expected answers; **18/18** no-answer boundaries |
| Existing narrow regression packet | **20/20** supported answers; **10/10** boundaries |
| Prior32 interpretation cases |16 supported answers;16 clarifications/abstentions; historical contour expectation preserved and separately explained below |
| Actual final candidate traffic |132 HTTP requests;78 model compositions;0 fallbacks/service failures |
| Exact source/citation checks |378 displayed citation links match canonical evidence; no corpus change |
| Answer latency across final suites |1.53–14.49 seconds; median2.21 seconds |
| Python / UI / build |289 focused Python checks;85 UI checks passed,1 skipped; build passed with existing large-chunk warning |

I read all20 final public answers against the unchanged required concepts. Every
new fact and both variants were compared with the canonical passages; UI validation
also rejects changed prose, missing qualifiers and substituted citations. Factual
support, completeness, readability, citations, refusal behavior and latency are
recorded separately in `engineering-review.json`. This is one engineering review;
it is not an independent adjudication. The old interpretation matrix's contour row
originally requested abstention while the topic was uncovered; its new supported
answer satisfies the unchanged formal question, not that historical expectation.

Version4 is activated through the existing study-answer API and UI contract. The
pre-activation candidate UI check used the same generic validators with version4
source contracts; after activation, all132 actual responses also passed through the
normal UI entry point. No browser automation or human layout walkthrough is claimed.
The release script's four-second readiness window was too short for service startup:
the same process subsequently became healthy without relaunch. An initial UI test
correctly rejected its old version2 pins before the switch; applying the qualified
version4 contract resolved the mismatch. Both observations are preserved, not erased.

Readable actual answers and sources: `outputs/prowl/rag-coverage-20261022/all-questions.md`.
Initial candidate, duplicate-plan diagnostic, corrected diagnostic, final four suite
receipts, producing snapshots and release evidence remain alongside that packet.
The corpus remains14papers/1179passages; the pinned Qwen3:8b model is unchanged.

The **public development answer criterion** now exceeds the existing18/20 threshold.
This does not close AI-04 or certify overall accuracy: independent questions, source
retrieval MacroRecall@5/MRR, broader operational reliability, human review and the
measurement extension remain separate unfinished requirements. The next useful work
is to consolidate exposed development material and use the existing independent
question/labeling workflow, without another custom tool or model sweep. Unknown
question types can still receive source-only results or clarification; typed topic
selection remains deliberately limited.

Post-activation checks through5180 also pass: TAGS reliability and subregion input
answers, the inflammation-versus-tumor answer, an instruction/privacy boundary and a
source-only TAGS query. Three live compositions took1.52–6.56s; source search0.37s.
All five responses passed the normal UI validator. Temporary candidate8019 was stopped;
live8016 remains active. No database/model restart or unrelated-service change was
needed during this continuation. Reliability's earlier historical questions remain open.
