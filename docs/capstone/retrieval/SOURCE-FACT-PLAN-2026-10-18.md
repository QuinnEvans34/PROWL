# Source-linked volume fact records: bounded prototype

Quinton approved implementation and testing after the controlled evidence experiment, with Trello
updates and coherent commits. Start with the existing PMID25950180 MRI volume study, separately
representing its14-person normal-glucose-tolerance comparison group and41-person well-controlled
type2-diabetes/metformin group. This is a local prototype, not a production policy replacement.

## Contract

Each versioned record binds object, anatomical extent, quantity, unit, population, sample count,
method, statistic, mean, uncertainty and its kind, matching and interpretation limits. Each source
field references exact canonical passage offsets/hashes. Record digests include those locations.
A separate engineering-review inventory admits only the exact reviewed record and corpus identity.
That inventory is trusted repository configuration, not a cryptographic proof of factual truth or
reviewer identity. Editing the inventory would require a new source review. Independent review is
pending; do not describe agent-curated facts as human-verified or accepted gold.

The prototype validates field presence, supported types, canonical spans, limited literal field
correspondence and review identity. It cannot automatically establish arbitrary semantic entailment.
The reviewed mapping, for example the order of paired T2DM/NGT values, remains a curation obligation.
Retain exact source payloads locally; tracked files contain structured facts and hashed locators.

Deterministic assembly includes ALL required qualifications. No model chooses whether to retain
the sample, MRI method, SEM meaning, matched population or study-specific limits. Interpretation
limits and the controlled statistical glossary are labeled separately from direct source findings.
The envelope binds every sentence to its fields/spans/original citations; exact regeneration rejects
a later rewrite, qualifier removal or citation substitution. No question-specific answer strings,
expected answers or evaluation labels enter the catalog or rendering functions.

## Separate selection and rendering

Selection consumes real canonical search hits plus an explicitly supplied structured intent:
object/extent/quantity/population/method/uncertainty kind/use. The result passage must be retrieved;
a paper title or incidental methods passage is not enough. On selection, expand the complete reviewed
record, including metadata not in top5. Never select a whole-organ volume record for head dimensions,
lesion size, CT norms, SD or a patient-normality/diagnosis request. No automatic fallback to a different
population or quantity. Unsupported requests return no eligible record or unsupported use.

Natural-language intent extraction is NOT implemented/qualified here. The diagnostic harness openly
supplies the intent; it does not hide a question-to-answer lookup table or claim free-text success.
One fresh source-only live query uses unchanged exposed quality-03 wording; separately select both
reviewed populations from the result hit and render each. Compare the NGT result against retained
incomplete quality-03 drafts and the unchanged required concepts. No Ollama/model generation calls,
training, full selector, protected evaluation, new corpus/model download or patient arrays.

## Checks and result gate

Use synthetic fixtures for meaningful mutation tests: missing field/limit, mismatched evidence,
changed result/group/count/unit/object/statistic, changed source text/offsets, missing result hit,
unsupported intent, fabricated retrieval hit, post-render omission/relabeling and alias mutation.
Test deterministic qualification preservation separately from record selection and provenance.
After the implementation checkpoint, run one actual-corpus canary with one source-only query and
manual inspection of every rendered sentence and supporting spans. Preserve errors and original
source/labels/failed trials; do not tune the old evaluation answers to make this pass.

Success here means complete supported assembly for these two reviewed records and rejection of the
declared mismatches. It does not mean improved LLM reasoning, broad retrieval coverage, independent
acceptance, disease-answer qualification or permission to switch the UI. Keep baseline dense/v6.1.
Finish with results, readable local answers/source evidence, spec/handoff/Trello and Git checkpoints.
Bound the canary to60seconds/one HTTP query/12MiB local output, no retries. No human hours inferred.
