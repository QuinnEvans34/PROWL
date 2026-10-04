# D-308 — schedule, patch composition and loss investigation

**The strongest changed factor is the schedule, but schedule is not the only unresolved issue.**
Installed-runtime replay found correct scheduler ordering and rates. Extending the cosine horizon
from300 to1200 made the first300 updates accumulate1.8945x the sum of applied rates, while the same
initial weights, membership, sampler, loss and prediction mechanics were retained. The saved models
reproduced six selected native masks exactly. Sparse targets, substantial padding and almost no
negative-only patches expose additional objective/sampling concerns that plausibly affect both runs.

This investigation is complete under [D-308's bounded plan](CAP-EXP-008-OPTIMIZATION-AUDIT-PLAN-2026-10-01.md).
No new training, original source reads, qualification change, model promotion or Git publication
occurred. A next experiment is [proposed separately](LOCALIZER-SCHEDULE-NEXT-PROPOSAL-2026-10-01.md).

## 1. What the scheduler actually did

The optimizer steps before the scheduler. Saved `learning_rate` is the rate **after** that update,
available for the next one. It is not the rate used by the completed update. All600 saved rate entries
across007/008 reproduced the installed PyTorch2.13.0 scheduler to1e-12. No misplaced scheduler step,
unexpected restart, resume, missing update or swapped member order was found.

| Completed updates |007 recorded next LR, horizon300|008 recorded next LR, horizon1200|
|---|---:|---:|
|0|0.000300000|0.000300000|
|75|0.000256066|0.000297118|
|113|0.000206676|0.000293484|
|150|0.000150000|0.000288582|
|226|0.000042829|0.000274502|
|300|0|0.000256066|

The final **applied** rates were8.22460e-9 in007 and0.000256343 in008. The sums of300 applied rates
were0.04515 and0.08553618, ratio1.894489. This is a descriptive schedule quantity, not a measure of
parameter displacement or a proof of an excessive LR: AdamW's moments and evolving gradients matter.
The model's L2 displacement from initialization was6.1341 in007 versus8.2527 in008, consistent with
different optimization trajectories but not proof of overshooting or exploding gradients.

The retained seed initialization,300 sampling/case/pass traces and153 initial metrics match. Ten key
captured function ASTs are identical: initialization, update, member order, patch sampler, loss,
preprocessing/restoration, prediction and export. The scientific schedule change therefore has much
stronger support than an accidental change to those mechanics. Finite-gradient checks passed in the
actual runs; gradient magnitudes were not retained, so clipping/instability cannot be diagnosed here.

A synthetic600-call probe of the **old**300-horizon scheduler found LR0 at300,0.00015 at450 and
0.0003 at600. Extending the loop alone would raise the LR again. Current version1's300-update cap
prevents this; it is a future-extension hazard, not a bug that affected007 or008. The cosine formula
and per-call behavior are described in [PyTorch's documentation](https://docs.pytorch.org/docs/2.8/generated/torch.optim.lr_scheduler.CosineAnnealingLR.html).
Those public2.8 docs are background; all numeric/runtime claims above were checked on installed2.13.0.

## 2. Patch composition is much less balanced than center selection

All300 saved training patches were exactly replayed from the113-member qualified cache. This required
no original CT/label or primary-drive reads. Patches and actual labels, not just requested center
classes, were checked. Every foreground center remained foreground; no target lay outside the
geometric native support used for the diagnostic.

| Measured item | Result |
|---|---:|
|Foreground/background centers|146 /154|
|Patches containing foreground|295/300|
|Empty, background-only patches|5/300|
|Background-center patches that still contain foreground|149/154|
|Patches containing the entire cached visible reference|247/300|
|Median target voxels / patch voxels|9047 /2,985,984|
|Median target fraction|0.302982%|
|Maximum target fraction|0.873313%|
|Patches below0.1% target fraction|28/300|
|Median extra144³ patch padding|32.6389%|
|Median centers outside native half-voxel support within patches|32.6389%|
|Patches with more than half their centers outside native support|37/300|
|Background sampling centers outside native support|8/154|

The last support measurements map processed voxel centers into the native acquisition and check
half-voxel bounds. They are geometric diagnostics, not tissue masks or exact interpolation-support
measurements. Temporary patch padding is added after center selection; the8 outside-support centers
come from pre-existing preprocessing padding. That behavior is explicitly allowed by the sampler.

The144³ physical context often includes the pancreas even when the requested center is background.
There is therefore very little completely negative patch exposure. This is a candidate explanation
for persistent false foreground, not a demonstrated causal effect or a reason to shrink context now.
The median outside-support share of background-class voxels is32.68%. Easy artificial background
enters the class average and may dilute pressure on real confusing background. Both runs use the
same patches, so this cannot by itself explain their between-run difference.

No held empty reference was promoted to a trusted negative. Any later negative-sampling experiment
must use positively qualified inputs and explicitly verified patch contents. Difficult and partial
cases remain in their original membership and every applicable experiment aggregate.

## 3. Balanced CE is functioning, with a consequential tradeoff

The implemented loss averages foreground CE and background CE equally within a nonempty patch,
then adds foreground soft-Dice loss. Synthetic logits verified the decomposition and gradients.
Empty patches contribute background CE only, as intended. There is no double softmax or label-channel
swap: CE receives logits and integer targets; Dice receives foreground softmax. This agrees with
the [CE input convention](https://docs.pytorch.org/docs/2.8/generated/torch.nn.CrossEntropyLoss.html).
The equal-class reduction is our implementation, not PyTorch's default voxel average.

For a patch withN voxels andn foreground voxels, the foreground/background CE coefficient ratio per
voxel is(N-n)/n. Its median across295 nonempty patches is328.91. In tiny training6110, saved patch3
has only12 foreground voxels and a ratio248,831; its other two patches have146 and a ratio20,450.95.
The same patch receives half of its CE class weight from those few foreground voxels. This preserves
their learning signal but may amplify sparse/boundary supervision. It does not justify deleting or
relabeling6110. The ratio describes CE coefficients; actual gradients also depend on predictions.

The previous voxel-CE collapse motivated balancing. Removing it without a separate comparison would
ignore that evidence. Plausible later interventions include explicit acquisition-support masking,
negative-only sampling where valid, or bounded class-balancing strength, each as its own comparison.
Neither the current class balance nor its probabilities were certified as an operating policy.

## 4. Saved-model probes explain why lower loss misled us

Each independently backed-up step300 model received the same four saved training patches and three
full cached validation volumes. All six standard native masks matched their retained exports exactly.
Models remained at300 with identical before/after weight hashes; real optimizer calls were blocked.
Numerical loss decomposition agreed with production loss on the matched patch forwards.

Below are **processed-reference** results, not the separately retained native scores. Probabilities
are descriptive model outputs, not calibrated confidence. Selected cases are development probes.

|Selected validation case|007 processed recall|008 processed recall|007 foreground CE|008 foreground CE|007 background CE|008 background CE|
|---|---:|---:|---:|---:|---:|---:|
|6186|0.914292|0.055856|0.328197|1.347445|0.256452|0.196175|
|6534|0.989246|0.679177|0.150049|0.542000|0.218419|0.161520|
|1004|0.991296|0.970315|0.054059|0.123287|0.256947|0.209777|

On6186 the reference's median foreground probability falls0.7691→0.2611. Background's median falls
0.1349→0.0780 while its95th percentile rises0.4832→0.5198. The model suppresses much background more
strongly yet leaves a troublesome high-probability tail and loses the reference. Better average
background CE does not imply fewer false-positive regions or preserved pancreas coverage.

The matched6449 training patch illustrates the surrogate mismatch: total loss improves1.104828→
1.069894 and soft-Dice loss improves0.961907→0.949476, while hard Dice worsens0.150299→0.126107.
Reference recall remains1.0, but foreground excess increases. Tiny6110's matched positive patch155
also loses processed recall1.0→0.849315; this is a patch probe, not a new full training-cohort score.

The underlying issue is broader than tiny references. Worst validation6186 has111.536ml native
reference, not a tiny reference. Posthoc slice-thickness groups all decrease in mean Dice and recall:
<=1.5mm(n17),1.5–3mm(n10),>3mm(n13). These descriptive groups do not establish a protocol cause,
independent test performance or grounds to choose a favorable subgroup.

## 5. Inference mechanics tested and questions still open

Gaussian versus constant sliding-window blending was probed on6186 with each frozen model. Processed
recall changes0.9143→0.9177 in007 and0.0559→0.0510 in008; corresponding Dice changes0.0594→0.0547
and0.00344→0.00284. This fixed probe does not recover the failure, so no blending change is selected.
It does not rule out every context/window effect or prove all other cases behave the same way.

Both models contain25 group-normalization modules, no batch-normalization modules and no dropout
modules. A running-BN-statistics or active-dropout train/eval mismatch is not supported. Group norm
still depends on each window's content; patch/full-volume context effects remain possible. Full
prediction/export replay and unchanged preprocessing support the existing geometry, not expert
annotation correctness. Native target-fidelity limits, partial references, limited two/three-case
exposures, no augmentation and development-set reuse remain documented constraints.

No sustained long duration has yet been tested on113/40 beyond300. This investigation cannot separate
all LR, gradient/noise, loss, sampling and exposure interactions. It gives a more controlled next
comparison and a ranked list of subsequent questions, not a single proven root cause.

## Verification and immutable evidence

CPU attempt02:10.332s,2.235GiB RSS;300 exact patch replays, both installed scheduler replays, synthetic
loss checks. Attempt01's exact-float equality assertion failed after cache replay; its log remains,
and the helper tolerance was corrected to1e-6. No production fix or original-byte reread occurred.
Each attempt read5,453,796,180 declared cache-member bytes, below its6,233,594,545 upper bound.

Native MPS:16 forwards,47.901s supervised,2.945GiB RSS/1.461GiB sampled driver;3,489,063,431 declared
cache-member bytes. Two existing independent backups were semantically validated/read; no new backup
or restore artifact was written. Six native-array replays exact. Source/environment and both model
weight hashes unchanged. All600s/16GiB/128MiB/AC/free-space bounds passed. Zero original CT/label
reads, primary-drive reads or real optimizer updates. Production source remains the1,574-test baseline;
no redundant full-suite rerun or dependency change was needed for ignored diagnostic helpers/docs.

Evidence:`outputs/prowl/CAP-EXP-008-SCHEDULE-AUDIT-20261001`.
Pinned MPS request:`6a5f4e6b32ca280853d427ef06a3fb8ac0762e1d76154388f1980aaf213cf3fd`.
Final23-member receipt:`8ae38155aa54a126ba55539a99c5fc4ca0dae175f0fe4f818ca1a9974a53fc86`.
The package retains300 patch measurements,113 cached-member summaries,600 rate histories, synthetic
loss checks, source AST comparisons, padding-center/strata analyses, model component/probability
records, supervisor logs and six native replay masks. Masks/review evidence remain local derived
scratch, not independently backed-up mask bytes. Original training/recovery receipts remain untouched.

**Recommendation:** first test extra exposure under a deliberately low-rate tail after reproducing
007's successful early schedule. Keep cohort, loss, sampler, geometry, inference and coverage guards
fixed. If that does not shrink excess foreground while retaining coverage, isolate support-masking,
negative sampling and loss-strength questions separately. A new training request is not prepared.
