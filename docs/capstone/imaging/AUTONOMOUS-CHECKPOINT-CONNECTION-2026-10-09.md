# Trained checkpoint connection — October 9, 2026

**Outcome:** Two CT-only development diagnostics completed using the actual localizer and segmenter.
Native output shapes/affines match both inputs. This establishes a working trained-model connection,
not acceptable segmentation quality, clinical readiness or a leakage-free benchmark.

## Implementation

- `src/inference/cascade_models_v1.py` verifies inference-weight SHA256, exact role/architecture,
  finite float32 tensors and strict state loading. Models are evaluation-only with gradients disabled;
  no optimizer is created. Payloads with optimizer fields are refused.
- `scripts/predict_autonomous_ct.py` requires exact CT-only request fields and pinned localizer/segmenter
  weights. A Python audit hook installed after model loading permits the named CT, output directory,
  installed libraries and source code; other file opens fail. It is an access tripwire, not an OS sandbox.
- Existing `autonomous_cascade_v1` performs whole-input localizer inference, predicted-region cropping,
  segmentation and native hard-mask export. No reference labels, precomputed reference crops, cohort
  manifest or diagnosis are supplied to the prediction worker.
- Fresh inference-only model bundles were derived from verified checkpoint tensors; their loaded
  tensors were compared exactly to the checkpoint model state. Source checkpoints remain unchanged.

Six focused loader/inference tests passed in1.45s (two upstream TorchScript deprecation warnings).
These cover exact state import, wrong hash/head rejection, optimizer/nonfinite payload refusal and
existing CT-only behavior. Actual-model diagnostics below are additional evidence.

## Models and lineage

| Component | Selected artifact | Verification |
|---|---|---|
| Localizer | CAP-EXP-012 child step300, absolute600 | Pinned artifact completion receipt and state; binary SegResNet,144-cubed sliding window, overlap0.25,2mm whole-input preprocessing |
| Segmenter | Full SuPreM Mac best checkpoint at14,000 | Original checkpoint SHA verified; strict three-class SegResNet state;144-cubed geometryv2,1mm intermediate sampling,10mm predicted margin |

Localizer completion receipt SHA256:
`c8a9c80d080a22134033d5868a5323cb8ff6cbd3d131d815352113561d08b4cf`.
Localizer source state SHA256:
`c4d8b62cbe623036c45a434771c5853764d2c95bdb08e2fd0d95e22923701595`.
Segmenter source checkpoint SHA256:
`89847675d2e4637571970ca662b74247e49e652d7b502ea1a800ac9b8d44e5c8`.

Localizer ancestry was followed through its retained parent reference to the cd6be21f run, verifying
completion and input/identity metadata hashes on both artifacts. Child and parent each list113
training cases. Their union has zero case-ID overlap with the segmenter's75 development cases;
that development set is also disjoint from the segmenter's training members. No additional parent
reference is recorded on the base artifact. This metadata review does not establish biological
patient independence or resolve SuPreM pretraining/selection membership.

Both selected checkpoints have prior development-selection history. These are integration diagnostics,
not a new untouched test cohort, and the source-use review's development-only limitation remains.

## Diagnostics and retained failures

| Attempt | Case / selection | Result | Sampled owned peak / wall time |
|---|---|---|---|
| A01 | PanTS_00001389; smallest admitted development CT by native voxel count, then ID | Native export succeeds; visual CT inspection appears to show head anatomy, while models predict pancreas/lesion classes. Unsuitable-anatomy issue retained | 701,579,264 bytes /2.863892s |
| A02 | PanTS_00001070; smallest admitted development CT with20M–96M voxels, after A01 finding | Abdominal anatomy visible; native export succeeds; accuracy unscored | 1,509,916,672 bytes /3.336852s |

