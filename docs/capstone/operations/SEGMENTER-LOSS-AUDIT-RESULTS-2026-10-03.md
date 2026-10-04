# D-329 — measured loss imbalance and next candidate

The training-only zero-update audit completed all24 observations: six retained training members at CAP-EXP-013 steps0/6/24/48. **CE pushes the pancreas output bias downward in every observation; Dice pushes it upward but is too small to reverse the sum.** This materially strengthens the loss-balance hypothesis. It does not prove that reweighting will fix real learning or predict AdamW's complete update.

Authority: Quinton's “Great, continue on” following the CAP-EXP-013 follow-up; [prospective plan](SEGMENTER-LOSS-AUDIT-PLAN-2026-10-03.md). No optimizer calls, original CT/target payload opens, validation model evaluations, model/optimizer/RNG mutation, imported initialization, eligibility changes or accepted producer edits occurred. CAP-EXP-013 remains completed/consumed with terminal48 primary. Six/one cohorts, all12 candidates/five holds and localizer153/23 remain fixed.

## What the gradients show

|Saved step|Mean CE / Dice scalar|Mean CE:Dice head norm ratio*|Mean pancreas bias gradient, CE / Dice|Pancreas predicted voxels / TP across6|
|---:|---:|---:|---:|---:|
|0|1.256426 /0.976155|51.50|+0.378104 /−0.000939|13,275,068 /220,723|
|6|0.750454 /0.973375|25.77|+0.262958 /−0.001234|381 /0|
|24|0.710252 /0.975235|22.06|+0.241593 /−0.001758|1 /0|
|48|0.507576 /0.977747|16.44|+0.190048 /−0.002756|0 /0|

*Mean of six per-case CE/Dice final-convolution gradient norm ratios, not a ratio of mean gradients. Individual ratios range11.53–84.09. Positive bias gradient means ordinary gradient descent would reduce that class's bias; measured bias components are not the whole head-weight/backbone gradient or AdamW update. All24 total pancreas bias gradients remain positive; CE and Dice scalar sizes alone hide this difference in parameter pressure.

By step6,68.1–99.9% of true pancreas voxels are predicted as lesion, depending on case. At48 the range is68.7–95.4%. The output channel remains finite; it loses class competition. These are cached tensor diagnostics, not original-native segmentation metrics. D-328's native results remain authoritative for contour quality.

Every row retains exact class counts/weighted denominator, classwise CE terms, present-class Dice, conditional probabilities/margins,3×3confusion, CE/Dice/total logit-gradient statistics by true/output class, and all51 final-head weight/bias components. The scalar decomposition matches the accepted v3 objective within2e-5; CPU invented analytic gradients match autograd and native144³ analytic maximum error3.64e-12. GroupNorm/no-dropout train/eval parity is checked on invented CPU inputs. Analysis clones have gradients enabled only on the output convolution; this does not profile full-backbone training.

## One provisional factor to qualify

The [predeclared arithmetic screen](SEGMENTER-LOSS-CANDIDATE-SCREEN-2026-10-03.md) compared pancreas weights16/32/64 while holding background1,lesion256 and Dice fixed. It rescaled saved true-class CE contributions/logit-gradient sums; it made zero additional model evaluations or input reads. Current bias reconstruction agrees with measured autograd within6.11e-8.

|CE weights|Early observations with upward pancreas-bias descent signal, at0/6|
|---|---:|
|[1,1,256] current|0/12|
|[1,16,256]|0/12|
|[1,32,256]|6/12|
|[1,64,256]|12/12|

**Provisional next candidate: `[1,64,256]`.** It changes one named loss factor and raises pancreas's weighted CE denominator share from1.11–1.99% to41.90–56.48%. Relative lesion/background pressure drops, including the tiny lesion's contribution; this tradeoff must pass explicit learning tests. The screen establishes bias arithmetic at fixed logits, not full head-weight gradients, learned accuracy or validation performance. The candidate is not yet accepted for training. [Next qualification packet](SEGMENTER-LOSS-REBALANCE-QUALIFICATION-PACKET-2026-10-03.md) preserves the original synthetic pancreas/tiny-lesion/negative bars, then calls for native resource/recovery checks before a separate fresh exact real launch.

