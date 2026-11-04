# Candidate prediction pilot: engineering pass, full-stage budget decision

## Completed

Six frozen verifier-fit cases, no tuning/calibration labels or development/test
reads. No optimization, scientific model selection, MLflow RUNNING entry or new
dashboard training card. Original generator and all3351producingpins unchanged.
36CPU tests pass12.77s; earlier23tests pass44.39s. New modules are additive:
verifier_candidate_inputs_v1, verifier_candidate_export_v1 and
verifier_candidate_provenance_v1. Original optimizer provider remains unchanged.

Evidence E:/PROWL/readiness/verifier-candidate-pilot-20261026-a01.
RequestSHA 6c3100911bc1d6a021a2260011d2ddc662fcd7d9a590f9acc5c832ba086e1436.
ResultSHA 4d8cdc3767760e647cb19ffb7074fcf83efdba67a8e30f0b4776b2664e121a80.
Request pins frozen; do not edit or rerun. Ownedexec77725 exited0/reaped.
395.328supervised seconds;2,349,985,792BpeakownedRSS;1,042,284,544BpeakGPUreserved.
Six cases,202tiles twice (export and independent original-predictor comparison).
All hard predictions EXACT, probability archive roundtrips EXACT, zero gaps,
zero annotated voxels outside region; provided-pancreas geometry exactly matches
existing admission metadata. No repeat duplicate audit or patient exclusions.
Six PNGs actually reviewed; factual visual-review.json binds result and each image.
Visual pass refers to engineering, not segmentation quality. Preview aspect is
voxel-based; anisotropic planes are not physical-aspect diagnostic images.

## What the pilot shows, without treating six selected patients as a benchmark

23predicted components:5overlap an annotation,18do not. Four positive patients all
have some overlap, but only4of5annotated components are detected. The medium-lesion
case misses one component; the large-lesion case severely under-outlines despite
complete input coverage. Both negative cases have alarms. Tiny annotation remains
visible and has overlap. Candidate counts are not independent patient samples.

These findings motivate false-positive verification but do not prove it will
work, increase Dice, or retain small lesions. A component gate cannot recover the
missed component or fill missing boundaries. H0 remains NOT TESTED. Preserve all
cases; no lesion-driven crop changes, score-threshold tuning or generator selection.

## Full-stage measured resource projection — NOT approved or dispatched

| Role | Patients | Tiles | Raw prediction bytes |
|---|---:|---:|---:|
| Verifier fit |266|9,970|14,264,866,665|
| Verifier tune |67|2,712|4,298,138,710|
| Calibration |200|7,205|11,274,601,845|

Total533patients/19,887tiles/29,837,607,220raw bytes. These are codes plus float32
lesion probabilities, not new CT copies. Pilot archives300,345,224B; lossless
compression ratios0.7195–0.7234 imply21.47–21.58GB for full533. This range is a
projection from six cases, not a guaranteed bound; budget raw size plus overhead.

Existingcache22,957,418,839B plus projectedcompressed outputs exceeds32GiB.
Rawworstcase pluscache52,795,026,059B; existingbackups4,779,431,301B plusrawoutputs
34,617,038,521B exceeds current27,917,287,424Bbackup cap. Available space at review:
C198.80GiB/E716.74GiB. No files deleted and no budget silently increased.

Conservative projection using the slowest observed per-tile total is12.74hours;
pilot totals include TWO forward passes plus labels/plots, whereas qualified full
export would need one. A tighter single-pass duration is not yet measured.

Recommended explicit next-stage limits:16hours wall,12GiBcombinedRSS,6GiBGPU,
64GiBcombined existingcache+prediction storage onE:,40GiBcombined independent
backups onC:,100GiBminimum free onboth drives,exclusiveGPU/AC, no retry/resume.
This is inference, NOT another training run. Preserve/reuse the six verified
archives rather than recompute them; role-aware fullstage supervision and backup
receipts still need implementation/qualification before dispatch.

## Remaining before verifier scientific training

1. Obtain explicit full-stage resource authority; qualify full-export supervisor
   with failure/duplicate/backup/storage checks, freeze its receipt, then export
   remaining527patients without reading tune/calibration lesion labels.
2. Bind complete533archive and independent backups. Use fit-only candidate/lesion
   size inventory (including <1mL truth-component sidecars) to freeze representation
   and patient-balanced fitting; three-slice pilot images do not replace this.
3. Implement and qualify verifier training and cold restore. Keep67tune for
   checkpoint selection,200calibration for the later locked sensitivity-constrained
   threshold. No calibration-driven architecture iteration.
4. Final readiness review and explicit scientific training launch approval.

No claim of next-training readiness yet. Resource approval is the current stopping
point, not a dataset-quality failure. Original coverage evidence and pilot remain
valid; no need to rerun them after approval.
