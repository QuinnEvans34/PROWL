# Duration recovery diagnosis — October 7, 2026

## Phone handback

**Diagnosis finished; scientific training has not launched.** A fresh continuation of the retained
invented step-48 checkpoint differs from the saved step-49 weights by at most **3.7253e-9** and
optimizer tensors by at most **4.3656e-9**. Progress/history and CPU/MPS RNG states match exactly.
The original bit-exact criterion still fails. No training-loop defect or harmless long-run drift
has been established.

The reporting defect that hid model magnitudes is fixed; **40 new model-free checks pass**.
Two short, separately frozen diagnostics used 16 forwards/two invented updates in total;
18.831315 seconds supervised, largest sampled owned RSS 1,162,100,736 bytes. Workers reaped.
No original/cache/CT/third-party-weight payloads or scientific job were used. N02, D01 and D02
remain consumed/retired with every failure preserved.

**Recommendation:** for the first uninterrupted duration comparison, qualify checkpoint loading,
saved predictions and exported masks; defer bit-exact optimizer continuation. This requires the
explicit limited-readiness amendment in [the prepared run packet](SEGMENTER-DURATION-REAL-DATA-PREPARATION-2026-10-07.md).
It is a proposed protocol decision, not permission to skip the current guard. No full producer
rehearsal is recommended solely to remeasure the same difference.

## Authorization and scope

