# SuPreM initialization qualification — concrete next packet

**Prepared:** October 6, 2026. **Owner:** this Codex imaging chat / Quinton.
**Authority:** Quinton approved preparing this packet with “Great, lets move forward with that
then.” This approves the repository-text/control review and drafting handback. **SUP-01 below is
proposed implementation, not dispatched.** No checkpoint payload, model forward/update, acquisition,
real import, scientific request, Git publication or external writer is authorized by this document.

**Later October6 implementation approval:** after the drafting handback Quinton said “Great, move
onto the next.” SUP-01's exact four-file invented-only coding slice is now approved. Earlier
proposed/not-dispatched wording records the drafting state; source qualification and real-session
integration remain separate. Stop after the SUP-01 implementation handback.

**SUP-01 delivered:** the
[implementation handback](SEGMENTER-INITIALIZATION-AUDIT-RESULTS-2026-10-06.md) records85targeted
invented checks and measured CPU resources. The historical proposal below remains the approved
design record; actual-source and pretrained consumer qualification remain open. No follow-on scope
is dispatched by its completion.

## Outcome and recommendation

The current scratch segmenter and the historical SuPreM-compatible model use the same declared
SegResNet backbone configuration. A head-replacement initialization is plausible; the actual
candidate's tensor inventory, source rights and protected-evaluation relationship remain unverified.
Implement a separate **SUP-01 in-memory initialization auditor** with invented CPU tensors first.
Then review a bounded actual-source/serialization audit. Keep the current scratch consumer closed.

This follows the [October 6 method review](../../experiments.md) and
[DUR-01 handback](SEGMENTER-DURATION-POLICY-RESULTS-2026-10-06.md). The cleaner historical EXP-24
reports motivate reuse of its methods, but they do not isolate pretraining's causal contribution.
The current six-positive/one-report-only diagnostic is not a reproduction of that larger-cohort
experiment. Varied development members and verified negatives remain a separate readiness packet.

Governing requirements: REQ-P05/P06, E02/E03/E07/E10 and the approved
[Plan 05 lineage boundary](../imaging/MODEL-LINEAGE-AND-TRAINING.md), especially P05-09.
This drafting review closes no scientific or source-rights gate.

## What the repository establishes

| Property | Current capstone scratch segmenter | Historical SuPreM-compatible definition |
|---|---|---|
| Factory | `segmenter_v5_training_session_v1.scratch` → `segmenter_session_v1.scratch` → `src.models.segresnet.build_model` | Same `build_model` factory |
| Input / destination output channels | 1 / 3 | 1 / 3, replacing a historically described 32-class source head |
| Initial filters | 16 | 16 |
| Down / up blocks | `[1,2,2,4]` / `[1,1,1]` | Same |
| Normalization / dropout | GroupNorm, 8 groups / zero | Same; factory converts zero dropout to `None` |
| Expected replacement keys | `conv_final.2.conv.weight`, `conv_final.2.conv.bias` | Exact pair named by the historical stricter loader |
| Current initialization | Fresh seed42, `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add` | Third-party source still needs new qualification |

Sources: [model factory](../../../src/models/segresnet.py),
[current architecture](../../../src/training/segmenter_session_v1.py),
[v5 identity/import boundary](../../../src/training/segmenter_v5_training_session_v1.py) and
[historical configuration](../../../configs/level45.yaml).
This is a source-code comparison; no model was instantiated and no checkpoint was decoded.
The historical comment about 32 source classes is an expectation for qualification, not a fresh
observation. The installed MONAI tensor signature must be checked by the proposed invented tests.

An early review comment suggested different backbone widths/blocks. Tracing the numerical factory
corrected it: the configurations match. Do not carry forward an architecture-mismatch claim.

## Candidate identity and unresolved provenance

