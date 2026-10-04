# Next slice — finish and qualify the short segmenter launch

D-326 has qualified the separate training session, role-safe cache boundary, sampler, dirty-state recovery and independent checkpoint/probe protection. See [results](SEGMENTER-TRAINING-TRANSACTION-RESULTS-2026-10-02.md). This packet describes the remaining executor work; it is **not a frozen training request or authorization for real updates**.

The next useful experiment is a short learning diagnostic on six training cases and one development-validation case using a provided pancreas-reference ROI. It will answer whether this three-class segmenter starts learning real CT supervision with the candidate objective. It will not establish autonomous cascade performance, specificity or generalization. Preserve D-319–326 producing pins and all previous requests. Implement separate wrappers and stage contracts rather than changing accepted producers.

## Candidate comparison to make executable

|Item|Proposed choice; freeze only after qualification|
|---|---|
|Members|Train 3, 26, 2232, 2973, 5821, 6238; evaluation-only 2514. All twelve permanent candidates/five holds and localizer 153/23 unchanged.|
|Inputs|Accepted D-323 cache and D-320 protected ancestry; D-321 pancreas-reference ROI/144³/float32/batch1/zero jitter. No original CT rereads.|
|Initialization|Fresh random seed42, exact initial hash `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`; no historical, synthetic-trained or third-party warm start.|
|Objective|D-322 v3 weighted CE `[1,1,256]` plus mean present-foreground Dice; exact reductions/absent-class behavior remain those of the pinned numerical helper. Candidate, not an established real optimum.|
|Optimization|AdamW, weight decay1e-5, constant learning rate0.0003; 48 committed updates, eight complete six-member epochs. No validation-driven rate/threshold changes.|
|Sampling|D-326 deterministic permutation each epoch. Exact per-case exposure8 at terminal; validation never optimizes.|
|Required checkpoints|Propose steps0,6,24,48 with complete same-run model/optimizer/CPU-MPS RNG/sampler/history/configuration/evaluation identity. Terminal48 is the primary comparison.|
|Tensor evaluations|Propose steps0,6,24,48, all seven members. These are diagnostics; they do not replace original-native truth.|
|Native comparison|Protected D-325 before scores, plus one fresh fourteen-target final scoring pass for all seven terminal exports. Intermediate native reads are not proposed.|
|Completion|All48 updates and declared evaluations/checkpoints/keepers/recovery complete; finite numerics and lineage/resource controls pass. Weak or failed learning is a retained experiment result.|

The rate and duration keep the first real comparison bounded. D-326 measured two invented MPS updates at 2.587/2.448 seconds each, but total time includes ancestry replay, evaluation, serialization, native target reads and independent recovery. Do not extrapolate a launch cap from update timing alone. No longer run or extension is implicit.

## 1. Exact request and launch dispatcher

Add a versioned executor with a canonical, closed request schema and completion-last publication. Bind source/runtime, new task, D-325 before baseline, accepted cache/cohort/descriptors/geometry, denied-import inventory, full configuration, role membership, sampling, checkpoint/evaluation points and every resource/keeper/read limit. Request hash must cover the exact persisted bytes including canonical newline.

Keep readiness APIs closed. A real `UpdatePermit` can only be issued by this dispatcher after validating the exact launch request and its separately recorded user launch decision. Check identity and source controls before the first update, at declared boundaries and before publication. Invented rehearsals must not issue a real permit. A consumed request cannot restart from scratch or silently run again.

Test altered task/head/domain, missing or forged approval, wrong request hash, stale source/runtime/cache, validation-as-training, held/extra cases, duplicate consumption, changed rate/sampling/cadence and missing required artifacts. Retain all failed attempts. Interrupted launch handling needs an explicit continuation record tied to the same committed run state and remaining original budget; do not reopen the original consumed request.

## 2. Transaction and interruption wiring

Use the accepted D-326 session and input provider. A checkpoint boundary comprises committed update, tensor evaluation where declared, checkpoint publication and verified keeper copy. Never report an incomplete boundary as durable. Inject failures before mutation, after optimizer mutation, during checkpoint publication and during backup publication. Dirty state must reload the last complete same-run checkpoint, including RNG and exact next member; unfinished attempts remain evidence.

