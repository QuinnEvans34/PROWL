# Measurement-aware AI expert final-deliverable extension

**Status:** Required final deliverable; bounded current-scan volume development started October 20 by explicit user sequencing amendment. Formal acceptance remains open.

**Authority:** Quinton's explicit October 17, 2026 instruction: “This is now a part of our plan and
must be part of the final deliverable.”

**Owner:** DAG/RAG development chat with Quinton; coordinate imaging and training adapters with
those components' owners.

**Execution:** [Completion specification](AI-EXPERT-COMPLETION-SPEC.md), Steps 10–12.

This is a committed scope addition, not an optional stretch goal. It adds verified measurements,
reference comparisons, plain-language explanations and a human-reviewed training-feedback path
on top of a proven literature system. Original proposal/appendix files and their integrity hashes
remain unchanged; this dated user amendment explicitly records the added implementation scope.
It does not claim institutional approval of a revised proposal or authorize patient diagnosis.

## October 17 disease context clarification

Quinton approved PanTS plus a focused pancreatitis/pancreatic-cancer literature collection, with
cystic disease later. The [first source slice](DISEASE-REFERENCE-CORPUS-2026-10-17.md) is built as a
separate candidate. REQ-X03 must distinguish measured facts, cited general disease associations and
unknown/unmeasured features in the selected scan. Disease names in an article or PanTS report are
not a diagnosis of the displayed case. Actual measurement and viewer adapters remain required.

The next capability contract must resolve head/body/tail measurement definitions and available
outputs, report provenance/split eligibility, and disease-context input/output behavior. Existing
clinical boundaries and numerical acceptance gates remain; source addition alone does not qualify
this extension. Quinton supplies realistic questions without technical evidence labeling; independent
label creation/verification is an engineering responsibility to arrange before collecting held-out work.

## October 20 implementation sequencing amendment

Quinton requested connecting current-scan measurements now. The [bounded contract](CURRENT-SCAN-VOLUME-CONTRACT-2026-10-20.md) permits a saved-mask volume development preview before core acceptance. It preserves the final acceptance criteria below; preview implementation does not satisfy or waive them.

## Original sequence and formal acceptance gate

Finish core RAG Steps 1–9 first. “Working as expected” means recorded acceptance, not a working demo:

- The frozen development and protected held-out sets each meet the existing retrieval and response
  thresholds: source recall@5 and MRR at least 0.80, at least 18/20 clean complete answers and 10/10
  required refusals, with all claim/citation and privacy gates met. Preserve the exact frozen rubric.
- Required corpus/index reproducibility, failure/recovery and finding-to-evidence UI checks pass.
- Plain-language questions and explanation behavior are qualified within that accepted scope.
- The producing release/configuration identities, limitations and operator procedure are recorded,
  and Quinton's core acceptance review is documented.

A rejected summary candidate or excerpt-only fallback does not satisfy this entry gate. Until then,
only planning/tracking for this extension proceeds. Current implementation priority remains the
scan-centered capability and evaluation reconciliation in Step 5. No training or full selector restart.

## Required capabilities and acceptance

| Requirement | Final-deliverable capability | Required evidence |
|---|---|---|
| REQ-X01 | Calculate pancreas and individual suspected-lesion volumes and a precisely defined lesion diameter from valid source-space outlines. | Versioned measurement method, units, geometry/coverage checks, multiple-lesion handling and source/mask/model lineage; analytic fixtures and reference-reviewed development cases. Freeze numerical tolerances before validation. |
| REQ-X02 | Compare an eligible measurement with an appropriate published reference statistic. | Rights-cleared reference record with population, quantity, units, measurement method, statistic type, source locator and eligibility rules; independently checked comparison arithmetic. Demonstrate at least one supported comparison. |
| REQ-X03 | Explain measurements and reference comparisons in everyday language, with inspectable provenance and citations. | Distinguish local computed facts from literature facts; preserve units, reference population and limitations; meaningful answer, mismatch, missing-evidence, invalid-measurement and refusal cases; viewer/case-switch/recovery checks. |
| REQ-X04 | Provide a human-reviewed feedback path for future segmentation training and error analysis. | Auditable review queue, verified corrections, training-consumable manifest, split-role enforcement and downstream loader dry-run with zero optimizer updates. Unreviewed AI claims and protected evaluation cases must be rejected. |

