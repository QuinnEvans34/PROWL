# CAP-EXP-012 results — gentler class-mean balance

**Completed all 300 new updates; every coverage stop passed, but the prospective usefulness target failed.**
D-313 accepted the [37.5/62.5 proposal](LOCALIZER-GENTLER-BALANCE-PROPOSAL-2026-10-01.md) and
[exact bounded sequence](CAP-EXP-012-LAUNCH-PLAN-2026-10-01.md). No model adoption, extension or pending run.

## What the comparison answers

Import original 007 step 300 model and AdamW state from independent backup; change only mixed-class CE
from the control's 50/50 class means to 37.5 foreground/62.5 background. Sole-class CE and Dice unchanged.
Same constant 0.00001, 113 train/40 development-validation, 144³/2 mm, seed 42, batch 1, architecture,
normalization, padding, shuffle/crops, windows, argmax, 10 mm margin and native scoring. Child sampler 300–599,
logical 600; old progress, moments/counters/options/RNG preserved. All 300 actual crop traces match 010;
first 150 match 011. Version 6 identifies the new loss and checkpoint/plan/request codecs. No new source
CT arrays, augmentation, support mask, threshold, cap 50 or cohort change.

The midpoint preserves recall better than 011 at 150, while shrinking less. It eventually yields
15/40 usable crop screens, but misses the frozen utility bar. This is evidence of a real precision/
recall tradeoff, not evidence that another scalar weight or more updates will solve localization.
We should keep the cases and failures rather than filter them out or lower the thresholds.

## Matched native validation

|Metric|007 parent|010 at 150|011 at 150|012 at 150|010 at 300|012 at 300|
|---|---: |---: |---: |---: |---: |---: |
|Mean Dice|0.098701|0.098067|0.140680|0.116419|0.110417|0.129078|
|Mean reference recall|0.982700|0.984547|0.948096|0.973851|0.975863|0.962519|
|Minimum recall|0.786705|0.795421|0.672303|0.739173|0.706283|0.674440|
|Median prediction/reference volume|18.4967|18.9064|12.8534|15.8467|16.5411|14.2596|
|ROI size + box screen|1|0|17|1|2|15|
|Boxes retaining ≥.995 reference|40|40|40|40|40|39|
|Mean acquired-scan crop fraction|0.421848|0.467199|0.301111|0.389350|0.392427|0.316842|

011 stopped at 150; it has no 300 result. At matched 150, 012 recall improves in 38 cases/ties 2 versus 011,
while all 40 masks are larger and 39 Dice scores lower. Against 010 at 300, all 40 validation Dice scores
improve and all 40 masks shrink; 38 recalls decline/2 tie/none improve. Mean paired Dice gain 0.0186613,
mean recall loss 0.0133440. Relative to 007 parent, median volume drops 22.907%;
mean crop fraction 42.185%→31.684%. These are selected development comparisons, not held-out generalization.

## Stops and usefulness remain separate

All 0/150/300 coverage checks pass. At 300, mean recall 0.9625189266≥.95,
minimum 0.6744402262≥.65, 39/40 boxes meet .995≥38 required, and mean drop
0.0201811056≤.03 from the best active boundary 007 parent. No limit was relaxed.

|Prospective 300 endpoint rule|Actual|Outcome|
|---|---: |---|
|Median volume ≤13.8725059808 x|14.2595778200 x|Fail|
|ROI screens ≥10/40|15/40|Pass|
|Mean recall ≥.9627000322|0.9625189266|Fail|
|All 40 boxes retain ≥.995 reference|39/40|Fail|

Recall misses its utility threshold by 0.000181106, about 0.0181 percentage points; the exact criterion
still fails. Volume and box criteria fail independently. A passing stop means the bounded run may
finish; it does not mean its model is useful or accepted. No promotion or automatic continuation.

