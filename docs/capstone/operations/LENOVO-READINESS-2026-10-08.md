# Lenovo training readiness — October 8, 2026

## October 9 authorized cache-preserving continuation

**Live:** commit `8e69054`, owned exec **71115**, started October 9 at 13:10:58 UTC.
Parent/control/prefix validation passed; initial retained batches match their parent hashes.
Preparation is active, not scientific training; the eight-hour clock has not started.
An additional existing input-provider regression passed (18 focused checks total).
The five-minute quiet monitor `lenovo-eight-hour-training-watch` is active for this new attempt.

Quinton requested starting the continuation after the preparation timeout. A new attempt at
`E:/PROWL/readiness/lenovo-8h-20261009-a02` will preserve the original failed audit and candidate
configuration. The parent must be stopped/reaped and have an exact successful ordered prefix,
unchanged source observations and input control, and no missing or orphan cache members.
The 1,101 retained batches are read and hash-checked against the parent ledger; their original
CTs are not reprocessed. Only the remaining 307 cases require preprocessing. The new preparation
watchdog is four hours; 12 GiB worker, 32 GiB cache, storage floors and all scientific limits remain
unchanged. No automatic retry. Failure evidence remains preserved.

Seventeen focused continuation, cohort-compilation and admission tests passed, including injected
corruption, missing members, altered configuration/control/source observations and orphan entries.
The three modified prior producing paths are the input cache-opening branch, preparation driver,
and pipeline orchestrator; numerical preprocessing, model, optimizer and timed executor are unchanged.
The pipeline still requires all 1,408 cases, exact original 1,333/75 membership, source hashes and
target states, followed by real CUDA/independent backup/cold recovery checks before eight-hour
scientific training. Preparation time does not count toward the eight-hour target.

## Terminal stop — October 8, 23:07 MDT

The pipeline stopped during cache preparation at its two-hour watchdog limit, before real
CUDA qualification or scientific training. The content ledger retains **1,101 technical passes,
zero recorded case failures, and 307 of the 1,408 cases not completed**. The last completed
record is at 7,194.766 seconds; the preparation watchdog ended at 7,200.016 seconds.
Peak sampled worker RSS was 3,899,154,432 bytes, below the 12-GiB ceiling, identifying the
elapsed-time limit rather than the memory bound as the resource stop.

`content-audit/resources.json` and `prepare-cache-resources.json` both report workers reaped;
owned exec 61716 returned exit 1 and is finished. The pipeline journal records terminal failure
at 2026-10-09T05:07:30.758Z. There is no long-run training history: zero scientific updates,
no training checkpoint/backup, and the eight-hour clock never started. The earlier verified
1,408 CT hashes remain evidence; no original CTs were rehashed by monitoring.

All logs and partial cache contents are preserved in their original directories. The scheduled
monitor `lenovo-eight-hour-training-watch` was deleted after this terminal failure as requested,
using the scheduled-task control; no retry, source/config change or Mac action occurred.
Next requires user direction: qualify a continuation that preserves completed cache work and
select a longer preparation allowance. Do not assume the existing scripts already support
resuming this partial cache, or rerun preparation from scratch automatically.

## Admission pipeline active — October 8, 21:07 MDT

All **1,408 CTs passed**, 46,341,767,190 bytes read in 779.328 seconds. Owned verifier
20288 finished; no need to repeat it. Frozen launch code commit `4b55583` adds the single
pipeline after `6c91b14` timed-run support. Five additional admission-gate tests pass:
47 distinct affected checks now pass, with one explicit native MPS skip.

Owned exec **61716** runs `scripts/diagnostics/launch_lenovo_endurance.py`, with:

- Handoff: `E:/PROWL/transfer/PanTS-8h-20261008/`
- CT verification: `E:/PROWL/readiness/ct-verify-20261008-a01/`
- Pipeline logs/pins/authority/config: `E:/PROWL/readiness/lenovo-8h-20261008-a01/`
- Training output, after all gates: `E:/PROWL/artifacts/full_segmenter_suprem_lenovo_8h_01/`
- Independent backup root: `C:/Users/quinn/PROWL-Backups/`

