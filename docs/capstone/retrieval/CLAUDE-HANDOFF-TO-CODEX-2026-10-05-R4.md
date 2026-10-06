# Claude → Codex handoff, round 4: `sizing_v1.2` and the rest of N4 (2026-10-05)

**From:** Claude. This is a prompt for Quinton to paste; it dispatches nothing on its own.

## What changed since your follow-up handback

- Your bounded-diagnostics request (`operations/PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md`) is
  implemented as `sizing_v1.2`. See `CLAUDE-S2-V1.2-HANDBACK-2026-10-04.md`. The new code identity
  is `3198b2685709bff92367f0cba6254b09a9269c48837fde7d3dfc4ac61f464203`.
- Only three files changed: `__init__.py`, `parser.py` and `test_sizing_v1_parser.py`.
- The `fsio` contract is unchanged.
- **Quinton, 2026-10-05:** "Yes, commit locally". After the native tests pass, make one more local
  commit containing v1.2, the binding work and anything else verified. No push.

---

## Prompt for Codex (paste as one packet)

> **Objective:** qualify `sizing_v1.2` on Quinton's Mac, finish S1-S2-BINDING-V1 (N4) against it,
> and make one local commit. Imaging R-01 keeps priority. Stop after the handback.
>
> **Read first:**
> - `docs/capstone/retrieval/CLAUDE-S2-V1.2-HANDBACK-2026-10-04.md`;
> - `docs/capstone/retrieval/planning/RUNNING-LOG.md`, the 2026-10-04 and 2026-10-05 entries;
> - your own `PLAN07-FOLLOWUP-HANDBACK-2026-10-04.md`, `PLAN07-S1-S2-BINDING-PACKET-2026-10-04.md`
>   and `PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md`.
>
> **P1. Decision record** (`DECISIONS.md`). Record the 2026-10-05 approval of one more local commit
> (v1.2, the binding and anything else verified; no push), citing the RUNNING-LOG entry
> "sizing_v1.2 bounded diagnostics; Quinton approves one more local commit".
>
> **P2. Native qualification of v1.2** (read-only, offline). On Quinton's Mac, run
> `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1`, expecting 155 collected,
> then the full `tests/retrieval`, and report the counts. Then:
> - confirm code identity `3198b268…` and all 22 pins (3 new in the v1.2 handback, 19 carried
>   from v1.1);
> - confirm on macOS that `os.waitid` with `WNOWAIT` works (the grandchild test exercises it) and
>   that no drain thread or descriptor leaks.
>
> Report any failure to Claude verbatim; do not edit Claude's files.
>
> **P3. N4 binding**, against v1.2 and the approved binding packet:
> - implement the guarded `SizingFs` and `observe()` per the `fsio` contract table;
> - add the invented tests from your packet, including a full invented run under the guarded hook
>   with the live `WatchdogLauncher`;
> - do the native rehearsal only on invented input, only in binding-qualification child areas,
>   only while imaging is idle;
> - never create a top-level `sizing-*` in real scratch; keep the CLI refusal.
>
> If the contract is insufficient, send Claude a concrete interface request rather than editing
> Claude's files.
>
> **P4. Local commit** (approved, no push). Once P2 passes (and P3 if it is complete), refresh the
> exact scope:
> - v1.2's 3 changed files;
> - the v1.2 handback and this handoff;
> - the latest RUNNING-LOG;
> - your binding and decision files.
>
> Re-verify every hash and make one local commit. **Do not push.** If P3 is incomplete, commit only
> what is verified and list the rest.
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
