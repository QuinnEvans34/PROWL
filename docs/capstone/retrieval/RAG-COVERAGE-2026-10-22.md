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
