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

## Results

Baseline and comparison pending. Services verified alive with the expected pinned Qwen3:8b and
healthy dedicated database before this work. The initial generic `/health` check returned404;
the actual `/research-evidence/health` and `/research-answers/health` routes succeeded.
