# PanTS varied training views results and next experiment

## Selected checkpoint findings

The varied-training-views run reached a new native lesion Dice record of **0.423761 for the current
matched 70-case development series**, selected at 18,000 updates. This is promising progress toward
the project's 0.50 target, not a statistically established augmentation benefit. Earlier course
scores used other protocols and are not ranked against this series.

The intervention combined aligned spatial flips and rotations with CT intensity and noise variation.
The same 1,333 PanTS training cases, original SuPreM initialization with fresh head, 144-cube
provided-pancreas inputs, DiceFocal loss, seed42 and 24k optimization schedule were retained.
Masks remained supervision, not CT input channels. No PANORAMA, EMA or postprocessing was added.

| Native metric | Original selected 14k | Augmented selected 18k |
|---|---:|---:|
| Positive-case lesion Dice including misses | 0.405092 | 0.423761 |
| Cases with overlapping lesion prediction | 34/36 | 33/36 |
| Empty cases with any predicted lesion | 32/34 | 27/34 |
| Predicted lesion voxels across empty cases | 205,564 | 100,767 |
| Pancreas Dice across all 70 cases | 0.810533 | 0.811406 |

Tensor-grid peak was 0.424281 at 18k; terminal tensor Dice was 0.396219. Native and tensor values
remain separate. Training plus in-run validation took 75,647.875 seconds, or **21h00m47.875s**;
post-training native evaluations are additional time.

## Frozen hypothesis decision

H0: augmentation does not increase native positive-case macro Dice, delta <= 0.
H1: delta > 0. Practical acceptance additionally requires delta >= 0.02, positive lower 95%
paired-bootstrap bound, and every detection, alarm, pancreas and empty-voxel-burden guardrail.

Selected-versus-selected gain is **0.018668**, paired 95% interval **[-0.047826, +0.081128]**.
All four point guardrails pass, including the one-case detection decrease of 2.78 percentage points
against the frozen 3-point allowance. Passing that allowance does not mean detection was unchanged.
The Dice gain falls short of 0.02 and the interval spans zero: **H0 is not rejected; the practical
intervention is inconclusive**, neither accepted nor rejected. We do not accept H0 or move the goalposts.

Bootstrap uses 10,000 resamples, seed20261017 and sorted paired positive case IDs, treated as patient
units under the frozen cohort. It conditions on selected checkpoints and reused development cases;
it does not include checkpoint-selection or cross-seed uncertainty. These are exploratory results,
not independent generalization or statistical noninferiority evidence.

## What improved and what remains weak

Twenty-three positive cases improved, eleven worsened and two were unchanged. Descriptive size
subgroups, not prespecified independent hypothesis tests:

| Lesion size band | Cases | Control Dice | Augmented Dice |
|---|---:|---:|---:|
| Small | 5 | 0.164142 | 0.238386 |
| Medium | 24 | 0.429395 | 0.488376 |
| Large | 7 | 0.493877 | 0.334634 |

The best checkpoint is not merely benefiting from more false-positive paint: empty prediction
burden fell by about 51%. Nevertheless, 27/34 empty scans still trigger at the any-voxel definition,
and three positive scans have zero overlap. This is not yet a reliable lesion-presence system.
Large-lesion regressions merit targeted overlay review before attributing them to cropping, capacity
or undersegmentation; aggregate Dice alone cannot identify the cause.

The tensor curve remains unstable: 0.3527 at6k, 0.2092 at8k, 0.4243 at18k and 0.3668 at20k.
Augmentation may be helping robustness, but this one bundled-policy, single-seed comparison cannot
identify the useful transform or prove overfitting was the sole bottleneck. We still need a gain of
0.076239 to reach native Dice0.50 on this protocol.

## Proposed next run

**PanTS varied views with gentler optimization** is the preferred immediate candidate for discussion.
Change only peak learning rate from 0.0001 to **0.00005**. Keep the complete augmentation policy,
original SuPreM plus fresh seed42 head, 1,333/70 cohort, cache, loss, weight decay, batch1,
500-step warmup, cosine24k horizon, 2k validation cadence and ordinary-only checkpoint selection.
Start fresh, not from the selected18k weights. No PANORAMA, new labels, larger model, EMA or
longer horizon in the same comparison.

This is an optimization hypothesis motivated by the observed oscillation, not a diagnosis that the
current learning rate is too high. A lower rate can also underfit. It is a relatively inexpensive,
single-factor follow-up that reuses the already qualified data without another duplicate audit.
Expect roughly this run's21hours, subject to measured qualification speed; resource limits must be
checked before a frozen specification and separate launch approval.

