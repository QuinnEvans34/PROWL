# S1-S2-BINDING-V1 — concrete implementation and qualification packet

**Ordering approved (D-346): Claude hook first, then Codex binding/native qualification.** The exact
v1.1 handback has now arrived; [N2 in the other Codex chat](CODEX-S2-V1.1-NATIVE-REVIEW-2026-10-04.md)
passed144sizing/326retrieval checks with22pins and identitydf585e2b. This chat reverified those pins.
N4 remains incomplete because the [delivered watchdog diagnostic path](PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md)
is outside the hook and uncapped. This packet defines the bounded implementation/acceptance scope;
it is not a live sizing request, S3 capacity grant or S4 signature. No backend, qualifier capability
or external rehearsal is enabled. Start with Claude's exact bounded-diagnostics response/handback.

Sources: [S1 results](PLAN07-S1-RESULTS-2026-10-04.md),
[original S2 handback](../retrieval/CLAUDE-S2-HANDBACK-2026-10-03.md),
[delivered v1.1 handback](../retrieval/CLAUDE-S2-V1.1-HANDBACK-2026-10-04.md),
[Claude hook proposal](../retrieval/CLAUDE-S2-IO-HOOK-PROPOSAL-2026-10-04.md) and
[Codex's hook review](PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md). No prerequisite is satisfied by
file presence or by the original131/313passes once code identity changes.

## Allowlist and ownership

Codex: new `src/operations/literature_sizing_binding_v1.py`,
`tests/test_literature_sizing_binding_v1.py`, invented fixtures in
`tests/fixtures/literature_sizing_binding_v1/`, a new bounded qualification CLI under
`scripts/diagnostics/`, local ignored controls/receipts and new results/checkpoint records.
Existing S1 code stays pinned; reuse its descriptor/floor primitives without repurposing its setup
capability or changing its passed semantics. Any necessary existing-module change must first be
identified in the concrete scope and requalified. Claude owns hook/core/worker and its lane tests.
No roots/schema/dependency change, live CLI, original arrays, source activation, import, DB or model.

## Backend and capability contract

The new backend implements the finalized SizingFs interface against no-follow directory descriptors.
Areas are only scratch, receipts and fallback. Relative names are checked before any open/stat/list:
bare components or the approved `sizing-<run_id>/<bare>` child; no traversal, absolute path, arbitrary
area, symlink, nonregular file or hardlink. Pin directory/device/inode relationships and recheck
path substitution at parent boundaries. Lock objects preserve nonblocking held-versus-unsupported
distinction. One `.literature-writer.lock` wraps the entire call, interoperating with S1's lease and
S2's additional per-signed-copy lock; no age-based takeover or unsafe lock replacement.

A separate versioned **offline-qualification capability** pins the binding/S1/new S2 code inventory,
registry SHA, authorityD-346, executor/writer, run identity, literal areas, expected UUID/APFS/device,
purpose, bounded byte allowances and retained prior-run identity. Future live authorization is a
different reviewed job capability and frozen signed copy. S1's D-341 `bounded_setup` cap is not
reused to permit a sizing job. Source alias access and scientific_runs_enabledfalse remain unchanged.

Future live literal paths remain scratch `/Volumes/PROWL-Data/PROWL/scratch/literature`, receipts
`/Volumes/PROWL-Data/PROWL/artifacts/literature/receipts`, fallback
`/Users/quintonevans/PROWL-Literature-Receipts`. Guarded volume.observe verifies registry/roles,
UUID/mount/APFS/device and writable/space observations under the lease, then returns the dict S2
expects. Free bytes come from f_bavail; floor is `max(100 GiB, ceil(usable_capacity/10))`, freshly
computed. Retain S2's floor+40 GiB start and floor+remaining scratch before-file/60-second rules.

Exclusive creation and cumulative byte budgets cover all primary/fallback journal writes, not just
their opens. Cumulative receipts/fallback ceilings stay64 MiB each and include existing contents;
no reset. Fallback holds journal/failure events only, never downloads/parser data. Primary failure
stops payload work; fallback failure leaves an incomplete journal, never completed. The no-delete
backend retains empty failed journals and partial payloads, so ambiguous reruns remain refused.

Parent opens parser input/output through the backend and passes only validated descriptors. Child
meters/timeouts and parent watchdog checks guard the delegated operation; partial output remains
charged and preserved. Parent writes manifest only after successful validation. Diagnostic streams
must obey the finalized bounded mode in the hook review; no unbudgeted internal temporary files.
Report actual detection/poll overshoot rather than calling the watchdog an OS memory limit.

## Qualification sequence and exact exit requirements

1. Verify Claude's new handback and complete source/test/fixture/code-identity inventory; inspect
   every hook call and parser FD/diagnostics path. Run the exact native sizing/full retrieval
   commands. Send failures verbatim to Claude; Codex does not fix its files. Confirm original P3
   pins and current S1 baseline49checks remain intact. No live NLM/TLS exposure in this phase.
2. Implement the backend and invented unit/integration tests in temporary directories only. Deny
   outbound socket connection/DNS. Use the real runner with deterministic invented transports;
   preserve all hard caps and original counters. Ordinary dictionary/stub calls alone do not qualify
   the actual runner or parser child. No reference to external real literature/source files.
3. Test every boundary: invalid capability/code/registry/role/device; missing mount; path/parent/
   symlink/hardlink substitution; wrong/closed/competing lease; existing run/file/journal; unsupported
   locks; receipt/fallback overflow and short writes/fsync faults; child FD/no-path handoff and
   diagnostics limit/pipe pressure; headroom failure before a file/mid-parse; terminal/fallback merge,
   unknown/missing/truncated prior journal and two-run cumulative limit. Preserve failures; no filter,
   automatic retry, silent counter reset or weakened success rule.
4. After unit/native S2 checks pass, freeze a **fresh invented native qualification capability**,
   request/source pins and measured byte budget before external writes. One success scenario and
   one separately named primary-failure scenario only; a distinct pre-created denied-scope sentinel
   checks that substituted paths receive zero writes. Combined fixture/payload≤1 MiB; new primary
   and fallback receipts≤64 KiB each, within their existing cumulative64 MiB reserves. No writes to
   the shared checkpoint-backup allocation. Registered imaging backup ceiling remains fixed.
5. Native qualifier uses child areas named `binding-qualification-<id>`: scratch below the approved
   literature root, primary receipts below its approved receipts area, fallback below its approved
   internal area. Bind these exact paths in the qualification capability; never place test
   `sizing-*` directories at the actual Run S scratch parent or test `run-S-*` journals at the real
   top-level receipt/fallback roots. Preserve the complete qualifier; no auto cleanup. This prevents
   invented histories/orphans from masquerading as Run S evidence.
6. Run only while imaging is idle: no accelerator,≤120s total qualifier wall time,4 GiB parser RSS
   watchdog with its stated poll method, no network or registered-source reads. Stop on bounds,
   failed monitor, identity change, unexpected file or hook mismatch. No extension/rerun of the same
   consumed qualification request. Read back/fsync and test APFS locks in both failure domains.
7. Audit exact payload/journal bytes, child probes, descriptor closure, fallback-only terminal
   events and untouched sentinels; review the retained success/failure results. Qualify the actual
   binding/runner/child together and freeze their final identities. Update the pending checkpoint
   with these new versions, retaining all original S2/S1 evidence. Stop at the handback.

Only then propose S3, the complete frozen run S copy/S4 signature and a later launch. Current
packet creates no qualifier areas/capability, consumes no request and enables no execution branch.
