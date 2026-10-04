# Localization progression — result and next implementation boundary

D-280 work defines stronger diagnostic targets, measures CAP-EXP-004's actual region usefulness,
and prepares varied train/validation candidates. **No new training was needed for this investigation.**
The evidence supports advancing cohort work rather than repeatedly tightening the same two masks.
The new candidate cohorts are **not yet qualified or executable**.

## Localizer result

| Training case | Raw mask Dice | Predicted/reference mask volume | Predicted box coverage | Box/scan volume | Box dimensions |
|---|---:|---:|---:|---:|---|
| 3 | 0.439224 | 3.55× | 100% | 6.79% | 162×105×138 mm |
| 26 | 0.452774 | 3.42× | 100% | 5.38% | 165×102×120 mm |

Both masks have exactly one 6-connected component, so largest-component selection changes nothing.
The excess foreground is part of the main connected prediction; removing small disconnected islands
cannot fix it. Both masks fail the new per-case fit screen (recall >=0.98, Dice >=0.65, volume ratio
<=2), while both boxes pass the separate provisional pre-mapping screen (coverage >=0.995, fraction
<=0.25). The frozen diagnostic requests 10 mm margins; rounding outward on the 3 mm grid realizes
12 mm on each face. Neither box touches a scan boundary.

The localizer's purpose is to supply a manageable region, not the final pancreas contour. These
results justify testing broader localization before making tighter two-case mask fit a prerequisite.
They do not select a production ROI policy: training cases were reused, no lesion reference was
read, and final Stage 2 mapping/spacing/containment remains untested. The targets in
[LOCALIZATION-TARGET](LOCALIZATION-TARGET-2026-09-29.md) are Codex's provisional engineering screens,
not permanent clinical criteria or approvals attributed to Quinton.

Read-only diagnostic: `outputs/prowl/localizer-roi-abf86a2a-3d02-4393-993a-c68b0a5b6bc3`.
Receipt `c8ca6ce913f25a50a1104fcc1e6f1eaca8a6e695636492f3ddd9d335a49670f4`.
Two full-volume forwards, zero optimizer updates; exact terminal Dice/counts reproduced, model digest
and step unchanged. Original training source and receipt checked; diagnostic source captured separately.
45.19 s supervised, peak sampled RSS 2,088,910,848 bytes, no cap stop. Original exports unchanged.

## Candidate expansion and header findings

Selected **16 training candidates**, retaining cases 3/26, and **12 disjoint development-validation
candidates** from the immutable original splits. Phase × slice-spacing strata include missing
metadata, with deterministic rare-first round-robin/hash ordering. This deliberately varied sample
is not prevalence representative. No model score, tumor field or annotation quality entered selection.

The initial eight-validation selection omitted three thin-slice strata. Its package is preserved;
only the candidate budget changed to twelve, before source inspection or model evaluation. The final
selection covers every available stratum in each role. Held candidates cannot be silently replaced.

Current candidate package: `outputs/prowl/localizer-candidates-f1f88917-7aa0-4cd5-a4e7-e8a84897421c`.
Receipt `3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1`.
Earlier 16/8 selection receipt `b183d9fa98be1c9ca0115cc4ffd22789488d3a433c6efb7a1c942af719a66f41`.

Header package: `outputs/prowl/localizer-candidate-headers-1a1836b3-7ab0-4952-9383-fdbcf9c21984`.
Receipt `950a113e6d18d795b90fe1bce7f68555a5e302b48e88de8b97b8651b9e4e73ad`.
All 56 inventory-linked files read under mount/identity checks; **229,376 compressed bytes**, exactly
348 decompressed header bytes/file, zero arrays decoded. 8.22 s; peak RSS 55,984,128 bytes.
All receipt members rehashed. Header geometry agrees within each CT/pancreas pair.

There are 29 unknown-unit headers and 27 declaring mm. For 27 pairs the CT header declares mm;
validation candidate **PanTS_00006350** has unknown units in both. The generic header flag
`physical_units_need_evidence` appears on all pairs because it detects any undeclared header. This
is not a new revocation of the existing two cases' reviewed unit interpretation. For new cases,
paired geometry/declared CT units can support a documented assessment alongside full integrity
and alignment evidence; do not blindly assign units. Case 6350 needs separate evidence and remains
in the candidate list. Header agreement does not prove anatomical alignment, nonempty target,
strict-binary decoding, gzip integrity or permission for a new purpose.

Selected files total 693,588,981 compressed bytes and about 1,781,724,105 nominal decoded array bytes
according to headers. Largest CT: 55,808,000 voxels. These numbers support a bounded sequential full
content job, not whole-dataset enumeration. See the [next packet](../data/LOCALIZER-COHORT-EXPANSION-PACKET-2026-09-29.md).

## Implementation and verification

New modules: `src/training/localizer_roi.py` and `src/data/localizer_candidates.py`.
New diagnostic scripts: `localizer_roi_check.py` and `localizer_candidate_headers.py` under
`scripts/diagnostics/`. New regression files: `tests/test_localizer_roi.py` and
`tests/test_localizer_candidates.py`. Native suite: **1,107 passed**, two existing upstream warnings.
`git diff --check` passes. No dependencies, old objective/checkpoint bytes, original memberships,
Claude files, global source activation or Git publication changed.

The first restricted full-suite attempt failed only where two existing supervisor tests invoke
`/bin/ps`; native execution passed. The header-reader test exposed Python gzip buffering beyond
the intended cap; a max-output streaming zlib decoder replaced that path before source execution.
The bounded reader, geometry/margin/empty/component cases, selection determinism/role separation,
and refusal of changed evidence all have passing tests.

## Next work

Implement the versioned validation-reference qualification and role-safe loader boundary, then run
the exact candidate content/alignment job and publish only supported role-specific cohorts. The
current policy and executable v2 cohort are training-only, and their fixed two-case history cannot
be applied to the new cases by changing constants. This is the remaining implementation boundary,
not a request to hand-pick easier validation scans. Broader training/evaluation follows that work.

Correction during D-281 review: the earlier prose reversed the unit-declaring file. All 28 mask
headers have unknown units; 27 CT headers declare mm. The pinned raw header evidence was unchanged.
