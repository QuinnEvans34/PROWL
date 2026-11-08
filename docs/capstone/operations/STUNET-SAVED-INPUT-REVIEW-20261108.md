# Saved STU-Net input/pipeline review — November 8

Read-only source and saved-metadata review alongside the unchanged continuation. **No new input-integrity failure found in the examined evidence.** This is not a new cohort audit or a claim that all inputs are perfect. No CT/mask/model arrays, GPU/model calls, source edits, restart or monitor changes.

At the captured snapshot, the same supervisor48348/workerwrapper52992/actualworker32244 owned the run; global **12334**, **334 new updates**, 32.28 minutes recorded, MLflow13c709ae157949988de1d7f8821a03b7 RUNNING. The report records process identities and the SHA256 of a fixed complete-line journal prefix, not a hash claimed to describe the subsequently growing whole journal.

## What is actually fed to the model

- Both training and development use `normalize_region`: orient/crop CT, clip HU to[-100,250], then `(HU+100)/350` to[0,1]. Training adds bounded flips/rotations/intensity augmentation and clips back to[0,1]; development does not augment. This is an intentional training/inference difference, not an inconsistent base normalization.
- Single128-cube optimizer windows; inference reconstructs the whole provided-pancreas region with128windows/64stride. CT is linearly sampled and labels use nearest-neighbor sampling. The physical grid preserves fine native axes and subdivides coarse axes to at most1mm. It does **not** uniformly resample to1.5mm. Physical field of view therefore varies with source spacing.
- Current correction binding enforces the exact seven-case overlay and unchanged ordinary target bindings. Cohort664positive/669empty, no exclusions. No corrected case had yet appeared in this334-update prefix; their earliest scheduled visits begin atglobal12373. The seven real corrected-target/loader checks already passed during qualification. Do not confuse qualified preparation with observed scientific exposure.

## Observed class presence and supervision

Among334 updates, 157 used positive cases and 177 used empty cases. **122 patches contained lesion voxels**; 35 positive-case windows did not. The sampled voxels were **95.50% background,4.22% pancreas,0.275% lesion**. These are patch-weighted counts, not unique anatomy or full-cohort prevalence. Every examined class-count sum, lesion count and global augmentation address was consistent; logged losses/LRs were finite.

The prefix contains251coverage and83context windows, no component jitter yet. This matches the frozen schedule: all2978coverage-focus addresses precede jitter; **first jitter is global15971 (new update3971)**, with every fourth update remaining context. Positive-case coverage spans the annotated pancreas/lesion field and does not promise lesion presence in every patch. Early scores therefore reflect the coverage-first regime; do not interpret a75%focus ratio as75%lesion-positive patches.

Only one scientific per-scale diagnostic was available at this snapshot, at12001 on an empty patch. Body and head gradient norms were both nonzero (.237556/.042172). This confirms observed backbone/head gradients for that update, not a representative lesion-gradient analysis. The saved nonpromotable producer's positive case1996 retains lesion counts4821→597→74→9→1 across five scales. Nearest-neighbor deep supervision can plausibly undersample tiny lesions, but this one trace does **not** demonstrate a lost component or quantify its effect on Dice. Full-resolution foreground Dice and voxel-mean CE remain the unchanged objective; background prevalence alone does not prove the loss is the cause.

## Comparison with pretrained STU-Net preprocessing

**Confirmed:** the adapter extracts only four architecture classes from the upstream source and does not execute its nnUNet trainer/preprocessor. Our actual HU scaling and physical-grid policy are explicit above. The retained upstream trainer accepts `plans` and a configuration manager; it does not itself supply the checkpoint's numeric normalization statistics.

**Unresolved:** the reviewed saved CPU checkpoint-load receipt attests tensor equality, parameter counts and shapes, not exact checkpoint-bound normalization means/stds/percentiles or original resampling plans. The earlier local proposal of1.5mm/z-score is not proof of the original checkpoint's preprocessing. This bounded review therefore cannot state the exact upstream intensity transformation or quantify a mismatch with it. Matching tensor dimensions does not establish preprocessing equivalence. Authoritative exact plans are the missing evidence to reconcile next, without reopening arrays or altering the active experiment.

The current traces store hashes/class counts, not CT intensity histograms or saturation fractions. They cannot tell how much lesion contrast the HU window clips. Normalization/context mismatch with pretraining and sparse coarse-scale supervision are **testable hypotheses**, not confirmed explanations for low Dice. The original seven erroneous annotations were a confirmed omission already corrected for this continuation; no new label/cropping bug was established here.

## Evidence anchors

- [Normalization](../../../src/data/segmenter_fast_varied_v1.py):88–93.
- [Continuation loader](../../../src/data/stunet_continuation_inputs_20261108.py):19–28 correction/delegation;39–59 cache/geometry/sampling/augmentation.
- [Development and reconstruction](../../../src/data/stunet_inputs_20261106.py):92–121; same normalization at108.
- [Physical grid](../../../src/data/segmenter_physical_windows_v1.py):20–48.
- [Augmentation](../../../src/training/segmenter_augmentation_v1.py):38–78; input/output range assertions and stored class counts.
- [Architecture-only import/loss](../../../src/training/stunet_transfer_20261106.py):26–37 and107–135.
- [Schedule](../../../src/data/stunet_errata_20261108.py):44–69.

Adjacent [JSON](STUNET-SAVED-INPUT-REVIEW-20261108.json) contains exact source anchors/hashes checked against ready pins, saved metadata/qualification hashes, raw diagnostic summaries, correction visit addresses and process identities. JSON SHA256 **86378997607f46669af57b85254da546540c02584e6607df29f73468b8b3ce26**. No new counterfactual scoring was duplicated here; Mac is computing that separately from saved counts.
