# Configurable full training

The full-run entry point reuses the working `scripts/train.py` numerical loop through a versioned
experiment YAML. The six-case/192-step duration pilot remains historical and separate. A new full
run does not inherit its inference certificate, native scoring, backup qualification or stop policy.

## Use

```bash
.venv-prowl/bin/python scripts/train.py --experiment configs/experiments/full_suprem.yaml --preflight
```

This reads experiment/cohort metadata only and returns all observed blockers together (exit 2).
It does not open scan or weight payloads, create a run directory or train. Add `--inspect-input-paths`
to also check file availability. A ready metadata-only report does not certify payload contents.

Once source/cohort reviews and the concrete resource allocation are complete, the same command
without `--preflight` performs admission, snapshots metadata and starts the experiment. Keep the
computer powered/awake and use the established accelerator ownership arrangement. This adapter
does not itself replace the shared hardware supervisor or independent backup mechanism.

For a fresh longer experiment, change `run.max_updates`, the learning-rate recipe if needed, and
the unique run name. The trainer uses that horizon for its warmup/cosine schedule. Cohort membership
comes from the selected ID files, with no fixed member count. `validate_every`, `checkpoint_every`
and `log_every` are independent positive intervals; final validation also runs for non-divisible
horizons. Checkpoint selection uses development lesion Dice, with the legacy mean-score fallback
if the entire development evaluation has no lesion score. Thus a positive development cohort must
be part of the scientific design; the loader alone cannot establish useful selection data.

This first adapter supports fresh three-class scratch/SuPreM experiments. Resume and paired
anatomy5 experiments retain their separate existing routes and are not enabled through extra CLI
flags. YAML is the single configuration source. Do not reinterpret a fresh longer run as resuming
the old schedule.

## Reused and new pieces

- Reused: MONAI loader/transforms, SegResNet, loss, optimizer/schedule, validation, checkpoint writer
  and MLflow integration. Geometry/recipe are explicit; this does not silently substitute the R01
  144-cubed loss/geometry or claim autonomous inference.
- Added: flexible experiment configuration, strict cohort metadata checks, original-role separation,
  snapshots, isolated outputs/cache/MLflow, source-review binding, strict SuPreM backbone import,
  local JSONL metrics and nonfinite-loss refusal.
- SuPreM never falls back to scratch in this route. Its file hash is checked before restricted
  deserialization; missing/extra/mismatched backbone tensors fail before loading. The 32-class source
  head is discarded while retaining the fresh three-class head.
- Runtime/free-space checks run before creation and between updates. They are not a hard watchdog
  for a stalled kernel and do not constitute measured memory admission or an approved backup budget.
- `last.pt` is periodically replaced atomically within this run, while selected `best.pt` and final
  archive copies follow the existing trainer. This is not retention of every numbered checkpoint.
- No default early stop based on a poor update-48 quality score. Model performance remains an
  experimental outcome, and final accept/reject criteria belong to the recorded scientific plan.

## Input evidence

The manifest uses the existing columns `case_id`, `ct_path`, `pancreas_path`, `lesion_path` (or
head/body/tail paths for `hbt_union`). Paths must be absolute and all requested members present.
An accepted cohort review JSON contains `decision: accepted`, `input_sha256` equal to the six
file hashes printed by preflight, and `evidence` referencing the actual qualification findings.
It must account for label interpretation, holds and permitted uses; do not generate acceptance
from mere path existence or an empty lesion mask.

SuPreM source review JSON contains `decision: accepted`, `checkpoint_sha256`,
`protected_roles_sha256` (original train/development/test file hashes), and `evidence` for the
source/selection-separation conclusion. The adapter checks bindings, not the truth of that
scientific conclusion; an actual reviewed source determination is required.

## October 7 implementation result and tonight's status

The first 14 focused tests passed, followed by a real CPU integration check (15 total): nine
invented training cases, two development cases, three actual updates, validation at updates two
and three, best/last saves and isolated history. Config tests accept 24k/72k/100k horizons without
running those horizons. Artificial SuPreM tensors test backbone/head behavior; no actual pretrained
payload was opened. This is functional evidence, not a native/full-scale benchmark.

`full_suprem.yaml` is a preparation template, not a ready launch. Metadata preflight finds the
historical 1,412-case ID list, but reports missing current manifest/development IDs, pending cohort
review, pending SuPreM source review and an unset runtime allocation. Existing source/backup
constraints remain unresolved; no real run has launched.

The user selected SuPreM rather than scratch. Focused public follow-up found the official downstream
recipe using the selected release, but no checkpoint-bound training/selection crosswalk resolving
the existing separation question. PanTS issue 4 discusses comparing annotations with SuPreM
predictions; that is not membership/overlap evidence. No source clearance or contamination claim
follows. Publisher outreach remains with Quinton; no message was sent.

Sources: https://github.com/MrGiovanni/SuPreM/tree/main/target_applications/pancreas_tumor_detection
and https://github.com/MrGiovanni/PanTS/issues/4, plus the retained October 6 source-gap review.