Current checkpoint: input binding passed, cache preparation active, first 13 content cases pass
with zero failures. **No scientific optimizer updates yet.** The pipeline will automatically
compile the unchanged cohort, compare all newly prepared source hashes and target states to
the handoff, run a bounded real CUDA/75-case validation/independent-backup/cold-continuation
qualification, then start exactly one fresh eight-hour training job. Any failure stops it with
evidence; no retry or cohort shrinkage. Preparation has a two-hour inner resource limit;
training targets eight elapsed hours after the initial checkpoint/backup with a nine-hour
watchdog. Do not modify its pinned source/config files or launch a second invocation.

A quiet five-minute in-chat heartbeat, `lenovo-eight-hour-training-watch`, observes this pipeline
and reports confirmed actual training start, failure/required action, or completion. It removes
itself on a terminal outcome. This uses the documented scheduled-chat follow-up mechanism, not
a second training process. Keep the desktop app running, AC connected, both drives attached,
lid open and vents clear. Ask this chat to stop the owned pipeline before unplugging storage;
stopping is not a graceful final-save guarantee, and unsaved updates after the last checkpoint
may need replay. Verify every owned worker has exited before drive removal.

## Launch requested; eight-hour duration selected

Quinton requested training launch and explicitly selected eight elapsed training hours rather
than a potentially shorter 24,000-update ceiling. New optional duration support targets 28,800
seconds after the initial checkpoint, including the training loop's validation/checkpoint time.
A separate 32,400-second watchdog and one-million-update safety ceiling bound the job. The
learning-rate horizon remains 24,000; beyond it the last original update's very small rate is
held fixed (endurance work, not a claim of meaningful continued learning). Failure/resource/AC
stops remain enforced. Timed resume refuses automatic timer resets pending an explicit remaining
duration calculation. Historical non-timed identity/result formats remain unchanged.

Affected checks: 42 distinct passes and one explicit native MPS skip. The first attempt found
one result-shape regression (35 pass/1 fail/1 skip); restoring the old non-timed return shape
fixed it (11 affected checks pass/1 skip). Six new duration configuration boundary checks pass.
Three new local handoff/real-profile helper entry points compile. No full historical-suite replay.

CT verification is running under owned exec session 20288, preserving an append-only per-file
hash ledger in `E:/PROWL/readiness/ct-verify-20261008-a01/`; first 575 files matched at this
checkpoint. This is not completion. Next: all 1,408 CT matches, local manifest/cache preparation,
complete no-new-failures cohort compilation, actual CUDA updates/75-case validation and cold
continuation from an independently hashed internal backup, then the authorized single long run.
No cohort shrinkage, scratch fallback, AMP or tensor-size change is implicit. PANORAMA is separate.

## Private handoff received and verified

Magic Wormhole 0.24.0 is installed in a separate environment,
`C:/Users/quinn/.cache/prowl-transfer-venv`; pip check passes. The CUDA environment was
not modified. User-authorized receive completed in owned session 87831 through the
encrypted relay, with receiver exit zero. No Mac job was controlled from this machine.

Received `E:/PROWL/transfer/PROWL-Lenovo-PanTS-8h-private-20261008.zip` matches the
user-supplied SHA256 `047032713173bce4264eacbb47404fcf0b48fffd806f6700c1eb4c7cc4dab56a`.
Archive validation checked 4,252 entries, 440,931,704 expanded bytes, destination containment,
case-insensitive duplicate paths and symbolic-link rejection before extraction into fresh
`E:/PROWL/transfer/PanTS-8h-20261008/`. The verifier source was inspected; inventory paths
were checked before execution without an execution-policy override. It reports **4,251
payload files verified**, including labels and the pinned pretrained checkpoint.

