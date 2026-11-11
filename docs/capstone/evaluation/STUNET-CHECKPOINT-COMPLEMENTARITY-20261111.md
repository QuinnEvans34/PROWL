# Small-lesion checkpoint comparison

The saved 24k core rule found 7 of 12 reference components under 1 mL on the 70 exposed development scans. None of the five misses intersected even the most permissive saved 24k margin decision (+1, before proximity filtering). The archived decisions cover five discrete margins, so a miss here does not establish the absence of weaker model signal.

The saved 12k output overlapped two of those five misses after its fixed 5 mm pancreas filter. Its raw connected components recovered 74 of 1,602 lesion voxels (4.6%) and 8 of 150 (5.3%). At the 0.50 cutoff, the remaining overlaps were 57 and 8 voxels. The 24k raw output labeled every one of those 65 overlapping voxels as pancreas. At 0.60 the older output retained four overlap voxels in the first component and zero in the second, with the same pancreas conflict. The other three small misses had no overlap with the older raw output either.

## Fixed replay on saved outputs

Tested four rules combining 12k cutoffs of 0.50 and 0.60 with removal of one or two weak 24k lesion voxels per added voxel. Each rule could add at most one disconnected 10–1,000 mm³ candidate per scan with an existing 24k lesion call. Candidate generation used only saved predictions. It excluded 24k raw pancreas voxels and required a candidate within 5 mm of the same-scan predicted pancreas in physical coordinates. Removal was limited to weak 24k lesion voxels without 12k lesion support, ordered by margin and distance from the 24k core. Reference masks were loaded after the candidate outputs were decided.

| Rule | Positive-case mean Dice | Small components hit | Positive-scan FP mL | Empty-scan FP mL | Empty-scan alarms /34 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing 24k core rule | 0.436709 | 7/12 | 154.519 | 47.292 | 23 |
| 0.50, remove 1 per voxel added | 0.436433 | 7/12 | 154.529 | 47.292 | 23 |
| 0.50, remove 2 per voxel added | 0.436530 | 7/12 | 154.327 | 47.112 | 23 |
| 0.60, remove 1 per voxel added | 0.436684 | 7/12 | 154.525 | 47.292 | 23 |
| 0.60, remove 2 per voxel added | 0.436717 | 7/12 | 154.412 | 47.193 | 23 |

The last rule's Dice gain was 0.000008, with 11 fewer true-positive voxels and slightly lower macro recall (0.542689 to 0.542530). None passed the combined Dice, small-lesion detection, recall, and false-positive criteria. The existing rule remains the comparator. Matching aggregate false-positive volume does not guarantee that every scan avoids new false-positive tissue.

## Next experiment

Use 12k–24k disagreements inside the predicted pancreas as **candidate locations** for a high-resolution CT refiner or verifier. Preserve the incumbent output while testing whether CT evidence can distinguish those locations from matched disagreement candidates on reference-empty and lesion-positive scans. Train any verifier on training patients only. Evaluate newly found small components and Dice alongside positive/empty false-positive volume, empty-scan alarms, existing hits, and pancreas Dice. Confirm any winning rule on a patient-disjoint set unused in development. This tests the two cases with available checkpoint signal. The other three motivate a separate small-lesion training or proposal-recall experiment.

The replay checked all 70 source identities and native grids across the checkpoints, replayed the existing 24k core metrics exactly, and verified both archives against independent copies. CPU time was 85.6 s with peak owned RSS 1.52 GiB and all workers reaped. No CT inputs, model forwards, training, or protected test cases were used. Results use exposed development cases and reference overlap as the component-hit definition.

[Replay script](../../../scripts/diagnostics/screen_stunet_checkpoint_swaps_20261111.py). Full local result SHA-256 `48d1b466027246f60891880a9645809b94cb36344bc0af6f612810ce71220939`.
