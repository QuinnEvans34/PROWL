# STU-Net-B audit decision — 6 November 2026

> Initial audit snapshot. Read [the later clearance follow-up](09_clearance_followup.md) for newly verified publisher checksums, historical test-use evidence, sidecar plans and candidate-image findings. The initial release is preserved.

**CONDITIONAL GO for preparing a controlled transfer-learning study. No clearance for a leakage-free or unseen-patient performance claim, and no training launched by this audit.**

The original checkpoint is a credible, technically viable initialization for learning pancreatic-lesion segmentation. We should not reject it merely because its anatomical training task includes the pancreas. We also cannot claim it has never encountered our evaluation patients. The current development set is repeatedly used, biological patient grouping is unverified, and original checkpoint training/selection membership is incomplete.

## What the evidence supports

The audited checkpoint is the authors' original **STU-Net-B**, a roughly 58-million-parameter convolutional model released as TotalSegmentator-pretrained, not the different Universal-Swin model previously screened on four PROWL cases. Its source affiliations are Shanghai Jiao Tong University and Shanghai AI Laboratory. The [pinned source](https://github.com/uni-medical/STU-Net/tree/0652eaf5cafda6bc269942238c3695994f2dc4f0), author-linked download, epoch 4000, tensor dimensions and parameter count agree. No downstream pancreatic-tumor head was found. The [original source dataset](https://zenodo.org/records/6802614) provides 104 anatomical classes, including pancreas; anatomical pretraining can legitimately initialize a new lesion task.

All **58,157,984 intended body parameters** loaded exactly. The five original heads were discarded, ten fresh three-class head tensors remained unchanged, and a supervised CPU synthetic forward/backward passed with finite gradients. This demonstrates transfer feasibility, not patient accuracy. **There is no STU-Net-B PROWL Dice result yet.** The earlier approximately 0.71 screen was Universal-Swin and must not be attributed to this model.

The approved original 28.4-GB TotalSegmentator v1 archive matches its publisher MD5. We compared all **75 permitted development scans** against **1,203 valid original reference CTs**, retaining **one corrupt reference member** as a blocker in the 1,204-case denominator. No original-file or complete orientation-normalized voxel-array identity was found. Candidate checks and their limits are in [the overlap report](04_dataset_overlap_report.md) and [per-case table](overlap_results.csv). None of these negative checks proves patient independence or exhaustive absence of transformed duplicates.

Five development aliases and 91 training aliases list Basel in the actual PanTS workbook. The five development cases remain **SUSPECTED_OVERLAP**; the other 70 are **UNRESOLVED**. No case is cleared. A shared institution is not confirmed image or patient identity. No reliable PanTS-to-TotalSegmentator original patient/study crosswalk is available. The other PROWL training scans were not image-compared, and no protected PROWL test images or labels were read.

## What remains uncertain

| Question | Finding |
| --- | --- |
| Can we credibly say this model never encountered our evaluation CTs or patients? | **No — NOT VERIFIED.** Negative file/array checks and different aliases are insufficient. |
| Can it be used for a properly described transfer-learning experiment? | **Yes, conditionally:** matched controls, explicit exposure limits, qualified preprocessing/device/recovery, and prospective approval. |
| Exactly which source cases trained or selected this binary? | **Not verified.** Archive metadata says 1,082/57/65; the paper says 1,081/57/65. Corrupt training member s0864 could explain the difference, but this is only a hypothesis. |
| Is the download independently authenticated? | Author-linked origin and a local SHA256 are recorded. No publisher checkpoint checksum/signature was located. |
| Are the evaluation patients independent of each other? | **Not verified.** Study-as-subject fallback is not biological patient grouping. |
| Is the 901-case public benchmark an untouched final test? | Not established by this audit. A historical usage ledger and separate exposure assessment are required. |
| Does TotalSegmentator-only pretraining exclude all other selection exposure? | No. The STU-Net paper also evaluates public downstream benchmarks. Exact released-binary participation/selection history remains unknown. |
| Are licensing and redistribution fully cleared? | Source code is Apache-2.0 and the original data record identifies CC BY 4.0; no separate checkpoint-specific grant was located. Public redistribution remains a separate unresolved permission question. |

Overall confidence in this conditional recommendation is **moderate**: confidence is high in the measured loading and accessible-reference accounting, moderate in author-linked checkpoint provenance, and insufficient for absence of patient exposure. We have no calibrated clinical sensitivity estimate for the duplicate detector. The corrupt member and missing crosswalk are material limitations, not missing values to silently discard.

## Why this does not replace the existing baseline

The completed, provided-region KD study selected positive-case lesion Dice **0.389084** versus matched control **0.383593**; terminal values were **0.383439** versus **0.381964**. These are exploratory development results, not autonomous full-CT performance or proof of a generalization gain. A separately verified historical augmented run selected **0.423761**. Current SuPreM initialization and teacher exposure must also be disclosed; it is not a scratch baseline.

An unchanged pretrained model's four-case result, an autonomous baseline, and a provided-pancreas-region KD run have different inputs, tasks and evaluation scopes. Their maxima cannot establish a fair ranking. STU-Net's benefit must be measured after lesion fine-tuning, against the identical architecture initialized randomly, using the same input trace, training budget and scoring protocol.

## Recommended next decisions

1. **Resolve evaluation provenance first.** Seek a privacy-preserving original patient/study crosswalk or author-administered independent assessment. The questions in [08](08_author_questions.md) are drafts; no author contact or image upload occurred. Obtain the exact checkpoint membership ledger and clarification of s0864. Do not silently drop the five flagged cases or declare the remaining 70 independent.
2. **If we accept exploratory development claims, approve and freeze the matched study in [06](06_experiment_protocol.md).** Start with fresh three-class heads and full-body fine-tuning; compare random versus TotalSegmentator initialization under one fixed recipe. Report selected and terminal checkpoints, lesion components, false positives, negative-case alarms and uncertainty. A later independent evaluation is necessary for unseen-patient claims.
3. **Qualify the actual implementation before training.** Verify small-lesion preservation, full-field CT-only inference, intended tensor loading, real-device 128³ memory/throughput, full-state recovery and independent backups. The 64³ synthetic CPU check does not qualify Mac MPS or Lenovo CUDA. A complete upstream preprocessing plan is missing; any chosen replacement must be explicit and identical across arms.
4. **Preserve alternatives.** A randomly initialized STU-Net control and independently sourced evaluation remain useful if checkpoint membership cannot be resolved. Rejecting all anatomical pretraining would discard a plausible representation without showing that it is ineffective. Accepting an unverified Dice improvement as independent would overstate the evidence. Anatomy-aware targets or a new distilled student belong to later separate ablations.

This is a recommendation for review, not permission to launch or to promote a model. Audit tools and reports remain uncommitted, as the supplied outline requested. Existing training code, scientific recipes, splits, checkpoints and failed audit attempts are preserved.
