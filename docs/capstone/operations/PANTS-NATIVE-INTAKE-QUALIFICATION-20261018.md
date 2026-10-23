# PanTS full lesion coverage qualification

The input fix is being qualified before scientific training. The previous pancreas crop
clipped **43 of 671 positive training cases**. The replacement preserves acquired target
detail and uses overlapping 3D windows instead of shrinking an entire crop into one cube.

**Final status: INTAKE_VERIFIED_REVIEW_REQUIRED. All seven intake-qualification stages complete.**
The new input path is qualified for scientific-run review. Scientific training has not
started and still requires approval of the run configuration and its launch integration.
Engineering fidelity is not learned-model Dice.

| Stage | Verified result |
|---|---|
| Measure coverage | All 671 positive training masks accounted for; 43 clipped by the old crop |
| Freeze design | Versioned upsample-only physical windows, 144³, stride 72; documented context/compute tradeoffs |
| Separate implementation | Original pipeline preserved; 178 focused tests passed, one explicit Mac-only skip |
| Real pilot | All 12 cases exact tiled target reconstruction; all 12 image sets reviewed |
| Complete intake | All 1,333 train and 70 development cases passed; no omissions or new exclusions |
| Actual GPU path | Four updates plus one cold-restored update; independent backup; two gap-free full-scan reconstructions |
| Readiness evidence | Frozen code/configuration/evidence receipt; MLflow engineering record verified; human review pending |

## What changes and what stays fixed

The loader first reorders and flips axes losslessly. Coarse axes are then subdivided by
integer factors to at most 1.00001 mm spacing; already finer axes remain unchanged.
Voxel-cell field edges and acquired obliquity are preserved. CT is linearly interpolated
after the existing HU normalization; labels use nearest neighbors. No axis is downsampled.
Windows are sampled on demand, avoiding a dense upsampled whole-scan cache.
It supplies 144 × 144 × 144 voxel windows. Inference
covers the full CT with 50% overlap, positive blending weights and exact restoration to
the original voxel grid. Neither lesion nor pancreas labels select inference windows.

Training retains the existing full-cohort case shuffle. For positive cases, it cycles
windows covering the complete lesion bounding field, followed by varied component-centered
windows. Every fourth case visit samples a window uniformly from the full CT. Reference-empty
cases use complete pancreas coverage plus a pancreas-centered view. These are training-only
uses of annotations. The audit requires the union of the minimum 18 training visits to cover
100% of annotated lesion voxels, or the pancreas in reference-empty cases.

The previous pipeline, source data, exclusions and completed scientific runs remain unchanged.
The network still receives a single CT channel. Pancreas and lesion masks provide supervision;
they are not additional input channels. The targets retain background, pancreas and lesion classes.
The proposed scientific comparison retains the architecture, original SuPreM initialization,
loss, optimizer and augmentation. Learning rate reduction remains a later experiment.

This is a combined input representation, sampling and inference experiment. Any improvement
cannot be attributed to cropping alone. Full-CT inference is a harder background search than
the previous provided-pancreas crop, so false-positive behavior remains a key guardrail.

## Coverage findings

The original crop inventory accounted for all 671 positive training masks and verified
their identity, geometry and lesion totals against the admitted metadata.

| Original crop finding | Cases |
|---|---:|
| Complete lesion coverage | 628 |
| Some lesion outside the crop | 43 |
| Less than 90% retained | 22 |
| Less than 50% retained | 10 |

The lowest retained fraction was 3.07%. These cases remain in the cohort. No difficult
annotation was deleted or relabeled to improve the audit result.

## Intermediate native-only pilot and source audit

All 12 previously selected training cases passed the strengthened native-only pilot. The complete
source lesion targets survived exactly, with target round-trip Dice and recall of 1.0.
The actual weighted tiled reconstruction of one-hot targets was also exact. This is an
oracle geometry test, not a learned-model score.

All 12 cases reached 100% annotated lesion-field exposure in the simulated 18-visit schedule.
Three native planes per case were reviewed with CT, annotation and the first training window.
The tiny 12-voxel lesion remains 12 voxels; the severely clipped large annotation remains
fully available across its coverage windows. Clinical correctness of the source annotation
has not been re-adjudicated.

