# Autonomous prediction investigation: two-stage, single-stage and specialist systems

**Owner:** Quinton Evans + development chat  
**Created / updated:** October 8, 2026  
**Target window:** October 8–22, 2026; review October 11 and 18; decision checkpoint October 22  
**Status:** Living investigation; experiments proposed, no new jobs launched by this document

## October 9 ownership update

Quinton reports training running on Lenovo and the entire dataset downloaded there. All long training
work now belongs to Lenovo; Mac develops/integrates/evaluates using its4TB drive. This supersedes the
optional dual-laptop weekend training plan below. The Mac's resume02 result reports24,000 completed
updates with best reference-crop development Dice0.3953174294791896. Lenovo's implementation/results
are pending a handback here; no remote action or restart follows from this planning update.
See the [Week2 development plan](../weeks/WEEK-02-WORK-PLAN.md).

## Purpose and proposal alignment

Choose an evidence-backed baseline that turns a raw CT into pancreas and lesion predictions without
reference outlines or a supplied pancreas box at inference. Over the next two weeks, integrate and
measure the simplest available route, identify its limiting stage, and select the next training
experiment. This window is a planning target, not a promise to train every candidate architecture.

This advances the approved proposal's Week4 unified pipeline, Week5 autonomous baseline and Week6
controlled comparisons. It runs alongside Week2 protected-cohort work and Week3 PANORAMA integration;
it does not replace them. See the [weekly plan](../weeks/WEEK-01-WORK-PLAN.md),
[proposal](../../../Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx), sections 2–4 and 6,
and [appendix](../../../Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx), A2–A5 and A8.
Matching published PanTS performance is a research aspiration; no numerical improvement is promised.

## What is established, and what remains uncertain

| Finding | Evidence and qualification |
|---|---|
| The new trainer supports a long, configurable full-cohort experiment | [Training guide](../../training-full-segmenter.md); current FULL-SEG-MAC-001 configuration targets 24,000 updates. This document does not report live progress |
| Current experiment uses reference-pancreas crops | Geometry v2, 144 cubed tensor, 1mm intermediate sampling, 10mm margin, pancreas-only region. It measures segmentation with privileged localization, not autonomous full-scan performance |
| Current experiment is PanTS-only | Oct8 read of resume configuration, input manifest and admitted IDs: all 1,333 train and 75 development members have PanTS identifiers and PanTS CT paths; zero PANORAMA members |
| Existing localizers may be useful candidates | Check exact architecture, checkpoint, training memberships and evaluation before reuse; do not assume qualification from an old headline |
| The remembered 98% result is not yet identified conclusively | EXP-22 records 98.9% tumor containment (86/87) and 94.6% full pancreas containment (685/724). The July19 audit explicitly withdraws these as held-out results because of split leakage. Another entry records 98% lesion detection, a different metric. Neither establishes generic 98% localization accuracy |
| Earlier autonomous near-oracle result is also withdrawn | EXP-20's autonomous Dice 0.483 versus supplied-box 0.496 belongs to the contaminated history. Retain as historical motivation, not valid performance evidence |
| More recent localizers have unresolved quality limitations | [Structure audit](../operations/LOCALIZER-STRUCTURE-AUDIT-RESULTS-2026-10-01.md) records coverage/overprediction issues; [predicted-ROI adapter](../operations/PREDICTED-ROI-ADAPTER-RESULTS-2026-10-06.md) has invented-input tests, not a complete qualified real-data cascade |
| Lenovo is dedicated to training | Quinton confirms uninterrupted home use for the remaining plan; RTX4060 Laptop with 8GB VRAM and 32GB RAM from specs commit 0c78ff7. CUDA port and measured fit remain to be demonstrated; external 1TB drive has no dataset loaded |

Historical numerical claims and withdrawals: [experiment notebook](../../experiments.md), EXP-20,
EXP-22, July19 audit, EXP-24 variants and EXP-27. Do not overwrite those entries with this plan.

