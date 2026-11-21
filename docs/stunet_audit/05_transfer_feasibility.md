# Transfer feasibility and limits

> Initial audit snapshot. Read [the later clearance follow-up](09_clearance_followup.md) for newly verified publisher checksums, historical test-use evidence, sidecar plans and candidate-image findings. The initial release is preserved.

**Technically viable for further qualification; not integrated or training-qualified.** The successful synthetic check establishes that the intended pretrained body can be reused with new lesion heads. It does not establish that transfer will improve lesion Dice. **STU-Net-B has no PROWL patient accuracy result in this audit.** The earlier approximately 0.71 four-case screen belonged to the different Universal-Swin model, not this checkpoint.

## Input and geometry

STU-Net-B accepts one CT channel. Five downsamplings require compatible dimensions, such as the original 128³ patch; the verified smoke input was only 64³. Patch size, spacing, coverage and memory are coupled: a 128³ patch at 1.5 mm spans 192 mm per axis. Coarse resampling may remove small lesions. Before using it, audit annotation/component preservation and native reconstruction on permitted training cases, then freeze the same transform for scratch and pretrained arms.

The supplied `plan_files/plans.pkl` is only 583 bytes. Its restricted inspection reveals `GenericPreprocessor`, `normalization_schemes={0: nonCT}`, `use_mask_for_norm={0: false}` and identity transpose settings. It does **not** contain a complete target-spacing/patch/intensity-statistics plan. In the inspected v1 `preprocessing.py`, that nonCT/no-mask path uses per-case mean/std normalization after the crop/resample path. It is not evidence for silently reusing Universal-Swin HU clipping or the student's existing normalization. Inspect and freeze the entire chosen preprocessing path, including training-only fitted statistics if used.

The overlap audit's unknown-unit appearance mode is strictly duplicate-candidate tooling. It assigns no millimetres and cannot qualify an unknown-unit scan for clinical inference, resampling or training.

## Target design

**Approach A is the recommended first experiment:** background, pancreas parenchyma and pancreatic lesion. The existing binary source masks can overlap; construct class 2 from lesion first, class 1 from pancreas minus lesion. Record both parenchyma and organ-plus-lesion union scores. Preserve the original masks and validate the conversion. No target annotations may determine development/test inference crops.

**Approach B should be a separate later ablation.** PanTS has substructures and surrounding anatomy, but availability and mutual exclusivity are not yet audited for this cohort. Parent pancreas, head/body/tail and lesions can overlap semantically. Use a hierarchical/multitask or multilabel formulation with explicit valid-label masks where appropriate; do not force nested labels into one softmax or treat missing annotations as verified background. No substructure labels were opened for this audit.

## Optimization and matched comparison

Start with full-body fine-tuning and fresh heads. Freezing the encoder is an optional later budgeted ablation, not a guaranteed improvement. The upstream recipe describes smaller body learning rates, but using different optimizers or schedules across the primary arms would confound initialization with training strategy. The proposed primary experiment therefore gives the random and pretrained architectures the same optimizer, schedule, head seed, sampling and input trace. Report that a fixed recipe does not establish either architecture's best achievable performance.

Use Dice plus cross-entropy with explicit background and deep-supervision policy. Balance lesion-focused and CT/context views using training annotations only; retain reference-empty cases rather than optimizing only positive lesions. Freeze rotations/scales/flips/intensity augmentations and deterministic seeds. Select checkpoints on the same development metric/cadence and report selected **and terminal** checkpoints. Sliding-window geometry, probability blending, output remapping and any postprocessing must be identical between arms.

## Resource and integration assessment

The new model has about 4.1 times the student's parameter count. Float32 parameters alone require roughly 222 MiB; gradients, optimizer states and especially 3D activations require substantially more. The 64³ CPU probe peaked at 4.78 GiB including checkpoint/loading and audit copies. This is **not a GPU peak measurement** and cannot be extrapolated into a qualified batch size or runtime. Neither Mac MPS nor Lenovo CUDA has been qualified for 128³ STU-Net training here. Apple unified memory is shared by CPU and GPU; owned RSS alone does not certify MPS allocation or system pressure. Future qualification must measure the actual device allocator and combined memory pressure, not interpret 64 GiB RAM as dedicated VRAM.

Before launch: bounded real-device forward/backward, full-field inference, original/new head checks, numerical/recovery checks, independent backup and cold restore, measured runtime/storage estimate and a fresh launch receipt. Keep the live student pipeline unchanged. A future distilled student would use a separate train-only cache with teacher provenance, world-geometry checks and its own matched zero-KD control.