Both supervised workers finished/reaped under the600s/12GiB ceilings. No optimizer updates occurred.
Timing covers each process, not the source preparation/model export step; do not generalize these
small-case timings to the full cohort. A02 was selected after viewing A01; this is explicitly adaptive
diagnostic selection, not a representative estimate or hidden exclusion of A01.

A01 source shape110×125×116, output classes0/1/2 contain1,550,526/24,161/20,313 voxels.
A02 source shape426×301×157, output classes0/1/2 contain19,968,840/156,262/6,380 voxels.
Both output affines equal the input affines; crop provenance is `predicted_region`. Input-access logs
permit only each isolated CT as a data input. Neither reference masks nor training caches were opened
by inference. CT copies matched hashes from the existing pinned preparation metadata.

**A01 issue:** The visible scan appears non-abdominal. The correct source file/hash was copied, so
this is not evidence of a copy mismatch introduced by the new runner. Its original dataset membership,
annotation pairing and upstream source provenance still need investigation. Do not assume a label defect
without reading that evidence, silently remove the case, or report its generated labels as valid anatomy.
The present models lack an adequate out-of-scope-input response on this example.

## Local private evidence

`outputs/prowl/autonomous-real-ct-20261009/` (ignored, not published) contains:

- checkpoint-review.json: complete localizer training-membership ancestry, model identities and limits;
- request.json/request-a02.json; pinned localizer.pt/segmenter.pt inference-only derivatives;
- ct-only/ct.nii.gz and ct-only-a02/ct.nii.gz: exact isolated source CT copies, no masks;
- prediction-a01/ and prediction-a02/: native prediction.nii.gz, result.json and input-access.json;
- resources-a01.json/resources-a02.json and inference logs;
- output-inspection.json/output-inspection-a02.json and prediction-preview images;
- preparation and supervised-run helper source retained for reproducibility.

A02 example invocation (already completed; choose a fresh output path for an intentional new attempt):

```sh
PYTORCH_ENABLE_MPS_FALLBACK=0 .venv-prowl/bin/python scripts/predict_autonomous_ct.py \
  --request outputs/prowl/autonomous-real-ct-20261009/request-a02.json
```

The direct CLI has no long-job supervisor; real diagnostics here used the retained outer watchdog and
shared accelerator lock. Do not replay completed requests or overwrite their result directories.

## Next work

1. Investigate the A01 source/annotation mismatch or unsupported anatomy, preserving its original role.
2. Build a separate scorer that reads saved predictions and references without altering predictions.
3. Evaluate a fixed eligible development set, retaining failed and unsuitable inputs in accounting;
   compare predicted and reference regions under the same native-grid metrics.
4. Add a supported-input/failure policy based on evidence, then review generalization and holdout
   limitations before any Johns Hopkins performance claim.

Lenovo training was untouched. No weights/data were published and no external messages were sent.

## October 9 debugging: independent native scoring and matched crop diagnostic

Added `src/inference/saved_prediction_scoring.py`. It reads saved predictions and pinned references
without importing models or changing predictions. It rejects changed bytes, incompatible grids,
invalid codes and unsupported units. Empty lesion references produce undefined Dice/recall plus false
positive volume; they are not treated as verified healthy cases. Four focused tests passed, including
known overlap arithmetic, lesion precedence, grid/hash rejection and explicit unknown-unit handling.

Both original pancreas masks declare unknown spatial units; both CTs and lesion masks declare mm.
The scorer initially refused this. The diagnostic now explicitly records the assumption that these
pancreas masks share the mm units of their exactly matching shape/affine. No header or label was edited.
The saved prediction hashes remained unchanged before/after scoring. Private evidence:
`verified-scores.json`, `score_saved.py`, and `score-log.txt` in the diagnostic folder above.

| Case | Pancreas+lesion union Dice | Lesion Dice | Lesion recall | Lesion false-positive mL |
|---|---:|---:|---:|---:|
| A01 / 1389 | 0.000 | undefined (empty reference) | undefined | 68.556 |
| A02 / 1070 | 0.760 | 0.726 | 0.635 | 0.541 |