The preliminary pilot was strengthened before cohort verification to check whole-field
training exposure, rather than component centers alone. Both pilot attempts are preserved.
The first cohort dispatch stopped before reading a new case because the journal reader
did not tolerate blank lines. Its logs and reaped-worker evidence are retained separately;
a tested parser amendment preserves all original journal bytes and numerical policies.

The serial audit was intentionally stopped after preserving its completed prefix to improve
CPU throughput. A two-worker continuation reuses 153 qualified records, including pilot
cases not yet reached in serial order, and checks only the remaining 1,250 cases. It retains
the original total time allowance, combined 12 GiB memory limit and 100 GiB free-space floors.
The numerical input code remains frozen. The initial continuation test fixture used the
wrong resource-key name; that test evidence is retained, and all three corrected tests pass.

The complete source audit subsequently passed all 1,333 training and 70 development cases.
Combined audit time was 4,710.093 seconds, peak owned RSS was 2,932,871,168 bytes, and workers
were reaped. The physical-window cohort verification reuses this completed CT-content
evidence under unchanged source observations; it does not repeat CT or overlap audits.

## Why the final candidate differs

The native-only candidate passed target preservation but exposed an avoidable scale issue:
source spacing reaches 10 mm, so one 144-voxel axis could span 1.44 m. We therefore chose
upsample-only physical windows before scientific training. All 671 positive training
annotation fields still fit into at most two guaranteed coverage windows. The final
physical design is frozen in `PANTS-PHYSICAL-DETAIL-INTAKE-20261018.json`.

The final 12-case pilot tests actual CT windows and complete tiled native reconstruction.
All twelve now pass, including exact native target restoration and 100% scheduled field
coverage. All twelve three-plane figures were visually reviewed. Supervised duration was
536.75 seconds, peak owned RSS 2,437,160,960 bytes, and the worker was reaped. Black padding
on short scan axes and partial anatomy in individual windows are explicit, not missing
source data. The unusually large annotation remains included without clinical relabeling.

The regression suite passes 125 tests with one explicit Mac-only skip. An additional
53 physical reconstruction safety tests pass, including all axis-order/flip combinations
with oblique geometry and rejection of missing, duplicate and invalid tiles.

The complete physical cohort pass separately checks each case's field-edge mapping,
gap-free inference coverage, target preservation in every annotation-coverage window,
and deterministic 18-visit training exposure. It does not claim a full tiled oracle was
run on every case: that expensive actual reconstruction is exercised on all 12 pilot cases,
with per-case axis coverage proofs and actual annotation-window round trips on all 1,403.

The complete physical cohort pass finished successfully: 1,333 training and 70 development
cases, no omissions or new exclusions, exact native targets, and 100% annotation-field
coverage. It reused the twelve pilot records, checked the remaining 1,391, and performed
zero additional CT-content reads. Supervised duration was 2,978.406 seconds with peak
owned RSS 1,866,088,448 bytes; all workers were reaped.

Across both roles, the verified labels contain 7,145,665 lesion voxels and 868 connected
lesion components, all preserved. Positive training lesion fields need at most two
guaranteed coverage windows; complete pancreas coverage in reference-empty cases can
need more (up to eight). Every case passes the minimum 18-visit exposure check.

Full-CT inference requires 9–468 windows per scan (median 96). The 70-case development
set totals 7,698 windows per validation pass. This is a material compute tradeoff and
must inform validation cadence, rather than silently reusing the old cheap crop schedule.

## Important tradeoffs

- Spacing is capped at approximately 1 mm without coarsening finer scans. Physical scale
  therefore varies less but is not identical across scans. A 144-voxel window is not always
  a 144 mm cube. Thick slices do not gain newly acquired detail from interpolation.
- Exact round-trip claims apply to annotation targets and their native boundaries, not
  bitwise CT intensity preservation. Linear CT interpolation changes samples and can
  soften intensity transitions; the pilot images were reviewed for this distinction.
- A forward pass still sees one window, not the entire pancreas or CT at once. Overlap and
  complete coverage do not create whole-organ neural context.
