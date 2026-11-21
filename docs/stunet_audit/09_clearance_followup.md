# Leakage-clearance follow-up — 6 November 2026

**Definite decision for the present evaluation claim: NO-GO. We cannot describe the current PROWL evaluation as leakage-free or its public 901-case benchmark as untouched.** This does not prove that every development case leaked, and it does not disqualify STU-Net-B as an attributed transfer initialization. A positive unseen-patient claim still requires a verified patient/source crosswalk or a separately admitted independent final evaluation.

This follow-up adds evidence to the initial conditional recommendation. The entire original 47-file audit release and its execution manifest are preserved under `audit-release-01` in the external audit evidence directory. No training, scientific cohort changes, protected test image/label reads or author messages occurred during these checks.

## What is now definite

| Question | Answer and evidence |
| --- | --- |
| Is our downloaded checkpoint the same artifact published on the author's model repository? | **Yes.** The author-linked Google Drive download exactly matches the `base_ep4k.model` LFS SHA256 and 466,715,133-byte size at publisher repository revision `a50a9375d52e06c8498387bb222c7ca374125139`. |
| Was the public 901-case cohort previously used in this project? | **Yes, according to explicit retained experiment records.** They document EXP-24 test results, EXP-25 acceptance/rejection on that cohort, and subsequent threshold exploration. It is not an untouched final test for this ongoing project. |
| Are current train/dev aliases and retained original-file hashes separate? | **Yes at that limited level.** All 1,333/75 aliases are distinct; retained CT SHA256 values have zero train/dev collisions and zero training/reference collisions against the 1,203 valid source CTs. This does not exclude transformed images or repeat patients. |
| Is patient independence established? | **No.** All 1,408 registry members still have `unverified_unique` identity assurance and study-as-subject fallback. No verified biological patient crosswalk or exact checkpoint training/selection ledger has been recovered. |
| Can negative exact hashes clear the five Basel candidates? | **No.** One candidate has strong near-duplicate evidence after local visual review; none receives independence clearance. |

## Publisher artifact identity and additional metadata