The retained D-326 byte-inventory control
`outputs/prowl/SEGMENTER-CHECKPOINT-INVENTORY-20261002/result.json` has SHA-256
`994e2a13b99e04c8b1f3d8dee176ef04f7146db77fa5fe6254f851aac4b3fe3d`.
It records 203 files; this review read that JSON, not those files. Its recorded SuPreM candidate is:

- URI: `pretrained_weights/supervised_suprem_segresnet_2100.pth`.
- Recorded bytes: **56,500,623**.
- Recorded SHA-256: `2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3`.
- Category: `third_party_weights_not_approved_for_this_run`; `weight_import_allowed=false`.
- Recorded upstream locator: [MrGiovanni/SuPreM](https://github.com/MrGiovanni/SuPreM), as linked
  by the historical repository README. This review did not access or verify the upstream page.

The [accepted D-326 report](SEGMENTER-TRAINING-TRANSACTION-RESULTS-2026-10-02.md) separately records
inventory receipt `edef069e1017ba6a7c5d3ff667844f12684b246712cb0c9ec6a35c87a3e30689`.
The JSON hash above identifies the control read today, not an independent rerun of that receipt.
Current file presence, mount/stat identity and payload equality were not checked.

| Evidence needed before actual-source acceptance | Current state / required resolution |
|---|---|
| Exact upstream revision, artifact URL and citation | Locator/name recorded; recover the release-specific references through a bounded public-metadata review. |
| Code, checkpoint and pretraining-data terms | Not verified here. Record each applicable license/use restriction and its source/version; a repository code license alone is insufficient. |
| Retrieval/derivation history | Tie the local recorded hash to the reviewed upstream artifact. A familiar filename or a hash from an old inventory does not establish licensed origin. |
| Pretraining-data/task relationship | Review datasets/targets and protected PanTS evaluation-task overlap under Plan05. Unavailable membership is uncertainty, not proof of separation; reject an unresolved prohibited source. |
| Actual wrapper, namespace, full tensor names/shapes/dtypes | Not decoded. Head32 and `net`/`module.` conventions are historical expectations, not newly qualified facts. |
| Fresh original file identity | Future exact-path/no-follow/stat/hash scope, after its source review and read budget are agreed. No inventory replay or arbitrary checkpoint search. |

All 88 prior-project and 113 capstone-diagnostic inventory members remain prohibited initialization
sources. The other recorded third-party member, MedFormerPanTS's task checkpoint, is not this
candidate. No old inventory import-denial flag is edited. A later permission applies only to its
new exact task/candidate and cannot reopen a consumed scratch request. Unknown sources fail.

## Why a new auditor is needed

`load_suprem` accepts shape-matching subsets, ignores source-only keys and uses `strict=False`;
the historical training script can silently switch to scratch if the source is absent.
`load_suprem_asserting_head_only` checks the exact replacement pair, but mutates the model before
its assertions and does not fully reject source-only keys. Both use `weights_only=False`.
The legacy inspector also attempts an unrestricted fallback after a restricted decode fails.

The new design validates all controls and tensors **before preparing any replacement state**.
Existing factory, loaders, historical scripts, v5 sessions/executors and checkpoint validators stay
unchanged. Initialization remains distinct from same-run recovery, which restores optimizer/RNG/
progress under its existing full-state identity.

## SUP-01 — proposed four-file implementation

**Objective:** an in-memory CPU audit and full replacement-state builder. It consumes only
test-created tensors in this slice and returns a fresh complete state mapping plus a report.
It does not deserialize a file, mutate a live model, create an optimizer or issue permission.

New-file allowlist:

1. `src/models/segmenter_initialization_audit_v1.py`.
2. `tests/test_segmenter_initialization_audit_v1.py`.
3. `docs/capstone/imaging/SEGMENTER-INITIALIZATION-AUDIT-CONTRACT-V1.md`.
4. `docs/capstone/operations/SEGMENTER-INITIALIZATION-AUDIT-RESULTS-<actual-finish-date>.md`.

Routine queue/notebook/Trello handback pointers may be maintained. Do not edit existing producer
code/tests, source registry, environment locks, global DECISIONS/current-checkpoint, or another lane.
Read/reuse `build_model` in invented tests only; use already installed dependencies. No new script,
file reader, network helper, checkpoint output directory or real consumer is part of SUP-01.

### Interface and controls

Proposed public entry point:

```python
prepare_initialization(
    source_state, fresh_destination_state, *,
    candidate_manifest, expected_candidate_sha256,
    policy, expected_policy_sha256,
    historical_inventory, expected_inventory_sha256,
) -> tuple[dict | None, dict]  # full CPU state (None on refusal), JSON report
```

The implementation contract must define exact JSON fields and reject unknown fields/types.
Canonical manifest/policy/inventory hashes bind the caller's reviewed controls. Candidate metadata
names original-file hash/bytes, classification, source/version/citation/rights/overlap evidence
references, source architecture/class count and source-state content signature/hash. Policy binds
destination architecture, fresh state/hash, seed42, exact head pair, namespace and limits.
Source tensor content is bound independently of names/shapes. Invented controls explicitly declare
`evidence_domain='invented_weights_only'`; real-source evidence is refused in this first slice.
Pins demonstrate identity consistency, not authenticity or truth of rights/overlap assertions.
The returned report carries `execution_authority='none'` and an invented-only qualification scope.

### Required load decisions

- Validate control pins, classification, declared source identity and all tensor bounds first.
  Historical/capstone/unknown candidates, unresolved rights or prohibited-overlap assessments fail.
  In tests these assessment records are explicitly invented, never actual-source acceptance.
- Accept an already extracted state mapping. No `torch.load`, path, byte-buffer deserialization or
  container guessing belongs to this API. A future reader must bind the extracted state to the
  original bytes; the module cannot establish that relationship by itself.
- Permit only the policy's `identity` or uniform one-`module.` namespace transformation. Refuse
  collisions, mixed prefixes, repeated prefixes, non-string keys and ambiguous normalization.
- Check the complete source and destination inventories. Every non-head destination tensor must
  have one same-shape/same-dtype source tensor. Source-only or missing backbone keys fail.
  Reject non-tensors, nonfinite, non-CPU, non-dense/unsupported tensors and implicit dtype conversion.
- The source head must be present and match the declared 32-class source architecture. Expected
  source shapes are `[32,16,1,1,1]` and `[32]`; destination shapes `[3,16,1,1,1]` and `[3]` must be
  confirmed against the installed factory. A different actual source requires revised scope.
- Replace exactly the two task-head tensors with the caller's bound fresh seed42 values. Load all
  compatible non-head tensors, including final-block normalization. Never use a broad
  `conv_final` exclusion. Reject a task-head/class-count substitution rather than silently loading it.
- Prepare detached clones for the entire destination state only after every check passes. Leave
  source/fresh mappings, caller controls and RNG untouched on success and failure. No optimizer,
  scheduler, resume history or old best-checkpoint state enters initialization.
- Report sorted loaded/missing/unexpected/mismatched/replaced keys, source/destination signatures,
  head-before/after and full initialized-state hashes, all input/control pins and pass/fail reason.
  Refusals carry no replacement state. A caller can strict-load the complete mapping into a fresh
  disposable model; this proposed auditor does not publish or attach it to a real training task.
- Proposed input caps: at most1,024 tensors,512 UTF-8 bytes/key,64MiB of actual tensor content per
  mapping and1MiB per JSON control. Check types/shapes and aggregate bytes before cloning/hashing.
  These are offline component limits, not a real checkpoint decoding or experiment budget.
- An absent/unqualified source is an explicit audit failure. Choosing scratch is a separately named
  initialization/configuration decision; do not relabel a failed transfer attempt as a transfer run.

### Meaningful invented checks

Use test-owned CPU tensor values. At least one complete32-output SegResNet fixture and a separate
seed42 three-output destination must use the existing factory without a forward/backward call.
Use distinctive source values so skipping a backbone tensor or importing the source head is caught.

1. Every expected non-head tensor transfers exactly, both task-head tensors stay exactly fresh,
   and the returned full state strict-loads into a disposable matching model. Check final-block
   normalization explicitly and compare tensor content, not only report counts.
2. A missing backbone tensor, unexpected source tensor, wrong shape/dtype, nonfinite value or
   missing/wrong source head fails before any state replacement; original tensors/controls stay exact.
3. Uniform prefix mapping succeeds; prefix collision/mixing/repetition and invalid keys fail.
4. Known prior-project/capstone hashes, another candidate, unknown source, altered pins and
   unavailable rights/overlap evidence fail. Invented success does not accept a real candidate.
5. Content tampering with unchanged names/shapes fails its source-state binding; destination fresh
   head/state drift or wrong class/seed policy fails. CPU RNG before/after remains exact.
6. Repeat preparation produces identical state/report hashes; modifying returned tensors cannot
   mutate inputs. Limits fail without allocating an oversized clone.
7. File-open/`torch.load`/network/forward/optimizer calls are absent; tests fail if such calls occur.
   No existing v5 import gate, initial hash or checkpoint receipt is widened by this new module.

Targeted future check, using the existing native environment:

```text
PYTHONDONTWRITEBYTECODE=1 .venv-prowl/bin/python -m pytest -q tests/test_segmenter_initialization_audit_v1.py -p no:cacheprovider
```

Proposed check budget: CPU only,5minutes and3GiB peak RSS; no accelerator or external artifact
writer. Record actual timing/counts and any failure. Exceeding the resource envelope requires review;
do not add dependencies or silently relax limits. Tests run only after this coding scope is approved.

**Finish:** four allowed files delivered, targeted checks pass, input pins verified unchanged,
and a phone-readable handback identifies real-source and consumer-integration prerequisites.
**Stop:** no automatic actual checkpoint audit, initialization import, longer executor or experiment.

## Later actual-source and integration packets

After SUP-01 and a public source-metadata review, propose one separately bounded actual-file audit:
exact registered path/root identity, candidate hash/size, source/reference pins, byte/RSS/time/read
limits and output/keeper allowance. Inspect serialization before decode, use restricted tensor-only
loading with no unrestricted fallback, and stop on unsupported containers or excess storage.
No numerical budget here grants an actual payload read. Preserve failures and source uncertainty.

If that passes, a new versioned pretrained session/inference/checkpoint integration must bind the
accepted initialized-state hash and source audit, prove cold restore/next-update behavior on
invented data, and retain all role/import/resource gates. The present v5 decoder explicitly requires
the scratch initial hash at step0; a pretrained identity cannot be spliced into it.

Any subsequent experiment compares scratch and permitted pretraining with matched architecture,
cohort, ROI, loss, duration and evaluation roles on one qualified platform. That is an initialization
comparison, distinct from the accepted192-update duration-only question. Actual duration/storage
and device fit remain measured decisions. No EXP/CAP-EXP ID is reserved by this packet.

Keep [varied-data readiness](VARIED-MULTICLASS-GAP-INVENTORY-2026-10-06.md) next in the queue:
retained-metadata candidate/negative-standard selection before new source inspection. Original
memberships, six train/2514 report-only, all12/five holds, localizer153/23, historical failures and
the fixed18,318,645,873-byte whole-backup ceiling remain unchanged.

## Exact next starting point

Review and approve **SUP-01's four-file invented-only implementation** if this is the chosen next
coding packet. Its inputs are created by its tests, so the absent external drive does not block it.
The actual candidate's provenance/rights/overlap/serialization and source-access packet remain open.
The Windows ThinkPad's GPU/VRAM/storage are still unknown;32GiB system RAM alone does not qualify
that platform. No Windows adaptation or daily cross-device resume is dispatched here.
