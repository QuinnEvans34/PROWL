# Lenovo training setup and first long-run handoff

**Created:** October 8, 2026  
**Owner:** Quinton Evans; Lenovo chat implements locally, Mac chat reviews the handback  
**Status:** Implementation handoff; CUDA compatibility and data provisioning not yet complete  
**Purpose:** Prepare the stationary Lenovo to run one long experiment on the NEW capstone trainer,
then support independent Mac/Lenovo experiments over the weekend.

## User intent and working arrangement

Quinton wants the Lenovo to stay at home on power, dedicated to training for the remaining capstone.
The 1TB external drive currently has no dataset loaded. The Mac remains the development machine and
may also train an independent model over the weekend. Tonight's goal is a verified long training
launch, conditional on actual data availability, fit and restart checks; do not promise an ETA before
measuring setup and transfer time. Two machines permit concurrent experiments, not guaranteed twice
the research progress or identical runtimes.

Implement this bounded setup and return the report below to Quinton. He will relay it to the Mac chat
for review and select the first experiment before the long launch. Do not message another chat,
create cloud resources or spend money implicitly. Routine setup need not become a series of new
approval packets. Ask only for a genuine missing decision or required machine permission.

## Known hardware and recommended environment

Inventory commit `0c78ff7`, `WINDOWS_LAPTOP_SPECS.md`, records ThinkPad P1 Gen6, i7-13800H,
32GB RAM, RTX4060 Laptop with 8GB VRAM, Windows11, WSL2 Ubuntu installed, and roughly220GB internal
free at collection. These are observations from October7; verify current state. Windows Python
installations do not establish which Python is available inside Ubuntu.

Prefer existing **WSL2 Ubuntu + CUDA**, with code and virtual environment in its Linux filesystem.
Use Python3.12 to align with the current project environment if available/installable. Inspect the
existing Ubuntu version before choosing installation commands. Pin a compatible PyTorch CUDA build,
MONAI and other required dependencies; record versions. The broad lower bounds in `requirements.txt`
are not a reproducible lockfile. Do not install unrelated UI, serving or tuning infrastructure merely
to run this trainer. Confirm actual imported dependencies before pruning the environment.

Initial PowerShell inventory:

```powershell
wsl --list --verbose
nvidia-smi
Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem, SizeRemaining, Size
wsl -d Ubuntu -- bash -lc 'cat /etc/os-release; python3 --version; nvidia-smi'
```

WSL uses the Windows NVIDIA driver; do not install a Linux display driver inside WSL. Select the
PyTorch wheel from official compatibility guidance; a separate full CUDA toolkit is not required
merely to use prebuilt PyTorch wheels. Verify `torch.cuda.is_available()` and device identity inside
the actual virtual environment, not only `nvidia-smi` in Windows.

