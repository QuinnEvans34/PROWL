# Universal Swin candidate: provenance and next study

November 6 discussion draft. Research, metadata review and planning only; no new
GPU job, acquisition of evaluation scans, retry, fine-tuning or promotion is
launched by this document. The completed four-case request/permit is consumed.

## What the candidate is

This is the CLIP-Driven Universal Model with a Swin UNETR backbone: a 3D CT
segmentation network, not the conversational assistant. City University of Hong
Kong, Johns Hopkins and NVIDIA contributed the official implementation, associated
with ICCV 2023 and its Medical Image Analysis 2024 extension. CLIP class embeddings
condition segmentation heads; users do not chat with this model. The
[official source](https://github.com/ljwztc/CLIP-Driven-Universal-Model/tree/43c12399cc98a40f447342a8dc2cecae5edae84c)
and [paper](https://arxiv.org/html/2301.00785v3) describe this design.

Our strict-loaded implementation has 62,595,315 parameters versus roughly 14.1M
in the student. Its 32 independent sigmoid channels include pancreas and pancreas
tumor. Its advantages as a candidate are task-relevant supervised CT pretraining,
greater capacity, and successful CT-only inference on our actual hardware. Those
are reasons to test it, not proof that size caused the observed improvement.

| Identity | Exact retained value |
| --- | --- |
| Source revision | `43c12399cc98a40f447342a8dc2cecae5edae84c` |
| Weight repository revision | `76f0304ff9387c1baccbbc1d9eac78c5c5ccfeed` |
| Weight filename | `clip_driven_universal_swin_unetr.pth` |
| Weight SHA256 | `cde35d9ca344a744c849ebe0cd086cb64984e79f605376c56bd04531c767ed07` |
| Actual model-load audit | `outputs/prowl/universal-swin-audit-20261105-01/audit.json` |
| Completed screen request SHA256 | `4654d46b730abe8c144b1cc57af607d579154b1c96ff707c37861fbce55fadc5` |
| Screen MLflow run | `051c194b2e54428aba6b9420129e18b6`, FINISHED |

The [screen results](UNIVERSAL-SWIN-RESULTS-20261105.md) average .710754 lesion Dice
on four positive exposed-development cases: 2028, 1347, 2514, 8743. Three improve
over the prior autonomous predictions; 1347 worsens. No negative case passed that
screen's strict unit admission. All twelve proposed training cases also failed
reference-unit admission, so no fine-tuning occurred. Inference took 365 seconds;
GPU reserved memory peaked at about 4.58 GiB under the existing 6 GiB ceiling.
Training memory and speed are not yet qualified.

This four-positive result is not comparable to the KD average over 36 positives,
does not measure negative-case false alarms, and is not a new trained successor.
The native restoration implementation also differs from the historical upstream
environment, as recorded in the frozen screen design. We do not reproduce or
claim the publisher's benchmark numerics.

## Leakage finding: source overlap is confirmed; patient membership is unresolved

The Universal paper describes 3,410 training CTs assembled from fourteen public
datasets, including MSD pancreas and Pancreas-CT. Its
[dataset table](https://arxiv.org/html/2301.00785v3#Sx2) distinguishes training
sources from external evaluations. The pinned repository also lists these sources;
the paper and current repository describe different release details, so aggregate
paper counts must not be substituted for this checkpoint's exact membership.

The [PanTS paper, sections 3.2 and Appendix A](https://arxiv.org/html/2507.01291v1)
states that its public training partition assembles earlier public datasets,
including MSD, Pancreas-CT, LiTS, CT-ORG and several other Universal sources.
Our custom development cases are drawn from that public partition, not the
publisher's independent institutional test set. Thus a random custom train/dev
split does not establish separation from external pretraining.

| Question | Current answer | Evidence still required |
| --- | --- | --- |
| Do the projects share source datasets? | Yes | Already supported by both publications |
| Were these four patients used to train/select this checkpoint? | Unknown | Checkpoint-bound train/selection lists plus original patient/series crosswalk |
| Are all custom train/dev cases independent biological patients? | Unverified | Reliable patient grouping, including unresolved 6755/2889 relationship |
| Does different PanTS naming, file hash or release date prove absence? | No | Renaming, conversion, reorientation and repeated series can change bytes |
| Does an encoder-only transfer or new head remove pretraining exposure? | No | The retained encoder has still seen its pretraining images |
| Is the existing KD teacher proven unexposed to our development cases? | No | Retain the existing teacher-assisted exploratory label |

There is no verified patient match yet, so do not assert that the four cases are
contaminated. There is also no verified separation, so do not assert leak-free
generalization. Reannotation of a previously seen CT does not create an unseen
patient. Model selection/validation exposure matters as well as training exposure;
unlabeled pretraining exposure must also be disclosed.

Resolve this using retained metadata first. Record original source collection,
original case/series and patient-group identifiers, evidence reference/hash, and
pretraining and checkpoint-selection membership for each intended evaluation case.
Use `confirmed_seen`, `verified_unseen`, or `unknown`, with reasons; never treat
missing metadata as unseen. Reuse existing duplicate evidence rather than silently
running another bulk image audit. Lenovo has been asked for a bounded retained
metadata review; patient-level clearance remains pending that evidence.

If the crosswalk cannot be established, retain these results for exposed-development
engineering only. A clean claim needs a separately admitted source/patient-disjoint
evaluation cohort, supported by training/selection provenance or a reliable
publisher attestation. Source-disjointness must consider nested/repackaged datasets.
Alternatively select an initialization with auditable separation or use a fresh
random-initialized model. Switching checkpoint names or relying on an older
publication date is not a fix. No author message or new data access has been sent.

## Recommended experiment sequence

1. **Close the KD interpretation.** Use the full-series
   [descriptive analysis](KD-DESCRIPTIVE-ANALYSIS-20261106.md), retain selected and
   terminal artifacts, and inspect matched saved overlays for major gains/misses.
   Do not train again simply because unused budget remains.
2. **Resolve provenance and geometry before expanding the model screen.** Freeze
   eligibility using source/patient separation, role and valid physical units,
   without consulting scores. Preserve all exclusions and unknowns. Missing-unit
   training/negative cases require an independently justified geometry path; do
   not add `mm` to original headers or reuse an incompatible cache.
3. **Measure the untouched checkpoint broadly.** After eligibility is frozen,
   evaluate both positives and reference-empty cases, retaining failures in the
   attempted denominator. Reuse the four saved predictions under their original
   scope. Keep verified-unseen and unknown/seen strata separate; never select the
   favorable cases to obtain a clean-looking mean. A broad development screen
   remains exploratory after repeated use.
4. **Qualify one short adaptation.** Compare the untouched checkpoint with a new
   train-role-only adaptation, using the same architecture, preprocessing, output
   mapping and inference in both arms. Freeze encoder initially as a proposed
   resource-saving adaptation strategy, then decide from a measured pilot; this
   does not test architecture size alone. A draft ceiling is 1,000 updates and two
   supervised hours, subject to actual training memory/throughput, restore and
   safety qualification. Exact sampling, learning rate, loss and selection cadence
   remain to be frozen; no unqualified values are silently inherited from the
   SegResNet recipe. Inference fit does not establish training fit.
5. **Decide before committing to a long run.** Primary: positive-case macro Dice
   over the fixed eligible cohort, misses included. Also report lesion-component
   overlap/recall, small-component coverage, positive voxel recall/precision,
   negative alarm rate and lesion volume, pancreas Dice, runtime/memory and all
   failures. Preserve a fixed threshold rather than tuning on final holdout.
   Select using only the designated development policy and report terminal too.
   Resolve patient grouping before patient-level intervals. Freeze a practical
   decision bar before seeing adaptation outcomes; the old KD bar is not silently
   rewritten or transferred to a different experiment.

An untouched final cohort must remain out of adaptation, threshold choice,
checkpoint selection and model-choice feedback. A final model is frozen before
that one evaluation. A reused custom development cohort cannot be made untouched
by assigning it a new label. Evaluation access remains a separate scoped action.

## How to log the work

Keep one scientific identity per question, with original attempt/continuation
identities beneath it; retain failed attempts and their budgets. Use the project's
[experiment protocol](../evaluation/EXPERIMENT-PROTOCOL.md) and
[MLflow convention](../../experiment-tracking.md).

| Record | What it represents | What it must not imply |
| --- | --- | --- |
| Existing matched KD series | Completed exploratory teacher-assisted control/treatment, all twelve validations, selected and terminal endpoints | Independent teacher exposure or practical success |
| Existing Universal screen | Pretrained inference-only exploratory run, four positive cases, zero optimizer updates/training hours | Fine-tuned model, balanced baseline or clean test result |
| This review | Post-hoc analysis/provenance findings, exact source hashes, no model calls | Prospective preregistration or another training run |
| Future adaptation | New versioned exploratory experiment with its own preregistration, parent weights and bounded qualification | Continuation of the consumed four-case permit |

MLflow should retain resolved configuration, data-role/membership hashes,
source/weights revisions, training and selection exposure status, environment,
hardware, code commit, native prediction/checkpoint identities, per-case metrics,
full curves and resource/cleanup evidence. Tag unknown overlap explicitly and link
the comparison report and continuation lineage. Register a new trained model only
after an actual adaptation, not after loading publisher weights.

Do not create a replacement RUNNING record or rewrite the FAILED historical
control continuation to make a cleaner dashboard. A comparison-only record, if
added, logs already completed results and references their owning runs, with zero
additional training time. The append-only review index below records this review
without modifying old frozen experiment designs:
[experiment review index](EXPERIMENT-REVIEW-INDEX-20261106.md).

The checkpoint card's MIT declaration and source CC-BY-NC-ND terms are separately
recorded in the original audit. Keep upstream source, weights and adaptations
private while artifact-specific redistribution terms remain unresolved. No source
license is inferred from a model-card tag.

**Decision:** Universal Swin is the leading candidate for the next investigation,
not an accepted leak-free replacement. Establish provenance, inspect saved outputs,
and freeze a balanced screen before budgeting adaptation.
