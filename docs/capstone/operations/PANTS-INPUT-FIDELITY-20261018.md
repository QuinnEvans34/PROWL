# PanTS training input coverage and detail review

## Decision before the next training run

The current input pipeline can severely truncate a labeled lesion even when its component-survival
check passes. One of12targeted training cases retained only11.63%of its annotated lesion inside
the provided-pancreas box. Keep the agreed lower-learning-rate experiment on hold for discussion
of crop policy. No production geometry, labels, cache, model or membership was changed.

This finding does not explain every model error. All15selected development lesions were fully
inside their crops, including all7large-lesion cases. Their remaining model errors cannot be
attributed simply to lesions being outside the field of view.

## Scope and method

Read12positive training cases selected across lesion-volume and final-spacing quantiles, plus
all5small and7large positives in matched development and the3medium cases with the worst
selected-model Dice changes. This targeted27-case subset is not a prevalence estimate or a
new model benchmark. Original roles and five development exclusions are unchanged.

Verified the selected cache and metadata hashes, original lesion/pancreas hashes, transforms and
native label geometry. Counted original lesion voxels within each stored native crop box. Restored
the exact cached multiclass training target through the production native inverse transform and
compared it with original lesion labels. This isolates target representation and restoration from
model prediction. Round-trip Dice is a diagnostic, not a mathematical ceiling on learned-model Dice.

The primary review completed in121.766seconds. It read27pairs of labels and6CTs for figures.
One additional CT view of the newly discovered clipped training case was made afterward; total
7unique CT cases. No models, optimizer updates, test arrays, duplicate scans or cache rewrites.
Two focused tests passed for overlap accounting and physical-plane coordinate mapping.

## Findings

| Question | Evidence |
|---|---|
| Are entire annotated lesions inside the crop? | 26/27selected cases yes; one training case only11.63% |
| Is target detail preserved when coverage is complete? | Median round-trip Dice0.9631; minimum0.7976 across26cases |
| What about the7large development lesions? | All100%covered; round-trip Dice0.9584–0.9941 |
| What about the5small development lesions? | All100%covered; round-trip Dice0.8545–1.0000 |
| Does good target fidelity guarantee model success? | No: worst large regression has round-trip0.9674, model0.1381 versus prior0.7711 |

The clipped case has189,621original lesion voxels, of which167,565are outside the box and22,056
inside. Returning its cached target yields21,971lesion voxels,21,924true positives, native
Dice0.2072and recall0.1156. Within the retained region the target is preserved well; loss of field
of view dominates. Because this pipeline always predicts zero outside the crop, even perfect
labeling of all retained lesion voxels would limit this case to approximately0.2084Dice before
accounting for other discretization errors. This is a case-specific crop-support bound, not a
dataset-wide ceiling.

The tiny training example has12reference lesion voxels,10returned voxels and9overlapping voxels:
round-tripDice0.8182and recall0.75despite100%cropcoverage. Component presence alone does not
establish boundary fidelity. Upsampling after the1mm intermediate stage cannot recover detail
already removed at that stage; this review measures combined effects, not their separate attribution.

The cache images show expected smoothing and discretization. Matched-plane displays did not
show a gross image/target displacement in the reviewed examples. This is an engineering visual
check, not radiologist adjudication of the original lesion annotations. The unexpectedly extensive
annotation in the clipping case should be checked against its source semantics before changing
the crop around it; do not automatically relabel or exclude it.

## Images

Images remain local, outside the public repository and aggregate phone dashboard. Reference
lesions are red, cached or returned target lesions cyan, and reference pancreas yellow. These
are annotation contours, not model predictions or input channels.

- [Exact cached cube with zero padding](E:/PROWL/readiness/input-fidelity-20261018-a01/exact-cached-cube.png)
- [Clipped training lesion in expanded original context](E:/PROWL/readiness/input-fidelity-20261018-a01/clipped-training-lesion-expanded-context.png)
- [Large development regression with intact target](E:/PROWL/readiness/input-fidelity-20261018-a01/development-22.png)
- [Tiny training lesion](E:/PROWL/readiness/input-fidelity-20261018-a01/training-01.png)
- [Typical training example](E:/PROWL/readiness/input-fidelity-20261018-a01/training-04.png)
- [Additional training example](E:/PROWL/readiness/input-fidelity-20261018-a01/training-12.png)
- [Small development lesion](E:/PROWL/readiness/input-fidelity-20261018-a01/development-23.png)
- [Medium development regression](E:/PROWL/readiness/input-fidelity-20261018-a01/development-25.png)

Matched-plane figures use the same physicalRAS coordinates and physical aspect ratio across
columns. Original CT uses linear display sampling; cached CT uses nearest display sampling to
expose its actual grid. These display choices are not additional preprocessing. The expanded
context figure intentionally shows anatomy outside the model field; black there means unavailable
to the model, not a blank original scan. The exact-cube figure separately shows actual full tensor
slices including padding. Neither figure implies the model trains on2Dslices: it consumes the3Dcube.

## Proposed next decision

First confirm the source annotation semantics for the severely clipped example. Then consider a
training-role-only coverage inventory of positive labels to establish how often this occurs; this
would be a mask/geometry check, not CT requalification or duplicate discovery. It has not been run.

If the extent is valid, design a coverage-preserving crop policy and check its resolution cost
before training. A larger fixed pancreas margin or an independent localization proposal can apply
at inference. A pancreas-plus-ground-truth-lesion crop can be a training/oracle diagnostic, but must
not silently define development/inference inputs: the unknown lesion would be choosing its own box.
Simply expanding the field while keeping144cube can worsen lesion detail. Consider resolution or
overlapping3Dwindows only as an explicitly separate representation experiment, preserving the
full native reference for scoring and documenting any changed inference field.

The prior large-lesion regressions still justify investigating optimization: all7are fully covered
and preserve labels well. Keep the agreed LR5e-5 experiment recorded, but do not combine it with
new cropping/resolution and then attribute any gain solely to learning rate. No new launch authority
is implied by this review.

## Reproducibility

Private evidence: `E:/PROWL/readiness/input-fidelity-20261018-a01/selection.json`, `cases.jsonl`,
`results.json`, `additional-view.json` and PNGs. Per-case source identities stay in private evidence.
Scripts: `scripts/diagnostics/review_training_input_fidelity.py` and
`scripts/diagnostics/render_input_fidelity_detail.py`; tests:`tests/test_input_fidelity_review.py`.
Source/cache hashes and code hashes are retained in the diagnostic evidence. Existing scientific
run scores, frozen producing files and source annotations remain unchanged.