Terminal training: mean Dice 0.126738, recall 0.968681, minimum 0.463016,
median volume 13.5089 x, ROI 36/113, boxes 110/113.
Against 010 at 300, 112 training Dice scores improve/1 declines; all 113 masks shrink, 104 recalls decline/9 tie.
Child exposure counts: 54 members twice, 44 three times, 15 four times. Combined original+child 600 updates
cover every 113 member: 78 five times/35 six times. Centers 155 foreground/145 background. No member replaced.

## Failures and selected inspection

Thirteen three-row contact sheets were viewed: 6186, 3115, 8847, 1004, 6534, 2727, 6110, 7604, 7684,
5641, 756, 6822, 150. Same retained processed-cache CT/reference, three orthogonal planes; parent 007,
control 010 and treatment 012 native exports projected only for display. Native full-volume metrics
govern; these views are not full expert adjudication. No source-grid mismatch apparent on selected
planes. Broad excess foreground and some missed reference remain visible.

|Case / role|010 recall→012 recall|012 box coverage|Why retained|
|---|---|---: |---|
|3115 / validation|.706283→.674440|.990587|Worst validation recall; new box failure below.995|
|6186 / validation|.883786→.747615|1.0|Largest validation recall decline; ROI screen passes despite mask deficit|
|6534 / validation|.974758→.927913|1.0|ROI screen passes; contour is not certified|
|2727 / validation|47/51→46/51 voxels|1.0|Tiny reference, volume 4091.35 x, crop 42.42%; boundary case preserved|
|6110 / training|1.0→1.0|1.0|Tiny reference fully recalled but volume 705.69 x/crop 42.63%still fails size screen|
|7604 / training|.784040→.771115|.860597|Persistent inherited box deficit|
|7684 / training|.923637→.908301|1.0|Volume 25.86 x/crop 42.5%remain oversized|
|756 / training|.832947→.816665|.975844|New training box deficit|
|6822 / training|.844814→.744671|.973284|New training box deficit|
|150 / training|.706174→.463016|1.0|Only training Dice regression, worst training recall; covering box hides mask loss|

The native count arithmetic, descriptor/transform/reference pins, acquired-scan denominator and
all 233 exports were independently replayed. All 502 execution files rehashed. Initial 40 metrics and
native masks exactly match 007 parent. Thirteen views and the [validation trajectory chart](../../../outputs/prowl/CAP-EXP-012-review-20261001/validation-trajectories.png)
are retained with inspection notes and machine-readable pairs. Chart uses actual boundaries only.
The experiment environment lacks Matplotlib; its failed plotting attempts were preserved and the
chart was produced with bundled ReportLab charts/SVG and sharp. No package was installed or changed.

## Implementation, qualification and recovery

- 1,763 native tests pass, 57 new, twoexisting torch.jit warnings. Independent stable-logit formula/
  gradients, mixed/sole-class/empty/sparse learning, old-codec refusal, parent state preservation,
  absolute sampler, identity/changed-factor forgery refusal, scope and consumed-request checks.
- Two shared mechanics modules add gated version 6 support; eight new production modules plus three
  test files. Prior data/model/loss modules unchanged; all other 010 plan fields remain equal.
- Native invented producer 29.491 s/recovery 14.672 s: seven independent keepers,
  primary reads blocked, probes 0, nextweights 1.862645149e-09, interrupted mutation
  refused for save/reuse. Source/runtime matched before real qualification.
- Real zero-update qualification: 40 fresh labels, noCT; all 40 native parent masks exact, three independent
  restores/probe 0, 97 files/40 exports checked. Worker 129.394 s, total 144.740 s,
  RSS 4.673 GiB, driver 1.410 GiB.
- Real training/evaluation/recovery: 1497.078 s worker, 1518.694 s
  total/25.312 min, peakRSS 6.252 GiB/driver 4.853 GiB. Within 2700 s/16 GiB/4 GiB and
  registered keeper quotas; AC/exclusiveMPS/100 GiBfree supervisor remained active.