- Short scan axes require zero padding. Padding is tracked explicitly and is not augmented
  into invented anatomical content.
- Full-CT inference takes many more forward passes. Actual GPU costs and the proposed
  training budget must be reviewed before launch.

## Actual training-path qualification

Four real CUDA optimizer updates passed with finite loss and gradients using the original
SuPreM initialization, new physical-window provider, retained augmentation and actual
model/optimizer. These weights are nonpromotable. The step-three checkpoint was copied
to independent internal storage and hash verified. A fresh worker restored exactly and
reproduced step four with identical sampled/augmented input hashes; maximum state difference
was 7.450580596923828e-9, within the existing numerical tolerance.

Full-CT model inference on the largest native positive and reference-empty training grids
completed 420 and 294 windows, respectively, with positive blend weights and zero gaps.
They took 291.828 and 229.953 seconds including loading and metrics. This was a resource
stress test, not a scientific model-quality evaluation. Four-update model Dice is not
evidence for or against the scientific hypothesis.

Peak GPU allocation was 3,454,467,072 bytes (3.22 GiB); reservation was 3,883,925,504 bytes
(3.62 GiB). Peak owned producer RSS was 8,231,505,920 bytes (7.67 GiB), below the 12 GiB
limit. Producer and cold workers were reaped. Individual update times were 14.125,
11.235, 4.390 and 3.062 seconds; four heterogeneous updates are not a reliable whole-run
runtime estimate. Full validation cadence must be budgeted for 7,698 development tiles.

All 445 producing files pinned by the successful prior scientific run still match.
The focused test suites have 178 passes and one explicit Mac-only skip. A separately
attempted legacy content suite imports Unix-only `resource` and cannot collect on Windows;
its failure is retained, not counted as passing. This is not a claim that every repository
test suite has been run successfully on Windows.

## Decision and scientific handoff

**Engineering acceptance: pass.** Full annotated field coverage, native target boundaries,
component retention, role protections, reconstruction and checkpoint restoration meet the
frozen gates. No difficult cases were removed. No protected-test payloads were read.

**Scientific hypothesis: untested.** We have not established that these inputs improve
learned lesion Dice, detection or false positives. The next experiment must evaluate that
on the unchanged development cohort. This is a bundled input/sampling/inference change,
not an isolated cropping-only causal test. The previous selected native Dice of approximately
0.424 remains the trained-model reference; target-oracle Dice 1.0 is not a new model record.

Before scientific launch, review this report, approve the training/validation time budget,
and bind the scientific run configuration and production launch integration to this
qualified input path. The current receipt is explicitly not launch authorization.
No long run, automatic retry, resume or scheduled monitoring was started.

## Frozen receipt and MLflow

Receipt: `E:/PROWL/readiness/physical-intake-20261018-a01/ready.json`.
SHA256: `837bfbce8f81198c4ee1fd1a939456e7d1ea2e49551d90ff07fec5cb2ad924da`.
It binds code, configuration evidence, case records, images, tests and E:/C: checkpoints.
Final source observations and original baseline producing hashes were checked again.

Local MLflow experiment: **PROWL input engineering**. Human-readable run:
**Preserve every annotated lesion voxel — input qualification**.
Run `2a7376bd21fc45d5aa679946a8af1cd2` is FINISHED, with all ten engineering metrics read
back and verified. It is tagged nonpromotable, backfilled and not scientific training.
Oracle target fidelity is namespaced as engineering, never recorded as learned-model Dice
or credited to the dashboard's scientific training-hour total.

## Local evidence

- Original coverage inventory: `E:/PROWL/readiness/training-coverage-inventory-20261018-a01/`.
- Strengthened pilot and cohort audit: `E:/PROWL/readiness/native-intake-20261018-a02/`.
- Final physical-window qualification: `E:/PROWL/readiness/physical-intake-20261018-a01/`.
- Preliminary pilot and preserved producing sources: `E:/PROWL/readiness/native-intake-20261018-a01/`.
- Original input fidelity comparison: `E:/PROWL/readiness/input-fidelity-20261018-a01/`.

CT figures and case-level evidence remain private local artifacts, not dashboard content.
