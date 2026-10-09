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
