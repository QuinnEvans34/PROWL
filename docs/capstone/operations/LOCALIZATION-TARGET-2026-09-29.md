# Stronger localizer target and bounded next sequence

D-280: Quinton requested stronger localization targets, work on excess foreground, then a varied
qualified training cohort with separate validation. Codex owns localizer diagnostics, bounded
imaging experiments and cohort preparation; Claude's retrieval lane is unchanged.

## Separate engineering targets

The localizer is a region proposal, not the final review contour (Plan 05). Keep the historical
minimal learning indicator unchanged. Add a stricter **two-case fit diagnostic**, provisionally:
per-case mask recall >= 0.98, Dice >= 0.65, predicted/reference volume <= 2.0. Every case must pass;
no averaging away a failure. These are engineering targets chosen by Codex, not clinical standards
or user-approved permanent acceptance thresholds. They do not determine data eligibility.

For region usefulness, measure all-component argmax bounding box plus 10 mm physical margin,
clipped to the available grid. Compare a deterministic largest 6-connected-component candidate
with the same margin to diagnose isolated false positives. Both select using predictions alone.
Largest-component ties choose first component in array traversal order. No candidate is promoted.
Report mask precision/recall/Dice, component count/physical volumes, half-open box, requested/realized
margins, boundary contact, physical dimensions, scan-volume fraction, and reference coverage.
An empty prediction is explicit localization failure, never a whole-volume or reference-box fallback.

Provisional **pre-mapping ROI diagnostic**: every case must retain >= 99.5% of its pancreas reference
inside a box occupying <= 25% of its processed scan. The volume cap is an engineering screen, not a
final Stage 2 resource limit. Report both individual pass conditions; do not widen the policy to
make these two cases pass. These numerical criteria are defined before the new box measurements.
The final cascade gate still requires train-disjoint development selection, qualified lesion
containment evaluation, complete letterbox/mapping retention, effective spacing and resource tests.
Pancreas-only coverage does not establish lesion coverage. Two-case training evidence cannot freeze
D-208 or a production ROI policy.

## First diagnostic execution envelope

Read only CAP-EXP-004's pinned terminal checkpoint and its two qualified CT/pancreas pairs. Verify
its local receipt, terminal completion, input binding and terminal metrics; record current diagnostic
source separately from original training source. Restore step 300, two image-only full-volume
forwards, zero optimizer updates, unchanged model digest. No new raw cases or lesion reads.
Native MPS, no automatic CPU fallback; AC and cooperative accelerator lock; 600 s / 16 GiB / 256 MiB
local output cap, 100 GiB internal free floor. Preserve original files and write a new receipt.
Synthetic tests first: geometry, margin clipping, disconnected components/ties, empty masks,
invalid grids, missing references and per-case target failures. No dependency changes.

## Follow-up and expansion

Use this evidence to distinguish adjacent overprediction from disconnected false positives. If a
simple component policy does not resolve the excess, compare one explicitly versioned objective
change against CAP-EXP-004, retaining data, initialization, LR, horizon and sampling. Freeze that
concrete run before compute; preserve null results. Do not tune several losses or thresholds at once.

Cohort expansion starts from the immutable 7,200/1,800 train/validation memberships and retained
metadata inventory, never model performance. Select deterministic candidates across available scan
geometry/protocol strata, record missing metadata as a stratum, retain difficult/held members and
explicit nonreplacement/expansion rules. Detailed CT/target qualification is required for every
consumed member. Validation is disjoint from train and is development validation, not publisher-test.
The existing two-case resolver is deliberately specialized; extending it requires a new versioned
cohort package and role-aware consumer tests, not changing its constants or pretending its narrow
qualification history applies to new studies. No candidate is executable merely by being selected.
