# Small Stage 2 qualification and cascade slice

**October 1 update — D-317:** [four-case content/alignment pilot complete](SEGMENTER-CONTENT-PILOT-RESULTS-2026-10-01.md).
All4 native targets technically supported and reviewed; real Stage2 permissions/cohort remain zero.
2973 is a124-voxel single-slice fidelity challenge;5641 has disjoint masks but full pancreas-only-box
containment. Preserve both observations. Next [remaining-eight continuation](SEGMENTER-CONTENT-CONTINUATION-PACKET-2026-10-01.md)
before purpose dispositions and shared geometry. Source pilot scope consumed; no model updates.


**October 1 update — D-316:** [M1/M2 source checks complete](SEGMENTER-SOURCE-VERIFICATION-RESULTS-2026-10-01.md).
All 36 files and 12 lesion grids verified; no arrays, lesion-purpose permissions or cohort yet.
Five scaled int8 targets need strict semantic decoding; six unknown target-unit headers have the
exact matched qualified mm CT context. No unresolved CT units are inferred. Next:
[bounded content/alignment pilot packet](SEGMENTER-CONTENT-ALIGNMENT-PACKET-2026-10-01.md), starting
with synthetic resource/fault qualification before any fresh source-array request.


**October 1 update — D-315:** Phase A's synthetic purpose/cohort contracts and retained-metadata
candidate proposal are complete. [Implementation and results](STAGE2-METADATA-RESULTS-2026-10-01.md).
No real lesion-purpose qualifications, source reads or training cohort yet. Next bounded proposal:
[source metadata/stat, headers and content](SEGMENTER-SOURCE-VERIFICATION-PROPOSAL-2026-10-01.md).
The original phase definitions below remain the planning baseline; earlier pending wording is historical.

October 1, 2026 — prepared under D-314. Planning packet; no lesion-purpose qualification,
source-array job, model download or training request is issued by this document.

## Goal and place in the capstone

Make a small, reproducible three-class segmenter experiment possible while the localizer's
precision/coverage problem remains visible. We already have protected ancestry, purpose-specific
pancreas qualifications, role-safe 113/40 consumers, spatial records, bounded transactions and
independent checkpoint recovery. These are reusable engineering foundations, not lesion permissions
or a completed autonomous baseline. CAP-EXP-012 is not an accepted localizer.

The useful next milestone is a qualified lesion-target slice plus tested shared ROI geometry. Then
a small provided-pancreas-region diagnostic can establish whether the segmenter can learn and restore
lesion contours. A separate predicted-region diagnostic using the same segmenter exposes localization
loss. Neither substitutes for the eventual G4 autonomous/reference baseline or untouched evaluation.

Authority: Plan 05 P05-04 through P05-11, Plan 06 P06-08/P06-10, D-048–D-050/D-065/D-067,
[ROI contract](../imaging/LOCALIZATION-AND-ROI.md), [spatial contract](../imaging/SPATIAL-TRANSFORMS.md),
[model lineage](../imaging/MODEL-LINEAGE-AND-TRAINING.md). This packet narrows implementation;
it does not override those decisions. It is independent of Claude's literature implementation.

## Qualification checklist

Original membership stays permanent. Permission is purpose-specific. A localizer qualification
cannot authorize a lesion training target or reference. Difficult, noisy, thin/thick, partial-field
and tiny-target cases remain candidates; these are observations, not quality-filter exclusions.

