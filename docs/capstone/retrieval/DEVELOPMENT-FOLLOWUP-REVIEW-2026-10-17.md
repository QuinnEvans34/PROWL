# Development evaluation follow-up review — October 17, 2026

**Result:** All 30 development cases received a follow-up review by the same authoring agent.
Four label sets were corrected; no question wording or expected answerability changed. This is a
review of proposed evidence labels, not measured AI performance or independent expert validation.
AI-03 remains In Progress; the full evaluation freeze is incomplete.

Quinton reported that the first five cases looked great and relevant, then requested agent review
of the rest. Record that as favorable relevance feedback on `q:dev2-01`–`05`. His expectation that
the other cases will look fine is not a review of those cases. No completed source-label adjudication
or second human consistency pass is inferred; machine-readable human review remains pending.

## Current artifacts

Start with the [readable questions and expected answers](DEVELOPMENT-QUESTIONS-AND-ANSWERS.md).
The local HTML remains available for exact source-text inspection.

- Revised draft: `configs/evidence/evaluation/development-v3-draft.json`.
- Canonical content SHA-256: `ca4dacfe39a429493d56fdf8f7ed0f928d2ec76657ee199eea0ad5ca7387a83e`.
- Review receipt: `configs/evidence/evaluation/development-v3-review.json`.
- Local source-text packet: `outputs/prowl/evaluation-review-20261017/development-review-v3.html`.
- Prior v2 draft, preparation receipt and original HTML packet remain unchanged.

The filename versions the suite. Stable `q:dev2-*` IDs and question version 1 remain because wording
has not changed. Cases 05, 08, 16 and 17 now carry `label_version: dev2-draft-v2`; other 26 case
records are byte-equivalent as JSON values. The corpus, schema and validator are unchanged.

## Findings and corrections

1. **05 — additional background:** PMC8997008 body-38 explicitly discusses interdisciplinary
   segmentation variation. Added this as partial context and corrected its source judgment. It does
   not contain the required mean volumes; PMC8357939 remains the direct numerical source.
2. **08 — missing review trigger:** the original labels included inspection and optional blinded
   editing, but omitted the intervening sentence identifying unusually divergent contours. Added
   that exact sentence from PMC8357939 body-21 as direct support. STAPLE remains a surrogate.
3. **16 — comparison identity:** explicitly identify 47.0% as TAGS (Zero-Shot) and 15.8% as each
   fine-tuned variant, MSD-TAGS and SAM-TAGS. Body-27 supplies the named comparison; the unnamed
   discussion statement in body-38 is now partial context. No measured workflow benefit follows.
4. **17 — entailment strength:** “generally did not surpass” and “did not consistently outperform”
   do not alone establish the stronger “less accurate” claim. Downgraded the abstract/conclusion
   spans to partial context. Body-47 explicitly supplies the stronger study-specific comparison.
   The prostate scope and distinction between observer agreement and reference accuracy remain required.

All source identifiers refer to immutable representations in the seven-source frozen corpus manifest.
Exact source text stays in the local packet and canonical bundles; this report paraphrases findings.

## Case-by-case disposition

“Retain” means no further change recommended in this bounded agent review, not human acceptance.

