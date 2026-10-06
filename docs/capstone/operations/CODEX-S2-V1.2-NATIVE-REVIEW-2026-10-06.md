# S2 v1.2 native handback — October 6, 2026

**P1 finished; P2 failed; P3 and P4 remain incomplete.** D-350 records Quinton's October 5 local
commit approval and October 6 round-4 dispatch. Native sizing: **153 passed, 2 failed**, 182
deselected, 155 selected. Full retrieval: **335 passed, 2 failed**, 337 selected. Neither native
run skipped tests. No binding backend, external rehearsal, commit or push was performed.

## Exact inputs and checks

- Delivered v1.2 identity: `3198b2685709bff92367f0cba6254b09a9269c48837fde7d3dfc4ac61f464203`.
- All **22/22** source/test/fixture pins matched before and after tests and the diagnostic probe:
  three v1.2 replacements, ten other explicit v1.1 rows, nine original invented fixture pins.
  The complete inventory and verbatim outputs are in
  [the machine-readable evidence](CODEX-S2-V1.2-QUALIFICATION-2026-10-06.json).
- Native Mac Python 3.12.13 reports `hasattr(os, 'waitid') == False` and
  `hasattr(os, 'WNOWAIT') == True`. `os.waitid(..., WNOWAIT)` cannot be confirmed: the function
  is absent in this Python build. No runtime, dependency or environment package was changed.
- The initial sandbox sizing attempt reported 142 passed/13 failed; its `ps` RSS monitor was
  denied. Both required suites were then run outside that sandbox with the native monitor. Those
  two native failures remain after removing the sandbox restriction; they are not attributed to
  the sandbox's monitor denial.
- Tests used `PYTHONDONTWRITEBYTECODE=1`, disabled pytest cache writes and `--tb=short` to preserve
  concise verbatim failures. Invented disposable test data only; no network or live sizing job.
- [The v1.2 handback](../retrieval/CLAUDE-S2-V1.2-HANDBACK-2026-10-04.md) matches logged SHA
  `9e5845e2b91f84ef4dfc2c677ee94c47dfdaf23655a348c07c37a42c6d90e2b3`.
  [Round-4 handoff](../retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-05-R4.md) matches
  `d323018864bcddb1d3909d9042bf15fa6955f5b920783ba6c895af47adb06134`.
  RUNNING-LOG SHA stays `1eeac0961dfb18d4a9d98766fa8f262fea0b9145edb4baa16eadb7a2d0f375e4`.
  Claude's files were not edited.

## Root cause and bounded process probe

`parser._exited` catches the absent `os.waitid` and calls `proc.poll()`, which reaps the exited
leader. `_kill_group` then returns because `proc.returncode` is already set. The process group is
not killed. The native test expecting one group kill observes zero; the grandchild test fails
with `diagnostics_pipe_held` before reaching its own cleanup assertions.

One additional invented native probe exercised that same failed path without patching Claude's
code. It failed with `diagnostics_pipe_held` after 10.090 seconds. `/dev/fd` inventory showed no
extra descriptors; no `run-s-diag-drain` thread remained alive in that probe process. Its recorded
60-second sleeper grandchild **was still running**. Codex verified the recorded child command and
terminated only that still-live probe child with SIGKILL. This is narrow evidence of descriptor and
thread closure on the failed path, not successful group cleanup or qualification. Other tests'
ordinary descriptor/overflow/timeout checks passed; no universal absence of leaks is claimed.

## Copyable report and concrete request for Claude

Please repair the macOS process-group lifecycle in the Claude-owned parser and tests. The native
Mac Python 3.12.13 has `WNOWAIT` but no `os.waitid`. The fallback reaps the leader before group
cleanup, so `_kill_group` skips the kill. Do not remove/skip the two tests, weaken the acceptance
criteria, or simply signal a group after its leader has been reaped: that loses the PID-reuse
protection. Provide a portable, tested mechanism that safely keeps the intended group identity
valid until cleanup, stops/reaps descendants, and closes diagnostic drains on every exit. Keep
bounded concurrent diagnostics, RSS/time/volume checks, no temporary diagnostic files, descriptor
handoff, caps and CLI refusal. Publish a fresh exact code identity, complete pins and handback.
Codex will repeat the native qualification before implementing the guarded binding.

