# D-311 — foreground/objective audit results

The current loss already favors reducing a uniform foreground logit on seven of the eight fixed
training patches in both007 and010. The exception is a six-voxel cropped reference: its extreme
class balancing favors increasing foreground despite an oversized prediction. Padding weakens
background pressure in the padded probes. These findings support testing a gentler class-mean
rebalance, rather than claiming that the loss universally rewards excess foreground or immediately
adopting the illustrative weight cap50.

Quinton authorized this audit with “Great, check that now. Continue on.”
[Pre-execution plan](LOCALIZER-FOREGROUND-AUDIT-PLAN-2026-10-01.md), D-311;
[motivating010 result](CAP-EXP-010-RESULTS-2026-10-01.md). Eight identical training-only144³ patches
were passed through exact independently backed-up007step300 and010childstep300/logical600 models.
Selection and methods were frozen before new logits. No validation patch was used to select a loss.

## What the measurements mean

The reported derivative shifts every foreground-minus-background logit by the same amount.
A positive value favors decreasing that logit under gradient descent; a negative value favors
increasing it. It is a detached-logit diagnostic, not a model-parameter gradient or a prediction of
AdamW's next update. The same scalar can coexist with different local errors and shared-feature
effects. Eight deliberately selected patches cannot estimate the prevalence of a mechanism across
the cohort. Patch metrics here are not native full-volume validation metrics.

The current positive-patch CE is0.5×mean foreground CE +0.5×mean background CE, with the same
foreground soft-Dice added. Empty references receive background CE alone. All predeclared
counterfactuals use the same logits/targets: voxel-mean CE, weighted-mean CE capped at foreground
weight50, and fixed50. Native half-voxel support is a second arithmetic calculation, not a changed
training mask. The actual operating policy remains argmax, with background winning ties.

## Exact010 patch observations

All144³ patches contain2,985,984voxels. Coefficient is the current foreground/background per-voxel
CE ratio. The quarter/three-quarter column is **post-hoc proposal arithmetic**, described below;
it was not part of the frozen native measurement alternatives.

|Case / absolute patch index|Reference voxels|Coefficient|Current CE+Dice derivative|Cap50 CE+Dice derivative|Post-hoc25/75 CE+Dice derivative|Hard predicted voxels|
|---|---:|---:|---:|---:|---:|---:|
|3206 /329, empty|0|1|+0.202186|+0.202186|+0.202186|179,928|
|5286 /387, smallest positive|6|497,663|−0.141289|+0.200967|+0.029873|187,479|
|3744 /325, median positive|9,177|324.4|+0.105168|+0.175447|+0.153115|103,088|
|2454 /359, greatest extra padding|1,093|2,730.9|+0.090157|+0.179672|+0.136584|83,942|
|7604 /351, prior coverage concern|6,800|438.1|+0.008879|+0.155046|+0.100793|113,348|
|7684 /300, prior Dice regression|1,707|1,748.3|+0.056137|+0.172420|+0.117702|65,510|
|6110 /368, tiny boundary case|146|20,450.9|+0.075640|+0.182857|+0.129511|99,379|
|8937 /481, upper-quartile positive|11,643|255.5|+0.103877|+0.181562|+0.161624|168,316|

007 has the same direction pattern: current7/8 favor shrinkage, cap50/voxel-mean8/8.
007's six-voxel patch derivative is−0.179998, versus010's−0.141289. Its mean reference probability
increases0.426742→0.516384 and hard reference recall0/6→5/6, while prediction size declines
201,243→187,479. This is an actual sparse-target benefit of010 alongside persistent false positives.
The six voxels are a cropped portion of case5286's reference, not its full native reference.

010's mean background foreground-probability and hard prediction count both decline on all eight
probes. Reference probability improves on six of seven positive probes;7684 worsens
0.943223→0.928634 and patch recall0.947862→0.930873.7604's reference probability improves slightly
but hard patch recall worsens0.797647→0.792353. Existing source-grid coverage failures remain
material; a lower background mean or aggregate loss does not resolve them.

## Why a hard cap50 is not the first recommendation

Cap50 changes the six-voxel patch from aggregate expansion to shrinkage, but reduces its summed
absolute foreground CE+Dice logit-gradient contribution to0.000222of the current amount—about
4,514times smaller in010. Foreground CE alone is reduced by roughly4,977times; the remaining Dice
contribution is also tiny. For6110 the combined foreground contribution falls to0.005829of current,
about172times smaller. Plain voxel-mean CE is more severe. Fixed50 and cap50 coincide on these
selected sparse patches; synthetic checks distinguish their behavior on other class proportions.

This raises a credible sparse-reference protection concern, not a demonstrated training failure.
The early CAP-EXP-001 empty-mask result also argues against blindly returning to voxel-mean CE.
The illustrative50 is neither optimal nor an adopted recipe. No cases are removed because of
these counts, and held empty-reference studies do not become trusted negatives.

## Padding and negative exposure