This resolves the metadata/label/weights transfer blocker, not full data admission. Next:
independently match the 1,408 admitted CT hashes against the supplied source-file inventory,
then prepare Windows observations/cache/review against the protected 1,333/75 split. No CT
arrays, pretrained model state or training job were opened/launched during transfer verification.
Keep the handoff private and external to Git. Its README's proposed eight-hour cap plus
24,000-update ceiling is not equivalent to the user's at-least-eight-hour endurance request;
reconcile the duration design before launch while preserving safety stops and LR-horizon semantics.

## E: connected; PANORAMA acquisition and real-data endurance request

Quinton connected `E:/`, requested PANORAMA there and selected real-data PanTS training
for at least eight hours. E: is QUINN, NTFS, TOSHIBA External USB 3.0, volume GUID
`3daa84f0-0000-0000-0000-100000000000`, total 1,000,202,039,296 bytes and initially
1,000,064,032,768 bytes free. This resolves the archive-destination capacity blocker.

The new Windows CT-only downloader preserves the historical Mac acquisition implementation.
Nine new unit checks pass (HTTP range/size/encoding rejection, hash verification, complete
partial promotion and oversize preservation). It reserves 512 GiB, binds the volume GUID,
holds a Windows acquisition lock/awake request, requires AC, retains failures/partials,
validates pinned sizes and publisher MD5 and records local SHA256. No extraction, source
activation or label qualification occurs. Initial launch at 2026-10-09T02:33:24Z, owned
exec session 48517, destination `E:/PROWL/sources/panorama/acquisition-20261008/`;
follow its existing attempt JSONL before any action. No automatic duplicate/retry.

The eight-hour real-data training job has **not** launched. The original protected splits,
current Mac cohort manifest/review and pretrained checkpoint are absent from this checkout.
`D:/PanTS/data/ImageTr/PanTS_00000001/ct.nii.gz` exists (40,442,531-byte metadata observation);
the `D:/PanTS/data/LabelAll` directory lists no entries. This is not a label/content qualification.
No patient arrays were opened. Do not create a fresh random split to substitute for the Mac split.
Plan primary/cache on E:, independent checkpoint backups on C:, existing 100-GiB training
free floors. Actual prepared-batch and backup qualification precedes launch. The requested
eight hours is an endurance target, not authority to ignore errors, AC or resource stops;
step/time configuration must avoid a shorter fixed-step run masquerading as an eight-hour test.

Quinton authorized a request to the Mac Codex instance. The app's available chat inventory
does not expose that Mac training chat; no message has been sent. Ready-to-relay request:

> Prepare a minimal read-only handoff for the Lenovo's requested eight-hour real-data PanTS
> training test. Do not interrupt or take over the Mac training job. Include the exact original
> `outputs/splits/train.txt`, `val.txt`, `test.txt`; the current selected train/development IDs,
> manifest, cohort review, exclusions and source-use review from the admitted full-segmenter run
> (including dependencies of `outputs/prowl/full-segmenter-inputs-mac-20261007/`, not just that
> initial candidate directory). Provide a relative-path inventory with byte sizes and SHA256s,
> producing Git revision and run configuration. Explain which case labels are needed and
> where to obtain their original pancreas and pancreatic_lesion files: the Lenovo's D: has
> ImageTr CTs but LabelAll lists empty. Include or identify the pinned SuPreM checkpoint
> `supervised_suprem_segresnet_2100.pth` (expected SHA256
> `2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3`) and development-use
> limitations if using the same initialization. Do not publish patient data, weights, secrets
> or runtime artifacts to GitHub. Return the small metadata handoff and a private transfer
> plan; Lenovo destination is `E:/PROWL/transfer/`. Mac absolute paths/inodes will be rebound
> and checked locally, not accepted as Windows observations. The Lenovo CUDA environment and
> 144-cube synthetic save/restore smoke test have already passed; no real training has launched.

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