|Requirement|Evidence already available|Evidence still needed|Exact pass/fail rule|
|---|---|---|---|
|Protected source and role|Pinned publisher release, original split lineage; 113 train/40 development members under D-294|Bind candidate CT, pancreas and lesion records to that ancestry|Train may consume train-role only; evaluation validation-role only; disjoint IDs and original membership replay exactly. Unresolved ancestry holds the affected use.|
|Purpose permission|Local research/source review and localizer records; release-license discrepancy remains documented|New versioned Stage 2 training/reference dispositions with source-use basis|Every consumed CT and target has positive permission for its exact purpose. Empty/missing permission rejects; no inference from localizer approval. Release clearance remains separate.|
|Physical CT geometry|All 153 localizer grids qualified; 23 older holds preserved|Reuse byte-bound CT evidence and pair new lesion geometry|CT/pancreas/lesion shape and affine agree within explicitly versioned NIfTI storage tolerance; spatial units positively resolved in mm; unknown units stay held.|
|Exact bytes and identity|Pancreas/CT hashes and retained file receipts|Read-only lesion inventory/header/content receipts and checksums|Actual retained file hash/bytes match record; source bytes immutable. Stale or changed evidence rejects.|
|Binary decoding lineage|D-259 strict semantic zero/one tolerance policy|Link each lesion's scaled values, audit, policy/version and approval|Only supported finite binary endpoints normalize under the approved tolerance. Scaled binary is not rejected merely for storage encoding; multi-valued/ambiguous masks need separate mapping. Never generic `>0`.|
|Lesion target meaning|PanTS source claims and prior narrow lesion-mask investigations|Case-specific annotation identity, structure, availability/completeness/status evidence|Nonempty valid mask supports a visible lesion-positive reference. Missing/empty mask alone never certifies a negative patient. State unsupported/unknown explicitly and deny negative-target use.|
|Verified lesion-negative training/reference|No general negative qualification established|Positive evidence supporting negative annotation semantics for the selected use|Negative supervision/specificity needs explicit verification, not filename presence or zero voxels. If none qualifies, use a labeled positive-only diagnostic and do not report specificity.|
|Pancreas/lesion relationship|Approved lesion-over-pancreas class precedence|Overlap/outside-pancreas counts and paired source views|Assemble class 0 background, 1 pancreas excluding lesion, 2 lesion; preserve all lesion components. Lesion outside pancreas is an observation to investigate, not automatic deletion or ROI enlargement.|
|Reference-derived ROI|D-048 pancreas-only region and physical margin|Versioned shared box/normalization implementation and exact transform evidence|Only pancreas target determines training/provided-region ROI. Lesion extent must not influence box selection, jitter acceptance or repair. Record excluded lesion voxels after ROI is fixed.|
|Target fidelity and effective resolution|2 mm localizer fidelity evidence; does not qualify Stage 2 resolution|Native→ROI→tensor→native lesion/pancreas counts, component retention, landmarks and effective spacing|Record tiny/boundary loss per case. A lost positive is never silently treated as a qualified negative. Geometry must match independent landmarks; resolution problems remain visible and require a measured recipe/budget decision. No Dice-based removal of difficult cases.|
|Issue preservation and cohort freeze|Localizer permanent membership/held ledger|New purpose records and immutable Stage 2 cohort/resolver|Every candidate gets a disposition; only positively qualified cases enter the frozen consumed subset. Retain holds and reasons; changes create a new cohort, never overwrite/relabel original members.|
|Operational readiness|MPS profiles and keeper/recovery mechanics from localizer|Separate segmenter tensor/model/loss/request budget and independent recovery tests|No launch until synthetic learning, exact identity, save/reload/interruption, resource ceilings and independent restoration pass for this new consumer. Localizer limits are evidence, not inherited Stage 2 limits.|

## Phase A — metadata and bounded target evidence

First implementation packet: add separate Stage 2 purpose records and synthetic resolver guards,
leaving existing localizer consumers unchanged. Read retained metadata for the 153 qualified members;
do not reopen raw arrays in this phase. Inventory candidate lesion references and link existing
provenance/annotation evidence. Include the 23 localizer holds in accounting, without changing them.

Proposed first diagnostic size: at most 8 train and 4 development-validation candidates, selected
from permanent roles with visible diversity in protocol, physical spacing, field coverage and known
difficulty. This size is an engineering proposal, not a freeze or a claim of representative testing.
Create the exact candidate list and rationale before new header/content reads. Keep every selected
candidate's result; any replacement requires a new recorded selection, not a hidden refill.

Then freeze an exact read-only header/content request for CT/pancreas/lesion inputs still lacking
evidence. Reuse already qualified evidence where its bytes and scope suffice. Pin filenames, roles,
compressed/expanded sizes, audit checks, CPU/read/output/time budget and stop behavior. Inspect each
consumed candidate's content/geometry views and issue a Stage 2 disposition. Do not predict runtime
from the localizer cache alone or launch an unbounded scan. A single positive can support a mechanical
learning check; a train/validation comparison needs disjoint qualified positives in both roles.