A cancellation/resource failure stops further optimizer calls and original reads. Preserve last complete checkpoint and failure/counters; an interrupted outcome is not terminal success. Define supervisor termination and flush/kill handling, fallback/power/device checks, CPU/MPS memory ceilings and free-space guards. Check every predeclared boundary rather than relying only on a terminal call.

## 3. Original-native final evaluation contract

Use a fresh task/stage-specific target-only reader wrapper. D-325's source request is consumed; its payload/approval cannot authorize this stage. Pin exactly the original fourteen pancreas/lesion paths, registered roles, original hashes and source observations. Perform stat-only preparation first; if metadata changes, use a separately evidenced reconciliation rather than rewriting old observations.

If files remain identical, expected aggregate scope is 1,265,220 compressed bytes for hashing, 1,265,220 for decoding and 272,494,704 expanded bytes. Recompute these from the frozen evidence before approving the actual request. Reserve complete paired reads before opening payloads, enforce no-follow observations/hash/gzip CRC/header/scaling/binary semantics, and forbid CT/extra paths. Existing original-source numerical helpers may be reused; do not edit accepted D-325 readers or relabel cached targets as original truth.

Export all seven terminal predictions through the accepted continuous three-channel source-grid inverse before argmax, with background outside the provided ROI. Bind each export to its committed step, exact trained weight hash, role, image/transform and source geometry. The old inference exporter records step0 in its report: use its geometry codec through a new training export contract that truthfully records step48. Do not publish step0 metadata for trained predictions.

Keep original lesion precedence, outside-pancreas voxels, all 26-connected reference components and empty/oversized/wrong predictions. Independently replay per-case confusion/class counts, parenchyma/lesion/union Dice and recall, component sizes/bounds/hits and six-case macro/pooled aggregates. Report the lone validation case separately. Preserve tiny2973 and boundary6238 in every denominator. Review all seven terminal native overlays with fixed source geometry and reference/prediction identity.

## 4. Protected evidence and measured budget

Declare required full-state checkpoints, immutable request/configuration/lineage, objective/sampling/evaluation histories, all seven native predictions, original-native scores/references/counts and a reproducible task probe. Cached tensors, reference arrays and rendered views may remain rebuildable scratch; required numeric/provenance records and predictions need independent keepers.

Calculate actual payload, per-artifact maximum, primary/keeper/restore/control bytes and `2×payload + 2MiB` retry reserve before freezing a fresh stage capability. Account for existing D-326 occupancy: 518,961,193 bytes in its primary area and 11,283,770,932 bytes in the independent root at review. Those are historical observations, not available capacity grants. Do not reuse/reset the qualification-only D-326 ceilings, delete failures or infer real-update authority from its capability. Original registry/physical domains remain fixed.

Rehearse the entire executor on invented six/one data, including all checkpoint/evaluation boundaries and maximum native-grid exports/scoring. Verify every required keeper in a fresh process with accepted descriptor-aware primary denial, exact member bytes/semantics, prediction/native replay and next-update tolerance. Measure total worker/supervisor time, peak CPU RSS and MPS allocated/driver memory, output/read counters and protected occupancy. Then derive the exact real launch limits with explicit margin and backup recovery reserve. A 30-minute total/12GiB RSS/driver envelope is only a planning candidate until this end-to-end rehearsal qualifies it.

## 5. Reviewable exit and interpretation

Run meaningful refusal/analytic/transaction tests and the full native suite after executor changes. Independently audit predecessor pins, all request/artifact members, exposure and read/storage accounting. Freeze one concrete request and present its hash, exact 48-update recipe, total limits, final fourteen-target scope, keeper inventory and cancellation/recovery plan for the user's separate launch decision.

Before launch, freeze learning screens: compare terminal training lesion macro Dice and recall against D-325, record each case/component's direction and failures, and report pancreas/union behavior. These observations guide a later named-factor experiment; they do not decide eligibility or choose a checkpoint using one validation case. If there is no useful learning signal, inspect training inputs/gradients/exposure/objective before proposing longer training. There is no automatic extension or promotion. Pre-course engineering remains separate from formal post-October5 experiment registration.
