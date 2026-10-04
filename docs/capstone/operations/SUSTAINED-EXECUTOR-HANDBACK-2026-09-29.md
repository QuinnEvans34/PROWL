# D-287 sustained executor verification

Scope: extend the existing qualified expanded executor for one fixed CAP-EXP-006 experiment.
No new dependency, dataset qualification, model/loss implementation, role change or retrieval edit.

## Implementation

- `src/training/localizer.py`: explicit `budget_id=sustained_localizer_v1`, max2400; old100/300
  limits remain for configurations without this identifier. Objective remains balanced CE + Dice.
- `src/training/expanded_executor.py`: exact CAP-EXP-005/006 configuration, cadence and time
  allowlist; unchanged real input/initialization pins. Bound operation must match experiment.
  Emit complete evaluation records as each finishes. Terminal still requires full cadence,
  all referenced checkpoint/export artifacts and matching final metrics.
- `scripts/diagnostics/expanded_localizer_launch.py`: experiment-specific frozen requests and
  supervisor limits. Immediately back up each completed checkpoint, persist backup receipts and
  evaluation files. Final recovery verifies the same artifacts independently of primary reads.
- `tests/test_expanded_executor.py`:10 new tests (including parametrizations). Legacy cap,
  sustained cap/objective ID, altered config/cadence/time/approval/scope refusals, complete CPU
  transaction, evaluation journal, backup callback failure and actual301-update CPU restore with
  exact next-update equality. Existing interruption/export/terminal/refusal checks retained.

No automatic resume introduced. A stopped run preserves completed primary checkpoints,
completed independent backup receipts and evaluation journals; a later continuation needs its own
plan and authorization. Partial exports cannot become a complete terminal. Completed requests remain
single-use. A run is fresh even when a prior checkpoint could technically be restored.

## Native evidence

Initial sandbox suite:1177 passed,2 process-monitor permission failures,2 upstream torch warnings.
Native rerun after adding301-update continuation test: **1180 passed,2 upstream warnings,31.93s**.
Logs and reviewed file hashes: `outputs/prowl/cap-exp-006-qualification-20260929`.

Synthetic MPS transaction: `outputs/prowl/expanded-execution-309a6117-4352-4917-a137-8335451740d5`.
4 invented-data updates; full16/11 invented-role evaluation/export,31 artifacts backed/restored;
step4 recovered in fresh process, primary Python reads blocked, fixed-probe difference0.
100.58s overall; peakRSS1,887,322,112bytes. All request-source/environment and receipt members verified.
Receipt SHA `e42692ed6ac67728fa09c3f317e1ef7a95834ad35da2836e65241e4a69dbf999`.
Source diff reviewed against the retained CAP-EXP-005 source snapshot; only the3 implementation
files listed above changed within its captured code inventory.

## Exact authorized launch

See [design](CAP-EXP-006-LAUNCH-PLAN-2026-09-29.md) and D-287. User authorization covers the next
sustained experiment; exact2400-update parameters were selected and documented by Codex.
Request `expanded-launch-request-bb413397-e1a1-463d-8aba-1edf0887129c`;
SHA `024fb5b495d78a4ad4686846ec113c3ecc9d8c023cd298a189cafc3c304cf01e`.
Approval SHA `d041179d7e7573803348ad393989ce91cc5c82f48bc8050cfb31412e459b695e`.
Run `outputs/prowl/expanded-execution-943d4c6d-29b8-4d85-a2e5-fce579116f59`.
Outcome belongs in the separate experiment-results record; this handback is engineering evidence.
