# TotalSegmentator / PanTS overlap audit

> Initial audit snapshot. Read [the later clearance follow-up](09_clearance_followup.md) for newly verified publisher checksums, historical test-use evidence, sidecar plans and candidate-image findings. The initial release is preserved.

**Completed bounded audit, with declared limitations.** All 75 permitted development scans were compared against 1,203 valid original-reference CTs. One corrupt reference remains blocked. No exact image identity was confirmed, and no patient-independence clearance is issued.

## Scope and primary evidence

The permitted PROWL evaluation scope is all **75 development registry cases**, including the five outside the historical 70-case KD scoring subset. Every CT was available and fingerprinted. No training image, protected PROWL test image, reference mask or model prediction was used in this duplicate search. The 1,333 training aliases were examined at the retained source-metadata level only. Planned external evaluation and the protected public 901-case benchmark have **not** been image-audited here and receive no independence clearance.

Primary sources: original [TotalSegmentator v1 record](https://zenodo.org/records/6802614), its [record API](https://zenodo.org/api/records/6802614), the pinned [STU-Net release](https://github.com/uni-medical/STU-Net/tree/0652eaf5cafda6bc269942238c3695994f2dc4f0), [PanTS repository](https://github.com/MrGiovanni/PanTS), [PanTS paper](https://arxiv.org/html/2507.01291v1), and the actual locally acquired PanTS metadata workbook. Source names alone do not establish different patients.

## Source-level findings

| Comparison | Evidence tier | Interpretation |
| --- | --- | --- |
| TotalSegmentator v1 / Basel | Confirmed source institution | Original publisher record attributes dataset creation to University Hospital Basel; clinical CTs include varying pathologies and acquisitions |
| PROWL PanTS / Basel | Confirmed source institution | Actual workbook lists Basel for 91 train and five development aliases |
| Those five aliases / original v1 images | Image search completed; identity unresolved | No exact file/full-array/candidate-crop identity confirmed; shared hospital and approximate similarity do not identify a patient or exact checkpoint membership |
| Other PROWL source groups / original v1 | Unknown at patient level | Different source text, countries or dataset names are not patient-independent crosswalks |
| PanTS / Universal pretraining families | Confirmed source-family overlap in earlier research | MSD pancreas / Pancreas-CT reuse is separately documented; all four Universal screen cases list MSK, without an exact original-ID match |
| STU-Net-family downstream benchmarks / PanTS source families | Possible evaluation/selection exposure | Published direct inference includes MSD Pancreas; this does not establish extra gradient training or exact released-binary case membership |
| Independent final evaluation | Not established in this audit | Requires an authorized crosswalk/attestation or independently admitted external assessment |

The five Basel development aliases are **1389, 1823, 2935, 6011, 6115** (full pseudonyms in the CSV). Retained cohort reference states identify three as annotation-positive and two as reference-empty. This is not a clinical diagnosis. The metadata gives site codes I/I/B/I/C but no verified original TotalSegmentator case ID, study-series UID or biological patient identifier. Original PanTS pseudonyms and fallback subject IDs cannot provide that missing link.

The full `source_provenance.csv` contains 1,408 permitted source-field records, pinned to workbook SHA256 `4bcbf14a31b1ca9441af051a104702e7a832391f47d3af5f493048ec813283e3`. Its field-extraction boundaries and raw XML traversal limitation are described in the inventory. No original dataset crosswalk is invented from site text. Reuse involving PROWL training-role cases alone is not evaluation leakage; the concern for unseen-patient claims is exposure involving development/final-evaluation patients or studies. No paper located in the targeted primary-source search establishes exhaustive PanTS/TotalSegmentator patient disjointness; this search is not proof that no unpublished overlap audit exists.

## Original reference release and split uncertainty

Use only original v1 DOI `10.5281/zenodo.6802614`, expected **28,404,091,806 bytes**, publisher MD5 `f0fbb3f91d9d99f2169863545f577b30`. Do not substitute the 1,228-case v2 release. The small original archive directory contains 1,204 CT members (27,732,395,487 compressed-NIfTI bytes; largest 100,092,283 bytes). The metadata member's length/CRC verified by a bounded range read; the full archive now matches the published MD5 and passed a second whole-file on-disk MD5/SHA256 check.

That member lists **1,082 train / 57 val / 65 test**. The STU-Net paper instead reports 1,081/57/65. Archive partition labels support a conservative reference-pool analysis but are not a checkpoint-bound gradient/selection ledger. A match to the full pool must retain the publisher partition and distinguish image reuse, possible gradient exposure and possible selection exposure. The original TotalSegmentator held-out partition is reference provenance for this audit, not permission to open PROWL's protected benchmark.

## Source-member integrity failure and bounded continuation

The checksum-matching original archive contains a CT member that fails ZIP CRC: `Totalsegmentator_dataset/s0864/ct.nii.gz`, expected `08acde52`, independently observed `cca32844`. Python's ZIP reader stopped extraction after 727 completed members; `/usr/bin/unzip -t` confirmed the same failure. Original resources: 853.123 supervised seconds, 208,011,264-byte peak owned RSS, exit 1, workers reaped. The partial CT is preserved and **unusable**. It is not a fingerprint input or an admitted substitute for a valid scan.

A separate continuation rechecked the whole original archive, verified the 727 retained successes by size/CRC/SHA, and extracted 476 additional valid CT members without repairing or accepting CRC failures. It completed in 492.725 supervised seconds, peak owned RSS 383,631,360 bytes, exit 0/reaped. The original 3,600-second extraction budget is preserved: 853.123 seconds plus a conservative 120-second independent-diagnostic charge plus 492.725 continuation seconds. Failed members remain explicit blockers in the 1,204-member denominator. No PROWL case or scoring cohort changed, and no v2 replacement was used.

`s0864` is listed as publisher training data. One inaccessible training member would yield 1,081 accessible train images, matching the STU-Net paper's reported count. This is an **unverified explanatory hypothesis**, not proof that the released checkpoint excluded that case. Ask the authors for the exact ledger and a valid original-source artifact if available.

The final acquisition attempt took 4,385.025 seconds including part assembly and checksum work. Its 3,600-second elapsed checks covered network ranges, not the subsequent assembly loop; this helper is not qualified as a 3,600-second end-to-end watchdog. The actual clinical-image audit stages use independent process supervision. See `archive_manifest.json` and the retained acquisition timing note.

## Reproducible method and safeguards

1. Pin cohort membership, CT source SHA256 values, source code and explicit image-read request. Use a fresh evidence directory and the existing independent process guardian. No source/image writes.
2. Compare reliable IDs only within a verified original collection/release namespace. No such PanTS-to-v1 ID crosswalk currently exists.
3. Hash original files. For bounded native arrays, orient to RAS and hash **all exact scaled float32 values plus canonical shape**. Hash equality is a same-image observation, not a recovered patient identity. Geometry is stored separately.
4. Derive a bounded overview (at most roughly 96 voxels per axis), robust intensity clipping/body extent, full/0.75/0.5-scale patches, and 12³ normalized appearance vectors. Build one approximate projection index; rerank a bounded candidate set with full patch-vector correlation. Exact file/voxel matches bypass approximate candidate retrieval.
5. Cache fingerprints and source identities. Retrieve five ranked candidates per query; retain classification as unresolved until evidence is adjudicated. An approximate score is **not** a calibrated match probability or patient identifier.
6. Keep units explicit. Seven development CTs declare unknown spatial units; their appearance-only mode assigns no millimetres and performs no physical registration. It cannot qualify clinical/training geometry.

References above the 128-million-voxel native allocation limit use bounded proxy slicing to create an appearance overview without allocating the full native array. They retain full original-file SHA256 but have **no full native voxel hash**, and are counted separately. Invalid/unsupported files must be reported as failures, not silently omitted from the reference coverage denominator. Exact-file joins can still cover an allocation-refused reference if its source bytes have been verified. Resampling, phases, severe/disjoint crops, nonlinear reconstructions or coarse-index misses can evade appearance retrieval. Negative search results cannot issue `CLEAR` without adequate independent provenance.

Synthetic tests cover orientation changes, resampling, intensity changes, crops, shifted padding, an unrelated control, hash/role/source/output guards and archive traversal/symlink/count/size guards. The final 28 tests passed in 1.276 seconds, including exact complete-query crop proofs, transformed-crop translation ranking, checks that a proxy-only overview is not mislabeled as native voxel equality, and that a corrupt ZIP member never returns an admitted digest. These validate fixtures and guard behavior; they do not measure clinical duplicate-detection sensitivity/specificity. Actual development fingerprinting completed 75/75 in 53.901 supervised seconds, peak owned RSS 5,983,633,408 bytes, workers reaped. No patient-model forward or optimizer update occurred.

## Measured results and candidate adjudication

| Check | Completed scope | Finding |
| --- | --- | --- |
| Source file SHA / full RAS scaled-float32 array hash | 75 development queries versus 1,203 valid CT references | Zero identities found; all references received full native hashes, no proxy-only references and no fingerprint failures |
| Approximate multiscale candidate retrieval | All 75 queries; five ranked candidates each | Candidates retained for review; scores are uncalibrated and never confirm identity |
| Same-grid, contained-shape candidate screen | All 75 cached query geometries | Six candidate pairs involving five Basel queries selected for exact crop checks |
| Exact complete-query crop SHA | All six selected pairs | Zero confirmed crops; no intensity tolerance or relaxed identity threshold |
| Within-development file / native-array hashes | All 75 cached fingerprints | Zero duplicate groups; repeat acquisitions from the same patient remain unresolved |
| Optional descriptive translation/intensity diagnostic | One completed pair; next pair blocked by its allocation limit | Partial evidence only, preserved failure; no identity or independence verdict |

Reference fingerprinting/comparison took **570.897 supervised seconds**, peak owned RSS **6,663,438,336 bytes**, exit 0/reaped. Candidate exact-crop supervision took **3.828 seconds**, peak **925,990,912 bytes**, exit 0/reaped. Both remain within the original comparison budget. The parent pipeline rechecked all 75 source-file hashes after comparison. The permitted 75-case registry membership is unchanged.

The six exact-crop pairs were 1389/s1014, 1823/s0863, 1823/s1355, 2935/s0560, 6011/s0075 and 6115/s0661. Full names, publisher partitions, ranked appearance candidates and case actions are retained in `overlap_results.csv`. Geometry suggested candidate offsets only; the proof criterion required all query voxels to equal a reference subvolume. Unknown units were never assigned millimetres. Different intensity scaling, interpolation, non-integer shifts, other phases or other crops may still evade this exact criterion.

The optional translation diagnostic independently rechecked admitted source/hash identities and searched contained translations by normalized intensity correlation. For 1389/s1014 it found whole-query correlation 0.981300, body-range correlation 0.927668, mean absolute intensity difference 35.141446 and fitted residual RMSE 115.183579. These are descriptive numeric intensities, not a validated same-patient criterion or calibrated probability. The next pair exceeded the diagnostic's 16-million-voxel allocation cap. The guardian stopped the worker (1.401 seconds, 1,555,578,880-byte peak owned RSS, exit 1/reaped); partial results remain under `translation-review-01/progress.json`. No bound was relaxed and no automatic retry was run. This optional diagnostic is incomplete and cannot be reported as six negative registrations or six completed near-duplicate adjudications.

Final classification: **5 SUSPECTED_OVERLAP, 70 UNRESOLVED, 0 CONFIRMED_OVERLAP, 0 CLEAR**. The five suspected classifications reflect institution and candidate evidence, not confirmed leakage. No approximate candidate has been cleared as unrelated. No claim of complete image disjointness, patient independence or exact binary training exclusion is supported. The original initial CSV/summary are preserved under `initial-published-overlap-01`; the final summary binds additional candidate evidence and the final CSV SHA.

## Classification policy

- `CONFIRMED_OVERLAP`: verified same image/study/patient against the stated reference scope. Keep exact checkpoint training/selection membership separate if unverified.
- `SUSPECTED_OVERLAP`: institution/appearance or other evidence warrants adjudication but does not confirm identity.
- `UNRESOLVED`: insufficient evidence; includes negative image searches without patient provenance.
- `CLEAR`: adequate independence evidence for a specifically stated standard. No current case receives this from a similarity score or absence of a match.

Keep every original case and attempt. Do not repair a suspect split silently or claim patient independence after dropping only exact image duplicates. The proposed paired experiment can remain useful as explicitly exposed/uncertain-development research, with a separately established final evaluation.
