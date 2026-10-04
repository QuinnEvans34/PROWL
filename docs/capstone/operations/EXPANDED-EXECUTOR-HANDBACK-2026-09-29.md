# Expanded executor handback — D-285

**Historical preparation record:** Quinton subsequently approved D-286 and CAP-EXP-005 completed.
See [the results](CAP-EXP-005-RESULTS-2026-09-29.md). The request below is consumed.

**Ready for exact CAP-EXP-005 launch review; not launched.** Quinton requested completion of the
loop, localization metrics, exports and interruption handling, followed by request freezing.
That preparation scope is complete. No real source arrays or real optimizer updates were consumed
by this slice. The qualified D-282/D-283 inputs and D-284 resource measurements remain applicable.

## Exact prepared run

| Setting | Frozen value |
|---|---|
| Experiment | CAP-EXP-005, fresh scratch pancreas-localizer smoke |
| Membership | 16 training / 11 separate development-validation; no replacement |
| Updates | 288, 18 equal frozen-order cycles over training members |
| Model/input | Existing two-output SegResNet; seed 42; 96-cube patches; v2 3-mm preprocessing |
| Optimization | Balanced CE + foreground soft Dice; AdamW LR 0.0003, weight decay 0.00001; cosine horizon 288 |
| Evaluation | Complete train and validation roles at steps 0, 144, 288 |
| Checkpoints | Steps 0, 96, 192, 288 |
| Final exports | All 27 cases, separately published native binary NIfTI + PNG + transform/metrics record |
| Limits | 600 s update phase; 1,200 s total including load/backup/recovery; 16 GiB RSS |
| Storage | 512 MiB RAM cache; 96 MiB/artifact; 1 GiB new bytes/domain shared across backup/recovery |
| Runtime | Native MPS float32, fallback disabled, AC power, cooperative accelerator lock |

Prepared directory:
`outputs/prowl/expanded-launch-request-7d7dea23-ed27-4d00-9f11-8798f79e70cc`

**Request SHA-256:** `2fa5f7f20916fb047ddcc54c3aede63e5f1c57566227cec1ef07a1d9756ae456`

| Bound member | SHA-256 |
|---|---|
| Inputs | `562f95b4d8b0a29d9cd5e31543a723c9f9299f02b0c3e1ee6cd280db15ced447` |
| Plan | `93acdc8f02745cb0ed649b9480bf0682cc2accb8da26b318750c7df6f8939f6b` |
| Source | `6a8c9148e8d33f3c9bd19183b1743436337b4fd470591f19cc97c0e0e92cc950` |
| Environment | `735eed0ad5ad5686d13298303f2b0ad7bb86a64d9e4ae1a94e57aeb2f61f0d22` |
| Recipe | `6ed81b30ae9f5b23103e108a6480387f269755c9bb717adcc04013bcbfd9de04` |
| Read capability | `0b9d2edb3900211b745894d30865d060fb90ca984d170d2030c97fbf7e6ca0d1` |
| Design | `8dec5b0ac9c10301c6d61f8d838efab05b60bc3de757bf27a5243ae2a6510e21` |

The request is `prepared_not_authorized`; no launch claim exists. The launch command requires a
separately pinned approval record explicitly naming Quinton, operation `launch_CAP-EXP-005`, and
this exact request digest. A denied record was tested and rejected before any source read. Do not
run a synthetic or real request again after its claim is consumed. Source/environment drift requires
reassessment and a new request. The exact design is retained inside the request, independently of
later planning-doc edits.

## Implementation

- `src/training/expanded_executor.py`: approval-bound loop, deterministic training-only schedule,
  full-role evaluation, metrics, native exports, checkpoint and terminal publication/validation.
- `src/training/expanded_localizer.py`: additive schema 2 execution identity and checkpoint support;
  schema 1 readiness semantics remain covered by existing tests.
- `scripts/diagnostics/expanded_localizer_launch.py`: metadata-only prepare, exact approval check,
  single-use claim, AC/lock/time/memory supervision, complete backup and fresh-process recovery.
- `tests/test_expanded_executor.py`: 15 regression/fault-injection cases. Original two-case loader,
  preprocessing, run and smoke modules are unchanged.

Each final prediction is restored to its source shape/affine and checked as uint8 binary data.
Terminal validation resolves every checkpoint and every case reference, checks complete cadence,
role membership, final metric agreement, NIfTI geometry and PNG validity. An export failure retains
completed case artifacts and the latest checkpoint, but creates no terminal. Injected interruption
at update 3 preserves completed checkpoint 2, records the interrupted state, and never auto-resumes.
Hard termination is additionally recorded by the supervisor; fsynced events retain completed refs.
A primary terminal means computation/exports completed; overall success additionally requires the
backup/recovery evidence and final job receipt. A failed backup does not erase valid primary work.

Metrics include per-case Dice, precision, recall, foreground-volume ratio, balanced loss, prediction-
only all-component box, pancreas reference coverage and scan fraction. Empty predictions remain
explicit localization failures. Component counts above 4,096 report a detail-budget limit while
preserving the case's box and voxel metrics. The requested 10-mm margin rounds up to 12 mm on the
3-mm grid before boundary clipping. Fit/ROI thresholds are the existing provisional engineering
screens, not data eligibility or clinical acceptance rules. No lesion containment claim is made.

## Verification and retained attempts

**1,170 native tests passed**, two existing upstream warnings, 27.14 seconds. Command:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Final MPS rehearsal used 16/11 invented cases and four synthetic updates. It exercised evaluations
0/2/4, checkpoints 0/2/4, all 27 native exports and a terminal. All **31 artifacts** were backed up
on the independent internal device and restored into new destinations by a fresh process with
Python primary-drive reads blocked. The fixed restored prediction probe differed by **0**.
Total supervised time **87.36 s**; peak RSS **1,998,815,232 bytes (1.86 GiB)**. Zero real updates.
The final request's source and environment bytes exactly match this successful rehearsal.

Final evidence: `outputs/prowl/expanded-execution-8801ec48-45ca-4b47-a5e2-2ba46c0a09fd`.
Job receipt: `748ad87d5100b2d42277408ec77d1e39d6ae60bc0320ccfd1c3e5db4737ecda6`.
All 14 receipted evidence files were independently checked for size/hash.
Primary terminal receipt: `4628cfbc0672f073c17cc1a7944dcded21276af4d7bd5d8d8fb6d090fcd86a54`.
The recovery request/journal retain all primary/backup/restore references.

Earlier complete rehearsal: `expanded-execution-a9930a35-73ad-4c7b-b91b-8b5a5ee56711`,
receipt `bc7cb4cdfc874e1165da6a6d32bbafb469c38bae52898b41dc8d8837e0099c84`, 89.88 s.
Subsequent review tightened the recovery phase to reuse the original absolute storage ceiling,
then reran the final source. Both attempts remain preserved. No drive-unplug test is claimed.

## Next action

Obtain Quinton's approval to launch the exact prepared request above. Then record that approval,
run once within the fixed limits, inspect learning/localization on every training and validation
case, and document results including nulls/failures. Do not promise the smoke will meet useful-mask
or ROI screens. It gives only 18 updates per training case, substantially fewer per case than the
previous two-case run. Do not tune on the publisher test set, remove difficult members after seeing
performance, or interpret this small validation cohort as broad generalization evidence.

Case 6350 remains held; partial-coverage/noisy members remain included. Source-use/redistribution
limits and the study-as-subject limitation persist. No literature work, source rewriting or Git
publication occurred in D-285.