| Case | Disposition | Main check |
|---|---|---|
| 01 | Retain | Less than 15 HU applies to both named phases; study definition only. |
| 02 | Retain | Portal venous timing is relative to pancreatic phase, not contrast injection. |
| 03 | Retain | Retrospective/single-center selection and EUS-FNA specificity limitation retained. |
| 04 | Retain | Fixed imaging conditions and possible 5 mm partial-volume effects, not proven universal effects. |
| 05 | Revised | Numerical observers/units preserved; additional review background added. |
| 06 | Retain | Inter-reader 0.742 versus repeat-reader 0.838; 30 examinations and three-week washout correctly assigned. |
| 07 | Retain | Uncertain regions and non-target exclusions belong to this research protocol. |
| 08 | Revised | Complete outlier-review trigger; six-observer STAPLE remains a surrogate. |
| 09 | Retain | Duodenal adjacency does not establish a frequency of segmentation errors. |
| 10 | Retain | Arrangement, length and volume priors are method-specific assumptions. |
| 11 | Retain | Whole-pancreas assumption limits surgical/inflammatory applicability; no subgroup error rate implied. |
| 12 | Retain | Reference-based crop and masking prevent autonomous-localization claims. |
| 13 | Retain | Reference-derived point, MedSAM2 box and different system components preclude matched-prompt interpretation. |
| 14 | Retain | Train three centers/test fourth; MSD-TAGS DSC 0.703 to 0.678; prompt-assisted scope. |
| 15 | Retain | DSC versus NSD at 5 mm; predictions returned to native image grid. |
| 16 | Revised | Zero-shot and fine-tuned model identities explicit; workload benefit unmeasured. |
| 17 | Revised | Weaker non-superiority statements are context, not direct evidence for inferiority. |
| 18 | Retain | Possible automation bias and deliberate acceptance are alternatives, not established causes. |
| 19 | Retain | 96% follows shared review; remaining labels resolved by agreement, not independent agreement measurement. |
| 20 | Retain | Initial single reader, senior edits, extra reliability contour excluded from reference. |
| 21 | Retain refusal | Current-patient diagnosis is outside the literature assistant's scope. |
| 22 | Retain refusal | Current-lesion staging is outside scope. |
| 23 | Retain refusal | Patient-specific treatment is outside scope. |
| 24 | Retain refusal | Patient-specific prognosis is outside scope. |
| 25 | Retain refusal | Patient source reports cannot enter literature retrieval. |
| 26 | Retain refusal | Citation/policy bypass request; no legitimate literature question to answer. |
| 27 | Retain refusal | Protected system information and credentials request. |
| 28 | Retain refusal | Literature support cannot certify a current contour. |
| 29 | Retain insufficient evidence | Duct signs and attenuation ROI exclusions do not specify pancreas-contour inclusion policy. |
| 30 | Retain insufficient evidence | Probability maps and segmentation variability are not calibrated uncertainty validation. |

The eight refusals match the frozen RF categories. Both gap judgments were rechecked with lexical
inspection across all seven representations and relevant context, including the TAGS statement that
uncertainty estimation was not evaluated. These remain bounded absence judgments, not proof that
no such evidence exists elsewhere. This review did not conduct an exhaustive new literature search.

## Consistency and limitations

Related cases 11/12, 06/20 and 17/18 ask distinct but related questions and remain in the exposed
split together. The old ten-case suite remains exposed and separate. No held-out content was read,
so no cross-split independence claim is possible. Explicit study names and shared sources can make
retrieval easier. The designated difficulty categories are author judgments; multiple support spans
do not necessarily require multiple retrieved chunks. Do not report them as demonstrated difficulty.

The current draft remains 20 answerable, eight refusals and two gaps, across all five families.
There are **60 spans: 45 direct, 10 partial context and five limiting**. Each answerable question
still has one direct gold source. Source recall@5's theoretical ceiling remains 1.0, not an observed score.
All direct spans fit frozen passages, and every required concept has a direct support link.

The existing offline validator passes on the revised draft. Verification also checks unchanged
question text/order, exactly four revised cases, unchanged old pinned artifacts, and revised-packet
case coverage. No production code changed, so the prior 31-test result is historical and was not rerun.
The first draft revision incorrectly incremented question versions for label-only edits and was
rejected by the unchanged schema. A repair attempt used system Python without jsonschema and made
no changes; the virtual-environment repair retained question version 1 and versioned the labels.
Rejected draft and attempt notes are preserved locally; final validation passed without weakening guards.

## Next review

Use the readable Q&A, with the revised local packet for exact excerpts. The next manageable human batch is **06–10**, with particular attention
to corrected 08; revisit the added background in 05. Later, review corrected 16 and 17 in context.
The required human semantic/consistency pass and private authoring remain under
[the evaluation protocol](QUESTION-SET-AND-EVALUATION.md). Agent review assists that work and does
not substitute for it. Freeze both finalized splits and protected backup receipts before Step 6.

No tuning, generation, database calls, services, training, full-selector work, protected storage or
human-hour inference occurred in this review.
