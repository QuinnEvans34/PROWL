# Structured evidence selection — October 15, 2026

Quinton approved this next development step after the failed prompt-only comparison.
The source remains the approved capstone proposal; this is still an extractive prototype.

## Change and comparison contract

`source-spans-v1` offers exact contiguous ranges of up to three source sentences,40–1600 characters.
The model sees all sentences of each retrieved passage in order, grouped by source, plus allowed
range IDs such as `P2:1-3`. Its response selects up to three IDs. A request-specific JSON schema
enumerates allowed IDs; the server independently checks the selection and resolves IDs to original
passage IDs, exact text and relative character offsets. The model cannot author the published text.
The existing quotation validation remains the final check; duplicate-sentence handling is unchanged.
The final saved answer/UI contract stays compatible with earlier results.

IDs are aliases scoped to the ordered passage catalog, not globally stable source identifiers.
Provenance records the catalog hash, schema hash, span policy and prompt hash; selected IDs are
retained. Sentence boundaries conservatively avoid common abbreviations and decimals, preserving
all original characters/whitespace in a selected range. They are not a linguistic guarantee:
preexisting chunks may start or end mid-sentence, and study context absent from retrieval cannot
be recreated. No cross-passage stitching, inferred study labels or automatic semantic verification.
Input bounds refuse more than20 passages,20 sentences per passage or4000 characters per passage.
No selectable span skips generation with an explicit `no_selectable_spans` reason.

New generation policy: `verified-spans-v1`. Model, digest, temperature, seed, token limits and
retrieval remain fixed. The prompt describes the selection protocol and requires matching study,
technique/task and cohort while keeping necessary context. Thus this comparison measures a
structured-selection package, not a causal isolation of prompt wording from output constraints.
No question IDs, expected answers, gold references or score rubrics enter model input.

Before live evaluation:39 focused tests pass, including12 new span/selection checks. These cover
exact offsets and reference markers, abbreviation/decimal handling, invalid/duplicate IDs,
cross-source refusal, full context delivery, dynamic schema, exact server materialization and
fail-closed generation. Existing saved-answer validation and request behavior remain in place.

Run the frozen ten-case development suite once, reusing baseline passages. Assess all previously
recorded metrics; promotion requires improvement in clean complete answers, no per-case loss of
baseline aspect coverage,3/3 missing-evidence abstentions, exact quotations throughout, and no
generation rejection. Preserve raw outputs/failures. This is development evidence, not held-out
validation. If accepted, refresh only the existing answer service and check a new live answer plus
unchanged saved-response retry. Do not restart the corpus or other services.

## Results

**Implemented and retained as an experimental selector; not promoted to the live demo.**
All ten cases completed. The source-span comparison used exactly the same retrieved passages as
baseline; no new retrieval or corpus writes. All7 supported cases produced valid answers, all3
missing-evidence cases abstained, and there were zero generation rejections. Copying errors are
eliminated by server materialization for valid selections; semantic scope errors remain.

| Measure | Baseline quotations v2 | Structured spans v1 |
| --- | ---: | ---: |
| Supported reference hit@5 | 7/7 | 7/7 (reused) |
| Published exact citations | 13/13 | 12/12 |
| Strictly relevant extracts | 10/13 (76.9%) | 8/12 (66.7%) |
| Supported questions answered | 6/7 | 7/7 |
| Expected aspects covered | 11/14 | 12/14 |
| Complete answers with only relevant extracts | 4/7 | 4/7 |
| Correct missing-evidence abstentions | 3/3 | 3/3 |
| Rejected generations | 1 | 0 |

The CT detection answer now selects one relevant CT study without the PET/CT addition. The general
EUS answer remains clean. But the radiomics answer adds a study-application sentence unrelated to
how features are extracted, replacing the previous clean answer with a partly irrelevant answer.
The nCLE question still selects other EUS morphology results and misses the requested82% result.
The CT external-performance answer now publishes exact AUCs, but includes another CNN study's
results and omits CT-method context in its relevant excerpt. MRI and explicitly requested PET/CT
answers remain clean. These judgments were made against the existing rubric, without an LLM judge;
they are engineering review, not independent clinical adjudication or held-out evidence.

Promotion criteria failed: clean-answer count did not improve and an existing question regressed
in relevance. The successful copying repair does not establish study attribution or semantic support.
No extra prompt variants or repeated model runs were used to obtain a passing score.

Selection latency median1.535s (range0.977–2.596), compared with baseline median6.590s. Both use
the same installed model/options; the structured response is much shorter. This is an observed
sequential development-run difference, not a controlled warm/cold or hardware performance benchmark.
Total case median1.537s includes reading cached retrieval, not live search or encoder setup.

## Final integration and evidence

The experimental implementation lives in `src/retrieval/span_answer.py` with reusable span
construction/resolution in `src/retrieval/evidence_spans.py`. The evaluator requires explicit
`--selector spans`; its default and both live APIs retain the baseline quotation policy.
`src/retrieval/grounded_answer.py` is byte-identical to the committed baseline. No API restart,
UI change, saved-response rewrite or silent default switch occurred.

The comparison initially ran with the candidate in the default module, without restarting the
live service. Before separating it into the experimental module, every producing source was copied
and verified against the run manifest under the ignored `producing-sources/` directory. All ten
raw model responses were then replayed offline through the final experimental module and reproduced
the retained generation objects exactly. This establishes that the module separation preserved the
evaluated behavior; replay made zero model/DB calls.39 focused checks pass after separation.

Public judgments: `configs/evidence/evaluation/structured-spans-v1-review.json`.
Immutable local evidence: `outputs/prowl/development-evaluation-20261015/structured-spans-v1/`.
No article text, model bytes, credentials or runtime receipts are committed.

Recompute the score with no model or database calls:

```sh
.venv-retrieval/bin/python -m src.retrieval.evaluation --run outputs/prowl/development-evaluation-20261015/structured-spans-v1 --review configs/evidence/evaluation/structured-spans-v1-review.json
```

For an explicitly intended new experimental run, use a fresh output directory:

```sh
.venv-retrieval/bin/python scripts/retrieval/evaluate_answers.py --selector spans --reuse-retrieval outputs/prowl/development-evaluation-20261015/baseline --output outputs/prowl/development-evaluation-20261015/NEW-RUN-NAME
```

## Next

Use the span mechanism as the input to a separate study-scope verification step. It must associate
each selected result with its technique, cohort and task, reject neighboring-study substitutions,
and retain necessary method/result context. It must also expose unsupported or ambiguous study
attribution rather than treating exact text matching as a relevance verdict. This step is not yet
implemented; the same small model's self-review would not be independent verification. Keep held-out
evaluation separate and measure loss of useful evidence as well as rejection of irrelevant evidence.
The full selector remains parked; no training, corpus writes or human-hours inference.
