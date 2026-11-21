# PDAC-TAGS Center D: acquisition and provenance result

**Download integrity passed. All 96 image/mask filename triplets are present. Patient independence remains unverified.** The archive does not supply a standalone original-source, acquisition-date or patient-crosswalk ledger. This completes the authorized download and bounded provenance inspection, but does not admit Center D as an independently verified final evaluation.

This follows the [external cohort screen](11_external_cohort_screen.md). The user explicitly approved **“Center D download and provenance inspection.”** That supersedes the screen's pending-download status for these two parts only. Earlier reports/manifests are preserved as historical snapshots. No other center was downloaded; no clinical image or mask was opened, extracted, decoded or passed through a model.

## Verified acquisition

The files came from the [publisher's public OSF release](https://osf.io/g6rv5/). Each completed part matches its expected size and **both** publisher-reported SHA256 and MD5:

| Part | Bytes | SHA256 |
| --- | ---: | --- |
| `Center_D.zip.001` | 4,697,620,480 | `2cfdba0f95189bedd972c4d6137dc2a32c7d00209b12846b0ea21a28872cc55c` |
| `Center_D.zip.002` | 1,549,510,523 | `0b3a0ef1801a13be4af7f85f7a3c660860ff8441818130176e5cf2735aa408bf` |
| **Total** | **6,247,131,003** | Both parts verified |

Retained originals: `/Volumes/PROWL-Data/PROWL/sources/pdac-tags-center-d-audit-20261106-a01/`. The external drive had approximately 1.97 TB free at the pre-download check; the downloader enforced a 100-GiB free-space floor, two connections, a 1,800-second wall limit and at most two attempts per part. It completed in **828.981 seconds**. One timeout at 4,290,772,992 bytes of the larger part was preserved in the journal, followed by a validated HTTP-range resume. No failed partial was discarded or overwritten, and no second full download was required. The download worker exited and was verified absent.

Checksums establish identity with the retrieved publisher metadata. They do not certify annotation accuracy, biological patient identity, or the full checkpoint's training history.

## Archive inventory and pairing

An inventory-only reader treated the byte-split parts as one seekable ZIP without making another 6.25-GB archive copy. It bounded the central directory before parsing it and rejected unsafe paths, duplicate members, symlinks, encryption and oversized declarations. The central directory is **75,977 bytes**, with **584 members**:

| Member type | Count |
| --- | ---: |
| CT `.nii.gz` filenames | 96 |
| Tumor-mask `.nii.gz` filenames | 96 |
| Pancreas-mask `.nii.gz` filenames | 96 |
| macOS housekeeping files | 292 |
| Directories | 4 |

All 96 case aliases have one filename in each of `images`, `lesion_mask` and `organ_mask`. This is a **filename-level completeness check**, not proof that the images are distinct patients, aligned with their masks, or clinically eligible.

The actual suffixes are **`_image.nii.gz`, `_lesionmask.nii.gz` and `_organmask.nii.gz`**. The last two differ from the wiki examples, which use `_lesion_mask` / `_organ_mask`. A future reader must bind the actual explicit suffix mapping. No source file was renamed and no existing PROWL loader was modified.

Aliases span `D_1`–`D_99`, with numeric gaps at 25, 68 and 74. The count is the publisher-declared 96; without an authoritative expected-case ledger, those gaps are **not evidence of missing patients or unauthorized exclusions**. Do not invent three cases or relabel the archive as a failed 99-case cohort.

The inventory reports a 6,311,831,967-byte expanded-size declaration. This is ZIP member size metadata, not a measurement of uncompressed CT arrays. Individual clinical member CRCs, NIfTI headers/units, voxel values, label classes, geometry and image/mask alignment were **not** checked; doing so would require a separately admitted clinical-content stage.

## Provenance inspection

There are **no standalone README, license, CSV, JSON, source ledger, acquisition-date table or patient-crosswalk members** in this center archive. Its non-image entries are `.DS_Store` and AppleDouble `._*` files.

A bounded follow-up opened only those **292 housekeeping payloads**, totaling **1,198,084 bytes**. It checked their macOS container signatures and recorded entry metadata, hashes and detected attribute names. The detected extended attributes were `com.apple.macl` and `com.apple.quarantine`. These are filesystem/access/download metadata, not a patient/source crosswalk. Their presence does not identify original hospital patients or establish separation from pretraining. No arbitrary clinical text or medical payload was opened, and no file was extracted to disk.

The [public project documentation](https://api.osf.io/v2/wikis/t3dpr/content/) remains the source for the declared one-examination-per-patient cohort and expert annotation protocol. It is not a private source-owner patient reconciliation. Center D's original institutional mapping, exact acquisition identities, repeat-patient separation across datasets, and relationship to all inherited teacher/model exposures remain **unresolved**. This inspection does **not** demonstrate overlap either.

## Decision and next use

| Gate | Result |
| --- | --- |
| Authorized acquisition and publisher part integrity | **PASS** |
| Safe bounded directory inspection | **PASS** |
| 96 complete filename triplets | **PASS** |
| Original source/patient crosswalk recovered | **NO** |
| Patient independence from relevant upstream and PROWL exposures | **UNRESOLVED** |
| Clinical-content/geometry/annotation qualification | **NOT PERFORMED** |
| Model evaluation, transfer training or promotion | **NOT STARTED / NOT AUTHORIZED BY THIS STEP** |

**Do not label Center D leakage-free, unseen-patient or an independently verified final test.** It remains a plausible externally released **exploratory** PDAC benchmark, subject to later technical qualification and an explicit protocol. It is not cleared for the stronger final-evaluation claim. Negative image comparisons alone would not recover the absent patient history, so this result does not justify another bulk scan download or an open-ended duplicate search.

For stronger evidence, use adequate original patient/source records, a source-owner separation attestation, or a different cohort whose documented provenance establishes separation from the relevant models and our previous development. Public records can satisfy this without contacting authors if they are sufficient; none recovered here does so. The user's instruction to keep author drafts local remains in force.

Any future evaluation must keep all-positive PDAC performance separate from negative-patient false alarms and general pancreatic-lesion claims, freeze membership/model/settings before predictions, and describe pretraining and uncertainty accurately. No present score has been calculated. Download access and matching checksums do not resolve that scientific decision.

## Checks and retained evidence

The new directory-only reader passed **12 synthetic tests**, including byte-split/ZIP64 handling, member-open refusal during inventory, path traversal, embedded-NUL paths, symlinks, duplicate paths, truncation and oversized declarations. A test-fixture mocking error in the second test attempt is retained; it was corrected before the final passing run. Existing audit tests were not rerun or relabeled as new evidence.

The first inventory supervisor attempt failed before starting its worker because `jsonschema` was absent from its import path. That directory/failure is retained. A fresh attempt used the already-existing isolated test-dependency path; no package installation or frozen source edit was needed. The successful inventory worker completed in **0.0757 seconds**, observed peak owned RSS **18,825,216 bytes**, exit 0/reaped. The metadata-only follow-up completed in **0.0766 seconds**, observed peak owned RSS **21,938,176 bytes**, exit 0/reaped. These short-run resource observations are not a clinical inference benchmark.

Evidence root: `/Volumes/PROWL-Data/PROWL/artifacts/stunet-audit-20261106/center-d-admission-01/`. `center_d_admission.json` records the result; `center_d_admission_manifest.json` binds code, tests, request, transfer journal, directory inventory, metadata review and resources. Earlier source pins, audit reports, weights and splits remain unchanged. No images were uploaded or author messages sent. Changes remain uncommitted under the adopted audit outline.
