# CAP-EXP-011 — 25/75 class-mean balance comparison

D-312 authorizes implementation, qualification, exact request freeze and one bounded training launch.
Quinton: “Great, continue with that. Great work.” [Design proposal](LOCALIZER-CLASS-MEAN-REBALANCE-PROPOSAL-2026-10-01.md),
[motivating D-311 audit](LOCALIZER-FOREGROUND-AUDIT-RESULTS-2026-10-01.md).
This file is the prospective run design; observed qualification/request/result records follow
separately. No repeated launch confirmation is needed after the approved gates pass.

## Scientific identity and formula

Exploratory matched intervention against010's retained single control. Import exact independent
backup007step300 model/AdamW state, parent-reference SHA
`969d86b898e90ff8c5afc340c336588f5f757615409feb12bf8f975948f4d5cc`, model SHA
`8db271a2f458386e4fd33af7bd3540bade4ebd23a19e79b565c9b8715c8ea988`.
Preserve optimizer moments/counters/initial_lr0.0003 and original progress/RNG. New child uses
constant0.00001,300new updates, absolute sampler300–599/logical600;not a fresh600-update replay.

The sole scientific change from010 is the CE class-mean weighting. On mixed-class patches:

```text
CE = 0.25 * mean(foreground CE) + 0.75 * mean(background CE)
DiceLoss = 1 - (2*sum(p_foreground_on_reference) + 1e-5)
               / (sum(p_foreground_all_voxels) + reference_foreground_count + 1e-5)
Loss = CE + DiceLoss
```

Use stable two-class logits CE. Empty targets receive full-strength background mean CE and noDice;
all-foreground targets receive full-strength foreground mean CE plusDice. Per-case CE is averaged
across a batch, and Dice across nonempty cases, matching prior conventions; real batch remains1.
The class-mean formulation differs from per-voxel class weights0.25/0.75. No cap50 or support mask.

Retain113train/40development-validation,144³/2mm cache,seed42,batch1,architecture,AdamW wd0.00001,
float32 nativeMPS/no fallback,twoCPUthreads,center sampling,padding/windows/argmax/10mm margin,
native metrics and checkpoint selection.153members/23holds remain unchanged. Tiny/partial cases
are kept.001empty-mask history and D-311's sparse-target pressure motivate this gentler alternative.
Hypothesis: stronger background pressure reduces excess masks without violating coverage; null:
coverage fails or useful shrinkage remains unmet. Detached-logit direction is not a parameter update.
One retained control/treatment and known native variation do not prove general superiority orG5.

## Validity and resource gates

Version5 adapter/training identity, explicit new loss ID, new state codec/executor/evidence/launcher.
Old consumers reject new checkpoint identities and retain their declared recipes. Freeze a
machine-readable changed-factor record: only loss changes scientifically; necessary version/code
identities are declared. Synthetic arithmetic/finite-gradient/empty/sparse learning checks must pass.
Native invented MPS transaction must preserve parent state, absolute crops, reload next-update
parameters within1e-6/probes within1e-5, and refuse uncertain interrupted updates. Independently
recover every keeper with primary reads blocked. No invented member may be replaced by real data.

Separate fresh **zero-update** qualification:40pancreas references once,nooriginalCT,900s/16GiB
RSS+driver/1GiB localoutput,AC/exclusiveMPS/100GiB internalfree floor. All40 native007masks must
match exactly; imported weight digest must match and old terminal probe within1e-5. Session refuses
updates. Independently restore checkpoint/evaluation/qualification records. Refused qualification
does not permit training. Source/runtime drift invalidates qualification and requires new work.

After qualification, freeze a fresh training request:300new updates,233reference reads
(40initial+40middle+113train/40validation terminal),nooriginalCT,2700s **including recovery**,
16GiB RSS/driver,4GiB localoutput,AC/exclusiveMPS/100GiB free floor. Exact compressed/expanded
bytes and UUID-verified mount observations are frozen,not inferred from consumed010budgets.
Retain96MiB per-keeper/1GiB new-per-domain/20GiB backup ceilings. No dependency change.

## Evaluations and decisions

Checkpoints/evaluations at child0/150/300. Initial40native masks must again match007before any
update. Intermediate40validation; final113/40. Coverage active from0; stop if mean recall<0.95,
minimum<0.65, fewer than38/40boxes retain>=0.995coverage, or mean recall drops>0.03from the best
previous active boundary including imported0. Parent mismatch stops0. No filtering or later-stage
reads after a stop. Interrupted optimizer mutations poison the session and cannot be saved/reused.

Useful-shrinkage endpoint retains010's prospective parent-relative rule: median validation volume
<=13.872506x, ROI screens>=10/40, mean recall>=0.962700 and all40boxes retain>=0.995coverage.
Also report matched native Dice/recall/volume/box/crop changes against010at150/300, individual
regressions and actual prefix. Different loss values are not comparable scores of model quality.
Mandatory inspections: validation3115/2727/6534 and,if terminal training evaluation occurs,
training7604/7684/6110. Include strong/tiny/regressing cases without replacing members.

Complete run keeps three checkpoints,three evaluation records and terminal evidence, all
independently restored; verify every export and recompute guard/parent decisions. Native masks
remain reproducible local scratch, explicitly omitted from independent record keepers by hash.
Record hypothesis outcome and next decision in the living notebook before another experiment.
No automatic extension, model promotion,source rewrite,eligibility change,Git publication,
Claude dispatch,clinical claim or sealed-test use.009fresh replay remains held.
