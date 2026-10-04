# CAP-EXP-001 optimization investigation — D-276 findings

September28,2026. The read-only diagnostic completed. **The model developed weak foreground/background
separation while strongly suppressing foreground probabilities overall.** This supports testing the
loss balance next; it does not establish that changing the loss alone will produce useful contours.
Every sampled patch contained target voxels. Empty final masks were not empty targets, a missing
positive-center draw, or an endpoint evaluation mismatch.

No optimizer updates, threshold promotion, source/checkpoint changes or new training run occurred.
CAP-EXP-001's frozen result remains: mechanics passed, learning criterion failed, final Dice0/0.

## Reproducible evidence

- Plan: [D-276 investigation](LOCALIZER-OPTIMIZATION-INVESTIGATION-PLAN-2026-09-28.md), recorded before execution.
- Diagnostic: `outputs/prowl/localizer-optimization-2da20e71-6a17-4f1a-824d-8fb1a3337521`.
- Receipt SHA: `bc5ad7a35e8f39d726f7be1857b11056fc09934d3ac3ca3f833d854e3392b386`.
- Parent run receipt: `a470008bf2bf45cda5f3aaf1de451c64efe3b17687227486d750f232ca26f34a`.
- Exact steps0/25/50/75/100 resolved through original receipt/identity validators. Original model
  source bytes were checked before and after the diagnostic. Each loaded model's parameter/buffer
  digest was unchanged after inspection. All original run receipt members and diagnostic receipt
  members were verified. Original endpoint losses/Dice reproduced within1e-5.
- Two qualified source loads,100 exact crop replays,10 image-only full-volume passes and10 fixed
  patch forward passes. Fixed patch per case was its first actual foreground-centered crop, selected
  before inspecting checkpoint results. Probabilities/loss gradients were summarized, not saved as
  additional raw volumes. Logit derivatives were computed on detached CPU logits; no model update.
- Native MPS, fallback disabled. Whole supervised job51.45s; sampled RSS2,073,853,952 bytes
  (1.93GiB), boundary MPS driver1,252,261,888 bytes (1.17GiB); overlapping measures, not additive.
  Original records intact, no failure/retry. Scoped limits600s/16GiB/256MiB respected.

## 1. Exact crop replay rules out positive-example starvation

All100 replayed sampler traces matched the training log exactly. All100 patches contained pancreas.

| Case | Updates | Foreground-centered draws | Pancreas fraction per patch | Fraction of full pancreas retained per patch |
|---|---:|---:|---:|---:|
| 3 | 50 | 20 | 0.314896% every time | 100% every time |
| 26 | 50 | 24 | 0.104777–0.375479% | 27.90–100%; mean89.51% |

The remaining56 draws used background centers, but their patches still contained reference voxels.
Foreground-center sampling changes crop placement; it does not balance foreground/background voxel
counts. Changing the positive-center probability alone would not remove this severe voxel imbalance.
This does not imply that the cases are invalid or should be filtered out.

## 2. There is weak probability separation, not literally zero foreground probability

Mean predicted foreground probability at reference-positive versus reference-negative voxels:

| Step | Case3: inside / outside | Case26: inside / outside | Saved next-step LR |
|---|---|---|---:|
| 0 | 0.33039 / 0.41871 | 0.36534 / 0.41687 | 0.00300000 |
| 25 | 0.08302 / 0.07631 | 0.08538 / 0.07690 | 0.00256066 |
| 50 | 0.05561 / 0.03612 | 0.06216 / 0.03788 | 0.00150000 |
| 75 | 0.05320 / 0.02830 | 0.06780 / 0.03093 | 0.00043934 |
| 100 | 0.05694 / 0.02742 | 0.07359 / 0.03053 | 0 |

By step25, mean probability inside the reference was slightly higher than outside. The separation
increased later. At step100 the maximum probability anywhere was0.08935/0.09675, so neither volume
had a voxel near the original binary argmax boundary. “No foreground prediction” is correct;
“the model assigned zero pancreas probability” or “learned absolutely nothing” would be incorrect.
Mean separation alone does not establish useful discrimination, calibration or generalization.

The prespecified diagnostic threshold0.05 gave:

| Case | Predicted voxels | Reference recall | Dice |
|---|---:|---:|---:|
| 3 | 69,177 | 0.7911 | 0.06125 |
| 26 | 221,053 | 0.9931 | 0.02941 |

These are poor-overlap training-case diagnostics with extensive false-positive foreground. They
are not a selected threshold or replacement for the recorded Dice0/0. The other prespecified points
0.10/0.25/0.50 produce empty masks at step100. Lowering the cutoff is not a demonstrated fix.

