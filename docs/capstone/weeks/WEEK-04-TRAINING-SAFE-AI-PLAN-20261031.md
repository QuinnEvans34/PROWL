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

## October31 implementation handoff

CPU preparation is complete; actual GPU recovery, real answer quality/latency and
promotion remain Pending. Training was not stopped and no model was loaded.

- ae358ba: original-owner stop command with read-only default, verified launchd/PID
  ownership, explicit stop request and separate cleanup verification. No force-kill
  fallback. Added two-worker MPS cold-restore qualification command, not executed.
  Its engine was tested on invented CPU state; prior fresh-worker actual CPU session
  recovery remains covered. The live-launch gate now requires stage/device/resource
  evidence, not merely a JSON success flag.
- e3d5577: fixed cumulative storage accounting for a completed continuation parent
  when the next arm starts in another directory. Old attempts retain their budget.
- 014a962: paired baseline/candidate runner reuses the five exposed packets, alternates
  arm order by packet, verifies unloaded/resident state, retains raw calls and missing
  timing fields, preserves errors, blocks rerunning an attempted output and checks
  model unloading at cleanup. No answer or timing acceptance is automatic.
- c87753e: isolated browser checks for both page and panel variants, cancelled A/new B,
  citation opening and answer return. Synthetic viewer, disabled GPU, intercepted
  answer transport; no actual model, scan or shared service involved. Fixture now
  includes the assistant and current scoped styles.

Verification:39 Python tests passed12.43s;102 focused UI tests passed5.90s with
installed Node24.21.0;2 browser tests passed2.2s, screenshots inspected. Initial
Node20 run failed before tests (unsupported runtime); no dependencies were changed.
Initial browser fixtures lacked the Ask panel, then used an exact text locator that
included an inline citation. These fixture issues were corrected; first failures
remain in outputs/prowl/testing/summary-browser and summary-browser-02. Final scoped
screenshots are in summary-browser-05. No production UI defect was demonstrated.
Save/reopen/revision, failed acknowledgement/draft retention and source attachment
behavior passed existing component tests; earlier actual transport evidence is in
../orchestration/REVIEWER-WALKTHROUGH-20261027.md. No new real reviewer record was made.

Prepared review: outputs/prowl/paired-summary-preparation-20261031-02/paired-review.md.
All five packets contain five passages, with total text lengths2321/1734/2714/2503/
2490characters. Both paths fit their existing budgets. Do not truncate source text.

| Code inspection | Current general fallback | Candidate |
| --- | --- | --- |
| Local model | pinned Qwen3:8b | same pinned Qwen3:8b |
| Calls per answer | select + audit,2 | summarize,1 |
| Thinking | enabled both calls | disabled |
| Context allowance |8192tokens/call |8192tokens |
| Output allowance |4096tokens/call |1536tokens |
| Request deadline |90seconds |60seconds |
| Answer form | exact selected sentences | model prose + exact supporting quotes |

This identifies avoidable generation work, not measured speed. The benchmark
compares the general fallback generators on identical saved evidence; it excludes
reviewed-answer routing/cache hits, retrieval and UI time. Those require the later
end-to-end walkthrough. No prompt/model tuning was needed before this comparison.

### Commands for the later authorized window

Run from the repository with .venv312/bin/python and
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies
for recovery tools. All destination directories below must be fresh. Resolve the
current receipt hash, active arm and live owner again at execution time.

1. `scripts/diagnostics/stop_original_mac_kd.py --root ORIGINAL --receipt-sha256 HASH --arm control --checkpoint last.pt`
   is read-only. Add `--stop --output STOP_RECEIPT` only after the pause decision.
   Then `--verify --output STOP_RECEIPT` verifies owner/worker absence, resource
   reaping, backup identity, remaining time and released GPU lock. An unsuccessful
   verification does not authorize disconnecting the drive or starting another job.
2. `scripts/resume_mac_kd_comparison.py --prepare --root CONTINUATION --original ORIGINAL --original-sha256 HASH --parent ORIGINAL --parent-sha256 HASH --arm control --checkpoint last.pt --backup NEW_BACKUP`
   prints the continuation receipt hash. This can run only after cleanup.
