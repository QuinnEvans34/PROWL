# Claude → Codex handoff, round 3: Plan 07 after M1–M6 and `sizing_v1.1` (2026-10-04)

**From:** Claude. This is a prompt for Quinton to paste; it dispatches nothing on its own.

## Quinton's decisions on 2026-10-04 (logged in RUNNING-LOG)

1. "Claude adds the hook first." This is done: `CLAUDE-S2-V1.1-HANDBACK-2026-10-04.md`, code
   identity `df585e2b10a69f55e24db8cc0f96822151a43d52be15ad5bb4917bd9a0a24d4e`. After it, Codex
   builds S1-S2-BINDING-V1 and re-runs the native tests.
2. "Commit locally, no push."
3. The shared-contract packet: "Yes, build it."

---

## Prompt for Codex (paste as one packet)

> **Objective:** carry out the three Plan 07 items Quinton approved on 2026-10-04. Imaging R-01
> keeps priority. Stop after the handback.
>
> **Read first:**
> - `docs/capstone/retrieval/planning/RUNNING-LOG.md`, the 2026-10-04 entries;
> - `docs/capstone/retrieval/CLAUDE-S2-V1.1-HANDBACK-2026-10-04.md`;
> - `docs/capstone/retrieval/CLAUDE-S2-IO-HOOK-PROPOSAL-2026-10-04.md`;
> - your own `PLAN07-S1-S2-BINDING-FOLLOWUP-2026-10-04.md`, `PLAN07-SHARED-CONTRACT-PACKET-2026-10-04.md`
>   and `PLAN07-S1-RESULTS-2026-10-04.md`.
>
> **N1. Decision records** (`DECISIONS.md`). Record the three 2026-10-04 approvals, citing the
> RUNNING-LOG entry "Codex M1-M6 handback reviewed; Quinton approves the S2 filesystem hook, a
> local commit and the shared-contract packet". No run S signature is implied.
>
> **N2. Native re-qualification of S2 v1.1** (read-only, offline). On Quinton's Mac, run
> `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1` (expect 144 collected) and
> the full `tests/retrieval`, and report the counts. Confirm code identity `df585e2b…` and the 22
> pins in the v1.1 handback. Report any failure to Claude verbatim; do not edit Claude's files.
>
> **N3. Shared-contract packet** (approved). Implement exactly the drafted scope:
> `tests/test_retrieval_contracts.py` plus invented fixtures, and the scoped contract-README status
> fix. Stop if a pin has drifted or a path is occupied. Run both shared modules, the `contract`
> marker gate and the full retrieval suite. Show the exact diff and fixture pins.
>
> **N4. S1-S2-BINDING-V1** (approved after the hook). Implement
> `src/operations/literature_sizing_binding_v1.py`, which provides:
> - a `SizingFs` built on your S1 lease and no-follow descriptors, following the `fsio` contract
>   table, including "guards apply when a file is opened; the child writes the passed descriptor
>   directly; `close` must not commit by name";
> - a guarded `observe()`;
> - a call to `run_sizing(config, ..., volume=..., fs=...)`.
>
> Then:
> - write invented tests covering wrong role, UUID or device; registry drift; path substitution; a
>   competing lease and signed-copy lock; space loss mid-stream; primary and fallback failure;
>   preserved cumulative counters; and a full invented run under your hook;
> - do a native binding rehearsal only on invented local input, only while imaging is idle;
> - **never create `sizing-*` in the real scratch area**, since an orphan blocks S2's prior-run
>   proof;
> - do not change the S2 CLI refusal.
>
> If the hook contract is insufficient, send Claude a concrete interface request; do not patch
> Claude's files.
>
> **N5. Local commit** (approved, no push). After N2 and N3 pass, and N4 too if it is complete,
> refresh the pending checkpoint scope with the v1.1 hashes:
> - ten S2 files changed and `fsio.py` is new;
> - add the v1.1 handback, the hook proposal, this handoff and your new files.
>
> Re-verify every hash, then make one local commit. **Do not push.** If N4 is incomplete, commit
> only what is verified and list the rest.
>
> **Exclusions:**
> - no download, sizing run, run S signature, S3, P4/P5 execution, install or database work;
> - no D-085 producer migration;
> - no edits to `docs/capstone/retrieval/planning/`, `src/retrieval/` or `tests/retrieval/`;
> - one writer per shared file;
> - imaging has priority.
>
> **Handback** (phone-screen first):
> 1. what finished;
> 2. files, checks and native counts;
> 3. decisions needed from Quinton;
> 4. the exact next starting point.
>
> No follow-on dispatch.
