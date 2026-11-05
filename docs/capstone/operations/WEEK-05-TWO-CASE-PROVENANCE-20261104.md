# Retained provenance review: visually similar cases 6755 and 2889

**Patient relationship remains unresolved. Keep both cases and the original 70-case denominator.** This bounded follow-up examined 17 known metadata/text records, including peer main `b2dad58`, and reused the completed visual review. No scan/mask bytes, new headers, arrays, inference, scoring or GPU work were read or run. The adjacent JSON lists every input's SHA256; no private patient identifiers or medical pixels are published.

| Retained property | PanTS_00006755 | PanTS_00002889 |
| --- | --- | --- |
| Compressed CT bytes | 68,653,910 | 66,786,913 |
| CT SHA256 prefix (full values in JSON) | 71abce399a152 | c0ae6d21be7ef |
| Native dimensions | 512 × 436 × 250 | 512 × 436 × 250 |
| Spacing magnitudes, mm | 0.738281 / 0.738281 / 0.800000 | Same |
| Native x/z direction | Positive / positive | Negative / negative |
| Biological patient independence in frozen request | Unverified | Unverified |

The saved CT hashes and byte lengths differ; the pancreas and lesion file hashes also differ. This excludes byte-for-byte serialized file identity in the retained snapshots. It does **not** establish different underlying anatomy, acquisitions or patients. No fresh file hashing or canonical voxel-content comparison was performed.

Arithmetic on the retained shapes and affines places the positive-axis origins approximately 0 mm apart in x/y and **300.800005 mm apart in z**, after accounting for the x/z flips. This is coordinate arithmetic, not image registration or proof of matching anatomy. Saved lesion component sizes also differ (1563/1952 versus 1997/1602 voxels); annotation differences cannot resolve patient identity.

The retained `source_identity.study_id` is each PanTS case alias. It is not an independently verified patient identifier or DICOM StudyInstanceUID. No actual patient/study/series relationship mapping was found in the reviewed records. This finding is limited to those records; it does not claim the publisher has no such mapping. Different PanTS IDs, archive placement or hashes are insufficient evidence of patient independence.

The November2 restoration sequence places case 6755's verification after starting `PanTSMini_ImageTr_00006001_00007000.tar.gz`. Its saved source path identifies `ImageTr/PanTS_00006755/ct.nii.gz`. The November3 restoration verifies case 2889 against its expected bytes/hash and retained case path, but an explicit archive-member ledger for that case was not established in these reviewed records. No archive is guessed from its numerical ID. Both restorations support continuity with the retained sources, not independence between them. The historical duplicate-scope authority record grants a workflow; it is not a completed adjudication for this pair.

## Consequences for comparisons

Preserve both dispositions, scores, cohort membership and the 70-case denominator. Same-update matched-case descriptive differences can be reported with the existing exposed-development and numerical-exception limitations. Do not describe an ordinary case bootstrap as a verified independent-patient uncertainty interval while patient linkage is unresolved. A patient-cluster bootstrap would require a verified relationship mapping. A prespecified sensitivity analysis grouping this pair could show sensitivity to an assumption, but would neither establish identity nor replace that mapping. No bootstrap, metric recomputation or hypothesis verdict was produced here.

All work used standard-library, single-thread metadata handling. The publication pass took approximately 3.6 seconds; earlier interactive review elapsed time was not instrumented, so compliance with a measured cumulative 10-minute duration is not claimed. The 17-record count is within the 30-record bound. No reusable software was introduced; assertions verified that saved source hashes, dimensions, affines and byte counts agree across the request/cache/source observations. The publication inputs were rehashed, not scan files. Existing producing files remain unchanged.

Sanitized JSON SHA256: `996be9c75ecc8c0dd0574d211cda8f2cd9ce0216774a95d5eba74b0f56b6bb15`.