A01 has only74 pancreas-reference voxels (approximately0.250mL), with zero overlap with the
predicted union. Source CT and both label SHA256s exactly match the retained training-preparation
metadata. The historical manifest also records the same110×125×116 CT dimensions. This rules out
an accidental new input-copy change and a simple native-grid mismatch; it does **not** prove correct
anatomical pairing or identify the upstream cause. Visual non-abdominal appearance plus tiny organ
annotation requires source review. No case was silently excluded, no frozen manifest/split/cache was
changed, and the source archives were not re-extracted or independently rehashed in this diagnostic.
Previous mechanical admission checked nonempty pancreas and lesion survival, not anatomical validity.

For A02 only, a separate, explicitly reference-assisted diagnostic used the same segmenter weights,
preprocessing and native export, substituting the reference pancreas box. This is an oracle comparator,
never an autonomous prediction or deployable result. Both region boxes cover100% of annotated pancreas
and lesion voxels. Results:

| Crop | Union Dice | Lesion Dice | Lesion recall | Lesion false-positive mL |
|---|---:|---:|---:|---:|
| Predicted region (original A02) | 0.760 | 0.726 | 0.635 | 0.541 |
| Reference region (diagnostic) | 0.826 | 0.703 | 0.909 | 3.195 |

The predicted region did not cut off the reference target on this example. Differences in crop
context/resampling affect predictions; higher Dice here accompanies lower lesion recall, and is not
evidence that localization always improves performance. One adaptively selected development case
cannot establish general quality, equivalence to published results or absence of source leakage.

The first comparator helper failed before a model forward because it treated the loader's
`(model, receipt)` return as a model. That helper error was corrected in a fresh retained attempt.
The successful comparator performed one inference, zero updates, took2.669301s and peaked at
1,511,948,288 sampled owned bytes; workers were reaped under600s/12GiB supervision. Evidence includes
`reference-diagnostic.log`, `resources-reference-diagnostic.json` (failed attempt), and
`reference-diagnostic-a02-retry01/result.json`, helper source and retry resource/log files (success).

**Current conclusion:** The CT-only connection works on the tested abdominal CT, and there is no
observed crop truncation or native-grid mismatch explaining its result. The system is not yet robust
on unsuitable inputs. Further work is fixed-cohort evaluation and anatomical/source review, followed
by an evidence-based input-quality/localizer failure policy. A hardcoded case exclusion or an arbitrary
organ-volume cutoff would conceal the problem rather than solve it. Lenovo training remains untouched;
its historical cohort should be reviewed against this finding before interpreting final metrics.

## Fixed75-case development baseline — October 9 continuation

Evaluated every ID in the existing admitted development list in its original order. The case list,
checkpoint pair, crop policy and preprocessing were frozen before execution. The two earlier predictions
were reused after checking CT/model identity, result hashes and prediction hashes;73 new inference
attempts ran. No model or crop policy was tuned during this evaluation. Workers received CT-only
requests, with reference scoring in a separate process after all inference ended. No original test
cases, optimizer updates, Lenovo changes or external publication were involved.

Private evidence lives under `outputs/prowl/autonomous-real-ct-20261009/fixed-development-75/`:
`plan.json`, `software.json`, `ct-header-audit.json`, ordered `inference-journal.jsonl`, per-case requests,
logs/results/predictions, `execution-summary.json`, `scores.json`, `summary.json`, scoring source/logs.
Plan SHA256: `eab509bc8bb85d35d22aa43a5a8da3f748ada762525628ffef596e9b658c227a`.
The recorded inference/scoring source hashes remained unchanged through execution/scoring.

### Results, including failures

- Fixed cohort:75 cases (38 positive lesion references,37 reference-empty).
- 56 predictions scored:54 new successful outputs plus two reused outputs.
- 19 explicit inference failures:11 predicted-region sampling allocations exceed16M voxels;
  seven CT headers declare unknown spatial units; one whole-scan projected-resampling budget exceeded.
