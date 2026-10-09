# Lenovo training readiness — October 8, 2026

## Follow-up: JHU drive is now readable, PANORAMA capacity blocked

After Quinton attached `D:/`, filesystem inspection identifies `JHU-PanTS`, APFS,
500,090,011,648-byte volume, 34,608,918,528 bytes free. Standard Windows volume/partition
cmdlets do not expose D:, but .NET DriveInfo, PowerShell filesystem access and Python disk
usage agree it is available. This is a mount/access observation, not a drive-health qualification.

`D:/PanTS/data/` contains `ImageTr`, `ImageTe`, `LabelAll` and `metadata.xlsx`.
Only directory metadata was inspected; publisher-test arrays and patient payloads were not read.
`D:/PANORAMA/` contains only `panorama_labels-main.zip` (91,264,820 bytes), with identity and
integrity not yet checked. No PANORAMA CT archive was present in that directory.

The retained publisher inventory requires 194,181,682,590 bytes for all four CT archives;
the smallest alone is 46,271,075,077 bytes. Neither fits D:'s free space. Publisher Zenodo
records 13715870 and 10999754 still show matching batch 1/4 checksums and rounded sizes.
The challenge's landing page returned HTTP 403 in the browsing tool. C: had approximately
219.6 GB free at inspection, only 112.3 GB usable above the existing 100-GiB free-space floor.
It cannot hold the full CT archive set within that floor, either. Earlier retained extraction
inventory indicates roughly 195.7 GB of additional expanded output; new download/extraction
planning must include both archives and expanded data.

PANORAMA download is requested, but no transfer was started because a suitable destination
is missing. Next: connect the previously mentioned empty 1-TB drive and inspect its identity,
filesystem and free space for the PANORAMA destination. Preserve the existing PanTS data.
The prior environment and CUDA qualification remain valid. The earlier unmounted-drive
observation below is historical.

## Current outcome — environment and synthetic CUDA qualification passed

The isolated `.venv-prowl-windows` is installed using the app's existing Python 3.12.14
runtime. No standalone Python installer was executed. PyTorch 2.11.0+cu128,
torchvision 0.26.0+cu128, MONAI 1.6.1, MLflow 3.17.0 and imaging/testing dependencies
import successfully; `pip check` reports no broken requirements. Full training and cache
preparation entry points import and expose their CLIs on Windows.

The new full route now has CUDA float32 execution, isolated CUDA RNG state/restoration,
Windows power/locking/process supervision and write-through checkpoint replacement.
A portable full-trainer batch wrapper avoids importing the historical macOS source resolver;
its NPY hashes and mutation refusal match the preserved historical class in a parity test.
Historical pilot source files remain unchanged. CPU/MPS identity and state formats are preserved;
actual Mac execution of these edits was not performed here.

Focused verification: **49 distinct tests passed, one explicit MPS-native test skipped**.
Retained attempts under `outputs/prowl/windows-readiness-20261008/`:

- `focused-a01.xml`: collection failed because legacy requirements omitted `jsonschema`.
  `requirements/windows-training.in` and the checker now include it and the testing dependencies.
- `focused-a02.xml`: collection exposed the indirect Unix-only `resource` import. The new
  portable batch wrapper and direct RNG handling removed that dependency from the full route.
- `focused-a03.xml`: 47 passed, one skipped, one CSV fixture failure. Windows newline expansion
  caused the deletion test to remove a blank line instead of a case; its CSV writer now uses
  `newline=''`.
- `focused-a04.xml`: all 16 affected experiment-config tests plus the new batch-parity test pass.
  Latest outcomes across a03/a04 are 49 passed, one skipped, zero outstanding failures.

The actual full-session **144-cube CUDA profile passed in float32 without AMP**. Producer:
three optimizer updates and one evaluation; cold process: one continuation update. Peak CUDA
allocated memory across both processes was 3,454,467,072 bytes (3.22 GiB), peak reserved
3,879,731,200 bytes (3.61 GiB), on the 8,188-MiB GPU. Full restored state was exact. The next
update met float32 `rtol=1.3e-6, atol=1e-5`; maximum tensor difference was
2.086162567138672e-7, and the next batch/loss matched. This is not a bitwise future-run guarantee.
Supervised producer/cold durations were 22.282/16.813 seconds; peak sampled owned RSS
1,761,681,408/1,856,286,720 bytes; both worker trees were reaped. These startup-inclusive fixture
durations are not a real-data training ETA. Source pins, logs, states and resource reports remain
in `cuda144-a01/`. `environment/` retains package inventory and installed-version freeze.

