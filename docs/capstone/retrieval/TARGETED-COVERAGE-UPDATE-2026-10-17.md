# Targeted coverage update and evaluation checkpoint

October 17, 2026. Quinton authorized one pre-freeze corpus update, followed by the evaluation checkpoint.
The new corpus is built and reproducible. Changed human label review, set-wide consistency and independent
protected authoring/freeze remain pending; no retrieval comparison or answer-quality acceptance is claimed.

## What changed

`research-coverage-v2` and its independent rebuild contain **10 papers / 947 passages / 32 batches**.
All seven previous sources and 23 batches (693 passages) were reused unchanged. The original live
`research-v1` demo and both v1 coverage collections retain their exact inventories.

Content SHA: `6978c2f0aaef592efaec76792c615d2fd96e63fde37688d0b595e2f003baeb8d`.
The [manifest](../../../configs/evidence/corpus-coverage-v2.json) preserves its v1 parent, source snapshots,
rights, normalization, vectors, acquisition bounds and receipts. Raw articles remain in ignored local outputs.

| Addition | Passages | Coverage and limitation |
|---|---:|---|
| [Macauley et al., MRI volume study](https://pmc.ncbi.nlm.nih.gov/articles/PMC4423920/) | 60 | Study-specific volume example: 14 normal-glucose-tolerance controls, MRI, mean ± SEM. This small matched group is not a universal population reference or CT normality threshold. |
| [Choi et al., multiplanar/volumetric CT](https://pmc.ncbi.nlm.nih.gov/articles/PMC7540900/) | 51 | Diameter measurement planes, segmented 3D volume and irregular-lesion rationale. Single-center retrospective surgical cohort; no patient staging, prognosis or treatment inference. |
| [Pancreatic senescence review](https://pmc.ncbi.nlm.nih.gov/articles/PMC9962587/) | 143 | Age/fat-related morphology context. Narrative review with human and animal evidence; not a validated contour policy or patient reference interval. |

The [v2 coverage matrix](../../../configs/evidence/coverage-matrix-v2.json) changes N2.1, N2.3 and N3.3:
**7 direct / 16 partial / 2 gaps**, versus 6/15/4. Diameter/volume and normal-variation needs have bounded
support, not exhaustive coverage. Duct inclusion/exclusion and validated boundary-confidence calibration
remain gaps after checking the additions. All judgments are exposed development work.

Discovery was purposive, not systematic. PMC7674810, PMC12004316 and PMC8711217 remain metadata-only
because their licenses fall outside the current adapter. PMC8904764 was inspected but excluded: its
reported overall volume mean conflicts with its sex-specific means/counts, and reported total and sex
counts differ. This is a local quality hold, not a claim of retraction. Its metadata relation names a
preprint, not a correction. Other discovery leads were not acquired/admitted. The retained acquisition
amendment replaces this candidate while keeping three admitted additions and the original resource bounds.

## Ingestion and verification

The coverage parser now recognizes exact CC BY 4.0 identifiers using HTTP as well as HTTPS, plus the
publisher's license attribute and ALI license-reference field. This does not admit NC/ND/older licenses,
lookalike hosts, arbitrary redirects or licenses mentioned outside article permissions. Legacy-profile
acceptance is unchanged. All ten raw snapshots reproduce their canonical bundles exactly, including all
seven old sources. The selected new snapshots contain no inspected correction/retraction relations;
notice checking is bounded to retained JATS/core metadata, not exhaustive surveillance.

- 37 ingestion/inventory/rebuild checks passed; five optional DB tests skipped. The real build and rebuild
  are separate live evidence, not replacements for the skipped synthetic integration checks.
- Exact independent rebuild completed in 5.99 seconds. Three existing guided queries match between v2
  and its rebuild; this tests reproducibility, not relevance or acceptance.
- 59 draft/review checks passed, including seven new review-inheritance tests.
- 34 public checkpoint checks passed using invented content-free receipts.
- The real v5 draft validates against the new corpus. `--require-ready` correctly refuses the unfinished checkpoint.

Preflight preserved the 104 GiB internal / 408 GiB external free-space floors and 8 GiB DB cap. Existing
pinned MiniLM embeddings were used only for the additions; old vectors were reused. No generator call,
training, full selector, protected-store access, service restart or demo repointing occurred.

## Evaluation delta, not a restarted review

[Development v5](../../../configs/evidence/evaluation/development-v5-draft.json) retains 30 cases:
20 answerable / eight scope refusals / two evidence gaps. Two revised intents exercise the additions:
Q8 diameter versus volume and Q10 a study-specific average pancreas volume. Their old wording remains
exposed in v4 and must remain in cross-split duplicate review. Q1/Q5/Q7/Q9 gain background-only spans;
none becomes an additional direct gold source. Every answerable case gets judgments for all three new
papers. No expected answer is added to the literature database or model prompt.

The [v5 reading copy](DEVELOPMENT-QUESTIONS-AND-ANSWERS-V5.md) is separate from the unchanged v4 file.
The old ten-event human review remains untouched. Delta validation compares exact question/concept/
answer content, labels, source judgments and corpus identity: it carries **28 wording/answer decisions
and eight refusal evidence decisions**, with zero invented events. The other 22 cases need only changed
source judgments/new labels/gap rechecks; existing accepted evidence remains visible. All 30 require the
already-planned second consistency pass. Changed corpus-gap labels cannot inherit old acceptance merely
because their spans are empty.

Local consolidated packet: `outputs/prowl/development-v5-coverage-review-20261017/changes-to-review.md`.
The same folder has `all-questions.md` for the final consistency pass. Do not return to small batches.
Source text stays local; public artifacts contain labels, provenance and paraphrases.

## Continue the evaluation checkpoint

Run from the repository root:

```sh
.venv-retrieval/bin/python -m src.retrieval.evaluation_checkpoint --require-ready
```

This checks the actual corpus, v5 development record, inherited v4 decisions and a closed content-free
held-out receipt. It currently exits pending. The [v2 blank receipt](../../../configs/evidence/evaluation/heldout-receipt-template-v2.json)
contains no private content and truthfully says `not_created`. Keep v1 as historical. The completed
receipt is a separate `heldout-receipt-v2.json`; the command accepts only those two named public files.
Extra fields such as questions, labels, paths, credentials and free-form notes are refused without echo.

Quinton must complete the delta review and set-wide consistency, independently author 30 protected cases
(20 answerable/10 unsupported), review all exposed versions/intents, confirm storage allocation, validate
private labels, and freeze/verify the independent encrypted backup. Return only the receipt's hashes,
aggregate counts and attestations. See [updated private authoring worksheet](PROTECTED-EVALUATION-AUTHORING.md).
The public checker cannot prove the truth of those attestations or inspect the private backup. No private
image, questions or validation run was created by this work. A private authoring/validation runner remains
undelivered; do not mark its mechanical-validation attestation true without actual private verification.

Only the complete checkpoint permits Step 6 configuration comparison. The required measurement-aware
pancreas/lesion extension remains after core Steps 1–9 acceptance.
