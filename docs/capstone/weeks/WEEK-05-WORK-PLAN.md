# Week 5 work plan — November 2–8, 2026

Make the autonomous imaging path demonstrable while the matched KD treatment runs.
Preserve the working literature prototype and fast assistant; focus remaining work
on integration and measurable answer quality. This plan does not change the approved
proposal, frozen training recipe, evaluation roles or acceptance criteria.

## Proposal commitments and current position

Approved proposal v3.8, section6, Week5: **Autonomous baseline and retrieval
foundation**. Deliverable: “Held-out baseline, error analysis, and a versioned,
queryable retrieval prototype.” Its failure condition is that the baseline cannot
run end to end or the retrieval prototype is not queryable. Proposal and appendix
v3.1 hashes were checked November2 against references/governance/APPROVED-SOURCES.md
and match. Older July-course Week5 documents are not this schedule.

| Commitment | Position on November 2 | Week 5 finish line |
| --- | --- | --- |
| Autonomous imaging baseline and error analysis | Open. Completed control and running KD use provided pancreas regions; neither demonstrates autonomous localization. | Qualified full-volume CT → predicted ROI → segmentation → native export, frozen eligible evaluation roles, metrics/failure denominators and error analysis. No reference crop in the autonomous arm. |
| Versioned queryable retrieval prototype | Delivered early; W05-02 closed by evidence reconciliation today. | Reuse14 authorized sources/1,179 passages, pinned corpus/index/encoder/source identities, exact rebuild, live queries and internal database restart parity. No new corpus build needed. |
| Week4 restartable workflow integration | Carryover W04-01; CPU adapters and actual training recovery evidence exist, full G3 still open. | Reconcile evidence and connect the specific missing production stages needed for the baseline, with reuse and failure recovery demonstrated. |
| Controlled model comparison | KD is later authorized exploratory work; formal comparison is Week6. Control24k complete; treatment launched November2. | Preserve matched run and evaluate completed outputs when available. KD success is not promised and cannot substitute for autonomous G4. |
| Stakeholder preparation | Master plan/Plan11 call for participant or fallback confirmation by Week5, main walkthrough Week7. | Quinton confirms participant/role/date or suitable fallback. Scheduling is not completed validation. |

Evidence: [prototype](../retrieval/LIVE-DEVELOPMENT-SEARCH-2026-10-17.md),
[corpus](../retrieval/DISEASE-REFERENCE-CORPUS-2026-10-17.md),
[internal search](../retrieval/INTERNAL-LITERATURE-SERVICE-2026-10-28.md),
[training and recovery](../operations/MAC-KD-LAUNCH-HANDOFF-20261027.md),
[G3 gaps](../orchestration/G3-EVIDENCE-REVIEW-20261027.md),
[master plan](../MASTER-PLAN.md).

## Work order and observable completion

1. **Autonomous baseline preparation — W05-01 with W04-01.** Inventory existing
   localizer, predicted-ROI adapter, native reconstruction and failure reporting.
   Identify the exact missing connection before writing code. Evaluate whether the
   completed control's preselected20k checkpoint is an eligible fixed candidate;
   do not wait for or select on future KD/held-out results. Check model provenance,
   cohort roles and exposure before freezing the evaluation packet. Use synthetic
   or already-permitted development evidence for CPU geometry, source identity,
   invalid-input, reuse and recovery tests. Finish preparation with an executable
   bounded command and explicit remaining GPU/data gates, not another framework.
2. **Complete the baseline in a free GPU window.** Once qualified and scheduled,
   execute the frozen autonomous path and separately labeled provided-region
   comparison. Report pancreas/lesion overlap, missed lesions, false positives,
   scan coverage, failure denominators and important error groups. Preserve all
   failures. A supplied-region result or exposed regression set cannot be renamed
   independent acceptance. No protected data is opened merely for this plan.
3. **Keep KD progressing — KD-MAC.** The matched control completed24k; selected20k
   lesion-positive macro Dice0.383592868, terminal24k0.381964037. Treatment is
   launchd-owned, with actual updates, teacher access, MLflow and initial independent
   backup verified. Keep one GPU owner and frozen pins. At completion, verify final
   validation/backup/cleanup, compare selected and terminal endpoints on the same
   cohort, and assess missed lesions, false alarms, contour/coverage errors and
   measurement limitations separately. Teacher membership remains unknown, so this
   is teacher-assisted exploratory evidence. No result-dependent new experiment.
