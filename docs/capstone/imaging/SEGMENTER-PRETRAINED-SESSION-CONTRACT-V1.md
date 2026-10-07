# S01 — invented pretrained session contract

Closed October 7, 2026 before implementation. Owner: imaging Codex.
Quinton requested: “Tell me what we need to get done before this. Lets plan this out, and get it
done,” following the recommendation to prepare the pretrained session/recovery coding scope.
This authorizes this bounded engineering slice and its tiny invented CPU unit mechanics.
It does not authorize actual source access, source acceptance, a scientific qualification or training.

## Exact scope

Create only:

1. `src/training/segmenter_pretrained_session_v1.py`
2. `tests/test_segmenter_pretrained_session_v1.py`
3. This contract.
4. `docs/capstone/operations/SEGMENTER-PRETRAINED-SESSION-RESULTS-2026-10-07.md`

Routine pointers: AGENTS, the live readiness and Week 1 queues, the existing session packet,
Trello and this chat's existing automation. Preserve all 296 prior protected pins, scratch
consumers, consumed requests, failures, dataset membership/holds and the experiment-log tail.
No keeper, executor, dispatcher, actual-value reader or retrieval code in S01.

## Identity and initialization

Task: `pancreas_lesion_segmenter_pretrained_transaction_v1`.
Identity/config/progress/state schemas have distinct `segmenter-pretrained-…-1` names.
Input domain is exclusively `invented_arrays_only`; only the exact InventedInputs class is
accepted. Source initialization must be a validated V02-I InitializationAudit, with generated
source domain, exact complete 83-tensor target, full 81-tensor backbone and seed42 fresh head.
Actual candidate SHA or a relabeled actual/source/input domain is rejected before model allocation.
There is no actual permit or real-provider branch in this version.

Config binds the D-335 recipe: 24³ or 144³ shape, three-class SegResNet, float32, seed42,
class-normalized loss, AdamW LR0.0003/weight decay1e-5/constant schedule, max1–48 updates,
six-member seeded epoch permutation, no jitter, terminal primary. It is a new transaction,
not a scratch checkpoint relabel. 24³/CPU is the only execution in this unit packet.
144³/MPS code paths are unqualified until separate frozen native requests pass.

Controls are canonical UTF-8 JSON bytes: inputs, source, environment, geometry, initialization,
lineage, acceptance. Identity binds every control hash plus run ID/device/config. The source
control records generated source and values-audit identities; initialization retains the complete
V02-I report. Lineage names exact backbone/fresh-head policy and denies teacher/prior-task imports.
Acceptance explicitly says invented fixture, actual source unresolved, training eligible false.
Environment binds torch/MONAI versions and immutable helper pins; geometry binds fixture shape,
ROI source and no-original-read/no-jitter policy. Arbitrary additional fields refuse.

Factory, typed initializer, value auditor, checked input provider, numerical helper, loss, scorer
and six/one progress/sampler helper are pinned to the reviewed bytes. Reuse only their applicable
invented numerical/role/formula checks; do not reuse scratch initialization validation or artifact
types to certify this task. The original scratch code remains unchanged.

## Session and transaction

`make_identity(config, provider, controls, initialization_audit, *, run_id, device)` validates
the typed audit and controls. `Session(identity, controls, initialization_audit)` strict-loads
owned target state, verifies digest/head/backbone lineage, and creates a fresh empty AdamW.
No released optimizer/epoch/scheduler is imported. Session/controls/fixture state cannot alias
the audit's storage. Preserve caller RNG during factory construction and every operation.

`invented_permit(identity, request_sha256)` creates a cooperative typed unit permit bound to
this immutable invented identity and a nonempty 64-hex request digest. It is not human approval
or a security sandbox. `update(provider, *, exact_permit)` requires it before observing inputs.
Check provider class/control/role, batch seal, hashes, shape, normalization and classes before
mutation. Set dirty before forward/backward/optimizer mutation. Commit step/history/RNG only
after finite loss/gradients/model/AdamW and complete row accounting; failure remains dirty.
Dirty state cannot update, predict, evaluate or serialize. Same-run restore is the recovery path.

Predict/evaluate accept only checked invented CPU arrays/providers. Evaluations bind integer
confusion/component counts and immutable reference metadata. Report-only evaluation does not
choose a checkpoint, tune a recipe or enter optimizer sampling. Duplicate/out-of-order evaluations
refuse; terminal remains primary. Explicit fresh-state digest is required at step0.

## Checkpoint codec

In-memory payload inventory: seven controls + identity.json + progress.json + state.pt.
State contains full model/AdamW, CPU RNG, optional MPS RNG, immutable identity digest and step.
Progress includes every committed update, losses/LR/batch hashes, role-bound evaluations,
exposure counts and next/exhausted sampler trace. No best selector or partial resume.
Decoder requires externally supplied exact same-run identity and canonical control/progress bytes;
restricted `torch.load(weights_only=True, map_location='cpu')` only for the bounded payload bytes.
Control≤1MiB each, identity≤1MiB, progress≤4MiB, state≤64MiB, whole payload≤80MiB.
Validate complete model names/shapes/float32/CPU/finite tensors; step0 digest must match typed
initialization. Later model values may differ through updates, while initialization controls stay
immutable. AdamW must have exact groups and per-parameter moments/step matching completed step;
CPU RNG must be accepted by a temporary generator. Native restore is unqualified in this packet.

`payload`, `validate_payload`, `restore_payload` operate on bytes only; no filesystem publication
or independent keeper claim. Fresh-process decode/prediction is tested using an invented tmp root;
this does not establish primary-path isolation, SIGTERM recovery or native-sized resource fit.

## Meaningful unit checks and envelope

Freeze before executing: typed full-backbone/fresh-head and empty optimizer; no audit alias or
caller RNG mutation; actual/forged domains and control substitutions reject before allocation;
exact sampler/recipe compatibility; checked train-only updates; dirty fault after optimizer
mutation; last-complete decode and next update/prediction/state/history equality; fresh-process
restore; malformed head/optimizer/RNG/progress/lineage/payload/control bounds and dependency pins.
No repeated old test suite. Generated fixtures may reuse V01-I/V02-I fixture preparation for this
new integration, without rerunning their old successful tests or reading any actual checkpoint.

At most 12 tiny CPU optimizer calls (including dirty failures) and 24 direct session forwards
in one test attempt; no learning threshold experiment. Native monitored targeted pytest envelope:
300 seconds, 3GiB sampled pytest+owned descendant RSS, 50ms polling, one-thread CPU defaults,
no network/MPS/real roots. Stop/reap owned workers on monitor/time/RSS failure and retain outputs.
After a code/test correction, repeat only this changed slice with a separate retained attempt log.
Successful unchanged checks never rerun to fill idle time or generate commits.

## Finish and next dependencies

Report exact tests, call counts, wall time/RSS, failures and source/test/contract pins. Update and
read back the task card; make one reviewed local completed-work commit. No push from this scope.
Actual source acceptance remains unresolved; B03 stays consumed/pass. S02 keeper is next for
concrete review, followed by S03 executor and S04 dispatcher. Their implementation, qualification,
actual values/cache bridge, current external storage inventory and exact launch remain distinct
scopes. Stop at this handback unless Quinton approves the next concrete scope.
