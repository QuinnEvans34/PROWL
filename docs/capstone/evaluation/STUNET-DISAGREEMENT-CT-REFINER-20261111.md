# CT refiner prompted by 12k and 24k disagreement

The frozen CT refiner recovered one previously missed small lesion on the 70 exposed development scans. At the 0.50 refiner cutoff, positive-case mean Dice increased by 0.00111, while false-positive volume increased by 3.13 mL and two more reference-empty scans raised alarms. Neither cutoff satisfied the false-positive or pancreas Dice guards. The two-for-one swap never found enough eligible weak voxels to fund a refiner addition. The existing 24k core rule remains the comparator.

| Fixed arm | Positive-case Dice | Small hits /12 | Positive FP mL | Empty FP mL | Empty alarms /34 | Mean pancreas Dice |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Existing 24k core rule | .436709 | 7 | 154.519 | 47.292 | 23 | .804715 |
| Saved 12k seed only, 5 mm | .436563 | 9 | 155.193 | 47.685 | 25 | .804667 |
| CT refiner 0.50, 5 mm | .437819 | 8 | 155.299 | 49.644 | 25 | .804601 |
| CT refiner 0.70, 5 mm | .437473 | 8 | 155.121 | 48.520 | 24 | .804653 |
| Either cutoff with two-for-one swap | .436709 | 7 | 154.519 | 47.292 | 23 | .804715 |

Both refiner cutoffs added seven reference-disjoint candidates, increased FP volume on nine scans, and preserved all 39 existing lesion-component hits. The new hit grew from 57 true-positive seed voxels to 406 of 1,602 annotated voxels at 0.50, or 267 at 0.70. At 0.50 the grown candidate also added 534 false-positive voxels. The other overlapping seed had 8 of 150 annotated voxels. Neither cutoff retained a valid refinement of that seed. The other three small misses had no overlapping saved prompt. A candidate verifier would have to reject the false prompts while keeping the true ones before this route is ready for confirmation.

The replay used all 16 eligible prompts across the 70 native development scans. It proposed 12k lesion components at 0.50 that overlapped 24k raw predicted pancreas and had no voxel overlap with incumbent lesions and ranked them by older confidence, size of the disagreement, and component size. It used a native CT crop and an actual disagreement voxel as the refiner hint. Only one seed-supported component under 1 mL could be added per scan. The raw and fixed 5 mm addition arms gave identical results. The filter used the same-scan predicted pancreas remaining after the proposed relabeling, with full-affine distances. The guard also required no extra reference-disjoint components, no scan with increased false-positive volume, and no loss of existing hits or macro recall. Reference labels entered only after inference and mask selection.

The refiner weights came from the verified 2,400-step known-location pilot. Source identity, training/development split, native geometry, checkpoint backups, and comparator counts were checked. No training or GPU job ran. The final CPU replay took 93.5 s, used peak 2.42 GiB owned memory, and reaped its worker. Three stopped attempts were preserved and charged against the 900 s envelope. The corrected replay fixed the baseline policy reference, canonical pancreas target accounting, and report serialization. The final per-case journal reproduced the aggregate result exactly. Fourteen evidence files matched between the external run folder and independent internal backup. Twenty-four focused tests passed.

[Replay script](../../../scripts/diagnostics/replay_mac_disagreement_refiner_20261111.py). Verified result SHA-256 `44fc50a3ab6c48610f44c2639af177dfe0659f92225b2e3b0a31db573b360ab2`.