4. **Verify answer quality and the reviewer flow — W04-04 / AI-04.** Preserve the
   user-accepted fast preview and conversation UI. Review existing public answers
   against their sources while training runs; fix a demonstrated failure only.
   Prepare one compact table for support, completeness, citations, refusals and
   cold/warm latency. In an available GPU slot, exercise Research and Workbench,
   cancellation/edit/resend and case → contours → qualified measurement or explicit
   limitation → cited answer → save/reopen/revise. The reported2–4second responsiveness
   is useful UX evidence, not independent accuracy. Fresh W06-02 evaluation remains
   separate; no new labeling application or wholesale UI redesign.
5. **Stakeholder and closeout — W05-03/04.** Quinton confirms the participant or
   fallback and personal work hours. Prepare the existing walkthrough script and
   weekly evidence summary. No outreach messages or course submissions are inferred.

## Timing and capacity

Monday/Tuesday: baseline adapter/gate audit and smallest demonstrated CPU integration
fix. Wednesday: review readiness and remaining KD runtime; identify an actual GPU
slot for the baseline and assistant checks. Thursday/Friday: run the qualified
baseline if resources permit, otherwise report the precise schedule risk and agree
with Quinton whether to pause KD. Weekend: review completed evidence and prepare
Week6; do not force a passing verdict or assume treatment will finish by Sunday.

One primary coding task alongside one GPU training job. CPU checks, saved-artifact
review, UI fixtures and documentation can proceed without pausing training. Do not
launch answer models, inference, another training run or heavy GPU UI benchmarks
concurrently. A planned pause must preserve checkpoint/backup and verify worker/GPU
cleanup; neither this plan nor board rollover pauses the current run.

The schedule risk is real: a long supplied-region KD run can consume the GPU time
needed for the required autonomous baseline. Reuse the completed control where
eligible and decide the GPU slot midweek rather than discovering the conflict Sunday.
Human availability is unconfirmed; prioritize the baseline over optional UI polish,
corpus expansion or another model experiment. Existing measurement comparison and
reviewed-feedback commitments remain visible; none are silently removed.

## Trello reconciliation

