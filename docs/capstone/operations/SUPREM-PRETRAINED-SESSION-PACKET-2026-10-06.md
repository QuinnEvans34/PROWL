# R03 draft — versioned pretrained session and independent recovery

October7 update: Quinton requested planning and implementation toward training. S01 now has a
[closed four-file invented session contract](../imaging/SEGMENTER-PRETRAINED-SESSION-CONTRACT-V1.md)
and [current result/sequence](SEGMENTER-PRETRAINED-SESSION-RESULTS-2026-10-07.md). Tiny invented
CPU mechanics are included only in that scope. S02–S04 and qualification requests below remain
proposals; actual source acceptance remains unresolved. The October6 draft is preserved below.

October6,2026. **Draft complete; implementation and qualification requests are not dispatched.**
[Value/initialization packet](SUPREM-VALUE-AND-INITIALIZATION-PACKET-2026-10-06.md);
[launch-readiness draft](SUPREM-TRAINING-LAUNCH-READINESS-2026-10-06.md).
Tracking: [W01-15](https://trello.com/c/9hAhaaF1).

## Why a new session is necessary

Current `segmenter_v5_training_session_v1.py` binds scratch hash3ee49a53, modefresh_random_only,
empty imports and an import-denial lineage. Its decoder also requires scratch atstep0. Its executor,
evidence and backup codecs bind old task/artifact identities and D-333 storage authority. Replacing
weights inside it would violate the qualified transaction. A new pretrained task/session/decoder/
keeper/executor is required; preserve every old producer, codec, request and source/test pin.

The new session starts atstep0 with accepted general-pretraining backbone and exact fresh3-class
seed42 head. Create **new AdamW0.0003/decay1e-5/constant** with empty optimizer state. Released
optimizer/scheduler/epoch and prior-project/capstone trained weights cannot resume this task.
Resume only a complete same-run checkpoint from this new session and immutable source lineage.

## Finite proposed implementation slices

Each row needs its own reviewed coding scope. No code is created by this draft. Close each named
contract first; tests use invented CPU tensors/inputs/roots only. Qualified numerical/geometry/
scorer helpers may be reused by exact pins if their preconditions apply; no old guard weakening.

| Slice | Exact proposed new-file allowlist |
|---|---|
| S01 session | src/training/segmenter_pretrained_session_v1.py; tests/test_segmenter_pretrained_session_v1.py; docs/capstone/imaging/SEGMENTER-PRETRAINED-SESSION-CONTRACT-V1.md; docs/capstone/operations/SEGMENTER-PRETRAINED-SESSION-RESULTS-2026-10-06.md |
| S02 keeper | src/operations/segmenter_pretrained_keeper_v1.py; tests/test_segmenter_pretrained_keeper_v1.py; docs/capstone/imaging/SEGMENTER-PRETRAINED-KEEPER-CONTRACT-V1.md; docs/capstone/operations/SEGMENTER-PRETRAINED-KEEPER-RESULTS-2026-10-06.md |
| S03 executor | src/training/segmenter_pretrained_executor_v1.py; tests/test_segmenter_pretrained_executor_v1.py; docs/capstone/imaging/SEGMENTER-PRETRAINED-EXECUTOR-CONTRACT-V1.md; docs/capstone/operations/SEGMENTER-PRETRAINED-EXECUTOR-RESULTS-2026-10-06.md |
| S04 dispatcher | src/operations/segmenter_pretrained_launch_v1.py; tests/test_segmenter_pretrained_launch_v1.py; docs/capstone/imaging/SEGMENTER-PRETRAINED-LAUNCH-CONTRACT-V1.md; docs/capstone/operations/SEGMENTER-PRETRAINED-LAUNCH-RESULTS-2026-10-06.md |

Qualification wrappers/requests are separate scopes after these implementations; their exact
allowlists, commands and frozen request pins must be reviewed then. Do not silently add real
providers or native forwards to unit tests. Unit checks may use tiny invented optimizer mechanics
only if explicitly included in that next coding scope; CPU learning/native jobs below are distinct.
Routine pointers are this queue/these packets/AGENTS/Trello; retrieval-owned work stays separate.

## Closed identity and interfaces

Proposed new task `pancreas_lesion_segmenter_pretrained_transaction_v1`, new schema/session IDs;
never claim compatibility with old scratch checkpoint identity. Proposed operations:

- `make_identity(config, checked_provider, controls, initialization_audit, *, run_id, device)`:
  validate all controls and source/task domain before constructing a session.
- `Session(identity, controls, initialization_audit)`: exact accepted step0 state or an invented
  audit for invented tests; fresh optimizer; bounded isolated RNG/sampler/history.
- `update(provider, *, exact_permit)`, `predict(image)`, `evaluate(provider)`: same validated
  role-safe/provider semantics, no raw tuple optimizer entry, dirty-state refusal.
- `payload(session)`, `restore_payload(files, identity)`, `resume(keeper, reference, identity)`:
  complete strict same-run decoder; immutable source/head lineage included in every checkpoint.
- `execute(request, provider, stores, *, exact_grant, guard)` and one-use dispatcher: all request/
  approval/pin/resource/storage preconditions checked before work; dirty state never published.

Close controls explicitly: inputs,source,environment,geometry,initialization,lineage,acceptance.
Session identity binds their canonical SHA256 values, config, domain,task,run ID anddevice.
Initialization binds source file SHA, normalized source/full-backbone SHA, R04/R05 results,
acceptance hash, fresh-head SHA, seed42, target complete state SHA and exact mapping policy.
Source acceptance is actual-only; invented controls cannot become actual by changing domain text.
No permission field is inferred from file presence or a hash. The sampler binds the same six-member
seeded epoch permutation policy as D-335, ordered membership and completed step/cursor.

Checkpoint controls plus identity/progress/state form a closed inventory. State contains complete
model, new optimizer, CPU and MPS RNG, committed step; progress contains every update/exposure,
loss/rate and batch hash, tensor evaluation history and exhausted/next sampler trace. Source audit
and exact fresh-head lineage are immutable through restore; no source-file reread is needed to
resume a complete accepted checkpoint. Step0 verifies pretrained target digest; later steps verify
full optimizer step/count/shape/dtype and same-run membership. Terminal is primary; no bestselector.

## Transaction, interruption and keeper behavior

Set dirty before any mutating forward/backward/update. Commit only after finite model/gradient/
optimizer checks and complete history accounting. A SIGTERM/fault during mutation retains the
journal and last durable checkpoint. Dirty state cannot infer, advance or publish; recovery starts
a fresh process from last-complete checkpoint. Repeated input/control/source/run changes refuse.
No automatic resume beyond the approved maxupdates/resource budget or a consumed dispatcher.

New artifact types bind pretrained task and source/head/acceptance lineage. Preserve domain-bound
primary/independent keeper/restore receipts, member hashes, request/derivation pins and complete
transaction publication. Older v5 artifact validators cannot certify the new task by changing a
label. A cold worker must be unable to access primary paths/descriptors under the qualified guard;
report the guard's cooperative nature. Exact restored artifacts and independent numerical oracles
are required. Copy completeness alone does not prove decode/recovery.

## Distinct measured qualification requests

| Qualification | Proposed work and original bars | Proposed envelope / pending facts |
|---|---|---|
| QCPU learning/restart | Fresh invented32-output source transformed to fresh3-class task; fixed sparse,multiple,boundary,outside,negative fixtures;480uninterrupted and actualSIGTERM30/fresh450restart (960calls total); original pancreasDice≥0.8,positive lesionDice≥0.65/recall≥0.8,everycomponent hit,negativeFPfraction≤0.02,lossratio≤0.8 | 400s combined/180s per trajectory/2GiB RSS;CPU LR0.001 is qualification-only; exactsource fixture/seed/requests/storage pending |
| QMPS mechanics | Fresh invented source/head,144³/nativeMPS/0.0003;0/2/4complete checkpoints plus one dirty-fault branch and bounded next-update equivalence; record exactcall budget beforedispatch | 600s combined/12GiB RSS and12GiB driver;no fallback,AC,100GiB free floors;storage/request/identity pending |
| QFULL executor/recovery | Entire invented144³48-update transaction, seven invented image/native exports, all keeper/restore members, four checkpoints and fresh-process recovery/next-update proof | 1800s total/1200s producer/300s cold,12GiB RSS/driver;exactprimary/backup/restore caps need measured rehearsal |
| QBRIDGE actual source/cache | Accepted R05 initialization plus existing exact6/1qualified cache binding and retained geometry; shape/role/identity checks with0forwards/0updates first | Separate source/cache read allowance,byteshash/decoding/currentvolume/free-space/resource requests **pending** |
| QZERO actual inference | If needed after bridge: exact7cache-only image forwards/native inverse,exports,independent recovery; target scoring only under separately exact14-target scope | Not included in bridge/unitpermissions;fresh source/target/keeper budgets and approval required |

QCPU fixtures are invented general-pretraining inputs and remain in that evidence domain; no
learned synthetic checkpoint ever initializes real CT training. The recipe/fixture definitions and
acceptance criteria must be frozen **before** a request. A failure preserves all outputs and stops
that branch before MPS/real access. No optimization sweep, lost difficult case or relaxed gate.
QMPS/QFULL invented native checks establish mechanics/resources; their contours are not real-data
performance. Current Windows is unqualified for these MPS/macOS monitor paths.

Recovery requirements: CPU complete state/predictions exact; same completed sampler/history and
next input; native probability delta≤1e-6, argmax/native mask exact, next-weight maxdelta≤1e-7
(proposed tolerances, freeze after numerical review). Original baselines' tighter observed deltas
are evidence, not an automatic guarantee. Test mismatch handling and every resource stop.
Actual real cold recovery replays all required artifacts and seven predictions with0updates and
0original reads; it makes **no real next update**. Establish next-update recovery on invented paths.

## Matched scratch compatibility and storage stop

Before calling the eventual48-update result an initialization comparison, demonstrate unchanged
loss/optimizer/sampler/geometry/evaluation and fresh-head seed behavior against pinned D-335 code.
An invented same-input scratch-control replay through the new mechanical path may qualify parity;
its actual call count requires a separate request. Compare complete updates/state/outputs within
frozen device tolerances and preserve any mismatch. R01 unit tests prove none of this.

If changes beyond initialization remain, the comparison is inconclusive; propose an explicitly
approved matched fresh scratch control instead of rerunning the consumed D-335 request. No extra
scratch run or duration192 job is inferred. Storage includes that possible additional control.

Fixed whole-backup ceiling18,318,645,873B/registered20GiB cannot increase here. Historical post-
preservation occupancy17,341,924,636B leaves976,721,237B, **not current capacity**. The historical
583,041,786B full one-copy real payload implies1,166,083,572B for both keeper and full restore,
already more than that historical remainder before qualification/failure reserves. Proposed new
lineage may change payload sizes. Current occupancy/free-space/mounts are null until preflight.

Therefore budget every qualification and real run cumulatively before external writes. If the
full-copy protocol cannot fit, obtain a separately reviewed independent destination or qualify a
concrete alternate cold-read protocol; preserve existing evidence and keep the ceiling fixed.
Do not quietly omit recovery members, delete outputs or count space on another filesystem as
available under an unapproved writer. [Launch draft](SUPREM-TRAINING-LAUNCH-READINESS-2026-10-06.md)
keeps this as an explicit readiness gate.
