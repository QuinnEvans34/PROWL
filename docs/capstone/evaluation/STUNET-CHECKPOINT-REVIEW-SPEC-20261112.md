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
