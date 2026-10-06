# N4 guarded binding results — October 6

**The binding is implemented and passes native integration with temporary invented volumes.
P3 remains incomplete: the required rehearsal on the two actual APFS failure domains cannot run
while `/Volumes/PROWL-Data` is unmounted.** No external qualification area, capability or consumed
request was created. Preserve verified work under the approved P4 local checkpoint; no push.

## What was implemented

- `src/operations/literature_sizing_binding_v1.py`: separate offline qualification capability;
  unchanged S1 writer lease and shared lock; descriptor-guarded SizingFs and volume observation;
  actual `run_sizing(config, volume=..., fs=...)` delegation.
- No-follow directory/file opens, pinned device/inode relationships, fresh registry/role/UUID/APFS/
  writable/headroom checks, bounded relative names, competing signed-copy locks, and cumulative
  payload/primary/fallback budgets. Open descriptors are passed directly to the parser child;
  closing a handle only closes that descriptor, with no named commit or deletion.
- Existing contents count toward the 40 GiB scratch and 64 MiB primary/fallback ceilings. The
  smaller rehearsal bounds are 1 MiB payload, 64 KiB new primary receipts, 64 KiB fallback and
  120 seconds. Failed/short writes remain charged; partial payloads and empty journals are retained.
- Invented-only transport with fixed `.invalid` responses, fixed 4 GiB RSS watchdog, native Python
  executable and bounded polling. There is no live transport/CLI branch. Full headroom allowance
  is checked conservatively by this qualification binding; no live Run S capacity is inferred.
- A bounded qualification CLI prepares local controls and executes only consumed, pinned invented
  requests in `binding-qualification-<id>` children. It includes denied-scope sentinels, primary/
  fallback APFS lock probes, counters, bytes and process/thread/descriptor closure audits.

The separate capability does not widen S1's D-341 setup authority. It supplies D-346/D-350 offline
invented job authority. Future live use needs its own reviewed job capability and frozen signed
copy. Registry access and `scientific_runs_enabled: false` stay unchanged. Guards are cooperative
checks, not an OS sandbox against an adversarial process.

## Verification and exact limits

Final native command:

```text
.venv-prowl/bin/python -m pytest -q tests/test_literature_sizing_binding_v1.py tests/test_literature_storage_v1.py tests/test_contracts.py tests/test_retrieval_contracts.py tests/retrieval
626 passed in 14.82s
```

62 binding + 49 retained S1 + 173 shared-contract module + 342 retrieval checks. Earlier combined
runs were 617 and 625 passes; final count includes the full qualification executor, additional
watchdog-bound checks, ambiguous prior history and unchanged live CLI refusal. No skips.
The contract marker gate also reports `198 passed, 3181 deselected, 2 warnings in 7.20s`;
the two warnings are existing Torch deprecations. This is scoped verification, not a new full-project
or imaging acceptance.

Tests exercise wrong role/UUID/device, registry drift, substituted paths/symlinks/hardlinks,
wrong/closed/competing lease, signed-copy lock and unsupported locking, space loss during a live
parser, primary and fallback failure, short writes/fsync failure, retained quota accounting,
truncated/unknown/orphan prior evidence and the two-run limit. The full qualifier executes under
real WatchdogLauncher in temporary invented volume areas: one success, one injected primary
failure, two lock probes, untouched sentinels, zero live tracked children/threads/extra descriptors,
and consumed-request reuse refused. This does not substitute for actual APFS/volume qualification.

S1 exceptions map through S2's existing generic hook-error path: the injected primary observation
failure produces `stopped_internal_error`, with a `primary_lost` fallback event and cumulative final
counters. It never reports success. Both-domain failure raises JournalUnwritable and leaves incomplete
evidence. We corrected our initial invented expectation of `stopped_journal_primary_lost`; no Claude
code or test was changed to fit it. Two complete success runs exceed the smaller rehearsal receipt
allowance; the approved success-plus-failure sequence keeps the bound instead of raising it.

## Native external prerequisite failure

Preparation 01 used a relative registry argument and refused with
`StorageRefused: non-literal or unsafe absolute path`, before capability/external writes.
Preparation 02 used the correct literal absolute registry; native inspection refused with
`CalledProcessError: diskutil info -plist /Volumes/PROWL-Data returned exit status 1`.
A separate read-only check confirmed the mount path does not exist and diskutil reports
`Could not find disk: /Volumes/PROWL-Data`. Both local failure records are retained under
`outputs/prowl/PLAN07-BINDING-QUALIFICATION-20261006-01/` and `...-02/`.
No request was frozen or consumed. No mount was changed and no directory was substituted.

The [qualification JSON](PLAN07-BINDING-QUALIFICATION-2026-10-06.json) records final runtime/S1 pins,
verbatim checks and the exact failures. All 22 S2 pins and registry SHA were reverified. Original
S1 source/fixtures and registry were unchanged. Imaging evidence, consumed requests, memberships,
holds and the 18,318,645,873-byte whole-backup ceiling remain outside this packet.

## Exact next starting point

When the exact approved primary volume is available and imaging is idle, inspect this result and
reverify the pinned runtime/registry/UUID/devices and current cumulative bytes. Prepare a **fresh**
invented qualification ID; preserve both failed preparations. Freeze its request/capability hashes
before any external writes. Run the success-plus-primary-failure rehearsal only in the three named
qualification children, then inspect bytes, locks, counters, sentinels and process/descriptor closure.
Only passing actual-domain evidence can close N4. Do not create top-level `sizing-*`, reuse a consumed
request, reset a quota or infer a Run S signature. This handback dispatches nothing further.
