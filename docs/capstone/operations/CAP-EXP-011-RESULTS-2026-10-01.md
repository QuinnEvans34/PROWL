# CAP-EXP-011 — useful shrinkage with a required coverage stop

The25/75class-mean CE comparison produced substantially smaller predictions and17/40ROI-screen
passes, but mean native reference recall fell below the agreed floor. The run stopped after
**150new updates**, not300. Updates151–300 and the terminal113-member training evaluation were
prevented. This is a valid stopped exploratory comparison, not a promoted model or a successful
complete300-update treatment.

D-312 authority: Quinton, “Great, continue with that. Great work.”
[Prospective design](CAP-EXP-011-LAUNCH-PLAN-2026-10-01.md),
[motivating audit](LOCALIZER-FOREGROUND-AUDIT-RESULTS-2026-10-01.md),
[retained control010](CAP-EXP-010-RESULTS-2026-10-01.md).

## Matched scientific comparison

Both010and011import the exact independent-backup007step300 model/AdamW state, preserving moments,
counters, RNG and old initial_lr0.0003. Both use constant0.00001, absolute sampler300–599, same
113train/40development-validation,144³/2mm cache, seed42,batch1,model,weight decay0.00001,padding,
inference/argmax/10mm margin/native metrics and0/150/300cadence.011changes only mixed-patch CE
class means from0.5foreground/0.5background to0.25/0.75, with the same foregroundDice. Empty
targets keep full-strength background mean CE/noDice;all-foreground targets keep full-strength
foreground mean CE+Dice. No cap50,threshold adjustment,support mask,negative sampler or filtering.

The required version5 code/config/checkpoint identities are declared necessary implementation
differences. Machine-readable changed-factor records match010's remaining plan/config fields.
All150executed sampling traces match010exactly. The new objective changes parameter gradients;
known native variation and a single retained control limit causal/generalization claims.
This is exploratory development evidence,not formalG5 or a replicated estimate of superiority.

|Mean native validation metric|Imported007parent|010control,150new|011treatment,150new|
|---|---:|---:|---:|
|Dice|0.098701|0.098067|0.140680|
|Reference recall|0.982700|0.984547|0.948096|
|Minimum reference recall|0.786705|0.795421|0.672303|
|Median prediction/reference volume ratio|18.496675x|18.906358x|12.853448x|
|ROI size+box-coverage screen passes|1/40|0/40|17/40|
|Boxes retaining>=0.995reference coverage|40/40|40/40|40/40|
|Mean acquired-scan crop fraction|0.421848|0.467199|0.301111|
|Empty predictions|0/40|0/40|0/40|

At the matched150boundary, all40Dice scores improve and all40prediction volumes shrink versus010;
38recall scores decline,none improve,two tie. Mean Dice gain0.042613 and mean recall loss0.036451.
Median volume is30.509%below the parent and32.015%below matched010. These are paired case results
and ratios of medians,not individual-case percentage averages. Predictions remain oversized.

## Why execution stopped

Coverage was active from imported0. At150:

- Mean recall0.948096is below the0.95floor.
- Mean recall fell0.034604from the best earlier active checkpoint0.982700,exceeding the0.03drop limit.
- Minimum0.672303passes the0.65floor;all40boxes pass,above the required38/40.

The two failed guards stop execution. Box coverage alone does not compensate for missed mask
voxels. No guard was relaxed after the result. Independent recovery recomputes the same stop.
The proposed utility endpoint was not completed: at this interim checkpoint,median volume and
ROI count reach their targets and all boxes pass,but mean recall misses the0.962700utility bar.
There is no full300-update outcome or new terminal training-cohort performance claim.

## Cases that explain the tradeoff

|Case|Matched010recall|011recall|Matched010volume ratio|011volume ratio|011ROI screen|
|---|---:|---:|---:|---:|---|
|6186,largest recall regression/minimum|0.920564|0.672303|28.144x|19.259x|Fail|
|3115,prior recall concern|0.795421|0.685326|17.686x|11.576x|Fail|
|5396|0.956242|0.828036|30.980x|18.531x|Fail|
|6534,prior screen success|0.982957|0.871806|16.260x|8.911x|Pass|
|2727,tiny boundary reference|1.000000|0.882353|6055.686x|3749.000x|Fail|

2727retains45/51native reference voxels and misses six;its reference remains in accounting.
6534demonstrates why an ROI screen is not contour acceptance:the crop retains the reference box
and is smaller,but its mask misses reference voxels. All original153members and23holds remain.
No held empty-reference case is promoted into a trusted negative.

Six three-row contact sheets were inspected: parent007,matched010at150,and011at150 on the same
cached CT/reference planes.6186/3115show foreground contraction alongside reference misses;
6534shows strong shrinkage with lower recall;2727retains an extremely small boundary reference
with substantial excess foreground;8847retains most reference overlap;1004shows strongerDice
with narrower foreground. Native metrics are authoritative;these selected processed-grid display
planes do not replace native evaluation. They are not contour certification or diagnostic claims.
No new6110/7604/7684training inspection was possible because terminal113-case evaluation never ran;
their earlier concerns remain unresolved. No supplemental model forwards or source reads were added.

## Implementation and native qualification

The dedicated `class_mean_loss` dispatch rejects old objective IDs. Separate version5 training,
executor,evidence,parity,reference and launcher/rehearsal modules retain older codecs;two shared
144³adapter/session modules add explicitly gated version5 behavior. New checkpoints are rejected
by old codecs. A pinned comparison record rejects undeclared factors or changed class-mean weights.
Consumed requests are refused before resource preflight. Original data/model source remains unchanged.