## Required autonomous input/output boundary

Input: CT plus acquisition/geometry metadata. Prediction must not read reference pancreas or lesion
masks, reference-derived boxes, source diagnosis or evaluation labels. Ground truth remains legitimate
for supervised training and independent scoring after predictions are saved.

Output: pancreas and lesion masks in the original scan grid, predicted case score, model/config/data
identity, spatial-transform history and explicit failure status. The eventual reviewer workflow adds
measurements and persisted accept/edit/reject decisions under the existing product contracts.

A case may not disappear from evaluation because localization was empty, the crop missed a lesion,
or inference failed. Record each failure and report whole-pipeline coverage and performance with a
prespecified failure policy. Supplied-box rescue is a labeled diagnostic, never an autonomous result.

## Candidate approaches and the questions they answer

| ID | Approach | Question | Main issue to measure |
|---|---|---|---|
| A | Existing localizer → crop → existing segmenter | Can current components produce a useful baseline without retraining? | Effective lesion coverage after every crop/resize and errors from imperfect regions |
| B | Same cascade; segmenter trained with crop variation or predicted regions | Can training reduce sensitivity to localization error? | Keep evaluation fixed; predicted training regions must come from a separate/fold-excluded localizer or disclose in-sample optimism |
| C | Full-CT single-stage segmentation using a feasible patch/sliding-window strategy | Does whole-scan prediction improve coverage enough to justify runtime and false alarms? | Small-lesion resolution, complete inference coverage and 8GB fit |
| D | Coarse full-scan prediction → fine-resolution refinement | Does an inexpensive first pass preserve candidates for detailed segmentation? | Candidate recall, refinement coverage and total runtime |
| E | Localizer + case classifier + specialist segmenters | Does specialization improve the full system over the ordinary cascade? | Routing mistakes, classifier target validity and whether each extra model adds measurable value |
| F | Combine predictions from multiple comparable segmenters | Do complementary errors make averaging/voting useful? | Improvement versus added inference/storage cost on the same cases |

E is a routed specialist pipeline; F combines predictions for the same task. They may be combined
later, but there is no reason to launch all variants together. These are hypotheses, not claims that
any architecture is superior.

## Specialist proposal from Quinton

The proposal contains four jobs, which need not require four independent networks:

1. Locate the pancreas from the full CT.
2. Estimate whether the case contains the explicitly defined target condition.
3. Delineate lesions using a lesion-focused expert.
4. Delineate the pancreas using an organ-focused expert.

Use “lesion present/absent” or “PDAC present/absent” according to the available labels; “healthy/unhealthy”
is too broad for these datasets. Non-PDAC can still contain other pancreatic lesions. A pancreas
expert should initially run on every case, including diseased pancreases. Restricting it to predicted
negative cases is a separate hypothesis and could leave diseased anatomy poorly represented.

**Recommended first version:** localizer supplies context; organ and lesion outputs are produced for
all cases; a classifier score is recorded alongside them without suppressing predictions. This creates
a baseline for measuring whether a classifier supplies information beyond segmentation-derived scores.

Then compare on identical saved cases/predictions:

- No classifier routing: lesion expert always runs.
- Hard routing: a selected classifier threshold permits or suppresses the lesion branch.
- Soft combination: classifier evidence changes the score while preserving the underlying lesion map.
- An uncertainty/failure route that retains extra processing or flags review, with its rule defined on development data.

A false-negative hard gate makes lesion detection impossible downstream for that case. Illustratively,
95% gate sensitivity multiplied by 90% downstream sensitivity **among passed positive cases** yields
85.5% overall sensitivity. These are invented numbers, not PROWL measurements or an independence claim.
Measure conditional and end-to-end results; do not multiply unrelated published accuracies.

Train/evaluate a classifier only with labels supporting its chosen target. Experts trained on positives
alone still need negative-case testing and, where justified, negative training examples; they may
otherwise over-predict. Compare against the existing shared pancreas/lesion model before paying the
cost of separate experts. A shared backbone with multiple output heads is another later option.

