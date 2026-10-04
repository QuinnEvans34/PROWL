# Stage 2 purpose and cohort contract slice

October 1, 2026 — D-315. Synthetic contract implementation complete; no real qualification,
cohort publication, source file inspection or training authorization.

## Separate dual-target permission

`segmenter_qualification_v1.py` supports exactly two new purposes:
`pancreas_lesion_segmenter_training` (protected train / training target) and
`pancreas_lesion_segmenter_validation` (protected validation / evaluation reference).
The policy binds CT, pancreas and lesion identity, both annotation IDs, source snapshot/version,
original role/protection group, subject/study and the union of applicable issues. Six exact reviewed
receipts cover geometry, mapping lineage, permitted use, source readiness, pancreas target and lesion
target. Every receipt binds the complete context, purpose and policy; held/excluded outcomes remain
records rather than being silently filtered.

The generic manifest and annotation formats already admit lesions. Their source-snapshot v2
inventory intentionally admits only CT/pancreas. Synthetic testing exposed that restriction, so
this slice leaves it unchanged and adds a paired `segmenter-lesion-inventory-v1` sidecar. A reviewed
sidecar pins the lesion file's exact bytes/hash/URI/root alias, study, source snapshot and source
version. It is supplied through the source-readiness receipt, not manufactured by the qualification
helper. This is separate evidence, not a claim that old snapshots verified lesion files.

Three new strict schemas describe qualification, cohort and paired lesion inventory records.
Existing source/manifest/annotation/localizer schemas are unchanged. No real manifest is migrated
or assigned the new policy here. Future real qualification must preserve predecessor annotations
and blocking issues through a separately reviewed successor/transition; this helper does not clear
or suppress old issues.

## Exact consistency rules

- CT spatial units must be positively resolved in millimeters. Target shape must match CT; flat,
  finite target affine values must match within 1e-5 absolute tolerance, zero relative tolerance.
  Target units may be mm or explicitly interpreted in the exactly matched mm CT grid, as in the
  existing source qualification rule. Unknown CT units remain unsupported; no header rewriting.
- CT/pancreas source inventory and the paired lesion sidecar must match exact annotation/file
  records. Decoder and approval bytes, audits, provenance and source-use decisions must match
  independently reviewed pins. Audit voxel counts must match the source grid.
- Approved semantic binary endpoints remain valid under D-259, including supported scaled storage.
  Canonical class mapping is pancreas 1, lesion 2, with lesion precedence. This module does not
  assemble arrays or choose a crop. Nonempty pancreas is needed for the proposed pancreas-region
  slice; noise, size, boundary contact and difficulty are not quality filters.
- A nonempty lesion audit supports a visible positive target only with matching explicit target
  identity and positive receipt. An empty lesion requires a case/context/purpose-bound reviewed
  negative reference standard and matching study status. An empty or missing mask alone never
  supplies negative supervision. Unknown targets are held when the check records a hold.
- Every applicable unresolved issue blocks except an information-only `DIFFICULTY_OBSERVATION`
  explicitly marked retain. A forged all-pass receipt cannot override such a hold. The helper
  checks consistency; a hash cannot establish that a reviewer or source assertion is truthful.

## Frozen-membership proposals and pure resolver

`segmenter_cohort_v1.py` accepts a fixed nonempty study list and exact requested count, one verified
matching-role original protection root and one selected purpose qualification per member. It never
refills a shortage. Membership order, qualifications, both annotations, target state, manifest and
parent identity determine the cohort content ID. Held/excluded qualifications cannot enter it.

The resolver requires an explicit optimizer/evaluator operation and rechecks the entire qualification
evidence and ancestry. Returned CT/pancreas/lesion descriptors retain purpose, protected role,
evidence domain, visible-reference scope, pancreas-only ROI source and lesion-over-pancreas precedence.
It opens no source files. Synthetic domains remain labeled synthetic and cannot be relabeled as
retained-source records. Pair validation enforces disjoint study/subject identities and CT content;
manifest validation also retains protection-group role constraints. Study-as-subject biological
uniqueness remains unverified, as in the original data records.

This is in-memory contract/resolution capability, not a disk registry, real cohort freeze, model
loader or permission to reuse localizer checkpoints for the segmenter. The future array consumer
must bind these descriptors to actual source bytes and its own read/resource request.

## Verification

47 new native tests cover positives, explicit negatives, unknown empties, inherited holds/exclusion,
difficulty retention, wrong policies/purposes/check contexts, missing evidence/pins, stale identities,
wrong mappings/units, malformed/broadcast geometry, source-sidecar substitution, changed annotations,
wrong-role resolution, fixed-membership shortages and deterministic metadata selection. Independent
expected statuses and adversarial substitutions govern; no real arrays or permissions are used.

Full native suite: **1,836 passes**, two existing torch.jit warnings. The existing supervisor tests
require process inspection, so the native run used the established test permission for `/bin/ps`.
No dependencies or old localizer modules changed. Four shared source modules and two old schemas
match D-294's retained code hashes exactly. Early synthetic attempts are preserved: first caught
the snapshot's two-kind restriction; second caught two fixture probes that needed to attack the
new sidecar and missing annotation through the production API. These were corrected before the
passing suite. Nothing was weakened to pass the fixtures.

Retained metadata evidence and the proposed 8/4 slice are documented in the
[results handback](../operations/STAGE2-METADATA-RESULTS-2026-10-01.md).
