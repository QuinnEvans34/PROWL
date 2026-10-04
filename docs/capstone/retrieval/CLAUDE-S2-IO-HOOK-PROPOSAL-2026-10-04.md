# S2 filesystem hook for the S1 binding: Claude's interface proposal (2026-10-04)

**Status:** a proposal. Nothing is changed. It answers item 4 of Codex's
[S1-S2-BINDING-V1](../operations/PLAN07-S1-S2-BINDING-FOLLOWUP-2026-10-04.md): S2 opens literal
paths, while S1's writer uses no-follow descriptors, and "a wrapper alone does not make every S2
path open a descriptor-guarded write". That assessment is correct. Codex cannot fix it without
editing Claude's files, so Claude proposes the hook. Implementation waits for Quinton's go.

## Every filesystem touchpoint in `sizing_v1` today (code identity `814b89c5…`)

| Where | Operation | Area |
|---|---|---|
| `runner._Run.execute` | `os.mkdir(scratch/sizing-<run_id>)` | scratch |
| `transfer._attempt` | `open(path, 'xb')`, write, `fsync` for each attempt file | scratch |
| `parser.parse_file` (in the child) | `open(src, 'rb')`; `open(out, 'xb')`; manifest `open(..., 'xb')`; `getsize` | scratch |
| `runner._charge_partial` | `exists` and `getsize` on failed parse output | scratch |
| `journal.Journal` | `open(primary, 'x')`, appends, `fsync`; directory `fsync`; `unlink` of own empty file | receipts |
| `journal._switch_to_fallback` | `open(fallback, 'x')`, appends; directory `fsync` | fallback |
| `journal.RunLock` | `os.open(O_CREAT)` plus `flock` | receipts |
| `journal.prior_runs` | `glob` and strict reads of journals; `glob` of `sizing-*` | receipts, fallback, scratch |
| `runner.validate_config` | `exists('.git')` walk up from the fallback | read-only check |
| `runner.code_identity`, `parser.PsMemoryProbe` | reads of the repo and `/proc` | outside the areas |

## Proposed interface (`sizing_v1`, tool version `sizing_v1.1`)

`run_sizing(..., fs=PlainFs(...))`: an injected `SizingFs`. The default `PlainFs` reproduces
today's behaviour exactly, so every existing test keeps its oracle. Paths become
`(area, relative_name)` pairs, with `area` one of `scratch`, `receipts` or `fallback`. Relative
names are single bare components, or `sizing-<run_id>/<bare>`.

| Method | Contract |
|---|---|
| `mkdir_exclusive(area, name)` | Create a directory; fail if it exists |
| `create_exclusive(area, rel)` | Return a writable binary file object (write, flush, fileno for fsync); fail if it exists |
| `open_read(area, rel)` | Readable binary file object (journals, samples, listings) |
| `list(area, prefix, suffix)` | Bare names only |
| `size(area, rel)` / `exists(area, rel)` | Size and existence of the named file |
| `fsync_dir(area, subdir='')` | Make directory entries durable |
| `lock(area, name)` | Exclusive non-blocking lock object with `release()`; "held" vs "unsupported" distinguished |
| `remove_own_empty(area, rel)` | Only for the journal-creation rollback; refuses non-empty files |
| `display(area, rel)` | String for journal events (no I/O) |

**Parser child.** The child receives no paths. The parent opens the source sample with
`open_read`, and the output with `create_exclusive` through the hook, then passes both file
descriptors with `subprocess.Popen(pass_fds=...)`. The child reads and writes only those
descriptors. The parent writes the manifest through the hook. All writes then go through the
binding's descriptor-guarded implementation, including the child's, and the watchdog design is
unchanged.

**Binding (Codex).** S1's adapter implements `SizingFs` on top of its lease and no-follow
descriptors, and provides `observe()` as already specified. S2 keeps its own per-signed-copy lock;
the S1 lease wraps the whole call, as the follow-up proposes.

## Tests Claude would add

- All 131 current tests run unchanged against `PlainFs`.
- A `GuardFs` test double records every call. While a full invented run executes, `builtins.open`,
  `os.open`, `os.mkdir`, `os.unlink` and `glob.glob` are patched to fail, except reads of the
  repository and `/proc`. The run must complete, which proves that no write or listing bypasses the
  hook.
- The child receives only descriptors: a test asserts that no path argument is passed and that the
  output is written through the passed descriptor.
- Injected hook failures each end with the right final status:
  - a create failure gives `scratch_write_failed`;
  - a lock reported as "unsupported" is refused with that reason, not as "held";
  - a list failure refuses the start.

## Effects

- The code identity changes, so the native S2 qualification (Codex M3) must be re-run, and the
  21-file pins replaced.
- No cap, check, journal semantic or run S rule changes.
- Estimated size: about 150 changed lines in `runner`, `transfer`, `parser` and `journal`, plus
  about 15 tests.
- The alternative is that Codex proves confinement around plain paths from outside, for example by
  checking that no symlinks were swapped before and after each operation. That can only detect
  substitution afterwards, never prevent it, so Claude does not recommend it.