3. `scripts/diagnostics/qualify_mac_kd_continuation.py --prepare --root QUALIFICATION --continuation CONTINUATION --continuation-sha256 CONTINUATION_HASH --backup QUALIFICATION_BACKUP`
   prints a request hash. Run `--root QUALIFICATION --stage producer --request-sha256 REQUEST_HASH`,
   inspect its receipt, then run the cold stage with the same hash. Each stage is
   bounded1200seconds/12GiBRSS; three engineering updates total, no horizon change
   or scientific update. This checks actual restore/next-update equivalence; it
   does not repeat native validation. Do not retry a failed directory.
4. AI comparison: `PYTHONPATH=. .venv-retrieval/bin/python scripts/retrieval/compare_single_summary_candidate.py --output FRESH_COMPARISON`.
   Its default path requires the exclusive GPU lock. Add `--prepare-only` for
   model-free preparation. Inspect paired-review.md, raw results and cleanup;
   then follow the existing single-pass candidate service-switch/UI/rollback steps.
5. After answer-model cleanup, use the existing owned launchd wrapper to dispatch
   `scripts/resume_mac_kd_comparison.py --launch --root CONTINUATION --receipt-sha256 CONTINUATION_HASH --qualification QUALIFICATION/qualified.json --qualification-sha256 QUALIFIED_HASH`.
   Use a fresh scoped launchd label, absolute script/runtime paths and the same
   environment. Verify updates, independent backups and MLflow segment lineage.
   New continuations accept `pause_mac_kd_comparison.py --root CONTINUATION --receipt-sha256 CONTINUATION_HASH`;
   a request alone is not cleanup confirmation.

Final read-only inspection found the original supervisor99276/worker99515 still
owned by gui/501/com.prowl.mac-kd-comparison-20261030-01, at10000updates and native
validation. last.pt and independent backup passed the audit at step10000; that
checkpoint precedes validation, so a restore would replay the pending validation.
Do not promise an immediate pause or a no-replay restart. Prefer a completed
non-validation checkpoint for the planned window when convenient.

## Authorized live window: recovery passed

The user subsequently authorized pausing training for AI testing. The verified
original launchd owner was stopped through stop_original_mac_kd.py; cleanup,
GPU release and independent checkpoint identity passed. Recoverable step10000;
pending native validation must replay. Original measured budget charged86548s,
remaining259052s of345600s. No scientific settings or original evidence changed.

External evidence under distillation-mac-20261023:
- mac-kd-demo-pause-20261031-01: stop request and verified cleanup.
- mac-kd-continuation-20261031-01: prepared continuation, NOT launched;
  receipt SHA256 c27121c457b6ca8d84260c66c376877cfd2aa77b08ffd1799693fcc97978b558.
- mac-kd-continuation-check-20261031-01: actual MPS producer19.660s,
  cold8.744s, both exit0/reaped; peak owned RSS2586476544/2427731968bytes.
  Independent restore and next input/state equivalence passed unchanged tolerance.
  Three engineering updates, zero scientific updates, no native validation replay
  in this check. Qualified receipt SHA256
  e7d72f89a8053be04c643d2c229c9ad9d4f3eacad38af586ec0e3c26c7e59195.

Training remains paused during the bounded AI comparison. Do not restart it while
the answer model or candidate service owns the GPU. Actual resumed scientific
progress and pending-validation replay remain to be verified after this window.

## Live answer comparison: candidate rejected

Evidence: outputs/prowl/paired-summary-live-20261031-01, including frozen inputs,
raw model calls, results, paired-review.md and verified model-cleanup.json.
All20 planned logical observations recorded; three candidate warm generations
were intentionally not attempted after their cold requests failed. No retries.
Thus17 generation requests ran, not20 successful answers. No request timed out.