- 28 positive cases scored: mean per-case lesion Dice0.244807, mean recall0.349978.
- 28 reference-empty cases scored: mean predicted lesion volume7.914077mL.
- 56 scored cases: mean pancreas+lesion union Dice0.634342.
- The19 unscored cases comprise10 positive and9 reference-empty cases. They remain in the75-case
  denominator; the quality means above cover only completed predictions. No failed case receives an
  invented Dice value, and reference-empty does not mean verified healthy.

These results replace the single-case0.726 example as the evidence for this **fixed development
baseline**. They are not an untouched benchmark. Do not directly compare0.244807 against the training
journal's0.395317: those use different input regions, scoring grids and case populations. The baseline
shows that working connections alone do not establish reliable autonomous performance.

The73 supervised attempts consumed472.799745 summed worker seconds, with maximum sampled owned
RSS3,606,478,848 bytes. All workers were reaped; none hit the600s/12GiB watchdog. Batch limits also
included30minutes total, a100GiB free-space floor and a shared accelerator lock. Missing-unit and
geometry-allocation rejections are application checks, not evidence that physical RAM was exhausted.
No successful unchanged inference was replayed to obtain a better score.

Added `src/inference/evaluation_summary.py` and three focused tests. It requires exact ordered case
accounting and reports failures and positive/empty reference populations separately. Tests cover
known means with failures/empty annotations, omitted/duplicate/reordered cases and an all-failure
cohort; all three passed.

### Source-review limitation and next corrections

A bounded120-second streaming audit of the33GiB downloaded CT archive did not reach the suspicious
case's member before timeout. `a01-archive-audit.json` records this incomplete result. No member was
extracted and no original-archive integrity or anatomical-pairing claim follows. The earlier verified
extracted-file/preparation hashes and74-voxel pancreas annotation remain the available evidence.

The concrete next work is:

1. Establish a CT-only spatial-unit normalization/provenance rule for the seven unknown-unit inputs.
   Shape/affine plausibility alone is insufficient evidence to silently invent physical units.
2. Support large predicted crops and projected whole-scan grids with bounded memory, or define and
   evaluate an explicit localization policy. Preserve this baseline; do not silently drop predicted
   components or borrow a reference region to make failing cases pass.
3. Compare reference-region and autonomous predictions on matched cases to separate localization,
   resampling and segmenter quality. One paired case does not settle the cohort-wide question.
4. Review the suspicious source and unsupported-anatomy response. Keep it visible in accounting;
   neither a hardcoded case exclusion nor an arbitrary organ-volume rule is validated by this result.

Separate post-inference coverage scoring (`crop-coverage.json`, `score_coverage.py`) checked pinned
reference masks against the recorded native crop boxes: all28 scored positive cases have100% native
lesion bounding-box coverage. None has a completely missed lesion at that stage. This narrows the
quality investigation: poor scores are not explained by simply excluding the lesion from these native
boxes. It does **not** establish lesion survival after resampling to144³, adequate crop scale/context,
or good segmenter predictions, and says nothing about the10 positive inference failures. Reference
labels were used only in this post-hoc coverage assessment, never to choose or repair prediction boxes.

## Geometry capacity and explicit CT-unit correction

The earlier geometry failures came from fixed allocation checks. The localizer's recipe can now set
`max_output_voxels` up to64,000,000, and the segmenter geometry can set `max_sampling_voxels` up to
64,000,000. The CT-only CLI accepts the latter as an optional top-level request field; omitted values
retain16,000,000. Existing recipes keep their original limits, and requests above the new ceiling fail.

