# SuPreM checkpoint inspection — bounded proposal

**Prepared:** October 6, 2026. **Owner:** this imaging chat / Quinton.
**Authority:** public review and this draft approved after SUP-01. SUP-02A implementation and
SUP-02B actual-file inspection below are proposed, not dispatched. No training request is created.
Read the [public-source review](SUPREM-PUBLIC-PROVENANCE-REVIEW-2026-10-06.md) first.

**October 6 SUP-02A approval and pre-code qualification:** after the Trello cleanup Quinton
selected “Lets move onto the next,” resuming this recommended four-file invented coding packet.
B remains proposed. The [closed A contract](../imaging/SEGMENTER-CHECKPOINT-INSPECTION-CONTRACT-V1.md)
records the initial direct-file API refusal and the revised metadata-only descriptor view before
implementation. PyTorch2.13.0's4KiB tail read overlapped an invented storage; the view will supply
reported virtual zeros there while reading only metadata. The identity hash pass still reads the
whole invented file. All requested/virtual bytes count toward the existing budget; no unsafe
fallback, real access or additional source scope is added.

**SUP-02A handback:** [94 native invented checks pass](SEGMENTER-CHECKPOINT-INSPECTION-RESULTS-2026-10-06.md).
The four-file reader is delivered; existing pins remain unchanged. Reports retain no execution
authority or training eligibility. SUP-02B is still a proposal: its separate actual entry, exact
root/control/request and tuple/container policy need review. Do not replay A or start B automatically.

**Later October6 continual-preparation request:** the [finite readiness queue](SUPREM-TRAINING-READINESS-QUEUE-2026-10-06.md)
now scopes the separate R01/SUP-02B-PREP boundary and auxiliary-tuple qualification with invented
CPU files. A remains fixed. This authorizes routine preparation, not the actual B attempt below;
R04 needs its exact qualified request/root/output scope and Quinton's separate approval.

**R01 delivered:** [89 native invented checks](SEGMENTER-CHECKPOINT-SOURCE-INSPECTION-RESULTS-2026-10-06.md)
qualify a separate source/approval boundary and auxiliary tuples. Its concrete actual access and
request-dispatcher scope remain proposals. A stays fixed; no actual source has been opened.

**Latest R04 handback:** Quinton approved the dispatcher and one metadata scope.73native invented
dispatch checks pass; sole native preflight refused volume_observer_unavailable before checkpoint
bytes or request creation. Actual metadata remains unverified. B01 retired operationally; no retry.
Read the [result and proposed diagnostic follow-up](SUPREM-CHECKPOINT-METADATA-DISPATCH-RESULTS-2026-10-06.md).
Earlier proposal wording below is retained history; no source reader/value/training follow-on.

## Objective and separation of phases

Determine whether the recorded released artifact can be inspected safely and whether its complete
model inventory matches the expected SegResNet. A successful metadata inspection does not prove
finite tensor values, initialize a model, settle data overlap or qualify a training session.

1. **SUP-02A: implement and qualify an invented-file metadata reader.** No actual weight access.
2. **SUP-02B: one fresh exact local identity/container/metadata inspection.** Proposed only; freeze
   its scope after A's handback. It can report compatibility while scientific-source acceptance
   remains unresolved. No materialized real tensor content or model loading in this phase.
3. **Later, separately scoped:** actual-value audit and source acceptance, then a versioned
   pretrained initialization/session/checkpoint/cold-recovery integration. No automatic advance.

## SUP-02A — concrete four-file coding slice

New-file allowlist:

1. `src/models/segmenter_checkpoint_inspection_v1.py`
2. `tests/test_segmenter_checkpoint_inspection_v1.py`
3. `docs/capstone/imaging/SEGMENTER-CHECKPOINT-INSPECTION-CONTRACT-V1.md`
4. `docs/capstone/operations/SEGMENTER-CHECKPOINT-INSPECTION-RESULTS-<actual-finish-date>.md`

Maintain this packet, queue, AGENTS and this chat's Trello handback pointers as needed. Existing
source/tests, SUP-01, historical loaders, v5 consumers and environment locks stay untouched.
Use installed dependencies. Test files contain invented tensors/containers only and use temporary
test-owned paths. A fresh factory-created 32-output model may provide the complete invented
signature/fixture; no forward/backward or optimizer restoration occurs. The reader itself does
not instantiate a model.
The public-source documentation is design context; no upstream code is vendored.

### Proposed interface and evidence boundary

