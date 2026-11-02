# Cross-device comparison failed the predeclared probability gate

The accepted pre-result rule from main c35cd2b was applied unchanged. The four-case
evaluation is blocked; no batch CT restoration, inference, scoring or retry started.
This is an engineering consistency failure, not a Dice or model-quality verdict.

The Mac archive was received through Magic Wormhole into
E:/PROWL/transfer/week05-mac-reference-20261102-a01/. Its145,928,223bytes and SHA256
c306cc9b810aaf4c725d55fbc4421f0f641b488f6471763d889715154fce06fd matched before
safe extraction. All13files were retained;12files match the included independent
backup receipt, and all4 result-bound artifacts match their size/hash. The Mac
request matches2a0c7bfb09eb53807967ac6efee8d78554fd4b36cf726528a27bad370b75510e.
Mac resources record success/exit0/reaped/no surviving workers. No CT or weights
were included or read by the comparison.

## Results

| Check | Observed result |
| --- | --- |
| CT, model and scientific recipe identities | Match |
| Eight core source pins | Match after LF/CRLF normalization only |
| Native grids, transforms, selected ROI and physical grid | Match |
| Reconstruction gaps | Zero on both |
| Final native hard codes | Exactly equal;0 disagreements/20,131,482voxels |
| Native localizer masks | Exactly equal;0 disagreements |
| Probability values compared | 51,444,975, all3 float32 ROI channels |
| Values exceeding atol1e-5 + rtol1e-4 times absolute Mac reference | **169** |
| Failure fraction | 0.0003285063% of values |
| Maximum absolute probability difference across all values | **0.00004851818084716797** |
| Maximum ratio to allowed tolerance among failures | 2.111610850095025 |
| Failing channels | Background0; pancreas167; lesion2 |
| Maximum normalization error, each backend | 0.0000007748603820800781, within2e-5 |

There is no changed hard prediction in this diagnostic. Nevertheless, the rule
required all probabilities to meet tolerance, so the result is
FAIL_ENGINEERING_COMPARISON. The small failure fraction does not waive that rule.
No probability clipping, averaging, threshold change or post-result tolerance
relaxation was performed. Both stored hard predictions also match argmax of their
own saved probabilities and native ROI embedding.

The comparison script applies the same0.001 hard-disagreement ceiling to both
native masks and final codes; both are zero, so this interpretation does not affect
the failed verdict. All exact failure coordinates/values/tolerances are preserved
in probability-failures.json, rather than only an aggregate maximum.

## Runtime differences and interpretation

| Library | Windows CUDA | Mac MPS |
| --- | --- | --- |
| Python |3.12.14|3.12.13|
| Torch |2.11.0+cu128|2.13.0|
| MONAI |1.6.1|1.6.0|
| NumPy |2.5.2|2.5.1|
| SciPy |1.18.1|1.18.0|
| NiBabel |5.4.2|5.4.2|

This does not isolate GPU-backend variation from library-version variation.
Small numerical variation is a plausible explanation, not an established cause.
The next decision should specify a bounded investigation using matched runtime/
operation evidence, preserving this failed attempt. Do not edit either frozen
producer, rerun the diagnostic, silently update environments or loosen the gate.
Any amended equivalence protocol must be prospective and separately reviewed,
never presented as a pass under this original rule.

## Evidence and handoff

CPU-only comparator and CLI:
src/inference/physical_cascade_comparison_v1.py and
scripts/diagnostics/compare_week05_reference_20261102.py.
Ten focused tests passed5.96s, including tolerance-boundary behavior, probability
failure despite equal hard outputs, normalization/nonfinite/representation refusal
and source checks. The real comparator exited0 while correctly recording a failed
comparison; it does not use its process exit code as a scientific pass flag.

E:/PROWL/readiness/week05-cross-device-comparison-20261102-a01 contains
comparison-request.json (pre-comparison source/rule pins), comparison.json and
probability-failures.json. ComparisonSHA256:
fd7be15a0745e5acdec22fdf738c9b6d4a95be35dbaaf555fd56906ad083c974.

The fixed batch remains2028/909/4681/6755, all exposed development. Manifest metadata
locates their original CTs on unavailable D: and their retained reference masks on E:.
Four exact CT restorations, complete header/units/source admission, separate assisted
worker/scorer and a frozen batch request still remain. They were not launched after
the comparison failure. No difficult patient was removed or replaced. No training,
MLflow training record, dashboard-hour change, schedule or control of Mac KD occurred.
