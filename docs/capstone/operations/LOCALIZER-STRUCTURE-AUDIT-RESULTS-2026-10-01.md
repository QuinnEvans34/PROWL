# Retained localizer structure audit results

October 1, 2026 — D-314 complete. No new model execution, training, original CT/target arrays,
qualification, adopted cleanup or promotion. Existing 153 members/23 holds unchanged.

Small disconnected regions often inflate crop extent, while most oversized foreground lies inside
one broad component. Both problems matter: component selection could materially reduce crop cost,
but deleting islands alone cannot solve overprediction or repair existing misses. A fresh reference
coverage diagnostic is justified before considering any changed ROI policy.

## Exact comparison

CPU analysis of 92 retained native masks: CAP-EXP-010 and CAP-EXP-012 child step 300 on all 40
development-validation cases plus training failures 150, 756, 6110, 6822, 7604 and 7684. Selection
was frozen before measurements. Separate 26-connected components, deterministic volume ranking/
discovery-order ties, physical volume and half-open acquired-grid bounds, unchanged 10 mm margin.
The hypothetical largest-only box never replaced a raw mask or production box.

|Validation measure, 40 cases each|010|012|
|---|---:|---:|
|Components per mask, range|2–36|1–33|
|Median foreground share in largest component|99.268%|99.394%|
|Minimum foreground share in largest component|54.078%|55.289%|
|Mean raw union crop / acquired scan|39.243%|31.684%|
|Mean hypothetical largest-only crop / acquired scan|25.986%|21.961%|
|Median relative box-volume reduction|28.510%|13.163%|
|Largest-only box identical to raw union|3/40|10/40|
|Raw boxes meeting **size only** ≤25%|2/40|15/40|
|Hypothetical largest-only boxes meeting **size only** ≤25%|22/40|31/40|
|Median largest-component / reference volume|16.015×|13.328×|

The last two size rows are not ROI passes: component-specific reference containment is unmeasured.
Existing raw 012 ROI screens remain 15/40 and its boxes retain ≥.995 reference in 39/40.
The 31 hypothetical small boxes cannot be reported as 31 successful localizations.

In 012, removing a median 0.606% of foreground changes 30/40 box extents. The largest improvement
is 75.21% less box volume in case 7839, despite keeping 97.10% of prediction voxels. Outlying regions
can control box faces with little volume. Conversely, 3115's largest component already controls
all six faces, so largest-only selection changes neither its box nor its existing containment failure.
Some cases have substantial competing regions: 3314, 4365 and 5396 keep only 57.10%, 68.52% and
55.29% of 012 foreground, respectively. A global largest-only rule is not demonstrably safe.

## Connected excess is independently established

From retained whole-mask true-positive counts, the largest component can contain at most that
many true-positive voxels. Thus at least max(0, largest size − whole-mask TP) of its voxels lie
outside the retained visible reference. The median lower bound on this excess fraction is 93.94%
for 010 and 92.69% for 012. This is a count-based bound relative to the annotated reference,
not component-overlap measurement, whole-organ completeness or an anatomical diagnosis.

The main component remains a median 13.33× reference volume in 012. Its median filled share of its
unmargined bounding box is 26.31%; a connected component need not be a compact anatomical region.
Component deletion can reduce distant extent, but the dominant foreground discrimination problem
persists. No new threshold, CE weight, support mask, component or distance rule was selected.

## Retained failures and geometry tradeoffs

|012 case / role|Largest foreground share|Raw→largest-only scan crop|Interpretation|
|---|---:|---:|---|
|3115 / validation|99.953%|28.929%→28.929%|All six union faces belong to the largest component; existing box coverage .990587 cannot improve through this deletion.|
|6186 / validation|98.976%|24.617%→14.538%|A smaller component controls the high face of axis 1 and another the low face of axis 2. Size improves; retained recall .747615 is already deficient.|
|6534 / validation|92.195%|19.358%→9.997%|Largest label is 2, not discovery label 1; surrounding regions determine several faces. Need actual overlap before deletion.|
|2727 / validation|99.376%|42.421%→40.463%|Tiny-reference excess remains; largest component alone is 4065.82× reference volume.|
|150 / training|89.705%|32.836%→15.015%|A smaller box does not recover the .463016 raw recall; largest-only recall could be worse.|
|756 / training|99.954%|22.207%→22.207%|Existing box coverage .975844 cannot improve by deletion.|
|6110 / training|72.901%|42.629%→15.471%|Raw recall 1.0, but reference allocation among components is unknown; do not assume the tiny pancreas is in the largest component.|
|6822 / training|76.913%|45.387%→15.654%|Existing box coverage .973284 cannot improve through a nested smaller box.|
|7604 / training|98.918%|26.839%→26.839%|Persistent .860597 box coverage and broad main region; no size improvement.|
|7684 / training|92.884%|42.500%→25.356%|Largest-only still exceeds the 25% size screen.|

