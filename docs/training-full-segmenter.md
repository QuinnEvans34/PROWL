# Full training through the capstone session architecture

The entry point is `scripts/train_full_segmenter.py`, using
`segmenter_full_session_v1` and `segmenter_full_executor_v1`. It does not call
`scripts/train.py` or the legacy general training loop. The frozen six-case pilot is unchanged.

The full session retains the capstone SegResNet architecture, normalized loss, checked input
batches, separate optimizer/evaluator roles, isolated RNG and dirty-state rule. Its sampler accepts
arbitrary cohort sizes and its update budget comes from one setting: `run.max_updates`.
Validation and checkpoint intervals are independent. Warmup/cosine scheduling uses that horizon.
It journals updates incrementally instead of revalidating the entire accumulated history each step.

`segmenter_geometry_v2` adds finite invertible affine support, including tilted scans, and supports
native volumes up to the explicit 256-million-voxel allocation. It maps the provided pancreas box
to a physical RAS grid and records the reversible transform. It retains v1's axis-aligned results
in the tested cases. The CT and reference masks must still agree physically; contradictory label
headers are reported, not overwritten. Downsampling that removes a lesion component is also reported.

## Preparation and launch

1. `scripts/prepare_full_segmenter_inputs.py` writes a candidate manifest from explicit train and
   development lists and verifies file paths and protected split membership. It never turns an
   empty mask into a verified negative.
2. `scripts/prepare_full_segmenter_cache.py` checks actual content and geometry and writes derived
   tensors to the external drive. The candidate provider cannot supply optimizer batches. Each
   case has a durable pass/failure record, source hashes, transform, fidelity result and cache hash.
3. After the complete pass and worker reaping, `scripts/compile_full_segmenter_cohort.py` freezes
   passed members and explicit exclusions. The scientific interpretation is training against the
   supplied annotations: empty references are background targets, **not confirmed healthy patients**.
   The original train/development/test files and previously held cases remain protected.
4. The full entry point checks the resulting configuration, then runs the new session/executor:

```bash
.venv-prowl/bin/python scripts/train_full_segmenter.py \
  --experiment /absolute/path/to/prepared/experiment.yaml --preflight --inspect-input-paths

.venv-prowl/bin/python scripts/train_full_segmenter.py \
  --experiment /absolute/path/to/prepared/experiment.yaml
```

The preparation template is `configs/experiments/full_segmenter_suprem.yaml`. Do not substitute
the old `full_suprem.yaml`: that earlier adapter routes to the legacy trainer. The full template
alone is not a ready launch while its cohort review is null.

`PreparedInputs` admits only reviewed cache members and verifies source observations, cache bytes,
metadata and protected roles. Training reuses these prepared tensors rather than preprocessing the
whole dataset again. No historical summer cache is silently treated as this geometry's output.

## Overnight operation and interpretation

The launcher owns the shared `outputs/prowl/.mps-profile.lock`, requires AC power, keeps the Mac
awake, and uses the existing owned-process watchdog. Its current preparation is for 24,000 updates,
validation every 2,000 and checkpoints every 500, with a 24-hour upper time limit and 12 GiB worker
RSS limit. This is an allocation, not an estimated duration. The derived cache allocation is 32 GiB
on the external drive. Checkpoints are external; verified copies and the journal go to the internal
backup under the existing total ceiling and free-space floor. Initial, latest and best states are
retained; every numbered checkpoint is not retained. No automatic restart is enabled.

The current development selection metric is positive-case macro lesion Dice on the tensor grid;
per-case predicted/target voxel counts include empty-reference cases. It is explicitly not a native
full-scan PanTS benchmark. Native final evaluation and an autonomous localization pipeline remain
separate from this provided-pancreas training experiment. Native optimizer continuation is not
qualified merely because checkpoint inference restoration passes.