[Board](https://trello.com/b/vac4k8Po/prowl-quinton-evans-capstone): active columns
rolled to Week5, new Week5 Complete added, historical completed columns preserved.
W05-02 prototype and W04-03 qualification/launch closed with evidence; the latter
finished November2 and is placed in Week5 Complete despite its original Week4 ID.
KD-MAC remains In Progress for actual experiment completion/results. W05-01,
W04-01 and W04-04 are queued for the work above. W02-02 remains a visible imaging
provenance dependency. Broader AI-04/05 and W07-01 remain in Backlog, represented in
this week's bounded W04-04 work rather than treated as completed or cancelled.

Created [W05-03 stakeholder confirmation](https://trello.com/c/WD6xJcnB) and
[W05-04 weekly closeout](https://trello.com/c/nl7XeVHH). Older human-hours closeouts
remain open in Backlog; unattended runtime is never personal time. Corrected the
misplaced completed W03-02 card and AI-03's unchecked completion flag to match its
existing completed set-preparation scope; independent assistant acceptance stays open.


## November 2 follow-up: reuse the existing localizer and split machine work

The early localizer exists: CAP-EXP-012 child step300 (absolute600), a binary
SegResNet trained with113 training/40 development cases. The existing whole-CT
cascade and CLI were already connected to real weights on October9. Reuse these
components; the next task is compatibility and quality qualification, not rebuilding
localization. See [the complete connection and evaluation report](../imaging/AUTONOMOUS-CHECKPOINT-CONNECTION-2026-10-09.md)
and [012 results](../operations/CAP-EXP-012-RESULTS-2026-10-01.md).

Today the retained inference-only localizer.pt exists and its SHA256 matches the
original request: 46417801f3d3c37e618d06823027e84f0ce84343f469f24124537167d40198d5.
No checkpoint was loaded into a model and no GPU work was performed for this review.
Its40-case localizer evaluation had mean recall0.962519 but mean Dice0.129078,
median prediction/reference volume14.2596x and only15/40 joint ROI screens passing.
It is an available candidate, not an accepted precise localizer.

The later68-case CT-only cascade comparison retained33 positive cases and35
reference-empty cases, with seven unresolved-unit inputs still visible in the
original75-case accounting. Largest-component selection retained native lesion-box
coverage in33/33 positives, but mean lesion Dice was0.246612 and mean predicted
lesion volume on empty references13.989806mL. The broad crops remained a limitation.
These old segmenter/development results are not current-control/KD metrics or fresh
held-out acceptance. Reconcile present geometry, cohort exposure and source lineage
before reusing the path with the current segmenter.

Recommended division: Mac retains the frozen KD treatment; Mac CPU work prepares
integration, manifests and scoring. Windows CUDA laptop handles a bounded autonomous
baseline evaluation after its current work is verified complete and its GPU free.
The latest read-only chat record in “Plan capstone experiment workflow” reports the
November2 verifier launch (10,560 updates planned), followed by an exit-0 launcher
result. This is not a fresh completion, backup or GPU-idleness check. No message,
remote launch, data transfer or interruption was made for this planning review.

Portable handoff contents: pinned code, localizer and eligible segmenter weights,
preprocessing/ROI settings, case manifest with source hashes and role/exposure audit,
native units/geometry, resource limits, qualification command, separate reference
scoring and per-case result/failure schema. Reuse matching laptop data rather than
transfer the entire dataset. Verify a small cross-device case first; freeze the
bounded evaluation before cohort inference. Return metrics, failures, timing and
integrity evidence. Do not start another long model experiment to solve scheduling.

Board follow-up: W05-05 model/localizer handoff continues W02-02; W05-06 lifecycle
and provenance continues W04-01; W05-07 reviewer/assistant acceptance continues
W04-04; W05-08 continues KD-MAC; new W05-09 owns the portable CUDA evaluation packet.
Original card histories are preserved. Week4 Complete contains only delivered work:
teacher targets, fast preview/conversation UI and completed control training.
Unfinished acceptance stays in Week5; historical hours closeout stays open in Backlog.


## November3 stakeholder update

Quinton selected his aunt (industry-experienced, existing fallback) for a tentative
SaturdayNovember7 walkthrough; exact time and specific role remain unconfirmed.
Preparation is active in the existing Plan11 living record. The session has not
occurred and does not constitute clinical validation. Main Week7 acceptance stays
open pending actual feedback and role-appropriate task evidence.

## November 4 baseline and KD milestone

The bounded Lenovo autonomous evaluation finished: 63 completed cases and seven
declared admission failures, all retained in the original 70-case accounting.
The Mac verified the transferred metadata and independently reconciled metrics,
components and region coverage with a tested CPU-only reader. The
[error review and case queue](../operations/WEEK-05-AUTONOMOUS70-METADATA-REVIEW-20261104.md)
prioritize five missed components and large false-positive predictions for saved
image inspection. All annotation remained inside the expanded evaluation regions.
The 58 saved reference-unit assumptions and original numerical-equivalence failure
remain explicit. This is exposed-development baseline evidence under the approved
exception, not completion of the proposal's independent held-out acceptance.

KD resumed from the verified 14,029 checkpoint through qualified MPS recovery and
advanced beyond 14,100; MLflow, independent backups and hourly monitoring are
verified. No recipe or cumulative budget changed. Next useful parallel work is
the saved-image error review and reviewer handoff, rather than another GPU run.
Full G3 integration, independent acceptance and stakeholder feedback remain open.

The [seven-case visual review](../operations/WEEK-05-MAC-VISUAL-REVIEW-20261104.md)
is now complete: Lenovo inspected26contact sheets and Mac verified/imported the
private gallery and inspected nine key sheets. Findings distinguish remote false
predictions, pancreatic-region extra lesion labels, component misses and large
partly overlapping spillover. Preserve the reference-unit, possible related-case
and display limitations. No new scientific recipe or acceptance verdict follows.
KD continued beyond14,380updates while this CPU work ran; Lenovo is now idle.