Proposed H0: lower LR does not improve selected native Dice relative to this augmented run.
Use the same decision structure: delta>=0.02, paired lower95%bound>0, detection delta>=-0.03,
alarm delta<=+0.03, pancreas delta>=-0.02 and no increase in empty lesion-voxel burden.
The resulting point target would be0.443761, not0.50 as a binary pass condition. Evaluate final24k
versus final24k as mandatory secondary. Preserve the original no-augmentation baseline as context;
using augmentation as a working comparator does not retroactively accept its inconclusive result.

Review the large-lesion regressions using existing predictions or a separately approved bounded
diagnostic before freezing this choice. If geometry/support failure is demonstrated, address that
specific failure before an LR trial. Do not infer such failure from lesion size alone. A matched
second-seed pair would strengthen causal evidence but costs two runs; it is a confirmation option,
not a prerequisite for discussing the next exploratory experiment.

## Knowledge distillation next week

The October18 request reopens **consideration** of distillation, superseding the old notebook's
blanket reference-only policy for discussion. It does not authorize distillation training now.
Keep an independent supervised line and a clearly labeled teacher-assisted line if it proceeds.

Distillation trains a student using teacher probability targets alongside real masks, rather than
merely loading pretrained weights. Its motivation is knowledge transfer, not a guarantee the student
will reach the teacher's Dice: [Hinton et al.](https://arxiv.org/abs/1503.02531).
First identify the exact checkpoint, license, output-class mapping, preprocessing, training membership
and provenance. The official [R-Super checkpoint list](https://github.com/MrGiovanni/R-Super)
includes distinct paper/demo models with different training sources. Evaluate the intended teacher
on permitted development cases using the same native scorer; compare its errors and predictions
before designing a supervised-loss-plus-distillation-loss experiment. Teacher targets for training
must come only from training cases; known or uncertain teacher exposure to our development cases
must be disclosed and resolved for any clean evaluation claim. Reuse existing dataset overlap
decisions; teacher provenance is a different question, not a repeat CT duplicate scan.

The official [PanTS benchmark](https://github.com/MrGiovanni/PanTS) currently lists MedFormer DSC52.9%
and R-Super53.4% on its901-case test set, not a universal0.60 target. Its case-detection definition
also differs from our overlap requirement. A0.60 development result would be an exciting milestone,
but matching Johns Hopkins requires matched data, ROI availability, scoring and evaluation protocol.
No test-set tuning, teacher download, inference or training was performed in this review.

## Evidence and completion

Frozen plan: [varied training views](PANTS-AUGMENTED-VIEWS-24K-20261017.md).
Reproducible saved-metrics review: `scripts/diagnostics/review_augmented_views.py`.
Private results: `E:/PROWL/readiness/pants-augmentation-review-20261018-a01/results.json`.
MLflow run: `dbf1a562e9eb4d5a96301718a19d07a8` in the existing local tracking database.
All24,000 updates and12complete tensor validations are verified. Both70-case native endpoints
completed; workers are reaped. All445frozen producing pins match, as do all five E:/C: checkpoint
pairs, both native reports and final journal backups. Supervisor runtime was76,635.312seconds;
peak owned RSS2,847,379,456bytes. Three focused comparison tests pass. An early read-only review
attempt correctly refused while native evaluation was incomplete; no inference was repeated.
No next scientific run is launched by this retrospective.

## Mandatory final checkpoint comparison

| Native metric at24k | Original | Augmented |
|---|---:|---:|
| Positive lesion Dice | 0.319538 | 0.393723 |
| Detected positive cases | 26/36 | 32/36 |
| Empty cases with alarms | 18/34 | 25/34 |
| Empty predicted lesion voxels | 20,652 | 72,314 |
| Pancreas Dice | 0.827748 | 0.820664 |

Final-versus-final Dice gain is0.074185,95%CI[0.000404,0.151294]. This secondary Dice-only H0
is rejected under the frozen interval rule, with a barely positive lower bound. However, the
practical secondary comparison is **rejected**: alarms rise7/34 and empty voxel burden rises.
It cannot substitute for the primary inconclusive result. Augmentation retained more lesion
performance at the end of training, but not without a detection/false-positive tradeoff relative
to the original terminal checkpoint. The selected18k remains this run's prospectively selected
candidate; do not switch endpoints after seeing native outcomes.
