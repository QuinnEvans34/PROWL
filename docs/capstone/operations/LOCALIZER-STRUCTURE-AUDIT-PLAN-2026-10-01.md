# Retained localizer structure audit

October 1, 2026 — D-314. Approved bounded diagnostic; no new training or adopted cleanup.

## Question and exact scope

Does disconnected foreground drive oversized crops, or does the largest connected region already
span most of the box? Compare CAP-EXP-010 and CAP-EXP-012 at child step 300: all 40 development
validation cases plus training cases 150, 756, 6110, 6822, 7604 and 7684. This is 46 paired cases,
92 retained native binary exports, not a new evaluation cohort. Selection precedes measurement.

The existing sealed review receipts pin case records and the completed execution receipts pin
their native files. Verify receipt hashes, review case-file hashes, native row identity and bytes,
shape, affine, millimeter units and foreground count. Prepare an immutable exact request after
the helper tests; consume it once before array reads. Keep any failed attempt visible.

## Method and limits

Use deterministic 26-connected components; rank descending by voxel count, ties by label discovery
order. Record physical component volume, half-open source bounds, margin-expanded bounds clipped
to the acquired scan, largest-component foreground share and components controlling each union
box face. The 10 mm diagnostic margin matches the retained evaluation. Report hypothetical
largest-only crop fractions and retained-prediction fractions without changing any raw mask.

Broad connected foreground is a structural finding, not an anatomical diagnosis. The audit has
no component-specific reference overlap. Existing whole-mask reference counts support only bounds:
largest-component true positives lie between max(0, whole-mask TP minus discarded voxels) and
min(whole-mask TP, largest-component voxels). These bounds are not measured cleanup recall.
Never call a hypothetical small box a passing ROI based on size alone. No lesion pruning.

CPU only, serial masks, maximum 96 million voxels per native array. Label volume int32, count
slabs avoid an int64 copy of the whole label volume. At most 100,000 components per case; exceeding
that analytical budget records a failed case and prevents a complete receipt rather than removing
the case. No selection on ease/quality. Every requested member receives a terminal record.

Budget: 1,200 seconds total, 8 GiB peak RSS, 50 MiB derived output, exact summed compressed bytes
and expanded voxel payload in the request. No GPU, checkpoints, cached CT, raw CT or original
labels. Source/runtime/helper/runner hashes are pinned. Check limits during execution; completion
is written last, with output hashes and verified input inventory. Do not replay consumed requests.

## Acceptance and next decision

Synthetic tests independently cover diagonal connectivity, separated outliers, broad dense regions,
deterministic ties, physical anisotropy/permuted axes, clipping, empty masks, invalid geometry/binary
values and immutable input. Runner tests cover changed pins, wrong member/stage, traversal/symlinks
and consumed requests. A small synthetic CPU profile validates the chosen implementation budget.

If disconnected regions account for substantial box inflation, propose a separately identified
component-policy coverage experiment with fresh qualified references. If the main component itself
dominates the box, focus the next model investigation on spatial discrimination rather than expecting
component deletion to solve it. In either case, prepare Stage 2 independently; do not spend another
long run guessing loss weights. This audit does not satisfy G4 or held-out generalization.
