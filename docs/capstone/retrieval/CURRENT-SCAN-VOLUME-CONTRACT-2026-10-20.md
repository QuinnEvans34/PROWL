# Current-scan volume development contract — October 20

Quinton explicitly requested connecting current-scan measurements today. This authorizes early
REQ-X01 development before formal core acceptance; it does not waive core acceptance or mark the
measurement extension complete. AI-05 is active in Week 3, ahead of the next wording sweep.

First slice: answer current-scan pancreas or total suspected-lesion **mask volume** questions from
saved prepared prediction files. No model estimates, retraining, reference-mask reads, held-out
assessment, normal-range comparison, diagnosis, head/body/tail size or individual-lesion diameter.
The legacy prepared grid may be cropped/resampled. Report the loaded outline's volume, never
assert whole-organ coverage. Pancreas extent is labels 1+2; suspected lesion is label 2, summed
across components. Zero lesion labels is not absence of disease. Empty pancreas is unavailable.

Before any validation execution, freeze these checks: exact integer label counts; affine determinant
volume within 1e-9 relative error on analytic fixtures; CT/mask affine and legacy spacing agreement
within 1e-4 absolute units; display volumes to two decimals (less than 0.01 stated explicitly).
Reject invalid/singular affines, inconsistent grids, unsupported dimensions/scaling/types/labels,
missing units without a matching explicit prepared spacing_mm declaration, invalid paths, missing
prediction, and live scalar responses without a bound mask. Reject boundary-contact outlines for a
size answer (they may be truncated). Even without boundary contact, full coverage remains unknown.

Read only selected saved CT/prediction assets, capped at 64 MiB each compressed/decompressed and
16 million voxels. Hash decoded NIfTI bytes (HTTP may remove gzip before fetch returns); keep raw arrays and study identifiers local.
Hashes identify inspected files, not proof of model/checkpoint lineage. Legacy units fallback must
be disclosed; it is a manifest declaration, not independently validated source geometry. No rewrite
of original assets. No model calls or literature service dependency for pure volume answers.
Clear pending/completed measurement results when scan or prediction identity changes. General
literature requests retain the existing independent path; no scan metadata is sent to it.

Analytic geometry, transport/decoding, refusal and UI stale-result tests precede a selected existing
prepared-demo walkthrough. That walkthrough verifies wiring and arithmetic, not independent clinical
accuracy or a scientific evaluation result. Full native-source lineage, reviewed development masks,
coverage certification, per-lesion components/diameter and reference eligibility remain open in AI-05/06.
