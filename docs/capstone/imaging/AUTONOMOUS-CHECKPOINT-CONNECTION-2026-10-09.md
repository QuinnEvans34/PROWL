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
