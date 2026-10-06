# Plan 07 v1.3 / binding handback — October 6

**Finished:** native v1.3 qualification; guarded binding implementation; invented unit/integration
checks and full temporary-volume rehearsal executor. Preserve this verified scope in the approved
single local checkpoint, no push. **Pending:** the actual APFS-domain rehearsal; PROWL-Data is not
mounted. N4 is not closed, and no live sizing is enabled.

## Checks and files

- Sizing: `160 passed, 182 deselected in 5.25s`.
- Full retrieval: `342 passed in 5.79s`.
- Supplemental lifecycle: `5 passed, 41 deselected in 0.59s`; 17 tracked children, no live tracked
  children, extra descriptors or surviving drain threads. Grandchild, hard-killed-parent and
  portable-anchor checks pass on this Mac, which lacks `os.waitid`.
- Final combined binding/S1/shared/retrieval: `626 passed in 14.82s` (62 new binding, 49 S1,
  173 shared and 342 retrieval); no skips. Contract gate: 198 passed, two existing warnings.
- All 22 v1.3 pins and identity `791be77f…` match. The registry and original S1 source/fixture
  inventory remain unchanged. Codex edited no Claude source, tests or planning file.

See [native review](CODEX-S2-V1.3-NATIVE-REVIEW-2026-10-06.md),
[exact native qualification](CODEX-S2-V1.3-QUALIFICATION-2026-10-06.json),
[binding results](PLAN07-BINDING-RESULTS-2026-10-06.md),
[binding evidence and runtime pins](PLAN07-BINDING-QUALIFICATION-2026-10-06.json), and
[the exact checkpoint scope](PLAN07-V13-LOCAL-CHECKPOINT-2026-10-06.json).
The scope includes the six Claude v1.3 replacements, v1.2/v1.3 handbacks and R4/R5 dispatches,
latest unedited RUNNING-LOG, D-350 and our reviews/binding/tests/fixture/evidence. Preserve v1.2's
failure as historical evidence. Other chat imaging/course files, AGENTS, hours log, registry,
external areas and unrelated files are excluded. The checkpoint object SHA is verified after the
single commit and recorded in ignored `outputs/prowl/PLAN07-V13-LOCAL-PRESERVATION-20261006/commit-result.json`.

## What needs Quinton

The exact approved external drive must be available for the actual-domain rehearsal. If it remains
unavailable, retain this incomplete N4 status; local verified preservation can still finish under
the packet's explicit incomplete-P3 allowance. No Run S signature, sizing launch or further plan
dispatch is requested or implied. Human working hours were not supplied; agent time is excluded.
The canonical Trello card is updated at handback and remains open for the missing prerequisite.

## Exact next starting point

[Binding results](PLAN07-BINDING-RESULTS-2026-10-06.md), “Exact next starting point”: reverify the
same primary UUID and internal failure domain, current registry/runtime pins, cumulative contents
and imaging-idle state; prepare a fresh invented request in the three qualification children;
freeze hashes, execute once and inspect locks/bytes/counters/sentinels/process closure. The two
failed local preparations are retained and no external request was consumed. Do not substitute a
mount, create top-level sizing histories, weaken budgets or treat temporary-volume integration as
actual APFS acceptance. Stop here; no follow-on dispatch.
