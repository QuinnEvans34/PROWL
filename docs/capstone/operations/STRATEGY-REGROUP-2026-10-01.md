# PROWL strategy regroup — October 1, 2026

**Status:** Codex assessment and recommendations for discussion with Quinton. These are not newly
approved decisions, implementation packets, launch requests or gate closures.
**Execution baseline:** D-306 / CAP-EXP-007 completed; no active or pending training run.
**Course start:** Monday, October 5; committed system by Week 8, Weeks 9–10 protected.

## Judgment

We are ahead of the pre-course localizer engineering target. We can qualify and freeze inputs,
train a new model, evaluate full volumes on their source grids, and independently restore its
checkpoints. The remaining bottleneck is useful localization, followed by the new lesion segmenter
and the complete review workflow. Training infrastructure progress does not mean the capstone's
autonomous imaging baseline or integrated product is complete.

The direction is appropriate: the proposal's central modeling problem is removing the supplied
pancreas region while controlling false alarms. The next work should use the infrastructure we
have built to answer that problem. Repeating completed qualification or continuing broad planning
without an experiment would add little. Spending the next several weeks only improving the
localizer would also put the rest of the committed system at risk.

## Evidence and authority reviewed

- Approved proposal v3.8 and appendix v3.1 were read directly from the preserved Word documents.
  Both hashes match [APPROVED-SOURCES](../../../references/governance/APPROVED-SOURCES.md).
  Later proposal drafts do not silently replace these sources.
- [MASTER-PLAN](../MASTER-PLAN.md), [Week 1](../weeks/WEEK-01.md),
  [implementation-start](../IMPLEMENTATION-START.md), Plans 04/05/06/11, and the
  [pre-course week](PRECOURSE-TRAINING-WEEK-2026-09-28.md) and
  [completeness review](PRECOURSE-COMPLETENESS-REVIEW-2026-09-28.md).
- [D-294 cohort freeze](../data/LOCALIZER-EXPANSION-V2-FREEZE-RESULTS-2026-09-29.md),
  [CAP-EXP-007 results](CAP-EXP-007-RESULTS-2026-09-30.md),
  [CAP-EXP-006 results](CAP-EXP-006-RESULTS-2026-09-29.md), and the current checkpoint.
- Latest retained Plan 07 [running log](../retrieval/planning/RUNNING-LOG.md), its phase checklist,
  the [UI foundation evidence](../testing/UI-FOUNDATION-2026-09-20.md), and local Git status/log.

This was a local evidence review. No training, new source-array reads, service installation,
literature download, outreach, commit or push occurred. Course-portal requirements, participant
availability and publisher-email delivery were not independently verified.

## What is ready and what is still owed

| Area | Evidence we have | Remaining work |
|---|---|---|
| PanTS localizer inputs | 113 training / 40 development-validation members frozen; all 176 candidates accounted for; 23 holds preserved; verified 2 mm cache | Expand only for an explicit experiment or unmet formal requirement; do not rebuild these same inputs by default |
| Training and recovery | Real MPS training, full-volume inference, native exports, checkpoints, independent keeper restores; latest source baseline 1,539 native tests | A separately tested longer budget and request; formal pipeline-wide orchestration remains separate |
| Useful localization | Learning and high reference recall, with retained per-case failures | Remove excess foreground while protecting coverage and manageable Stage 2 inputs |
| Lesion segmentation and cascade | Approved design and historical engineering knowledge | Qualify lesion targets, train a new three-class segmenter, connect predicted ROIs, and compare autonomous with provided-region inference |
| Scientific evaluation | Versioned localizer metrics and development evidence | Lesion containment, separate pancreas/lesion scores, patient sensitivity/specificity, controlled comparison and final freeze/evaluation |
| PANORAMA | Acquisition and integrity evidence; integration design | Source-specific mapping, provenance, exclusions, duplicate/group controls and mixed-source qualification under G2 |
| Literature | Frozen reviewer needs and accepted synthetic P3 foundation | P2 decisions/freeze, sizing/acquisition and infrastructure prerequisites, real corpus/index, retrieval and response evaluation |
| Interface and human review | Existing React/NiiVue foundation; bounded synthetic tests | Validated new prediction/evidence adapters, measurements, durable review events, real viewer tests and stakeholder feedback |
| Preservation and governance | September 28 Git publication and independently restored CAP-EXP-007 keepers | Review newer uncommitted source/docs; reconcile current evidence with Week 1 and gate summaries |

The data qualification is purpose-specific. A case qualified for pancreas-localizer supervision is
not automatically qualified for lesion supervision. References establish the visible annotation,
not complete-organ anatomy. Source-asserted provenance and unverified study-as-subject biological
uniqueness remain explicit in D-294; role checks alone do not prove final patient independence.

## What the latest run means

CAP-EXP-007 made 300 updates. Each of the 113 training cases supplied only two or three sampled
patches. That is sufficient for a bounded learning diagnostic, not a claim that the broader cohort
has been trained to convergence.