The pinned [MedIM README](https://github.com/uni-medical/MedIM/blob/2e89e54bc7604f723c454bbbb1cb7e7e5e41cc7e/README.md) links the author's `ziyanhuang/STU-Net` model repository. Its [published LFS pointer](https://huggingface.co/ziyanhuang/STU-Net/raw/a50a9375d52e06c8498387bb222c7ca374125139/base_ep4k.model) states SHA256 `7232a6296d320da1d60debe873a1d3fcad74e9404272db8f7440e30d62c5997a`, exactly matching our original download. We fetched the small pointer and model metadata, **not a second weight download**. This supersedes the initial audit's “no publisher checksum located” finding. It corroborates publisher artifact identity; it is not a signed record of patients, gradient updates or checkpoint selection.

The [model repository's pinned README](https://huggingface.co/ziyanhuang/STU-Net/raw/a50a9375d52e06c8498387bb222c7ca374125139/README.md) declares `license: apache-2.0`. This adds an explicit model-repository license declaration beyond the source-code license. The card otherwise contains no training lineage. It does not independently resolve source-data rights, clinical deployment suitability or scientific independence.

We also inspected the publisher's **1,605-byte `base_ep4k.model.pkl` sidecar**, matching its pinned upstream Git blob (SHA256 `2e6507001004d6c47f48f81572debb90176f75d4eca21c30a5cdaa5df06ef1ff`). The first restricted reader refused its NumPy reconstruction global; that refusal is retained. A separately tested reader maps permitted NumPy arrays to inert, size-checked records and refuses executable globals, object arrays and external references. No unrestricted pickle fallback or upstream trainer execution was used.

The sidecar names `STUNetTrainer_base`, records an initialization fold value of 0, and supplies batch size 2, 128³ patches, 1.5-mm spacing, nonCT/no-mask normalization and **four `[2,2,2]` pools followed by `[1,1,2]`**. It contains no case ledger or patient IDs. Fold 0 does not identify an actual case split without its split file. This adds detail absent from the standalone 583-byte plan and corrects any assumption that the original spatial path was necessarily five isotropic pools. The initial smoke explicitly used five isotropic pools and remains only a tensor/loading feasibility check. Before integration, choose and qualify the actual plan in both matched arms; no frozen training recipe was changed here.

Public STU-Net issue replies describe standard nnU-Net training and target-dataset planning ([pretraining](https://github.com/uni-medical/STU-Net/issues/11#issuecomment-1566367043), [transfer planning](https://github.com/uni-medical/STU-Net/issues/18#issuecomment-1783664796)); they do not provide this binary's case membership. A public [PanTS crosswalk request](https://github.com/MrGiovanni/PanTS/issues/15) was unanswered in the retrieved snapshot. Its existence is not proof that no mapping exists privately. No authoritative crosswalk or source-owner separation attestation was found in this targeted search.

## Historical test-use ledger

The retained `outputs/splits/test.txt`, `test_pos.txt` and `test_neg.txt` contain 901, 151 and 750 aliases respectively, all within official `PanTS_00009001`–`PanTS_00009901`. They share no aliases with the current 1,408-case registry. Only ID text was inspected; no protected image or label was opened.

The actual notebook `docs/experiments.md` records historical EXP-24 lesion Dice 0.474 on that cohort, EXP-25 evaluation on the same frozen 151/750 lists, a rejection on its detection threshold, and threshold exploration. These are **documented historical uses**, not newly reproduced scores or authenticated raw execution records. They are sufficient to refuse an “untouched test” description. Neither a new initialization nor a new project week resets that exposure. See `test_use_ledger.json` for exact source hashes and line locations.

The current train/dev hash review reused the frozen portable cohort and verified reference manifest. It did not reopen 1,333 training CTs, recompute their arrays, or certify current training-file bytes. Zero retained file-hash collisions is a narrow integrity observation, not a patient split audit.

## Strongest image candidate and field-of-view concern

Five geometry-selected candidates received bounded sparse translation review: 1389/s1014, 1823/s0863, 2935/s0560, 6011/s0075 and 6115/s0661. The worker samples at most 48³ numeric voxel positions, avoiding the prior full-array FFT's allocation failure. It uses the original bounded native reader and independent 8-GiB RSS gate; no physical units are assigned. All five completed in **3.577 supervised seconds**, peak owned RSS **969,490,432 bytes**, exit 0/reaped. These are local candidate alignments, not exhaustive registration or patient adjudication.

For **PanTS_00001389 / TotalSegV1:s1014**, sampled tissue correlation reached **0.961799**. Local review of all three generated central planes shows closely matching skull/brain anatomy, supporting a strong near-duplicate concern. The original reference metadata labels s1014 as **train**, institute code H; the PanTS workbook's Basel subsite code I must not be treated as the same code namespace.

The reviewed PanTS views show a **head field of view**, not abdominal structures. This requires a separate eligibility review before claiming a pancreas-specific clinical negative denominator. It is an observation of the displayed anatomy, not a diagnosis or an automatic case exclusion. No labels were reopened, no exclusion was made, and no existing model metrics were recomputed.

PanTS intensities in this volume range from -999 to 999, while the corresponding reference crop spans -1288 to 2411. We tested 15 explicit clipping/rounding hypotheses on the full query at the inspected offset. The best tested clipping `[-999,999]` yielded **93.6027%** of voxels within one numeric intensity unit, but only **51.7942% exact equality**, mean absolute difference **14.182932**, and maximum difference **1314**. **No complete transformed-query SHA matched.** Thus neither a simple clipping rule nor visual similarity supplies an exact patient crosswalk. We retain **SUSPECTED_OVERLAP with strong image evidence**, rather than silently promoting to confirmed identity or claiming the scans differ. The local contact sheet, full residuals and source hashes are retained; no medical images were uploaded or attached to correspondence.

The other four sparse alignments had low or negative fitted correlations under this restricted translation model. That does not prove unrelated patients or rule out other offsets, phases, resampling or transformations. All five classifications and all 75 original members remain intact. The original full-volume/crop-hash results remain true under their stated exact equality criteria.

## What closes the remaining decision

1. **Checkpoint-specific case/selection ledger:** obtain original source case membership, inherited initialization and downstream selection participation. Treat the entire source pool conservatively while this is unavailable, including unusable s0864.
2. **Patient/source crosswalk or private source-owner adjudication:** resolve transformed scans and repeat acquisitions across our train, development and intended final evaluation. Have the owner validate the workbook source fields independently of its reported structured-report alignment issue; do not apply an invented row shift to those fields.
3. **Independently admitted final evaluation:** the [PanTS submission route](https://github.com/MrGiovanni/PanTS#external-out-of-distribution-test-set) offers author-administered proprietary cohorts and a re-annotated RSNA cohort. Availability and patient separation from this checkpoint and our development need explicit confirmation. A different hospital name alone is insufficient. Agree a frozen package and feedback policy before submitting; do not download restricted labels or tune repeatedly against those results.

Two concrete emails to the published STU-Net and PanTS contacts are ready in `10_author_outreach.txt`. **The user directed both drafts to remain local. Author outreach is not authorized; do not send these drafts.** A targeted read-only Gmail search found no existing correspondence with those addresses. No message was sent, no GitHub issue posted and no model submitted.

Until those source-owner facts arrive, the definite answer is **NO to the present leakage-free/unseen-patient claim**, with **conditional scientific usability for a separately approved exploratory transfer study**. Additional negative image searches cannot manufacture the missing patient history. The remaining provenance answer depends on external evidence; it cannot be completed honestly by more local model training.

All **36 synthetic audit tests pass** (1.813 seconds). Original producing pins, source files, splits and checkpoints remain protected. A follow-up evidence manifest records the new public sources, preserved initial release, checks, resources and open requirements. No training or automatic follow-up job was launched, and audit changes remain uncommitted under the supplied outline.