Both native failures and their output follow verbatim. They are also stored verbatim in the JSON
record. Direct delivery was attempted by inspecting Claude's native app; it exposed only an empty
accessibility container, with no identifiable destination conversation. No message was sent.
Quinton can relay this section or direct Claude to this shared file. No follow-on phase dispatched.

### Native sizing output (verbatim)

```text
........................................................................ [ 46%]
...F..F................................................................. [ 92%]
...........                                                              [100%]
=================================== FAILURES ===================================
_____ test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives _____
tests/retrieval/test_sizing_v1_parser.py:421: in test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives
    rc, out, err, _ = P.run_with_watchdog([sys.executable, '-c', code], probe=P.PsMemoryProbe(), poll=0.01,
src/retrieval/sizing_v1/parser.py:598: in run_with_watchdog
    raise ParserGuard('parser child pipes are still held open after exit', reason='diagnostics_pipe_held')
E   src.retrieval.sizing_v1.ParserGuard: parser child pipes are still held open after exit
_____________ test_group_kill_happens_once_and_only_before_reaping _____________
tests/retrieval/test_sizing_v1_parser.py:477: in test_group_kill_happens_once_and_only_before_reaping
    assert len(calls) == 1
E   assert 0 == 1
E    +  where 0 = len([])
=========================== short test summary info ============================
FAILED tests/retrieval/test_sizing_v1_parser.py::test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives
FAILED tests/retrieval/test_sizing_v1_parser.py::test_group_kill_happens_once_and_only_before_reaping
2 failed, 153 passed, 182 deselected in 14.42s
```

### Full native retrieval output (verbatim)

```text
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 64%]
.........................................F..F........................... [ 85%]
.................................................                        [100%]
=================================== FAILURES ===================================
_____ test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives _____
tests/retrieval/test_sizing_v1_parser.py:421: in test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives
    rc, out, err, _ = P.run_with_watchdog([sys.executable, '-c', code], probe=P.PsMemoryProbe(), poll=0.01,
src/retrieval/sizing_v1/parser.py:598: in run_with_watchdog
    raise ParserGuard('parser child pipes are still held open after exit', reason='diagnostics_pipe_held')
E   src.retrieval.sizing_v1.ParserGuard: parser child pipes are still held open after exit
_____________ test_group_kill_happens_once_and_only_before_reaping _____________
tests/retrieval/test_sizing_v1_parser.py:477: in test_group_kill_happens_once_and_only_before_reaping
    assert len(calls) == 1
E   assert 0 == 1
E    +  where 0 = len([])
=========================== short test summary info ============================
FAILED tests/retrieval/test_sizing_v1_parser.py::test_grandchild_holding_pipes_is_killed_and_no_drain_thread_survives
FAILED tests/retrieval/test_sizing_v1_parser.py::test_group_kill_happens_once_and_only_before_reaping
2 failed, 335 passed in 14.86s
```

## Files, preservation and exact next starting point

This chat appended D-350 and added this review, its JSON evidence and
[the blocked checkpoint inventory](PLAN07-V12-PENDING-CHECKPOINT-2026-10-06.json). No changes to
Claude's source/tests/planning, S1, shared contracts, imaging cohorts/holds, roots, registry or
historical experiment requests. The current local commit remains `edf5e47` (67 reviewed files;
no push), with prior imaging preservation `5856fdc`. Course-assignment work in the other chat and
unrelated untracked documents/binaries are excluded from this packet's candidate scope.

P3 requires a qualified exact hook; P2 failed, so no unqualified binding/rehearsal was implemented.
P4 says “Once P2 passes”; that condition is unmet, so the approved local commit was not made.
The pending list is a measured review inventory, not a staging authorization or an accepted code
snapshot. Recheck every hash after Claude's repair; never substitute fresh pins into old evidence.

**No new Quinton decision is needed for the prescribed repair/qualification route.** After a fresh
Claude handback, repeat both native commands and lifecycle/leak checks, then implement/qualify N4
under the approved packet, freeze the exact verified scope and make the one conditional local
commit. Run S signatures/execution, S3, downloads, P4/P5, installation/database work and D-085
producer migration remain excluded. Stop here.
