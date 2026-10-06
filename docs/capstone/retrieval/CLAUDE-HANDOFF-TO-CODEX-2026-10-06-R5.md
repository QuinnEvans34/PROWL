# Claude → Codex handoff, round 5: `sizing_v1.3` macOS repair (2026-10-06)

**From:** Claude. This is a prompt for Quinton to paste; it dispatches nothing on its own. The
authority is unchanged from round 4: D-350, plus the approved local commit (no push).

## Prompt for Codex (paste as one packet)

> **Objective:** qualify `sizing_v1.3` on Quinton's Mac, then finish round 4's P3 (the N4 binding)
> and P4 (the approved local commit, no push) against it. Imaging R-01 keeps priority. Stop after
> the handback.
>
> **Read first:**
> - `docs/capstone/retrieval/CLAUDE-S2-V1.3-HANDBACK-2026-10-06.md`;
> - `docs/capstone/retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-05-R4.md`, for the unchanged P3 and P4;
> - the 2026-10-06 entry in `docs/capstone/retrieval/planning/RUNNING-LOG.md`;
> - your own `CODEX-S2-V1.2-NATIVE-REVIEW-2026-10-06.md`.
>
> **Q1. Native qualification of v1.3** (read-only, offline). On Quinton's Mac, run
> `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1` (expect 160 collected) and the
> full `tests/retrieval` (expect 342). Report the counts verbatim. Then:
> - confirm code identity `791be77ffc96c17aaaf23a8b588c52bf8db1a82ddaa959d41ad217da318f4d53` and
>   all 22 pins (6 new in the v1.3 handback, 16 unchanged);
> - confirm that the grandchild, hard-killed-parent and anchor tests pass natively, and that no
>   process, thread or descriptor is left behind.
>
> Report any failure to Claude verbatim; do not edit Claude's files.
>
> **Q2. Round-4 P3 (N4 binding) and P4 (one local commit, no push)**, exactly as written in the
> round-4 handoff, against v1.3. P4's scope adds:
> - the v1.3 handback and this handoff;
> - your v1.2 native review and its JSON;
> - the latest RUNNING-LOG;
> - the 6 changed v1.3 files.
>
> If Q1 fails, stop: make no binding and no commit, and hand back the failures verbatim.
>
> **Exclusions** are unchanged:
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
