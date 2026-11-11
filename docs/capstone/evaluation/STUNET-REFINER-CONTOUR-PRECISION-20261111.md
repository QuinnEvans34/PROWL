# Precision of the disagreement refiner contour

The best fixed contour rule kept the additional small-lesion hit, increased positive-case Dice from .436709 to .437643, and reduced total false-positive volume by 0.621 mL. No scan's false-positive volume increased and the number of reference-empty scans with an alarm remained 23. The rule still introduced one reference-disjoint lesion candidate on a scan that already had an alarm. It therefore failed the stricter requirement of zero new false candidates. The existing 24k core rule remains in use.

| Arm | Positive-case Dice | Small hits /12 | All-scan FP mL | Empty alarms /34 | Scans with more FP | New false candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Existing 24k core rule | .436709 | 7 | 201.811 | 23 | 0 | 0 |
| Untrimmed refiner, fixed 5 mm | .437819 | 8 | 204.943 | 25 | 9 | 7 |
| 0.65 score within 3 mm, add only | .437715 | 8 | 203.366 | 25 | 9 | 7 |
| Same trim, remove one weak voxel per addition | .437640 | 8 | 201.714 | 23 | 0 | 1 |
| Same trim, remove two weak voxels per addition | .437643 | 8 | 201.190 | 23 | 0 | 1 |

The trim reduced the recovered lesion's proposed contour from 940 to 651 voxels. It retained 297 of the 406 true-positive voxels from the untrimmed refiner, and removed 180 false-positive voxels from the proposed contour. The retained contour still contained 354 false-positive voxels. The two-for-one rule offset that tissue by removing 1,172 false-positive and 130 true-positive voxels from the incumbent contour on the same scan. The existing lesion stayed detected, and mean pancreas Dice increased from .804715 to .804780. The one-for-one rule gave almost identical headline Dice and removed fewer true-positive voxels (74).

The remaining false addition exchanged 427 added voxels for 854 removals on an already-alarmed reference-empty scan. Its net false-positive volume fell, even though it gained a false lesion candidate. An exploratory follow-up required an existing 50 mm³ connected lesion core supported by both saved checkpoints (12k at 0.60, 24k at −0.50 margin). It admitted both the true and false additions. This follow-up used the same development cohort after the primary screen.

## Replay and safeguards

The prior archive retained per-scan counts, so nine frozen CPU forwards reconstructed the nine accepted contours. Every original lesion and pancreas count was reproduced before scoring. Sparse contour indices and scores were saved with native affines. Six fixed trims combined prompt intersection or a local score cutoff with full-affine distance to the saved prompt. Each was scored with raw addition, fixed 5 mm addition, and one-for-one and two-for-one same-scan weak-voxel removal, for 24 arms. Removed voxels supported by the raw 24k pancreas were returned to that label. References entered only after all edits had been decided. The identical 70 exposed development scans were scored. Neither the refiner nor the thresholds were fitted on these cases.

The primary replay took 34.2 s at 2.40 GiB peak owned RSS. The agreement check took 10.7 s and used saved prediction archives without model forwards or reference-mask reads. Both workers were reaped. Eighteen evidence files and the MLflow snapshot matched independent backups. MLflow run `516c9d0452a1455e92ad92bbd11a390e` is FINISHED with metric readback verified. No training, GPU execution, or deployment occurred.

[Contour replay](../../../scripts/diagnostics/screen_mac_refiner_contour_precision_20261111.py) · [Exploratory agreement check](../../../scripts/diagnostics/screen_mac_contour_agreement_gate_20261111.py). Primary result SHA-256 `8ab814083241c7a9336ccc2dbc2058877ea39a5bd903b17d5f15f51758f63c24`.