## Execution, verification and retained faults

26new tests; **2,600 native tests pass**, two existing PyTorch deprecation warnings,98.72s. Initial invented profile passed; a prelaunch wrapper fault printed canonical's newline-inclusive hash instead of the saved request bytes' hash. SHA verification refused it before consumption/cache/model reads. The first request/profile and byte-exact first-wrapper snapshot remain preserved. A persisted-byte regression fixes the wrapper; a distinct attempt02 profile/request was qualified. No consumed diagnostic was retried.

Final invented144³ profile: six forwards/12head VJPs plus two analytic-logit oracle queries, zero optimizer calls. Real attempt02:24forwards/48CE-and-Dice head VJPs, zero optimizer calls/original payload reads/validation evaluations; all original checkpoint transactions unchanged. Worker200.359s, supervision202.195s; peak RSS1,788,379,136B (1.666GiB), sampled driver1,686,372,352B (1.571GiB), within900s/12GiB. Driver samples are not continuous profiling. A second fault in a read-only interpretation helper attempted to serialize a NumPy int; its empty failed output/original helper are retained. Casting the count to Python int and using a new output fixed it without source changes, model calls or rerunning the consumed audit.

Reads: four validated checkpoint payloads188,625,652B; full accepted seven-member cache verification closure104,576,736B. Only six training pairs reach the model:89,579,520B unique persisted image/uint8-target payload, repeated across four boundaries (358,318,080B logical pair consumption). The96MiB pair bound covers six unique pairs; expanded long targets are covered by memory limits. Cache ancestry verifies evaluation-member metadata/cache hashes, but no evaluation member is analyzed or used to choose a recipe. No original `.nii`/`.nii.gz` opens are allowed by the cooperative Python audit hook; this is not an OS sandbox.

Independent numerical checks verify all24class/confusion counts, CE denominators/contribution sums, head vector sums/norms/dot products and nonmutation records. New16MiB numeric-preservation capability copies56files/810,813B to registered `segmenter-loss-audit-D329-20261003` on the independent backup root. All copied members and manifest read back with cooperative primary Python reads denied. Whole-root occupancy13,911,176,703→13,911,987,516B, below the new scoped baseline+16MiB ceiling and the unchanged14,892,449,687B earlier ceiling. No original arrays, model checkpoints or masks were added; existing CAP-EXP-013 keepers retain those. No deletion, registry change or quota reset.

## Exact records

Records are under `outputs/prowl/`:

|Record|SHA-256|
|---|---|
|Attempt02 profile receipt|`4d3a09e5a900c28673253af63eb11426edd16a368f0297e19688f13bf200db0b`|
|Attempt02 exact audit request, consumed|`97e75261e9200d1d9dbb8bccebcd06be4dddf836ec66e5083947d41765497fb6`|
|Attempt02 audit receipt|`d78be296a0b0f42f462bedc546d002613399847b21b586b37aabfde7cbd12b09`|
|Final native tests record|`558a022d3b56fd7e327da4abbcb4a8f79c41a1f48ec3632e6e36c8c81413775b`|
|Corrected interpretation|`e3f509b1ac73bc769dc6353156501352acc2d94ed4789ac5967271cb0d22ec88`|
|Candidate arithmetic screen|`25d43660ec39e59849cb46c6c8a3ea4bf6dea928979a087b56301d8c9cd708c5`|
|Independent numeric manifest|`254a28f14a7a40e337ba12d8d477f8f31938f966f6666b8904cd5d35547d4456`|

New implementation: `src/training/segmenter_loss_audit_v1.py`, `scripts/diagnostics/segmenter_loss_audit.py`, `tests/test_segmenter_loss_audit.py`. Accepted111 producing pins and registry remain exact. Numeric evidence/source snapshots/helper histories are independently preserved; Markdown results/next packet remain repository documentation. No new training request is pending, no real loss was changed, and no automatic longer run or model promotion follows.
