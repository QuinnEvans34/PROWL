# CP02: fixed development measurement comparison

## Purpose and scope

Authorized by Quinton's autonomous post-demo sequence on October20. CP01 failed its one-case
screen; this follow-up compares the unchanged raw method and unchanged `largest-union-26-v1`
across a fixed subset before choosing another correction. It does not retrospectively pass CP01,
change its rules, retrain the model or promote measurements to the UI.

Use the already transferred fixed step6000 checkpoint, SHA-256
`ac50b534eb5e5334bfb29626743ed626a1d16363d8ac1c3374165140318f397f`, from
`pants_pancreas_region_24k_20261019`. Current70-case development-list SHA-256:
`6b69605f49de0dd20346bee9db7fea4842c050cea4cf8d85268775deabc301bf`;
input-control SHA-256 `bda7d9c58536c618936232628630996d793b331eb29fd6062630fb05a3888ae2`.
The existing Mac metadata proves only case00000029's current membership. Obtain the exact
current development IDs, train exclusion and admitted annotation-state/source identities before
selecting additional cases. Old Mac splits cannot establish current70 membership.

## Fixed selection, before case quality or prediction inspection

Select the first three sorted lesion-positive and first three sorted annotation-empty IDs from
that exact current exposed development list. Annotation status comes from admitted preparation
metadata, not model quality. If fewer than three exist in a stratum, retain all and report the
smaller denominator. Empty annotations do not establish healthy patients.

Require every selected ID in the current validation control and absent from current training;
no protected test membership/payload inspection. Freeze a private selection JSON with metadata
pins, exact IDs and the ordering rule before prediction/reference-array work. Match local CT,
provided pancreas and lesion source bytes to the admitted hashes. Do not substitute an easier
case after a size, geometry, source, resource or inference failure; retain the failure in the
selected denominator. For already retained case00000029, reuse the original package and CP01
comparison after checking its hashes, rather than repeat inference.

## Execution and comparison

Use unchanged on-demand inference recipe, model, MPSfloat32, provided-pancreas region assistance,
and native-grid restoration. The model receives CT only; lesion reference is unavailable to the
worker and selector. The provided pancreas mask selects the ROI and is disclosed as assistance.
No claimed CUDA parity or autonomous whole-CT localization.

At most six selected cases, one sequential inference per new case, no retry or parameter sweep.
Per case: existing600s/8GiB supervised worker,32M native voxels,64MiB compressed input,128MiB
decoded-per-image,132MiB job-output ceiling. Total inference ceiling60minutes; no concurrency
with local answer generation. Keep at least100GiB internal free and use the registered external
drive for additional retained patient artifacts, under a2GiB total CP02 artifact ceiling.
Metadata and source hashes must pass before model loading. Fail closed on geometry mismatch.

Compare raw and unchanged CP01 masks against reference pancreas/lesion with the existing
lesion-priority definitions: extent1+2 versus pancreas OR lesion, parenchyma1 versus pancreas
AND NOT lesion, lesion2 versus lesion. Report all three targets separately: exactTP/FP/FN,
Dice/precision/recall, predicted/reference mL, signed/absolute error and relative error only when
reference volume is positive. Report crop/CT contact, per-reference-lesion overlap loss, and
residual predicted lesion components with and without reference overlap. Report empty-reference
false-positive mL and component counts separately; never turn undefined recall into1.

Apply and report every original CP01 screen rule per case, including its absolute-volume-error
rule. A failed screen stays failed even if another metric improves. Describe correlations such as
FP/FN cancellation without changing the screen. No second cleanup candidate is evaluated in CP02.

## Review and disposition

Produce a per-case table and stratified summaries (positive versus annotation-empty), not only
an average. Inspect retained components and reference-overlap arithmetic before selecting the
next hypothesis. Next correction must address a demonstrated cross-case error mechanism and
receive its own frozen comparison. No absolute measurement acceptance threshold is invented
after observing these cases; reliable-size release and human outline review remain separate.

Current status: protocol frozen; current-split metadata requested through an authorization question.
No additional case selected, array opened or inference run for CP02 yet.
