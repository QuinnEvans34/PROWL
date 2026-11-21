# Original STU-Net-B provenance

> Initial audit snapshot. Read [the later clearance follow-up](09_clearance_followup.md) for newly verified publisher checksums, historical test-use evidence, sidecar plans and candidate-image findings. The initial release is preserved.

## Which model this is

This audit concerns **STU-Net-B**, not the previously screened CLIP-driven Universal-Swin model. The original STU-Net paper lists Shanghai Jiao Tong University and Shanghai AI Laboratory affiliations. The authoritative [repository](https://github.com/uni-medical/STU-Net/tree/0652eaf5cafda6bc269942238c3695994f2dc4f0) is pinned at `0652eaf5cafda6bc269942238c3695994f2dc4f0`; inspected source hashes are in `source_manifest.json`.

The pinned README places `base_ep4k.model` under **TotalSegmentator trained Models**, distinct from downstream fine-tuning. It specifies 128³ patches, 4,000 epochs and approximately 58.26M parameters. Actual checkpoint inspection confirms epoch 4000 and 58,262,669 parameters. This is credible author-linked origin evidence, not an independently signed training history.

The [paper's pretraining description](https://arxiv.org/html/2304.06716v1#S4) names TotalSegmentator: 1.5-mm resampling, 1,081 training, 57 validation and 65 test cases. Those numbers sum to **1,203**, while the dataset is described as 1,204. Do not invent the missing case or assume every archived CT received gradient updates. The original archive directory and its small metadata member were independently range-read for inventory: the CRC-checked `meta.csv` contains 1,082 train / 57 val / 65 test rows (1,204 total), with the full archive now verified against its published MD5. This records a count discrepancy without proving which rows the exact released binary used. The archived training member s0864 also has an independently confirmed CRC failure; excluding it would fit the one-case difference, but that explanation is unverified. Exact checkpoint training/selection membership and the relationship of the released 4,000-epoch checkpoint to that split remain unverified. Compare conservatively against the original v1 reference pool and label matches by the membership evidence actually available.

No evidence in the inspected original-model release identifies additional pancreatic-lesion training for this checkpoint. That is narrower than proving that its entire training history is independently authenticated. Anatomy supervision does not imply lesion-free source patients.

## Upstream evaluation is a separate exposure category

The [STU-Net paper](https://arxiv.org/html/2304.06716v1#S4.SS2.SSS1) also reports direct evaluation on MSD Pancreas and other public datasets. This is **not evidence that the original body was gradient-trained on those datasets**. However, family-level benchmark results may inform upstream release/architecture choices or our candidate selection. Exact evaluation/selection participation of this particular 4,000-epoch binary and case identities are not established here. The TotalSegmentator image search does not cover every downstream benchmark. Do not turn “released as TotalSegmentator-pretrained” into “never evaluated on any other data.”

## Actual architecture and transfer map

The pinned v2 source constructs a single-channel, six-stage 3D residual convolutional network with feature widths 32/64/128/256/512/512, depth one at each stage, 3³ kernels, five 2³ downsamplings, and nearest-neighbor upsampling followed by convolution. The smoke harness supplied the five isotropic strides explicitly; checkpoint tensors do not encode a complete preprocessing/pooling plan. This is weight/shape compatibility, not a full recreation of the original trainer. Five deep-supervision heads originally output **105 channels**: background plus 104 anatomical classes. The pinned author `label_orders.json` maps **46 to pancreas** and 0 to background; no tumor label appears. Do not borrow channel numbers from the default TotalSegmentator application or Universal-Swin. This source taxonomy is not an independently embedded binary training ledger. Pancreas anatomy is present; pancreatic-lesion supervision is not a separate original head.

The synthetic transfer audit creates new mutually exclusive three-class heads. It transfers all encoder, decoder and upsampling weights, rather than only the encoder:

| Item | Tensors | Parameters |
| --- | ---: | ---: |
| Pretrained body retained exactly | 120 | 58,157,984 |
| Original five 105-class heads discarded | 10 | 104,685 |
| Fresh five three-class heads retained from initialization | 10 | 2,991 |
| Resulting three-class model | 130 | 58,160,975 |

Each head has shape `[classes, features, 1, 1, 1]` plus bias, with features 512/256/128/64/32. `checkpoint_manifest.json` records every tensor and transferred key. All 120 intended body tensors differ from the seeded random initialization and equal the checkpoint after loading. All ten new head tensors remain exactly unchanged from their fresh initialization.

## Loader and version traps

Use the dedicated STU-Net fine-tuning path. The [v2 dedicated loader](https://github.com/uni-medical/STU-Net/blob/0652eaf5cafda6bc269942238c3695994f2dc4f0/nnUNet-2.2/nnunetv2/run/run_finetuning_stunet.py) skips `seg_outputs` and checks body shape compatibility. The v1 dedicated path also skips heads but can leave mismatched body tensors at random initialization. Our audit refuses any such body mismatch.

Generic nnU-Net loader names and comments are insufficient: v1 can merge shape-compatible head tensors, and generic v2 skip patterns use a different head name. The actual keys must be audited. Do not substitute the generic loader or assume v1/v2 state naming compatibility without checking.

Repository code carries Apache-2.0. A separate checkpoint-specific grant was not independently located. The original Zenodo record API identifies the dataset license as CC BY 4.0; it is distinct from the STU-Net repository code license and checkpoint-specific permissions. Redistribution permissions must be checked separately; this report does not grant blanket rights to republish weights or images.
