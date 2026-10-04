# CAP-EXP-008 — stopped at 300 updates under the coverage guard

Follow-up: [D-308 optimization findings](CAP-EXP-008-OPTIMIZATION-FINDINGS-2026-10-01.md) and
[proposed next schedule](LOCALIZER-SCHEDULE-NEXT-PROPOSAL-2026-10-01.md). These do not alter this run.

Quinton authorized this fresh duration/schedule diagnostic under D-307. The exact replacement
request ran once and stopped after its first active coverage review at update 300. **The planned
1,200 updates were not completed.** The stopped transaction, checkpoint preservation, native
exports and independent recovery verified successfully. The model did not meet the coverage
safeguards or improve the prior run's excess foreground. No run remains active or pending.

## What ran and why it stopped

The same 113 training / 40 development-validation members, frozen 2 mm cache and 144³ patch geometry
were used. Fresh seed42 SegResNet, balanced CE + foreground Dice, AdamW LR0.0003/weight decay0.00001,
MPS float32/fallback disabled, two CPU threads and no loader workers remain fixed. Cosine decay
was extended to a horizon of 1,200. [Frozen design](CAP-EXP-008-LAUNCH-PLAN-2026-10-01.md).

At update300, mean native validation recall0.911146 fell below0.95 and minimum recall0.055399 fell
below0.65. These two predeclared conditions caused `stopped_coverage_guard`. All40 boxes met the
>=0.995 reference-coverage condition. Step0 was correctly treated as warmup. There was no earlier
active checkpoint for the trajectory-drop condition. The checkpoint and evaluation records were
kept before stopping; no600/900/1200 stage or automatic continuation was executed.

300updates gave39 cases two exposures and74 three, with146 foreground /154 background sampling
centers. Every training member appears once in each complete113-case pass. All300 case-order,
pass and crop traces match CAP-EXP-007. No validation case entered the optimizer. All153 initial
metric records exactly match D-304. These checks support the comparison without implying a
formal generalization result. All176 original candidates and23 holds remain preserved.

## Native-grid comparison

Means are per case. Both update300 columns below use the same40 development-validation cases and
native visible-pancreas references. This is a duration/schedule diagnostic: changing the cosine
horizon changes the LR history, so it is not a duration-only experiment or the formal G5 comparison.

| Validation40 metric | CAP-EXP-007, horizon300 | CAP-EXP-008, horizon1200, stopped300 |
|---|---:|---:|
| Mean Dice |0.098701|0.077905|
| Mean reference recall |0.982700|0.911146|
| Minimum case recall |0.786705|0.055399|
| Median prediction/reference volume |18.497x|23.738x|
| Mean acquired-scan crop fraction |0.421848|0.409796|
| Box-reference coverage passes |40/40|40/40|
| Joint coverage/size ROI-screen passes |1/40|2/40|
| Recorded LR after update300 |0|0.000256066|

38/40 Dice scores decreased and2 increased. Recall decreased in22, increased in15 and remained
unchanged in3. All40 predictions remain nonempty. The slightly smaller average crop and one extra
ROI-screen pass do not establish a better localizer: median predicted volume is larger and mask
recall is lower. A large, scattered mask can form a covering box while missing reference pixels;
box coverage alone therefore did not catch this run's failures. Keep both measurements.

The initialized train/validation means remain Dice0.001700/0.002053 and recall0.018415/0.024605.
There is **no post-update full training-cohort evaluation**: the guard stopped before the planned
terminal training stage. Do not report a new training Dice, assess train/validation gaps, or claim
training7604/6110 improved. Their prior evidence remains intact.

First/last25-update median patch losses were1.440335/1.117138, compared with1.438248/1.145623 in
CAP-EXP-007. First and last patches differ; these are descriptive traces rather than matched loss
tests. Lower patch loss accompanied worse validation coverage. At300 the new recorded LR remains
85.36% of its initial value. The result supports investigating schedule sensitivity, but does not
establish that LR alone caused the failures. Benefit from updates301–1200 remains untested.

Tiny references remain in all applicable statistics. Mean validation volume ratio189.061x is much
larger than median23.738x; interpret those together. References describe visible annotated pancreas,
not whole-organ completeness. Development-validation is repeatedly used for development and is
not a sealed test. No lesion containment, Stage2 performance or clinical claim follows.

## Retained failures and selected inspection

Seven selected sheets were viewed: worst-recall6186/6727, near-median-Dice/former-ROI-pass6534,
best-Dice1004, tiny2727, and current ROI-pass7687/2573. Each shows retained cached CT/reference and
native predictions projected to2mm for display only. No additional source reads or model forwards
were used. This is selected-plane inspection, not exhaustive visual review or expert certification.

- 6186: recall0.055399 versus0.897549 previously; Dice0.003401 and volume31.578x. Selected planes
  show substantial missed reference alongside large separate prediction regions.
- 6727: recall0.668611 versus0.999369; missed reference and excess foreground remain visible.
- 6534: recall0.676842 versus0.990141; crop fraction0.335488 versus0.239329. The prior sole
  validation ROI-screen pass now fails the size screen.
- 1004: best Dice0.182243, recall0.970908, but volume9.655x and visibly extensive excess.
- 2727: recall1.0, Dice0.000304, volume6567.451x; the tiny reference is retained, not filtered.
- 7687/2573: boxes pass the ROI screen, but masks remain29.857x/29.659x reference volume.

[Inspection notes](../../../outputs/prowl/CAP-EXP-008-review-20261001/inspection.md) record the exact
scope. The planned terminal inspection of training7604 is deferred because the training evaluation
stage was never reached. No unbudgeted evaluation was added to fill that gap.

## Implementation, attempts and verification

