# D-288: source-grid coverage inspection

Quinton: “Great, continue with the inspection and anything else you deem important.”
Codex scope: diagnostic implementation, retained-evidence review and one bounded source-grid audit,
then document evidence and next experiment/cohort recommendations. No training or new inference.

## Questions and fixed checks

Compare the saved final CAP-EXP-005 and006 native predictions against the same original qualified
pancreas references. Verify receipt/member hashes, source/prediction shape/affine/units, source
provenance and recorded native foreground. Recompute source-grid overlap independently. Compare
native recall/Dice with the retained processed-grid metrics, allowing measured resampling differences
rather than requiring numerical equality. Large coverage loss persisting natively supports a model
failure rather than a processed-grid-only artifact; it does not prove absence of every geometry bug.

Use a fixed10mm prediction-only bounding margin, rounded upward per native voxel-axis spacing.
This differs in rounding from12mm realized on3mm processed grids; label native box results as a
separate diagnostic, never overwrite prior scores. Report missed reference fractions outside each
box face (faces may overlap), centroid offset, connected components and their overlap with reference.
For components, report counts, largest component fraction and false-positive-only component volume.
Reference overlap categorizes components after prediction; never use it to choose a deployed mask.
No threshold sweep, margin search, largest-component adoption, eligibility change or model promotion.

Check all16 train/11 development-validation cases, compare both runs, and summarize existing
phase×spacing strata plus physical size/coverage. Metadata associations are descriptive with tiny
cells, not causal or generalization claims. Preserve held6350 and missing-metadata status.
Generate source-grid overlays at planes through missed reference when available, otherwise reference
median planes. Those are explanatory reference-informed review views, never inference inputs.

## Scope and limits

Exact54 previously qualified CT/pancreas source files, once each using the D-283 role-safe native
loader and unchanged1GiB compressed/4GiB expanded/64m-voxel caps. Read54 saved native prediction
artifacts (27/run), bounded96MiB per artifact, and pinned local run/selection records. No source or
registered-artifact writes; new JSON/PNG evidence in outputs/prowl only, max256MiB. CPU only,
20min wall,16GiB RSS,100GiB internal free floor. Supervisor stops on failure and retains incomplete
evidence. No automatic retry after source reads. Save source/environment/design pins before reads,
verify again at end and hash all outputs. Neither case selection nor production model policy changes.

## Implementation and acceptance

Own new src/training/localizer_coverage.py, scripts/diagnostics/localizer_coverage_inspection.py,
tests/test_localizer_coverage.py and related operations/evidence documents. Preserve production
training/loader/evaluator code and Claude's lane. Synthetic tests cover exact/empty/missing masks,
anisotropic and flipped axes, distant false components, input mutation, nonbinary/shape/affine
refusals, face-accounting and zero-reference refusal. Native suite before source job.
Job success requires all27 pairs for both runs, exact54 source reads, valid export/source bindings,
independent overlap results and complete hashed evidence. Clinical contour acceptance is out of scope.
