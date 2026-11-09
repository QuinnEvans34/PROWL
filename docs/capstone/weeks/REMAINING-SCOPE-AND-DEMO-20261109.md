# Remaining scope and demo plan — November 9

Quinton's updated course sequence is two work weeks including this one, a class
demo, another work week, a PowerPoint/demo week, then final presentations. Exact
assignment dates are still unconfirmed. This is a recommended order of work;
it does not silently replace the master schedule or mark unmet requirements done.

**Recommendation:** prioritize one dependable imaging/review workflow, a usable
cited assistant, and an honest model comparison. A higher development Dice is
valuable, but another architecture is less useful now than a workflow we can
demonstrate and explain from input to saved decision.

## Keep and finish

| Deliverable | Concrete finish condition |
| --- | --- |
| Imaging and review | One admitted raw-CT → localization → segmentation → native-viewer → human-decision path, with valid reuse, stale-input rejection and recovery evidence. Keep a verified saved prediction available for demonstrations. |
| Model evidence | Close the existing continuation with its complete validation series, selected/final checkpoints, false positives, missed lesions, tracking and backups. Compare matched scopes; preserve raw scores and qualify the fixed 5 mm policy separately. |
| Cited assistant | Reliable startup, clear battery/source-only mode, correct citations, editing/cancellation and retained conversation behavior. Finish the source-grounded retrieval/answer evaluation rather than treating one successful answer as acceptance. |
| Stakeholder and communication | Conduct the planned aunt walkthrough, record actual observations and prioritized changes, reconcile personal work hours separately from compute, and assemble the demo/report evidence. |

The autonomous baseline still has 63 completed cases and seven declared failures.
Source-unit/resource admission and production workflow qualification remain open.
Supplied-pancreas transfer scores do not satisfy that autonomous baseline. If the
gap cannot close in time, agree an explicit fallback with the chair: demonstrate
the saved-result reviewer and report the autonomous shortfall, rather than
silently calling G3/G4 complete. Likewise, a postponed walkthrough or unfinished
formal retrieval evaluation remains a requirement gap, not a completed task.

## Defer unless needed to fix a core defect

- Additional architectures, model shopping, ensembles and a learned false-positive
  verifier. Do not start new runs merely to fill both GPUs.
- Broad corpus expansion, new dataset acquisition and infrastructure migrations.
  The existing versioned corpus is enough to finish the retrieval evaluation.
- Large visual redesigns and optional features unrelated to the core review task.

The prepared auxiliary-loss ablation remains a possible **single controlled**
comparison after the current evidence review, only if it answers a clear question
and fits the remaining qualification/evaluation time. This plan authorizes no
new training launch, data access, protected evaluation, gate change or promotion.
Pretraining/patient overlap remains unresolved; do not claim leakage-free scores.

## Order through the remaining course milestones

1. **This week:** close current model evidence; work through the specific
   autonomous-baseline blockers; finish retrieval/answer evaluation and the
   reviewer checks. Confirm and conduct Saturday's participant session.
2. **Next work week:** integrate the chosen model only after its admission checks;
   fix the highest-impact walkthrough defects and rehearse the complete demo,
   including battery/offline and failed-service behavior. Avoid starting training
   that cannot finish and be evaluated before integration must freeze.
3. **Class demo:** show the dependable path and describe development results,
   known errors, assistance and scope limits. Collect feedback.
4. **Following work week:** address demonstrated core defects and finish missing
   evidence. Freeze features before the presentation rehearsal; retain explicit
   shortfalls instead of filling them with new unqualified scope.
5. **PowerPoint/demo and final presentations:** focus on the story, measured
   results, limitations, reproducibility and reliable delivery. Change code only
   for demonstrated defects and rerun the affected checks.

## Battery meeting runbook

**Prepare AI expert** now starts CPU source search on battery using the existing
internal literature database. It does not load the local answer model. The UI
states that limit and blocks Ask/Help, including Enter submission; **Find sources**
and source passages/citations remain available. Returning to AC and preparing
again can upgrade the verified helper-owned service, subject to the existing GPU
and safety gates. Full generation was not requalified on battery.

For the short check-in:

1. Open [Training](http://127.0.0.1:5180/training) to show dated results and the
   measured/estimated compute accounting. Explain that this is a retained snapshot.
2. Open [Research](http://127.0.0.1:5180/research), prepare, then **Find sources**
   for “Why can pancreas boundaries be hard to outline on CT?” Open a citation
   and its original passage. This demonstrates retrieval, not a newly generated
   battery answer. Opening the publisher website itself requires internet.
3. Open the [saved prediction](http://127.0.0.1:5180/saved?review=b671bd4453db6c91d842d948c95eeac351df76902480d54b5389a2a174efd2f5)
   to show native CT and predicted overlays. “How big is this pancreas?” calculates
   the predicted-mask volume locally; it does not establish anatomical truth.
   Do not launch new segmentation or fabricate a participant decision.
4. If a local service cannot run, show the retained screenshots as saved examples.
   The earlier AC-powered AI answer can be discussed as a recorded example,
   with its known answer-quality limitations.

The CPU literature and saved-review services are deliberately left available for
this meeting. No local model inference or training is running. Existing Lenovo
training is unchanged. Read the [startup evidence](../testing/CHAIR-DEMO-READINESS-20261109.md)
and [ten-minute talking points](DEGREE-CHAIR-CHECKIN-20261109.md).