Exit: machine-readable candidate ledger, new purpose qualifications and frozen consumed subset with
independent replay. A positive-only subset must say so; it cannot support negative-case performance.

## Phase B — shared region geometry and source restoration

Build a new explicit consumer, not the legacy permissive label transform. The three-class target is
assembled on the qualified source grid, preserving lesion-over-pancreas precedence. Pancreas alone
sets the reference training box. The initial geometry diagnostic may use zero jitter under a named
diagnostic recipe; the formal baseline still needs bounded, versioned development-derived jitter.

Use one shared physical-margin and aspect-preserving scale-to-fit/symmetric-pad path for training,
provided-region inference and autonomous predicted regions. Do not independently stretch axes,
center-truncate overflow, or choose a box from pancreas-plus-lesion extent. Record requested/realized
margin, source/canonical/ROI/tensor grids, uniform scale, rounding, padding and effective spacing.
Define the ROI sampling grid in physical space before uniform letterboxing; preserving raw voxel
axis counts on an anisotropic grid is not proof of preserving physical aspect ratio. Pin any initial
isotropic resampling and its realized extent/spacing in the shared forward and inverse records.
Outside the chosen ROI, restored probabilities are background 1, other classes 0. Restore continuous
probabilities first, then discretize on the exact source shape/affine; labels use nearest interpolation.

Synthetic acceptance covers reversed/permuted axes, nonzero origin, anisotropic spacing, odd padding,
boundary contacts, long thin ROI, multiple lesions, lesion outside pancreas, empty lesion with verified
status, and empty/unsafe localization. Independent coordinate/landmark oracles must catch axis swaps
and crop offsets. Compare image-only inference and training preprocessing. Native round-trip views
and counts establish what small targets survive, without selecting easier cases. Candidate tensor
shape is profiled rather than automatically copying localizer 144³; measure effective spacing and
target loss before the freeze. Record all failures in the requested denominator.

Exit: shared geometry path with independent tests and a verified real zero-update geometry receipt.

## Phase C — fresh segmenter and synthetic learning transaction

Separate three-class SegResNet-family model/checkpoint identity, optimizer/loss/seed/configuration
and sampler state. Use a fresh capstone scratch initialization for the first mechanical diagnostic
unless third-party pretraining is separately pinned and audited. SuPreM remains a candidate requiring
source/license/checksum/architecture/load and protected-data overlap verification; do not load prior-
project weights or treat localizer weights as a segmenter checkpoint.

Propose a simple frozen loss only after class sizes and empty/positive behavior are known; do not
copy the experimental localizer class-mean formula without examining three-class gradients. Synthetic
checks should establish independent class mapping, gradients, sparse/multiple-lesion learning and
absence of class collapse. Record pancreas-parenchyma and pancreas-or-lesion union separately.
Test checkpoint source/config/lineage binding, exact probe replay, optimizer/sampler resume,
interrupted-update refusal and independent keeper recovery with primary access blocked.

Exit: synthetic CPU checks and native MPS rehearsal, versioned run records and independent recovery.

## Phase D — real zero-update profile and exact smoke plan

Bring only the new positively qualified, frozen members through the versioned loader. Verify model
input/targets, full selected ROI coverage, native exports and references, measured CPU/MPS memory,
time per update/inference/evaluation, tensor payload and independent recovery. No updates in this
qualification job. Its request has a fresh stage-specific reference/read budget.

Use measured values to freeze one short run: initialization, exact members/roles, sampler, loss,
learning-rate schedule, number of updates, evaluations, time/RSS/driver/disk ceilings, early-stop
conditions and checkpoint selection. Synthetic learning criteria validate mechanics; real endpoint
criteria are prospective and must not be retrofitted to observed results. A smoke is not long-scale
training or a clinically usable model. Issue the concrete request for the next launch decision.

Exit: source/runtime-bound launch packet. No Stage 2 launch is authorized by D-314.

## Phase E — same-segmenter reference and autonomous diagnostics

First evaluate the selected experimental segmenter with pancreas-only provided regions. Separately
use a pinned localizer/ROI policy to make predicted regions on the exact same validation members.
If using 010/012 for exploration, identify them as unaccepted experimental localizers; do not relabel
them as G4 baseline models. Keep segmenter weights and inference settings the same between modes.