Quinton chose SuPreM after the scan-membership uncertainty was explained. The new route can accept
an explicitly scoped `accepted_for_development` source-use record, with checkpoint and protected-role
hashes, evidence, the user instruction and visible limitations. The older `separation` preflight
still refuses that record. This does not assert that pretraining/model-selection membership is known
or certify a leakage-free benchmark. The publisher's release SHA-256 matches the selected checkpoint:
[official SegResNet release](https://huggingface.co/MrGiovanni/SuPreM/blob/main/supervised_suprem_segresnet_2100.pth).

## October 7 evidence

The candidate manifest has 1,412 train and 80 development cases with all paths present. Development
was sampled deterministically (seed 42; 40 historical positive and 40 historical empty references)
from the original development split. The historical `dev_subset_clean` list failed that current-role
check and was not reused. No test scans were read. Known held cases are absent from this selection.

V1 header admission rejected 252 cases: 222 exceeded its native-volume limit, 26 had unsupported
tilted geometry, and four had conflicting lesion headers. V2 accepts the sizes/affines in all 1,492
retained header records. The four label-grid conflicts remain separate data issues (6927, 259, 6466,
5731). Header compatibility is not content qualification.

The native invented profile used shape 510×431×918 (201,785,580 voxels) and a tilted affine. It
completed two 144³ MPS optimizer updates and four forwards, saved/restored a checkpoint with exact
evaluation results, and reaped its workers. Supervised duration was 13.0186 seconds and peak owned
RSS 5,101,207,552 bytes. It used no patient arrays or third-party weights. The first sandbox invocation
could not run `/bin/ps`; the supervised elevated attempt is retained separately as `a02`.

Actual SuPreM CPU initialization subsequently passed the strict 83-tensor import, finite-value checks
and fresh-head preservation. It performed zero forwards/updates and is not a real-data MPS run.
Focused tests cover long-horizon configuration, arbitrary cohort sampling, role/dirty-state failures,
CPU continuation, checkpoints, real NIfTI loading of invented arrays, cache integrity, physical ramp
oracles on tilted grids, axis-aligned parity, and the distinction between source use and separation.

The actual content/cache pass is recorded under
`outputs/prowl/full-segmenter-content-mac-20261007/`. Its request, original producing-code hashes and
source snapshots are retained even as subsequent launcher work continues. Read `summary.json`,
`resources.json` and `cases.jsonl` for its current state; absence of a summary is not completion.


## First full run launched

On October7 at20:31MDT, `full_segmenter_suprem_mac_01` began real SuPreM training through the new
session/executor (engine commit `3614f6c`, owned execsession48374). The completed preparation pass
admitted1,333training/75development cases and recorded84 exclusions. Its workers are reaped.
The admitted cohort includes218oversized and13tilted scans rejected by the previous loader.

Frozen configuration: `outputs/prowl/full-segmenter-admitted-mac-20261007/experiment.yaml`.
The adjacent `cohort-review.json`, `summary.json` and `launch-receipt.json` record exact membership,
exclusions and observed launch evidence. Eight actual updates were confirmed at02:31:22UTC;
initial checkpoint and its internal backup matched by SHA-256. Primary artifacts and journal are
under `/Volumes/PROWL-Data/PROWL/artifacts/full_segmenter_suprem_mac_01/`; backups are under
`/Users/quintonevans/PROWL-Backups/full_segmenter_suprem_mac_01/`.

Target24,000 updates, with a24h watchdog ceiling; a slower run may stop before the update target.
This is a running development experiment, not a completed result or qualified PanTS benchmark.
Keep the Mac connected to AC and the external drive mounted while the supervised job runs.


## Checkpoint continuation after transport

The launcher now accepts `--resume-checkpoint ABSOLUTE_PATH --resume-sha256 SHA256` with an
experiment YAML selecting a fresh name/output directory. Keep the model, initialization identity,
cohort, geometry, optimizer recipe, and total update horizon identical. The new segment retains the
checkpoint step, optimizer moments, learning-rate position, exposure counts, sampler position,
CPU/MPS RNG and best development score. Original logs/checkpoints are never truncated or replaced.
The checkpoint hash and its exact parent journal prefix are recorded in `continuation.json`.
Best checkpoints from earlier segments remain in their original folders; a new segment writes a new
`best.pt` only when its inherited score is exceeded.

October8 continuation was requested after transport. Resume configuration and retained checks:
`outputs/prowl/full-segmenter-resume-mac-20261008/`. It resumes13500 toward24000, with47716seconds
left of the original24h active-runtime allocation; time spent travelling is excluded. All storage
ceilings and1333train/75development members remain unchanged.

Validation:16distinct CPU checks (nine existing mechanics and seven resume checks) passed, covering
checkpoint/cohort/horizon/journal/best-score refusal, exact CPU continuation and parent preservation.
A fresh-process144³ MPS test restored full state exactly and completed the next update within
float32 tolerances (rtol1.3e-6,atol1e-5); maximum observed tensor difference2.682209e-7. Native
supervisor12.4509s/1563361280B peak/reaped. An earlier rtol1e-5/atol1e-7 comparison failed and is
retained alongside the successful result; no bit-exact GPU continuation or long-run drift claim.
Both native attempts used invented arrays only, three optimizer calls each. Engine commit867b034.


Actual continuation is running as `full_segmenter_suprem_mac_01_resume01` in owned session96730.
At08:12MDT onOctober8,13530 updates were confirmed. The actual restored full state matched the
parent checkpoint exactly; first replayed batch/loss matched, and the resumed initial checkpoint
matched its independent internal backup. Read this segment's `execution/history.jsonl` for current
progress. The original run's journal remains historical after its user-requested stop.
