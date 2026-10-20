# PANORAMA current inventory

**Status:** Planning evidence; not a complete source snapshot  
**Audited:** 2026-09-08  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/03-panorama-integration.md`](../implementation/03-panorama-integration.md)

This file distinguishes what is physically available now from what the approved appendix observed
earlier. It is not permission to train from an unpinned live dataset.

## October20 handoff reconciliation

The missing-archive statements below are historical. The [handoff audit](PANORAMA-HANDOFF-AUDIT-2026-10-20.md)
recovers completed extraction/transfer records and verifies current paths/sizes for4,480 files:
2,238 CTs and2,238 labels with matching study-ID sets. No current-byte rehash or array inspection.
Acquisition is evidenced; mapping/eligibility/duplicate/geometry/mixed-source smoke acceptance still
requires the data owner's handback. W03-01 is open, not blocked on downloading the same data again.

## September 19 acquisition update

The old drive is unavailable and excluded from acquisition/backup assumptions. A fresh public
[publisher inventory](acquisition-2026-09-19.json) records the four versioned Zenodo CT batches
(13715870, 13742336, 11034011, 10999754), their sizes/MD5 values, and label commit
`bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665`. The overnight queue started at 22:02 MDT. Its label ZIP
(91,426,460 bytes; SHA-256 `f6b0399d9a01572779ac62ff0652348913d67913f8373110f133da40e30787d7`)
matches all 2,242 blobs in the pinned Git tree. CT batch 1 is in progress, with batches 2–4 queued;
no complete CT/label source snapshot is declared. See the
[overnight evidence](../operations/OVERNIGHT-ACQUISITION-2026-09-19.md). The prior metadata findings
below remain evidence to reconcile, not
proof of fresh byte identity. Follow the [acquisition queue](../operations/DATA-ACQUISITION-QUEUE.md).

## Files visible at the September 8 audit

| File | Bytes | SHA-256 | Interpretation |
|---|---:|---|---|
| `clinical_information.xlsx` | 114,329 | `2ae925de8067600db62e186a91844dec6555dab2b17cafd33b886b8c99f19ea7` | Valid workbook used for the current metadata audit |
| `panorama_manual_ids.txt` | 6,265 | `2cfde5cb23972e448e0d902a44d0967c186d34379e4e800add32c557fb842c38` | Derived historical list of 482 unique manual-label study IDs; useful evidence, not source authority |
| `panorama_sample_label.nii.gz` | 14 | `d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed` | Invalid: the file contains the literal bytes `404: Not Found`; quarantine and never use |

No PANORAMA CT archive or valid label archive was found in the repository, `Downloads`, or mounted
external volumes during this audit. A prior exploratory script expects a label archive at
`/Volumes/JHU-PanTS/PANORAMA/panorama_labels-main.zip`, but that volume is not currently mounted.

## Workbook structure

Observed columns:

1. `PANORAMA_patient_id`
2. `PANORAMA_study_id`
3. `anonymized_study_date`
4. `patient_age`
5. `patient_sex`
6. `scanner`
7. `label`
8. `level`

| Property | Observed |
|---|---:|
| Rows / columns | 2,238 / 8 |
| Unique study IDs | 2,238 |
| Unique patient IDs | 2,224 |
| Subjects with multiple studies | 11 |
| Studies belonging to repeated subjects | 25 |
| Extra studies beyond one per subject | 14 |
| Maximum studies for one subject | 5 |
| Subjects spanning declared-import and import-clean groups | 0 |

## Source outcome and reference-standard profile

| `level` | PDAC | non-PDAC | Total | Plan 03 disposition |
|---|---:|---:|---:|---|
| `cytology` | 143 | 40 | 183 | Import-clean candidate |
| `histopathology` | 262 | 91 | 353 | Import-clean candidate |
| `pathology` | 124 | 86 | 210 | Import-clean candidate |
| `radiology` | 49 | 1,163 | 1,212 | Import-clean candidate |
| `radiology / 3yFU` | 0 | 6 | 6 | Import-clean candidate |
| `MSD_dataset` | 98 | 96 | 194 | Exclude: declared import represented in PanTS |
| `NIH_dataset` | 0 | 80 | 80 | Exclude: declared import represented in PanTS |
| **Total** | **676** | **1,562** | **2,238** | — |

After declared exclusions:

| Property | Count |
|---|---:|
| Studies | 1,964 |
| Subjects | 1,950 |
| PDAC-positive studies | 578 |
| non-PDAC studies | 1,386 |

`non-PDAC` is a source-level PDAC status, not a generic pancreatic-lesion-negative label. The 1,386
rows therefore remain `pancreatic_lesion=unknown` unless separate evidence is found.

## Annotation-method evidence

The current manual-ID list contains 482 unique IDs, and every ID matches exactly one workbook row.

| Stratum | Count | Current interpretation |
|---|---:|---|
| All manual IDs | 482 | Historical reconstruction of `manual_labels/` membership |
| Declared-import manual PDAC | 97 | Excluded with the MSD import |
| Import-clean manual PDAC | 382 | Approved primary expert lesion pool after pinned-archive reconciliation and QC |
| Import-clean automatic PDAC | 196 | Approved optional machine-label pool after its separate audit |
| Import-clean manual/non-PDAC | 3 | Anomalies requiring mask/repository adjudication |

The three anomalous study IDs are:

- `100598_00001` — histopathology;
- `100667_00001` — histopathology;
- `101632_00001` — radiology.

Directory membership must be re-derived from the pinned label archive. The text list is not allowed
to determine production provenance by itself.

## Missingness and anomalies

Across all 2,238 rows:

| Field | Missing |
|---|---:|
| anonymized study date | 194 |
| age | 274 |
| sex | 274 |
| scanner | 276 |
| patient ID / study ID / label / level | 0 |

Most demographic missingness aligns with the declared imports. Within the import-clean 1,964 rows,
only two scanner entries are missing. One additional scanner entry is the string `0`, which is
retained as an anomaly rather than converted to a manufacturer or silently imputed.

Import-clean scanner values currently summarize to Siemens 938, Toshiba 651, Philips 319, GE 46,
Canon 7, missing 2, and `0` 1. Capitalization/normalization may create a derived manufacturer field,
but the source value remains unchanged.

## Historical evidence requiring revalidation

The approved technical appendix reports that a previously available labels archive contained:

- 482 manual labels and 1,756 automatic labels, exactly one file for each workbook study;
- filenames equal to `PANORAMA_study_id`;
- raw values 0 background, 1 PDAC, 2 veins, 3 arteries, 4 pancreas parenchyma, 5 pancreatic duct,
  and 6 common bile duct;
- a verified example `100002_00001` with shape `512 × 512 × 561` and spacing
  `0.709 × 0.709 × 1.0 mm`.

Those observations are credible project history, but the live labels repository can change. G2
must reproduce them from the exact archive/commit used by the capstone.

## Snapshot gaps before implementation

The storage route is available but not mounted in the current audit environment. The previously
verified source data can be reconnected from the 500 GB drive, and a new 4 TB drive is available as
the intended long-term project store. Copying to the 4 TB drive must preserve immutable source bytes
and produce a new location/inventory record; prior documentation is accepted planning evidence, but
the live files still receive path, capacity, version, and checksum preflight before voxel work.

- Pin the labels repository commit and archive SHA-256.
- Pin every CT batch/release and publisher checksum or full local checksum.
- Record the CC BY-NC 4.0 evidence URI, attribution, and non-commercial restriction.
- Generate sorted inventories for metadata, labels, and images.
- Reconcile all publisher study IDs across the three inventories.
- Confirm storage location/capacity and root aliases under Plan 10.
- Replace the manual-ID derivative with provenance computed from the pinned directory inventory.

Until these gaps close, metadata planning may proceed, but no PANORAMA voxel artifact is eligible for
training and Plan 03 cannot complete G2.
