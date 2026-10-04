# Plan 07 S1 storage prerequisite — exact setup proposal

**Status:** prepared for Quinton's decision; not dispatched or implemented. Codex owns this
Plan 10 slice. It grants no sizing run, download, signature, source promotion or database access.
Imaging R-01 takes priority; no accelerator job or bulk storage operation belongs to this packet.

Authority: [Claude handoff](../retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-03.md), L2, and
[ACQUISITION-PLAN](../retrieval/planning/ACQUISITION-PLAN.md), Run S prerequisites S1.
Acquisition-plan bytes are pinned at
`a2be620c6b03373bc6a84b6cd88bf4f2177313bddc1992da7f3991ca713fc826`.
Run S's exact governing requirements are reproduced in the [S2 draft](CLAUDE-PLAN07-S2-PACKET-DRAFT-2026-10-03.md);
the proposed storage capability below does not replace or weaken them.

## Observed state, read-only

Existing `configs/local/roots.yaml` SHA-256:
`46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788`.
It remains setup-only with `scientific_runs_enabled: false`. Neither a literature source nor DB
alias is enabled. No registry bytes were changed.

| Binding | Existing value / observation |
|---|---|
| Failure domain | `external_primary` |
| Registered mount | `/Volumes/PROWL-Data` |
| Registered UUID | `22750B93-2F3F-499D-87F5-902981BFAB59` |
| Filesystem | APFS |
| Scratch root | `/Volumes/PROWL-Data/PROWL/scratch`; exists, not a symlink |
| Artifacts root | `/Volumes/PROWL-Data/PROWL/artifacts`; exists, not a symlink |
| Requested scratch child | `/Volumes/PROWL-Data/PROWL/scratch/literature`; absent |
| Requested receipt child | `/Volumes/PROWL-Data/PROWL/artifacts/literature/receipts`; absent |

A native read-only `diskutil info -plist /Volumes/PROWL-Data` confirmed matching VolumeUUID,
MountPoint, `FilesystemType: apfs` and `WritableVolume: true`. The initial sandbox call could not
access DiskManagement; the native read succeeded. This is an observation, not S1 acceptance or the
capacity reading required at signing (S3). APFS container capacity and the plist's zero-valued
`FreeSpace` field must not be confused with usable application free space; use `statvfs.f_bavail`
and the recorded Plan 10 headroom rule at each required check.

## Exact proposed authorization

Quinton can approve **S1 implementation and bounded setup only**, or defer it. Approval would permit
the code/test allowlist below, creation of the two requested child areas and their necessary
`artifacts/literature` parent, and activation of one capability-scoped literature writer. It would
not authorize arbitrary writes under the existing aliases or change their global access state.

The setup probe is proposed at at most 1 MiB of invented content plus bounded receipts, preserved
without deletion. Run S's future scratch allowance is 40 GiB, not permission to allocate it during
setup. Proposed receipt/fallback reserves are 64 MiB each; these are storage-budget proposals to
review, not amendments to Run S's transfer or parser limits. Any actual setup allowance must be
recorded before external writes.

The fallback required by Run S must also have an approved literal internal-disk location outside
Git and scratch. Proposed location for review:
`/Users/quintonevans/PROWL-Literature-Receipts/`. It is not created or registered here and is not
charged to or substituted for the shared checkpoint-backup allocation. Quinton may instead name
another suitable internal path. Settle its scope before enabling an executable writer; the signed
Run S copy must contain the final literal path. No silent fallback to `/tmp` or the checkout.

## Implementation and setup order, after approval

1. Recheck checkout, current file ownership, registry hash/schema, root roles, mounted UUID,
   filesystem, actual mount and device identity. Compare against the approved setup capability.
   Registry drift requires a new review; do not normalize it away.
2. Implement a separate `literature_storage_v1` adapter against the existing registry and a pinned
   capability. Keep the registry, cohort consumers, imaging consumers and source aliases unchanged.
   The capability identifies approval, registry hash, expected UUID/mount, allowed relative areas,
   writer identity, exclusive lock, byte ceilings and free-space floor. Missing approval denies access.
