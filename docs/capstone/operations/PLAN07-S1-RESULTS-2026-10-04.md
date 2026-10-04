# Plan07 S1 bounded setup — complete

D-341 authorization: Quinton's M1–M6 dispatch, confirming the October3 RUNNING-LOG approval.
R-01 was settled first in local commit `5856fdc9d4f6b2318c918505576244f324247f12`; no push.
Native process checks found no active Python imaging/sizing worker before setup. D-335 remains
the latest imaging experiment; its consumed requests, memberships, holds and backup ceiling stand.

## Implementation and scope

Added `src/operations/literature_storage_v1.py`,
`scripts/diagnostics/literature_storage_setup_v1.py`, `tests/test_literature_storage_v1.py` and two
invented fixture files. No existing operation, registry, schema, imaging or Claude producer changed.
The adapter checks a pinned capability and registry, root roles/access/domain, UUID/mount/APFS,
actual device and directory identities, writable observations and space. It uses descriptor-based
no-follow path traversal, exclusive run/file/journal creation, append/fsync, cumulative receipt
ceilings and one advisory flock. Replaced locks, symlinks and hardlinks refuse access. These are
cooperative application guards, not OS containment against arbitrary processes.

The enabled capability is **bounded setup only**. Its fixed setup identity cannot overwrite/repeat
the retained probe; it cannot run S2, publish corpus artifacts or write a DB. Setup reserves: 1 MiB
invented payload, 64 MiB primary receipts and 64 MiB fallback receipts. The future 40 GiB scratch
cap is checked as an observation, not allocated. Setup refuses below floor plus its bounded
allowances; later sizing requires floor+40 GiB at start and floor+remaining allowance thereafter.
`tick()` exposes the 60-second check; write boundaries always recheck identity/capacity.

## Native evidence

- **49 invented tests passed in 0.51 seconds**, after adding lock-replacement, file-boundary space,
  symlink-lock and fsync-failure checks. No real roots/network in unit tests. The earlier 45-test
  pass was before these four additions; no failed test attempt.
- Approved external UUID `22750B93-2F3F-499D-87F5-902981BFAB59`, internal UUID
  `542E8B1F-8D50-4783-9250-752DFDC899CD`, APFS and distinct devices verified natively.
- Created exactly the four approved areas: `/Volumes/PROWL-Data/PROWL/scratch/literature`,
  `/Volumes/PROWL-Data/PROWL/artifacts/literature`, its `receipts` child, and
  `/Users/quintonevans/PROWL-Literature-Receipts`. The sole invented probe child is
  `scratch/literature/setup-20261004-01/`.
- Preserved **61,440 payload bytes** in `invented-probe.txt`; exclusive create, fsync, reopen and
  read-back passed. A second writer was refused. Existing evidence was not cleared or repaired.
- Three primary events (392 bytes) and one fallback terminal event (139 bytes) reopen with sequence
  1–4. An injected `writable=False` observation stopped the next payload before creation; fallback
  contains only `stopped_primary_failure`, never a payload or `completed`. No drive was disconnected.
- Additional read-only flock contention checks passed on both existing APFS journals. Primary
  and fallback directory/file fsync had already passed during journal creation/append.

The final observation recorded external `f_bavail` free bytes **2,866,266,099,712**, capacity
4,000,750,501,888; floor **400,075,050,189** (`max(100 GiB, ceil(capacity/10))`). Internal free bytes
127,120,420,864; capacity994,610,155,520; floor107,374,182,400. Free-space readings can change;
these are setup evidence, **not S3 signing-time capacity acceptance**.

Local controls/receipts are Git-ignored in `outputs/prowl/PLAN07-S1-SETUP-20261004/`:
`capability.json`, `setup-approval.json`, `native-result.json`, `native-lock-qualification.json`,
`s2-native-qualification.json` and `cleanup-result.json`. Capability transport SHA-256:
`e6b9de3b381bfa891bae35725978e1e967f17c83bf2dfcede6f9b45ea51afe3a`.
Registry remains `46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788`,
`scientific_runs_enabled: false`. No write to the shared checkpoint-backup allocation; its fixed
18,318,645,873-byte ceiling/registered20 GiB remain unchanged. This is not an independent keeper
claim for the setup payload. If internal identity/durability also fails, fallback fails closed and
the journal remains incomplete.

## Interface handed forward

`NativeVolume('/Volumes/PROWL-Data', 'literature').observe()` returns a dict with `uuid`, `mount`,
`writable` bool, `free_bytes` int from `statvfs.f_bavail`, `role`, filesystem/device/capacity.
Literal S2 bindings are scratch_root `/Volumes/PROWL-Data/PROWL/scratch/literature` (parent of a
future `sizing-<run_id>`), receipts_dir `/Volumes/PROWL-Data/PROWL/artifacts/literature/receipts`,
fallback_dir `/Users/quintonevans/PROWL-Literature-Receipts`, and current external floor400075050189B.

Next is the separately scoped [S1-S2-BINDING-V1 follow-up](PLAN07-S1-S2-BINDING-FOLLOWUP-2026-10-04.md).
S2 still uses plain path I/O and is not bound to this lease. Run S's CLI still refuses execution.
No download, signature, live TLS/NLM test, source activation, install or follow-on dispatch occurred.
