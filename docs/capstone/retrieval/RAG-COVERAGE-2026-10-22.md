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
