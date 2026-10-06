# Claude handback: `sizing_v1.2` bounded parser diagnostics (2026-10-04)

**For phone screens:** this answers Codex's request in `operations/PLAN07-S2-IO-HOOK-REVIEW-2026-10-04.md`
("bounded-diagnostics mode").

The parser watchdog no longer creates any diagnostic file.
- **Bounded draining:** two threads drain the child's stdout and stderr into memory, accepting at
  most 1 MiB per stream and keeping a 64 KiB stderr tail. Overflow stops the child with
  `diagnostics_overflow`, and no manifest is written.
- **Checks keep running:** the RSS, time and periodic checks stay active under pipe pressure.
- **Child processes:** the child runs in its own process group, which is killed before the child
  is reaped, so a grandchild cannot keep the pipes open. If the pipes are still held after that
  kill, the parse fails with `diagnostics_pipe_held`. If the watchdog parent dies, the child stops
  itself (`parent_lost`).

Test results (Linux, Python 3.11.15):
- 155 sizing tests: 154 passed, 1 skipped as root;
- full retrieval suite: 336 passed, 1 skipped, in 9 of 9 runs.

**New code identity:** `3198b2685709bff92367f0cba6254b09a9269c48837fde7d3dfc4ac61f464203`.
It replaces `df585e2b…`, so the native test run must be repeated.

Unchanged: the `fsio` contract, the journal, transfer, runner, CLI, caps and run S rules.
Nothing was downloaded, signed or committed, and no network was used.

## Files (3 changed; the other 19 pins are unchanged from the v1.1 handback)

| Path | SHA-256 |
|---|---|
| `src/retrieval/sizing_v1/__init__.py` | `d7ad3280d35d1cf7f0f9cc048b02b3826d7930b6744431867691845ad044e541` (version `sizing_v1.2`) |
| `src/retrieval/sizing_v1/parser.py` | `2e4546f1d75f3d9cfdc7b782ebcabad7ebd3c9969c422af64c9176aabf6c7f76` |
| `tests/retrieval/test_sizing_v1_parser.py` | `112e915c47a86a65219375e86b15a8e67621f82684075fc403bcbc0dfbc23c25` |

The unchanged pins are:
- `fsio.py` `d2c6db41…`, `journal.py` `90b52ab4…`, `listings.py` `ad25719e…`, `runner.py` `8f42f526…`
  and `transfer.py` `fb8c159a…`;
- the CLI `e433bf9d…`;
- the tests for journal `3c4c2218…`, listings `6d06cd47…`, runner `cad03a10…` and transfer `b1de4cf7…`;
- the 9 fixtures, as in the original handback.

I verified on the device that all three changed files match and that the code identity there is
`3198b268…`. On the device's Python 3.10 the files parse cleanly.

## Behaviour (`parser.run_with_watchdog`)

- **No files.** stdout and stderr are pipes, read concurrently by two `_BoundedDrain` threads into
  memory. A test makes `tempfile` fail, and the run still works.
- **Limits.**

  | Constant | Value | Meaning |
  |---|---|---|
  | `DIAG_STREAM_LIMIT` | 1 MiB | Most bytes accepted per stream |
  | `DIAG_STDERR_TAIL` | 64 KiB | stderr bytes kept; the tail stays current after overflow |
  | `DRAIN_SELECT_SECONDS` | 0.1 s | How long a drain waits for data before rechecking its stop flag |
  | `DRAIN_JOIN_SECONDS` | 5 s | How long the parent waits for a drain to finish |

  After overflow, bytes are still read and discarded, so the child never blocks on a full pipe.
  Overflow is detected within one poll interval (about 0.5 s live). The child is then killed,
  the parse fails with `diagnostics_overflow`, and the parent writes no manifest.
- **Descriptor ownership.** Each drain duplicates its pipe's descriptor and closes the original file
  object at once. Only the drain thread closes the duplicate, at end of file or on stop. So the
  main thread never closes a descriptor a live drain might be reading, and a reused descriptor
  number is never read by a stale thread.
- **Process group.** The child is started with `start_new_session=True`. The whole group gets
  SIGKILL exactly once, while the leader is still unreaped:
  - exit is detected with `waitid(..., WNOWAIT)`;
  - if `WNOWAIT` is unavailable, the code falls back to `poll()`. The group kill is then skipped,
    and a pipe still held by a grandchild fails closed as `diagnostics_pipe_held`.
- **Parent loss.** The child records its parent PID and stops with `parent_lost` if it is
  re-parented. That bounds an orphaned child if the watchdog itself is hard-killed.
- **Every exit path** kills the group if needed, waits for the child, stops and joins both drains,
  and closes any stream no drain took over.

## Tests added (all invented, no network)

- overflow on stdout and on stderr: the child is stopped and reaped quickly, and no descriptor
  leaks;
- overflow after the child has exited is still a failed parse;
- under pipe pressure, both the periodic check and the memory cap still fire;
- no `tempfile` use;
- descriptors are closed on the success, memory-cap and time-cap paths;
- a failed child leaves no manifest;
- a grandchild holding the pipes is killed, no drain thread survives, and a reused descriptor is
  not read;
- the tail keeps updating after overflow (deterministic, on a pipe);
- a parent-loss stop;
- the group kill happens exactly once per run.

The overflow, leak and close tests were mutation-checked: removing the overflow flag, or the stream
closes, makes them fail.

## Independent review

The same reviewer subagent ran three rounds.

- **Round 6.** One MEDIUM: a grandchild holding a pipe could leave a drain thread reading a reused
  descriptor. It was fixed with the process group and drain-owned descriptors. Two LOW items
  were also fixed: the stderr tail froze after overflow, and a drain could be left unmanaged when
  starting the drains failed.
- **Round 7.** It confirmed the fixes and found nothing at MEDIUM or above. Its LOW items:
  - Two were fixed afterwards and covered by tests: a PID-reuse window (the group is now killed
    before reaping) and an orphan after a hard parent kill (the parent-loss stop).
  - Two were accepted. A grandchild that calls `setsid` itself escapes the group kill; the parse
    then fails closed with `diagnostics_pipe_held`, but the grandchild survives. `select` cannot
    take descriptors at or above 1024, a limit this process never reaches.

## What Codex needs

1. **Re-run the native tests:** `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1`
   (expect 155 collected) and the full `tests/retrieval`. Confirm the identity `3198b268…` and
   that `os.waitid` works with `WNOWAIT` on macOS (the grandchild test exercises it).
2. **Continue N4** (the binding) against v1.2. The diagnostics path is now bounded and needs no
   file.
3. **Commit:** the local commit `edf5e47` holds v1.1. v1.2 changes three files and is
   uncommitted; a new local commit needs Quinton's OK.

**Stop point:** nothing is dispatched. Run S is not signed or run.
