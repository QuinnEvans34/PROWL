# STU-Net checkpoint review spec

The 40k validation reported better detection in the five development scans with less than 1 mL total annotated lesion volume. Any-overlap case hits went from 3/5 to 4/5 and component hits within those five scans went from 3/6 to 5/6. Mean Dice in the group was .0713. This motivates tracking whether the same lesions stay detected at later checkpoints and whether the extra detections come with more false positives.

## Code to build

Add a read-only command for comparing two saved native reports. Reuse the existing [native report and component validation](../../../src/training/native_error_review_v1.py). Use the verified 32k report and component-level outliner rows as a saved-output fixture. Keep a separate test for legacy reports with aggregate component counts only. Reconcile step, cohort, reference identity, geometry, and scoring policy before treating rows as matched. Score raw against raw and the [fixed 5 mm policy](SEGMENTATION-POSTPROCESSING-POLICY-V1.md) against the same policy.

- Report whole-cohort positive-case Dice and voxel recall, reference-empty alarms, total false-positive volume and the number of scans where false-positive volume rose.
- Report the small-total-volume scan group and the all-cohort sub-1 mL reference component group with their own denominators. For component-level comparisons, list newly hit and lost reference components, even if the net hit count is unchanged. If component identities were never saved, mark that comparison unavailable and show the case-level results that can be verified.
- Group positive scans by whether overlap was newly found, lost, present at both checkpoints, or absent at both. For scans with overlap in both, show changes in true-positive and false-positive tissue alongside Dice. This separates detection changes from changes in contour overlap.

## Completion checks

- Reproduce the verified 32k metrics and small-component loss from the [saved outliner comparison](STUNET-32K-OUTLINER-REPLAY-20261111.md).
- Catch mismatched cohorts, references, geometries, and raw-versus-filtered inputs. Cover missing component data and a same-count swap where one component is gained and another is lost.
- When comparable Lenovo reports are available, run the command for 38k versus 40k, then 40k versus the next complete validation. Report the exact denominators, available evidence, and false-positive trade-offs. Treat these as exploratory development results.

Estimate 1–2 hours for the command and verification. Use saved reports and test fixtures on the Mac while Lenovo training runs. This work needs no new inference or checkpoint transfer. The [14k replay and matched supervision study](STUNET-OVERNIGHT-DICE-QUEUE-20261111.md) remain separate GPU work.

## Running the review

Use [compare_stunet_checkpoints.py](../../../scripts/diagnostics/compare_stunet_checkpoints.py) from the repository root. The command prints JSON and only opens saved metadata.

```sh
python scripts/diagnostics/compare_stunet_checkpoints.py bundle BUNDLE.json 38000 40000
python scripts/diagnostics/compare_stunet_checkpoints.py --policy predicted-pancreas-proximity-5mm-v1 outliner REPLAY_DIR OUTLINER_DIR
```

Bundle mode uses saved reports and frozen per-case source hashes, shape, affine, and tile count. An optional `--candidate-bundle` supplies a separate report and set of identities. Use the same policy for both arms. A fixed 5 mm export must carry the policy config hash and per-case application status. Raw-only historical reports can still support voxel and case comparisons and aggregate component counts. Exact component gains and losses require hit IDs. The all-cohort sub-1 mL component counts also require small-component IDs.

## Verification

The command reproduced the verified 32k trim comparison in both raw and fixed 5 mm arms. Dice, recall, pancreas Dice, false-positive volume and empty alarms matched the saved summary. The fixed 5 mm comparison moved Dice from .415860 to .417621, with no increase in false-positive volume on any scan and one lost small reference component. That hit loss reduced small-component detection from 5/12 to 4/12. The historical 18k versus 24k raw reports reproduced .430517 and .411972 Dice and correctly reported component identity comparison as unavailable. The new and existing native review suites passed 39 tests and 6 subtests.

## Lenovo results through 42k

The [verified Lenovo bundle](../coordination/STUNET-38K-40K-42K-NATIVE-METADATA-20261112.json) contains complete raw reports for the same 70 scans. The initial export contained CT hashes only. The command rejected it, and the corrected export includes all three source hashes from the frozen inputs. The archived reports record counts without component IDs, so the tool identifies changed scan-level overlap and reports component totals. Exact component gains and losses and fixed 5 mm results are unavailable for these checkpoints.

| Metric | 38k | 40k | 42k |
| --- | ---: | ---: | ---: |
| Dice, 36 positive scans | .377426 | .411317 | .422996 |
| Macro voxel recall, 36 positive scans | 43.10% | 64.64% | 51.06% |
| Positive scans with overlap /36 | 32 | 35 | 33 |
| Reference components with overlap /45 | 35 | 40 | 38 |
| Scans with overlap in the <1 mL group /5 | 3 | 4 | 4 |
| Components with overlap within those five scans /6 | 3 | 5 | 4 |
| Dice within those five scans | .055434 | .071344 | .070182 |
| False-positive volume across all 70 scans | 185.071 mL | 454.391 mL | 213.284 mL |
| Alarms on reference-empty scans /34 | 26 | 28 | 28 |

At 40k, three scans gained overlap and none lost it. False-positive volume rose on 56 of 70 scans. At 42k, the newly detected <1 mL scan retained overlap and the two newly detected medium-volume scans lost it. The 33 positive scans with overlap at both 40k and 42k gained .015924 mean Dice while losing 26,786 true-positive voxels and shedding 175.194 mL of false-positive tissue. The longer run so far shows a trade-off between detection, recall, and excess tissue. Use the same measures at 48k before choosing a checkpoint for further work.
