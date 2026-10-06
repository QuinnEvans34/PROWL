# Claude handback: `sizing_v1.3` macOS process-group repair (2026-10-06)

**For phone screens:** this answers the native failure in
`operations/CODEX-S2-V1.2-NATIVE-REVIEW-2026-10-06.md`. Native macOS Python 3.12.13 has no
`os.waitid`. v1.2's fallback then reaped the group leader before the group kill, so a grandchild
survived and two tests failed.

v1.3 replaces that mechanism with a portable **group anchor**. It needs no `waitid` and never
signals a group whose pinning process has been reaped.

Tests (Linux, Python 3.11.15):
- 160 sizing tests: 159 passed, 1 skipped as root;
- the full retrieval suite: 341 passed, 1 skipped, 7 times out of 7;
- one test simulates macOS by deleting `os.waitid`.

On the device's Python 3.10.12, a functional probe exercised the `preexec_fn` path: the
grandchild was killed, no drain thread was left and the run took 0.52 s.

**New code identity:** `791be77ffc96c17aaaf23a8b588c52bf8db1a82ddaa959d41ad217da318f4d53`
(tool version `sizing_v1.3`).

Nothing was downloaded, signed or committed, and no network was used.

## The mechanism (`parser._GroupAnchor`)

1. **Start the anchor.** It is a tiny Python process started in a new process group: `process_group=0`
   on Python 3.11 and later, otherwise `preexec_fn=os.setpgid(0, 0)`. Both keep it in the same
   session as the parent. It blocks reading a stdin pipe from the parent.
2. **Join its group.** The parser child joins the anchor's group (`process_group=<anchor pid>`), and
   so do any grandchildren it starts.
3. **Pinning.** The anchor is reaped only after the group is killed. While it is unreaped, alive or
   a zombie, its PID pins the group ID, so the one `killpg(anchor_pid, SIGKILL)` can never reach an
   unrelated process. The parser child is reaped normally with `poll()`; the `waitid` code is
   removed.
4. **Kill exactly once per run.** On the success path the kill happens after the child exits, so
   leftover grandchildren die and the pipes reach end of file before the drains are joined. In
   `finally` the kill is a no-op if it already ran. The anchor is then reaped.
5. **Parent death.** If the parent dies, even by SIGKILL, the anchor's stdin reaches end of file and
   the anchor runs `killpg(0, SIGKILL)`. The parser and any grandchildren never outlive the
   watchdog. The child's own `parent_lost` stop stays as a second layer.
6. **Launch failure.** If the parser child cannot be launched, the anchor is killed and reaped.

Also changed:
- **CLI signal handling** (`runner.install_signal_handlers`) now covers SIGQUIT and SIGTSTP as well
  as SIGTERM, SIGINT and SIGHUP. Ctrl-Z ends the run as `interrupted` instead of suspending a parent
  whose child would keep running unwatched.
- **Journal writes** (`journal.signals_deferred`) defer the same five signals.

Unchanged:
- bounded diagnostics (1 MiB per stream, 64 KiB tail, no files);
- drain-owned descriptors;
- the RSS, time and periodic checks;
- the `fsio` contract, caps and run S rules;
- the CLI refusal.

## Files (6 changed; the other 16 pins are unchanged from v1.1 and v1.2)

| Path | SHA-256 |
|---|---|
| `src/retrieval/sizing_v1/__init__.py` | `edc6a0f62cd69bd5d51f92ce1e04916e9c27c9d0916937d79fd74fafeb022fdf` |
| `src/retrieval/sizing_v1/parser.py` | `b8f6dc8db2fc3e353fb050af0f59ca9e6e0390ee1b5edea1489132c6255953f6` |
| `src/retrieval/sizing_v1/runner.py` | `4d1b9e79648a9b525ce49afb353502bb13f9e8a82abd5427d142bc4dc8508c1e` |
| `src/retrieval/sizing_v1/journal.py` | `4c94749c1b1cc74dd22c3bc6da6eb0d51cf56679913c630a792b62f4372c026a` |
| `tests/retrieval/test_sizing_v1_parser.py` | `bd58f66550e1245139ca5f53ac3198308ff4f41638409a9c5b8389c78f0a7853` |
| `tests/retrieval/test_sizing_v1_journal.py` | `ddee36ca812ab4050161af1b229b6b69b5c9ad34e32da27c7e29964d2473274c` |

Unchanged:
- `fsio.py` `d2c6db41…`, `listings.py` `ad25719e…` and `transfer.py` `fb8c159a…`;
- the CLI `e433bf9d…`;
- the listings `6d06cd47…`, runner `cad03a10…` and transfer `b1de4cf7…` tests;
- the 9 fixtures, as in the original handback.

All were verified on the device, where the code identity also computed to `791be77f…`.

## Tests added or changed

- **Group kill:** it targets the anchor's group exactly once, while the anchor is unreaped, on both
  the success path and the memory-cap path. This replaces the v1.2 test that failed on the Mac.
- **Simulated macOS:** with `os.waitid` deleted, the grandchild-cleanup test passes.
- **Shared group:** the parser child and the grandchild both run in the anchor's group, not the
  parent's.
- **Launch failure:** the anchor is reaped.
- **Hard-killed parent:** after the parent is killed with SIGKILL, the parser child dies within
  seconds.
- **CLI handlers:** they cover SIGQUIT and SIGTSTP.
- **Mutation checks:**
  - removing the success-path group kill fails the grandchild tests;
  - removing the anchor's parent-death kill fails the hard-kill test.

## Independent review

The same Claude reviewer subagent ran round 8 with no network and no edits. It found nothing at
MEDIUM or above.

It verified:
- the group pinning holds without `waitid`;
- the anchor dying early is safe, because as a zombie it still pins the group;
- `setpgid` across processes in the same session is legal;
- no descriptors, threads or processes leaked over 30 runs;
- nothing from rounds 1–7 regressed.

Its LOW items:
- a hard-killed parent orphaned the parser: fixed by the anchor's parent-death kill, with a test;
- Ctrl-Z and Ctrl-\\ left the parser unwatched: fixed by the signal handlers, with a test;
- a timing-test margin: already widened in v1.1.

## What Codex needs

Repeat the native qualification:
- `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1` (expect 160 collected);
- the full `tests/retrieval` (expect 342 collected).

Confirm the identity `791be77f…` and all 22 pins. Then continue N4 and the approved local commit,
as in round 4.

**Stop point:** nothing is dispatched. Run S is not signed or run.
