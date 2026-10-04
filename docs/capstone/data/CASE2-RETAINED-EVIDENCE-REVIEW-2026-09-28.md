# Case 2 retained-evidence review

September 28, 2026. Completed the requested next evidence review before the project regroup.
**Decision unchanged: hold geometry-dependent training use.** No new annotation, disposition,
cohort or source measurement was published. No software/schema changes were needed for this review.

## What was verified

The prior two-study manifest's independently pinned verification file matched. All 13 listed
package-file hashes passed, and its five canonical manifest outputs replayed exactly. All four
pilot report hashes matched the retained pilot receipt. The receipt hash is recorded now, not
claimed as a previously independently pinned control. Case 2's report CT identity matches its
pinned study record; the mask identities appear in the pinned selected-file inventory. The study
is in the exact approved 7,200-member training list.

For both case-2 pairs, audit completion, finite voxel counts, shapes, value-count totals,
foreground summaries and receipt summaries agree. CT and masks all have unknown spatial units,
null physical geometry, and no approved unit interpretation. Grid agreement is native numeric
agreement, not verified millimeters.

| Mask | Shape | Semantic values | Foreground | Physical volume |
|---|---|---|---:|---|
| Pancreas | 275 × 198 × 180 | 0 and 1 | 25,386 voxels | Unknown |
| Lesion | 275 × 198 × 180 | 0 only | 0 voxels | Unknown |

The empty lesion is an annotation observation, not a clinical negative conclusion.
The companion JSON records exact report/source/record hashes and the newly recorded receipt pin.
JSON SHA-256: `2716836b20e6d5e1b335cdccc9b585bb5efaf46330dda3dea512261fe72d8911`.

## Why no annotation record exists, and what would create one

The older manifest deliberately has zero annotations because v1 could not represent unknown
encoding without inventing mapping facts. The later v2 contract can retain original measured
values with null mapping, unknown provenance, empty allowed uses and quarantine.

However, the current link_audits adapter accepts the later follow-up package format: selection.json,
pair-NN.json, source_hashes and followup_source aliases. The pilot has named case/structure reports
and pants_slice references. Feeding it directly to that adapter is unsupported. Do not rename
historical evidence, invent missing receipt fields or rewrite aliases to bypass this distinction.

A bounded future adapter can validate the pilot's own receipt and exact prior file references,
produce linked assessments, then use quarantined_annotation to create a NEW v2 package. It needs
synthetic regressions for wrong study/mask, modified receipt/report/source links, incomplete audits
and unit preservation. This is a format bridge, not a need to reread the raw scans merely to recover
already recorded value counts. Source-protocol/allowed-use qualification remains separate.

## Training-priority recommendation

Do not put that adapter on the immediate first-smoke critical path: case 2 remains untrainable
under the current unit evidence even after serialization. Preserve its hold and this review;
return when new evidence or a specific experiment needs it. Prefer qualifying suitable train-role
candidates and implementing the frozen-cohort consumer. This recommends work ordering, not an
eligibility exception or approval to omit cases from final evaluation silently.

No external drive, raw CT/mask, held-out image, network, or existing package was modified/read beyond
retained repository evidence. No test suite rerun was necessary for this documentation-only pass;
latest data suite remains 631 passes from the preceding publication task.
