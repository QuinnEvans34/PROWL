# October31 work spec: prepare the AI expert test while training continues

## Outcome and scope

Finish the remaining CPU-side recovery and AI testing work, then use a deliberate
GPU window to evaluate the prepared single-call summary candidate. Preserve the
running matched control experiment. This spec does not authorize stopping it,
changing its recipe, starting another model, or promoting the answer candidate.

Existing work to reuse:
- Recovery executor/controller and 23 CPU checks (647aa43,20998f8).
- Five exposed question/evidence packets and the preparation/review runner in
  scripts/retrieval/check_single_summary_candidate.py.
- The single-pass summary backend and shared Research/Workbench UI, documented in
  ../retrieval/SINGLE-PASS-SUMMARY-2026-10-28.md.
- Existing cancellation, citation, readiness and reviewer-save tests.

The teacher targets are complete. The active resource owner is student control
training; older notes that call it the teacher are historical.

## Work while training runs

| Order | Work and implementation boundary | Deliverable / stopping condition |
| --- | --- | --- |
| 1. Recovery handoff | Review the additive controller against the frozen launcher, especially original-owner cleanup, repeat pauses, validation interruption, inherited selection, cumulative budgets and tracking lineage. Add only missing checks. Prepare a bounded actual-MPS qualification command and receipt validation using existing executor qualification components; do not execute it. | Synthetic fresh-process recovery and failure-path checks pass. A concrete later stop/qualify/resume procedure identifies the exact owned processes and verified checkpoint. Unknown ownership, incomplete backup, exhausted budget or failed qualification prevents launch. No claim of real-GPU reliability yet. |
| 2. Fair answer comparison | Extend the existing runner rather than create a new benchmark framework. Snapshot the same five questions and evidence for current and candidate paths, bind model/prompt/config identities, preserve raw responses and errors, and expose load/prompt-evaluation/generation/total timing where the backend provides them. Mark absent timings unavailable. | Mock transports prove identical inputs, bounded calls, failure preservation and no model calls in preparation mode. A readable paired review is ready with quality decisions Pending. Existing saved answers may be references, but their old timings are not a matched live baseline. |
| 3. Inspect avoidable generation work | Inspect current and candidate call counts, prompt/evidence lengths, thinking settings and output limits. Identify redundant work from code and saved traces. Keep candidate tuning separate from the live service and freeze settings before comparison. | One short comparison table explains what changes and why. No speed claim from token counts alone; no silent passage truncation, qualification removal, weaker citation checks or per-question canned fixes. Do not add a smaller-model branch unless live evidence justifies it later. |
| 4. Shared UI and reviewer checks | Exercise existing synthetic/fixture paths for answer-first presentation, citation opening, partial answers, evidence gaps, service errors, cancel A then ask B, and late A responses. Verify save/reopen/revise and failed-save draft retention with synthetic records. Avoid expensive 3D rendering while GPU training owns the device. | Research and Workbench component checks pass; targeted isolated browser tests where feasible. No stale answer replaces the new question, pending state clears, sources remain accessible, and failed saves retain drafts. Report fixture evidence separately from real end-to-end acceptance. |
| 5. Handoff | Consolidate commands, test results and remaining gates into this file or the existing handoff docs. Update W04-03/04 and commit coherent passing changes. | One ready-to-run live checklist and a clear list of unresolved issues. Stop adding infrastructure once this checklist is executable. |

Run one small CPU test batch at a time, with bounded subprocesses and one-thread
ML fixtures where applicable. Check training progress/resources before and after
heavier batches; stop development checks if they cause pressure or stalled progress.
Do not load Ollama, start inference, rebuild the corpus, restart shared services,
install packages, read private held-out material, or modify active producing pins.
Keep test outputs separate from live reviews and all experiment artifacts intact.

## Later GPU window — after an explicit pause decision

1. Verify current owner identity, stop it by the verified procedure, inspect the
   cleanup receipt, verify checkpoint/independent backup and release of GPU ownership.
   The frozen original launcher cannot consume the new cooperative pause request.
2. Run the bounded real-MPS continuation qualification. Preserve a failure and stop
   if restoration, next-step equivalence, selection or resource accounting fails.
   Do not promise a two-hour window or a successful resume before this passes.
3. Run the same five packets through both answer paths once cold and once warm per
   packet: 20 logical answer requests total. A cold request requires verified model
   unloading; record how it was established. Preserve current per-call/request limits,
   impose a 30-minute total benchmark ceiling, and do not retry failed answers.
   Record underlying call counts because the old path may use multiple model calls.
4. Inspect every resulting answer against the supplied passages: relevance, factual
   support, completeness, numbers/units/populations/exceptions, readability, citation
   accuracy and appropriate refusals separately. These are exposed regression cases,
   not independent evaluation or evidence of broad clinical reliability.
5. Only after the bounded comparison qualifies, test the candidate on the existing
   UI through the authorized service-switch/rollback procedure. Measure retrieval,
   answer-service and browser total time separately from saved-evidence generation.
   Exercise both Research and Workbench, including cancellation and a replacement
   question. Restore the previous service if the candidate fails.
6. Stop/unload the answer model, verify cleanup, then resume the same experiment
   through the qualified continuation path with unchanged scientific settings and
   cumulative budgets. Verify advancing updates, backups and MLflow segment lineage.

## Acceptance and decision

Promote only if every reviewed supported answer is supported and complete for the
available evidence, the evidence-gap case behaves appropriately, citations support
the actual paraphrases, and no UI regression remains. A valid quote or citation ID
alone is insufficient. For a useful speed improvement, require at least a 20%
reduction in median warm saved-evidence answer time across the five paired cases,
with no new timeout and no paired warm regression greater than five seconds.
Report cold timings separately. This is a practical acceptance target for a small
session, not a statistically established latency guarantee. If quality passes but
speed does not, retain the current default and use the measured breakdown to choose
one next change. No benchmark-specific retries or hidden failure exclusions.

Expected commits follow actual fixes: recovery handoff, paired timing/reporting,
shared UI defects, and final test evidence. Do not create code churn to meet a
commit count. Actual live qualification and quality results remain Pending.
