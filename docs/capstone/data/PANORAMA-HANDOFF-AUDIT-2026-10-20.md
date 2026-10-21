# PANORAMA handoff audit — October20

**Status, corrected October21:** The earlier exploratory integration and controlled training
comparison are complete within their documented scope. The training owner confirmed the completed
24,000-update mixed run. A port to the newer physical-detail pipeline remains unqualified but is
separate work; it is not a reason to treat the original integration as unfinished. Historical
October20 findings below remain preserved and are superseded where the correction says so.

## October21 owner clarification

After Quinton authorized a clarification request, *Plan capstone experiment workflow* reported:

- Completed `pants_plus_expert_panorama_dicefocal_24k_20261012`, MLflow
  `c038332411df4f38bf52d650810c77c0`: 19,055 PanTS plus 4,945 PANORAMA updates, totaling 24,000.
- 1,333 PanTS plus 345 manual-PDAC PANORAMA studies/344 source subjects; 70 PanTS development cases
  (36 positive, 34 annotation-empty). Existing exclusions and narrow exploratory admission remain.
- `segmenter-mixed-inputs-1`, `segmenter-geometry-v2`, `panorama-union-geometry-1` /
  `panorama-union-transform-1`: physical union crop/resampling, then uniform resize/pad to 144³.
- Matched selected PanTS-only14k versus mixed8k: lesion Dice .405092 versus .371897;
  any-overlap 34/36 versus 33/36; empty-case false positives 32/34 versus 34/34.
  Delta −.033195, reported interval [−.102249,+.028561]. Practical intervention rejected;
  null not rejected; mixed model not promoted. The proposal did not guarantee improvement.

Owner source: Windows `docs/capstone/operations/PANORAMA-POSITIVE-RESULTS-20261013.md` and
`E:/PROWL/readiness/panorama-positive-review-20261013-a01/results.json`.
Reported result SHA256 `ddecd2cc37307b3bb85e92b4b6080e82cefcf45dcf87d99fde85223d3f861c15`;
reported run-journal SHA256 `4abe5ee0104ce9615d564c7913e330510fb016cf64d50c35745877918f9e601c`.
These new facts are attributed to the training owner's response, not a fresh local rehash of those
Windows files. The October20 transferred evidence and its local checks remain independently retained.

The newer physical-detail/provided-pancreas-region runs are PanTS-only. Porting PANORAMA there
requires its own justification and qualification. Do not rerun the completed experiment merely to
close a tracking discrepancy. Undeclared overlap, silver-standard pancreas support, limited visual
review and unknown SuPreM membership remain explicit limitations; no broad clean-benchmark claim.

## Historical October20 audit

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

## Earlier Mac-only findings — superseded by the received handoff below

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

## Received owner evidence and local reconciliation

Quinton authorized the combined evidence-only request. *Plan capstone experiment workflow* returned
`w03-panorama-retained-evidence-20261020.json`,154,069 original bytes, received in18 numbered chunks
and verified as SHA256 `91580c4d3aac0b385a00237a071a2b13af5f935192998603176303e826cd45c4`.
It is retained in `outputs/prowl/model-panorama-handoff-20261020/`. This supersedes “missing handback”
above; it does not turn old-pipeline evidence into current-pipeline acceptance.

| Required evidence | Received disposition |
| --- | --- |
| Mapping and uses | Raw1→lesion2; raw4→pancreas1; other codes→background. Physical union crop +10mm, linear CT/nearest-label resampling into resized/padded144cube. Manual PDAC lesions only in primary arm; machine pancreas is silver-standard crop/training support, not expert evaluation truth. |
| Eligibility |345 studies/344 source subjects. Experiment-specific accepted development-use review authorizes this narrow arm; immutable source-catalog fields remain unassigned, not blanket admission. |
| Exclusions and separation |194MSD+80NIH declared imports excluded. Five uncertain PanTS development cases held out, not moved into training. Repeated studies grouped by source subject; these are not proven unique patients across datasets. Non-PDAC is not generic-lesion negative, automatic lesions excluded from primary arm. |
| Label/header qualification |2238 accounted:1905 technical passes,274 declared-import exclusions,59 technical holds. Technical pass alone did not admit training. |
| CT union qualification |2238 accounted:1904 passes,333 prior exclusions/holds,1 additional component-loss hold. Study100965_00001 lost component3 and is not among345 admitted studies. |
| Visual review |Five selected expert-case previews, engineering only. Earlier generic30-case review was not completed; no whole-cohort/radiologist certification. |
| Production cache/binding |345/345 new cache members checked;1678train=1333PanTS+345PANORAMA;70PanTSdevelopment=36positive+34empty. PanTS original control unchanged. |
| Production smoke |Five optimizer updates using two unique PanTS and two unique PANORAMA members; two PanTS development evaluations. Cold exact restore and one repeated update agree within declared tolerance, max difference7.45e-9. Workers reaped. This is an earlier completed smoke, not new work today or accuracy evidence. |

The local reconciliation script verifies received membership uniqueness/group counts, exclusion
nonintersection, audit denominators, held-case absence, cache count and mixed-source smoke sequence,
as well as the independent model comparison arithmetic. Source IDs/per-case hashes remain in ignored
receipts. The public aggregate is `configs/evidence/evaluation/model-panorama-reconciliation-20261020.json`.
These checks establish receipt integrity and internal consistency; they do not freshly hash the
Windows original files, inspect arrays, or independently certify their reported semantics.

Key producing bindings from the receipt:

- Selection: `71d169df76c26d42632c061d120f63e12f153de9d7cbfbbb46c060900b4df032`.
- Manifest: `cf6d72f050af5dcb888d64c7e4250a857624ac98b1d3c11407caf20b56b2c1eb`.
- Mixed-input adapter: `a4ab6269684b3a43fa6418e823c248caf7483bc93495b38bdcd87ec787e1c072`.
- PANORAMA geometry: `e7bd3bd6a77da1cefdef2bf5a0140986091722ed85a34f8ff61093974187e844`.

## Exact remaining scope and owner

The current physical-window producer needs its own PANORAMA mapping/support/patient-role binding,
whole-target coverage/fidelity audit, explicit exclusions and mixed-source smoke before current
integration can be claimed. Data/training owner owns that execution; this RAG chat records its
handoff and admission implications. Reuse the345-study manifest only after revalidating the new
pipeline's requirements. Do not redownload data or replay the old smoke to fill this gap.

Undeclared cross-source overlap remains unruled-out;118 ambiguous training records carry redundancy
risk,80 ambiguous original test records remain protected, and SuPreM source membership is unknown.
Component survival alone does not prove full-field lesion preservation or boundary/detail fidelity.
The old narrow exploratory acceptance and its limits are preserved; no current-run changes, new
training eligibility, clean-benchmark claim or whole-organ measurement qualification are inferred.

The requested W03-01 evidence handoff is resolved. The board now records both the completed earlier
integration and the specific current-pipeline dependency instead of saying no integration evidence
exists. This checkpoint does not declare the entire proposal milestone complete.