| Final development-validation result | Interpretation |
|---|---|
| Mean native Dice 0.0987 | Predicted foreground still agrees poorly with the reference |
| Mean native reference recall 0.9827 | Most visible annotated pancreas is included, averaged over cases |
| Median prediction/reference volume 18.50× | Excess foreground remains substantial |
| Mean acquired-scan crop fraction 0.4218 | The proposed crop still occupies roughly 42% of the scan on average |
| ROI screen 1/40 | Only one case meets both the current coverage and crop-size screen |

All 40 validation boxes cover their references at this checkpoint; 39 are too large for the current
screen. The mask recall average still hides weaker cases. Training case 7604 also loses box
coverage. Tiny references and difficult scans remain in the results; none was removed to improve
the aggregate.

High recall with enormous predictions is not useful localization. Conversely, the localizer does
not have to become the final review contour: Plan 05 assigns that contour to Stage 2. Its practical
test is whether it supplies an adequately covering region at a useful resolution and resource cost.
The current pancreas-box screen is an engineering diagnostic, not contour acceptance and not proof
of lesion containment after Stage 2 normalization.

CAP-EXP-007 completed in 33.082 minutes with peak RSS 5.638 GiB and sampled MPS driver allocation
4.799 GiB. Nine keepers independently restored, with an exact terminal prediction probe. This
supports trying a larger bounded local experiment; it does not establish throughput for full-scale
training. Mask and figure bytes remain local derived scratch; their recovery depends on retained
models, controls and inputs. A Git checkpoint protects a different set of assets.

## Recommended next modeling decision

**Question:** Can additional optimization reduce excess foreground while retaining reference
coverage on this same frozen cohort?

I recommend one fresh duration/schedule diagnostic before changing data, architecture or loss.
An initial candidate is **1,200 updates**, approximately 10–11 sampled patches per training case,
with earlier checkpoints for review. This is a proposed horizon, not an approved budget or request.
It is a more informative next step than immediately committing to days of training. Expansion to a
larger horizon should follow the evidence.

The current schedule decays to zero at 300. Extending its horizon changes learning-rate history as
well as duration. Name that combined intervention explicitly. CAP-EXP-007 can be contextual
evidence, but it is not a perfectly matched duration-only control for a different schedule.
Checkpoints within a fresh, consistently scheduled trajectory can show its learning curve.

The bounded packet should settle:

1. Exact fresh initialization, update horizon, schedule, checkpoint/evaluation cadence and comparison
   claims. Keep cohort, spacing, model, loss, sampling and prediction policy fixed unless declared.
2. Coverage safeguards with numeric review/stop rules chosen before launch. Include per-case
   recall and box coverage, worst cases, crop fraction, volume ratio and ROI-pass counts; never
   adopt a higher Dice result merely because it discards more reference pancreas.
3. Separate memory, elapsed-time, source-reference-read and output/backup budgets. Increasing updates
   is not permission for unbounded evaluations or reads. Reuse the verified cache; measure the new
   envelope rather than multiplying total runtime blindly.
4. Targeted synthetic checks for the changed horizon/schedule and transaction boundaries, followed
   by an exact frozen request and its launch decision. The current 300-update cap stays in force
   until that implementation is reviewed.

CAP-EXP-006 is the warning: 2,400 updates on the earlier 16/11 cohort increased Dice but drove
validation recall down to about 0.461. Undertraining is a plausible explanation for CAP-EXP-007's
oversized output, not an established diagnosis or a guarantee that more updates fix it. The runs
differ in cohort, spacing, context and exposure, so they cannot establish a cohort effect.

If the next trajectory shrinks predictions while maintaining coverage, plan the next justified
budget and Stage 2 handoff. If it shrinks predictions by losing coverage, preserve that failure
and investigate the objective/sampling/policy tradeoff. If it remains diffuse, examine probability
separation and sampling/loss behavior before another increase. Do not make cohort filtering the
default response. Formal G4/G5 baseline/comparison acceptance remains a later end-to-end milestone.

## The next capability: a small cascade slice

While the next run is being prepared or executing, specify the bounded Stage 2 implementation:

- Qualify a small development subset's lesion annotations and negative-case evidence for their
  actual purposes. Empty or absent labels must not become assumed lesion-negative targets.
- Build pancreas-only training ROIs with the approved physical margin/jitter policy. Lesion labels
  supervise output but never determine crop bounds.
- Verify pancreas **and lesion** containment after selection, margin, resizing and padding. Very
  large crops can lose useful resolution even when their boxes contain the reference.
- Train a new background/pancreas/lesion segmenter and verify native restoration and multiple-lesion
  preservation. Historical trained models remain excluded from the capstone model lineage.
- Run the same new segmenter with predicted and pancreas-reference ROIs under distinct identities.
  This measures where error comes from instead of attributing every failure to the segmenter.
- Preserve explicit failed/warning states. Plan 05 does not permit an oracle repair or silent
  whole-volume fallback for failed localization.