3. Verify every parent component using descriptor-based no-follow opens. Refuse symlink traversal,
   escaping paths, aliases with the wrong role, nested/overlapping source roots or a mount whose
   name matches but UUID does not. Bind open directories to the actual registered mount/device;
   a missing external mount must never resolve to an ordinary internal `/Volumes/...` directory.
4. After invented tests pass, create only `scratch/literature`, `artifacts/literature` and
   `artifacts/literature/receipts` beneath the verified root descriptors, plus the separately
   approved internal fallback area. Use exclusive/safe creation and preserve existing content.
   Flush new files and directory metadata. No chmod, relocation, source activation or deletion.
5. Enable exactly one capability-scoped writer: per-run scratch children are created exclusively;
   journal creation is exclusive; subsequent journal events append only. It cannot publish,
   build a final snapshot, populate a DB, create corpus artifacts or write imaging areas. Acquire
   a single-writer lock; age alone never authorizes taking over another writer.
6. Check UUID/mount, registry pin and available space at start, before each file and every 60 s
   during a later authorized run. Require free bytes at least headroom floor plus remaining scratch
   cap; start requires floor plus 40 GiB. Headroom is `max(100 GiB, 10% of usable capacity)`.
   Checks are supplemental to counters enforced while streaming, never replacements for them.
   Recheck identity at write boundaries and keep path/descriptor guards active between checks.
7. A volume disappearance, identity mismatch, unwritable primary or failed check stops work.
   Use the approved internal fallback only for remaining journal events and terminal failure;
   it never receives downloads/parser output and never masks the failure as `completed`.
8. Run a bounded native invented filesystem probe only when imaging is idle. Verify exclusive
   create, append/reopen/read-back, fsync, lock contention and stop/fallback behavior without
   disconnecting a real drive. Preserve its receipts and failures. Record code/capability hashes,
   actual path/UUID observations and test results in a Codex-owned S1 handback.
9. Stop. S1 acceptance makes storage available for a separately authorized tool/job; S2 tests,
   fresh signing-time capacity reading S3 and Quinton's frozen-copy signature S4 still precede Run S.

## Proposed write allowlist

Implementation authority is needed before creating these code files:

- `src/operations/literature_storage_v1.py`
- `scripts/diagnostics/literature_storage_setup_v1.py`
- `tests/test_literature_storage_v1.py`
- `tests/fixtures/literature_storage_v1/*` — invented records only
- a new Codex-owned S1 results document and local setup controls/receipts, explicitly named in the
  dispatch; real capability/path records stay outside public Git by the reviewed ignore policy.

Existing registry/schema files, other operations modules, shared contract checks and all Claude-owned
planning/implementation are excluded. If these paths become occupied or an interface change is
necessary, return with the proposed conflict; do not overwrite or broaden the allowlist.

## Required synthetic and bounded native checks

| Requirement | Exact pass/fail evidence |
|---|---|
| Pinned identity | Wrong registry hash, UUID, mount, filesystem, writable status or device is refused before writes |
| Path confinement | Parent traversal, absolute member names, symlink components, wrong role and source overlap are refused |
| Missing mount | Same-named ordinary directory and registry-only identity are refused; no internal fallthrough |
| Writer authority | Missing/mismatched capability, another live writer and writes outside literature areas are refused |
| Exclusive creation | Existing journal/run directory cannot be overwritten; an existing safe parent is preserved |
| Append durability | Invented events survive flush/reopen and retain order; no truncation or duplicate terminal success |
| Space/timing | Floor+40 GiB start rule and floor+remaining-cap checks at file boundaries/60 s use fake clock/volume observations |
| Failure fallback | Primary failure produces remaining events on the approved internal fallback and a stopped status; no continued payload writes |
| Native adapter | Read-only native metadata works; a monitor/tool failure denies the operation rather than guessing |
| Preservation | Imaging/source registries and existing bytes unchanged; no download, install, promotion or live sizing |

No tests are run by this proposal. Do not launch storage probes concurrently with an imaging run.