54new focused checks plus the existing suite: **1,706native tests pass**, two existing torch.jit
warnings. Independent formula/gradient tests cover sparse/dense/empty/all-foreground/extreme logits,
batch normalization, incorrect voxel-weight interpretation and sole-class scaling. Sparse/empty toy
learning verifies finite parameter gradients. Codec/history/ancestry/sampler/refusal/stop tests pass.
The first targeted test invocation had one stale expected CE value after its target changed;the
expectation was recomputed for the new target. Its failed log is retained;no real request existed.

Native invented MPS rehearsal:31.510s producer/13.934s recovery,peakRSS2.424GiB;seven independent
keepers restored with primary blocked,probes0,next weights1.862645e-9,interruption after optimizer
mutation refused. Fresh real **zero-update** qualification then reproduced all40parent masks,
three independent restores/probe0,97files/40exports verified.126.544s worker/140.925s total,
4.530GiB RSS/1.410GiB driver,40label reads/noCT. Training child0 repeats that exact40-mask check
before any update;its baseline metrics also match the retained control exactly.

## Actual compute and preservation

-150new updates/logical450,absolute sampler300–449,78foreground/72background centers. Child
  prefix exposes112/113train members:74once/38twice. The immutable cohort still includes113;
  combined parent+child exposure covers all113. No unseen member is removed or replaced.
-80actual training-stage label reads (40at0+40at150),9,824,370compressed/1,977,219,390expanded
  bytes,zerooriginalCT. The reserved final153reads were never opened. Qualification's separate40
  reads are not reused. Cached inputs and original references retain their distinct roles.
- Worker630.107s,total648.077s/10.801min including independent recovery. Peak monitoredRSS
  5.231GiB/sampled MPS driver4.853GiB,below2700s/16GiB. AC/exclusiveMPS/free-space/output/storage
  guards pass;native float32/no fallback/twoCPUthreads. No dependencies changed.
- Five keepers (checkpoints0/150,evaluation records0/150,stopped terminal) independently restored
  with primary reads blocked. Terminal probe difference0;parent/coverage/termination decisions
  replay exactly. Terminal weight digest
  `d0f34155bd2d3758dcdad3ea013413305b5d2d5eacc499ad59dbd6de8d9d9333`.
-192execution members and80native exports verified;33local review members/2,622,432bytes sealed,
  six selected sheets viewed. All150actual traces match010. Frozen production source/runtime
  unchanged after tests/qualification/launch. Local masks are derived scratch;independent keepers
  explicitly inventory omitted mask hashes rather than claiming those bytes were backed up.

|Evidence|SHA-256|
|---|---|
|Native invented producer receipt|`b13dbafd8a0053f5e35b4ccf32b45022f4b2b1c2344124071c203f5c5879a566`|
|Native invented recovery receipt|`bcce7d590d033ae8e0a480bb4b23bfce3dae23e3bca6cbdd933058899b23f21f`|
|Zero-update qualification request|`7575c72690540ff8992ccc45d6986a9296294b694d703b695e46102cc2ec2923`|
|Zero-update qualification receipt|`337187433952cf7aff0031cbf8db1cd37f4485930b7cf4c5c5fbf1864ab88d8c`|
|Training request|`562733c43722a5d3588f9f282ea0d26eb7431a8803a06c803f14ae3c31c2ef20`|
|Stopped execution receipt|`77fbe303affeda26694d94e74f4c3deec7eb0cf3811e20021191b83c972cd780`|
|Local review receipt|`b5f08446451a64381d0131775d1c2d4e279a13aa327850cf5f96437028ccd9f9`|
|Production source|`99a64ed0b4c68df4857bffc9c3be0f2685fd9359ea46f940dc79e23714c3fd07`|
|Runtime|`dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`|

Requests: `outputs/prowl/twomm-training-3ec13a6e-9f5d-4e03-9198-a18b79cf5b09` (qualification),
`outputs/prowl/twomm-training-6b94ab00-5a6e-4457-aa4a-fc434305daf0` (training),each with`-execution`.
Invented producer/recovery: `outputs/prowl/twomm-training-78b80f03-12e8-42fc-89f2-dcca1e878801` and
its`-recovery` sibling. Review: `outputs/prowl/CAP-EXP-011-review-20261001`,retaining methods,
paired-control/per-case/trajectory/assessment/inspection/source checks,test and launch logs/sheets.
Both real requests are consumed;no resume,automatic extension or replay.

## Next decision

The result supports class-mean balance as a useful factor under this parent/rate/crop setting,
with a real shrinkage/recall tradeoff. It does not justify relaxing coverage or promoting011.
Codex recommends **one gentler37.5/62.5 foreground/background class-mean comparison**, the midpoint
of the original50/50and tested25/75settings, with every other factor fixed. This would preserve
75%of original foreground CE pressure while increasing background CE pressure25%;011halved
foreground pressure and increased background pressure50%. It is an interpretable hypothesis,
not an optimal setting or predicted outcome.

[Next proposal](LOCALIZER-GENTLER-BALANCE-PROPOSAL-2026-10-01.md) requires a new decision/version,
synthetic/native recovery,real initial-mask qualification and fresh exact launch. No new run or
loss is adopted. FormalG5,lesion cascade and untouched evaluation remain separate work.
D-312 is finished with its required coverage stop;153members/23holds unchanged. No model promotion,
Git publication,Claude dispatch or pending training request.