- Actual 233 fresh native label reads, 31,766,649 compressed/6,376,087,421 expanded bytes, nooriginalCT;
  all three stages completed. Seven production keepers independently restored with primary blocked,
  terminalprobe 0, coverage/parent decisions and checkpoint/evaluation references replayed.
  Derived masks remain local reproducible scratch; independent keepers explicitly omit those bytes
  while retaining hashes/checkpoints/evaluation/control records. Do not claim masks were backed up.

## Immutable evidence

|Record|Path underoutputs/prowl|SHA-256|
|---|---|---|
|Native producer|`twomm-training-92a4a8d6-5105-473f-bace-ef1d248b5e41`|`d2ea23a202cedc1b317d6e16eb452872a94f99128f780f425bdfa6f37cdb5c83`|
|Native independent recovery|`twomm-training-92a4a8d6-5105-473f-bace-ef1d248b5e41-recovery`|`3e409b2d4fac128ba2a5eac89ece919d07582a59b9b46b9f8885b503217621fb`|
|Zero-update request|`twomm-training-febb98c7-41e0-45b7-9025-25d878b8a96c`|`49afaf63e44fb057ad55c5dd999f27e6e5211d6d4ca12623e3b026aa53934406`|
|Qualification execution|`twomm-training-febb98c7-41e0-45b7-9025-25d878b8a96c-execution`|`bcb8064fe24f86ff55885ca18442d18a2bf4cdda0d1864632efd1ac354057f12`|
|Training request|`twomm-training-a0636d70-2ea5-4e5f-9167-db28bff562ba`|`06cecda421626271eeb6fae5f02679d7fc9650b5afd0861ce39fce5ed0612218`|
|Training execution|`twomm-training-a0636d70-2ea5-4e5f-9167-db28bff562ba-execution`|`2ca47e685f28d8007c34db51410482dc77b5b34da56598f4a645314ef1991926`|
|Review, 52 members/6,063,791 bytes|`CAP-EXP-012-review-20261001`|`9f69df5f1d80acf845f89fde52fa6cc4b06a5ca9ac9a78f055b3e8be097e78a6`|

Qualification approval`736d364ec9a49c0ce0b932232cbaf63eb508d2e8e47717dd01c0ee10e4cddfe8`, training approval`4ea46c04f41c22c8fafa89f86a3ddaf75a31c7d9e9effc611406d08cfe772920` bind Quinton's
existing D-313 design acceptance to final generated requests; they do not claim he reviewed bytes
before creation. Source`94b77f49fb18ce3547a91a32d08bd52a787c6f8f86441cfbbd0d0d7a31b9293d`, runtime`dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31` unchanged since freeze.
Terminal model SHA`afeac3a083b8272d23217ff4571ab2b81c61808c93244166fc2589bfa232fbc6`. All review members rehashed after sealing.

## Recommended next discussion

Avoid another loss-weight guess or automatic extension. First timebox a retained-prediction
structure audit: what fraction of foreground is diffuse versus disconnected, and which regions
control box extent? Pair that explanation with the retained 3115/150/756/6822/7604 failures.
This is a recommendation, not a prepared request or adopted component/threshold policy. Structural
mask analysis alone cannot establish component-level reference retention; that would need a fresh,
qualified native-reference scoring scope. Do not recycle consumed label-read allowances.

Keep the broader capstone moving: prepare the small Stage 2 lesion-target qualification/cascade
slice in the [strategy regroup](STRATEGY-REGROUP-2026-10-01.md), without calling 012 a suitable localizer.
A provided-pancreas ROI diagnostic and an autonomous predicted ROI must remain separate identities;
no oracle repair or silent whole-volume fallback. Stage 2 qualification is not inherited from
pancreas-localizer permission. We need useful localization and the lesion/review workflow, not just
more variants of the same shrinkage tradeoff.

Both real requests consumed; no active/pending run, resume, extension, promotion, eligibility change,
Git publication or Claude dispatch.153 qualified members/23 holds and sealed holdout unchanged.
