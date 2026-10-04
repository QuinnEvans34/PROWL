# Qualified-input MPS bridge and independent recovery handback

September 28, 2026. **Both qualified cases reached MPS, and a full synthetic checkpoint was
published on the external primary, backed up internally, restored into a new destination and consumed
in a fresh MPS process with primary-file access refused.** No real optimizer update occurred.
D-273 authorizes this verification; [pre-execution plan](LOCALIZER-RUN-BRIDGE-PLAN-2026-09-28.md).
The [CAP-EXP-001 launch design](CAP-EXP-001-LAUNCH-PLAN-2026-09-28.md) is now written for review.

## Changes and trust boundaries

- `src/training/localizer_run.py`: exact frozen-descriptor/recipe binding checked before raw reads,
  MPS forward/inference and synthetic rehearsal updates, v2 run/control/checkpoint payload. Unknown
  cohort, changed input/source/environment control or checkpoint identity is rejected. Real updates
  remain explicitly refused by this prelaunch entry point; it is not a ready real-training CLI.
- `src/training/localizer_checkpoint.py`: extracted shared tensor/optimizer/scheduler validation into
  `decode_state`; the old CPU public identity/codec behavior and tests remain unchanged.
- `src/operations/localizer_run_storage.py`: scoped registered primary, independent backup and fresh
  restore areas, pinned capability/registry/UUIDs, no-follow paths, quotas including hidden attempts,
  cooperative quota locks, free-space floors. Recovery-only factory does not require a primary path.
- `src/operations/localizer_backup.py`: verify a complete primary, retain original payload/completion/
  attempt journal in an independent backup snapshot/catalog, then publish/reread a new restore copy.
  Backup validation checks member hashes, original completion, catalog and checkpoint semantics.
  Consumer restoration creates a separate receipt; it never edits the original backup catalog.
- `scripts/diagnostics/localizer_run_bridge.py`: supervised real-case forward checks, synthetic
  checkpoint/recovery drill, source/identity capture and retained failures/results. Existing global
  `scientific_runs_enabled: false`, source aliases and cohort-only capability are unchanged.

Capability: `LOCALIZER-RUN-CAPABILITY-2026-09-28.json`, SHA-256
`e2651188827877d11888d13e7e0e3555b83b97816c9f10d0db6820ab002d3486`.
It allows the bounded verification under D-273, not real-data training. Added ordinary areas:
`prowl_artifacts/localizer-runs`, `prowl_backup/localizer-keepers` and `prowl_backup/localizer-restores`.
The backup remains subject to the shared 20 GiB cap and 100 GiB internal floor, with no auto-deletion.

## Real input connection

The D-270 factory re-resolved the complete frozen cohort and its qualified-purpose evidence, then
read exactly four CT/pancreas files, **23,331,170 compressed bytes**. Cases 3 and 26 became normalized
single-channel volumes of 136×96×98 and 108×96×134. Each supplied one aligned 96³ image/target patch
and produced finite two-channel MPS output. Load/preprocess observations were **1.159 / 1.053 s**.
Every model parameter was compared before/after: unchanged; optimizer step remained zero.
The probes were not scored or used for model selection. They do not establish full-volume accuracy.

## Checkpoint and restore evidence

A separate invented 96³ cube supplied two synthetic optimizer updates. The checkpoint includes model,
optimizer moments, scheduler, completed step, CPU RNG state, stateless sampler policy/config and exact
inputs/source/environment controls. No dropout or worker randomness; bitwise MPS continuation is not
promised. This diagnostic's weights must never initialize CAP-EXP-001.

| Stage | Result |
|---|---|
| Primary publication | Five payload members, 56,588,714 bytes; 1.108 s |
| Independent backup | Eight members including original completion/journal/catalog, 56,591,741 bytes; 0.701 s |
| Fresh destination restore + MPS consumer/probe + synthetic update | 2.412 s inside recovery stage |
| Restored probability difference | **0.0**, tolerance atol1e-5/rtol0 |
| Restored optimizer/scheduler continuation | Synthetic step 3 passed; finite loss 1.26738 |
| Whole supervised verification | 50.583 s; both workers exit 0 |
| Peak sampled worker RSS across stages | 2,230,730,752 bytes (2.078 GiB) |