References: [Microsoft WSL GPU setup](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gpu-compute),
[NVIDIA WSL guidance](https://docs.nvidia.com/cuda/archive/13.0.2/wsl-user-guide/index.html),
[PyTorch installer](https://pytorch.org/get-started/locally/).

## Establish the correct repository before implementation

- Record `git status`, branch and commit; preserve existing Lenovo edits.
- Mac's full-session resume implementation is commit `867b034`. Inspect ancestry and the actual files;
  having an old PROWL checkout or the machine-inventory commit alone is not sufficient.
- Use `scripts/train_full_segmenter.py`, `src/training/segmenter_full_session_v1.py`,
  `segmenter_full_executor_v1.py` and `segmenter_full_resume_v1.py`.
- Do not substitute `scripts/train.py`, the legacy trainer, or retired duration-pilot consumers.
- This handoff was committed locally on Mac. A Git commit does not automatically publish it or the
  preceding engine commits to Lenovo. If missing, arrange a reviewed Git bundle/branch transfer or
  user-authorized normal publication. Never silently continue on stale code or force/reset local work.
- Work on a `codex/` branch and make meaningful local commits. Keep machine-local paths, data, weights,
  secrets, logs and checkpoints outside tracked source. Return the patch/commit for review.

## Bounded implementation work

### 1. CUDA session and state

The current session explicitly supports CPU/MPS only and inherits its RNG context from
`segmenter_pretrained_session_v1.Session.rng_scope`. Inspect that implementation too; adding `cuda`
to an allowlist alone is insufficient.

Add explicit CUDA execution, selected-device validation and isolated CUDA random-state handling.
Persist and restore model, optimizer, progress, sampler/exposure state, CPU RNG, CUDA RNG and any
precision state needed for continuation. Record backend and precision in experiment identity.
Check optimizer tensors are on the intended device after restoring a CPU-loaded checkpoint.

Keep CPU/MPS behavior and saved Mac checkpoint compatibility intact. Version new state formats if
needed; do not reinterpret old bytes or silently relax identity checks. Mac-to-CUDA optimizer resume
is not the first task: the Lenovo run starts as a separate experiment from its selected initialization.
Reuse SuPreM under the existing documented development-use limitations; no fallback to scratch without
Quinton's choice. Verify source weight bytes and backbone/fresh-head behavior.

### 2. Compatible supervised launcher

The launcher uses `fcntl`, `pmset`, `caffeinate` and a Mac-named shared lock. WSL supports Linux locks
but does not supply the macOS commands. Add platform/backend-specific behavior while preserving
single-job ownership, whole-worker-tree monitoring, resource limits, failure logs and cleanup.
Inspect inherited supervisor dependencies; do not assume only those three calls are platform-specific.

Use measured Lenovo limits, not the Mac's internal disk paths or MPS resource assumptions. Set Windows
plugged-in sleep policy appropriately, keep ventilation clear and initially leave the lid open.
Log the user-visible stop command and prove workers stop before drive removal. Prefer a graceful
checkpoint-boundary stop if implemented and tested; otherwise explicitly report the saved step and
unsaved work that will repeat. Never claim a suspended process makes a removable drive safe to unplug.

### 3. Portable inputs and prepared-cache evidence

The Mac's current manifest contains absolute `/Volumes/PROWL-Data/...` paths. The prepared provider
checks source/cache evidence; replacing text paths without rebuilding location-dependent evidence is
not sufficient. Inspect `src/data/segmenter_prepared_inputs_v1.py` and its reviewed cache inputs.

Create a portable mapping from stable case IDs and source-relative paths to local dataset roots.
Preserve content identity, target status, protected role, geometry recipe and cohort membership.
Regenerate machine-specific file observations and cache evidence through the appropriate loader;
do not disable integrity checks or reuse Mac inode/device observations as Lenovo evidence.

## Data provisioning and storage

First inventory the 1TB drive's actual filesystem, free space, connection and WSL accessibility.
Do not format it without an explicit request. Avoid placing a large hidden duplicate of the dataset
inside the internal WSL virtual disk. Record physical locations and benchmark a small representative
read/cache operation before committing to a transfer layout.

Provision only what the selected experiment needs:

1. Frozen train/development case lists, source/provenance and review records.
2. Matching CT and target files for those cases, copied or acquired from pinned sources with checksums.
3. Selected pretrained weights and their source/hash record.
4. A bounded processed cache with versioned geometry/config identity.
5. Separate run directories for configuration, histories, initial/latest/best checkpoints and results.
6. An independent physical backup location for indispensable run artifacts. Code on Git is not a model backup.

Produce a byte budget: selected source bytes + derived cache maximum + retained outputs/checkpoints +
backup allocation + free-space reserve. The external drive's nominal capacity is not its available
capacity. Backups on the same drive do not count as independent; use internal storage if its verified
capacity permits. Do not copy all archives plus all extracted data by default.

Current Mac experiment reference: 1,333 train and75 development PanTS cases, 24,000 total updates,
SuPreM backbone/fresh three-class head, AdamW1e-4,500-step warmup/cosine,144 cubed tensor,
geometryv2/1mm intermediate sampling/10mm pancreas-only reference crop,validation2000/save500.
This is an existing reference recipe, **not an automatic choice of Lenovo's first experiment**.
Actual manifests/configs are under `outputs/prowl/` and may be ignored by Git; transfer them explicitly
with content hashes. Do not reconstruct membership from a directory glob.

PANORAMA is acquired on the Mac but absent from the current run. Its candidate manual-lesion pool
needs the existing integration/overlap/provenance work; it is not a prerequisite for the first
PanTS-only Lenovo run. Do not label non-PDAC cases generically healthy.

## Verification sufficient for a long launch

Use relevant existing checks and add meaningful tests for changed behavior; do not repeat the entire
historical suite or construct a new approval framework.

- CPU/MPS compatibility: affected session/executor/resume tests pass; old state formats remain readable.
  Native MPS is unavailable on Lenovo, so report that limitation and arrange affected Mac verification
  after its current job, without competing for its accelerator.
- CUDA mechanics: finite loss, real parameter updates, deterministic sampler progression, correct
  device/RNG behavior and serialization in the actual environment.
- Recovery: compare saved/restored state and progress, then a fresh-process next update against an
  uninterrupted reference using an explicit numerical tolerance; do not require unjustified cross-device
  bit equality. Preserve failures and their cause rather than widen tolerance until tests pass.
- Data: correct ID/role joins, checksum identity, label mapping, geometry and no train/development overlap.
  Case-ID disjointness is not by itself proof of complete patient/source independence.
- Real representative batch: exercise training and validation at the proposed tensor size, record peak
  GPU allocated/reserved memory, host memory, time/update, validation cost and successful backup.
- Resource/stop behavior: supervised stop cleans up owned workers; retained checkpoint is readable;
  free-space limits and output identity behave as intended.

Try the intended FP32 recipe first if plausible; 8GB fit is unknown. If it does not fit, return measured
failure and propose a named adjustment. AMP, smaller tensors or changed accumulation affect the recipe
and must be disclosed, not silently applied. CUDA+AMP is a distinct experimental condition from MPS FP32.

## First experiment selection and launch

Once the report is ready, Quinton will bring it to the Mac chat. Recommend one experiment with an
explicit question: for example, a clean historical-localizer rerun or a full-segmenter comparison.
A localizer experiment may need a different training consumer; do not assume this segmenter port
already implements it. Identify its code/readiness separately before choosing that run.

Before launching, record exact code/config/initialization, fixed cohort, training horizon, cadences,
precision, output/backup paths, resource budget, expected runtime from measurement, and stop/restart
instructions. No automatic sweep, extension or next experiment. The first finish line is a running,
observable, recoverable long experiment using the new architecture—not an indefinitely growing
infrastructure project.

## Return this report to Quinton

```text
LENOVO HANDOFF
Repository branch/commit; how current Mac code arrived:
OS/WSL/Python/PyTorch/CUDA/MONAI versions; GPU detected:
Code changes and CPU/MPS compatibility status:
Drive root/filesystem/free space; source/cache/output/independent backup budgets:
Dataset IDs/counts/provenance; transfer and checksum completion:
Chosen initialization and hash:
CUDA update/validation results; peak VRAM/RAM; measured time/update:
Fresh-process save/restore and next-update result:
Supervisor stop/cleanup and checkpoint backup result:
Proposed first experiment, fixed configuration and expected duration:
Exact launch/status/stop/resume commands:
Remaining blockers or decisions (specific, not speculative):
Status: setup incomplete / ready for experiment selection / launched with user direction
```

## Weekend two-machine operation

Use one independently owned job per machine, unique run IDs/output directories and immutable code
snapshots for each active job. Share small source changes and result summaries deliberately; never
update code underneath a running job. Keep each job's data locally available so disconnecting the
Mac drive cannot interrupt Lenovo. Save results and failed attempts before selecting the next run.

Choose complementary experiments from the
[autonomous prediction investigation](../imaging/AUTONOMOUS-PREDICTION-INVESTIGATION.md).
Compare cases/metrics consistently and disclose backend/precision differences. For a controlled
architecture comparison, avoid changing hardware and precision at the same time where practical.
Cloud remains a capacity option; provider, data upload and spending have not been selected.
