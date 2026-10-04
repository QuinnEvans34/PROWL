# Overnight training investigation — morning handoff

Completed the planned overnight investigation and three controlled training comparisons.
**Training is stopped.** The strongest result reaches mean Dice **0.446** on the two training cases;
predictions still contain substantial excess foreground. All three new terminal checkpoints passed
independent backup recovery with zero fixed-probe probability difference.

## What we learned

The original smoke run's empty predictions were not caused by missing pancreas in the training
patches: all 100 sampled patches contained it. The original objective rewarded suppressing background
errors strongly enough that total loss fell while both final foreground masks disappeared. The
retained probability and local logit-gradient diagnostics support testing the objective balance;
they do not prove that one term dominates every parameter gradient.

Equal class weighting in cross-entropy made predictions nonempty, but much too large. Reducing the
learning rate tenfold substantially improved Dice and reduced those oversized masks. These are
controlled observations on the same two training cases, not evidence of performance on unseen data.
They also show why we should not select a recipe using total loss alone.

| Experiment | Deliberate change | Updates | Mean full-volume training Dice | Interpretation |
|---|---|---:|---:|---|
| CAP-EXP-001 | Original voxel CE + foreground Dice, LR 0.003 | 100 | 0.000000 | Both final masks empty |
| CAP-EXP-002 | Equal class means in CE; other settings retained | 100 | 0.054974 | Nonempty, roughly 35× reference volume |
| CAP-EXP-003 | LR 0.003 → 0.0003 only | 100 | 0.109935 | Minimal learning indicator passes; still 16–18× reference volume |
| CAP-EXP-004 | 300 updates and matched cosine horizon 300 | 300 | **0.445999** | Full reference coverage on both cases; still 3.4–3.6× reference volume |

Every experiment starts from the same scratch parameter digest and uses the same qualified cases
3 and 26, preprocessing, model and crop policy. The first 100 crop traces match across completed
runs 001–004. The longer run changes both duration and the cosine schedule's horizon; it is not an
identical learning-rate-prefix continuation. None reuses an earlier experiment's learned weights.

## Implementation and verification

- Added an explicitly versioned, identity-bound balanced objective while preserving the original
  loss behavior. Legacy run identities reject the new objective rather than silently changing it.
- Added class contributions, probability summaries, fixed-patch logit probes and intermediate
  full-volume evaluation. These observations do not select or replace the preset final checkpoint.
- Recorded the actual scratch weight digest and made prepared launch requests single-use.
- Registered the bounded lower-LR and 300-step comparisons. Only the explicit balanced configuration
  permits up to 300 updates; legacy configurations remain capped at 100.
- Native suite: **1,089 passed**, with two existing upstream warnings. Each new real route also passed
  a native synthetic MPS rehearsal, terminal publication and independent backup/restore check.
- Test development caught a fragile float32 finite-difference oracle and inherited process-high-water
  memory in unit tests. The former now uses a deterministic float64 oracle; the latter isolates the
  unit's RSS reading while retaining boundary/subprocess tests. Production memory limits did not change.

The model is the scratch binary SegResNet with 4,700,914 parameters, batch 1, 96³ patches, fp32 MPS.
The loader repeatedly resolves qualified inputs; full-volume inference receives images only and
stitches on CPU. Reported Dice is on the complete processed 3 mm grid, not a patch-only score
or a native-grid Dice claim. Native-grid masks and contact sheets are retained for inspection. Canonical files
hold run evidence; MLflow export remains deferred. This does not complete the full production trainer.

## What remains before expanding training

A tiny smoke answers whether the protected data path, optimization, evaluation and recovery work.
Its weak pass rule does not establish a useful localizer. We should first agree on a stronger
training-case fit target and inspect localization errors, then freeze the next bounded experiment.
The final run has reference recall 1.0 on each case, but precision only 0.281/0.293.
Those measurements are now recorded alongside Dice and volume ratio. The next useful check is
whether an explicitly specified predicted region gives enough reference coverage and meaningful
volume reduction for the intended cascade; it must also be tested on separate validation data. Any target-derived measurement is
for evaluation only; inference must continue to use images alone.

Once that check is convincing, qualify a larger, deliberately varied training cohort through the
existing rules and use separately qualified validation inputs for generalization. Preserve difficult
cases and original memberships; eligibility should establish trustworthy inputs and permitted use,
not filter cases by whether the current model finds them easy. These two repeatedly optimized cases
cannot be reused as independent validation evidence.

No architecture change, lesion supervision, augmentation, threshold selection, data expansion or held-out access
was introduced overnight. No literature files, publisher message, dependencies, or Git publication
were changed by this work. The current source is still a dirty working tree; captured code and controls
are retained with the run artifacts, but a reviewed repository checkpoint remains a useful next step.

## Evidence navigation

- [Original run investigation](CAP-EXP-001-OPTIMIZATION-FINDINGS-2026-09-28.md)
- [Balanced objective comparison](CAP-EXP-002-RESULTS-2026-09-28.md)
- [Lower learning-rate comparison](CAP-EXP-003-RESULTS-2026-09-28.md)
- [Final duration comparison results and exact evidence](CAP-EXP-004-RESULTS-2026-09-28.md)
- [Living experiment notebook](../../experiments.md)
- [Decision record, D-277 through D-279](../DECISIONS.md)

## Stopping point and next discussion

The final attempt took 577.91 s including recovery, stayed below every configured limit, and
completed without retry. Its full report contains the exact request, authorization, checkpoint,
backup and restore pins. Local receipt files for all four experiments were rechecked; final-run
source/environment and first-100 crop identity checks also passed. The two final contact sheets
show much tighter localization, with visible surrounding excess foreground.

My recommendation is to retain the balanced/lower-LR recipe as a promising candidate, not declare
it the permanent recipe. First agree on what a useful localizer must achieve and plan one bounded
follow-up addressing the remaining excess foreground. Then expand qualified training diversity and
measure independent validation performance. Broad architecture or data-quality changes are not
justified by this two-case result. We have moved from preparing training to running interpretable
experiments; the next goal is a useful, separately evaluated localizer.
