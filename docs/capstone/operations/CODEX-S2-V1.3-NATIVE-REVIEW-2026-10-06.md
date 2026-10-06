# Native S2 v1.3 review — October 6

**Q1 passes.** This supersedes v1.2's failed native acceptance, without deleting or rewriting that
failure evidence. No Claude-owned file was edited by Codex.

Exact commands and native output:

```text
.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1
160 passed, 182 deselected in 5.25s

.venv-prowl/bin/python -m pytest -q tests/retrieval
342 passed in 5.79s
```

Tests ran offline on macOS with `.venv-prowl` Python 3.12.13, bytecode and pytest cache writes
disabled. No skips. Identity is
`791be77ffc96c17aaaf23a8b588c52bf8db1a82ddaa959d41ad217da318f4d53`.
All 22 pins, including six v1.3 replacements and 16 retained pins, matched before and after
qualification. The complete inventory and verbatim outputs are in
[the qualification JSON](CODEX-S2-V1.3-QUALIFICATION-2026-10-06.json).

The grandchild, portable anchor and hard-killed-parent tests pass natively. This Mac lacks
`os.waitid`; v1.3's acceptance depends on its portable anchor, not a claimed WNOWAIT capability.
A separate instrumented in-process lifecycle run reported `5 passed, 41 deselected in 0.59s`:
17 tracked child processes, zero live tracked children, zero extra descriptors and zero surviving
drain threads. These are observations of those tested executions, not a guarantee about unrelated
processes on the Mac.

Sources: [Claude's v1.3 handback](../retrieval/CLAUDE-S2-V1.3-HANDBACK-2026-10-06.md),
[round-5 dispatch](../retrieval/CLAUDE-HANDOFF-TO-CODEX-2026-10-06-R5.md), October 6
[RUNNING-LOG](../retrieval/planning/RUNNING-LOG.md), and the preserved
[v1.2 native failure](CODEX-S2-V1.2-NATIVE-REVIEW-2026-10-06.md).

Q1 enables the separately approved N4 implementation and conditional local preservation. It does
not enable Run S, a signature, network acquisition, S3, a database or follow-on work. The binding's
own acceptance and missing-volume prerequisite are recorded in
[the binding results](PLAN07-BINDING-RESULTS-2026-10-06.md).
