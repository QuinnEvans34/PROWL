# Saved native prediction review and Mac adapter contract

CPU-only review of all eight retained four-case predictions. No inference or
training rerun, no source edits, no Mac KD interruption. The original probability
comparison remains FAILED/UNQUALIFIED; its admission exception remains four-case-only.

Evidence: E:/PROWL/readiness/week05-native-review-20261103-a01, independent copy
C:/Users/quinn/PROWL-Backups/week05-native-review-20261103-a01.
Four synthetic orientation/slice/component/display tests passed8.07s. Real review
completed147.125s/1,321,943,040B peak owned RSS, exit0/reaped, within600s/12GiB/1GiB
limits. All prior four-case files were compared against independent backups before
rendering. All six PNGs were actually viewed; visual-review.json binds their hashes
and factual observations. This is representative display inspection, not exhaustive
clinical review or annotation adjudication.

## Review selection and findings

Both arms use identical CT window[-100,250], physical aspect ratio and native planes
after lossless closest-RAS permutation/flips. Shear/obliquity is rejected rather than
silently deobliqued. Each selected component chooses maximum-area slice per axis;
smallest index breaks ties. Every plane includes RAS world coordinates and direction
labels. Yellow=reference lesion, magenta=prediction, green=overlap, blue=reference
pancreas outline. Every image binds CT/reference/prediction/result/score hashes,
case, model hashes, arm and deterministic slice indices in review-manifest.json.

| Target | Native component bounds, half-open XYZ | Volume mL | Observation on representative views |
| --- | --- | ---: | --- |
|4681 missed reference component1|[221,231)x[194,201)x[109,124)|0.205550|Circled yellow annotation remains distinct from predictions in both arms.|
|6755 missed reference component1|[243,255)x[257,276)x[29,44)|0.681542|Selected yellow annotation is unoverlapped in both arms; predictions occur elsewhere.|
|909 largest autonomous FP, component4|[279,310)x[96,135)x[135,182)|10.030000|Magenta target lies away from blue pancreas outline in coronal/sagittal views; absent there in provided-region row.|
|909 largest provided-region FP, component2|[224,234)x[194,204)x[311,328)|0.711000|A smaller target remains near the blue outline in both displayed arms.|
|2028 largest autonomous FP, component1|[87,104)x[169,190)x[1,11)|2.834794|Magenta prediction away from blue outline persists across arms.|
|2028 largest provided-region FP, component1|[88,124)x[169,204)x[0,15)|12.223709|Larger displayed region; component touches acquired-volume boundary.|

These are connected reference annotations and zero-overlap predicted components,
not clinically confirmed lesion counts. All other component rows remain in original
scores; selecting representative targets does not remove them from denominators.

## Exact physical executor contracts for the adapter

WEEK-05-PHYSICAL-RECORD-SCHEMAS-20261103.json contains observed JSON Schemas for
each arm's result, evidence and score, validated against ALL eight retained records.
These describe actual keys/types including nullable/empty variants; they do not
rename or fabricate a producer version. Original request/result bytes must remain
unchanged inside the viewer package.

Result top-level keys are exactly:status,case_id,arm,request_sha256,optimizer_updates,
source_shape,source_affine,units,evidence,reference_inputs_used,seconds,
peak_gpu_reserved,artifacts. Status=COMPLETED; arm=autonomous or provided_region;
units=mm; optimizer_updates=0. artifacts maps file basenames to SHA256 STRINGS,
not objects with bytes/sha256. It records progress.jsonl,prediction.nii.gz,
localizer.nii.gz,region-probabilities.npy. input-access.json and result.json are
written later and are not self-listed; transfer-manifest.json binds them separately.

Autonomous evidence.component=predicted-physical-region-v1. Geometry is NOT the old
autonomous-cascade-v1 resized-crop contract. evidence.geometry is the closest-RAS
native ROI geometry; parent_geometry is full acquired grid after lossless orientation;
region_low/high are half-open parent-RAS indices. result.source_shape/source_affine
and the exported NIfTI identify the ORIGINAL native grid. reconstruction.physical_grid
describes internal integer-subdivision sampling; it is NOT the exported NIfTI grid.
reconstruction.output_decision=native_center_probability_blend_then_argmax.
Class0=background,1=pancreas parenchyma,2=lesion. Autonomous evidence includes
localizer_transform,localizer_policy=all_support,probability_representation and
probability_outside_region. Provided-region evidence instead includes
region_origin=provided_pancreas_reference and reference_inputs_used=true; do not
credit it as autonomous. Exact remaining nested keys are in the observed schemas.

Bind result.request_sha256 to raw request.json SHA; find exactly one matching
request.cases[].case_id. Bind CT hash to identity.source_sha256.ct, header/native
shape and affine, model hashes to request.models and prediction bytes to
result.artifacts['prediction.nii.gz']. Do not dereference Windows source paths on
Mac. The transfer supplies portable filenames; original request provenance remains
unmodified. Proposed physical-prediction-view-v1 may store original request.json
bytes as evidence.json, but must preserve the original result and its truthful
physical-executor identity. A saved mask volume is descriptive, not normality.

## Verified initial transfer packet

Only2028 fits the requested32M voxel importer:12,784,277 voxels.4681 has40,327,168,
909 has58,568,704 and6755 has55,808,000; those are not silently downsampled.
Archive: E:/PROWL/readiness/week05-native-review-20261103-a01/review-2028-autonomous.tar.
Bytes15,001,600; SHA256
35d0e97d35ea0266facceb29f243510f417b810c75fa6c0d0c1757e3c5642126.
Six regular root-relative members including transfer-manifest.json; no directory or
link members. Manifest schema prowl-review-transfer-v1 enumerates all other files
exactly with size/SHA. Readback verified; below128members/512MiBunpacked/256MiBarchive.

| Member | Bytes | SHA256 |
| --- | ---: | --- |
|request.json|66120|f1d74994d3085831bc21a7693d88ca24723ad79096ca7afc7eca17fac080cefd|
|result.json|10080|b3419651e536ecc48cd3fb31d5916d3927fb90e9f2b1b9ce1fde0cc87a9c24c8|
|prediction.nii.gz|64719|d5781b375b4db5ff29a0c64e1349d85377fddecdaf143702b065c233e1588bc1|
|input-access.json|146|eeae0ed0fc31bb0591d1ea000f3a3811a0f0fa5b17c5e9f8b76c8d9b84cd7b92|
|ct.nii.gz|14838645|bc75f19627b1529629538aaa392075867ecaa282c9b9fa1dcef406a390d07160|

Scores, overlays, references and full continuous probabilities are deliberately
separate from this minimal requested viewer packet. Referenced original artifact
hashes remain in result.json even when an artifact is not needed by this packet.
Private Wormhole sender owned9509 is bounded3600s/1GiB; receiver code is recorded
only in the local chat/sender.log, not Git. Imaging payloads remain outside Git.
