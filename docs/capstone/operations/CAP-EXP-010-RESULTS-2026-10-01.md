# CAP-EXP-010 — low-rate tail helps modestly; excess foreground remains

D-310's approved parented diagnostic completed all300 new updates at fixed0.00001. It started
from independently backed-up CAP-EXP-007 step300 with exact model/AdamW history, then used sampler
indices300–599. All coverage safeguards passed. Validation Dice improved in40/40 cases and all40
prediction volumes decreased, but median volume fell only10.57% and only2/40 crops pass the joint
coverage/size screen. The predeclared useful-shrinkage target was not met. No model is promoted;
no run, extension or continuation is pending. Both new requests are consumed.

[Exact design and qualification references](CAP-EXP-010-LAUNCH-PLAN-2026-10-01.md).
[Next proposed investigation](LOCALIZER-FOREGROUND-NEXT-PROPOSAL-2026-10-01.md).
CAP-EXP-009's fresh-prefix design remains held; this experiment does not relax its failed native
parity bound or rewrite any consumed request. Same113train/40development-validation,144³/2mm,
SegResNet, balancedCE+foregroundDice, AdamW decay0.00001, sampling/windows/argmax/10mm margin.
All153 qualified members,176 original candidates and23 holds remain unchanged.

## What the comparison shows

Means are per case; volume is prediction/reference voxel count on the native acquired grid.
Child0 is the exact imported007step300, child150 is logical450, child300 is logical600.

| Validation40 metric | Imported parent |150 new updates|300 new updates|
|---|---:|---:|---:|
| Mean Dice |0.098701|0.098067|0.110417|
| Mean reference recall |0.982700|0.984547|0.975863|
| Minimum case recall |0.786705|0.795421|0.706283|
| Median prediction/reference volume |18.497x|18.906x|16.541x|
| Mean acquired-scan crop fraction |0.421848|0.467199|0.392427|
| Box coverage passes |40/40|40/40|40/40|
| Joint coverage/size ROI-screen passes |1/40|0/40|2/40|
| Empty predictions |0|0|0|

All40 validation Dice scores improve at the final boundary, with mean gain0.011716. Recall improves
in14, worsens in21 and is unchanged in5. Mean recall falls0.006837 from the parent; the worst
individual drop is0.080421 in3115. All40 native masks shrink, but a smaller mask does not guarantee
a smaller or sufficient crop. For example,1004's crop fraction grows while its mask shrinks.

Coverage is active from child0, with mean>=.95, minimum>=.65,>=38/40 boxes at>=.995 coverage and
no drop>.03 from the best earlier active mean. All three boundaries pass. Final mean0.975863 is
0.008684 below the halfway best, within the declared trajectory bound. No rule was changed after
observing results. Passing this guard is distinct from meeting the usefulness target.

Useful shrinkage required median volume<=13.873x,ROI>=10/40,mean recall>=.9627 and all40 boxes.
The first two conditions fail; the latter two pass. Thus the low-rate tail provides a modest
improvement with preserved aggregate coverage, not a sufficient localizer or an optimal-rate claim.
Mean volume ratio146.117x remains much larger than median16.541x because tiny references are retained.

Final training113 mean Dice0.108541/recall0.979678 versus parent0.097323/0.978471; median volume16.328x,
ROI2/113,box coverage112/113. Dice improves in112/113 and volume decreases in111/113. The sole training
Dice regression is7684 (0.062661→0.057699). These modest changes occur in both cohorts; this run alone
does not establish a generalization result, determine a best loss/rate or diagnose overfitting.
Repeated development-validation use is not a sealed test. Visible-reference scores do not assert
whole-organ completeness, lesion containment, downstream cascade performance or clinical accuracy.

## Retained concerns and inspection

