# Retrieval development evaluation — October 15, 2026

User authorized this bounded evaluation after restoring the local demo. The approved proposal
remains authoritative: evidence-supported reviewer assistance with citations or abstention.
This checkpoint evaluates extractive evidence selection, not the complete proposed expert.

## Frozen before execution

`configs/evidence/evaluation/development-v1.json` contains ten cases: three existing demo
regressions, four new supported questions, and three missing-evidence questions. Seven total
supported cases include paired CT/MRI/PET and subtype boundaries. These are corpus-informed
development examples, not an independent or held-out quality estimate. Final evaluation must
use a separate set. Expected statuses, aspects, scope exclusions and reference passage IDs were
written before running this baseline. References were reviewed in the retained source passages;
they are not exhaustive relevance judgments. Negative cases ask for evidence absent from this
two-paper corpus, not claims about the entire medical literature.

Suite canonical SHA256: `111870a211db6efcc2ac9c977d164634714274b5d2334d7fce51978ed0f1f061`.
Corpus: research-v1, 274 passages, PMID35406426 and PMID37173876; canonical sorted record SHA256
`2956ed092c71c787129cceb5237df0c06b98b8993faf5d6319eab7bd831319b8`.

Run `scripts/retrieval/evaluate_answers.py` with the existing retrieval environment, private
config and a fresh ignored output directory. It calls the same guided retrieval and generation
functions as the API; additional questions are offline harness inputs, not new public API choices.
Only question text and retrieved passages reach the model. No expected answers/reference IDs
or scoring rubric enter generation. No new embeddings, database writes, selector or training.

Each immutable run retains suite/code/prompt/model/encoder identities, retrieved passages,
raw model responses (including rejected generations), validated answers and per-case timings.
The runner rejects changed corpus records and existing output directories. Errors are retained
as errors, not counted as successful abstentions. A comparison can reuse the identical baseline
retrieval to isolate a generation change; its retrieval timing is then a file read, not a search.
Local article text and runtime evidence remain ignored; only questions, IDs, code and summary
judgments are committed. Initial system-Python preparation failed on missing jsonschema before
writing the suite; preparation then used the existing retrieval environment without installation.

## Scoring fixed before execution

- Retrieval reference hit@5: at least one authored relevant reference among retrieved passages,
  reported over seven supported cases. This is reference coverage, not precision or exhaustive recall.
- Citation integrity: exact quotation in the cited retrieved passage; every extract must validate.
- Extract relevance: manually mark each extract relevant, mixed (some relevant text plus unrelated
  study/task), or irrelevant using each case's scope. Only relevant counts toward strict precision.
- Answer coverage: manually mark each authored aspect present or absent in the selected excerpts;
  report covered/14 supported aspects. Reading the source alone does not count as answer coverage.
- Missing-evidence abstention: explicit insufficient evidence with no generation failure, out of three.
- Supported answer rate: valid nonempty answers out of seven; abstaining on every case cannot pass.
- Clean supported answers: all aspects covered and every extract relevant, out of seven.
- Latency: per-case retrieval, selection and wall time, with model duration where available; separate
  fresh retrieval baseline from cached-retrieval comparison. Ten sequential cases are not a load test.

Freeze judgments against receipt hashes; keep baseline failures. Choose one repair after examining
baseline outputs, then compare the same cases and retrieval once. Accept only if the targeted
error improves without reducing supported coverage or missing-evidence abstention. Report mixed
or negative results, and do not repeatedly tune until this set passes. No clinical-quality claim.

## Results and engineering decision

**Baseline completed; prompt-only candidate rejected. Production remains verified-extracts-v2.**
The freeze/harness was committed and published as `442daee` before either model run. Both runs
completed ten cases without service exceptions, with one rejected generation each. All ten
candidate retrieval snapshots exactly match baseline, so retrieval was not a changed variable.
Same model/digest/options, corpus, encoder, question wording and validator. The candidate changed
only the selection prompt and its policy identity to experimental verified-extracts-v3.

| Measure | Baseline v2 | Rejected prompt v3 |
| --- | ---: | ---: |
| Supported reference hit@5 | 7/7 | 7/7 (reused) |
| Published exact citations | 13/13 | 11/11 |
| Strictly relevant extracts | 10/13 (76.9%) | 7/11 (63.6%) |
| Supported questions answered | 6/7 | 6/7 |
| Expected aspects covered | 11/14 | 12/14 |
| Complete answers with only relevant extracts | 4/7 | 3/7 |
| Correct missing-evidence abstentions | 3/3 | 3/3 |
| Rejected generations | 1 | 1 |

