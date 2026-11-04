# Completed seven-case visual error review

The Lenovo rendered and actually inspected all 26 selected native contact sheets.
The Mac then received the private gallery, verified its exact inventory and hashes,
and inspected nine key sheets covering all seven selected cases. KD continued
through 14,384 updates with teacher access and stored MLflow metrics verified.
No training, inference, scoring, threshold or scientific recipe changed.

## What the images show

| Pattern | Direct Mac observations | Implication for later investigation |
| --- | --- | --- |
| Missed lesion labels despite pancreas localization | Selected yellow components in 4681, 8769, 6755 and 2889 remain unoverlapped near or within the pancreatic contours. In 6755/2889 another component has partial overlap elsewhere. | Better pancreas localization alone does not establish recovery of these missed labels. |
| Predictions far from the reference pancreas | In 4681, a posterior magenta island and extra cyan pancreas label are spatially separate from the reference pancreas. In 8769, a large magenta/cyan region is well superior to it. | Investigate remote false positives separately from pancreatic lesion delineation. A model's own pancreas prediction is not automatically a reliable filter. |
| Extra lesion labeling within or beside the pancreatic contours | Reference-empty 6880 has a large magenta crescent within/adjacent to the pancreatic outlines. Lenovo inspected two additional smaller foci there. | Restricting the field of view would not remove every observed extra lesion prediction. Empty reference does not establish clinical health. |
| Extensive spillover attached to a partly overlapping lesion prediction | In 8711, green overlap is concentrated inferiorly; a much larger magenta component extends along the pancreatic region, with some yellow reference still missed. | A queue limited to wholly zero-overlap components misses a major error class. Saved counts for this component are 20,503 predicted, 3,378 overlapping and 17,125 extra voxels. |
| Annotation beyond the parenchyma contour | The selected 2235 reference component lies anterior to and spatially separated from both displayed pancreas contours. Native through-plane sampling is visibly coarse. | A strict pancreas-parenchyma mask cannot be assumed to preserve every saved lesion annotation. Tissue identity and annotation correctness require qualified adjudication; neither is decided here. |

The saved cohort metrics already established full annotation containment inside the
expanded evaluation region. These images distinguish where the model labels fail;
they do not establish a failure mechanism or prove that fine detail survives every
model preprocessing/resampling step. Fixed-window CT texture, coarse sampling,
training and optimization remain hypotheses rather than demonstrated causes.

The two previously transferred 4681/6755 miss sheets were also reinspected, after
their autonomous score bytes were shown to match the completed baseline exactly.
Both older supplied-region rows missed the same selected targets. That is useful
context, not a new controlled comparison or a matched autonomous-versus-KD result.

## Unresolved findings and limits

- Cases 6755 and 2889 have strikingly similar anatomy and image artifacts in the
  inspected views despite distinct recorded files and geometry. Shared patient or
  source identity is **not established**. No new duplicate audit, cohort exclusion
  or score change was performed. Do not infer independent anatomy from IDs alone.
- Two tiny 2235 predictions are visible axially, but the ROI boundary line obscures
  their orthogonal overlay pixels. Lenovo recorded this display limitation; those
  images were not regenerated to conceal it.
- Representative component-centered slices are not an exhaustive scan review,
  clinical diagnosis or annotation adjudication. Unknown reference-unit assumptions
  remain visible. Exposed-development role and the original probability-equivalence
  **UNQUALIFIED** exception remain unchanged. Independent acceptance/G3 stays open.

The useful next comparison is to apply these same error categories to the completed
KD outputs when available, with matched inference scope and fixed cohort. Possible
localization, lesion-discrimination or false-positive-suppression changes need
separate tests; this review selects no new threshold, crop, model or experiment.

## Evidence and recovery

- Original plan `1b81693`, additive spillover-target amendment `61eb806`.
- Lenovo renderer/tests `57a29d5`; reporting recovery `255241f`; inspected report
  `f251ab0`, final shared closeout `96d2f78`. See the
  [immutable peer visual report](https://github.com/QuinnEvans34/PROWL/blob/f251ab0/docs/capstone/operations/WEEK-05-SEVEN-VISUAL-REVIEW-20261104.md).
- [Mac inspection receipt](WEEK-05-MAC-VISUAL-REVIEW-20261104.json) lists the nine
  newly inspected sheets and observations. All 26 image hashes, seven case/report
  bindings and 78 recovered plane/world-coordinate transforms checked here.
- Private archive: 15,370,240 bytes, SHA256
  `a2fcfb586d881e0b0373ff69b6d3ac3c50ceec920f1f895e3b7a980731cbc444`.
  Strict importer verified 31 declared payload members plus the transfer manifest.
  Final review JSON SHA256
  `6769a04712874b737f79922c11b3de1fdfc5ea79fdcda92b0695eb09473ab0c0`.
- Private gallery and import receipt:
  `outputs/prowl/autonomous70-visual-review-20261104-01/`.
  Imaging pixels, CTs, masks, weights and transfer codes are absent from Git.
- Original CPU worker produced all images in 296.406 seconds, peak owned RSS
  1,183,797,248 bytes, then exited 1 during NumPy integer JSON serialization.
  The failure, original pinned renderer and partial manifest remain preserved;
  the worker was reaped and never rerun.
- First metadata salvage used saved complete JSON fields/logs/images only. A
  separate 47.593-second recovery reconstructed full-precision plane metadata
  from the exact bound masks/headers using the frozen display functions. No CT
  voxels or model were read for recovery; no images were regenerated. It exited 0
  and was reaped. Cumulative charged worker/recovery time was 373.999 seconds,
  including a conservative 30-second first-salvage allowance, within 1,200 seconds.
- Lenovo reports ten passing geometry/display/serialization tests, preserved
  producing pins, verified independent backups and no surviving review workers.
  The original renderer remains truthfully failed; the saved-image visual review
  and separate metadata recovery are complete. Lenovo is idle.

Mac source integration was not required: peer code was inspected through Git and
the private packet was imported using the existing strict transport tool. The
active KD checkout, frozen recipe, receipts and cumulative budget stay intact.
