# CAP-EXP-001 — completed pipeline smoke, learning criterion not met

September28,2026. Quinton approved the exact prepared run under D-275. One real-data attempt
completed all100 optimizer updates, before/after full-volume evaluation, native exports, five
checkpoints, terminal publication, independent backup and fresh-process MPS restore.
**Mechanical checks passed; the preset learning criterion failed. Both final masks are empty.**
No extension, restart, second experiment or checkpoint reuse occurred.

## Exact execution and preservation

- Run: `outputs/prowl/localizer-smoke-c5f0d7d6-47f6-455b-adb7-e70c63d71bd3`.
- Experiment: CAP-EXP-001, `cohort:pants-localizer-smoke-0001:v1`, train cases3/26 only.
- Request SHA: `9b54a25d3ad014ca325464d35046496357f2e7969c9f4b2ddbd04e1ba2196452`.
- Authorization SHA: `d7d5adfb333a1bb79364676b1a460f465eb1871d58c2d5a0d768ef9ee5520207`.
- Source/environment/plan were unchanged from the prepared request. Live factory checks resolved
  qualified membership and purpose permissions; every consumed source load rechecked the approved
  file identity, hashes, geometry, binary policy and positive target. No raw data were rewritten.
- Scratch SegResNet,96³/batch1,fp32 MPS,seed42,AdamW0.003,weight decay1e-5,cosine100;
 50 alternating updates per case. No pretrained/rehearsal weights, augmentation, cache or workers.
- Checkpoints0/25/50/75/100 and terminal are complete and preserved. Terminal evidence includes
  full-volume metrics, four native binary masks, four contact sheets, controls and reload probe.

| Preserved artifact | SHA-256 |
|---|---|
| Overall run receipt | a470008bf2bf45cda5f3aaf1de451c64efe3b17687227486d750f232ca26f34a |
| Terminal primary completion | fbe7b43b4ac08f6c3810b8abd1b4a8a7081043b2b809f7a2ab82531d63249f7a |
| Independent backup completion | 90ce6dd10d80460b6a7bc3b3c7ae523783833f8be2535085d029e1961e4a15bd |
| Restored artifact completion | 385edede1e5f13c6d7006b6b7cf160d7d1f668c871902e0b6dd728a40be2a1b0 |

Primary terminal directory:
`/Volumes/PROWL-Data/PROWL/artifacts/localizer-runs/850c2021b757cbb05a1b524f09da22b2eed2c11fdde5d757c2ab922c0ad910b6`.
Its files including completion/journal total64,804,462 bytes. The independent internal backup retains
terminal evidence, not raw sources or all intermediate checkpoints. Recovery into a fresh destination
refused primary-volume opens/listings; the restored step100 model's fixed-probe prediction differed
by exactly0 (acceptance atol1e-5/rtol0). Overall receipt member hashes were reread and verified.

## Before/after results

These are **training-case** full-volume measurements on the deterministic preprocessed grid.
Inference used image-only sliding windows and CPU stitching. They are not held-out validation,
lesion segmentation results, native-grid Dice or clinical contour certification.

| Case | Loss before | Loss after | Foreground Dice before | Foreground Dice after | Predicted voxels after | Reference voxels |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 1.547985 | 1.025720 | 0.001799 | 0 | 0 | 2,786 |
| 26 | 1.543702 | 1.026698 | 0.000154 | 0 | 0 | 3,322 |
| Equal-case mean | 1.545844 | 1.026209 | 0.000976 | 0 | — | — |

Mean loss decreased33.6%, satisfying that portion of the preset indicator. Mean Dice did not improve
by0.10; it fell to0. Therefore `learning_observed:false` is the correct recorded outcome. A lower
combined loss must not be presented as successful pancreas localization.

Both native-grid final masks also contain0 foreground voxels. Native shapes/affines and binary export
semantics passed the terminal validator. All four saved contact sheets were visually inspected:
references are visible before and after; initial predictions include extensive off-target foreground,
while final sheets show only the reference overlay. This agrees with the counts. A three-slice contact
sheet does not prove all-volume alignment or expert contour quality; prior qualified preprocessing
and executable geometry checks remain the relevant supporting evidence.

## Timing and resource observations

| Measure | Observed |
|---|---:|
| Complete supervised attempt including preparation/backup/restore | 234.25s (3.90min) |
| Update phase including scheduled checkpoints | 173.98s |
| Executor through after-evaluation, before terminal/probe/publication overhead | 186.92s |
| Median load-and-update iteration | 1.534s |
| Maximum load-and-update iteration | 1.688s |
| Peak sampled worker RSS | 3,599,679,488 bytes (3.35GiB) |
| Peak boundary MPS driver allocation | 2,479,734,784 bytes (2.31GiB) |

RSS and driver allocation overlap and must not be summed. Sampling may miss transient peaks. The
run stayed within600s update/1,200s total,16GiB limits, scoped output quotas and free-space floors.
The supervisor exited0 with no stop reason. AC/native MPS and exclusive accelerator ownership checks
remained in effect. No global scientific roots/source aliases were activated.

## What the evidence does and does not explain

The first update loss was1.532822 and the final update loss1.026190; finite-loss/gradient/state checks
passed throughout. Member ordering was exact:50 updates for each case. The stateless equal-probability
center sampler selected44 foreground centers and56 background centers (case3:20/30;case26:24/26).
Equal probability does not require exactly50/50 in one seeded run, and a background center does not
mean its whole patch is target-free. There was no all-background-center sampling failure.

The full preprocessed targets contain2,786 and3,322 voxels. Even if every reference voxel lay in a
96³ patch, pancreas would occupy only0.315% and0.375% of that patch respectively. Thus foreground-
center sampling did not create voxel-balanced patches. This is an upper bound derived from existing
records, not a new raw-data measurement or proof of the optimizer's failure mechanism.

The observed outcome is an all-background argmax solution after100 updates. Class imbalance,
optimization rate/schedule, and insufficient learning time remain candidate explanations. No CT
probability distribution or per-class gradient summaries were retained, so do not claim the model
has zero foreground probability, that it learned no useful features, or that one particular cause is
proved. The earlier invented-cube success did not guarantee learning on much smaller real targets.
There is no basis here for excluding these valid cases, declaring their labels corrupt, altering
protected roles, claiming generalization, or approving a useful trained localizer.

## Recommended next discussion and bounded experiment

Keep the same two cases, qualified inputs, model, preprocessing, seed, inference and preservation
path. The next goal is **demonstrable tiny-set pancreas learning before cohort expansion**.

First prepare a small optimization diagnostic that records foreground probability summaries,
foreground/background CE contributions and target fraction per sampled patch. Use those observations
to distinguish suppression by the optimizer/loss from merely insufficient training. A lower learning
rate (for example0.0003 versus0.003) is a reasonable first controlled comparison; it is a proposal,
not a selected or approved run. Avoid changing loss weighting, sampling, horizon and LR together.
If additional steps are justified, give that comparison its own bounded plan and identity rather
than extending this completed experiment or silently resuming its checkpoint.

Freeze the exact comparison and resource budget before CAP-EXP-002. No automatic follow-on has been
launched. Preserve this null result as the baseline it is. The machinery is now exercised on real CT;
the learning gate remains open.

## Verification and unchanged work

No executable source or dependency changed during this launch. The existing1,074-test native baseline
therefore remains the applicable code verification; the requested real execution adds runtime evidence,
not a new unit-test count. Source controls were matched before compute; original run files remain
immutable. Result documentation and D-275 were added separately. No Git commit/push, literature
changes, download, outreach or additional CT investigation occurred.
