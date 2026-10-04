# Next localizer cohort — proposal after CAP-EXP-006

Status update D-289: **metadata candidates selected; not qualified, frozen or launch-ready**.
Quinton requested continuation; Codex implemented the proposed counts/policy as bounded preparation.
See [selection results](LOCALIZER-CANDIDATE-EXPANSION-RESULTS-2026-09-29.md). The original rationale follows.
Read CAP-EXP-006 results and the source-grid inspection report before adopting a training treatment.

## Why expand

The16-case cohort demonstrated learning and exposed a train/validation coverage gap. It was selected
rare-stratum-first to exercise varied inputs, not as a frequency-representative training population.
The protected metadata universe has12 train phase×spacing strata; several have only1–25 cases,
while noncontrast/thin alone has2820/7200. Retaining difficult cases and learning from more common
examples are compatible. More duration on the same16 is not the priority after006.

## Proposed candidate budget and selection

Recommend **128 training /48 development-validation candidates**, not promised executable counts.
This is a staged expansion, not full-scale training or a final evaluation sample. Exact batch costs
must be projected from inventory before any new source-array job. Do not pre-authorize all reads
based on these counts; produce bounded job manifests and budgets first.

1. Preserve all prior28 candidate identities and protected roles, including held6350. Retain existing
   positive qualifications as evidence, not blanket permission for changed targets or sources.
2. Use only pinned protected membership, inventory, case ID, phase and spacing for selection. No
   current prediction, Dice, disease metadata, apparent label quality or readability rank enters it.
3. Proposed coverage floor: up to4 candidates per available training stratum, up to3 per validation
   stratum, including retained candidates. For strata with fewer available members, retain/report
   the shortfall; never borrow across protected roles. Missing phase remains its own stratum.
4. Fill remaining slots in proportion to remaining stratum population using a frozen largest-remainder
   allocation; deterministic hash order within each stratum and a documented tie rule/seed. This
   adds a population-proportional component while preserving the deliberately varied diagnostic set.
5. Report retained diagnostic members, coverage-floor additions and proportional additions separately.
   The combined sample still oversamples rare strata; do not call its unweighted scores population
   estimates. Changing membership creates a new selection version; no model-driven exclusions.
6. All holds remain candidates and in requested-versus-executable accounting. No silent refill. For
   arterial/thin validation, additional explicitly selected candidates may qualify;6350 itself stays
   held until its physical-unit evidence is resolved. Candidate coverage is not executable coverage.

Current11 validation cases are repeatedly inspected development cases. New validation additions are
also development-only once inspected; they do not become an untouched final test set. Keep publisher
holdout and final model-selection boundaries unchanged. Biological patient uniqueness is still an
open limitation requiring evidence, not assumed from file or study separation.

## Bounded implementation phases

A. Review/adopt exact counts and deterministic selection policy; implement synthetic selection tests
   for nesting, held-member accounting, shortages, missing metadata, exact quotas and protected roles.
   Produce metadata-only candidate accounting and source-byte/header projections.
B. Freeze qualification jobs with exact inventories and staged resource budgets. Reuse valid retained
   evidence where appropriate; qualify every newly consumed CT/target. Preserve unknown units,
   partial coverage and annotation uncertainty explicitly; difficulty alone is not exclusion.
C. Publish new immutable role-specific cohorts with positive purpose qualifications, retaining all
   original source/protection/issue records. Independently resolve membership before model loading.
D. Implement a versioned consumer for that new bundle. Current16/11 factories,54-file budgets and
   request pins must not be widened by swapping constants. Measure streaming/cache options and
   complete preprocessing/geometry checks before choosing a RAM policy. The512MiB current cache
   is not presumed sufficient; likewise do not silently lift16GiB or per-domain storage caps.
E. Freeze the experiment question, exposure budget, scheduler and evaluation/ROI safeguards after
   the coverage audit. A larger cohort at the same total steps gives fewer draws per case; specify
   whether the comparison fixes total compute or per-case exposure. Changing both without reporting
   it is not a data-only causal comparison. Do not promise128×150 updates before resource profiling.

## Learning priorities

The immediate scientific requirement remains high-recall localization with a tractable crop.
Source-grid coverage, per-case misses, distant false components and downstream mapping matter
alongside Dice. Threshold/margin changes, sampling/augmentation, and data breadth are separate
candidate interventions; do not combine them all into the next run. Saved hard masks alone cannot
show whether a lower threshold would recover missing pancreas at acceptable crop size. Any such
probability audit needs a separately frozen inference-only plan; no automatic threshold adoption.

Keep all useful/null results and current diagnostic cases. PANORAMA, lesion segmentation and model
architecture changes remain separate work; none is a prerequisite to this PanTS-only cohort expansion.