Ten paired sheets were viewed:3115,6081,1004,6186,6534,2727,6110,7604,7684 and5641. They use retained
processed CT/reference, with native masks projected by nearest neighbor for display only. Selected
reference-median planes show modest shrinkage alongside extensive excess and remaining misses.
This is selected-plane inspection, not exhaustive review or expert certification.

- 3115: final minimum recall0.706283, down from0.786705, while Dice rises0.082795→0.089022.
- 2727:51-voxel native reference retained; four voxels missed, recall1.0→0.921569; volume5087.922x.
- 6110: full reference recall retained, but prediction remains875.647x its tiny training reference.
- 7604: its already failing training box coverage worsens to0.860597 despite a small Dice gain;
  its native mask recall falls0.7901→0.7840. It remains in the cohort and all reports.
- 7684: training Dice/recall regress and volume grows; no replacement or omission.
- 6534: the prior sole validation ROI-screen success now fails the size condition at0.253393.
- 5641/8855: the two current validation ROI-screen successes still have mask volumes8.764x/10.769x.

[Inspection notes](../../../outputs/prowl/CAP-EXP-010-review-20261001/inspection.md) and
`visual-selection.json` record exact scopes/hashes. Derived masks/figures remain local scratch;
independent checkpoint/evaluation keepers explicitly inventory their omitted mask hashes.

## Sampler and objective checks

The child preserves the parent's weights, AdamW moments/counters/options and initial_lr0.0003,
changes only next/applied LR to0.00001 and uses a bounded constant scheduler. All300 recorded used
and next rates equal0.00001; the final optimizer counters are logical600. Parent progress is immutable.
Every child member/pass/offset and recorded crop trace matches the absolute sampler sequence.

Starting mid-pass gives54 cases two child patches,44 three and15 four. Combining parent and child
gives78 cases five patches and35 six, with all113 represented. These are sampled patch exposures,
not600 epochs. No validation member enters an optimizer update.

A bounded CPU replay verifies all300 actual crops from the retained role cache, with no original
source reads, model forwards or updates.155 centers are foreground and145 background, but290/300
patches contain reference foreground. Only10 are fully empty. Median target fraction0.302982%,
padding31.25%,positive-patch foreground/background CE coefficient ratio324.643. Replay118.085s,
peakRSS2.212GiB. These are observations, not proof that balancing or negative exposure caused excess.

First/last25-update median patch losses1.154121/1.123975 are descriptive; the patches differ.
The tail's total applied-rate sum is0.003. Additional updates, changing sampled patches and their
low rate act together. Without a matched alternative tail, this does not establish a rate-only
causal effect. The exact parent start avoids the fresh-prefix qualification problem, but does not
claim deterministic equality across arbitrary fresh native training repeats.

## Implementation and verification

Separate version4 child identity/adapter/session/payload, executor, parent-mask check, evidence,
reference consumer and single-use launcher preserve older behavior/caps. Qualification mode refuses
updates. Tests cover exact state import, forged parents/moments/history/RNG, absolute sampler bounds,
constant scheduler/counters, purpose/phase/role denial, mask mismatch, interruption and scope drift.
**1,652 native tests pass**, with two existing torch.jit warnings; no dependency changes.

Source-matched invented MPS rehearsal passes: seven independent keeper restores with primary blocked,
probes0,next-update weights1.862645e-9, interrupted mutation refused. Producer/recovery27.742/13.964s,
peakRSS2.423GiB/driver4.853GiB. Before real updates, separate zero-update qualification reproduces all40
native parent masks exactly, validates imported weights/moments and old probe within1e-5, independently
restores three keepers/probe0.40 references/noCT,126.535s worker/141.998s total,4.931GiB RSS.
Its97 files/40 native exports are independently rechecked.

The training attempt repeats exact40-mask parent verification and active coverage at child0 before
updates. All checkpoint/evaluation/terminal records are kept; independent recovery reconstructs every
coverage and parent decision, verifies ancestry/weights/progress/probe, with primary reads blocked.
No production source/runtime drift occurred after native qualification. An initial preparation command
with relative rehearsal paths was refused before a request existed; corrected absolute paths were used.
No real worker failure, replay, restart, automatic extension or resource stop occurred.