`inspect_checkpoint(path, *, pinned_control, expected_control_sha256) -> dict`.
The exact contract must close control/report schemas before coding. The control binds domain,
single source path, source hash/size, permitted root, expected full model signature, namespace,
wrapper and budgets. A accepts only `invented_serialized_checkpoint`, with test-owned paths;
it refuses actual candidate paths/domains. Reports carry `execution_authority='none'`, metadata
scope and `training_eligible=false`. A's invention guard must not be disabled to run B.

B will need a separately reviewed real-read entry boundary, fresh exact controls and its own
qualification/pins; define that bounded addition after A, rather than put a dormant actual-file
switch into this first slice. A's pure format/metadata helpers may be reusable unchanged.

### Identity, format and read behavior

- Check the explicit source root/path and ancestors; refuse symlink aliases, directories/devices,
  path traversal, unknown roots and any extra input. Bind a regular-file descriptor; compare
  descriptor/path identity and size before and after reads. Refuse replacements or mutation.
- Stream a single exact file SHA-256 before trusting metadata. Refuse size/hash mismatch without
  attempting PyTorch decoding. Descriptor-bound reads use an aggregate byte counter, including
  repeated reads/seeks; no independent unmetered reader or mmap path may bypass it.
- Support only the qualified ZIP-based PyTorch format. Refuse legacy pickle-only formats rather
  than fall back. Bound the archive index before general ZIP parsing; reject duplicate names,
  encrypted/compressed members, unsafe names/paths, oversized metadata, excessive member counts,
  offsets outside the file and declared storage excess. Never extract members to disk.