| Packet | Current cold/warm seconds | Candidate cold/warm seconds | Manual candidate finding |
| --- | --- | --- | --- |
| Function |28.70/25.78 |8.27/not attempted | Rejected: quotation changes “epigastric region” to “epigastr”; endocrine claim's cited excerpt alone omits hormone secretion. Unnecessary partial-coverage limitation. |
| Function paraphrase |42.52/53.63 |8.01/not attempted | Rejected: quotation removes source reference markers and changes punctuation. Limitation wrongly treats everyday wording as an evidence gap, ends mid-sentence, and prose refers to passage numbers. |
| MRI methods |33.53/25.92 |10.92/not attempted | Rejected: model inserts an ellipsis into an exact quotation. Core method is supported, but limitation repeats the answer and ends mid-sentence. |
| Focal fat on CT |56.39/47.88 |10.79/8.28 | Citations and CT/MRI distinction supported; core CT criteria complete. Readability fails: limitation says differentiating fat from tumor does not answer how they look different and ends unfinished. MRI addition is secondary to requested CT. |
| Missing stiffness range |16.82/13.77 |3.39/1.32 | Correct refusal in both runs: no invented kPa range; clear explanation of missing evidence. |

Manual review covered every returned answer against its full supplied passages.
The current path's claims/citations are supported and contain the available core
answers; its function responses include distracting anatomy/cell detail and its
MRI response includes excessive acquisition settings. These are readability issues,
not evidence of broader independent acceptance. MRI answer is one study's method,
not a universal protocol. Both paths correctly refuse the unsupported numeric range.

Baseline median warm time25.92s. Only two complete warm pairs exist, so the required
five-pair latency acceptance cannot be established. Short rejected candidate times
are not successful-answer speedups. The candidate fails citation binding and manual
readability/coverage review; do not promote or switch8016. UI candidate walkthrough
is deferred because its answer-quality gate failed, not recorded as passed.

Next targeted revision should let the model cite existing sentence identifiers and
have the application copy exact source text, preserving full passages and semantic
review. Separately correct coverage instructions so ordinary paraphrases do not
trigger spurious limitations. Preserve this failed version and compare a newly
identified candidate; never loosen quote matching or silently repair model prose.

The existing general-source-extract backend remains active. After benchmark cleanup,
the normal Prepare AI expert action is used to warm the pinned model for user testing.
Training stays paused; unload the answer model and verify GPU cleanup before any
later explicit training resume.

## October 31 conversation UI and verified scientific resume

User requested a message thread, edit/resend, cleared composer and loading feedback,
then return to training. Implemented session-only chronological turns in Research
and Workbench; existing answers remain visible while drafting. Edit copies wording
into the composer and sends a fresh independent request, preserving the original.
Citations remain bound to each turn; history clears with study changes and is not
persisted across refreshes. Loading uses animated dots (reduced-motion supported),
elapsed time and Cancel; late callbacks cannot replace a newer answer. Workbench
keeps its composer visible while the conversation scrolls. New turns scroll to the
question/answer start rather than metadata. 75 focused UI tests pass; build passed
before the final scroll adjustment. Live Research and Workbench responses rendered,
and Research edit/resend preserved the original turn. Commits40823b9/ba55377/b7e91c9.

Stopped verified preview PID82044, unloaded8B, verified empty Ollama models and free
GPU lock. CPU source service PID2105 remains available. AI generation is unavailable
while scientific training owns the accelerator; no concurrent answer-model test.
Original slower backend is source-service fallback only during training. Restore
fast-preview service after the next explicit training pause; do not mistake this
fallback for an intentional reversal of the accepted fast-preview preference.

Verified continuation receipt c27121c457b6ca8d84260c66c376877cfd2aa77b08ffd1799693fcc97978b558
and qualification e7d72f89a8053be04c643d2c229c9ad9d4f3eacad38af586ec0e3c26c7e59195.
Launched ONCE via com.prowl.mac-kd-continuation-20261031-01, supervisor2277/worker2581.
Root: /Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/mac-kd-continuation-20261031-01.
MLflow7d9b079674454cfcb44ef367704a53f7 RUNNING, linked to original30016b3403bd422e8b1f00309aff290f.
Restoredstep10000; native validation replay began and firstcase completed after55s,
with24/24tiles observed. No new optimizer update claimed before pending validation
finishes. initial.pt and step-010000.pt match independent backup SHA256
5b37c9d3d0fb037093d0e3efc135a2e4480efc70bf965644244db3f3653379b1. Original
remaining budget259052s retained, no scientific recipe change or duplicate worker.
Use existing cooperative pause controller for this continuation. Preserve its pins.
