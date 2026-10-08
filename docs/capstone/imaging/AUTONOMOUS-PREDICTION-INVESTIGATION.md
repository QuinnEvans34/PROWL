# Autonomous prediction investigation: two-stage, single-stage and specialist systems

**Owner:** Quinton Evans + development chat  
**Created / updated:** October 8, 2026  
**Target window:** October 8–22, 2026; review October 11 and 18; decision checkpoint October 22  
**Status:** Living investigation; experiments proposed, no new jobs launched by this document

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
| Oct8 | User requests a two-week living investigation including specialist alternatives | Current discussion | Review over both weekends and append measured results here |
| Oct8 | Current training is entirely PanTS; PANORAMA source directories exist | Resume config + manifest + 1,408 admitted ID/path joins; source-root directory listing | Reconcile eligible PANORAMA pool under Plan03 |
| Oct8 | Older high containment and autonomous near-oracle claims have a documented leakage withdrawal | Experiment notebook July19 audit | Identify reusable checkpoint and eligible independent evaluation before claiming accuracy |

No new downloads, model jobs, source mutations or changes to the current training run were performed
to create this plan. Update this document rather than create competing architecture investigation queues.
