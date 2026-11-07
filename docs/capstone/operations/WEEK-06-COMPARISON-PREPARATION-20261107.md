# Model comparison preparation — November 7

The completed KD results now have a reproducible preparation packet alongside
the current saved STU-Net observation. This is a descriptive evidence handoff,
not a model ranking, final STU-Net assessment or new experiment authorization.

## Inputs and results

The [packet](WEEK-06-COMPARISON-PREPARATION-20261107.json) was generated from the
original completed KD report and the exact published Lenovo aggregate export:

- KD source SHA256:
  `2679c09ebefc2361cb81122ead80530c48fcbeb99b333d2e526d1723a2e0033b`.
  Its existing reader verifies the closed status, twelve validations in both
  arms, all 70 endpoint case identities/references, recomputed summaries and
  selected/terminal checkpoint rules.
- Lenovo snapshot SHA256:
  `664535b2116b22bdf49ea85bc92457152dd830305145c398490eced023184163`.
  Observation: 2026-11-07 18:51:06 UTC; training at 6,814/12,000 updates with full
  2k/4k/6k validations. It is an exported observation, not a current worker check.
  The shared UI admission contract checks its shape, complete-score denominators,
  cadence and partial-validation semantics. The new tool also binds the authorized
  run, receipt, MLflow identity, cohort counts and 12k horizon.

| Completed KD endpoint | Control | KD | Descriptive difference |
| --- | ---: | ---: | ---: |
| Selected at 20k, positive-case lesion DICE | .383593 | .389084 | +.005491 |
| Terminal at 24k, positive-case lesion DICE | .381964 | .383439 | +.001475 |
| Selected component overlap | 39/45 | 37/45 | Two fewer components overlapped |
| Selected empty-case alarms | 33/34 | 33/34 | No change in case count |
| Terminal empty-case alarms | 32/34 | 29/34 | Three fewer cases alarmed |

The packet retains the full twelve-point KD curve and both endpoints' recall,
precision, false-positive/negative voxel counts and detection denominators. The
small DICE gain does not establish practical acceptance: selected recall declines,
component coverage declines, and the false-positive burden remains substantial.
Original failures, including the control cleanup failure, retain their statuses.
The [complete KD analysis](KD-DESCRIPTIVE-ANALYSIS-20261106.md) remains authoritative.

STU-Net's three completed lesion DICE points are .144179, .222087 and .347182.
The last observation has detection 30/36 and empty-case alarms 26/34. These are
interim supplied-region development scores. The tool does not subtract them from
24k KD results or call the best observed point a final selected checkpoint.

## Claim and execution boundaries

Equal 1,333/70 cohort counts do not establish matching case/reference identity.
STU-Net's aggregate export lacks the per-case evidence needed to verify alignment.
Its architecture, initialization, horizon and input geometry also differ from the
KD study. Patient/pretraining relationships remain unresolved. No independent
patient interval or isolated architecture/pretraining effect follows from these
numbers.

All six STU-Net validations and the selected/terminal per-case result, producing
pins, checkpoint/independent backups, MLflow closeout and worker/GPU cleanup must
be reviewed before a final STU-Net assessment. Even an aggregate export marked
`completed` does not provide that evidence. G4 and a prospectively frozen protocol
remain prerequisites for the required formal controlled comparison.

The inference-only Universal four-positive screen and the exposed autonomous
63-score/seven-failure baseline remain separate evidence. Neither is inserted
into a training leaderboard or silently given the KD denominator. KD-specific
spatial overlays also remain pending; the seven-case autonomous gallery does not
replace them.

## Reproduction and checks

From the repository root, with the existing private completed report available:

```sh
PYTHONPATH=. .venv312/bin/python scripts/diagnostics/prepare_week06_comparison.py \
  --kd-report outputs/prowl/kd-results-20261105-final-01/report.json \
  --stunet-export configs/training-progress/lenovo-stunet-20261106.json \
  --stunet-sha256 664535b2116b22bdf49ea85bc92457152dd830305145c398490eced023184163 \
  --node /Users/quintonevans/.nvm/versions/node/v24.21.0/bin/node \
  --output outputs/prowl/testing/reviewer-flow-20261107-01/week06-preparation-reproduced.json
```

Always select a fresh output; existing reviews are never overwritten. A later
export requires an explicit new SHA256 and preserves this dated observation.
Inputs are byte-bounded and checked unchanged after reading. Node admission has a
ten-second timeout. No model calls, optimizer steps, tracking writes or scan reads
occur. This tool is not a launcher or an automatic queue.

Fifteen CPU/metadata tests pass: changed pins/run identities, partial and malformed
scores, private/unknown fields, oversized input, retained output, deterministic
projection and a synthetic fully completed export that still cannot clear
scientific closeout. The actual CLI produced twelve KD pairs and three STU-Net
points; a second fresh run reproduced the JSON exactly. The previously committed
KD analysis also reproduced exactly from its original report.

Next work is ordered in the [Week 6 plan](../weeks/WEEK-06-WORK-PLAN.md).
