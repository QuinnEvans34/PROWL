# Expanded runner readiness results — September 29, 2026

D-284 integration/profile slice complete. Exact frozen16 training/11 validation members reached
MPS through the new bounded role cache; all27 full-volume forwards passed. Zero real optimizer
updates. Expanded training launch remains a separate unfinished executor step, described below.

## What changed

`src/training/expanded_localizer.py` adds a512-MiB processed cache of owned float32 images/uint8
pancreas labels, with exact descriptor/recipe binding and defensive copies. It prechecks disjoint
roles, reads each source pair once, detects changed arrays/records and schedules only training
members. Complete-role evaluation reports all members. The new checkpoint codec binds both role
inventories, cache policy, recipe, config, source/environment and completed update history. Synthetic
continuation is executable; real updates are refused until the launch executor is implemented.
`expanded_localizer_profile.py` provides pinned single-use supervised forward profiling and a
fresh-process checkpoint recovery command. Old v1 loader/preprocessor/run/smoke source bytes were
compared with D-283's capture and remain identical. No original cohort membership changed.

## Measured native evidence

| Check | Result |
|---|---:|
| Full native regression suite | 1,155 passed; two existing warnings;17.77 s |
| New runner tests | 9 passed |
| Exact source files / real updates | 54 / 0 |
| Cached image+label bytes | 200,844,985 (191.5 MiB) |
| Verification + complete cache load | 209.28 s |
| Training-role full-volume forwards | 16 cases /8.97 s |
| Validation-role full-volume forwards | 11 cases /6.49 s |
| Supervised profile total | 227.31 s |
| Peak sampled RSS | 5,936,840,704 bytes (5.53 GiB) |
| Fresh-process saved-checkpoint probe difference | 0 (synthetic step3 and real-input step0) |

Synthetic MPS96-cube updates measured1.085 and0.871 s (only two timed samples, not a robust
throughput distribution). The continuation check made four actual synthetic updates: two initial,
then the same next update on uninterrupted and restored sessions. Both selected training member2
with identical sampling/loss trace. Parameter max absolute difference was3.725290298461914e-9,
within the documented1e-6 tolerance. CPU continuation was bitwise equal. The first MPS attempt's
bitwise-weight assertion failed; that failure and follow-up are retained in the experiment log.
Do not describe MPS continuation as bitwise reproducible. Fresh-process predictions from each
saved checkpoint were exactly equal to their saved probes.

The real model was freshly initialized. Its mean Dice was0.00064 on training-role inputs and
0.00095 on validation-role inputs; these are untrained resource-profile outputs, not evidence of
learning or a basis to change thresholds, loss, membership or the next experiment's design.

Nine new tests exercise single source loading/defensive copies, all-member cycling, invalid roles,
cache cap, wrong loaded provenance, exact CPU resumed next update, separate complete validation,
identity/input/history/inventory tampering, refusal of real updates and artifact corruption.

## Evidence and independent storage

Successful request: `outputs/prowl/expanded-profile-request-b9644313-c69e-4339-93c0-ae7c45207bac`,
SHA `e88dddb361b73092e693700ea1dc70d4287f399bce0f68034621b4fb5b067c8d`.
Profile: `outputs/prowl/expanded-profile-aa667930-da3a-4874-b6b5-b28b0d9ee79a`,
receipt `0a5f3335a46beabed727b4f2d4f662d80043873c94636b399e1ae64d2e8d99da`.
All15 receipted payload files independently checked for bytes/hash. Source/environment were
rechecked at completion. The checkpoint receipt is
`a6de458a50082f88fece5d1bc42afdcfefced8e378f1f7c43310cbf0b08a28d2`.

Synthetic checkpoint: `outputs/prowl/expanded-synthetic-ee42cf80-2321-4b7f-a645-f12115ee55a4`,
receipt `324f523042fc70a3f84db0f313374402ea5fa43d7691f470454cd35086317b8b`.
Synthetic backup evidence: `outputs/prowl/expanded-synthetic-backup-d284-20260929`;
backup receipt `23aa10d29ce693de5ca3fc9f97cb04f6be3aacc062441f56556d47c548dcd476`.
Real-input step0 backup evidence: `outputs/prowl/expanded-profile-backup-d284-20260929`;
primary receipt `98d50afc5462f75f003418e611b276e634e187aab46da1e8603e35dcc3460a42`,
backup receipt `c73495799506e70613e8e12fa87f9cd56705162f019e4a6f68675fe76ad7270e`,
restored receipt `2a8b2444cbf4fd9130ad766a0c54fa6af0e14abe6fad1e9f813720ee7b73e403`.

Both checkpoints published to the registered external artifact area and independent internal keeper
area under the existing D-273 storage capability, as scoped by the D-284 storage-check document.
Recovery-only store construction and a new restore destination produced byte-identical payloads;
the restore API had no primary-store argument. No physical drive unplug test was performed.
Verification scripts and hash receipts are retained beside the backup records. This exercises
expanded identity and optimizer-state storage; it does not certify future trained model quality.

## Next concrete implementation

[CAP-EXP-005 proposal](CAP-EXP-005-PROPOSAL-2026-09-29.md):288 updates/18 equal training cycles,
fresh seed42 balanced recipe, complete separate validation. The measured profile supports retaining
a20-minute total/10-minute update envelope with16-GiB RSS, subject to final executor verification.
No new input qualification or broad data investigation is needed for these27 members.

Remaining work is the expanded experiment transaction: bind the actual launch controls; connect
real updates to this role schedule; preserve interval checkpoints and interruption state; compute
the predeclared localization metrics; restore predictions to native grids; publish per-case exports
and terminal/backup references within existing caps. Test that transaction on synthetic fixtures,
then freeze the exact source/plan/request. Current readiness APIs deliberately refuse real updates;
CAP-EXP-005 is not launch-ready merely because the profile passed. Frozen case6350 hold, difficult
cases, validation stratum gap and study-as-subject limitation are unchanged. Literature work and
Git publication were untouched.