## First matched experiment: isolate localization

Keep the segmenter checkpoint, cases, intensity processing, tensor shape, interpolation, scoring and
postprocessing fixed. Change the source of the region only:

- **Reference arm:** current reference-pancreas crop, clearly labeled privileged localization.
- **Autonomous arm:** predicted region from the chosen eligible localizer, with a fixed physical margin.

Select checkpoints and any margins using training/development evidence only. Audit each candidate's
historical training membership against the proposed evaluation cases. Do not use a leaked checkpoint
on its training cases and present the score as held out. Freeze the comparison recipe before reading
its results; keep the protected test set out of iterative architecture selection.

Measure:

- Pancreas and lesion reference coverage in the predicted region, both before and after actual stage2 transforms.
- Region size, clipping, empty/multiple-component predictions and geometry failures.
- Native-grid pancreas Dice and lesion Dice on the declared eligible populations; state empty-case conventions.
- Lesion detection sensitivity, patient-level specificity where negative status is supported, and false-positive volume/count.
- Paired per-case change from reference to autonomous inference; uncertainty and representative failures.
- Runtime, memory, storage and completion rate; count missing outputs explicitly.
- Performance by lesion size and supported source/phase/annotation strata without silently dropping difficult cases.

Do not equate current tensor-grid positive-case Dice with full-scan native Dice or published PanTS
scores. A future benchmark comparison needs matching target definitions, splits, inference and metrics.

## PANORAMA: acquired, but not in current training

The [acquisition queue](../operations/DATA-ACQUISITION-QUEUE.md) records completion September20 and
publisher-checksum verification of four CT archives; the pinned label archive matched publisher Git
blobs. The [September28 record](../operations/TODAY-2026-09-28.md) records extraction progress.
On October8, both acquisition and extraction directories are present under the mounted PANORAMA
source root. This read checked directory presence, not all current voxel files or checksums.

The current full-segmenter manifest and admitted memberships contain only PanTS. No completed mixed
PANORAMA training result was established by this review. EXP-27 is an older unrun proposal, not proof
of integration. Its original 578-case treatment and “tumor-free” assumptions must not silently override
the later approved provenance/target policy.

The [metadata inventory](../data/PANORAMA-INVENTORY.md) and [mapping specification](../data/PANORAMA-MAPPING.md)
identify these **candidate counts**, pending reconciliation with the pinned files and current QC:

- 274 declared NIH/MSD imports excluded because of known source overlap.
- 578 remaining PDAC-positive studies: 382 candidate manual-lesion studies and 196 automatic-lesion studies.
- 1,386 remaining non-PDAC studies, which are not automatically generic-lesion-negative cases.
- Pancreas masks treated as machine generated unless source-specific evidence establishes otherwise.

**Recommended experiment:** a matched PanTS-only baseline versus PanTS plus eligible expert-lesion
PANORAMA cases. Keep the selected model, evaluation cohort, initialization policy and training recipe
fixed. State sampling, update budget and resulting exposures: equal updates and equal epochs are
not equivalent when the cohort grows. Test automatic-lesion supervision separately if warranted.
Measure PanTS development performance and source/subtype/false-alarm effects; more PDAC data does not
guarantee gains across all lesion types. Do not mix this dataset change with a new routing architecture
in the first comparison.

Integration work is concrete: reconcile CT/label/metadata IDs and manual-label provenance; apply the
existing label map; check paired geometry and lesion coverage; exclude known overlaps and resolve
cross-source duplicate candidates; preserve patient-level split separation; publish an eligible
manifest. Reuse existing Plan03 code/evidence and report only missing work, rather than restart design.