We can prepare and test that slice without calling the current localizer suitable or waiting for
perfect localizer Dice. The actual cascade's coverage and resolution evidence governs adoption.

## Proposed October 1–4 priorities

| Window | Priority | Concrete result |
|---|---|---|
| Thursday, October 1 | Review preservation and agree the next experimental question | Scoped Git checkpoint inventory; longer-run horizon/schedule/coverage proposal ready for discussion |
| Friday, October 2 | Implement and verify only the changed run envelope | Bounded executor changes, appropriate synthetic checks, measured budget and exact reviewable request |
| Weekend, October 3–4 | Execute if the exact request is approved; inspect and preserve | Learning curve with failures retained, restore evidence and an adopt/investigate decision |
| Alongside that work | Prepare the Stage 2 slice and reconcile Week 1 | Lesion-purpose qualification/ROI packet and a short evidence-backed October 5 queue |

The old Friday training-ready / Sunday first-smoke target has already been achieved on this
bounded imaging path. We should raise the learning target rather than pretend those milestones
are still ahead. A useful pre-course finish is **one informative broader-cohort learning curve,
preserved source and model evidence, and a concrete route into lesion segmentation**. If the
experiment cannot be safely ready, Week 1 still starts with a working, documented training path;
the proposal does not require a successful final model before October 5.

## Commitments that need attention alongside training

1. **Git and evidence preservation.** Local HEAD remains the September 28 documentation follow-up
   (`21f838c`). Newer data/training/retrieval source and docs are modified or untracked. Review and
   publish a scoped checkpoint after Quinton approves its concrete contents. Exclude local data,
   credentials, protected evaluation material and unrelated drafts. Audit ignored irreplaceable
   evidence separately; a public Git push is not a backup of every artifact.
2. **Week 1 / G0 reconciliation.** Most Week 1 design work is already approved. The checklist and
   implementation-start headers lag the current evidence. Map requirements to existing Python,
   UI and contract evidence, identify actual remaining failures, and update the current summary.
   Do not infer full G0 from 1,539 tests or rerun every old check solely to increase the count.
3. **Plan 04 orchestration.** The bounded localizer transaction is not the complete restartable
   workflow DAG. The tool spike and coding authorization remain separate under the current plan.
   Time-box that selection when authorized, reusing stable component interfaces instead of building
   a broad framework ahead of need. Full G3 is required before the expensive formal baseline.
4. **Claude's retrieval lane.** Latest retained P2 log still leaves whole-policy/seed freeze and
   candidate/scope decisions open; Run P remains unsigned. P3's accepted synthetic foundation is
   not a live corpus or evaluated assistant. Reconcile phase-checklist rows that still call the
   completed P3 packet pending. Resolve the remaining author decisions, storage/sizing and separate
   infrastructure approvals through the existing handoff; they do not block eligible imaging runs.
   Protected question authoring/evaluator access must precede formal retrieval evaluation.
5. **PANORAMA.** Keep the Week 3 integration commitment visible. Do not require it for this PanTS-only
   diagnostic, and do not treat acquisition/integrity evidence as completed G2.
6. **Course and people.** Quinton confirms actual course submission/work-log requirements. The
   publisher draft is still recorded as unsent; Quinton owns sending it at his chosen time. Record
   any new stakeholder status; detailed preparation remains deferred until a participant is confirmed
   or Quinton requests it. Week 5 fallback and Week 7 feedback checkpoints remain.

The existing UI foundation also has recorded dependency and real-viewer/accessibility follow-ups.
Address them before relevant integration/demo acceptance; they are not a reason to begin a broad
UI rewrite or interrupt an otherwise qualified local training diagnostic.

## Position against the ten-week plan

| Approved milestone | Position on October 1 |
|---|---|
| Week 1: architecture/test planning | Much design complete; executable evidence/status reconciliation remains |
| Week 2: protected cohorts | Early completion evidence for bounded PanTS localizer cohorts; formal source/patient completeness remains scoped |
| Week 3: PANORAMA | Acquired and partly verified; integration still owed |
| Week 4: reproducible inputs and restartable DAG | Localizer input/recovery path advanced; full DAG still owed |
| Week 5: autonomous baseline and queryable retrieval | Localizer experiments underway; new segmenter/cascade and real retrieval prototype still owed |
| Week 6: controlled comparison and retrieval evaluation | Diagnostic evidence informs this milestone; required end-to-end comparison and reports still owed |
| Week 7: integrated review and stakeholder feedback | Existing prototype/design, with production adapters, persistence and actual feedback still owed |
| Week 8: integration, held-out evaluation and documentation | Remains the committed system deadline; development validation is not final held-out evidence |
| Weeks 9–10: stabilization and delivery | Protected; no new experimental scope assigned |

Report progress by demonstrated capability rather than a percentage. We have crossed from
preparing to train into learning from real runs. The next strategic change is to spend more of our
effort on informative model experiments and the complete imaging path, while preserving the work
and keeping the supporting commitments moving.