- Qualify `FakeTensorMode` plus explicit `torch.load(..., weights_only=True, map_location='cpu')`
  using the bounded descriptor wrapper. Prove that model storage payloads are not read or
  materialized. If the installed APIs cannot satisfy that property, refuse; document a revised
  approach before another implementation/actual attempt. The public
  [PyTorch documentation](https://docs.pytorch.org/docs/main/notes/serialization.html) is guidance,
  not proof that our wrapper or environment enforces these boundaries.
- No unrestricted unpickling, `weights_only=False`, arbitrary `pickle.load`, dynamic imports,
  user-added safe globals, tensor subclasses, CUDA/MPS, network or legacy-loader invocation.
  A clean child worker is preferable so ambient allowlisted globals cannot affect interpretation.

### Container and model inventory

The [public pretraining writer](https://raw.githubusercontent.com/MrGiovanni/SuPreM/main/supervised_pretraining/train.py)
suggests `net`, `optimizer`, `scheduler`, `epoch`. Proposed supported wrapper is exactly that
four-key dictionary, with plain bounded primitives/dictionaries/lists and supported fake tensor
metadata; `net` must be the model mapping. Auxiliary fields are inventoried, never loaded into
an optimizer/scheduler/session. Refuse an unrecognized wrapper, raw-state alternative or extra
field; a different actual wrapper requires a revised scope, not container guessing.

Require complete reviewed source signature: one input, 32 outputs, init_filters16,
GroupNorm8, down[1,2,2,4], up[1,1,1], dropout0. Permit exactly identity or uniform one-`module.`
prefix stripping, frozen by control; refuse mixed/repeated prefixes and collisions.
Compare every source model key/shape/dtype with the full reviewed signature, not only a key count.
Require source final-convolution shapes `[32,16,1,1,1]` and `[32]`. Report strides, offsets,
storage sizes/locations and aliasing. Reject out-of-storage or oversized logical views and
unsupported layout/device/dtype/subclasses. Auxiliary storages count toward file-wide limits.

Inspection does not replace the head or return a loadable initialized state. Metadata can report
compatibility but cannot assert finite values or hash tensor contents. Preserve SUP-01's
invented-only controls and the exact fresh three-class head policy for later separately scoped work.

### Proposed bounds and invented checks

| Resource / structure | Proposed A bound |
|---|---|
| Each invented file | At most 64 MiB |
| Read budget per inspection | One file-length hash pass + at most 8 MiB metadata reads |
| ZIP central directory / `data.pkl` | At most 1 MiB each |
| ZIP members / file-wide distinct storages | At most 4,096 each |
| File-wide declared storage bytes | At most 128 MiB |
| Model tensors / total logical model bytes | At most 1,024 / 64 MiB |
| Key/path length | At most 512 UTF-8 bytes |
| Container nesting / visited items | At most 16 / 32,768 |
| Control / JSON report | At most 1 MiB each; no tensor values |
| Whole targeted qualification | 5 minutes, CPU only, 3 GiB peak RSS |

Time/memory monitoring must be qualified in the installed Mac environment. A sampled RSS stop is
not an OS hard limit; record sampling interval, termination behavior and measured peak. Refuse a
resource-qualified actual request if monitoring cannot run. Keep reports of any failed approaches.

Meaningful checks include a known complete invented source inventory/container, independent
archive offsets/storage accounting, exact hash binding, no storage-payload reads, deterministic
reports and unchanged file/inputs. Exercise missing/extra/mismatched keys/head, wrapper ambiguity,
nonfinite primitive metadata, dtype/layout/view/alias policy, legacy/unrestricted-load refusal,
unsafe globals, malformed/oversized ZIP index and members, compressed/encrypted/duplicate entries,
path/symlink/mutation cases, every size/count/read/output cap and worker time/memory stop.
Use guarded side-effect payloads that must never execute. No real file, benchmark images or prior
successful test suites are needed. Reject before resource-heavy operations whenever possible.

Deliver exact new test counts, source/control pins, API/resource evidence, failures and remaining
limitations. Stop after A. Do not invent a full-suite, actual-compatibility or source-permission claim.

## SUP-02B — proposed actual request, not launch-ready

Single candidate locator relative to the authoritative repository:
`pretrained_weights/supervised_suprem_segresnet_2100.pth`.
Current presence, symlink/volume relationship and bytes have **not** been checked. Do not search
other directories or substitute a second copy if it is absent. Resolve the actual registered root
under a new metadata preflight and explicit scope before an actual read.

| Frozen expected field | Value |
|---|---|
| Bytes | 56,500,623, from D-326 |
| SHA-256 | `2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3` |
| Published metadata | [Exact release file](https://huggingface.co/MrGiovanni/SuPreM/blob/main/supervised_suprem_segresnet_2100.pth) |
| Existing inventory SHA | `994e2a13b99e04c8b1f3d8dee176ef04f7146db77fa5fe6254f851aac4b3fe3d` |
| Source payloads | One checkpoint; zero CT/reference/cache/prediction arrays |
| Proposed aggregate checkpoint read cap | 64,889,231 bytes = 56,500,623 + 8,388,608 |
| Proposed worker envelope | 60 seconds, CPU only, 3 GiB sampled RSS stop |
| Proposed retained outputs | Control, receipt, metadata report and run log; aggregate 4 MiB maximum |

Before dispatch, A must pass and the separate actual-read boundary must be implemented/qualified
under its own bounded approval. Freeze its code/environment/control pins, full expected signature,
actual wrapper/namespace policy, worker command, source root/descriptor policy, output paths,
resource monitor and exact acceptance/stop rules. Bind publisher weight terms and explicitly
record that overlap is unresolved if still open. There is no permission file or consumed request
for B now; do not manufacture one by treating this Markdown as launch authorization.

Proposed output location is a fresh `outputs/prowl/SUPREM-CHECKPOINT-INSPECTION-<run_id>/` diagnostic
control area, only after exact path/capability approval and existing occupancy/free-space review.
It would retain numeric/control metadata only, with no weight copy or serialized output. No directory
is created now. This proposal does not grant a registered writer or an independent-keeper claim.
Do not write to the missing external volume, raise the fixed backup ceiling or substitute storage.
Absent source/root, identity mismatch, format/namespace/signature mismatch, unsupported global,
budget excess or unqualified monitoring terminates the attempt and retains bounded evidence.
No automatic retry, broader read, download, environment change or unsafe fallback.

The report separates `identity_verified`, `metadata_compatible`, `values_audited=false`,
`rights_review_status`, `overlap_review_status` and `training_eligible=false`.
Even a complete metadata match grants no access to initialization, forward/update or old optimizer
state. Actual finite/content/full-load audit needs a new real-source contract; current SUP-01
explicitly refuses that evidence domain.

## Scientific use and exact next choice

Candidate-specific training and upstream model-selection separation must be resolved before real
initialization/training. Keep scratch as the control; changing initialization requires its own
matched comparison and preregistration. Varied development/negative qualification remains needed
for useful quality/generalization conclusions, independent of this checkpoint's compatibility.

**Recommended next approval:** SUP-02A's four-file invented metadata reader only. It is useful while
the drive is absent and does not wait on training access. After its handback, decide on the separate
real-read boundary and exact B request using observed qualification and source evidence.
No existing scientific, storage, source, retrieval or Git authorization is broadened by this draft.
