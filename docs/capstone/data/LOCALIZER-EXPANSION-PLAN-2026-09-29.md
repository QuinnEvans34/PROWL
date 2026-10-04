# Next localizer cohorts — bounded selection and qualification sequence

D-280 authorizes progression. This document defines candidate selection before its execution;
selection grants no new target permission and does not alter the existing two-case cohort.

First candidate budget: **16 training studies, including existing cases 3/26, and 12 development
validation studies**. Use original protected roles, not the historical manifest's split column.
The retained manifest SHA is `16bfb945a7cdd8f8296e5712f7e71fb71ad7936cd5fe4eb7bb1affaebbc31554`;
its phase and spacing columns describe diversity only, never independently qualify geometry.
The source metadata inventory receipt is
`201342b56dd420783136a25c6faf278a224b68f904b1b56dd39278e458c1131b`.

Strata are normalized recorded contrast phase × recorded third-axis spacing (<=2 mm, >2–5 mm,
>5 mm, missing/invalid). Missing metadata stays in the candidate pool. Deterministic round-robin
visits rare strata first, then lexical stratum order; within strata rank by SHA-256 of policy ID,
seed `prowl-sept29-v1`, and study ID. Retain the existing smoke members first. Report any unrepresented
strata and intentional oversampling; this small sample is not representative prevalence estimation.
No model score, tumor field, report content, target volume or annotation cleanliness is used.

For each selected study, bind the current CT/pancreas inventory entries and archive lineage. Preserve
held candidates; no silent replacement to improve results. Every new CT/target needs bounded full
content/hash/geometry/encoding and alignment assessment before execution. Unknown units, ambiguous
coverage or provenance remain explicit holds. Difficulty alone does not justify a hold. Record
study-as-subject fallback and duplicate-assurance limits; check exact CT duplicates across selected
train/validation before publication. No publisher-test payload is opened.

## Consumer work that must precede publication

The current qualification policy requires `training_target`, and executable cohort v2 requires
train ancestry. The current registry/loader binds exactly two cases and its reviewed S3 transition
history. Do not relax or relabel those objects in place. Add a versioned validation-reference
qualification purpose with separate evidence/use checks, immutable role-specific cohort records,
and loader entry points that cannot feed validation references to an optimizer. Preserve old guards.
Tests must reject role substitution, training requests against validation cohorts, missing/changed
qualification, incomplete members, stale manifest pins and cross-role duplicates. Freeze exact
qualified memberships only after their evidence passes; candidate IDs are not runnable descriptors.

Development validation may guide later policy/model choices; it is not an untouched final test.
Report coverage and failures for every frozen validation member; never remove a difficult validation
case after seeing predictions. Exact final Stage 2 containment/spacing and lesion-reference permission
remain separate gates. The provisional 10 mm region check does not select the production ROI policy.

## Candidate budget revision before raw reads

The initial 16/8 candidate package `b183d9fa98be1c9ca0115cc4ffd22789488d3a433c6efb7a1c942af719a66f41`
is preserved. Its validation selection omitted all three common thin-slice phase strata because
the rare-first round-robin exhausted eight slots. Increase only the validation candidate budget to
12 and publish a superseding selection, before looking at source voxels or model results. This
addresses descriptive coverage, not annotation quality or measured model performance.