Deleting components makes the margin-expanded box a subset of the original box. It cannot restore
reference already outside that original box; this monotonic conclusion requires no new reference
read. It also cannot increase pixel recall. The audit's count-only largest-component recall interval
is [max(0, TP − discarded voxels)/reference size, min(TP, largest size)/reference size]. Five 012 and
eight 010 validation cases have a zero lower bound. Even nonzero bounds are not measured recall.

## Verification and resources

All 92 masks and native rows agree with the pinned completed review/execution records. Shapes,
millimeter units, uint8 binary values, affines, foreground counts and reconstructed union boxes
match exactly; crop fractions agree within 1e-12. All requested members completed. A final check
rehashes 184 selected inputs and both audit source modules; masks/source remained unchanged.

1,789 native tests pass, including 26 new helper/runner checks and independent flood-fill oracles.
Two existing torch.jit warnings remain. Initial sandbox execution passed 1,787 but blocked two
existing `/bin/ps` supervisor tests; the complete native rerun passed all tests with process
inspection available. No dependency changes. Dense 96-million-voxel synthetic profile passed in
1.362 s at 0.563 GiB RSS, preserving dense failures rather than excluding them.

Real retained audit: 33.239 seconds including its preflight, peak RSS 1.464 GiB, CPU only. The 92
array payloads total 21,606,141 compressed bytes / 2,436,199,082 uint8 voxel bytes, within the exact
request and 1,200 s/8 GiB/50 MiB limits. These are input payload counts, not cumulative OS bytes
including hash verification. Original-array reads and model updates are zero. No keeper/model
restore is claimed for this diagnostic; raw retained masks were checked in place.

## Evidence and next steps

New local directory: `outputs/prowl/LOCALIZER-STRUCTURE-AUDIT-20261001`. It contains the frozen
request, 92 per-mask terminal records, full component tables/face controllers, summary and case
tables, dense profile, test outputs, final input checks and replayable summary script.

|Record|SHA-256|
|---|---|
|Exact request, consumed once|`f5d455d9eb514f213c11cb8be1be84a90c22e6d4a03870a6954bbcda58de2054`|
|Execution receipt|`b58ff84cab945fa1990d9e66d6b4efee62e9d1a09b2b73001057bafee5ac07a1`|
|Whole review receipt, 105 files / 3,046,235 bytes|`63fb49bb9c63e8ea8e0a4654c3ef9d4944cfcfeeeb26951cb2f0e6526e988046`|

Recommended next implementation: Phase A's separate Stage 2 purpose records and retained-metadata
candidate proposal in the [Stage 2 packet](STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md).
It spells out lesion-positive/verified-negative requirements, source ancestry, exact role/purpose
permissions, shared physical ROI/letterboxing, synthetic learning/recovery, real zero-update profile
and separate provided/predicted-region diagnostics. Planning is complete; no Stage 2 qualification,
cohort freeze or run has happened.

In parallel scope, review the [fresh component-coverage proposal](LOCALIZER-COMPONENT-COVERAGE-PROPOSAL-2026-10-01.md)
before any original-reference job. Largest-only is a diagnostic candidate; passing size is insufficient
for adoption. Continue improving localization with actual containment evidence while bringing lesion
segmentation into the development loop. Another long run or scalar-loss guess is not issued here.

Modified scientific code is isolated to a new structure helper/diagnostic and tests. Shared decision/
notebook/checkpoint navigation is updated; the prior 012 results document receives only numeric
spacing corrections. No sealed old artifact, retrieval file, protected cohort, model/loss consumer,
source dataset, Git publication or Claude dispatch changed.