These are allocation limits, not new spatial resolutions. The2mm localizer,1mm intermediate ROI,
all-predicted-support10mm margin,144³ segmenter tensor, interpolation, HU windows and weights are
unchanged. No component is discarded to fit a crop. Resource supervision is still required: the CLI's
voxel ceilings do not themselves enforce a process-RSS limit. Previously pinned consumers retain their
old recipes/evidence; this code change does not silently rebind historical source hashes.

`src/inference/spatial_units.py` supports an explicit CT-side review for missing units. The optional
`spatial_units_review` request object must have exactly `ct_sha256`, `interpreted_units` (`mm`),
`basis` (`ct_acquisition_metadata` or `source_dataset_documentation`), `evidence`, and `reviewer`.
It must match the actual CT hash. The decision is retained in `result.json`, and source CT bytes are
never modified. Declared non-mm units are not relabeled; unknown units without a review still fail.
This is a mechanism for recording a reviewed fact, not an automated verification of evidence text.
A reference-mask header is deliberately not an accepted evidence basis.

No real unit reviews have been invented for the seven unknown-unit cases. The [PanTS paper](https://papers.nips.cc/paper_files/paper/2025/file/2dc24f4adc257251b2f3929c67ec1e3a-Paper-Datasets_and_Benchmarks_Track.pdf)
reports image spacing in millimeters, but that population-level convention alone does not establish
the interpretation of each malformed NIfTI header. Attempts to retrieve the pinned dataset card and
repository README through the browser were unsuccessful. These seven cases still need CT-side
acquisition or release evidence; the synthetic review test demonstrates software support only.

Tests:22 capacity/cascade/ROI/geometry checks,2 additional unit-review/localizer-cap checks, and7
localizer restoration/parity/default-envelope checks passed (31 distinct tests). Existing supported
synthetic images produce identical tensors under16M and64M limits. The tests also cover wrong CT
identity, mask-derived review rejection, unchanged source CT bytes, explicit output mm units, old
recipe rejection of oversized grids, and refusal above64M. Two upstream TorchScript deprecation
warnings remain.

A separate correction attempt targets exactly the12 prior geometry failures, with larger caps and
all other numerical choices fixed. Its private directory is `geometry-repair-12/` beside the baseline;
plan SHA256 `942879fbd6b678cba9c2c9a2922ac3c109e78ecd6debd78b29c853af570393a3`.
It retains fresh requests, source hashes, supervised resource records and outputs. The original75-case
baseline is unchanged. No Lenovo runtime or training configuration was touched.

**Correction result:** All12 geometry retries completed and scored. Summed worker time122.285110s;
peak sampled owned RSS4,464,967,680 bytes (4.16GiB), below the12GiB ceiling; all workers reaped. Fresh
outputs match their source grids. Five lesion-positive cases have mean Dice0.119480/recall0.218704;
seven reference-empty cases have mean predicted lesion volume74.802730mL. Execution success is not
quality acceptance. Larger allocations expose poor predictions instead of hiding them behind failures.

Combined accounting in `geometry-repair-12/combined-summary.json` reuses the56 original predictions
and adds12 corrected outputs:68/75 scored, seven unknown-unit failures retained (five positive and two
reference-empty). Mean lesion Dice0.225818/recall0.330088 over33 positive cases; union Dice0.578969 over
68 cases; mean predicted lesion volume21.291808mL over35 reference-empty cases. This is a mixed retained/
corrected development report, not a fresh75-case run or a matched accuracy-improvement comparison.
The different denominator explains why it must not be described as a Dice regression caused by the fix.

The remaining unknown-unit IDs are:
`PanTS_00006011`, `PanTS_00005780`, `PanTS_00001823`, `PanTS_00002935`, `PanTS_00005370`,
`PanTS_00006901`, `PanTS_00006115`. No review was supplied and none of these was rerun. Their next step
is source/acquisition-unit evidence, not a reference-mask fallback. All twelve geometry failures from
this baseline are resolved within measured resources; this does not qualify arbitrary future volumes
or resolve the suspicious anatomy/weak model behavior.