## 3. Nearly all net loss reduction came from the background CE contribution

The original objective is mean voxel cross-entropy (CE) plus foreground soft Dice loss. Its CE
foreground/background contributions sum to the same voxel-averaged CE; they are not class-normalized.

| Case | Background CE, before→after | Foreground CE, before→after | Soft Dice loss, before→after |
|---|---|---|---|
| 3 | 0.548935→0.027819 | 0.002470→0.006260 | 0.996580→0.991641 |
| 26 | 0.545448→0.031097 | 0.002422→0.006258 | 0.995832→0.989343 |

The equal-case background CE drop was0.517734 versus total loss drop0.519635: about99.6% of the
net improvement. Foreground CE contribution actually increased as foreground probabilities fell.
The soft Dice term improved slightly, but remained close to1. The low combined loss did not imply
accurate pancreas localization.

A constant0.003 foreground-probability baseline would have total loss1.01312/1.01423 on these
reference grids, below the final model's1.02572/1.02670, despite producing no foreground mask.
This is an analytical baseline under the original objective, not a trained alternative. It helps
explain why reducing loss alone is a weak success test in this regime; it is not proof of a local
optimum or an unavoidable failure of Dice+CE.

## 4. Local derivatives support a loss-balance comparison

On the fixed positive-centered patches, derivatives with respect to a uniform increase in the
foreground-minus-background logit at step100 were:

| Case | CE derivative | Dice derivative | Sum |
|---|---:|---:|---:|
| 3 | +0.026913 | −0.000761 | +0.026153 |
| 26 | +0.028125 | −0.001066 | +0.027059 |

For this common logit shift, gradient descent on CE favors lowering foreground logits; Dice favors
raising them, with net CE magnitude about35.4×/26.4× greater. At initialization that imbalance was
larger. This is evidence about one output-space direction, **not a claim that CE dominates every
parameter gradient** or a prediction of the next AdamW update.

Both terms have negative foreground-voxel derivatives, so both favor higher foreground logits at
reference-positive locations. In fact, at step100 the summed Dice derivative on just foreground
voxels is larger in magnitude than CE there. Background terms and their aggregation matter; it is
misleading to say the Dice term is disconnected or that the loss never asks for foreground.
These are logit derivatives, not measured per-layer parameter gradients or a complete optimizer diagnosis.

As a counterfactual calculation from the retained patch summaries, changing only CE to
`0.5 * mean(CE on foreground) + 0.5 * mean(CE on background)` would give CE common-shift derivatives
−0.45536/−0.44624 at the final outputs (rather than +0.02691/+0.02812). This follows from
`0.5 * (mean(p_foreground_on_target) - 1 + mean(p_foreground_on_background))`.
It would alter the pressure substantially, but may also increase false positives. It has not been
trained and is not an approved replacement objective.

## 5. Schedule and remaining uncertainty

The scheduler reached zero after exactly100 updates as configured. There is no evidence here of
an accidental early scheduler stop. Separation was still changing between75 and100, so more learning
time or a different schedule remains a plausible alternative. Simply resuming the completed cosine
schedule is not a sound proposal: its planned LR is exhausted, and the bounded executor refuses
extensions. Any longer or differently scheduled comparison needs its own identity and plan.

The evidence does not establish that0.003 was too high, that a lower LR will help, or that class
balancing alone will solve the problem. This investigation therefore changes the priority from the
previous tentative lower-LR suggestion to a controlled loss-balance test. Keep LR/schedule fixed in
that first comparison, rather than change several factors together.

## Recommended next experiment

[CAP-EXP-002 proposal](CAP-EXP-002-PROPOSAL-2026-09-28.md): same two cases, scratch initialization,
seed, crops,100-step horizon, LR/schedule, geometry and evaluation threshold. Change **only the CE
class weighting**, keeping the same foreground Dice term. Add objective-aware telemetry so the result
can distinguish improved localization from increased false positives. It remains a proposal; no new
training run has occurred. Broader cohort qualification should follow a meaningful tiny-set learning
result, not replace diagnosis of this failure. Preserve difficult-case membership throughout.

## Code and verification

Added `src/training/localizer_diagnostics.py`, its numerical tests, and the bounded native runner
`scripts/diagnostics/localizer_optimization_check.py`. Production training/loss/configuration were
not changed. Five new checks cover independent CE/Dice arithmetic, empty-target behavior, finite-
difference logit derivatives, invalid inputs and unchanged input logits. Full native suite:
**1,079 passed**, two existing torch.jit warnings,13.98s. `git diff --check` passes.
No install, Git publication, retrieval edit, remote transfer or source activation was performed.
