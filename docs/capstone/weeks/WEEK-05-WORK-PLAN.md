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
