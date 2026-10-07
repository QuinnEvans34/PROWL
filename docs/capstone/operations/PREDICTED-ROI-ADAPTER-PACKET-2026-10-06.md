# Predicted-ROI adapter — bounded coding packet

Prepared for Quinton's development regrouping on October 6. **Bounded implementation approved.**
Quinton selected “Proceed with that bounded batch” on October 6: this invented-only adapter, then
the three drafting/read-only packets in the [execution queue](../weeks/WEEK-01-EXECUTION-QUEUE-2026-10-06.md).
No new model forward, training run or real source read is authorized. It implements the first small
part of R-04 without changing the existing experiment.

## Problem and outcome

The current segmenter preprocessing calls `select_pancreas_box` on the provided pancreas reference.
However, `segmenter_geometry_v1.plan_geometry` already supports `roi_origin='predicted_region'`,
and the forward/inverse image mapper is separate from targets. Reuse that qualified physical
geometry instead of building a second crop/resampling path.

Outcome: a new explicit adapter which takes an invented native-grid localizer prediction and
CT geometry, binds their identity, chooses a region from the prediction alone, and produces the
segmenter transform/image input. This is an engineering adapter, not an adopted localizer or
autonomous-baseline result.

## Proposed file allowlist

- New `src/data/segmenter_predicted_roi_v1.py`.
- New `tests/test_segmenter_predicted_roi_v1.py` with test-owned invented arrays.
- New `docs/capstone/imaging/PREDICTED-ROI-ADAPTER-CONTRACT-V1.md`.
- New `docs/capstone/operations/PREDICTED-ROI-ADAPTER-RESULTS-2026-10-06.md` or actual finish-date
  equivalent, with exact checks and remaining real-input qualification requirements.

Read/reuse `src/data/segmenter_geometry_v1.py`, existing geometry tests and the approved spatial/ROI
contracts. Do not change the old mapper, cache/loader, training consumers, cohorts, registry or
Claude-owned source/tests/planning. A needed change outside the allowlist returns for scope review.

## Interface and diagnostic policy

- Require an explicit source study/CT identity, native shape/affine and prediction lineage, including
  model/run/prediction identity and the grid to which the prediction belongs. Stale, mismatched or
  missing identity fails; merely matching an array shape is insufficient.
- ROI planning accepts prediction/geometry only. It accepts no pancreas/lesion reference, cannot
  reopen a source file and cannot repair a localization using a target.
- For the invented diagnostic, retain all binary prediction support with the existing 10 mm margin
  and 144³/1 mm sampling recipe. Smaller invented tensor sizes may be used for fast tests. This is
  a named diagnostic policy, not adoption of largest-component cleanup or a real cascade policy.
- Use the shared signed-permutation/axis-aligned geometry contract. Preserve half-open RAS boxes,
  physical margins, uniform scaling/symmetric padding and exact native restoration. Refuse
  unsupported oblique/sheared grids rather than approximating them.
- Empty, nonfinite, nonbinary, wrong-grid and unsafe predictions produce explicit failure reasons.
  They remain failures in the caller's requested-case accounting. There is no reference-box or
  hidden whole-volume fallback.
- Image preparation uses only CT and the pinned predicted transform. Reference arrays may appear
  solely in separate invented test oracles after the ROI is fixed. No selected policy can expand a
  box based on lesion extent. Inputs are not mutated.

## Checks and finish line

Meaningful tests should catch a wrong axis, physical margin or lineage, not merely mirror the code:

1. Independent landmark/world-coordinate oracles for permuted/reversed axes, anisotropic spacing,
   nonzero origins, odd padding and source-boundary contacts.
2. Mismatched study/CT identity, prediction provenance or native grid refused.
3. Empty/invalid/unsupported localization refused with explicit reasons and no fallback.
4. Multiple prediction components retained; no largest-component-only behavior.
5. A lesion outside the fixed invented prediction box cannot affect ROI selection and remains
   absent from the restored foreground, with explicit excluded-coverage accounting in the oracle.
6. Deterministic transform hashing, unchanged inputs, correct CT normalization and probability
   restoration, including background outside the region.

Run only the new targeted tests plus the existing shared geometry tests appropriate to this adapter,
using `.venv-prowl/bin/python`. Invented CPU arrays only. No dependency install, original/processed
real-array opens, MPS/GPU execution, registry writes, request consumption or external-drive writes.
If a real-input or resource ambiguity appears, stop that part and report it rather than expanding scope.

Done when the new contract/adapter and meaningful tests pass, existing shared geometry behavior is
unchanged, and the handback states exactly what remains before a real zero-update qualification.
After that handback, only the approved queue's drafting packets may continue. A real qualification
later needs model/prediction/policy pins, matched
members, purpose permissions, source/native-grid evidence, budgets and a separate exact request.
