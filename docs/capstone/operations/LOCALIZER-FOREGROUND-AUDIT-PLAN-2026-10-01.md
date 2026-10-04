# D-311 — frozen-model foreground/objective audit

Quinton authorized the proposed investigation: “Great, check that now. Continue on.” Implement,
verify and run one bounded audit of retained007/010 models and fixed cached training patches.
No optimizer updates, original source reads, primary-drive reads, qualification changes, threshold
selection, model promotion, Git publication or Claude dispatch. Discuss results before selecting
a training loss. D-310's requests remain consumed.

## Exact selection before new logits

Verify the27-member010review seal `4055ed5addbac03f06f3f6c6ac973b6170fe1975f1e6a46d952ad29aad3e88c1`.
Use its300 crop records and training-only membership. Select eight unique absolute indices:

| Reason |Absolute index|Case|Recorded foreground voxels|
|---|---:|---|---:|
| First empty crop |329|3206|0|
| Smallest positive crop, ties earliest index |387|5286|6|
| Median positive crop, sorted count/index, position len//2 |325|3744|9177|
| Greatest extra-padding positive crop, ties earliest index |359|2454|1093|
| First7604exposure, prior box-coverage failure |351|7604|6800|
| First7684exposure, training Dice regression |300|7684|1707|
| First6110exposure, known tiny boundary reference |368|6110|146|
| Positive upper quartile, sorted count/index, floor(.75*(len-1)) |481|8937|11643|

The first6110exposure replaces a generic lower-quartile fill to represent the known tiny case
reference as well as a sparse cropped corner. This is a pre-logit selection clarification, not an
outcome-driven replacement. A frozen selection pins exact target/image bytes, crop trace, geometry
and source-support masks; no later substitution. All held empty-reference cases remain held.

## What will be measured

Two exact independently backed-up terminal models, eight identical144³ patches each:16 forwards
maximum, float32 native MPS, no fallback, two CPU threads, AC/exclusive MPS/100GiB free floor.
Models remain byte-exact; optimizer step methods are refused.16GiB process RSS/driver,600s total,
128MiB output. The current role-safe cache/binding remains pinned. No primary/backup writes.
Methods live in a sealed diagnostic output package; production source/recipes are unchanged.

Report target/foreground/background probabilities, hard counts at the existing argmax operating
policy, false-positive probability mass, foreground/background CE contributions and foreground
soft-Dice. Do not tune thresholds. Report derivative of each loss with respect to a uniform
foreground-minus-background logit shift, both signed class contributions and absolute sums.
Negative derivative favors increasing that logit under gradient descent; this is not a parameter
gradient, AdamW update prediction, clinical calibration result or proof of a better training loss.

Use stable binary CE on the same detached logits. The current positive-patch CE is half the
foreground mean plus half the background mean; absent classes are omitted. Compare voxel-mean CE,
and weighted-mean CE with foreground/background weight ratio either fixed50 or capped at50 relative
to the current n_background/n_foreground. Normalize by sum of voxel weights; empty/all-foreground
cases reduce to their sole-class mean. Add the same foreground soft-Dice, smooth1e-5, omitted for
empty references.50 is an illustrative diagnostic choice, not an approved/optimal training weight.

Repeat arithmetic on the native half-voxel support subset to expose padding effects; this is a
counterfactual only. Support maps processed crop centers through frozen affines into
[-.5,shape-.5); extra patch padding is separately counted. Preserve and report any reference outside
that geometric support. No real target or loss support is changed. Patch scores are not native
full-volume validation scores.

## Qualification and preservation

Before model reads, invented tests check class means/normalization, empty/all-foreground behavior,
stable extreme logits, analytic logit-shift derivatives against autograd and finite differences,
and masked-support counting. CPU scalar calculations must reproduce the existing configured loss
within1e-5 on native logits. Freeze source/runtime, methods/tests, selection, model references and
budgets before launch; bind existing D-311 approval to that exact request.

Verify independent backup/catalog/payload hashes and original model identities, and weights before
and after every model's eight forwards. Block primary reads. Preserve worker/supervisor logs and
each completed row even if stopped. No automatic replay of a consumed request. Verify every retained
member and scalar identity, then document the evidence and a proposed next loss/sampling decision.
