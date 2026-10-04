# Plan07 M1–M6 handback — stop point

**Finished:** S1 storage setup/qualification, native S2 tests, two exact cleanup deletions and the
approved decision records. Integration packets and a fresh checkpoint list are prepared.
**Checks:** 49 S1 tests; **131 native sizing tests; 313 full retrieval tests, no skips**. S2's 21 file
hashes and code identity814b89c5…37aa match Claude's handback. **Run S is not ready to sign/run.**
**Next:** review **S1-S2-BINDING-V1**, then its invented/native binding qualification, S3 capacity
and S4 frozen-copy signature. No follow-on task was dispatched. Stop here.

## What finished, in order

R-01 came first: prior local preservation commit `5856fdc9d4f6b2318c918505576244f324247f12`
contains 625 reviewed files, Monday wording is settled and nothing was pushed. D-335 remains the
latest imaging experiment; no worker was active at the native storage preflight.

| Item | Result |
|---|---|
| M1 | Appended D-341–345, citing the exact October3 RUNNING-LOG approval entry. S1/S2 dispatch, watchdog, two deletions and three integration choices recorded; no Run S signature inferred |
| M2 | Separate S1 adapter/setup CLI and 49 invented tests; four approved areas created after tests passed. The 61,440-byte invented probe is preserved; exclusive creation, append/reopen/fsync, competing writer refusal and terminal-only fallback pass |
| M3 | Native requested sizing command: 131 passed / 182 deselected in 3.80 s. Full retrieval: 313 passed in 3.67 s. Python 3.12.13 / expat 2.7.4. All 21 Claude pins and the code identity match; no failures to forward |
| M4 | Rechecked regular types, 114 / 0 bytes and full L1–L6 hashes; deleted only `_to_delete/claude-RUNNING-LOG.md.tmp` and `.git/index.lock.stale-claude-20260928`. No active Git lock removed |
| M5 | Shared offline-contract packet and named/pinned P4a-B1 packet drafted; D-085 amendment accepted/recorded with denominators, rights, tokenizer and development-only role |
| M6 | Added S2's 21 files, original handback, R2 handoff and current S1/decision/docs/navigation changes to a fresh pending scope based on 5856fdc; hashes verified, no staging/commit/push |

## Files changed and evidence

Shared files: `AGENTS.md`, `docs/capstone/DECISIONS.md`, `operations/CURRENT-CHECKPOINT.md`.
S1 new files: `src/operations/literature_storage_v1.py`,
`scripts/diagnostics/literature_storage_setup_v1.py`, `tests/test_literature_storage_v1.py` and
two invented fixture files. New operations documents: this handback, S1 results, binding follow-up,
shared-contract packet, D-085 amendment, P4a packet and pending-checkpoint Markdown/JSON.
The exact list/hashes are in [the pending checkpoint](PLAN07-PENDING-CHECKPOINT-2026-10-04.md).

Claude's current RUNNING-LOG and new S2 files were read and listed, never edited. The existing P3
producers/tests/schemas/design and imaging producers stayed byte-identical to the prior commit.
The contract README's stale status is identified for its future scoped update; not rewritten here.
S2 handback SHA `07040e5712adf9b364017ac17f34ab39e1d9a98d0e84dd72b5e2c552e2704ab3`;
R2 handoff SHA `7cb99b807633f107525d8cc698c44accdc225ce4cd743f6d95bffc0a4ff79de7`.
Tool identity `814b89c5dac055b59df4c28ff14cca008d7831d63ba31b418e380831fad837aa`.

Native S1 primary/fallback journals survive reopen and fsync on distinct verified APFS volumes;
additional read-only flock contention passes on both. Injected primary failure does not detach the
drive or write payload on fallback. [S1 results](PLAN07-S1-RESULTS-2026-10-04.md) names the paths,
budgets, observations and Git-ignored receipts. Registry unchanged, `scientific_runs_enabled: false`;
no checkpoint-backup writes, cap reset, dataset/source activation, model calls or downloads.

These results establish the tested offline/native mechanics. They do **not** prove live NLM listing
compatibility, proxy support or a real outbound TLS handshake. S2 socket-watch tests use local
synthetic sockets; no internet TLS transfer was exercised. No real literature was read or fetched.
S2 still uses plain path I/O and refuses CLI execution; binding confinement qualification is owed.
No new full-project suite/portability pass or G6/P4/P5 closure is claimed. The earlier 2,933 fast / eight
local-evidence baseline belongs to 5856fdc; this task adds 49 S1 + 131 S2 tests and verifies its scoped suites.

## Decisions still needed from Quinton

- Dispatch a concrete S1-S2 binding/qualification scope when ready. The proposed scope is
  [S1-S2-BINDING-V1](PLAN07-S1-S2-BINDING-FOLLOWUP-2026-10-04.md); no new request to Claude was sent.
- Review the [shared-contract packet](PLAN07-SHARED-CONTRACT-PACKET-2026-10-04.md) before code;
  Claude separately scopes migration of the [approved metric policy](PLAN07-D085-AMENDMENT-2026-10-04.md).
- P4a later: review [the draft](PLAN07-P4A-INSTALL-PACKET-2026-10-04.md) after its shared Docker
  inventory/settings gap is resolved. Native macOS denied reading settings; existing engine socket
  is absent. No install/global setting is approved; no runtime was started to inspect it.
- Explicit new local-commit authorization for the current pending checkpoint; push remains separate.
  The old preservation approval was already consumed by5856fdc and does not cover this new scope.
- S3/S4 and a later exact launch only after binding acceptance. Watchdog/HTTP reserve/expansion and
  partition-format details must be disclosed in the frozen signed copy; current tests do not sign it.

## Exact next starting point

Read S1 results and S1-S2-BINDING-V1, review the capability/lease-to-`run_sizing(..., volume=...)`
boundary, and freeze the invented binding qualification packet. Resolve any needed S2 file/lock
interface change with Claude through an explicit request, preserving its ownership. Do not start
from a live sizing command. Imaging duration/coverage/FP planning remains visible in the Week1
queue, independently requiring a fresh bounded proposal. This handback dispatches nothing else.
