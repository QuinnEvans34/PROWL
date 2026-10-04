# CAP-EXP-002 proposal — isolate cross-entropy class balance

**Proposed after D-276; not yet implemented or launched.** This replaces the tentative lower-LR-first
recommendation with a comparison grounded in the retained checkpoint diagnostics. Approval of the
investigation is not represented here as approval of this new recipe.

## Question

With everything else held fixed, does equal foreground/background weighting in CE allow measurable
pancreas localization within100 updates on the same two cases, rather than primarily suppressing
foreground probabilities? This is a training-set mechanics/learning diagnostic, not generalization.

## Exact intended change

Keep foreground soft Dice loss unchanged. Replace the voxel-averaged CE term with:

`balanced_CE = 0.5 * mean(-log(p1) where y=1) + 0.5 * mean(-log(p0) where y=0)`

Compute via stable logits/log-softmax, not manually clamped training probabilities. Give each class
half the CE weight when both classes occur. If only one class exists in a patch, use that class's
ordinary mean CE; retain the existing empty-target Dice policy. This avoids division by zero and
does not fabricate positive targets. Both real cases' replayed patches contained both classes.
No weight search or outcome-selected weighting: this is the prespecified equal-class comparison.

Hold fixed CAP-EXP-001's exact qualified cohort/input/recipe pins, protected roles, model architecture,
scratch seed42 initialization, deterministic crop keys and member order,96³/batch1/fp32 MPS,
AdamW LR0.003/weight decay1e-5,cosine T_max100,100 updates, no augmentation/cache/workers,
image-only full-volume inference, binary argmax and native-grid restoration. Verify that newly created
scratch weights match the original step0 parameter digest; do not initialize from its checkpoint.

## Measurements and interpretation

- Preserve all original per-case/full-volume argmax Dice, predicted/reference counts, source-grid
  masks and overlays. Empty-reference policy remains null, not an invented score.
- Report **both objectives** on every checkpoint's evaluation: original unweighted CE+Dice and new
  balanced CE+Dice, with named foreground/background contributions. Their absolute loss values are
  not interchangeable. Compare the new objective's own before/after values, and use the common Dice
  metric when comparing experiments.
- Keep the preset learning indicator structure: at least10% reduction in this run's named evaluation
  objective AND mean full-volume Dice improvement at least0.10. Also require complete mechanical and
  backup/recovery checks. A nonempty but oversized prediction is not automatically a good result.
- At steps0/25/50/75/100 record foreground/background probability summaries and Dice on both cases,
  plus the fixed-patch local derivative probes used in D-276. These are observational; no tuning,
  early selection, schedule change or extra optimizer update follows from intermediate results.
- Record target fraction per training patch. Keep diagnostic thresholds separate; no threshold
  selection or retrospective replacement of the original argmax endpoint.

## Bounded implementation before launch

1. Add an explicitly versioned loss choice without silently changing CAP-EXP-001's loss/config;
   preserve old checkpoint readability and original source evidence.
2. Test stable CE against hand-computed class means, duplication invariance within a class,
   empty/all-positive fallbacks, correct gradients and the untouched original loss.
3. Bind the loss choice and objective-aware metric definition in new plan/config/run/checkpoint
   controls. Reject loading state under a different objective. Preserve checks for wrong roles,
   mismatched inputs and unavailable MPS. Keep the original consumed launch request closed.
4. Verify the new path with synthetic fixtures and a bounded native check, then prepare the concrete
   real request with source/environment bindings. No implicit launch while changing these contracts.

## Candidate real-run budget and next decision

Use one fresh attempt,100 updates,600s update phase/1,200s overall,16GiB limits,1GiB new bytes per
domain, existing disk floors and AC/exclusive MPS lock. Ten full-volume evaluations and ten fixed-
patch probes maximum; complete checkpoints0/25/50/75/100 and terminal independent backup/restore.
No automatic extension/restart. The extra telemetry must fit these bounds, otherwise revise before
launch. Freeze the implementation-backed request before execution.

If this improves Dice materially, inspect per-case false positives and then choose whether to repeat
or expand qualification. If it does not, retain the null and next isolate schedule/horizon or LR.
Do not change loss, LR, patch size and training duration together and lose the explanation.
