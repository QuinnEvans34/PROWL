# Claude handback: `sizing_v1.1` filesystem hook (2026-10-04)

**For phone screens:** the filesystem hook Quinton approved ("Claude adds the hook first") is in
place. Every read, write, list, create, lock and delete that `run_sizing` performs in the scratch,
receipts and fallback areas now goes through an injected `SizingFs`. The parser child receives
only file descriptors, never paths.

Tests (Linux, Python 3.11.15):
- 144 sizing tests: 143 passed, 1 skipped as root;
- the full retrieval suite: 325 passed, 1 skipped, in 10 runs out of 10 after a timing margin was
  widened (see Review);
- a bypass detector that fails the run on any direct filesystem call in the areas, which I
  mutation-checked.

**New code identity:** `df585e2b10a69f55e24db8cc0f96822151a43d52be15ad5bb4917bd9a0a24d4e`. It
replaces `814b89c5…`, so the native S2 qualification must be re-run.

Not changed:
- the CLI, which still refuses execution;
- any cap, check, journal rule or run S rule;
- `listings.py`, the CLI script and the fixtures.

Nothing was downloaded, signed or committed, and no network was used.

## Authority

- Quinton, 2026-10-04: "Claude adds the hook first". Logged in RUNNING-LOG.
- Design: `CLAUDE-S2-IO-HOOK-PROPOSAL-2026-10-04.md`, SHA `270436ae…`.
- Context: item 4 of Codex's S1-S2-BINDING-V1.
- `fsio.py` is one new file inside the Claude-owned `src/retrieval/sizing_v1/`. No other path was
  touched.

## Files

| Path | SHA-256 | Change |
|---|---|---|
| `src/retrieval/sizing_v1/__init__.py` | `3eec5d35e8cf5470af53bbea177f11024dd5db801a25a0291cefbbe73311789d` | Tool version `sizing_v1.1`; docstring |
| `src/retrieval/sizing_v1/fsio.py` | `d2c6db413c72b4b54169a316410036aab8fa58218081f16814a89d8557714705` | **New:** `SizingFs` contract, `PlainFs`, `check_rel`, `LockHeld`/`LockUnsupported` |
| `src/retrieval/sizing_v1/journal.py` | `90b52ab491a8cea11eb87d99129eabbd561847a8c8475f0d7dc8db8abe270cd5` | Journal, lock and prior-run proof go through `fs`; any hook exception on write moves to the fallback |
| `src/retrieval/sizing_v1/parser.py` | `a2081337d8a9516090acdfb722c1e9ee47e7509d9d5243ea568ed4adeeb317f8` | `parse_stream` on file objects; child gets descriptors and runs `check_handover_fds`; up to 2 missing RSS readings tolerated |
| `src/retrieval/sizing_v1/runner.py` | `8f42f526164a2a412859a104ca9a19d8bf0af12286914d2791a57cde6df782bf` | `run_sizing(..., fs=None)`; checks `fs.roots()`; parent writes the manifest; partial charge via `fstat` |
| `src/retrieval/sizing_v1/transfer.py` | `fb8c159abd6fada2f1c9160c85e72c61a602c329090900f1a33656d13ff2cb1a` | `ScratchDir`; `fetch` refuses plain-path targets |
| `src/retrieval/sizing_v1/listings.py` | `ad25719ee617bdbd19d54748fa7ddae0e5330fa15f6a340e104c105b581e3d17` | unchanged |
| `scripts/retrieval/run_s_sizing_v1.py` | `e433bf9df28619c46fc82512e2a6ceb46374ea853d8eef7f21df67e2a7b97c15` | unchanged |
| `tests/retrieval/test_sizing_v1_journal.py` | `3c4c2218b528016f5253594e7ed494333af87e6544bb7207dfb97fa0be384e29` | Calls adapted to `fs`; same oracles |
| `tests/retrieval/test_sizing_v1_listings.py` | `6d06cd475085a34298b0ee56a760555ab5de63ae2a72a3ab75297c5cafda53f2` | unchanged |
| `tests/retrieval/test_sizing_v1_parser.py` | `b181314332e0f3479ccb64018dbcea8d9c0d6b4c5a84363e4d09c83edf6a9c33` | Launcher calls take file objects; new handover, descriptor and missing-reading tests |
| `tests/retrieval/test_sizing_v1_runner.py` | `cad03a1036390d7a22679d4f4684cff3eead9ec0c4b49ca7683837d251503424` | New `GuardFs` bypass detector and hook-failure, lease, read-ahead and identity tests |
| `tests/retrieval/test_sizing_v1_transfer.py` | `b1de4cf728cf6ca978d372c42b6bcfb1a5c622d4e98b70cba0118cd258037dca` | `ScratchDir` targets; plain-path refusal; wider timing margins |
| `tests/retrieval/fixtures/sizing_v1/*` (9 files) | unchanged; pins are in `CLAUDE-S2-HANDBACK-2026-10-03.md` | — |