Measure box containment and **effective containment after actual normalization**, lesion-positive
Dice, pancreas class-1 Dice, pancreas-union Dice, empty-reference behavior, patient detection and
verified-negative specificity where supported. Preserve all source-grid lesion components and use
the preregistered deterministic one-to-one tumor matching; no largest-lesion-only pruning. Keep raw
masks/probabilities immutable; derived variants get separate identities. Failed localization produces
an explicit failure, never a ground-truth repair or silent whole-volume fallback.

Small validation is reused development evidence. Publish per-member/component outcomes and full
denominators, not generalization or clinical claims. Formal G4 later requires frozen policy/model
selection, the registered wider baseline cohort and complete evaluation/identity contracts.

## Decisions to settle after Phase A evidence

1. Exact 8/4-or-smaller candidate proposal and whether qualified negatives exist; no invented
   negative status. Preserve variation and holds rather than filtering for easy lesions.
2. Initial tensor size/physical margin based on target fidelity and measured cost. Ten millimeters
   is a diagnostic starting proposal from localizer evidence, not a newly selected cascade policy.
3. Scratch diagnostic architecture/loss and bounded update count after the synthetic/profile work.
4. Diagnostic zero-jitter versus separately frozen baseline jitter derived from localization errors.
5. Which experimental localizer/ROI to pin for the matched predicted-region diagnostic. Any component
   cleanup needs its own fresh reference coverage evidence before selection.

## Recommended order before October 5

Finish the timeboxed component audit now; begin Phase A's synthetic records/metadata proposal next.
Aim for the first qualified lesion slice and shared synthetic geometry before course start. Real
geometry/MPS readiness and a small segmenter smoke follow when their gates pass. A failed gate changes
the evidence-backed next task, not cohort membership or the acceptance rule. Long-scale training
waits for useful localization/Stage 2 resolution and the bounded cascade baseline; the current
localizer's high recall alone is insufficient.

Other pre-course work remains on the board: preserve a reviewed Git checkpoint, publisher email
draft (Quinton will send later), stakeholder preparation when requested/confirmed, literature review
handoffs and overall G0/Plan 10 readiness. None requires making the literature system a prerequisite
to this small imaging slice. This packet does not implement the still-gated full Plan 04 orchestration
or publish Git changes automatically.

## First bounded implementation packet to review next

Proposed scope is Phase A's synthetic contracts and retained-metadata inventory only. Owned new
files: `src/data/segmenter_qualification_v1.py`, `src/data/segmenter_cohort_v1.py`,
`scripts/diagnostics/segmenter_candidate_inventory.py` and their tests. Add a separate versioned
record/schema only if the existing generic manifest contract can represent its source evidence
without weakening old validation. Do not edit `purpose_qualification_v2.py` to silently widen its
pancreas-only purposes or migrate existing consumers. Proposed purpose names are
`pancreas_lesion_segmenter_training` and `pancreas_lesion_segmenter_validation`; freeze them with
the schema review, rather than asserting they already exist.

Qualification records bind snapshot/split/study, all three input identities, two annotation
identities, mapping approval, target status, source-use basis, evidence hashes, issues, purpose and
protected role. A cohort records ordered members and qualification pins; a resolver rechecks
positive permissions and content/evidence identities before producing descriptors. Immutable old
members/holds remain available in the ledger. A synthetic fixture never becomes a real qualification.

Acceptance: refuse train/validation overlap, wrong-role use, unknown/empty permission, changed mask
or evidence hash, unresolved units/mapping, missing lesion annotation and unsupported negative status.
Preserve legitimate nonempty lesion positives, verified negative fixtures, multiple components,
outside-pancreas observations and difficulty warnings with their exact target semantics. Excluded
or held candidates remain counted. Resolver replay is exact and prior localizer behavior unchanged.

Metadata inventory reads only already retained manifest/cohort/evidence JSON. It emits a full
candidate/hold accounting table and a proposed 8/4 list, exact missing evidence and proposed header/
content-read budget. It must not open any NIfTI array, create real positive qualifications, rewrite
source masks, freeze a training cohort, run the GPU or download pretraining. Those are later bounded
phases with their own completed readiness evidence. This is the concrete next implementation
proposal after reviewing the structure audit; D-314 itself authorized this packet's preparation.