Publisher references checked October8:
[dataset description](https://panorama.grand-challenge.org/datasets-imaging-labels/) explains that
non-PDAC cases can include other pancreatic lesions;
[label repository](https://github.com/DIAGNijmegen/panorama_labels) describes annotation/source imports.
Local pinned provenance remains the authority for the bytes actually used.

## Two-week work sequence

| Phase | Concrete output | Finish criterion |
|---|---|---|
| Preparation and first weekend, Oct8–11 | Identify historical localizer; trace current components; choose eligible paired cases; specify portable inputs and Lenovo setup | Exact checkpoints, cohort, inference path and missing code listed; one bounded implementation task ready |
| First experimental cycle, Oct12–15 | Native-output cascade and reference comparison; Lenovo first selected long run when data/CUDA/fit/resume work passes | Actual end-to-end outputs and paired failure report, not merely successful unit tests |
| Second weekend and follow-up, Oct16–21 | Choose one response to observed failures: localizer improvement, crop-robust training, whole-scan challenger or classifier/specialist comparison | Fixed hypothesis, controlled comparison and recorded results; incomplete long jobs labeled pending |
| Decision checkpoint, Oct22 | Select working baseline and next experiment | Evidence supports the decision or clearly explains remaining uncertainty; no forced winner |

PANORAMA integration proceeds with the scheduled Week3 data work and can supply a separate cohort
comparison. If compute is limited, finish the reference-versus-predicted-region comparison first;
defer extra expert networks before extending infrastructure work indefinitely.

## October 8 continuation: historical recipes and compute capacity

Quinton confirms the historical manifest contamination is known and wants to reuse promising ideas
in fresh, properly separated experiments. Recover the architecture, preprocessing, initialization,
loss and training horizon from the historical localizer recipe; do not carry forward its contaminated
performance claims. Prefer fresh training from the intended initialization on the corrected cohort,
with explicit split checks and a new experiment ID. Preserve each experiment's documented validity
status rather than infer that every historical experiment had identical contamination.

Both laptops may be available for concurrent weekend experiments. Plan independent jobs with fixed
code/config versions and separate outputs; each needs locally available inputs, capacity and backups.
A possible pairing is localizer training on one machine and segmenter work on the other, selected after
fit measurements. Different-device results must disclose backend/precision differences; a comparison
that changes both architecture and device is not a pure architecture ablation.

Cloud compute is an option to investigate if local runtime or memory limits progress. Before selecting
it, compare expected run cost, data transfer/setup time, storage and checkpoint retrieval, availability,
and compatibility with the portable CUDA route. No provider, spending limit, upload or paid job has
been selected or authorized by this planning discussion. Do not make cloud setup a prerequisite for
local progress.

### Minimum software work for the first Lenovo job

Implementation handoff: [Lenovo training setup specification](../operations/LENOVO-TRAINING-SETUP-SPEC.md).
Quinton will relay the Lenovo chat's readiness report for review before selecting the long experiment.

The current new trainer is not yet ready to launch unchanged on Lenovo:

- `segmenter_full_session_v1.py` accepts CPU/MPS only. Add CUDA execution and CUDA random-state
  checkpoint/restore handling, plus the corresponding state validation.
- `train_full_segmenter.py` uses macOS power/sleep commands and a platform-specific lock. Choose the
  actual Lenovo environment and provide compatible launch, locking and resource monitoring behavior.
- The current input manifest stores absolute Mac paths. Provide a portable root/path mapping and
  regenerate appropriate location evidence while preserving case membership and file identity.
- On Lenovo, verify the environment and a representative real batch, measure VRAM fit, then exercise
  save/restart on that backend before the selected long experiment. Do not assume an 8GB fit or promise
  launch immediately on arriving home. Transfer/preparation time is also still unmeasured.

These are bounded operational tasks, not a redesign of the model architecture. The autonomous adapter,
classifier, specialist networks, ensemble fusion and PANORAMA treatment arm are investigation work;
none must be complete before the first selected PanTS-only Lenovo training experiment. Quinton can
work on other homework today and resume setup at home; no unattended development is implied by this
plan. The present training run is not changed by these edits.

## Experiment record — fill before each launch and append results

- ID, question and proposal deliverable:
- Architecture/checkpoints and training membership:
- Data snapshot, patient groups, train/development roles and label provenance:
- Changed variable and fixed controls:
- Training horizon, sampling/exposure, initialization and precision:
- Inference reference-access boundary and failure behavior:
- Primary metrics, threshold-selection rule and adoption tradeoff:
- Machine, memory fit, storage, checkpoint/recovery and estimated runtime:
- Exact code/config and launch evidence:
- Results, paired comparisons, failure examples and uncertainty:
- Decision, limitations and next experiment:

## Decision checklist and living findings

- [ ] Historical 98% claim tied to its exact model, metric and leakage status.
- [ ] Raw-CT inference demonstrably independent of reference labels.
- [ ] Matched reference/autonomous outputs scored in original coordinates.
- [ ] Localizer failures retained in whole-system results.
- [ ] Lenovo completes a selected long run with retained checkpoints and usable recovery evidence.
- [ ] PANORAMA eligible pool and missing integration work documented from actual source evidence.
- [ ] Specialist routing evaluated against always-running the lesion expert before adoption.
- [ ] Baseline and next experiment chosen from measured failures and resource cost.

| Date | Finding / decision | Evidence | Next action |
|---|---|---|---|
| Oct8 | User confirms clean historical-recipe reruns, potential dual-laptop weekend experiments and cloud exploration | Current discussion; no paid job selected | Prepare bounded Lenovo port and choose independent experiments from evidence |
| Oct8 | User requests a two-week living investigation including specialist alternatives | Current discussion | Review over both weekends and append measured results here |
| Oct8 | Current training is entirely PanTS; PANORAMA source directories exist | Resume config + manifest + 1,408 admitted ID/path joins; source-root directory listing | Reconcile eligible PANORAMA pool under Plan03 |
| Oct8 | Older high containment and autonomous near-oracle claims have a documented leakage withdrawal | Experiment notebook July19 audit | Identify reusable checkpoint and eligible independent evaluation before claiming accuracy |

No new downloads, model jobs, source mutations or changes to the current training run were performed
to create this plan. Update this document rather than create competing architecture investigation queues.

## October 9 first implementation result

Implemented `src/data/segmenter_predicted_roi_v2.py`: a native binary localizer prediction defines
an all-support10mm region using geometryv2. Image-only preparation shares the current trainer's
physical mapping and HU normalization; hard three-class predictions can return to the native grid.
The adapter accepts no reference mask. It checks prediction/source/grid identity and refuses empty
localization, altered transforms, invalid image values and unknown output classes.

`segmenter_geometry_v2.plan_geometry` now explicitly distinguishes predicted versus reference origin;
its default retains existing training-record behavior. Added image-only `prepare_image`; the training
preprocess numerical path was not changed. The v1 adapter remains unchanged. V2 restores hard codes,
not interpolated probability maps; choose and document that distinction in the eventual scorer.

Verification:74 focused CPU tests passed in1.11s across predicted-ROI v1/v2 and geometryv2, including
seven new v2 cases. Tilted/sheared synthetic images match the existing training image preparation,
known tensor targets return to the expected native region, and failure cases are retained as errors.
No patient/model inference, trained-checkpoint loading, GPU work or new training was used. Lenovo's
running code was not changed. This is an implemented connection component, not an end-to-end result.

Inventory findings: the historical localizer run-info is retained under
`outputs/checkpoints/pants-level45/runs/localizer_fullscan_scaledmax__20260717_235833/run_info.txt`:
16k updates,96-cubed full-scan patches,1.5mm spacing,transfer initialization,DiceFocal,seed42,scaledmax.
Its leakage history remains disqualifying for the withdrawn validation claim. A filename search of
repo checkpoints and mounted artifact filenames found that record but did not locate a matching
historically named weight file; this does not establish that no weight exists in hashed stores.
The newer localizer code uses a binary SegResNet and sliding-window prediction. CAP-EXP-010/012
have retained audit evidence, but selecting/restoring an eligible checkpoint and its preprocessing
still remains to be connected to the new adapter and current segmenter.

Next concrete task: resolve one candidate's checkpoint/identity/preprocessing from its artifact receipt,
then implement a CT-only inference runner with native exports and explicit per-case failures. Reuse
existing checkpoint validation; do not silently load a historical three-class localizer into a binary
architecture. The completed adapter removes the geometry mismatch without deciding which localizer wins.

## October 9 CT-only execution and leakage safeguards

Quinton intends to share results with Johns Hopkins and explicitly requires avoiding oracle inputs
and leakage. The executable boundary is now `src/inference/autonomous_cascade_v1.py`:

- `run_case` receives one explicit CT path/hash, case ID, output directory and model options. There is
  no manifest, label path, reference box, outcome label or scoring input. Extra reference arguments fail.
- Whole-volume localizer preprocessing is called without a target, then sliding-window model logits
  produce a native binary mask. That prediction alone determines the stage2 region.
- Stage2 image preparation, inference and native hard-mask export use the geometryv2 predicted route.
  No component receives case diagnosis as a model feature. Case ID records lineage only.
- The runner reads the named NIfTI directly without discovering sibling files. Its current supported
  input is a finite3D CT with millimetre units; DICOM support is not implied. The localizer's inherited
  96M-source-voxel cap is still narrower than the segmenter's256M cap; refusals remain visible.
- A fresh output directory retains success or failure. No empty-localizer rescue with a reference crop.
  Evaluation/threshold selection are absent from this module and belong in a separate scorer.

Verification:19 focused tests pass in2.94s (two upstream TorchScript deprecation warnings). Three
new integration tests exercise real preprocessing, sliding-window execution, native restoration and
NIfTI export using **synthetic deterministic torch models**, not trained clinical models. Predictions
are identical with masks absent, deliberately incorrect masks present, then masks removed. A Python
file-open guard rejects reference-directory reads during the test and records that the adjacent mask
was not opened. Hash-mismatched CTs and reference arguments are rejected; empty localization retains a
failure report. This is code-level isolation evidence, not an OS sandbox or a trained-model benchmark.

The runner currently takes trusted model objects plus their declared checksums; it does not itself
load or authenticate checkpoint files. The next integration must bind those objects to verified,
reviewed checkpoint bytes and recipes before any trained-model result is reported. Neither a supplied
hash nor `reference_inputs_used=false` is, by itself, evidence of model provenance or zero leakage.

### Separate evidence needed for a scientific claim

1. **Inference inputs:** run the fixed executable with a CT-only directory, model artifacts and writable
   outputs; reference storage unavailable to that process. Preserve input/output identities. The present
   synthetic read-guard test is an initial check; real isolated inference remains pending.
2. **Training membership:** compare evaluation cases/patient groups/known duplicates against every model's
   training membership, including localizer, segmenter, classifier, ancestors and initialization where known.
3. **Selection:** development data may select checkpoints, crop margins, thresholds and architecture.
   Lock those choices before final held-out evaluation; repeated development scores are not test results.
4. **Scoring:** save predictions first; use a separate scorer that can read references and cannot alter
   predictions. Count every requested case and include failures. Report oracle/reference-crop comparisons
   as diagnostics only, never as autonomous performance.
5. **Limits:** distinguish case-ID disjointness from verified biological patient separation and disclose
   unresolved pretraining membership. Unlabeled scans demonstrate operational independence, but cannot
   establish Dice or lesion sensitivity without a suitable independent reference.

Read-only membership observation: CAP-EXP-012 attempt inputs at
`outputs/prowl/twomm-training-a0636d70-2ea5-4e5f-9167-db28bff562ba-execution/attempt/inputs.json`
contain113 optimizer and40 evaluator IDs. Optimizer IDs overlap current75 segmenter development IDs
in0 cases; evaluator IDs overlap in3. This is metadata evidence for that attempt only. Its parent
reference names the cd6be21f localizer checkpoint at step300; full ancestor/cohort reconciliation and
checkpoint payload verification remain pending. Do not infer parent separation from child separation.
The earlier historical scaledmax contamination remains withdrawn. The current SuPreM source-use
review explicitly leaves pretraining/selection membership unverified; this work does not resolve it.

No new real-data predictions, scientific metrics, training runs, data uploads or Johns Hopkins messages
were produced. Lenovo training was not changed. Next is the verified trained-model loader/lineage
binding and a small CT-only diagnostic, followed by independent native scoring on eligible cases.

## October 9 trained-model connection completed

See [checkpoint connection results](AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md). Actual CAP-EXP-012
and full-segmenter checkpoints now run through CT-only inference/native export on two development
cases. One visibly non-abdominal input produced unsupported organ predictions and remains a retained
failure finding; the second showed abdominal anatomy. Accuracy is unscored. The next step is separate
reference scoring and input-anatomy/provenance investigation, not another synthetic connection claim.

### October 9: first separate native scores and crop comparison

See [checkpoint connection diagnostic](AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) for retained
results and limitations. The abdominal diagnostic achieved lesion Dice0.726 from CT-only prediction;
both predicted and reference regions contained all annotated targets. The reference-assisted comparator
had Dice0.703 with higher recall and more false positives. These are selected development diagnostics.
The suspicious scan has a74-voxel pancreas annotation and severe autonomous false positives. Its CT/label
hashes match prior preparation, but anatomical validity is unresolved. Frozen cohorts and Lenovo training
were not changed. Added independently tested, model-free native scoring; robust unsupported-input
handling and fixed-cohort evaluation remain unfinished.

### October9 fixed75-case autonomous baseline

All admitted development IDs were frozen before evaluation, with two existing outputs reused.56
predictions scored;19 failed explicitly (11 oversized predicted-region grids,7 unknown CT units,
1 projected whole-scan grid). Mean lesion Dice0.244807 over28 scored positive cases;10other positive
cases failed. This supersedes interpreting the single-case0.726 as typical quality. See the detailed
[connection report](AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) for denominators, resource evidence,
source-review limits and specific next corrections. No training was changed.

October9 geometry correction recovers all12 prior geometry failures with explicit64M voxel ceilings
and unchanged numerical settings; measured peak4.16GiB under12GiB. Combined accounting now68/75
outputs, with seven unknown-unit inputs still unresolved. CT-only hash-bound unit-review support is
implemented, but no source evidence has been fabricated.31 focused tests pass. Recovered-case quality
is poor; matched crop/resampling-versus-segmenter analysis remains necessary. See the connection report.

### October9 paired diagnosis: crop scale/context is a major contributor

All68 available cases now have matched autonomous/reference-crop results, with the same segmenter.
On33 positive cases, lesion Dice is0.225818 versus0.422671; on35 reference-empty cases, predicted lesion
volume is21.291808 versus1.527572mL. Reference-assisted values are diagnostics, never autonomous scores.
All41 lesion components survive both resampling paths. Nearest-label roundtrip Dice is0.896041 versus
0.946782, so complete lesion disappearance does not explain the gap. Median paired crop-volume ratio
is5.533175 and median lesion-tensor-voxel ratio0.225107: predicted crops present much broader context.

The next controlled experiment should refine the CT-only crop policy and measure both coverage and
quality with fixed weights. A separate Lenovo experiment should investigate training with realistic
crop variation. Neither is a reason to modify the currently running job. Four diagnostic tests pass;
initial near-binary decoding failures and one interrupted attempt are preserved. See the
[matched results and limits](AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md) before interpreting these
selected development findings as general performance.
