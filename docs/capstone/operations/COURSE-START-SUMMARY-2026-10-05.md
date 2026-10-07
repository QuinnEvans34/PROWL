# PROWL course-start progress account — October 5, 2026

Prepared October 3 for Quinton's Monday discussion. Official Week 1 is October 5–11.
Wording settled during Quinton's October 3 preservation discussion. Actual course assignments and
due times still need to be checked against the course portal.
Preservation and literature status reconciled October 4; this is a progress account, not the
instructor's assignment specification.

**October6 update:** the Monday account below retains its October4 snapshot. Setup has since
been submitted; Resources and What/Why/How artifacts are prepared. Imaging development and the
B03 technical metadata pass are in [the live Week1 queue](../weeks/WEEK-01-EXECUTION-QUEUE-2026-10-06.md).
The retrieval owner's [October6 handback](PLAN07-V13-HANDBACK-2026-10-06.md) records v1.3 native
acceptance and qualified guarded binding, with actual N4 rehearsal still incomplete. Current
[hours](../weeks/HOURS-LOG.md) are provisional and [preservation](WEEK-01-COMMIT-HANDBACK-2026-10-06.md)
now follows Quinton's meaningful-commit/GitHub-visibility request. No new training claim.

## Suggested Monday wording

Before class, I established working training and evaluation paths for PROWL's pancreas localizer
and three-class segmenter, including native-coordinate prediction exports and independently
verified checkpoint recovery. This exceeds the initial pre-course training-readiness goal.

The model results remain early. The localizer proposes oversized regions, and the segmenter still
produces poor contours. Its current pilot uses a pancreas region derived from the reference label,
so it does not yet demonstrate the autonomous localize-then-segment workflow. I am retaining weak
results and difficult cases in the evidence.

The reviewed implementation and evidence are preserved in local checkpoints. My Week 1 priorities
are to prepare a controlled duration comparison with coverage, false-positive and resource
requirements, and define the predicted-ROI integration and varied multiclass qualification path.
PANORAMA integration, literature
retrieval, orchestration and the durable reviewer workflow remain on the ten-week plan. The aim is
a coherent, auditable annotation-assist system with honest evaluation.

## What the results mean

| Evidence | Demonstrated result | Remaining limitation |
|---|---|---|
| Localizer, CAP-EXP-012 | 113 train/40 development-validation cases; validation Dice 0.129078 and mean recall 0.962519; independently recovered checkpoints | Median predicted/reference volume 14.2596×; usefulness endpoint failed. No adopted autonomous ROI policy |
| Segmenter, CAP-EXP-014 | Six train/one report-only case; fresh 48-update v5 comparison restored pancreas predictions. Training pancreas Dice 0.159877, lesion Dice 0.055142 and lesion recall 0.833063; all six lesion components hit | Training lesion volumes 12.78–383.26× reference; poor precision and contours. Report-only 2514 lesion recall declined to 0.123936. Positive-only pilot cannot establish specificity |
| Recovery and software | Latest experiment ran against a 2,933-test native baseline; four checkpoint probes and seven restored native predictions matched exactly | Software checks establish mechanics, not clinical utility, model generalization or percentage complete |
| Literature and interface | Accepted P3 synthetic retrieval foundation; bounded S1 storage setup; Claude's S2 v1.1 offline tool, with 144 native sizing/326 retrieval checks; all 12 retrieval schemas in the shared offline checks; existing UI foundation | S1–S2 binding incomplete pending bounded parser diagnostics; no signed sizing run or live corpus/index/evaluation. Real model/evidence adapters and durable accept/edit-required/reject interaction remain |

Local preservation is complete: `5856fdc` preserved 625 reviewed files and the portable-test work;
`edf5e47` preserved 67 Plan07/setup/shared-check files and handbacks. Nothing was pushed. The
[latest handback](PLAN07-FOLLOWUP-HANDBACK-2026-10-04.md) names the unfinished binding and exact
next dependency. Shared checks passed 173 combined/198 contract-gate tests; these targeted results do
not replace the historical 2,933 native baseline or claim a new full expanded-project suite pass.

The segmenter currently receives a reference-derived pancreas region. This is a provided-region
pilot. The autonomous cascade has not been demonstrated. Tiny, boundary and failed cases remain in
the evidence; unknown empty lesion labels remain held rather than being called verified negatives.
The report-only case selects no settings, checkpoints or membership.

## Week 1 working priorities

1. Match the actual Week 1 assignment/rubric to existing evidence and identify any requested
   deliverable or proposal revision. The [original local preservation](PRESERVATION-COMMIT-2026-10-03.md)
   and [Plan07 preservation](PLAN07-LOCAL-PRESERVATION-2026-10-04.md) are complete. The
   [portable test boundary](TEST-PORTABILITY-RESULTS-2026-10-03.md) passes 2,933 fast tests without
   local outputs/registry, plus eight selected local-evidence checks. Public push is a separate decision.
2. Prepare one fresh, bounded segmenter duration comparison: controlled recipe, terminal-primary
   endpoint, per-case coverage, false-positive reporting, stop rules and exact resource/storage
   budget. Falling saved loss supports the question; it does not prove that more updates solve it.
3. Define predicted-ROI integration and containment qualification, alongside the route to a varied
   multiclass cohort with verified negatives and separate development evaluation.
4. Reconcile architecture/test traceability and next bounded packets for PANORAMA, the workflow DAG,
   literature and durable reviewer interaction. Keep these commitments visible while imaging work
   progresses; protect Week 8 integration/evaluation and Weeks 9–10 stabilization/delivery.

The [weekend/remote queue](WEEKEND-AND-REMOTE-WORK-PLAN-2026-10-03.md) breaks these into finite tasks
with outputs and stop points for asynchronous phone access. Quinton retains publisher outreach and
consequential experiment/publication decisions.

## Before submitting a course update

- Verify the actual Week 1 assignment, required format, due time and any proposal revisions.
  October 5–11 is the internal planning week, not a confirmed assignment deadline.
- Record Quinton's own working hours separately from agent runtime.
- Use the current repository-review result for preservation status; no new run is pending.

The [original retrieval support handback](../retrieval/CODEX-PLAN07-L1-L6-HANDBACK-2026-10-03.md)
records P2 reconciliation and the earlier S1/S2 proposals. The
[October 4 follow-up](PLAN07-FOLLOWUP-HANDBACK-2026-10-04.md) records qualified setup/tool work,
shared-contract integration and the pending binding. Candidate verification/freeze, S3/S4 and
live execution remain ahead; the binding gap does not prevent the Monday progress discussion.

Evidence: [master plan](../MASTER-PLAN.md), [Week 1](../weeks/WEEK-01.md),
[pre-course retrospective](PRECOURSE-RETROSPECTIVE-2026-10-03.md),
[CAP-EXP-012](CAP-EXP-012-RESULTS-2026-10-01.md),
[CAP-EXP-014](CAP-EXP-014-RESULTS-2026-10-03.md).
