# D-294 — broader purpose qualification and frozen cohorts

**113 training and 40 development-validation members are positively qualified and frozen.**
All176 candidates remain accounted for; 23 are held (15 unresolved CT units,8 empty references).
No replacement, raw source read, model inference or optimizer update occurred. The existing16/11
runtime and earlier cohort artifacts remain unchanged.

## What the records permit

Training annotations permit `training_target`; validation annotations permit `evaluation_reference`
only. Qualification is for the publisher's visible pancreas reference in the acquired CT, not
whole-organ completeness or expert contour acceptance. Difficult cases remain, including2727's
single boundary slice,5190's sparse reference,8988's noise and limited coverage, and4359/6110's
short coverage. Case-specific observations and all23 predecessor issues are retained. Empty masks
are unknown targets with no allowed use, not automatically trusted negatives or corrupt labels.
The15 CT-unit holds remain unresolved; no source units were inferred or rewritten.

All28 predecessor annotation identities and attached issues remain; their snapshot linkage is
updated in the new manifest. All13 older issues and the10 D-282 additions survive exactly.
Protection parents remain7200train/1800validation/901publisher-test. No publisher-test data opened.
Private research scope, license discrepancy, source-asserted label provenance and unverified
study-as-subject biological uniqueness remain explicit. No public release permission is inferred.

The40-case validation cohort includes6 arterial/thin-slice cases, filling that gap in the earlier
11-case cohort. Delayed/thin-slice validation has only1 qualified case of3 candidates. Candidate and
executable stratum counts are retained separately. Rare strata were deliberately oversampled:
unweighted cohort performance will not be a population estimate or final-test result.

## Reproduction and implementation

New `localizer_expansion_v2.py` derivation and `freeze_localizer_expansion_v2.py` publication CLI bind
the exact candidate selection,16 content packages, reconciliation and earlier reviews to purpose
records. Every retained package member was verified. Publication reproduced the proposed payload,
validated the persisted bytes before atomic completion, and a fresh process independently resolved
**113 optimizer /40 evaluator members** from the registered external cohort area. No global registry
switch changed. Published inputs and derived payload total53,200,808bytes.

| Identity | Value |
|---|---|
|Bundle|`cohort-bundle:pants-localizer-expansion-0002:v1`|
|Train cohort|`cohort:pants-localizer-expansion-train-0002:v1`|
|Validation cohort|`cohort:pants-localizer-expansion-validation-0002:v1`|
|Plan SHA-256|`e6bda831b66966b3a93f4cdb9c0eab5f7fa86b49313e9141215fd51132e58ab7`|
|Inputs SHA-256|`2c6c723cf4658d8d4926d07b804f20abc10b1afd83485f36adab4d436a809785`|
|Current manifest SHA-256|`3f1a54f202773dd2ed7fe8c274385b52f53e8ececedd5c1fe2ec4a07d5065558`|
|Completion SHA-256|`b401fa1ba8b0ab25dbe6abfe575e60d03dba438db493175c5d5b4bd0b03293b7`|
|Review receipt SHA-256|`1143fd10557c1d87b8b714c648b051e631dc49f867ef43a7353da6550ba72db9`|

Local staging: `outputs/prowl/expansion-v2-candidate-6bc5c245-47b4-45ab-9616-cd75da986b74`. Publication/replay and test logs:
`outputs/prowl/expansion-v2-freeze-review-20260929`. Internal staging preserves the same payloads
as the external publication; this is not a new automated backup-policy or model-checkpoint claim.

**1,284 native tests passed**, two existing upstream warnings (elapsed time retained in the native log). Twenty new regressions cover
empty-target retention, inherited holds, role safety, stale manifests, missing/mutated evidence,
source geometry tolerance and canonical identity scopes. `git diff --check` passed.

During implementation, synthetic checks caught the empty-target schema requiring unknown/unavailable
status rather than a voxel-presence method; fixed before publication. Initial retained-evidence
preparations also exposed differing historical receipt formats, absent plane lists for empties and
an exact-affine comparison. The last affected held2691 only:1.49e-8 difference, within the audit's
existing1e-5 absolute tolerance. Tests now preserve that same tolerance and reject larger differences.
No failed preparation published a bundle or changed eligibility.

Two unpublished preparations were deliberately stopped to address validation cost. CPU sampling
first identified repeated linear source-identity lookups. `source_inventory_records.py` now builds a set for membership tests while
retaining sorted/unique checks and canonical output. A real retained inventory summary matched
exactly and took0.137s versus0.902s (6.6x for that operation). A second bottleneck was full-manifest revalidation per qualification. The new CLI opts into a
one-entry process-local validation session keyed by actual canonical manifest bytes, original
membership bytes and every contract schema's bytes. Mutations invalidate it; failed validations
never populate it; fresh processes start empty. All other callers retain uncached behavior. Tests
verify mutation, schema/membership changes, scope exit and Python/JSON shape confusion. The first completed preparation
`expansion-v2-candidate-f70e458e-345f-4b06-80b8-b070c6485155` was retained but superseded before
publication to add the JSON-shape regression. Fresh code pins were captured after both
changes and the full native suite passed. No caller-supplied validation claim is trusted.

## Next: expanded input readiness

The [consumer packet](LOCALIZER-EXPANSION-V2-CONSUMER-PACKET-2026-09-29.md) specifies the next bounded
implementation.306 qualified source files total5,152,089,856compressed and13,196,550,237expanded bytes.
Five qualified scans exceed the old64M source-voxel cap; maximum92,889,088. The existing3mm/HU/geometry
recipe is retained as the starting point, pending projection and real preprocessing verification.

Implement a separately versioned role-safe consumer, synthetic geometry/resource checks, frozen
read-only batch requests and transformation review. Verify that narrow/sparse references survive
resampling; do not silently drop a failed case. Measure cache/streaming and CPU/MPS costs before a
new run budget and launch request. Qualification is complete; broader preprocessing and training
are not yet complete or launched.