Primary and backup are distinct registered APFS volumes/devices (external UUID
`22750B93-2F3F-499D-87F5-902981BFAB59`; internal UUID `542E8B1F-8D50-4783-9250-752DFDC899CD`).
The recovery process refused primary-file opens/listings with an audit hook and used a recovery-only
root resolver. Primary was not physically disconnected. Unit coverage also uses an absent primary
path. This is logical primary-unavailability recovery evidence, not a hot-unplug/endurance test.
The saved expected probe is independent local diagnostic evidence, not a primary checkpoint read.

Primary receipt: `9805e38d040fddf3eaa602ad1e814b8c62aee5966abc478fdd3a8ea535e6395c`.
Backup receipt: `ccab4ec289285dd007376d25092a9367deb1232853206cc1e6900f6c69d32d9d`.
Restore receipt: `c325f7738ad3685ffb8bbe549fe8afbab2b988ef65e72553af1c27eaa600b580`.

Physical artifacts:

- `/Volumes/PROWL-Data/PROWL/artifacts/localizer-runs/460355fe227d452496ab33f2c828954c6b7c492ed62941b6be73076f453952ce`
- `/Users/quintonevans/PROWL-Backups/localizer-keepers/0809d7fc63e45f587fd3e3c7f6c8e624ccab3d77b5999d21bdd6e2b9e2670c33`
- `/Users/quintonevans/PROWL-Backups/localizer-restores/6fbd5e3d7eb75baffc14f3cec5c4c866bb881bf4cff0935230e78e2db7970e4c`

All three completion pins, covered member hashes/lengths and journals were independently reread and
verified after the drill. The backup protects this checkpoint and its embedded controls; it is not a
mirror of raw CTs, the entire qualification history, all earlier evidence or the whole project.

## Diagnostic package, failure and tests

Success package: `outputs/prowl/localizer-bridge-447b7a35-9f76-415c-8c7c-dc8259834e05`.
Receipt: `5b5b08fddc3cc3e7abb5baf5f8432056e2d63bd0d88b39f13df8bb5baaa1dba5`.
Ten covered files / 7,161,441 bytes, plus receipt; all hashes independently verified.

Earlier attempt `localizer-bridge-82b808b7-f79e-4850-9e98-53ad3829de08` failed before source reads,
model creation or checkpoint writes. `Path.is_mount()` returned false for the registered internal
macOS APFS Data mount. Native diskutil and mount-table identity confirmed the correct writable UUID
and `/dev/disk3s5 on /System/Volumes/Data (apfs, ...)`. The correction uses the exact native device/
mount/filesystem entry when the internal-volume heuristic fails; all UUID/device/writable/capacity
checks remain. Failure request/log/supervisor evidence is preserved. No replacement root was created.

**1,062 native tests passed**, two existing torch.jit warnings, 16.22 s; sixteen new bridge tests.
Tests cover bound-input/control mutation, run identity mismatch, held member, real-update refusal,
independent-device requirement, corrupt backup, backup-only restore, no-follow capacity inventory,
quota failure before publication, absent-primary recovery and native APFS mount matching. Full native
command is unchanged. `git diff --check` passes. No dependency, raw source, Claude file or Git commit/push.

## Concrete remaining work

The input and storage/recovery uncertainties are retired for this scope. The finalized launch design
specifies 100 updates, the two cases, scratch seed42, 96³/batch1/fp32, AdamW LR0.003, cosine100,
before/after full-volume loss/Dice/native-grid review, checkpoints every25, independent terminal
restore, 10-minute update and 20-minute total ceilings, 16 GiB memory and 1 GiB output reserve.
Production publication measured here is about 1.1 s/checkpoint and backup+restore about 3.1 s; even
five checkpoint publications plus terminal recovery add roughly nine seconds before contingency.
These are small-snapshot observations, not guaranteed later storage latency.

**Next implementation:** the bounded real-update loop and terminal evaluation/export wiring against
this plan, including synthetic tests and source capture; then launch approval is the final action.
This coding is within the already requested training connection scope and needs no renewed design
approval. It remains explicitly listed rather than presenting the forward-only bridge as a complete
real-training executable. The actual first real run remains unlaunched and unapproved. The design
must not be broadened while finishing that small executor. No unrelated product work blocks it.
