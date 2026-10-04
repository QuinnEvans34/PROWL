# Frozen-cohort loader and preprocessing handback

September 28, 2026. **The two-case cohort now reaches verified, aligned, single-channel CT tensors
and binary pancreas targets through a dedicated capstone consumer.** The bounded native preprocessing
check and engineering visual review passed. This is Phase C evidence, not a training result or launch.

## Implementation and decisions

D-270 records Quinton's explicit loader/preprocessing request. New components:

- `src/data/localizer_inputs.py`: resolve the exact frozen cohort and its history/qualifications before
  source payload reads. Bind `followup_source` through the pinned registry and previously verified
  extraction request. Open only consumed CT/pancreas files without symlinks, verify stat and byte hashes,
  check descriptor geometry and explicit CT mm units, apply D-259 after NIfTI scaling. The unknown mask
  unit is accepted only within the already-qualified same-grid / explicit-mm-CT pairing. No guessed CT units.
- `src/data/localizer_preprocessing.py`: deterministic MONAI transforms and source-grid restoration.
  Images and targets remain separate; the target cannot affect image channels, field of view or crops.
  Shared train/inference image processing; one CT channel, target values exactly 0/1. The serialized,
  content-hashed transform record stores original/processed shape and affine, recipe and operations.
- `configs/capstone/localizer-preprocessing-v1.json`: Codex's versioned engineering starting recipe:
  RAS, 3 mm, HU [-100,300] to [0,1], trilinear image / nearest target, symmetric zero-pad to minimum 96³.
  Normalize before resampling so out-of-field zeros are normalized zeros, not 0 HU. No crop, augmentation,
  reference ROI, persistent cache or data-loader workers. This is not a model-selected optimum.
- `scripts/diagnostics/localizer_preprocessing_check.py`: supervised CPU-only real-case check, reports
  and contact sheets under the preregistered [job](LOCALIZER-PREPROCESSING-JOB-2026-09-28.md).

The loader reuses the previously tested no-follow file-opening/stat helpers. Historical dataset/transform
code, old experiments and approved D-259 implementation bytes remain unchanged. In particular, the
historical multi-class loader is not implicitly made capstone-compliant by these new components.
The global scientific-run flag and source registry aliases remain disabled; D-270 supplies a narrow
read-only preprocessing capability, not general source activation or permission to train.

Recipe file SHA-256: `3bdc8ae7f60039b6a3e4e8a3ae2629255af4f3519ff83814145f7988d2242f94`.
Read-capability SHA-256: `0e0a05279dead8c365a3359f35da260aacdcca20c98400ddb820242a1ed80473`.
Cohort completion SHA-256 remains `37a4f6a8e248200de579a31631d740b5009b0836147b382aff50212084cb632c`.

## Native execution and actual results

Package: `outputs/prowl/localizer-preprocessing-b5f21624-03d9-4f2b-9e2e-177d88a5699e/`.
Receipt SHA-256: `286a454c890637b228cb879b698e5b019571e50d465b27c34797316c7deae446`.
All **11 covered hashes** verified; 12 files total, **686,256 bytes**. The worker completed successfully
in a supervised **42.30 seconds** (40.92 seconds inside the worker), including full cohort resolution.
Peak observed worker RSS: **2,869,755,904 bytes (2.67 GiB)**, below the 4 GiB polling ceiling. Four raw
source files / **23,331,170 compressed bytes** read; no lesion/test payloads or model/accelerator work.

| Case | Native shape | Processed shape (excluding channel) | Native foreground | Processed foreground | Restored foreground | Round-trip mask Dice |
|---|---|---|---:|---:|---:|---:|
| 3 | 495×349×40 | 136×96×98 | 14,894 | 2,786 | 14,892 | 0.94548 |
| 26 | 512×362×81 | 108×96×134 | 45,095 | 3,322 | 45,218 | 0.94354 |

Foreground voxel counts at different spacings are not directly comparable physical volumes.
Round-trip Dice measures resampling changes, not model performance or accuracy against an expert.
The source shape/affine is recovered exactly within the declared geometry tolerance; label boundaries
are not promised lossless after changing resolution. These differences do not revoke source qualification.
Training and image-only inference tensors were **bitwise equal for both cases**. CT load/decode checks
were approximately 0.99 / 0.78 seconds and train transforms 0.15 / 0.26 seconds on this already-running
process. Those are component observations, not MPS training throughput or a cold-machine benchmark.

## Visual assessment

Codex inspected all four saved sheets: transformed CT/plain-and-overlay in axial, coronal and sagittal
planes, plus original-versus-restored target sheets on the same native planes for each case.
No obvious gross shift, axis reversal, lost pancreas foreground or restored-grid displacement appeared
in these views. Expected coarser boundary/partial-volume appearance is visible after 3 mm resampling.
This supports the engineering preprocessing check; it is not a clinical diagnosis or expert boundary
certification, nor a review of every slice. Display sheets use the separately labeled [-160,240] HU
window; model normalization uses [-100,300].

## Tests and reproducibility

**1,013 native tests passed**, including 28 new preprocessing/loader tests, with only the two existing
upstream torch.jit warnings (8.33 seconds). The earlier pre-run suite passed 1,010 tests; three final
integration tests then covered full dataset access and the factory rejection order. Coverage includes axis permutations/reflections with exact
landmark recovery, anisotropic/oblique geometry, continuous-probability versus nearest-label restoration,
source immutability, binary labels, image-only parity despite changing targets, disappearing thin target,
invalid affine/nonfinite CT, unsafe/stale source files, wrong role/kind/cohort, failed cohort rejection
before raw reads, recipe pin rejection, full dataset tensor access and deterministic repeated loading.
A vanished positive target stops the recipe for review; it is not silently turned into a negative.

Persistent caching is explicitly disabled and unsupported cache modes are rejected. Repeated loads
produce identical tensors/transform records; they reread verified inputs rather than reuse an unbound
cache. There is therefore no unverified warm-cache path to claim. Future cache support must include
input, target/policy, code/config and environment identity and pass its own stale-cache tests.
The receipt captures producer source text, recipe/capability pins, transform records and runtime versions:
Python 3.12.13, PyTorch 2.13.0, MONAI 1.6.0, NumPy 2.5.1, NiBabel 5.4.2. No dependencies were installed.

## Next: learning and checkpoint safety

Phase C passes for this **specific deterministic full-volume preprocessing recipe and cohort**.
The output is not yet an approved direct whole-volume SegResNet training batch: spatial dimensions
need not be multiples of the model's downsampling factor. Phase D must specify and test the bounded
model input/patch adapter (for example 96³ patches), sampling policy and corresponding full-volume
inference path. It must not quietly introduce target-dependent inference crops.

Next implement scratch initialization, binary output/loss, finite gradients, synthetic learning,
checkpoint save/reload and interruption/recovery with exact run/cohort/recipe identity. Then measure
MPS resources and freeze the real smoke's patch/step/time budget in the experiment notebook before
launch review. No capstone training, checkpoint, source rewrite, commit, push or literature download
occurred in this task. The optional Claude/P2 decisions are documented separately and do not block
this imaging sequence.