Separate adapter/training/plan/request versions2 support the bounded1,200 horizon and honest stopped
outcomes; version1's300-update limit and inference-only readiness remain unchanged. Coverage decisions
are derived from every checked validation record, journaled, independently reconstructed after
restore, and bound to the completed read/evaluation prefix. A stopped session cannot be reused.

Attempt01 failed at step0 before the first original-label byte read or optimizer update. One cached
prediction export, step0 checkpoint, failed journal and consumed request remain preserved. macOS had
remounted the registered APFS volume: retained device16777239, live16777243. Metadata-only checks
found all153 label inodes, sizes, mtimes and ctimes unchanged, with the same registered volume UUID.

The bounded replacement froze a153-file mount observation and used a separate UUID-verified reader
that substitutes only the live device in a temporary observation. Original inventory/descriptors,
cohorts and cache bytes remain unchanged. No-follow checks, every other stat field, pre/post-read
checks, compressed hashes, binary decoding and geometry checks remain enforced. Mid-attempt mount
changes are refused; the default/version1 reader still rejects device drift. Successful reads verified
all153 baseline compressed source hashes. The first consumed request was not replayed.

After the repair, **1,574 native tests passed**, with the two pre-existing torch.jit warnings. New
regressions exercise horizon limits, stopped-prefix accounting, guard failures, keeper validation,
interruption refusal, altered source metadata/content, launch mount drift and mid-read remounts.
Final source-matched synthetic MPS producer/recovery workers took45.174s, peakRSS2.551GiB and sampled
driver4.853GiB. Prediction probes were exact, next-update weights differed by7.45e-9, and an
interrupted update was refused.51 rehearsal package files were independently rehashed.

## Actual execution and independent recovery

| Item | Verified result |
|---|---:|
| Actual / planned updates |300 /1200|
| Worker time |1352.982s|
| Total supervised launch + recovery |1363.738s /22.729min, below90min|
| Peak process RSS |5,582,929,920bytes /5.200GiB|
| Peak sampled MPS driver |5,152,505,856bytes /4.799GiB|
| Original pancreas-reference reads |193 =153baseline +40at300|
| Compressed / expanded reference bytes |26,854,464 /5,387,477,726|
| Original CT reads |0|
| Checkpoint / evaluation / terminal keepers |2 /2 /1 =5|
| Independent restores with primary reads blocked |5|
| Restored terminal prediction probe maximum difference |0|
| Sealed execution package files rehashed |415|
| Native exports independently rechecked |193|
| Sealed execution member bytes |203,421,226|
| Review members / selected sheets viewed |33 /7|

All193 per-case counts, native geometry, crop arithmetic, decoder counts, hashes and memberships were
verified from retained records, without another source-label pass. Both source/environment and live
mount checks passed at worker end; a later read-only check also confirmed exact frozen source/runtime
bytes. No post-freeze source/dependency change or resource interruption occurred. No new qualification,
source rewrite, threshold tuning, model promotion, Git publication or Claude work occurred.

The five independently restored keepers protect checkpoints, evaluation records and terminal journal.
Native masks and review figures remain derived local scratch; they are not independent mask backups.
Only the artifacts actually restored are covered by the recovery claim.

## Immutable references

Attempt01 request:`outputs/prowl/twomm-training-ec57d6ba-4027-4f3b-876e-c505d21023be`, SHA
`294c26b867903a99f8598ee6f904639073864f3f9f83f220eac31f8ea73e624e`.
Its consumed/failed evidence is preserved in that execution directory and the review package.

Attempt02 request:`outputs/prowl/twomm-training-068616f8-c4f1-491c-b415-e0542ddb328a`, SHA
`843fd09a1a7a7283a989c8644ea86cfe591b1a49f5f2dde90812b13eab283ba9`.
Authorization:`outputs/prowl/CAP-EXP-008-ATTEMPT02-APPROVAL-2026-10-01.json`, SHA
`63097f48e9d07d75994c40a2666743b28e8afd37eaeb768b34fade3002872131`.
Mount observation:`a79e2a218a5f395229dfa61cfa6040d09b8c0a50499146ef7e654195bb8dadbc`.

Execution:request prefix plus`-execution`; receipt SHA
`fc833dc461fb365ebc9064fa9513249b789f77441108899a3ac833aa19af0cb8`.
Terminal checkpoint:`twomm-training-068616f8-c4f1-491c-b415-e0542ddb328a:step:300`;
primary receipt:`c7e0cbc86eb0229be01438778bdb3cf47c2f1489c3170dcf0bb0cdc915d89227`;
backup receipt:`e0fec4d9bcc5a7a30321a248ff690f5cf4e6440d917c55d38bc2857f9b6536b7`.

Review:`outputs/prowl/CAP-EXP-008-review-20261001`; receipt SHA
`0a6d2c480ed3c641da9205e3339b81f9cfa33673fa6ff633be75d81af7028b24`.
The review includes all193 case records, all300 updates, paired40-case comparison, verification logs,
attempt/remount evidence, final native test/rehearsal summaries, source check and seven selected sheets.
Frozen source SHA:`436c350c26dd3cd5359ffd336961e604d50fa5c487898f3a1a0708e0adb32b02`;
environment SHA:`dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.

## Next discussion

Keep CAP-EXP-007 as the stronger retained coverage reference, without promoting it. Before allocating
a larger duration budget, review a fresh schedule comparison that retains its earlier decay behavior,
alongside patch-level loss/sampling evidence. Do not relax the guards after observing this failure,
remove difficult cases or resume this stopped request. A next experiment needs a new design and
single-use request. CAP-EXP-008 establishes schedule sensitivity at300; longer training remains an
open question. The broader lesion cascade and formal comparative evaluation remain separate work.
