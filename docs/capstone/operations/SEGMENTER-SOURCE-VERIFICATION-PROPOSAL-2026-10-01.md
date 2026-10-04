# First segmenter source-verification proposal

**Status October 1 — D-316:** M1/M2 completed under fresh requests; both consumed.
[Results](SEGMENTER-SOURCE-VERIFICATION-RESULTS-2026-10-01.md) and
[next M3 content/alignment packet](SEGMENTER-CONTENT-ALIGNMENT-PACKET-2026-10-01.md).
Original prospective wording below is retained; no M3 arrays or real permissions issued.

October 1, 2026 — after D-315. Proposed bounded sequence, not a source request or launch approval.

## Why this is next

The new purpose/cohort contracts pass synthetic checks. Retained metadata proposes 8 train and 4
validation candidates, but none has Stage 2 permission. Need case-specific lesion availability,
geometry, encoding and target meaning, then reviewed use dispositions. Preserve every candidate,
including a held or empty result; no automatic replacement. Old localizer permission cannot be
promoted to dual-target use.

The proposed IDs are train 3/26/6110/2973/2232/6238/5821/4965 and validation 2514/5641/2727/7265.
Machine-readable source identities and expected relative paths are in the sealed D-315 inventory.
Lesion paths are expected siblings named `pancreatic_lesion.nii.gz`; expected does not mean observed.
Old legacy absolute paths must never be resolved or used to redirect source roots.

## M1 — exact metadata/stat verification

First build/test a dedicated source capability and freeze a fresh request: the 12 expected lesion
files plus their 24 CT/pancreas companion references, 36 exact paths total. Verify registered source
root aliases and the approved PROWL volume UUID, canonical existing directories and safe regular
files; no symlink traversal, recursive scans or fallback paths. Sources are read-only. No CT/target
payload, NIfTI header, decoding, GPU, source rewriting, qualification or cohort freeze in M1.

Proposed M1 budget: 90 seconds, 512 MiB RSS, at most 36 file observations and 1 MiB local output.
Check mount identity before/after. Record existence/type, bytes and filesystem observations for
each file, linked to its protected role. Missing or changed companions are explicit holds needing
review; do not drop them or infer corruption. Existing CT/pancreas compressed sizes total
274,941,698 bytes, but M1 does not read those payloads. New lesion sizes are unknown until this job.
No empty-mask/negative conclusion follows from a small compressed file.

Exit: exact path/size ledger and a prepared, measured header/content budget. M1 would be the next
bounded implementation/request to review, not a repeat of D-315's metadata-only JSON/CSV invocation.

## M2 — byte identity and bounded geometry headers

Use M1's exact files/observations to freeze a separate header/identity request. Reverify companion
hashes and read the 12 lesion headers without loading arrays; replay the positively qualified CT/
pancreas geometry evidence only where exact bytes still match. State all compressed hash reads and
header allowances explicitly. Do not count a full-file hash as merely a header read.

Measure source/target dtype, stored scaling, grid, affine and units; compute expanded payload and
per-case memory projections from actual headers. Require matched grids and resolved CT mm units.
Unknown target units can be interpreted only under the exactly matched qualified mm CT grid; do
not infer unknown CT units or rewrite a header. Case 2973's legacy 124-voxel hint is a fidelity
challenge, not a reason to exclude it or assume a correct current mask.

Exit: verified file identities and native geometry, plus a fresh content request with exact
compressed/expanded bytes and per-case/read ceilings. A larger-than-planned input needs a separately
measured exception or revised request; it stays in the ledger throughout.

## M3 — content, alignment and annotation semantics

Perform serial bounded lesion content checks: finite values, strict approved binary decoding,
foreground counts, components/bounds and pairing with qualified pancreas/CT. Define and budget any
new CT/pancreas array reads needed for native alignment views; do not hide them inside a lesion-only
request. Existing 2 mm CT displays may lose tiny detail and are not automatically sufficient for
lesion fidelity review. Preserve original arrays; no rewriting, dilation or automatic cleanup.

Read source-grid views and record technical alignment observations without claiming expert lesion
adjudication. Nonempty supported masks can be assessed as visible positives. Empty masks remain
unknown unless a separate reviewed negative-reference standard establishes the intended annotation
semantics; legacy `has_lesion=False` and voxel count 0 do not do so. The first slice may consequently
be positive-only. Negative-specificity claims remain unavailable in that case.

Exit: content and alignment evidence per candidate, paired lesion-inventory sidecars, qualifications
or holds under the new purpose policy, and a reviewed successor/transition proposal preserving all
historical issues/annotations. Real publication/freezing is a later explicit slice; no blanket
clearance from passing engineering checks.

## M4 — geometry, learning and real smoke readiness

Use the positively qualified subset for the shared pancreas-only ROI/physical-aspect letterbox
implementation and fidelity checks in the [Stage 2 packet](STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md).
Then fresh three-class synthetic learning/checkpoint/recovery, zero-update MPS profiling and one
source/runtime-bound short-run plan. Preserve multi-lesion targets, source restoration, raw masks,
provided-region versus predicted-region identities and explicit failures. No model updates occur
in M1–M3. Long-scale training and formal baseline performance need broader lesion-positive validation
and effective cascade containment; two unverified positive hints cannot establish that baseline.

The [component-coverage proposal](LOCALIZER-COMPONENT-COVERAGE-PROPOSAL-2026-10-01.md) remains a separate
new-reference scope. It may proceed alongside this lane after its own request is prepared and approved.
