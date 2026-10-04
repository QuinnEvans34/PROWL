# Purpose-disposition retained-input review

September 28, 2026. **Inputs reviewed; no actual-case purpose issues published.**
This completes the exact-input review after the synthetic purpose helper. The first bounded
publication can use cases 78 and 266 in the existing five-study v2 evidence slice. Case 2
requires a separate evidence/annotation step. This is a review inventory, not a manifest,
cohort, new permission, or an operational disposition package.

## Evidence checked

Only retained repository-local evidence was read; no external source drive or raw CT/mask
was opened. File hashes were compared with retained controls, and both manifest versions
were replayed from their persisted assembly inputs:

| Retained package | Hash checks | Exact replay outputs | Finding |
|---|---:|---:|---|
| manifest-slice-35acf328-ae35-4c32-954c-df2c34034d87 | 13 | 5 | Cases 1/2; zero annotation records |
| manifest-v2-slice-685cfdbd-ae54-4508-be6f-5b9267197bd9 | 25 | 5 | Cases 3/26/31/78/266; ten quarantined annotations |
| voxel-followup-140effff-129c-4ff8-b455-70a2119707a1 | 13 | — | Retained pair audits match receipt |

These are 51 package-file hash comparisons, not 51 unique source images. Coverage evidence
JSON, retained bone PNG and review document for case 78 also match the linked-assessment
pins. Its evidence CT hash matches the selected study. The PNG was hashed, not reinterpreted.
The five-study package retains all twenty existing holds and zero eligibility.

Both proposed candidates are in the pinned 7,200-member approved training partition.
The train-file SHA-256 is in the companion JSON. No validation/test membership was changed.
File/record hashes establish identity and reproducibility, not biological subject uniqueness,
clinical validity, annotation quality, source rights, or spatial units.

## Exact first candidates

| Case | Annotation | Requested purpose | Rule and supporting evidence |
|---|---|---|---|
| 78 | Existing v2 pancreas record | pancreas_present_localizer | PANCREAS_PRESENT_TARGET_EXCLUDED; approved purpose decision, retained coverage review and pair-06 audit |
| 266 | Existing v2 pancreas record | pancreas_present_localizer | PHYSICAL_UNITS_UNRESOLVED; approved purpose decision, unit investigation and pair-09 audit |

The companion JSON pins full study/annotation/snapshot identities, canonical record hashes,
CT/mask identities, existing issue hashes, audit-file hashes, decision/evidence documents and
helper/schema versions. The decision input for both is PURPOSE-ELIGIBILITY-DECISIONS;
case 78's primary reviewed evidence is CASE78-COVERAGE-REVIEW, and case 266's is
UNIT-EVIDENCE-INVESTIGATION, with their linked audit evidence retained.

Case 78's coverage assessment remains provisional, not clinical adjudication. Quinton's
purpose-specific exclusion does not declare it corrupt, disease-free, or qualified for
anatomy-absent robustness. Case 266's retained audit explicitly says unknown CT spatial
units and its study geometry remains null; matching grids do not establish millimeters.

Case 2 is absent from the five-study v2 package. Its older two-study package contains **no
annotation records at all**, so there is no qualified v2 pancreas record to pass to this
helper. Retain the geometry-dependent hold and older evidence; prepare a separate bounded
representation/evidence slice later. Do not silently enlarge the five-study package or
manufacture a v2 record from the absence of annotation evidence.

## Next bounded publication

Use a new diagnostic-package identity/output directory and persisted deterministic inputs.
Preserve both old packages byte-for-byte. Recheck these pins before invoking the helper;
changed bytes require review. Create two new rejection-only purpose issues, preserve all
existing issues and original study membership, and validate the independently pinned
issues/evidence through check_purpose. Do not activate binary mappings or promote uses.

If publishing a complete derived five-study manifest, retain five studies, ten quarantined
annotations and twenty historical issues plus the two new purpose issues (22 total).
Verify references, canonical replay and every output hash before publishing a receipt.
Report purpose-check rejection reasons separately from general quarantine. This remains
an evidence/diagnostic package, not a frozen training cohort or a training authorization.
Case 2 stays outside that first publication and remains blocked.

## Machine-readable inventory

[PURPOSE-DISPOSITION-INPUT-REVIEW-2026-09-28.json](PURPOSE-DISPOSITION-INPUT-REVIEW-2026-09-28.json)

SHA-256: `51c70d3866ab23b355d4aed0f10245f538136fd2640e5195ed98aaba5eb40441`.
Canonical record hashes use the existing manifest canonicalization; file hashes cover exact
file bytes. This JSON is review evidence and intentionally does not create new issue IDs,
issue timestamps, operational eligibility flags, or a new serialization contract.

Native verification in the same session: 120 retrieval tests and 751 full-suite tests pass
(two existing upstream warnings). Retrieval contract corrections are tracked separately in
../retrieval/CODEX-P3-REVIEW-2026-09-28.md and do not change these retained data inputs.
