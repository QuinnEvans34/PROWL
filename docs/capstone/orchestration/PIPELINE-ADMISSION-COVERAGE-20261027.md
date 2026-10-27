# W04-01 pipeline and accelerator admission coverage

October27. **124 CPU tests pass in15.52s**, including24 admission/supervision
checks and the100 prior workflow regressions. Production training, target-admission
and teacher supervision code is unchanged. This qualifies specific control
boundaries; it does not close G3 or authorize another accelerator job.

## Accelerator ownership evidence

The actual `full_training_platform.training_guard` was exercised by isolated CPU
subprocesses on temporary lock files. Tests inject AC outcomes in those subprocesses
only; no GPU work follows acquisition.

- Two contenders are refused while the first process owns the lock.
- Normal release, SIGTERM and SIGKILL are followed by process reaping and successful
  reacquisition of the same lock inode. No lock file is deleted or replaced.
- AC rejection prevents entry into the guarded body and releases ownership.
- Stale text in a lock file does not imply ownership; kernel locking is authoritative.
- Existing actual supervisor/watchdog tests cover successful worker/guardian cleanup,
  resource stops and bounded process-sampling timeout behavior.

A separate nonblocking probe of the real `.mps-profile.lock` reported busy. Its inode,
size and modification time were unchanged. No teacher ownership was displaced.
All328 repository producing pins matched. The teacher supervisor13779/worker15917
were still active after testing, with517 targets completed at the last count.

These tests do not simulate every parent-loss race or prove an accelerator kernel
has stopped. A released lock alone is insufficient to restart after a supervisor
crash: the existing guardian/cleanup evidence must establish that the old worker
and descendants are gone before any new launch.

## Target admission evidence

Invented4×4×4 arrays exercise the existing generated-target admission function and
the optimizer's `TeacherTargetStore`, without importing a model or running an update.
The gate rejects incomplete membership, a protected/nonmatching request, changed
provider identity, reordered cohort, unreaped workers, nonzero exit, wrong payload
dtype/shape/member inventory, mismatched geometry, missing voxel coverage and bad
payload hashes. Correct full inputs reach the store; an explicitly qualification-only
manifest is rejected by the full-training store.

This is not an audit of the live incomplete target directory. It does not establish
teacher scientific quality, unknown development membership, final cohort readiness,
sampling correctness or actual GPU executor recovery.

## Mapping to the approved stage registry

The design authority remains `STAGE-REGISTRY.md`. The smaller offline registry is
an adapter implementation subset, not a replacement stage taxonomy.

| Approved boundary | Current evidence | Remaining integration |
| --- | --- | --- |
| `preflight_roots` | Runner rejects missing/replaced roots and insufficient capacity; target job keeps its separate root/AC/storage guards | Unified production root-preflight artifact and capacity forecast |
| `snapshot_sources` → `build_manifest` → `build_cohorts` | Existing upstream frozen artifacts remain inputs; this turn checks target/provider membership rejection only | Named workflow must bind the owning source/cohort validators and explicit artifact references |
| `build_prepared_cache` → `train_model` | CPU target admission and exclusive-lock control checks pass | Full target inventory, actual provider/sampling, full-executor GPU qualification and frozen launch receipt |
| `infer_autonomous` → `postprocess_measure` → `evaluate_model` | No new evidence in this turn | Autonomous input separation, real inference/recovery and measurement/evaluation qualification |
| Literature build/index/evaluation stages | Existing literature service/admission regressions pass; no rebuild or new evaluation | Versioned full retrieval subgraph remains separate from offline capture validation |
| `select_integration_versions` | Offline adapters bind exact saved manifest and response pins | Complete prediction/measurement/evidence/UI selection contract |
| `assemble_case_packages` / `validate_case_packages` | Saved-package integrity and linked handoff execute/reuse with owning validators and approved run summaries | This descriptor handoff does not assemble every production package format or qualify voxel geometry |
| `smoke_review_transport` | Separate synthetic UI save/reopen/revise/citation walkthrough passed | Real-case contours, qualified measurements and human walkthrough |
| `build_release_package` | No new evidence | Release selection and G8 prerequisites remain open |

The original stage IDs/dependencies have not been renamed or silently accepted.
No placeholder stage claims completion for training or real imaging. Independent
evaluation and measurement reliability remain distinct from transport checks.

## Evidence and next step

New tests: `tests/test_pipeline_accelerator_admission_v1.py` and its isolated helper.
They use the unchanged production guard and admission code; all owned subprocesses
have bounded waits and cleanup. Combined run also includes `test_mac_teacher_watch_v2`
and the100 workflow/registry/artifact/service tests from the preceding handoff.

Local logs: `outputs/prowl/pipeline-admission-20261027/`. Preserve early failures:
the teacher environment lacked pytest, so execution moved to the existing retrieval
environment with no dependency changes. The initial invented provider omitted its
parent geometry; a second fixture used the wrong fixed manifest basename. Both
were corrected in tests, without changing production contracts or acceptance criteria.
Final `regression.txt` records124 passes; `live-boundary.json` records the live lock
probe and repository pins.

Next useful CPU integration is a read-only frozen-cohort/prepared-cache handoff
using its owning validators and exact references. Actual training dispatch still
waits for complete target generation and full-executor qualification. Existing
teacher supervision remains authoritative throughout; no new scheduler is needed.
