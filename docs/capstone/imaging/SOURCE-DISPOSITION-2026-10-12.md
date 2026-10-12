# W02-02 imaging source disposition

October 12, 2026. Metadata review delivered; seven unit failures and upstream anatomy/annotation questions remain open. No source, model, prediction or cohort membership changed.

## Findings

The acquired PanTS `metadata.xlsx` identifies **PanTS_00001389 as `ct angiography head`**. This corroborates the earlier visual concern in the [October 9 investigation](AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md). It is unsuitable as our abdominal viewer demonstration. This does not establish why its source pancreas annotation contains 74 voxels or prove an extraction/annotation defect. Keep its existing output and failure evidence in the fixed-cohort report.

All seven unknown-unit CTs have matching shapes and numeric voxel spacing in the source workbook. The column is named `spacing`, without a unit declaration. Matching values establish consistency, not millimeters; none qualifies for an override yet.

| Case | Source spacing, units unspecified | Disposition |
|---|---|---|
| PanTS_00001823 | 1.5, 1.5, 1.5 | Source units unresolved |
| PanTS_00002935 | 1.5, 1.5, 1.5 | Source units unresolved |
| PanTS_00005370 | 0.703125, 0.703125, 5 | Source units unresolved |
| PanTS_00005780 | 0.83984375, 0.83984375, 5 | Source units unresolved |
| PanTS_00006011 | 1.5, 1.5, 1.5 | Source units unresolved |
| PanTS_00006115 | 1.5, 1.5, 1.5 | Source units unresolved |
| PanTS_00006901 | 5, 0.75, 0.75 | Source units unresolved |

The rotated final case uses affine column lengths for spacing comparison, not diagonal elements. Existing `src/inference/spatial_units.py` requires a CT-hash-bound review based on CT acquisition metadata or source dataset documentation. Mask units, plausible spacing and population descriptions do not supply the missing declaration.

## Evidence and verification

Private evidence: `outputs/prowl/imaging-disposition-20261012/disposition.json` and reproducible `audit.py`. The ledger records eight source row numbers, selected geometry/study-type fields, inherited CT hashes, workbook hash, and retained plan/header-audit hashes. The script maps sparse XLSX cells by column, verifies eight unique selected IDs, checks seven shapes/spacings, and checks the head-study designation. All passed. Demographics and structured report text are not copied into the ledger.

Source workbook: `/Volumes/PROWL-Data/PROWL/sources/pants/acquisition-3b1cd6110811/metadata.xlsx`. See the [release linkage review](../data/PANTS-SOURCE-USE-REVIEW-2026-09-28.md) for provenance limits. This pass read workbook/retained metadata only, with no CT/mask arrays, weights or test payloads. CT hashes are inherited evidence, not freshly recomputed payload verification. No application code changed; no broad test suite rerun.

## Next actions

1. **Units:** obtain acquisition metadata or a publisher unit definition applicable to this release and the seven CTs. Review against each pinned CT before a targeted rerun. Preserve original failures and all 75 requested cases.
2. **Anatomy:** clarify upstream provenance of PanTS_00001389 and its pancreas annotation. No publisher contact was made. This finding does not qualify an automated anatomy detector or justify a size-based exclusion or cohort revision.
3. **Viewer W02-04:** inventory saved PanTS_00001070 next, then verify package identities and geometry. Label predictions as unvalidated development outputs. This adaptively selected abdominal example does not establish representative performance.
4. **Model handoff:** no new candidate supplied; W02-03 remains conditional, with training owned by the other laptop/chat.

Baseline remains **68 outputs / 75 requested, seven explicit failures**. W02-02 stays open for source dependencies; its bounded Week 2 disposition is delivered. Independent viewer work can proceed without declaring these failures repaired.
