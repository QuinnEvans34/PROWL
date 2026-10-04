# Qualified localizer run bridge and recovery verification

D-273, September 28, 2026: Quinton requested connection of the qualified cohort to MPS,
production checkpoints/backup recovery and a finalized smoke launch plan. This authorizes
bounded integration verification and scoped artifact/backup writes, not the first real training launch.

## This verification

Resolve the existing frozen cases 3/26 through the D-270 factory. Read exactly four CT/pancreas
files once (23,331,170 compressed bytes). Create one 96³ supervised patch per case, transfer to MPS,
check finite two-channel forward output without optimizer updates; record provenance/transform hashes.
Do not score, select or optimize on these prelaunch outputs. Separately perform two synthetic updates,
publish a full checkpoint to prowl_artifacts/localizer-runs, copy its exact validated payload/control
snapshot to prowl_backup/localizer-keepers and restore into a new localizer-restores artifact. Recovery
must open only the backup, instantiate/load MPS and compare fixed synthetic probabilities at atol1e-5.
A further synthetic update checks restored optimizer/scheduler state; no trained rehearsal initialization
will be reused by CAP-EXP-001. Backup catalog includes all members and source receipt, volume identities,
operator/authority and omissions. Restore creates a separate receipt; no mutation of the backup catalog.

Limits: 600 s, 16 GiB RSS and MPS allocation, 1 GiB primary and 1 GiB new backup/restore allowance,
20 GiB existing total backup cap, 100 GiB internal floor; external reserve max(100 GiB,10% device).
Single cooperative accelerator owner, AC power, fallback disabled, no raw-source changes or global
registry activation. Dedicated capability pins both volume UUIDs and unchanged registry SHA. Preserve
failed attempts and all prior data/evidence. No install, Git push, remote upload, literature work or emails.

Owned code: new training bridge and scoped run storage/backup modules, checkpoint validation helper
extraction preserving the old CPU public contract, diagnostic script/tests and shared records. Tests
must cover wrong run/input/recipe, corrupt/partial checkpoint, real-update launch gate, backup scope,
unsafe paths, capacity/device checks, same-domain refusal and backup-only recovery.

## Proposed CAP-EXP-001 scope to finalize afterward

Private scratch binary pancreas localizer smoke on the exact two-case frozen cohort; 96³/batch1/fp32,
seed42, equal foreground/background centers, deterministic alternating member order, no cache/workers/
augmentation, 100 updates maximum. AdamW LR0.003/wd1e-5 and 100-step cosine horizon are engineering
smoke settings, not baseline-optimal choices. Before/after image-only full-volume training-cohort loss,
foreground Dice and source-grid masks; no validation/test or generalization claim. Save step0 and every
25 updates, final keeper plus controls copied to independent backup and consumer restore verified.
10-minute update/20-minute end-to-end ceilings, 16 GiB memory, 1 GiB output reserve and 25% forecast
contingency. Review exact evidence and launch record before any real optimizer step.
