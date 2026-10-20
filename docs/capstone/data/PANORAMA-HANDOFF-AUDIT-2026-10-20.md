# PANORAMA handoff audit — October20

**Status:** Acquisition/transfer evidence recovered; integration acceptance remains unverified.
W03-01 stays open pending the data owner's implementation handback. No voxel or model work.

The older inventory's missing-data statements are historical. Four CT archives and the pinned
label archive are present under `/Volumes/PROWL-Data/PROWL/sources/panorama/`. Retained acquisition
logs report archive download checks; retained extraction finished September27 with `source_ready=false`
and `cohorts_reconciled=false`. These flags accurately distinguish acquisition from eligibility.

The October9 transfer result records4,480 files/195,692,251,008 bytes copied with source/destination
SHA256 agreement at transfer time. A fresh **path/size-only** reconciliation of all4,480 Mac files
against that ledger has zero mismatches. Names give2,238 CTs and2,238 labels, equal study-ID sets,
no duplicate IDs within either set,482 manual and1,756 automatic label files. This does not establish
patient disjointness, correct geometry, label values, present-day content hashes or training eligibility.
No large files were rehashed and no arrays/workbook content were reopened.

Evidence:

- `outputs/prowl/panorama-handoff-audit-20261020/receipt.json` — fresh metadata reconciliation.
- `outputs/prowl/panorama-quinn-transfer-20261009/result.json` and `files.jsonl` — retained transfer.
- Transfer ledger SHA256: `0d7e94e2fb2d130705f766416f840d06643eb29d2cb593057baac945516ce973`.
- `outputs/prowl/extraction-2026-09-22/panorama.jsonl` — completed extraction, no source admission.
- `outputs/prowl/inventory-2026-09-22/panorama-classes.md` — manual/automatic structural inventory.

## Required unresolved handoff

| Evidence | Current disposition |
| --- | --- |
| Acquisition, extraction and transport | Retained evidence recovered; current path/size presence verified |
| Publisher/workbook reconciliation and pinned source manifest | Historical planning evidence; current integration receipt needed |
| Per-structure mapping, annotation method and allowed uses | Approved design exists; execution/QC evidence needed |
| NIH/MSD exclusions, patient grouping and cross-source duplicate dispositions | No current handback found in reviewed Mac records |
| Native geometry/content/crop qualification and failures | Current producer audit needed |
| Frozen mixed-source smoke result and final eligibility manifest | No completion evidence found in reviewed Mac records |

Preserve approved semantics: non-PDAC is not generic-lesion negative; machine pancreas is not expert
ground truth; manual/automatic lesion methods remain separate; declared imports and unresolved
duplicates cannot silently enter an eligible pool. Acquisition completion cannot close W03-01.
The [prepared owner request](../retrieval/MODEL-AND-PANORAMA-HANDOFF-2026-10-20.md) asks only for
existing evidence or exact missing items. No training/data mutation or implied hours.
