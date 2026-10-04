# Segmenter purpose dispositions and annotation history — D-319

October 1, 2026. **Twelve paired lesion inventories and a separate purpose ledger are published locally and independently replayed. Six training references and one development-validation reference qualify; five cases remain held.** No cohort, source-array read, model operation or training launch occurred.

## Exact outcomes

|Outcome|Protected train|Protected development validation|
|---|---|---|
|Qualified visible positive reference|3, 26, 2973, 2232, 6238, 5821|2514|
|Held: empty lesion is unknown|6110, 4965|2727, 7265|
|Held: source annotation relationship unresolved|—|5641|

All twelve candidates remain in the ledger. Qualification grants only the exact `pancreas_lesion_segmenter_training`/`training_target` or `pancreas_lesion_segmenter_validation`/`evaluation_reference` purpose within the existing private noncommercial academic project. The [narrow use assessment](../data/SEGMENTER-PURPOSE-USE-2026-10-01.md) preserves the source-asserted publisher protocol, attribution, staged integrity and existing release restrictions. It does not certify per-voxel correctness, completeness, biological subject uniqueness, clinical contour acceptance or public model/data release.

The retained source assessment supports `human_manual` lesion annotation at publisher-protocol scope. It does not explain case5641's completely disjoint masks. That case therefore stays held; no publisher convention, corruption or incorrect label is inferred. Four empty references remain unknown, without negative supervision. The supported pool has one positive validation case and no verified negatives: it is suitable for engineering preparation, not a stable generalization or lesion-detection estimate.

Difficult positive cases remain included:2973's single7.5mm slice,6238's native source-boundary contact, and measured outside-pancreas pixels in26/2973/2232/6238/5821. No clipping, lesion-driven ROI repair, replacement or quality filtering. Shared target fidelity remains the following geometry phase, not an accomplishment of this metadata slice.

## Preserved history and separate transition

The successor manifest preserves **all184 predecessor annotations, all247 predecessor issues, every original pancreas annotation, all179 studies, subjects, source snapshots and9,901 protected membership records**. Twelve new lesion records bring annotation count to196; thirteen new information/hold issues bring the total to260. The old localizer manifest and113/40 cohorts are unchanged, as are153 localizer members/23holds and original7,200/1,800/901 roles.

Cases3/26 retain their quarantined original lesion records and pending-use issues verbatim. Distinct successors bind the same exact raw lesion bytes to current encoding audits, approved mapping, source-protocol evidence and the new narrow use decision. The transition certificate explicitly records which generic pending-use issue is addressed for each successor; it does not mutate or erase the original issue. The other ten cases have no invented lesion predecessors. Specific or unknown inherited blocking issues cannot be silently left behind when creating a successor.

The new pure transition checker verifies append-only annotation/issue history, fixed source/protection/subject records, exactly reviewed study annotation/lesion-status additions, role/purpose, paired inventory and all qualification dependencies. The existing pancreas-localizer transition and all old consumers/schemas remain unchanged. All ten D-315 shared implementation/schema pins were independently rechecked.

Each case has six context-bound receipts: geometry, mapping lineage, permitted use, source readiness, pancreas target and lesion target. Exact CT/pancreas inventory remains in the unchanged source snapshot; the separate lesion sidecar binds current compressed URI/hash/bytes and source version. Current source facts and reviews are pinned from D-316–D-318. Unknown label units are interpreted only in the exactly aligned qualified mm CT context; no headers or masks are rewritten. Empty and relationship-held cases have held lesion-target receipts and no new lesion allowed uses.

## Implementation and tests

New files: `src/data/segmenter_dispositions_v1.py`, `src/data/segmenter_transition_v1.py`, `scripts/diagnostics/publish_segmenter_dispositions.py` and `tests/test_segmenter_dispositions.py`.

**25 new checks;1,956 native tests pass**, two existing torch.jit warnings,67.43seconds. Both roles, new/retained predecessors, empty/relationship holds, specific inherited blockers, lost/changed issues or annotations, wrong sources/subjects/roles, unrelated study edits, raw-byte changes, extra annotations, omitted qualifications, sidecar substitutions, forged checks, review omissions, altered history links/target claims and certificate changes are exercised. Adversarial probes refresh applicable identities to reach semantic guards where structurally valid. Targeted65 tests passed in3.41seconds; strengthened transition25 checks passed in1.73seconds.

Two initial fixture failures are preserved: the older fixture lacked evaluation-reference permission for its validation pancreas; the next fixture reused the same provenance reference twice. The fixture was made role-correct and given distinct invented use/provenance evidence. Production permission or uniqueness checks were not weakened. All attempts are retained in the sealed review.

## Publication, replay and resource evidence

|Pin|SHA-256|
|---|---|
|Prepared publication plan|`a259c6b965dd7da4fb9eac2cd5bb7277af271966917d8f6f784f0e0f356dfabd`|
|Self-contained inputs|`9f45cdf776a7bdbdd2441e61c7b94a25cd461b3435fe4b6b4d53b8ae31920401`|
|Successor manifest|`31c7239dab12f7e2072897426fd696c9cfafe214ad02682faefc1ed0fa462221`|
|Transition certificate|`62447d63b981fd6f7fecd1c800f11a2d84ee3dbd66b6e41e180d3938dc3c9eb4`|
|Complete purpose package|`7334b71e58eaed425ae4d73c2feffc35a7d9f8d9d3af52e90ae5869fdb17f442`|
|Sealed independent review|`81ee950a65f79219399e1e98a63465f131884b8d22100aa734c1eebc54bb0dc5`|

Local purpose package: `outputs/prowl/SEGMENTER-DISPOSITIONS-20261001`, four covered members/26,756,709bytes, completion receipt written last with no overwrite. Candidate and exact input/derived/code/runtime/plan pins remain preserved separately. This is a local versioned metadata publication; no registered executable cohort or external keeper publication is claimed.

Publication rederived and checked all records, reporting58.47seconds and1,029,259,264B process peakRSS (0.959GiB), below1800seconds/2GiB/96MiB metadata ceilings. The `/usr/bin/time -lp` wrapper then failed a supplementary `kern.clockrate` sysctl measurement in the sandbox. The worker had completed and written its valid receipt; publication was not repeated. This telemetry limitation is retained in the log and does not replace successful resolution evidence.

Fresh-process resolution independently verified the supplied completion/input/manifest pins, rebuilt all derived bytes, revalidated the twelve purpose qualifications and transition, and matched the complete payload: exit0,57.591seconds,1,028,456,448B peakRSS (0.958GiB). A separate case-by-case oracle checked expected outcomes, exact current lesion identities/counts, both targets' context receipts, sidecars, unchanged pancreas records, source/role ancestry, prior annotations/issues and all old shared code/schema pins. No raw source files were reopened.

Sealed review: `outputs/prowl/SEGMENTER-DISPOSITION-REVIEW-20261001`,19 covered members/245,703bytes. It contains code/test/use/plan snapshots, every test/preparation/publication/replay log and the independent verifier/report. No source array or model data is included.

## Next

[Freeze the supported6/1 role cohorts](SEGMENTER-COHORT-FREEZE-PACKET-2026-10-01.md) through a bounded registered artifact adapter that requires the D-319 transition and completion pins, tests held/wrong-role rejection and independently resolves both children. Retain all twelve candidates and five holds without refill. Then qualify shared pancreas-only ROI/three-class geometry and target fidelity, followed by synthetic learning/checkpoint recovery, zero-update MPS/resource profiling and a separately approved exact scratch training request. No cohort or training request is pending from D-319.
