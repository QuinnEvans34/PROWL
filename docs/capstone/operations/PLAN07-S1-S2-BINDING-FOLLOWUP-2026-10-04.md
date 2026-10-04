# S1-S2-BINDING-V1 — named follow-up proposal

**Proposed, not dispatched.** Codex owns the adapter; Claude owns `sizing_v1`. Start from
[S1 results](PLAN07-S1-RESULTS-2026-10-04.md) and the unchanged
[S2 handback](../retrieval/CLAUDE-S2-HANDBACK-2026-10-03.md).

Proposed allowlist: a new `src/operations/literature_sizing_binding_v1.py`, corresponding invented
tests/fixtures outside `tests/retrieval/`, a bounded native binding qualification packet and result
document. No edits to `src/retrieval/sizing_v1/`, its tests, roots or scientific producers. The current
setup capability cannot authorize a sizing job. A future job capability must pin the S1/binding/S2
code, registry, literal areas, executor, signed-copy hash and cumulative budgets; signature and
launch remain separate.

The small adapter should:

1. Acquire the one literature-writer lease for the entire invocation, preserving S2's additional
   per-signed-copy advisory lock. Validate both volume identities and all root relationships.
2. Build literal `scratch_root`, `receipts_dir`, `fallback_dir`, `volume_uuid`, `volume_mount` and
   freshly checked `headroom_floor_bytes`; call
   `run_sizing(config, ..., volume=guarded_volume, ...)`. `guarded_volume.observe()` must verify
   the pinned registry, roles, mounted UUID/device and path identities under the lease, then return
   S2's dict interface. S2 retains its start/before-file/60-second floor+remaining-cap checks.
3. Support exclusive `sizing-<run_id>` creation and ordinary write/append/flock in the named areas.
   Preserve S2 journal/rerun semantics and never create `sizing-*` during setup or binding fixtures
   in real scratch; an orphan would block S2's prior-run proof.
4. Reconcile the I/O boundary explicitly: S2 currently opens literal paths directly, while S1's
   setup writer uses no-follow descriptors. A wrapper alone does not make every S2 path open a
   descriptor-guarded write. Prove confinement at all S2 write/append/lock boundaries with invented
   substitution/failure tests before proposing live use. If this needs a new injectable file/lock
   hook, send the concrete interface request to Claude; Codex must not patch Claude's files.
5. Test wrong role/UUID/device, registry drift, path substitution, competing lease and signed-copy
   lock, space loss mid-stream, primary/fallback failure and preserved cumulative counters. Native
   rehearsal uses invented local input while imaging is idle; it grants no network acquisition.

Current interface supplied by S1 needs no immediate S2 change to return observations/paths.
The plain-path versus descriptor boundary is an open binding qualification requirement. No interface
change or follow-on work was dispatched to Claude by M1–M6, and no live binding was implemented.
After acceptance: fresh S3 capacity reading, reviewed frozen run S copy (including watchdog,
HTTP-layer counter/reserve, expansion accounting and proposed partition format), S4 Quinton's
signature, and a separately reviewed launch. Tests/setup alone satisfy none of those permissions.
