# Degree-chair check-in — November 9

Talking points for a roughly ten-minute conversation. Results below are dated
development observations; the ongoing experiment's final result is still pending.

**Where I am:** I've built PROWL into a working research application that combines
CT viewing, pancreas/lesion predictions, a cited literature assistant and saved
human reviews. The main work now is improving model quality and finishing the
qualification of the fully autonomous imaging workflow.

**What I've built and improved:**

- The viewer shows full CT scans with prediction overlays and native-coordinate
  measurements. The reviewer can record a decision, reopen the same prediction
  and retain revisions. I added identity, integrity, stale-result and recovery
  checks so a response or saved decision cannot silently belong to another scan.
- The AI expert retrieves passages from a versioned collection of 14 authorized
  sources and 1,179 passages, then produces a cited response. I found retrieval
  was much faster than local answer generation, so moving all the data off the
  external drive was not the main fix. I did qualify an internal working copy of
  the small literature database for availability. A single generation call, bounded output
  and disabled thinking mode made the assistant much faster. In my October 31
  testing, responses went from around 40 seconds to usually 2–4 seconds; that is
  an observed development result, not a benchmark guarantee for every question.
- I rebuilt the conversation UI around question/answer history, cleared drafts,
  editing/resending, cancellation and source inspection. I've also written tests
  around citations and saved review state. Formal answer-quality measurement and
  actual stakeholder feedback are still ahead of me.
- The training setup now spans a Mac and Lenovo, with reproducible configurations,
  MLflow, checkpoints, independent backups, recovery evidence and an experiment
  history. Failed attempts stay recorded instead of disappearing from the story.

**What the model experiments taught me:**

- The matched 24k-step knowledge-distillation comparison completed. Selected
  development Dice was **0.3836 for control versus 0.3891 for KD**. The improvement
  was small and lesion-component detection worsened, so I did not treat KD as a
  clear winner. It was still useful to implement and evaluate the approach.
- STU-Net-B transfer learning reached **0.3716 at 12k**. A corrected continuation
  is now running to 24k total ancestry steps. Its best raw lesion Dice so far is
  **0.4305 at 18k**; the latest complete 22k validation is **0.4122**. These scores
  average the 36 lesion-positive cases within a 70-case development cohort and
  use supplied pancreas regions. They are not an autonomous or independent test.
- I investigated false positives rather than only extending training. Confidence
  thresholds did not improve Dice. A fixed 5 mm predicted-pancreas proximity filter
  improved the original 12k checkpoint from **0.3716 to 0.3949**, with measured
  lesion recall and detection unchanged. That result still needs qualification
  on each future model. It has not been applied to the ongoing training results.
- Inspecting publisher-model predictions and our own error galleries showed both
  missed lesions and excess predicted tissue. This helped choose follow-up tests;
  it does not mean our model matches a published benchmark. Pretraining/patient
  overlap remains unresolved, so I am keeping those claims restricted.

**How much compute:** The reconciled records show **646.1 training-session hours**
across the two machines: Mac 323.5 and Lenovo 322.6. This includes 177.0 hours estimated
from early MLflow timestamps. Teacher-target generation adds 91.0 hours, for 737.1
recorded model-work hours. These include validation/checkpoint/I/O time, exclude
unattended time from my personal work log, and are not measured GPU-active hours.
They are the records we can verify, not a certified exhaustive project history.

**What remains:** The autonomous evaluation retained63 completed cases and seven
declared failures. I still need to resolve unit/resource admission and workflow
qualification before calling that baseline complete. This week's priorities are
closing that gap, reviewing the completed continuation, measuring retrieval and
answer quality, and preparing the preliminary stakeholder walkthrough with my
aunt on November 14. Exact session details remain to be confirmed.

**What I'd like feedback on:** Does the balance between software integration and
model experimentation match the capstone expectations? For the remaining weeks,
is closing the autonomous workflow and documenting reliable evaluation the right
priority over pursuing more model variations?

**How I'm protecting the remaining time:** I want to finish one reliable imaging
and saved-review path, measure the assistant's answer quality, and close the
existing model comparison before adding more architectures or broad UI changes.
The [remaining-scope plan](REMAINING-SCOPE-AND-DEMO-20261109.md) maps that work to
the class demo and final presentations. If the autonomous qualification remains
blocked, I want to agree an explicit scoped fallback rather than overstate it.
For this battery-powered meeting, Research now supports live AI summaries as
well as source search and citations. Unplugged loading and generation were
[verified after the explicit battery authorization](../retrieval/BATTERY-EXPERT-20261109.md).

## Optional things to open

1. [Training page](http://127.0.0.1:5180/training): current saved Dice history,
   source time, per-machine hours and the estimate/accounting boundaries.
2. [Research](http://127.0.0.1:5180/research): one general question, then a citation.
   The boundary question already used in development is a suitable regression,
   not an untouched accuracy test. Conversation is session-local, not persistent.
3. [Saved development prediction](http://127.0.0.1:5180/saved?review=b671bd4453db6c91d842d948c95eeac351df76902480d54b5389a2a174efd2f5): open the retained
   package directly; explain predictions and mask measurements without asserting anatomical
   truth. Do not launch new inference during the meeting or create a participant
   decision just to demonstrate that saving works.
4. If services or the drive are unavailable, use the retained screenshots and
   reports. Identify saved examples as saved; do not present them as live output.

## Supporting evidence for a deeper discussion

- [Week5 closeout and open requirements](WEEK-05-EVIDENCE-CLOSEOUT-20261107.md).
- [Week6 plan](WEEK-06-WORK-PLAN.md).
- [Training-hours reconciliation and source pins](../operations/TRAINING-ACCOUNTING-REFRESH-20261109.md).
- [KD comparison](../operations/KD-DESCRIPTIVE-ANALYSIS-20261106.md).
- [Original STU-Net review](../operations/STUNET-RESULTS-AND-NEXT-STEP-20261108.md)
  and [current continuation snapshot](../coordination/LENOVO-CHECKIN-EXPORT-20261109.md).
- [Spatial policy results](../operations/STUNET-POSTPROCESS-RESULTS-20261108.md)
  and [standing per-model qualification policy](../evaluation/SEGMENTATION-POSTPROCESSING-POLICY-V1.md).
- [Reviewer-flow checks](../testing/REVIEWER-FLOW-20261107.md).
- [Today's demo check and preparation instructions](../testing/CHAIR-DEMO-READINESS-20261109.md).
- [Measured retrieval/model latency breakdown](../retrieval/EXPERT-SPEED-2026-10-28.md)
  and [internal literature database qualification](../retrieval/INTERNAL-LITERATURE-SERVICE-2026-10-28.md).
- [Concrete autonomous-baseline next work](../operations/AUTONOMOUS-BASELINE-NEXT-WORK-20261109.md).

This is a prepared check-in, not a record of a meeting, participant feedback,
course submission or confirmed personal hours. Meeting date/time itself was not
provided; November9 is this preparation date.
