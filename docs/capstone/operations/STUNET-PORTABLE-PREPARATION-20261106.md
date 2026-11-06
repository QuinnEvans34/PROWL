# Portable STU-Net-B preparation and Windows restoration estimate

**CPU preparation passes; actual pretrained training remains unqualified.** No scientific host has been dispatched. The Mac is checking its complete source availability; an explicit host handoff is required before the one scientific launch.

## Code available for Mac inspection

- `src/training/stunet_transfer_20261106.py`: exact source-hash architecture extraction, original-checkpoint hash/size gate, restricted weights-only loader, exact body transfer, seeded three-class heads, and proposed five-scale loss.
- `scripts/diagnostics/inspect_stunet_cpu_20261106.py`: portable worker payload for a supervised CPU audit. It writes exclusively and distinguishes random architecture from actual original-checkpoint loading. Pass `--source`, `--output`, optionally `--checkpoint`; run under the host resource supervisor.
- `tests/test_stunet_transfer_20261106.py`: seven CPU checks for missing/unexpected/prefixed keys, shape/dtype/nonfinite rejection, source rejection before execution, body/head separation, all-scale gradients, exact loss reduction and target/scale rejection.

The external architecture file matches SHA `53da5fa6ea87c0b63177af6a93b5b148bda96b6e4be22290a8e5d49a4ef261bc` at the pinned STU-Net revision. Only `Decoder`, `STUNet`, `BasicResBlock`, and `Upsample_Layer_nearest` are compiled. Upstream trainer imports are not executed or redistributed. Original weights were not downloaded/reloaded on Lenovo in this stage. The restricted loader path remains to be tested with the actual original checkpoint; no unsafe fallback exists.

## Measured CPU evidence

Seven tests passed (1.836s test body; supervised11.469s,562,282,496B peak owned RSS). Actual external architecture instantiated with58,160,975 parameters and produced five finite three-class outputs on a synthetic32-cube; supervised4.063s,832,770,048B peak RSS. Both workers exited0 and reaped. Bounds were300s/4GiB each. No CT/mask/test reads, GPU work or optimizer updates.

The random synthetic architecture used explicit pools four `[2,2,2]` then `[1,1,2]`, matching the reported author sidecar pooling. This is not actual128-cube preprocessing or CUDA proof. Evidence and code hashes are in the [companion JSON](STUNET-PORTABLE-PREPARATION-20261106.json). The final loader explicitly allowlists the legacy NumPy scalar qualified name; this optional checkpoint branch is not exercised by the random-architecture smoke.

## Proposed loss, pending actual input review

Inputs are five highest-to-lowest-resolution logits and long labels0background/1pancreas-minus-lesion/2lesion. The full-resolution target must match exactly. Lower-scale labels use nearest-neighbor interpolation. Each scale sums voxel-mean3class cross entropy and foreground soft-Dice loss, averaged over batch and classes1/2, spatial sums only, numerator/denominator smoothing1e-5, absent classes included. Scale weights are `[16,8,4,2,1]/31`. This explicitly specified proposal is not a frozen scientific recipe. Small lesions may disappear at coarse supervision scales; audit that rather than assume deep supervision preserves them.

128-cube physical input design, normalization, augmentation and sampling remain to be frozen. Reusing the historical144-cube native-detail/HU loader would change the proposed input recipe and requires an explicit decision. No silent resize or uniform1.5mm resampling was added. Full cohort coverage, actual CUDA forward/backward, strict original body load, optimizer/RNG cold replay from independent backup, native70 cost and the48h total budget remain required.

## Windows restoration estimate

There are923 missing training CT paths totaling30,264,489,348 compressed output bytes. All nine relevant training archives are already on E: (317,707,829,738 bytes). The previous178-case restoration traversed four archives totaling140,186,437,662 bytes and completed in2,034.907s while writing6.13GB. Scaling archive traversal alone gives4,611.76s, about77minutes; writing30.3GB adds uncertainty. **Plan roughly1–2hours**, not a guaranteed completion time. A proposed bounded restoration would use a3h ceiling,35GiB new-CT output limit,4GiB worker RSS and100GiB drive floors. No restoration request or process was launched here. Exact per-member original byte/hash checks and archive receipt checks remain required.

The Mac may be faster to start if all1,403 required source paths are already usable and its actual MPS training qualification passes. CPU tools are portable, but Windows CUDA evidence cannot qualify MPS or vice versa. Neither host should dispatch science until ownership is handed off explicitly.