These are engineering judgments by Codex against the prewritten rubric, not independent clinical
adjudication. Exact citations measure published outputs only; the rejected raw generations remain
available and are not counted as correct missing-evidence abstentions. No model served as judge.
The public JSON reviews retain per-case judgments, reasons, receipt hashes and recomputable totals.

Baseline failures:
- CT detection adds PET/CT neuroendocrine evidence despite retrieving the relevant CT studies.
- Specific EUS-nCLE question includes a different EUS morphology study's 43-patient cohort and
  99.6% result. The requested 35-patient cohort is present, but its 82% result is omitted.
- Specific CT external-performance question is rejected: a candidate quotation from an unrelated
  CNN study drops its inline reference marker, failing exact matching. The valid relevant quote
  cannot rescue an invalid whole answer under the existing fail-closed validator.

Candidate prompt explicitly required matching modality/technique, disease, task, study and cohort;
it also emphasized retaining reference markers. It removed the CT/PET mistake and recovered the
requested nCLE accuracy and CT performance, but still mixed studies. It regressed the general EUS
answer by including adjacent MRI results, and mistyped a radiomics passage ID (`ps3:` instead of
`psg:`), causing rejection. The lower strict relevance and fewer clean answers justify rejection
despite higher aggregate aspect coverage. No additional prompt variants or model sweep followed.
The candidate prompt is retained in `scoped-selection-v3-review.json`; its exact producing source
is retained locally. Restored production source is byte-identical to the frozen baseline.

Timing: baseline retrieval median0.114s (range0.093–0.129), answer selection median6.590s
(range1.064–14.082), total median6.688s (range1.179–14.211). Candidate answer selection median7.330s
(range1.143–13.956); retrieval was a cached file read, not a new search. Summed case time66.813s
baseline and65.725s candidate excludes encoder initialization and setup. No latency improvement,
load capacity or reproducibility-across-hardware claim follows from these two sequential runs.

## Reproduce and inspect

Existing local evidence, excluded from Git:

- `outputs/prowl/development-evaluation-20261015/baseline/`
- `outputs/prowl/development-evaluation-20261015/scoped-selection-v3/`

Each contains a manifest, ten immutable case receipts, raw model responses and a scored review.
The candidate directory also contains `candidate-grounded-answer.py`. The default public model
interface remains the original three fixed questions; the additional seven are evaluation only.

From the repository root, recompute either saved score without model/DB calls:

```sh
.venv-retrieval/bin/python -m src.retrieval.evaluation --run outputs/prowl/development-evaluation-20261015/baseline --review configs/evidence/evaluation/baseline-review-v1.json
.venv-retrieval/bin/python -m src.retrieval.evaluation --run outputs/prowl/development-evaluation-20261015/scoped-selection-v3 --review configs/evidence/evaluation/scoped-selection-v3-review.json
```

Both score recomputations passed; all receipts and review bindings verify. A new live baseline
can use the following command with a **new** run name; it will call the local model ten times:

```sh
.venv-retrieval/bin/python scripts/retrieval/evaluate_answers.py --output outputs/prowl/development-evaluation-20261015/NEW-RUN-NAME
```

Verification:8 new offline evaluation checks pass;27 combined evaluation/generation/retrieval/store
checks pass. The first immutable-writer test expected the wrong exception class; corrected to the
existing ValueError contract before the freeze commit. Existing source and UI were not changed by
the final checkpoint, so no browser/build rerun or API restart was needed. Services were verified
alive with the pinned Qwen3:8b and healthy database. An initial generic `/health` request returned
404; actual `/research-evidence/health` and `/research-answers/health` routes succeeded.

## Next development step

Evidence selection is the demonstrated bottleneck for these cases; adding corpus volume is not
the first repair. Implement selection from server-owned source spans with stable bounded IDs,
preserving neighboring study context and distinguishing the requested technique/task. That should
remove free-form ID/text copying as a failure source; relevance still requires separate measurement.
Keep this development set available for regression and reserve unseen cases for later evaluation.
This is proposed follow-on work, not an implemented semantic verifier or accepted quality fix.
The explicit expert DAG/reuse/retry milestone follows this selection repair. Full selector and
training remain parked in this chat. No human project hours inferred.
