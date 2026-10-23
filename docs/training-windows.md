# Native Windows training

The Lenovo uses `.venv-prowl-windows` with Python 3.12 and CUDA PyTorch. Always invoke
that environment explicitly; the system default Python is a different environment.

```powershell
& .\.venv-prowl-windows\Scripts\python.exe scripts/diagnostics/check_windows_training.py
& .\.venv-prowl-windows\Scripts\python.exe scripts/train_full_segmenter.py --help
```

`scripts/setup_windows_training.ps1` creates the environment from a supplied Python 3.12
executable, or reuses the existing Windows environment. It installs CUDA 12.8 wheels before
project dependencies and checks imports plus a small CUDA kernel. The macOS dependency lock
is not a Windows installation lock. Retain the installed inventory with each experiment;
the environment checker supports `--output` to save JSON and `pip freeze` in a fresh directory.
The initial environment uses the app's existing Python 3.12.14 runtime as its base; keep that
runtime available, or recreate the venv from a standalone Python 3.12 installation if it moves.

## Full trainer support

The current full session accepts `device: cuda`, with float32 computation and TF32 disabled
inside the session. CUDA precision is recorded in the session identity. Its version-2 CUDA
state includes CUDA RNG; CPU/MPS identities and version-1 states keep their prior formats.
Backend identities prevent silently resuming a Mac run on CUDA as the same experiment.

The full training and cache preparation launchers use Windows exclusive locking, AC checks,
idle-sleep inhibition and a process watchdog. Windows job ownership terminates descendants
when the supervisor closes; sampled process-tree RSS and runtime are bounded. File contents
are flushed before write-through checkpoint replacement. Primary and backup volumes still
need to be distinct for real launch admission.

The bounded GPU qualification uses generated images/labels and the actual model, normalized
loss, optimizer and state codec:

```powershell
& .\.venv-prowl-windows\Scripts\python.exe scripts/diagnostics/profile_windows_full_segmenter.py --output outputs/prowl/CHOOSE-NEW-PROFILE-ID --size 144
```

It performs three producer updates and one evaluation, writes a checkpoint, then checks exact
state restoration and one next update in a fresh CUDA process. Each stage has a 600-second
and 12-GiB sampled process-memory ceiling. It records peak GPU allocated/reserved memory.
This is an engineering qualification; actual-data fit, data loading, independent backup and
scientific results require the selected real experiment.

## Data admission

The committed Mac template contains Mac paths and is not a ready Windows experiment.
Prepare a Windows configuration against accessible storage, preserving approved cohort
membership, protected roles and source hashes. Local path/inode observations must be generated
for the destination. Do not reuse copied Mac filesystem observations as Windows qualification.
Use the full input preparation/cache/cohort scripts, then the full trainer's preflight.
Current source-use and supplied-annotation limitations remain attached to the experiment.

See [Lenovo readiness evidence](capstone/operations/LENOVO-READINESS-2026-10-08.md).