Five selected patches include extra144³ patch padding. Their native-support complements account
for38.65%–79.17%of patch voxels and31.12%–74.97%of010's false-positive probability mass.
Extra patch padding and preprocessing geometry padding overlap; these fractions must not be added.
All selected reference voxels are inside native half-voxel support. No reference was discarded.

On those five patches, mean background foreground-probability rises when calculated only inside
native support, and current shrinkage derivatives strengthen. For example7604 changes
+0.008879→+0.023786;7684 changes+0.056137→+0.082692. The current sign is unchanged on every probe.
Synthetic padding therefore dilutes the background mean here; it does not alone establish the
cause of oversized native masks. All-voxel training loss still penalizes that padding, and native
prediction exports retain their existing geometry. Masking padding is a separate future factor.

The010 replay already established290 positive/10 empty patches out of300, despite155/145
foreground/background centers. The audited empty patch is genuinely target-empty within a
qualified positive-reference case. It receives background CE alone, correctly favors shrinking,
and still produces179,928foreground voxels after010, down from218,616in007. More negative exposure
is plausible, but increasing background-center frequency does not guarantee empty patches.
This audit neither qualifies an explicit-negative sampler nor supplies negative-reference semantics
for the23held cases.

## Gentler proposed comparison, not adopted

After reviewing the predeclared counterfactuals, Codex calculated an additional scalar alternative
from the saved components: **0.25×foreground mean CE +0.75×background mean CE + unchanged Dice**
when both classes are present. Sole-class patches keep their existing sole-class mean CE; omit
Dice for empty targets. This is class-mean weighting, not per-voxel weights0.25/0.75.

It halves foreground CE pressure and increases background CE pressure1.5times, while keeping
sparse targets represented independently of their voxel fraction. Including unchanged Dice, the
foreground logit-gradient magnitude retains50.00%–53.22%of current across positive probes, rather
than cap50's large sparse-target reduction. It favors shrinkage on all eight probes in both models;
that does not prove coverage preservation or improved training. The0.25choice is a bounded,
interpretable proposal, not a fitted optimum. Five invented sparse/dense/empty/all-foreground/extreme
cases independently check its scalar values and derivatives against autograd and finite differences.
These calculations use retained scalars and invented vectors; no extra native forwards occurred.

[Proposed matched training comparison](LOCALIZER-CLASS-MEAN-REBALANCE-PROPOSAL-2026-10-01.md)
sets out the exact formula, fixed factors, coverage/utility criteria and implementation gates for
discussion. There is no new training authorization, implemented loss or prepared launch request.

## Execution and evidence

- Native worker15.7808s, total17.3955s; sampled peakRSS1.8235GiB/driver1.3708GiB, below the frozen
  600s/16GiB limits. AC/exclusiveMPS/free-space/output guards passed. Native float32 MPS, no fallback.
- Exactly16forward passes, zero optimizer updates and zero original CT/label reads. Primary reads
  blocked by the audit hook. Both model imports use validated independent backups; expected weight
  digests match before/after each eight-patch group. The optimizer step method is explicitly denied.
-27invented math tests pass, covering normalization, empty/dense targets, extreme logits and
  analytic derivatives against autograd/finite differences. Maximum discrepancy between native
  configured loss and detached float64 decomposition7.19836e-8, within the frozen1e-5 bound.
- All16rows pair exact image/target/support/trace hashes, train role and model ancestry.20execution
  files and42review-package members rehashed;1,782,877bytes of retained review evidence, excluding
  generated bytecode. Production source/runtime unchanged; prior1,652-test baseline remains valid.
  No production source changed, so the full suite was not repeated for this detached audit.

Local evidence directory: `outputs/prowl/localizer-foreground-audit-20261001`.

|Record|SHA-256|
|---|---|
|Frozen request|`dff832472a74618b6e3ca5a689811863b04f397ab91715796f3bf4757981b02a`|
|Native execution receipt|`e90e8b1b72a7d83ff93f5068237b5083e37afbadd2491c2a0bd2d70ed8e02f7f`|
|Full audit/review receipt|`d4b1f0bc0c0be5a0acde60e1b878bf5df538c3e070d71097680f4af4cf59e74c`|
|Production source|`0c857972139c44f561d0c338c6dbdf922920abd9b967423bc9b905c2ed5f08fc`|
|Runtime|`dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`|

`request/` retains exact methods,27-test log, selection, model references, design, config and
source/runtime snapshots. `execution/` retains16scalar rows, result, worker/supervisor logs and
its independent receipt. `review.py`, `review.log` and `analysis.json` retain verification and
explicitly post-hoc25/75 arithmetic. The request is consumed and cannot be replayed.

The plan and immutable request preceded execution; the living-notebook entry was appended after
execution, rather than before launch. This documentation timing deviation does not change the
frozen selection/measurement scope and is not retroactively described as prospective notebook entry.
Local diagnostic evidence remains ignored scratch; retained model/checkpoint backups remain the
independent persistent ancestry. No backup write or Git publication was performed during this audit.

D-311 is complete.153members/23holds are unchanged. There is no active/pending native audit or
training run, automatic extension, adopted loss, model promotion or Claude dispatch.
