# R03 draft — selective source values and fresh task initialization

October6,2026. **Draft complete; no implementation or actual request approved.**
[Readiness queue](SUPREM-TRAINING-READINESS-QUEUE-2026-10-06.md);
[R01 result/actual metadata proposal](SEGMENTER-CHECKPOINT-SOURCE-INSPECTION-RESULTS-2026-10-06.md);
[source-use block](SUPREM-SOURCE-SEPARATION-STATUS-2026-10-06.md).
Tracking: [W01-15](https://trello.com/c/9hAhaaF1).

## Decision and implementation order

R01 observes metadata only. SUP-01 accepts invented in-memory tensors only. Neither can be
relabeled to load the real candidate. Propose two separate four-file slices, followed by a fresh
actual-value/initialization request once R04 passes and source rights/separation are accepted.
No old source/test/contract/import gate or roots registry may change in either slice.

| Slice | Future exact new-file allowlist | Finish |
|---|---|---|
| V01 | src/models/segmenter_source_values_v1.py; tests/test_segmenter_source_values_v1.py; docs/capstone/imaging/SEGMENTER-SOURCE-VALUES-CONTRACT-V1.md; docs/capstone/operations/SEGMENTER-SOURCE-VALUES-RESULTS-2026-10-06.md | Restricted selective descriptor reader, invented-file qualification; no actual use |
| V02 | src/models/segmenter_pretrained_initialization_v1.py; tests/test_segmenter_pretrained_initialization_v1.py; docs/capstone/imaging/SEGMENTER-PRETRAINED-INITIALIZATION-CONTRACT-V1.md; docs/capstone/operations/SEGMENTER-PRETRAINED-INITIALIZATION-RESULTS-2026-10-06.md | Separate strict full-backbone transfer and fresh-head auditor; invented tensors only |

Names are proposed absent destinations, not links to delivered code. Result filenames record their
actual completion date inside the record. Close each contract before implementation. Unit scopes
permit CPU factory/state construction, tensor value checks and strict load, **zero forwards or
optimizer calls**. Targeted tests only:300s/3GiB aggregate sampled pytest/owned-worker envelope,
50ms polling, meaningful new changes/failure checks; no old full-suite replay. Qualify positive
paths on invented sources and actual approval/separation denials without touching the candidate.

## V01 interface and selective materialization

Proposed API: `inspect_values(control, *, control_sha256, metadata_report,
metadata_report_sha256, acceptance, acceptance_sha256, approval, approval_sha256) -> ValuesAudit`.
The public interface requires the trusted consumed-request dispatcher; it grants no execution.
`ValuesAudit` is a typed CPU-only internal result carrying all83 normalized tensors plus a bounded
JSON report. It is not an arbitrary caller mapping or a training permit. Durable outputs contain
hashes/inventory/checks, not source tensor values, unless a later exact snapshot scope permits it.

The closed control binds:

- Fresh domain (`invented_source_values` or `accepted_suprem_source_values`), run/request/code/
  environment pins, explicit approval and consumed receipt, exact source/root identity/APFS UUID,
  R04 pass/result hash, unchanged full83 signature and frozen namespace/wrapper.
- Exact published candidate56,500,623B/SHA
  `2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3` for actual use.
  No search, alternate checkpoint, unsafe fallback or revived R04 consumption.
- Separate source-acceptance record, genuinely reviewed by Quinton, binding artifact-specific
  checkpoint terms, provenance and pretraining **and selection** protected-case separation.
  Historical inventory row remains denied; acceptance is limited to this new task/request.
  It never flips global weight_import_allowed or clears prior-project/capstone denials.
- All limits, exact report members and explicit zero image/reference/cache/prediction permissions.
  Missing acceptance or actual approval rejects before descriptor open/model factory/tensor clone.

Version only applicable R01 descriptor/archive/fake-metadata routines and pin their delivered
source. Do not mutate or monkeypatch R01/A or import a permissive existing loader. Recheck exact
identity and whole-file hash in this **new** request; an older R04 result cannot replace current
identity. Restricted fake decoding observes wrapper/auxiliary storage metadata, not actual values.
Require little-endian stored float32 model records; reject unsupported byte order/packing instead
of broadening the format after actual access.

After complete headers/signature/aliases/view bounds pass, read **only model storage spans** through
the same metered descriptor. Freeze those offsets from the current archive and compare them with
R04; never trust a caller-supplied offset alone. Require each model tensor's storage byte length to
match its dense contiguous logical length and storage offset0. Reject larger/aliased model storage,
including model-to-optimizer aliasing, in this initial narrow reader. Unknown actual packing yields
a refusal and new review, not a fallback. Auxiliary optimizer/scheduler storage contents stay unread
apart from the explicitly authorized whole-file hash; they are never restored or materialized.

Read each unique model span once, make owned CPU float32 tensors, verify all finite, and compute
independent per-tensor/complete normalized-state hashes. Bounds precede allocation. Descriptor/path/
root/volume checks bracket reads; mutation/replacement refuses. No np.fromfile, torch unrestricted
load, mmap, source copy, CUDA/MPS or model execution. Check every83 tensor, including the old32-class
head, for finiteness even though that task head will later be excluded from transfer.

### Exact proposed actual envelope

| Quantity | Proposed maximum / derivation |
|---|---:|
| Identity hash bytes | 56,500,623 |
| Metadata/virtual requested bytes | 8,388,608 |
| Unique model-storage value bytes | 18,805,696 (complete83 dense float32 signature) |
| Total source requested bytes | 83,694,927 (sum above; repeated reads also counted) |
| Live source model tensors | 18,805,696; temporary copies separately metered |
| Source/backbone/fresh-target working allocation | At most128MiB ledger for tensor/buffer copies; process RSS cap additionally applies |
| CPU worker / whole attempt | 120s /180s;3GiB aggregate sampled RSS stop,50ms |
| Persistent numeric/control diagnostics | At most8MiB internal exclusive output area; no raw weights |
| Proposed actual forwards/updates | 0 /0 |

These are **proposed maxima**, not measured actual usage or accepted rights. Actual model storage
packing, current volume identity/free space, source-acceptance/request/output pins are pending.
A narrowed read budget cannot assume actual model spans are18,805,696B before R04. If the qualified
packing differs, stop and review the scope. Consume one fresh request before any source bytes;
retain each refusal within its diagnostic budget. No automatic retry or additional acquisition.

## V02 interface and exact transfer

Proposed API: `initialize_task(values_audit, fresh_task_state, *, candidate, candidate_sha256,
policy, policy_sha256, acceptance, acceptance_sha256) -> InitializationAudit`.
Use a separately closed actual-source boundary; SUP-01 remains unchanged and invented-only.
Require a genuine V01 typed audit, exact source/result/state pins and the same acceptance record;
no arbitrary hash-only attestation or old project checkpoint substitute.

Construct the installed SegResNet1→3/init16/group8/down[1,2,2,4]/up[1,1,1]/dropout0 inside a
seed42 RNG scope and restore the caller RNG afterward. Fresh-state signature/content hash and
head digest must be recorded before transfer. Transfer all81 backbone entries exactly, including
`conv_final.0` normalization; exclude exactly `conv_final.2.conv.weight` and `.bias`. Reject unknown,
missing, repeated/mixed prefix, head/backbone shape/dtype, nonfinite, device/layout, alias or
unqualified-source differences before partial mutation. Use strict full target-state load once.

Source32-output head contains2,176B; source backbone18,803,520B. New3-output head contains204B;
target complete state18,803,724B. Exact named bytes are arithmetic from the reviewed signature,
not measured source values. New head remains bit-exact to fresh seed42 state; source head values
never populate it. No freeze/unfreeze schedule or learning-rate change. Clone ownership prevents
caller/source-state mutation; initialization does not construct a released optimizer or scheduler.

Report exact source/full-backbone/fresh-head/target-state hashes, all mapped81 entries, the two
excluded task-head entries, signature and no execution authority. No top-level “trained” or
“launch ready” claim. Preserve rights/overlap denial explanations separately from format failures.

## Required qualification and next actual scope

Invented tests must independently establish full source/target signatures, selective storage-read
accounting, all-value finiteness (including NaN/Inf source head), per-entry content hashes, complete
strict load, unchanged exact fresh head, source/input ownership and caller RNG. Exercise oversized/
aliased/out-of-bounds/noncontiguous/unsafe-global files, rights/separation/request/source-pin denial,
resource/output caps and child reaping. Prove published optimizer/scheduler values are unused.
No guards are disabled to make actual controls pass tests.

Actual R05 request is built only after V01/V02 qualification, R04 metadata pass and source acceptance.
Its source/limits/output/control/approval/consumption command is frozen then; request hash, actual
state hash and head/target digest are **null/pending** now. Audit any actual mismatch before moving
to a session. No scientific run is bundled into R05. Historical requests, failures, cohorts, holds
and fixed backup ceiling remain unchanged.
