# D-288 inspection amendment: acquired-scan crop-size accounting

Discovered after the bounded native audit completed. Quinton authorized inspection and other
important follow-up; Codex implements this correctness correction under D-288. The initial frozen
audit request/design/source remain preserved. This is a subsequent metadata-only derivation and
small evaluator extension, not a source-job rerun or new training/inference request.

## Finding

`expanded_executor.metrics.scan_fraction` computes box voxel volume divided by the processed tensor
volume. Preprocessing symmetrically pads short dimensions to at least96. Consequently this fraction
is not necessarily the fraction of acquired CT retained by a crop. The earlier pre-mapping ROI
screen was explicitly processed-grid/provisional, but interpreting its size term as acquired-scan
fraction is wrong. This issue does not explain the major validation recall loss; the independent
native-reference audit reproduces that loss.

Holding the EXACT processed box fixed, mapping its voxel edges through the recorded affines,
rounding outward to native voxel edges and clipping to source bounds yields:

| CAP-EXP-005 case | Padded-tensor fraction | Acquired-source fraction |25% size screen |
|---|---:|---:|---|
|26 train|20.58%|26.66%|pass→fail|
|4226 train|20.25%|40.12%|pass→fail|
|4995 validation|18.95%|25.014%|pass→fail (borderline)|
|7484 validation|21.34%|35.34%|pass→fail|
|7687 validation|24.89%|25.51%|pass→fail|

No CAP-EXP-006 size-screen result changes at25% under this same-box correction. This is distinct
from the audit's native-mask10mm box, which re-rounds margin on native spacing and can have different
bounds. Neither calculation overwrites the original processed-grid metrics or claims native
reference coverage for a newly mapped crop without measuring it.

## Implemented correction

- `localizer_coverage.mapped_source_box`: prediction-box geometry only, no target/policy lookup.
  Version `source-crop-geometry-v1`; supports signed axis permutations/scales; rejects unsupported
  oblique/sheared relative transforms, singular affines, out-of-bounds/fractional boxes and oversized
  shapes. Maps half-voxel edges, snaps tiny integer roundoff, rounds outward and clips to source.
- Expanded evaluator now emits `source_crop_geometry` and `source_size_diagnostic_pass` for every
  evaluated case, and labels `scan_fraction_scope` explicitly as padded processed tensor space.
  These fields persist in trajectory/export records and are checked by existing terminal bindings.
  The acquired-source size gate also requires positive crop volume, rejecting padding-only boxes.
- Old fields remain for historical compatibility. Their `pre_mapping_roi_diagnostic_pass` is not a
  native-crop acceptance gate. New launches/ROI policy work must use acquired-source crop size plus
  independently defined source-reference/lesion containment, not the legacy provisional conjunction.
- No threshold, margin, mask, cohort, objective, training schedule or CAP-EXP-006 result was changed.
  No production ROI policy or stage2 acceptance was selected.

## Evidence

20 focused coverage tests include7 new geometry cases: padding invariance, flipped anisotropic axes,
clipping, empty region, padding-only boxes and refusals; the expanded CPU transaction verifies new fields through
terminal/export publication. Full native suite result is recorded in the main inspection report.
Same-box derivation covers all54 retained final case records after hash verification:
`outputs/prowl/coverage-inspection-review-20260929/same-box-source-geometry.json`.
Native audit source and this later metadata derivation have distinct source pins. No raw reread.
