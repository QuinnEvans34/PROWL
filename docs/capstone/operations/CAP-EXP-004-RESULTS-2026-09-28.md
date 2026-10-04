# CAP-EXP-004 result — longer run improves fit; excess foreground remains

The final overnight D-279 experiment completed all **300 updates** and passed its preset minimal
learning indicator, terminal publication and independent recovery. Mean full-volume training Dice
increased from 0.000976 to **0.445999**. This is materially better fitting of the same two training
cases, not validation or a claim that the contours are ready for use. Training stopped after this run.

## Preset comparison and observed result

Compared with CAP-EXP-003, retain the balanced CE + foreground Dice objective, LR 0.0003, seed 42,
scratch SegResNet, cases 3/26, preprocessing, 96³ patches and argmax. Change 100 to 300 updates and
cosine T_max 100 to 300; checkpoint/evaluation cadence becomes 75. The matched schedule horizon also
changes the learning-rate trajectory, so duration alone is not isolated. No old weights initialize
this run and no intermediate checkpoint is selected instead of the final endpoint.

| Case | Balanced loss before → after | Original loss after | Dice after | Predicted / reference voxels | Precision | Recall |
|---|---|---:|---:|---|---:|---:|
| 3 | 1.838895 → 1.049670 | 1.121795 | 0.439224 | 9,900 / 2,786 | 0.281414 | 1.000000 |
| 26 | 1.775748 → 1.048054 | 1.120881 | 0.452774 | 11,352 / 3,322 | 0.292636 | 1.000000 |
| Mean | 1.807322 → 1.048862 | 1.121338 | **0.445999** | — | — | — |

These metrics cover the entire processed 3 mm volumes, not selected patches. Precision and recall
are descriptive post-run calculations from the retained Dice/counts: TP = Dice × (predicted +
reference) / 2, checked to yield exact integer intersections. No native-grid Dice or held-out
performance is claimed. Final predictions are **3.55× and 3.42×** reference volume, leaving 7,114 and
8,030 false-positive voxels respectively. Both after contact sheets were inspected: their three
orthogonal processed-grid views show improved localization and surrounding excess foreground.
This is a limited visual review, not exhaustive examination of every slice.

| Completed updates | Mean balanced loss | Mean Dice |
|---:|---:|---:|
| 0 | 1.807322 | 0.000976 |
| 75 | 1.178968 | 0.069718 |
| 150 | 1.078732 | 0.303144 |
| 225 | 1.052717 | 0.425373 |
| 300 | 1.048862 | 0.445999 |

Improvement slowed near the endpoint as the cosine learning rate approached zero. This does not
establish a plateau under another schedule or justify an unattended extension. The preset ≥10%
objective decrease and ≥0.10 Dice gain pass; they remain weak learning indicators, not contour
acceptance criteria. The before/after losses are comparable within this objective; absolute objective
values must not be directly compared across the different loss definitions of CAP-EXP-001 and 002.

## Execution and preservation checks

- Exactly 150 updates per case. First 100 crop traces equal CAP-EXP-001; original scratch parameter
  digest `365306b1aec77681bd651a1e87ca7902b10efffef38607f1618303220d20954e` verified.
- Source/environment re-captured after execution and matched the prepared request exactly.
- Update phase 518.49 s, below 600 s. Whole supervised attempt including startup/backup/restore
  577.91 s, below 1,200 s; no cap stop or retry.
- Sampled peak worker RSS 3,501,178,880 bytes; stage-boundary MPS driver allocation 2,475,524,096
  bytes. These overlapping memory measures are not additive; both remain below their 16 GiB caps.
- Checkpoints 0/75/150/225/300 and terminal exports preserved. All 15 local receipt members and
  21 primary terminal members independently rehashed after completion.
- Fresh-process restore read the independent backup with primary data access forbidden. Restored
  step 300; fixed-probe maximum probability difference **0.0** (allowed absolute tolerance 1e-5).
- Native implementation baseline **1,089 tests passed**, two existing warnings. The final native
  synthetic rehearsal passed before request preparation. No executable changes followed that check.

The raw invocation records optional CLI flags (`experiment: null`, `balanced: false`) because launch
was specified by its pinned request. Effective experiment/loss/configuration come from the checked
`plan.json`, `identity.json` and authorization, which record CAP-EXP-004 and the balanced objective.
These raw flags did not choose the real training configuration.

## Exact evidence

Run: `outputs/prowl/localizer-smoke-274c7bca-dc33-43a6-b025-8bd8aa110737`.

| Record | SHA-256 |
|---|---|
| Request | `a4d5a6ab403f0da59645132f9c244afbd4d1abfa803c30cda9e1d0446a4c3bf3` |
| D-279 authorization | `0c7c0471e3f07db0a364898d0cf0059d9951832e32645d9c01acb42b63af1c2c` |
| Local receipt | `1de1d74746ed79c365beadeee528a60fd6f3b61fc2b3d0e429a96ee8c9d39f2c` |
| Terminal completion | `e1caff1244b17c944604435ab7b556b6175715568eba005d9015c31ffb7bd1b6` |
| Independent backup | `235cf1f0827f5eda2189ccf7515dc58076aa6d0bd589929280ceaba557f1cf7d` |
| Independent restore | `b2e6305a432a384eac8c347c0d1900bd2b12e1a05fbe4790b7a7645306fba65a` |
| Post-run descriptive review | `8f2c0840ed43d6b91f459840d591821ccbc3705381ce9db310bf63e56d2a3e37` |

Post-run review: `outputs/prowl/CAP-EXP-004-POSTRUN-REVIEW.json`, separately written after completion;
not retroactively added to the immutable run receipt. Primary terminal directory key
`e3d7eb10b2470b59dda2c0fb32c34dcd86e776b5738f5f51940e8ea44b35ec59` under the registered localizer root.
All earlier experiments and unsuccessful outcomes remain retained. No source rewrite, data expansion,
validation/test access, learned-weight reuse, threshold selection or global source activation.

Next: discuss a stronger small-cohort fit/localization gate and one controlled follow-up, then qualify
broader varied training and separate validation cohorts. The current recall of 1.0 applies only to
these repeatedly optimized training references. See the [morning handoff](MORNING-HANDOFF-2026-09-29.md).