| Training execution / review item |Verified result|
|---|---:|
| New / logical completed updates |300 /600|
| Training worker time |1515.001s|
| Total supervised launch + independent recovery |1536.013s /25.600min, below45min|
| Peak process RSS |6,322,225,152bytes /5.888GiB|
| Peak sampled MPS driver |5,211,226,112bytes /4.853GiB|
| Original pancreas-reference reads |233 =40+40+153|
| Compressed / expanded reference bytes |31,766,649 /6,376,087,421|
| Original CT reads |0|
| Checkpoint / evaluation / terminal keepers |3 /3 /1 =7|
| Independent restores with primary blocked |7|
| Restored terminal probe maximum difference |0|
| Sealed execution files independently rehashed |501|
| Native exports independently checked |233|
| Sealed execution member bytes |88,610,879|
| Selected paired sheets viewed |10|

Every retained per-case decoder count, target hash, geometry, metric/crop arithmetic and membership
was checked without another original-label pass. Two separate scopes consumed273 total reference
reads including qualification, zero originalCT reads. Source/mount/runtime checks pass at worker end;
later source/runtime capture is byte-exact. Backups cover the seven keepers, not independent mask copies.

## Immutable references

Parent reference:`outputs/prowl/CAP-EXP-010-preparation-20261001/parent-reference.json`, SHA
`969d86b898e90ff8c5afc340c336588f5f757615409feb12bf8f975948f4d5cc`.
Qualification request:`twomm-training-422156cf-1654-45b1-abf0-6230e6c2fd8a`, request SHA
`7ed04c3e1c32a9c085921dcb04b5338c488f7d3bb6059986467b63569b6b288c`, execution receipt
`3f2c561741c58784de081f9ea4166b855ab16d0015ce515e9e15ab9868a0e45b`.

Training request:`outputs/prowl/twomm-training-a2593f26-59b6-4582-947d-582bfed6928f`, request SHA
`f37f07ad891ea29406e099f1b46d15188e4eb748dcbd295f31fc6b263a796562`. D-310 authorization SHA
`e8405df86cf6baf40e54d5e1628dd5373d8072b14867a795ef6225689a52c7bd`.
Execution:request prefix plus`-execution`, receipt
`84a16cc4e39409140404e8639daead08abce7fce9fee9f400effdccef548eee8`.
Terminal checkpoint:`twomm-training-a2593f26-59b6-4582-947d-582bfed6928f:step:300`, primary receipt
`045273d7a1ac42c1f3be1b2ce002f8abc641da94771b3f599ef96b8385fefd54`, backup receipt
`b235e6786476a7f7188fefb6b61ada6c7f8c83bcab66dcd91eec8c7dffaa0466`.

Review:`outputs/prowl/CAP-EXP-010-review-20261001` contains all233 records,300 updates, paired40-case
comparison, qualification/source checks, exact crop replay, methods/logs and ten selected sheets.
Source SHA `0c857972139c44f561d0c338c6dbdf922920abd9b967423bc9b905c2ed5f08fc`, runtime SHA
`dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.
Review receipt `4055ed5addbac03f06f3f6c6ac973b6170fe1975f1e6a46d952ad29aad3e88c1` seals27 members,
3,477,173bytes, including the exact replay and selected inspection. All27 members rehashed.

## Recommendation

Retain both007 and010 as research evidence;010 improves overlap modestly,007 has higher minimum
validation recall and better7604 box coverage. Neither is sufficient for promotion. Before longer
training, inspect objective pressure and negative-patch exposure on a fixed bounded patch set, then
prepare one controlled foreground/loss comparison. Keep difficult/tiny cases and numeric coverage
safeguards. No new loss, cohort filter, threshold, training request or formalG5 result is adopted here.
