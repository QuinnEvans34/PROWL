# Step 1 handback: synthetic qualification and protected cohorts

**Date:** September 28, 2026. **Status:** bounded in-memory Step 1 implemented and natively tested.
Quinton requested starting the four-step sequence after approving D-266–D-268 and discussing synthetic
checks. This is not production cohort publication, source activation, eligibility promotion or training.

## What works

- Source snapshot v2 distinguishes complete accounting from present/hashed payload coverage. Explicit
  missing/unextracted rows remain visible; incorrect assurance totals and changed identities fail.
- Manifest v3 preserves the entire declared protection universe, including held cases and issues,
  while permitting only a subset to have full study/annotation evidence. Real migration mode requires
  all three exact approved base-file bytes and all original memberships; fixture mode is labeled.
- Qualification requires all five independently reviewed, exact-dependency check receipts: source
  readiness, geometry, target, permitted use and mapping lineage. It also checks existing annotation
  v2 permission/provenance, D-259 lineage, actual inventory references and initial-smoke foreground.
- Applicable issues are discovered across source/subject/study/annotation, not accepted as a caller's
  shortened list. Unknown issues block. The only information-only nonblocking rule in this first
  version is `DIFFICULTY_OBSERVATION` with information severity and retain disposition.
- Protection-only cohort parents retain every original member for their role. Executable children
  require positive qualification, exact parent/manifest/target hashes and full checked ancestry.
  Wrong roles, held cases, omitted protected members, changed inputs and silent shortages fail.
- The pure consumer returns copied validated member descriptions only. It cannot load arrays or
  publish files. Cohort state is explicitly `validated_in_memory`, not `frozen`.

Native focused command from the packet: **67 passed in 1.43s**.
Full command: **880 passed in 7.44s**, two existing upstream torch.jit deprecation warnings.
Tests include altered receipts/pins, omitted or unsupported issues, wrong targets, unsupported
mapping, singular geometry, mismatched voxel counts, exact-image duplicate candidates, ancestor
changes, changed membership and difficult-but-qualified cases. These are injected invalid fixtures,
not a claim of a mutation-testing campaign or real-data performance validation.

## Files and compatibility

New schemas: `source-snapshot-v2`, `manifest-v3`, `purpose-qualification`, `cohort-v2`,
`cohort-member-v2` under `docs/capstone/contracts/`.
New modules: `src/data/source_inventory_records.py`, `manifest_records_v3.py`,
`purpose_qualification.py`, `cohort_records.py`.
Tests: four packet test files plus shared `tests/qualification_fixtures.py`.

Old schema files, original manifest assemblers, binary policy, denial helper and historical source
records are unchanged. No automatic version migration. Unknown schema versions are rejected.

Implementation refinements from the draft packet:

1. The bounded new manifest embeds record collections in one canonical object; publication/chunking
   is deferred. Qualification records are separate, bound to exact source/subject/study/annotation/
   issue hashes and the policy; cohorts reference them explicitly. This avoids circular identities
   and lets independent qualification assessments exist without editing the source accounting record.
2. Protection-only roots represent the fixed split membership directly. The first executable builder
   supports one parent and exact fixed membership only; seeded sampling is not implemented or implied.
3. No generic resolution framework: current supersession/resolution claims are rejected. A future
   evidence-backed resolution path must be separately specified and tested before a held case can
   qualify. Cases 2/266 and case 78 retain their existing dispositions.
4. No filesystem registry, COMPLETE marker, locks or resume implementation is introduced. Step 4
   must add these under the shared Plan 04/10 prerequisites before any real consumer is enabled.

## Trust boundary and scientific limits

Builders/validators cannot establish that an external reviewer or source evidence is truthful.
Independent manifest, qualification and evidence pins must come from a reviewed authority, never
be copied from untrusted proposed records. The synthetic receipts demonstrate binding and enforcement;
real source-readiness/geometry/provenance receipts do not exist merely because fixture receipts pass.
This is not a new way to bypass G1 or treat a partial snapshot as ready for training.

The first policy is specific to pancreas-present localizer learning. Its foreground requirement is
not a general exclusion of empty/limited-coverage cases. No field selects by model Dice or visual ease.
Exact hash collisions are blocked when visible in the supplied manifest; this is not full image
fingerprinting or proof of biological uniqueness. Difficulty descriptors are not a sampling engine.

## Retained evidence rechecked for Step 2

All three original split byte hashes/counts passed; combined role assignments remain disjoint and
cover 9,901 study identities. The existing purpose-disposition package passed **55 file hashes** and
**five exact v2 manifest output replays**. Its ten annotations remain quarantined with zero eligibility.
No source drive was read or written during these checks.

[Source-verification scope JSON](SOURCE-VERIFICATION-SCOPE-2026-09-28.json) pins the actual local
controls/receipts and nine training archive identities. Historical expanded training CT payload is
317,614,413,856 bytes (~296 GiB), illustrating why full content verification needs a measured budget.
Historical extraction rate is not a forecast for the next job. Current mount state was not checked.

Step 2 is **prepared from retained controls, not execution-ready**. Remaining items: verified live
root binding, exact per-file inventory, review of required integrity coverage, measured read budget
and positive source/annotation-use evidence. Steps 3/4 have not started; no real candidate selected.

Next action: bounded metadata-only source preflight/inventory preparation, then finalize the actual
content-read and candidate-qualification job. Do not perform a ~318 GB read under an unmeasured budget.
