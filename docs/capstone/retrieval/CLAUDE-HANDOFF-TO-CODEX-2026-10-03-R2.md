# Claude → Codex handoff, round 2: Plan 07 after the L1–L6 handback and S2 (2026-10-03)

**From:** Claude (Plan 07 lane). This file holds a prompt for Quinton to paste. It dispatches
nothing on its own.

## Quinton's decisions since the L1–L6 handback (logged in RUNNING-LOG)

1. S1 and S2: **"Approve both."** S1 is bounded storage setup by Codex. S2 was dispatched to
   Claude and is now done; see `CLAUDE-S2-HANDBACK-2026-10-03.md`.
2. Memory cap: **"Watchdog is fine."**
3. Cleanup: **"Delete both."**
4. Integration: **"Accept all three"** of Codex's recommended options.

---

## Prompt for Codex (paste as one packet)

> **Objective:** carry out the Plan 07 items Quinton approved on 2026-10-03. Work through them in
> order, with imaging R-01 first. Stop after the handback.
>
> **Read first:**
> - `docs/capstone/retrieval/planning/RUNNING-LOG.md`, the three 2026-10-03 entries after
>   "handoff to Codex written";
> - `docs/capstone/retrieval/CLAUDE-S2-HANDBACK-2026-10-03.md`;
> - your own `PLAN07-LITERATURE-S1-PROPOSAL-2026-10-03.md`,
>   `CODEX-PLAN07-INTEGRATION-OPTIONS-2026-10-03.md` and `CODEX-PLAN07-L1-L6-HANDBACK-2026-10-03.md`.
>
> **M1. Record the decisions** (`DECISIONS.md`). Add records citing the RUNNING-LOG entry
> "Codex L1-L6 handback reviewed; Quinton's S1/S2, cleanup and integration decisions":
> - S1 bounded setup approved, with the internal fallback
>   `/Users/quintonevans/PROWL-Literature-Receipts/`;
> - S2 dispatched to Claude;
> - the watchdog memory-cap method;
> - deletion of the two named leftovers;
> - the three integration choices: retrieval schemas join the shared offline contract checks;
>   D-085 span-hit and delivered-evidence metrics approved as additional, separately reported
>   metrics with their preconditions, official metrics unchanged; P4a prepared after the imaging
>   queue and run in an idle window.
>
> Do not grant or imply a run S signature.
>
> **M2. S1 implementation and setup** (approved; your proposal's allowlist and order):
> - implement `literature_storage_v1` and its invented tests;
> - after the tests pass, create only `scratch/literature`, `artifacts/literature`,
>   `artifacts/literature/receipts` and the internal fallback folder;
> - enable one capability-scoped writer.
>
> Native probes only while imaging is idle.
>
> **Interface S2 needs from S1:**
> - a volume probe whose `observe()` returns a dict with `uuid`, `mount`, `writable` (bool) and
>   `free_bytes` (int, from `statvfs.f_bavail`), and preferably `role`;
> - the literal `scratch_root` (the parent of `sizing-<run_id>`), `receipts_dir` and
>   `fallback_dir` paths;
> - the headroom floor in bytes.
>
> `sizing_v1` creates its `sizing-<run_id>` folder exclusively and needs plain write access there
> and in `receipts_dir`. It also takes an advisory `flock` file in `receipts_dir`. Propose the
> binding, a small adapter that maps your capability onto `run_sizing(..., volume=...)`, as a
> named follow-up. Do not edit `src/retrieval/sizing_v1/` (Claude-owned); return requested
> interface changes to Claude.
>
> **M3. Native qualification of S2** (read-only and offline). On Quinton's Mac, run
> `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1` and the full
> `tests/retrieval`, and report the counts. Confirm the tool code identity
> `814b89c5dac055b59df4c28ff14cca008d7831d63ba31b418e380831fad837aa` with
> `python -c "from src.retrieval.sizing_v1.runner import code_identity; print(code_identity('.'))"`.
> Report any failure to Claude verbatim. Do not fix Claude's files.
>
> **M4. Cleanup** (approved). Recheck the exact paths, types and hashes in your L1–L6 handback, then
> delete only:
> - `_to_delete/claude-RUNNING-LOG.md.tmp` (SHA `0c1f14cf…`);
> - `.git/index.lock.stale-claude-20260928` (0 bytes).
>
> Never delete the `_to_delete` folder, an active lock, or anything else.
>
> **M5. Integration scoping** (approved choices; each needs its own concrete scope before code):
> - (a) a scoped packet adding the 12 retrieval 1.0.0 schemas as a separate offline section of
>   the shared contract checks, and reconciling the retrieval contract README's stale "pending
>   re-review" status;
> - (b) the D-085 amendment record, naming the metrics, denominators, rights, tokenizer and
>   development-only role;
> - (c) a P4a install-authorization packet (named runtime, pinned PostgreSQL image, pgvector,
>   storage and resource limits, stop limits) for Quinton to approve later.
>
> Drafts only for (a) and (c).
>
> **M6. Checkpoint scope.** Add the S2 code, tests, fixtures and handback, and this handoff, to the
> pending checkpoint file list, with hashes from the S2 handback. **Commit or push only with
> Quinton's explicit authorization.**
>
> **Exclusions:**
> - no literature download, sizing run, run S signature, P4/P5 execution, install or database work;
> - no edits to `docs/capstone/retrieval/planning/`, `src/retrieval/` or `tests/retrieval/`
>   (Claude-owned);
> - one writer per shared file;
> - imaging has priority for accelerator and storage.
>
> **Handback** (phone-screen first):
> 1. what finished;
> 2. files changed and checks, including native S2 test counts;
> 3. decisions needed from Quinton;
> 4. the exact next starting point.
>
> No follow-on dispatch.

## After this, on Claude's side

Claude acts on any native S2 failure and any S1 interface request.

These need new authority:
- the S1/S2 binding;
- run S signing (S3 capacity reading plus Quinton's signature);
- run A;
- P4a.