Measurements are software calculations, not language-model visual estimates. Record whether the
mask is a prediction or a human-reviewed revision. Missing or invalid measurements are not zero.
Check spatial units, transforms, cropped/partial coverage, empty masks, multiple components and
mismatched artifacts. A plausible number does not establish an accurate contour. Do not fabricate
measurement confidence or use a segmentation score as a confidence interval.

Before extending model inputs, version the measurement-summary contract and its validation. Reuse
existing imaging measurements where qualified. The current coarse-input contract remains binding
until that version is delivered. Keep images, masks, identifiers and private case linkage out of the
literature index/model prompt. Permit only the minimal validated summary needed by the new adapter.
Reference eligibility may require additional context; any such fields require explicit schema/privacy
review. Missing matching information must not be guessed or silently filled from a patient record.

Reference records must distinguish length, diameter and volume; means, medians, ranges and
percentiles; and population versus study-specific findings. Do not derive a percentile from a mean
alone. A source describing a general length range cannot substantiate average organ volume. New
corpus additions and reference tables require rights/source checks and new version identities.

## Intended statements and limits

- “The predicted lesion's maximum diameter is X mm,” with its defined method and mask provenance.
- “The estimated pancreas volume is above the mean reported for this reference cohort,” only when
  the measurement/reference comparison is eligible. Above a mean is not a finding of abnormality.
- “This study reports the following findings for lesions in this size group,” only with its actual
  population, methods and limitations attached; no conclusion about the displayed lesion follows.
- “A reliable comparison is unavailable because the outline is incomplete / the reference method
  differs / matching information is missing,” when the evidence does not support comparison.

Patient-specific diagnosis, malignancy, stage, prognosis, treatment and contour certification remain
outside this extension. “A lesion this size indicates cancer” is not an authorized output. General
cited research context is required; clinical inference would be a separate scope and validation effort.
Unusual size may reflect anatomy or a segmentation problem: it triggers review, never automatic
reshaping toward an average. Preserve citation requirements and protected-system refusals.

## Training feedback boundary

The final deliverable includes a working feedback pipeline, not merely a suggestion to train later.
Record reviewer identity/action, original and corrected mask identities, measurement/error evidence,
source provenance and eligibility role. Produce an inspected training-consumable manifest and show
that the existing or versioned loader can consume eligible reviewed entries without optimizer work.
Keep evaluation/development records segregated according to their frozen roles; no automatic transfer
of held-out or development cases into training. Human approval does not override prohibited roles.

AI-generated explanations are annotations to review, not ground truth. No automatic self-training,
LLM fine-tuning or measured model improvement is promised by this requirement. Actual retraining
requires its own cohort/experiment/resource scope and remains unstarted. The expert initially gains
knowledge through validated measurements and retrieval, not by memorizing its own generated claims.

## Execution and final release

| Step | Trello | Exit |
|---|---|---|
| 10 | [AI-05 — verified measurements](https://trello.com/c/Ob3VE0MN) | REQ-X01 and versioned adapter validated after core acceptance. |
| 11 | [AI-06 — cited comparisons and explanations](https://trello.com/c/TKCLH5PZ) | REQ-X02–X03 supported comparison and failure/refusal evidence; ready for integrated acceptance. |
| 12 | [AI-07 — reviewed feedback and extension acceptance](https://trello.com/c/pL25Swot) | REQ-X04 plus integrated viewer, extension evaluation, operator documentation and presentation walkthrough. |

Before implementation experiments, freeze extension cases, expected measurements, reference
eligibility, claim rubric and numerical tolerances. Preserve accepted core results as that version's
baseline. Newly tuned functionality needs a separately protected final assessment; do not reuse
exposed core held-out cases as fresh independent evidence or tune against their outcomes. Quinton
owns protected authoring/storage; the chat receives only permitted hashes/counts/attestations.

Completion requires successful supported behavior as well as correct failures: a refusal-only demo
cannot close REQ-X02 or REQ-X03. Deliver the measurement and reference records, test/evaluation
reports, UI flow, feedback export/loader evidence, reproducible runbook and presentation examples.
No new numerical threshold is claimed frozen by this high-level plan; criteria must be fixed before
results and cannot be relaxed afterward to manufacture acceptance.

Core RAG acceptance alone no longer completes the expanded AI-expert deliverable. All four REQ-X
requirements and Steps 10–12 must pass. If a dependency or reference source cannot be qualified,
report the unmet requirement and resolve it explicitly; do not silently downgrade it to stretch work.
Schedule impact must be reconciled at the next planning checkpoint; existing dates are not evidence
that the increased scope fits. This documentation amendment launches no code, model or training job.