Quinton selected a bounded diagnosis followed by a launch decision: measure the components,
repair only a demonstrated cause, use a focused check and prepare the real-data comparison.
[DUR-05's four-file contract](../imaging/SEGMENTER-DURATION-RECOVERY-AUDIT-CONTRACT-V1.md)
closes reporting implementation; [D01/D02's actual diagnostic packet](SEGMENTER-DURATION-RECOVERY-DIAGNOSTIC-PACKET-2026-10-07.md)
closes the fresh retained-invented-state access and model-call envelopes. Native automatic review
accepted both invocations. Neither changed acceptance, numerical recipe, storage capacity or roles.

## What the actual comparison measured

| Component | Exact? | Differing tensor/state fields | Mismatched tensor elements | Maximum absolute difference |
|---|---|---:|---:|---:|
| Model | No | 30 | 3,873 | 3.725290298461914e-9 |
| Optimizer | No | 103 | 925,459 | 4.3655745685100555e-9 |
| Progress/history | Yes | 0 | 0 | 0 |
| CPU RNG | Yes | 0 | 0 | 0 |
| MPS RNG | Yes | 0 | 0 | 0 |

D02's component summaries recorded zero nonfinite elements and zero reported structural/scalar
differences. All fields contribute to component maxima/counts; the path list is limited to 16,
so its truncation does not truncate the maxima. No raw tensor values are emitted. Relative error,
multi-update divergence and prediction changes after the replay update were not measured.

Both diagnostics loaded the same independently kept invented step-48 and expected step-49
artifacts. Each generated the same invented144³ inputs, made seven image-only predictions in the
declared first-case/six-train order and performed one update. These are new continuations, not
reconstruction of N02's discarded failed in-memory state. They do not qualify later checkpoint
probabilities or all 25 native exports/views. The old N02 failure remains a combined assertion;
the new diagnostics identify the components for these new executions.

Small finite floating-point differences are consistent with numerical execution variation.
PyTorch documents limited floating-point precision and that mathematically identical operations
need not produce bitwise identical results. This supports investigating numerical equivalence;
it does not identify an MPS operation or prove the observed difference harmless.
[PyTorch numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html).
Matching seeds/RNG alone do not establish deterministic execution.
[PyTorch reproducibility](https://docs.pytorch.org/docs/main/notes/randomness.html).

There is no evidence here justifying a sampler, optimizer or training-loop rewrite. Do not round,
replace or copy state values to force equality. Do not select a tolerance simply large enough to
pass D02. Training continuation can remain explicitly unqualified while a bounded uninterrupted
pilot answers the duration question, provided its separate checkpoint/inference evidence passes
and Quinton approves that change in scope.

## Reporting implementation and checks

- New `src/training/segmenter_duration_recovery_audit_v1.py`: independent existing predicates,
  bounded differences and component summaries; exclusive atomic JSON publication; failure phase,
  attempted counters and partial recovery evidence without suppressing the original exception.
- `scripts/diagnostics/segmenter_duration_launch.py`: only `cold()` reporting/comparison extraction
  changed. All code before/after that function is byte-identical to the retained original. The
  exact conjunction and next-weight-hash requirement are unchanged.
- New `tests/test_segmenter_duration_recovery_audit.py` and the closed contract above.

Initial fake-session tests exposed fixture-only reference/serialization mistakes, retained as
A001/A002. Integration and atomic-publication checks subsequently passed. D01 exposed a real
reporter defect: `OrderedDict` model states were classified as structures instead of traversed.
The repair accepts dictionary subclasses and records full component maxima beyond the path cap.
Regression checks cover that defect. Final A006: **40 passed**, 1.588161 seconds supervised,
352,616,448 bytes sampled owned RSS/22 samples; workers reaped. No actual model or optimizer calls
occurred in these checks; model construction/forward/update entry points were blocked. No old
successful suite was replayed. The two upstream deprecation warnings remain visible.

| Actual attempt | Outcome | Forwards / updates | Supervised seconds | Sampled owned peak bytes |
|---|---|---:|---:|---:|
| D01 | Diagnosis complete; model magnitude unmeasured by original reporter | 8 / 1 | 9.788469167 | 1,162,100,736 |
| D02 | Diagnosis complete; component-wide magnitudes measured | 8 / 1 | 9.042846250 | 1,161,510,912 |

Worker-internal times are 8.119653 seconds (D01) and 7.460784334 seconds (D02); the table includes
supervisor lifetime. Both requests retained read/time/RSS/output/free-space ceilings, AC and
shared MPS ownership checks. Worker payload-member accounting was 113,213,038 bytes per attempt
(226,426,076 total), below each136MiB ceiling. No keeper copies or external primary payload reads.
Reports do not confer native acceptance. Both actual counters were persisted; old N02 wrapper
zero placeholders remain historical, not evidence of zero work.

## Evidence and preservation

Ignored local receipt: `outputs/prowl/SEGMENTER-DURATION-DUR05-20261007/` contains all test logs,
resource records, original launcher/397-pin snapshot, D01 producing snapshots, both requests and
reviews, pinned source metadata, and the inactive real-target read ledger.

- D01 request SHA256: `f53440052a12a9c0569d3c0e99be8ce3b9e957bde96b4998b1861991218431cb`.
- D02 request SHA256: `8e9c492cf3d06117b1be5446ee4d12fd5dd00b22e03d96f1f00a50d65b0ff264`.
- Actual report namespaces: `outputs/prowl/SEGMENTER-DURATION-RECOVERY-D01-20261007/` and
  `outputs/prowl/SEGMENTER-DURATION-RECOVERY-D02-20261007/`.
- Final current producing ledger: `protected-pins-post-repair.json`, 400 paths: 396 original
  paths unchanged, original launcher amended only in `cold()`, three new producing paths.
  D01's earlier400-pin ledger and exact producing snapshots remain preserved separately.
- Historical experiment tail remains byte-identical; no new scientific notebook result is claimed.

Task tracking remains W01-28 incomplete for qualification; completed diagnosis is distinct from
readiness. Reviewed local preservation is authorized, public push is not. Human9am clock-in stays
open with pauses/net time pending; unattended diagnostics are not credited human hours.

## Exact next starting point

Review the **unapproved DUR-06 inference-only readiness scope** in the prepared run packet.
If chosen: targeted model-free guard checks, then one fresh read-only cold checkpoint/inference
qualification over retained N02 artifacts, with zero optimizer updates. After that succeeds, freeze
and review the fresh actual-data request with current source/storage/idle evidence. Scientific
launch remains Quinton's separate decision. No automatic resume, retry, producer repeat, tolerance
revision or scientific dispatch follows from this handback or scheduling.
