# S2 filesystem hook — Codex integration review

**Latest reconciliation: the v1.1 hook has arrived and N2 passed in the other Codex chat.**
[Claude's exact handback](../retrieval/CLAUDE-S2-V1.1-HANDBACK-2026-10-04.md), SHA
`3d00e92aac6f12ae4a052c70988a630522bd5af3ad210e40cc846d8a1f13b2c6`, reports identity
`df585e2b10a69f55e24db8cc0f96822151a43d52be15ad5bb4917bd9a0a24d4e`.
[Native N2 verification](CODEX-S2-V1.1-NATIVE-REVIEW-2026-10-04.md) records144sizing/326retrieval
passes, no skips, and all22pins. This chat independently rechecked the22pins and identity without
rerunning the other chat's tests. Hook forwarding, parent manifest ownership, descriptor handover
and inclusion of `fsio.py` in code identity are implemented. Guarded journal wrappers, cumulative
budgets, no-delete policy and lease enforcement remain Codex binding responsibilities.

**One Claude-owned prerequisite remains:** `parser.run_with_watchdog` still uses an uncapped
`tempfile.TemporaryFile()` for stderr and drains stdout only after the child exits. `SizingFs`
cannot govern that diagnostic path. A returned2,000-byte tail is not a disk ceiling; a stdout pipe
can also block a noisy child until timeout. Native N2 is valid compatibility evidence, but it does
not qualify a bounded guarded launcher. N4 is incomplete; no binding or native external rehearsal
was enabled. The concrete request below is ready for Quinton to relay to Claude.

### Concrete request against the delivered v1.1

Add a named bounded-diagnostics mode to `WatchdogLauncher`/`run_with_watchdog`, keeping the existing
PlainFs compatibility oracles and CLI refusal. In that mode, drain both streams concurrently into
bounded memory; proposed limits are1 MiB accepted per stream and64 KiB retained stderr tail.
Overflow must stop/reap the child and report a distinct failed parse, without a manifest. Keep
RSS/time/periodic-volume checks active under pipe pressure and close all pipe/child descriptors on
every exit. No anonymous temporary diagnostic file in this mode. Test noisy stdout/stderr, overflow,
periodic failure and child failure, then publish fresh code identity and complete pins/handback.
These proposed diagnostics limits are an interface request, not Run S authorization or a signed
copy amendment. Codex will qualify the actual guarded launcher together with the binding afterward.

The initial proposal review below is retained as history. Its “not arrived” status describes the
earlier read, not the delivered revision. No direct delivery is claimed: Claude's native app exposed
only an empty accessibility container, so the destination conversation could not be verified.

## Initial proposal review, before v1.1 arrived

The proposed `SizingFs` is the right prerequisite for S1-S2-BINDING-V1. This reviews Claude's
proposal `270436ae6e19fd73730bfbbd05d5c5e94725dc52aeb64d9f5b6b353deedea87b`; current source is
still sizing_v1 `814b89c5dac055b59df4c28ff14cca008d7831d63ba31b418e380831fad837aa`.
Quinton's October4 log records Claude-first implementation. Codex has not changed Claude's files,
sent a new coding dispatch or claimed acceptance of unseen sizing_v1.1.

## Required hook details before binding acceptance

1. **Explicit injection throughout.** `run_sizing(..., fs=...)` must forward the same object through
   lock, prior-run discovery, mkdir, transfer, partial-output accounting, journal and parser-parent
   operations. The guarded path must never fall back to PlainFs on an error or omitted hook. Keep
   PlainFs for backward-compatible offline tests; it is not an acceptable live binding.
2. **Journal streams need guarded append/flush.** `create_exclusive` returning an ordinary binary
   object is insufficient if later writes bypass receipt quotas and lease checks. A binding-owned
   file wrapper must guard each append/flush, account bytes before acceptance and preserve partial
   writes. Clarify binary-to-text adaptation, fileno/close ownership and exceptional close behavior.
   Keep primary/fallback sequence reconciliation and stopped/incomplete semantics intact.
3. **Parser capabilities end at file descriptors.** Parent opens and verifies source/output under
   the lease; child receives only those descriptors plus non-path metadata. Include `pass_fds` in
   the launcher/watchdog interface, close unrelated inherited descriptors and write the manifest in
   the parent through the hook. Test the actual child path, not only an in-process stub. Descriptor
   delegation prevents a substituted path from redirecting output; it does not call a Python stream
   wrapper on every child write. Parent watchdog checks and the child's byte meter must provide the
   stated stop latency/accounting. Do not claim instantaneous revocation after volume/path loss.
4. **Diagnostic I/O is currently missing from the proposal's inventory.**
   `parser.run_with_watchdog` opens `tempfile.TemporaryFile()` without a location/byte limit; child
   stderr writes directly there. The later2,000-byte tail limits only returned data, not disk use.
   `test_noisy_child_stderr_cannot_block_the_watchdog` writes300,000bytes and proves drainage,
   not a storage ceiling. This is a source-read finding; no new noisy process was launched.

   Recommended guarded behavior: drain stdout/stderr concurrently into bounded memory, with a
   maximum1 MiB accepted per stream and a64 KiB stderr tail; overflow stops the child and records
   failure. Preserve the existing4 GiB RSS/0.5s watchdog and time/periodic checks. Never block on a
   full pipe. A bounded diagnostics file is an alternative only if its location, writes and partial
   bytes are capability-scoped/charged, not an anonymous unbudgeted internal file. Keep PlainFs
   legacy test behavior if needed; test the guarded diagnostic mode separately. Final bounds/reason
   names are part of the exact handback, not already an amendment to Run S's signed copy.
5. **Failed empty journal preservation.** `remove_own_empty` must use descriptor/inode ownership
   and refuse a substituted, hardlinked or nonempty target. The binding's current approval includes
   no new deletion: its implementation should refuse removal and retain the failed empty journal,
   reporting the resulting incomplete/start refusal for review. Never rename it out of prior-run
   discovery or delete it to reset counters. PlainFs compatibility is separate from this guarded
   preservation policy.
6. **List/stat must be guarded too.** Return bare names; reject unsafe or symlink entries. `exists`
   returns False only for a missing authorized entry, never for identity/permission/tool failure.
   Restrict area/relative paths before I/O. Reads for prior-run proof and parser input are included;
   source-data arrays and arbitrary metadata must not be reachable through this hook.
7. **Frozen identity includes new code.** Add the hook module and any parser-worker helper to the
   code-identity file inventory, bump tool identity/version and publish a complete new per-file
   handback. Preserve original21pins/results as historical evidence; do not edit their hashes.

Suggested adversarial coverage: hook-required guarded mode, no bypass in parent or actual child,
substituted parent/final symlink, hardlink/lock collision, closed lease, receipt/fallback cap mid-line,
guarded diagnostic overflow and pipe pressure, descriptor closure on launch/parse failure, no manifest
after child failure, retained partial outputs, and exact prior-run counters after primary loss.

## Copyable note for Claude

Please use this review with your already approved sizing_v1.1 hook work. The interface direction is
accepted for integration planning. Cover parser stderr/stdout as well as payload/journal paths:
current `TemporaryFile()` stderr is outside the capability and uncapped. Clarify guarded stream
append/flush, pass_fds/manifest ownership, fail-closed list/stat and a no-delete preservation mode for
the failed empty journal. Keep original tests/oracles with PlainFs and add guarded-mode tests; do
not weaken caps or enable execution. Return the final interface, exact code inventory/hash and
native commands in a new handback. Codex will then implement the descriptor backend and qualify it.

This note is saved for Quinton/Claude to read. No direct Claude messaging connector is available
in this task, and no delivery to Claude is claimed. It does not authorize a download or signature.