The connected old drive is a 500,107,862,016-byte USB device with an APFS partition and no
mounted Windows filesystem. Disk enumeration alone does not establish filesystem/data health.
No recovery, formatting, filesystem repair or source payload reads occurred. The usable empty
training drive, data provisioning, protected cohort records, source-use review/weights, real-batch
checks and independent checkpoint-backup admission remain before a scientific job.

Use [the Windows training guide](../../training-windows.md). The initial observations below
are retained as history; the environment installation and CUDA software blockers are now resolved.

## Initial audit (superseded by the outcome above)

User requested latest work and preparation of the Lenovo as the primary stationary training
machine. Checkout fast-forwarded from `0c78ff7` to `8d64dda`; it was clean before setup.
The relevant committed task is W01-P02 and “Minimum software work for the first Lenovo job”
in `docs/capstone/imaging/AUTONOMOUS-PREDICTION-INVESTIGATION.md`.

## Observed state

- RTX 4060 Laptop GPU: 8,188 MiB VRAM, driver 596.58, idle, 58 C at inspection.
- AC connected; battery 98%; Windows Balanced power plan.
- Only the internal KIOXIA drive is visible. C: has 228,524,253,184 bytes free
  (approximately 212.8 GiB). The planned external 1 TB drive is not mounted.
- Python launcher lists 3.14, 3.13 and 3.11; Python 3.12 is absent.
- Default Python has no torch, MONAI, pytest or MLflow. No project virtual environment exists.
- No local roots registry, output split files, prepared cache or SuPreM checkpoint is available
  in this checkout. These ignored inputs did not arrive with Git.
- `winget` is unavailable. A command to download the official Python 3.12.10 installer,
  verify its Authenticode signature and install it per-user was rejected by automatic approval
  review: “blocked by policy.” It did not execute. No alternative installation was attempted.

## Reproducible environment setup

Install Python 3.12 using the official signed Windows installer:
https://www.python.org/downloads/release/python-31210/

Then run from the repository in PowerShell:

```powershell
& .\scripts\setup_windows_training.ps1
& .\.venv-prowl-windows\Scripts\python.exe scripts/diagnostics/check_windows_training.py
```

The setup creates a separate `.venv-prowl-windows`, installs CUDA 12.8 PyTorch wheels before
project dependencies, and runs dependency/environment checks. It does not launch experiments.
If script execution is restricted, use a permitted PowerShell session or run its reviewed
commands individually according to the machine's policy. Do not reuse the macOS wheel lock.
Package resolution and GPU checks have not been run on the new environment.

## Concrete first-job requirements

Use native Windows Python/CUDA for the initial port. Keep the new full session/executor model
and protected cohort semantics; preserve the historical pinned pilot implementations.

1. Connect and inspect the intended external drive, including filesystem and free space.
   Preserve its contents. Mac APFS storage is not assumed readable on Windows.
2. Provision the selected train/development membership, protected split metadata, source-use
   review and SuPreM bytes with content hashes. Choose transfer from existing verified data
   or a fresh acquisition based on actual availability. Git does not contain these files.
3. Add CUDA to the full session with isolated CUDA RNG and checkpoint state validation.
   Explicitly record precision. The normalized loss currently requires float32/float64 logits;
   an AMP port must cast logits to float32 for that loss and qualify optimizer continuation.
   Preserve the current 144-cube geometry until measured fit requires an explicit recipe change.
4. Replace launcher-only macOS dependencies (`fcntl`, `pmset`, `caffeinate`, `/bin/ps`, process
   groups) with native Windows locking, power/awake handling and owned process supervision.
   Checkpoint and backup directory fsync also need a Windows-compatible durability strategy.
5. Measure peak VRAM on representative batches, and qualify save/restart in a fresh CUDA
   process with explicit numerical tolerance and preserved history. Then freeze one experiment's
   config, budget, independent backup allocation and evaluation scope.

Initial status: environment installation was blocked; storage/data were unavailable; CUDA trainer port
and fit/recovery qualification remain outstanding. No patient arrays, pretrained weights,
training updates or model checkpoints were opened or generated by this readiness audit.