All hashes were verified identical on the device. `py_compile` passes under Python 3.10.12, and
the code identity computed on the device matches.

## The hook contract

The contract is in the `fsio` docstring; this is a summary for the binding.

- **Areas:** `scratch`, `receipts` and `fallback`. Relative names are a bare component, or
  `sizing-<run_id>/<bare>` (`check_rel`). There is no traversal.
- **Methods:**
  - `roots()` is checked against the signed config before anything else;
  - `display`;
  - `mkdir_exclusive`;
  - `create_exclusive`: a new, empty, regular file with a real `fileno`;
  - `open_read`: positioned at 0;
  - `list`: all entry types; raises rather than skipping;
  - `fsync_dir`;
  - `lock`: `LockHeld` only when another holder has it, otherwise `LockUnsupported`; returns an
    object with `release()`;
  - `remove_own_empty(area, rel, fh)`: device, inode and size checked against the open handle.
- **Errors:** `FileExistsError` for a collision, `OSError` otherwise. Any other `Exception` is still
  treated as a failure.
- **Guards apply when a file is opened.** The parser child reads and writes the passed descriptors
  directly. It first checks that both are regular files, that the output is empty and that they
  are not the same file, then rewinds both. So a guarded file object's `write` or `close` does not
  see the child's bytes, and `close` must not truncate or commit by name.

## Test evidence

| Where | Command | Result |
|---|---|---|
| Cloud workspace (Linux, Python 3.11.15, expat 2.6.1) | `python3 -m pytest -q tests/retrieval -k sizing_v1` | 143 passed, 1 skipped (root) |
| Same | `python3 -m pytest -q tests/retrieval` | 325 passed, 1 skipped, in 10 of 10 runs (8 confirmed after the final margin change) |
| Device VM | `py_compile`, Python 3.10.12 | compiled |
| **Quinton's Mac** | `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1` | **Not run.** Required: the code identity changed |

**Bypass detector.** `GuardFs` plus the `no_bypass` fixture patch `open`, `os.open`, `mkdir`,
`unlink`, `remove`, `listdir`, `scandir` and `rmdir`. Any such call on a path under an area root
that does not come through the hook fails the test. The detector runs over a full invented run
with both the in-process and the live watchdog launcher, and over a primary-loss run.

I mutation-checked it: a direct manifest `open` and a direct `glob` of the fallback were both
caught. The child-rewind and handover tests also fail if the `lseek` is removed.

**Still outside the hook, by design** (metadata only, no reading or writing of area contents):
- `validate_config` resolves the configured roots and checks upward for `.git`;
- `run_sizing` compares `roots()` using `realpath`;
- the bypass detector does not cover the child process; the descriptor-only handover is asserted
  separately.

## Independent review

The same Claude reviewer subagent did rounds 4 and 5, with no network and no edits.

**Round 4** found no CRITICAL or HIGH findings. It found three MEDIUM ones, all fixed:
- the child could misread after a hook read ahead, and bypassed guards in `write`/`close`: fixed
  with `check_handover_fds`, rewinding and the contract clause;
- a hook exception that is not an `OSError` lost the final status: fixed, as any `Exception` now
  moves the journal to the fallback;
- the contract was too thin: fixed with the full method table and handle-based `remove_own_empty`
  and partial charge.

It also found two LOW issues, both fixed: an `err_file` leak, and a successful parse that could go
uncharged on interrupt.

**Round 5** confirmed all of these and found nothing at MEDIUM or above. It flagged one
timing-sensitive test that failed 2 of 13 runs under CPU load; its margin was widened, and the test
is now recorded as timing-sensitive.

Open LOW items, accepted:
- `PlainFs.remove_own_empty` has a check-then-unlink gap. It is the reference implementation; a
  guarded hook should remove relative to an open directory descriptor.
- A signal in a narrow window can overcharge scratch. That is conservative.

## What Codex needs

- **Re-run the native S2 qualification:** the code identity is now `df585e2b…`.
- **Refresh the pending checkpoint scope:** its S2 pins are the `sizing_v1` ones. Ten files changed
  and `fsio.py` is new, so the commit must use the hashes above.
- **The binding implements `SizingFs`** on the S1 lease, plus `observe()`, and calls
  `run_sizing(config, ..., volume=..., fs=...)`. Claude's files are not to be edited.

**Stop point:** nothing is dispatched. Run S is not signed or run.
