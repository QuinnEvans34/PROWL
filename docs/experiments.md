# PROWL living experiment notebook

**Active use confirmed by Quinton:** 2026-09-18

**Purpose:** Plan every experiment before execution, retain every outcome, and use evidence to choose
the next experiment throughout development. This is the continuing notebook, not a retired archive.

## Current capstone authority and historical boundary

The [capstone hub](capstone/README.md), approved proposal/appendix, and
[experiment protocol](capstone/evaluation/EXPERIMENT-PROTOCOL.md) govern new work. The earlier log
below is preserved unchanged, including future ideas, original claims, amendments, and withdrawn
results. Its old commands, priorities, models, thresholds, and headings marked `CAPSTONE` or
`PRE-REGISTERED` are not automatically current execution plans.

In particular, old ideas that repeatedly evaluate or tune on the official test cohort must be
redesigned around permitted development data. Publisher-test data remains held out until selection
is frozen. Historical oracle results, contaminated comparisons, and prior trained checkpoints cannot
be promoted into capstone evidence or initialization. Lessons and hypotheses can carry forward;
previous project models cannot.

This notebook is the human-readable plan and interpretation layer. Immutable experiment/run,
configuration, checkpoint, and evaluation artifacts remain the execution evidence under Plan 06.
Link them by ID/hash rather than copying changing scores into competing logs. GitHub/Notion summaries
link back here and to those artifacts; they do not replace either record.

## Required working loop

1. **Before execution:** create an entry here with the question, prior evidence, comparison or
   functional gate, planned changes, fixed factors, data roles, success/failure rules, prerequisites,
   and time/storage/cost ceiling. Use the full Plan 06 preregistration for substantive experiments;
   smokes use its compact form. Do not launch an undocumented experiment.
2. **At launch:** link the frozen design version and exact run/attempt IDs, code/environment/config,
   registered cohort identities, command, and output location by artifact alias. Capture the design
   before results; do not expose secrets, raw data, or private absolute paths here.
3. **During work:** append dated health observations, deviations, interruptions, and retry/resume
   identities. Do not revise the original hypothesis or decision bar after seeing results.
4. **After every attempt:** record the terminal state, evidence links, outcome, caveats, and what was
   learned. Include nulls, invalid runs, cancellations, and operational failures—not only successes.
5. **Before the next experiment:** explain what evidence motivates it, what recipe/settings carry
   forward, what changes, and why that is the next useful test. Link the parent experiment(s), not
   just whichever checkpoint has the largest score. A promising exploratory result motivates a
   controlled follow-up; it does not become a formal winner retroactively.

An experiment is the question/design; a run or attempt is an execution of it. Record every rerun and
resume under that design, and create a new design version/ID when the scientific question changes.
Routine unit tests stay in test reports; experimental smokes, benchmarks, retrieval experiments, and
model/evaluation experiments all receive notebook entries at a proportionate level of detail.

## Active capstone queue

Use `CAP-EXP-001`, `CAP-EXP-002`, and so on for new capstone entries; retain historical `EXP-*` IDs.
Reserve an ID only when adding an actual planned experiment. No capstone experiment is newly queued
or launched by this documentation update. Review the historical future ideas during the required
post-planning strategy session, then register selected ideas with current gates and data roles.

Each queued item links to an entry below and states its priority, status, dependencies, expected
duration, and next decision. Queue presence never grants execution permission. Update after each
attempt and review priorities at least weekly. Week 9 permits stabilization only; Week 10 cannot
introduce result-changing experiments.

## Capstone entry template

Copy this template into the active entries section, without changing the historical record. The
linked Plan 06 protocol supplies the full fields for controlled/confirmatory work.

```markdown
### CAP-EXP-NNN — question/title

#### Plan — recorded before execution
- Owner, date, design version, status, and run class:
- Prior evidence / parent experiment IDs (or rationale for an initial baseline):
- What we learned from those parents; what carries forward; what remains uncertain:
- Question, hypothesis/null or binary functional gate:
- Control/baseline and treatment; exact changed and fixed factors:
- Registered data/cohort/reference roles and identities:
- Code/environment/config/initialization identities and exact planned command:
- Evaluation protocol, sample size, primary endpoint, guardrails, and decision rule:
- Checkpoint selection, horizon, stopping rules, and uncertainty method as applicable:
- Required code/tests, validity gates, resource budget, and interruption fallback:
- Expected output artifacts, retention/backup class, confounds, and limitations:
- Frozen preregistration reference/hash before compute (required by run class):

#### Attempts — append one record per execution
- Run/attempt ID, launch/finish times, resolved identities, and evidence references:
- Health observations, deviations/amendments, retry/resume parent, and terminal reason:

#### Result and next decision — append after execution
- Evaluation evidence, metrics/counts/uncertainty, and guardrail outcomes:
- Decision: accepted / rejected / inconclusive / invalid / operationally_failed / canceled:
- Interpretation and limits; what changed in our understanding:
- Selected artifact IDs or explicit no-promotion decision:
- Next experiment/diagnostic or stop/defer decision, with rationale:
```

## Active capstone entries

**October7 full-training scope clarification:** Quinton asks why the run was fast compared with
his prior14hour experiments and requests full training sessions. [Scale review](capstone/operations/FULL-TRAINING-SCALE-REVIEW-2026-10-07.md)
compares historical6k–24k/larger-cohort methods with the six-case scratch pilot. R01 is now the
latest actual attempt:48updates,quality stop,retired; its appended record below preserves outcome.
The October6six-case192proposal was an engineering duration comparison, not full model training.
Recommend a full-development baseline readiness packet covering varied qualified data, adequate
thousands-of-updates horizon and reuse of a general trainer. Proposed24k/casecounts/cadences/
selection/stops remain unselected;no new experiment ID/control/job or source use granted here.
Historical results/withdrawals/commands and D-335/R01 evidence remain unchanged. The older
D-335-as-latest and pending-training paragraphs below are dated snapshots.

CAP-EXP-001 through014 have dated records appended later in this notebook. The latest imaging
checkpoint remains [D-335/CAP-EXP-014](capstone/operations/CAP-EXP-014-RESULTS-2026-10-03.md),
complete/consumed. The September18 opening queue wording above is historical; it does not describe
a pending launch. No new experiment ID is reserved by the October6 planning review below.

### October6 — reuse prior methods; preserve historical score boundaries

Quinton requested consulting this notebook before choosing the next training work: prior models
reached about.5Dice, and existing outlined experiments should inform the capstone. He accepted the
192-update planning choices and DUR-01 invented-count policy slice. That module is an engineering
building block; the longer-run executor, qualification and scientific launch remain separate scopes.

The preserved record supports useful prior performance, with essential distinctions:

| Historical result | Recorded evidence | Use in current planning |
|---|---|---|
| EXP-17c lesion.524raw/.528cleaned, provided union ROI | July17 full-eval account; July19 split audit found30/40 positive evaluation cases in training | Withdrawn headline; retain failed split/ROI/confounded scale+duration lessons. |
| EXP-20 autonomous lesion.483raw | Same historically contaminated segmenter/localizer comparison, also withdrawn by the audit | Prior cascade design/error-analysis lesson; no accepted capstone autonomous score. |
| EXP-24 clean lesion.415raw/.412cleaned | July19 development40-positive evaluation after leakage repair; SuPreM-initialized whole-box/24k training, provided union ROI | Stronger prior-method reference; development selection and oracle ROI remain explicit. |
| EXP-24 official-test lesion.474, sensitivity96%, specificity17% | Recorded in EXP-25's July23–25 baseline comparison,151positive/750negative | Historical final-cohort account, not new capstone evidence or a tuning cohort. |
| EXP-25 healthier1:9 cohort lesion.374, sensitivity88%, specificity46% | Rejected on the predeclared90% detection floor; small-case damage | Preserve coverage/subgroup safeguards; more negatives is a controlled tradeoff, not an automatic improvement. |
| EXP-26 auxiliary anatomy | Rejected at24k despite a promising12k comparison | Compare declared endpoints; avoid adopting an early trajectory winner. |

This is a text/control review of existing records, not independent re-scoring or weight validation.
All original claims, later withdrawals, difficult cases and future ideas remain intact below.
The current6-positive/1report-only scratch48-update result is not a reproduction of the old
larger-cohort/pretrained24k result. Its lesionDice.055142 establishes limited engineering behavior;
neither a20%relative gain nor192updates would establish recovered prior-quality/generalization.

Carry forward whole-box physical geometry, qualified caching, adequate exposure, role-separated
evaluation, positive/negative accounting, per-size/phase failures, durable checkpoints and explicit
coverage-versus-foreground tradeoffs. Existing capstone geometry/cache/recovery already implement
several of these lessons. Repeating sampling/background/resolution guesses is not the leading move.

**Recommended next scientific preparation after DUR-01:** prioritize varied multiclass/development/
verified-negative readiness plus a bounded SuPreM provenance/load-audit proposal before committing
to a full longer-run executor. [Plan05 permits audited third-party general pretraining](capstone/imaging/MODEL-LINEAGE-AND-TRAINING.md),
while D-003 prohibits prior-project fine-tuned weights. The current scratch consumer denies every
weight import; a new audited initialization needs a separate versioned scope and qualified source/
license/hash/architecture/load/overlap evidence. No checkpoint bytes are read or imported here.
192 remains an accepted planning choice for the same-cohort duration question, not an order to run
it ahead of that strategic review. Pretraining/cohort/loss/ROI changes must not be silently combined
with a comparison described as duration-only.

Keep the outlined experiments visible, but replan their selected methods under current roles/gates:
EXP-34 training-versus-development gap before assuming capacity, EXP-33 adequate horizon and
EXP-32 EMA after a stable baseline; EXP-29 anisotropic context and EXP-28 retrieval-derived features
are later bounded comparisons. EXP-27 PANORAMA needs source/overlap/purpose qualification;
EXP-30 extra anatomy and EXP-31 external-model error comparison have further supervision/provenance
dependencies. Old official-test curves/selection commands, arbitrary exclusions, old split lists,
cleanup instructions and prior trained checkpoint warm starts do not carry forward. Use development
data for selection, freeze the final test protocol before its separately permitted execution.

No training/source acquisition/array job, checkpoint import, formal run registration, deletion,
Git publication or follow-on dispatch occurs through this notebook update. Exact restart is the
[duration policy handback](capstone/operations/SEGMENTER-DURATION-POLICY-RESULTS-2026-10-06.md),
then review the next data/pretraining preparation scope with Quinton.

**October6 follow-up preparation:** Quinton approved the repository-text/control review and
[SuPreM qualification-packet draft](capstone/operations/SUPREM-INITIALIZATION-QUALIFICATION-PACKET-2026-10-06.md).
The current scratch backbone matches the historical SuPreM-compatible definition; actual source
rights/overlap/tensors remain unqualified. The retained byte inventory supplies a candidate identity,
not import permission. [Review handback](capstone/operations/SUPREM-INITIALIZATION-REVIEW-2026-10-06.md)
proposes an isolated in-memory invented-weight auditor before actual-checkpoint and pretrained
consumer qualification. No new coding/experiment/request is dispatched; historical bytes below
remain unchanged. The accepted192duration question keeps its original scratch initialization.

**SUP-01 implementation handback:** Quinton then approved the four-file invented initializer audit.
[85targeted CPU checks](capstone/operations/SEGMENTER-INITIALIZATION-AUDIT-RESULTS-2026-10-06.md)
verify complete backbone transfer, exact fresh three-class head retention, strict load and failure/
input/RNG isolation within1.45s/0.40GiB. This is an invented component result, with no actual
third-party checkpoint/source acceptance, model forward/update or new experiment. Source-metadata/
actual-file/pretrained-session qualification and varied-data readiness remain separate next scopes.

**October 6 public SuPreM review:** Quinton approved the
[public-source review](capstone/operations/SUPREM-PUBLIC-PROVENANCE-REVIEW-2026-10-06.md) and
[bounded inspection draft](capstone/operations/SUPREM-CHECKPOINT-INSPECTION-PACKET-2026-10-06.md).
The published released-file SHA agrees exactly with the retained candidate record. Weight/code/
dataset terms are recorded separately; candidate-specific pretraining AND upstream model-selection
separation remain unresolved. Actual local identity/serialization/value audit and a versioned
pretrained session are still owed. No checkpoint payload/model/source array/scientific job used.
The proposed invented-file metadata reader can be developed without the drive after its concrete
scope is approved. The 192-update scratch comparison retains its separate initialization/factors.

## Preserved earlier experiment record

Everything below this boundary is the pre-September-18 record, including its future ideas. Preserve
the original text; add new capstone work above and append dated cross-referenced corrections rather
than rewriting earlier hypotheses or results.

<!-- PROWL-HISTORICAL-EXPERIMENT-RECORD: original bytes begin on the next line -->
> # ⛔ READ FIRST — `docs/SUBMISSION-READINESS.md`
>
> **BLOCKER 1: largest-connected-component post-processing is incompatible with tumour-wise
> sensitivity, the metric Johns Hopkins ranks on.** It structurally caps us at one detected tumour
> per patient. This is a design contradiction, not a tuning issue, and it is the **first code change
> of the capstone** — before any training run.
>
> Five blockers total. Nothing is emailed to JHU until they are closed.

# Experiments Log

A running scientific record of every training run and change I have made, written so I can see what worked, what did not, and why. The rule I hold myself to: change one variable at a time, hold the rest constant, and decide the outcome against a bar I set before looking. A clean "this did not help" is a real result and is logged the same as a win.

Two kinds of numbers appear below, and they are not the same thing:
- Training-time validation (logged live to MLflow): measured during the run on whatever val cases the loop sampled. Useful as an in-loop signal but noisy and dependent on which cases were drawn.
- Full evaluation (from `scripts/evaluate.py`): the authoritative score, full-volume sliding-window inference on tumor-positive cases for Dice and tumor-free cases for specificity. When I quote a headline result it is this one.

A caution on the early runs: MLflow did not log the loss's `include_background` flag or the sampling ratio until 2026-07-07, so for runs 1 to 6 those settings are reconstructed from the code history and are marked as such. That gap is exactly why I added richer param logging.

---

## Run ledger (the six real training runs, from MLflow)

| # | MLflow id | date | mode | loss | iters | patch | headline |
|---|-----------|------|------|------|-------|-------|----------|
| 1 | 1f3c1242 | 07-03 | scratch, overfit 2 | dice_ce | 1200 | 96 | pancreas 0.02 to 0.888, lesion stuck 0 |
| 2 | f42bc200 | 07-03 | scratch, overfit 2 | dice_ce | 800 | 96 | pancreas to 0.792, lesion stuck 0 |
| 3 | d3198004 | 07-03 | scratch, overfit 2 | dice_ce | 800 | 96 | lesion learns, to 0.695 |
| 4 | 45e62189 | 07-03/04 | transfer | dice_ce | 6000 | 96 | train-val lesion read 0.000 (artifact) |
| 5 | e72cfdc8 | 07-04 | transfer | dice_focal | 6000 | 96 | "aggressive" model, over-predicts |
| 6 | 4979a5b7 | 07-06 | transfer | dice_focal | 6000 | 96 | "balanced" model, ~identical to 5 |

---

## EXP-01: Can the pipeline learn at all? (overfit gate)

Run: 1f3c1242 (scratch, 2 cases, dice_ce, 1200 iters, lr 2e-4, patch 96).

Purpose: a sanity gate, not a hypothesis. Before trusting anything, force the model to memorize a tiny fixed set. If it cannot drive loss down on 2 cases, the data, loss, or labels are wired wrong.

Result: training loss fell smoothly from 1.874 to 0.538 and pancreas Dice climbed from 0.02 to 0.888. Lesion Dice stayed flat at 0.000 the whole run.

Decision: gate PASSED for the pipeline overall (it clearly learns), but the lesion result exposed a problem to chase. Two causes turned out to be tangled together: the two overfit cases happened to be tumor-free (so lesion Dice was undefined and printed as 0), and the loss was letting the 0.04 percent lesion class be ignored. That sent me into EXP-02.

---

## EXP-02: Make the lesion learnable

Runs: f42bc200 then d3198004 (both scratch, 2 cases, dice_ce, 800 iters).

Hypothesis (H1): the lesion reads 0 because (a) I was overfitting tumor-free cases and (b) background dominates the loss. Drawing overfit cases from tumor-positive scans and excluding background from the loss will let the lesion be learned.

Variable: use `--positive` overfit cases and set `loss.include_background: false` (reconstructed from code history; not logged for this run).

Result: run f42bc200 still showed lesion 0 (pancreas 0.792), an intermediate step. Run d3198004, with the fix in place, showed lesion Dice climb to a max of 0.695 while pancreas reached 0.622.

Decision: ACCEPT. The model can fit both classes when it is actually shown tumors and the loss does not bury the lesion. Key learning that reshaped how I measure everything after this: a lesion Dice of 0 usually means "no tumor in these cases," not "model failed." Locked in `--positive` for overfit and `include_background: false` going forward.

---

## EXP-03: First full transfer run, and the validation measurement artifact

Run: 45e62189 (transfer from SuPreM, dice_ce, 6000 iters, lr 1e-4, patch 96, full 100-case dev subset).

Hypothesis (H1): a real fine-tuning run on the whole dev subset will produce a usable lesion segmenter, and transfer from SuPreM will give a strong starting point.

Result: training-time val lesion Dice read 0.000 the entire run (val pancreas 0.691), which looked like failure. It was not. The val set is about 90 percent tumor-free, so lesion Dice was undefined on almost every case and averaged to near zero. I built `scripts/evaluate.py` to score properly, and on tumor-positive val cases the model scored pancreas Dice 0.716 and lesion Dice 0.174, with specificity only about 8 percent.

Decision: the model does find tumors (real, non-zero lesion Dice), but it badly over-predicts on healthy scans. Two lasting outcomes: fixing the measurement (score positives and negatives separately) mattered as much as fixing the model, and "over-prediction, specificity about 8 percent" became the central problem for everything after.

---

## EXP-04: DiceFocal loss (the "aggressive" model)

Run: e72cfdc8 (transfer, dice_focal, 6000 iters, patch 96, positive-heavy sampling).

Hypothesis (H1): swapping DiceCE for DiceFocal, whose focal term concentrates on hard and rare voxels, will improve the lesion without hurting the pancreas.

Variable: loss `dice_ce` to `dice_focal` (include_background still false).

Result: training-time val reached pancreas 0.703, lesion 0.140. Full evaluation on this checkpoint (the one I later called "aggressive"): pancreas 0.720, lesion Dice 0.169 raw, specificity still about 8 percent. This is the checkpoint the later post-processing levers were first tested on.

Decision: KEEP DiceFocal (lesion learning was at least as good and the focal term is the right tool for the imbalance), but note the over-prediction was not solved. The positive-heavy sampling here was the suspected culprit, which set up EXP-05.

---

## EXP-05: Balanced 1:1 sampling (NULL result)

Run: 4979a5b7 (transfer, dice_focal, 6000 iters, patch 96, balanced 1:1 positive-to-negative sampling).

Hypothesis (H1): the over-prediction is caused by aggressive positive patch sampling; rebalancing to 1:1 will raise specificity without hurting lesion Dice.

Null (H0): the sampling ratio is not the cause and specificity will not move.

Variable: sampling positive-to-negative ratio, aggressive to 1:1. Everything else identical to EXP-04.

Result: essentially identical to the aggressive model on every metric. Pancreas 0.721 versus 0.720, lesion 0.169 versus 0.169, raw specificity 8 percent versus 8 percent, cleaned specificity 42 percent versus 42 percent, threshold sweep nearly the same.

Decision: REJECT H1, accept H0. The sampling ratio is not what drives the over-prediction, so it is ruled out. This is a valuable negative result: it redirected effort away from sampling and toward the loss (EXP-07) and more data. It also reconfirmed that the over-prediction is a property of the model's training, not of the crop mix.

---

## EXP-06: Post-processing levers (evaluation only, no retrain)

Applied to the checkpoints from EXP-04 and EXP-05 with `scripts/evaluate.py`. No training was done, so this is an evaluation experiment.

Hypothesis (H1): false positives on healthy scans can be cut at inference, either by a probability threshold or by an anatomical rule that a lesion must sit near the pancreas.

Result, identical on both the aggressive and balanced models:
- Anatomical constraint (demote lesion components more than 10mm from the predicted pancreas): raw specificity 8 percent (1/12) rose to 42 percent (5/12). Strong lever.
- Probability-threshold sweep: weak. Lesion Dice stayed around 0.16 to 0.18 and specificity held at 8 percent until a 0.90 cutoff, where it reached only 25 percent.
- Cost of the constraint: cleaned lesion Dice on tumor cases dropped from 0.169 to 0.139, the expected sensitivity-for-specificity trade.

Decision: ADOPT the anatomical constraint as the banked specificity lever at evaluation. Interpretation: the false positives are high-confidence and near the organ, so a probability cutoff cannot remove them but a geometric rule can. The fact that it gave the same 8 to 42 lift on both models is why I trust it, it is independent of how the model was trained.

---

## EXP-07: Loss includes background (running 2026-07-07 night)

Run: to fill in (transfer, dice_focal, `include_background: true`, patch 96, 6000 iters). MLflow name `transfer_dice_focal_bg1_posneg_6000i`.

Hypothesis (H1): the over-prediction is driven by the loss excluding background, so the model is never rewarded for calling healthy tissue not-lesion. Including background will raise specificity, and the focal term should keep the rare lesion from being buried.

Null (H0): including background does not lift raw specificity above 8 percent, or it collapses lesion Dice toward 0.

Variable: `loss.include_background` false to true. Single change versus the balanced EXP-05 run.

Accept H1 if: raw specificity climbs above 8 percent while val lesion Dice holds near 0.17.
Reject if: raw specificity stays about 8 percent, or lesion Dice collapses (then use the wired fallbacks, `class_weights [1,1,3]` or lower `lambda_dice`).

Runbook (run this FIRST when I get home; the config already has include_background true):

```bash
source .venv312/bin/activate

# preserve the balanced model before tonight overwrites best.pt
cp outputs/checkpoints/pants-level45/best.pt \
   outputs/checkpoints/pants-level45/balanced_step6000.pt

# tonight's loss experiment (no patch flags, plain 96-cube, only the loss changed)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000

# in the morning: evaluate the new model against the balanced baseline
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 12 --n-neg 12 --sweep --lesion-within-pancreas-mm 10
```

Watch in the first ~15 min: startup prints `device=mps ... cases=100`, the MLflow line `run 'transfer_dice_focal_bg1_posneg_6000i'`, and loss every 25 steps. `last.pt` first writes near step 200. Keep the drive connected and the lid open. Runtime about 5.5 to 6 hours. (A macOS update killed the run at step 5000 overnight; resumed from `last.pt` to finish the last 1000 iters.)

Result (2026-07-08, resumed to 6000, val n=12/12): REJECTED on the primary metric. Raw specificity stayed at 8 percent (1/12), unchanged from every prior model, so including background did not stop the over-prediction at the default decision point. Lesion Dice came in around 0.149 (below the balanced run's 0.169) and cleaned specificity was 33 percent (below the balanced run's 42 percent). On the deployable numbers this is a small step backwards, not forwards.

One real secondary effect worth keeping. Including background recalibrated the model's confidence. The probability-threshold sweep, which was nearly useless before (specificity stuck at 8 percent until 0.90 reached only 25 percent), now climbs to 33 percent at threshold 0.80 and 42 percent at 0.90. So background made the lesion probabilities less overconfident on healthy scans, which finally makes the threshold lever work. But that does not beat what the balanced model already gets from the anatomical constraint (42 percent), and it costs lesion Dice.

Decision: REJECT H1 and revert `include_background` to false. The balanced bg0 config stays the best base (lesion 0.169, cleaned specificity 42 percent). Bigger picture, this is the SECOND training-side lever, after sampling, to leave raw specificity pinned at 8 percent. Two independent knobs ruling it out is strong evidence that the raw over-prediction is a data-scale problem, not something a training tweak fixes at 100 cases. So the plan shifts: stop chasing raw specificity with loss and sampling knobs, bank the post-processing levers (the anatomical constraint reaches 42 percent, and a threshold helps once the model is calibrated), and treat further specificity gains as a more-data problem for the capstone. The next experiment moves to a different axis entirely, patch size and field of view (EXP-08), which tests accuracy rather than specificity.

---

## EXP-08: More pancreas context via a larger patch (queued)

Run: to fill in (transfer, patch 128 via `--patch 128`, `--roi 128` at eval). MLflow name auto-includes `p128`.

Motivation: at patch 96 and 1.5mm spacing the field of view is 14.4cm, which usually holds the tumor and most of the pancreas but can clip the tail, and each inference tile reasons locally.

Hypothesis (H1): increasing the patch from 96 to 128 (field of view 14.4cm to 19.2cm, roughly the whole pancreas) improves accuracy, a gain of at least +0.03 pancreas Dice OR +0.02 lesion Dice over the matched 96 baseline, because the model sees more of the organ at once.

Null (H0): the larger patch produces no meaningful change (within plus or minus 0.02).

Variable: patch size only (`sampling.patch_size` and `inference.sw_roi_size` together). Spacing, model, loss, seed, iterations all held constant. Memory-coupled change to watch: try `num_samples 4`, drop to 2 if MPS runs out of memory.

Measurement: full evaluation at n-pos 20 and n-neg 20 (not 12, to cut noise), re-evaluating the 96 baseline at the same n for a fair comparison.

Accept H1 if: pancreas Dice +0.03 or lesion Dice +0.02 without specificity regressing, then adopt patch 128 for the rest of the project.
Reject if: both within plus or minus 0.02 or worse, then record that more context did not help at this depth and defer the fuller fix (ROI cascade) to capstone.

Note: growing the field of view (patch) is transfer-safe; widening the network (init_filters 16 to 32) is not, it breaks the SuPreM load, so that is capstone-only.

Result (2026-07-09, both models re-scored at matched n=20/20):

| metric | 96 baseline | 128 |
|---|---|---|
| pancreas Dice | 0.740 | 0.747 |
| lesion Dice raw | 0.206 | 0.187 |
| lesion Dice cleaned | 0.197 | 0.175 |
| specificity raw | 10% (2/20) | 25% (5/20) |
| specificity cleaned | 35% (7/20) | 40% (8/20) |

REJECTED on the accuracy hypothesis. Pancreas Dice moved +0.007 (fails the +0.03 bar) and lesion Dice actually went down 0.206 to 0.187 (fails the +0.02 bar, wrong direction). Both accuracy differences are within the noise of 20 cases, so the honest read is that more context did not improve accuracy. Important correction: the apparent lesion "win" seen the night before was an artifact of comparing the 128 (n=20) against the old 96 number on n=12; once the 96 baseline was re-scored on the same 20 cases it came out at 0.206, erasing the gain. This is exactly why the matched baseline is mandatory.

What the larger patch DID do is raise specificity: raw 10 to 25 percent, cleaned 35 to 40 percent. So more context made the base model less trigger-happy on healthy scans, the same over-prediction axis the anatomical constraint works on, at a small cost to lesion Dice. That is a sensitivity-for-specificity trade, not an accuracy gain.

Decision: REJECT H1. Do not adopt 128 as the base for the accuracy line, the plain 96 bg0 balanced model has the best lesion Dice so far (0.206) and stays the accuracy baseline; 128 is noted as a specificity lever if that becomes the priority. The bigger takeaway: context (EXP-08) is now ruled out for accuracy, which isolates the one untested lever, resolution, and elevates EXP-10 (crop to pancreas + finer 1.0mm) as the experiment most likely to move lesion Dice. EXP-10's baseline to beat is the 96 model's lesion Dice of 0.206.

Runbook: see the commands block below.

```bash
source .venv312/bin/activate
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/ctx_baseline_backup.pt
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --patch 128 --num-samples 4 \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000 \
  --run-name transfer_p128_ctx
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 --roi 128
```

---

## EXP-09: Transfer versus from-scratch (the pretraining ablation) [Week 3, queued]

Run: to fill in (`--scratch`, whole-box recipe, 6000 iters). MLflow name `scratch_wholebox_p128_1p5`.

Design update (2026-07-12): the original stub compared scratch-vs-transfer at the old patch-96 recipe (baseline lesion 0.206). That is superseded. The project's best base is now the EXP-12 whole-box recipe (transfer lesion 0.263, pancreas 0.807, spec 55%), so the fair and presentation-relevant version of this ablation runs from-scratch on the SAME whole-box recipe and compares against EXP-12. This makes the transfer arm a run we already have (EXP-12) and keeps the comparison on the model we actually present. The single toggled flag is still `--scratch` vs `--transfer`.

Question it answers: does the SuPreM pretraining actually earn its place, or would a from-scratch SegResNet on 95 cases do just as well? Every prior scratch run was only the 2-case overfit gate, so the transfer benefit has never been measured at full scale. This is the number that defends the core model decision at the Week 3 check-in.

Hypothesis (H1): SuPreM pretraining materially helps, so from-scratch scores clearly lower pancreas and/or lesion Dice than the EXP-12 transfer model.
Null (H0): from-scratch matches transfer within noise, meaning the pretraining is not doing much at 95 cases (which would itself be a real, report-worthy finding, and consistent with the data-scale story).

Variable: `--scratch` instead of `--transfer`. Everything else identical to EXP-12: same `dev_subset_clean` split, whole-box, crop-native 16, patch 128, spacing 1.5, bg0 DiceFocal, seed 42, 6000 iters, val on the same 20 tumor-positive cases.

Confound to state honestly (do not skip): the two arms are not a pure initialization-only test. Transfer uses `lr_transfer` 1e-4 with a 3-epoch encoder-freeze warm-up; scratch uses `lr_scratch` 2e-4 with no freeze (train.py applies the freeze only when pretrained). That is the intended, each-regime-tuned way to run them, so the honest framing of the result is "the SuPreM transfer recipe vs a from-scratch recipe," the practical question. If a strictly initialization-only isolation is wanted later, re-run scratch at matched LR with no freeze on the transfer side.

Measurement: full eval at n-pos 20 / n-neg 20 on the same val cases as EXP-12, so the transfer numbers are EXP-12's (0.807 / 0.263 / 55%). Report pancreas Dice, lesion Dice (raw + cleaned), and specificity.

Accept H1 if: transfer beats scratch by a clear margin (lesion Dice gap >= 0.03 or pancreas Dice gap >= 0.03). Reject (accept H0) if they land within noise (both within +/- 0.02), and record that pretraining does not move the needle at this scale.

Runbook (fire-and-forget overnight; no dependency on other runs; back up whatever best.pt currently exists first):

```bash
source .venv312/bin/activate
# preserve the current best.pt before this run overwrites it
cp outputs/checkpoints/pants-level45/best.pt \
   outputs/checkpoints/pants-level45/prev_best_backup_$(date +%Y%m%d).pt 2>/dev/null || true

# from-scratch arm, identical to EXP-12 except --scratch
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --scratch \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name scratch_wholebox_p128_1p5
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/scratch_wholebox_best.pt

# morning: eval on the SAME 20/20 val cases and recipe as EXP-12, compare to 0.807 / 0.263 / 55%
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/scratch_wholebox_best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Note on the transfer arm: EXP-12's whole-box checkpoint is the transfer side of this comparison. If that checkpoint was overwritten by the EXP-13/14 20-case runs (see the EXP-15 provenance note), re-run the EXP-12 command (swap `--scratch` back to `--transfer`, run-name `transfer_wholebox_p128_1p5`) so both arms are freshly matched under the current code, then compare the two directly.

Result (2026-07-14, both best-val checkpoints, eval n=20/20; transfer = regenerated EXP-12 step 2000, scratch step 4000):

| metric | transfer (SuPreM) | scratch |
|---|---|---|
| pancreas Dice | 0.778 | 0.650 |
| lesion Dice raw | 0.257 | 0.120 |
| lesion Dice cleaned | 0.263 | 0.137 |
| specificity raw | 50% (10/20) | 0% (0/20) |
| specificity cleaned | 55% (11/20) | 5% (1/20) |

Decision: ACCEPT H1 DECISIVELY. Transfer beats scratch on every axis by margins far past the 0.03 bar: lesion +0.137 raw, pancreas +0.128, specificity +50 points. From-scratch on 95 cases barely learns the pancreas (0.650) and over-predicts on every single healthy scan (0% specificity), while the SuPreM-initialized model reaches a usable 0.778 / 0.263 / 55%. So the SuPreM pretraining is not a marginal boost, it is what makes the model work at this data scale, which is the number that defends the model choice at the Week 3 check-in. Confound acknowledged: the two arms also differ in LR (1e-4 vs 2e-4) and the encoder-freeze warm-up (transfer only), so this is the practical "transfer recipe vs scratch recipe" comparison, not a pure initialization-only isolation. But the gap is far too large for the LR/freeze differences to account for it. The transfer arm here is also the regenerated EXP-12 (see EXP-12 regeneration note), which reproduced the lost original within noise.

---

## EXP-10: Oracle pancreas ROI at high resolution (the cascade proof-of-concept)

Motivation: the "what the model sees" analysis made it concrete that the model reads a 1.5mm-blurred, low-contrast grid where a tumor is only a handful of voxels whose value barely differs from the pancreas around it. This experiment tests the cascade idea directly: crop each scan to the pancreas and resample it finer, so the model works on a high-resolution view of only the organ. For the course we use the ground-truth Johns Hopkins pancreas mask as the provided outline (the oracle ROI); at capstone a stage-1 model predicts that region and the pipeline is fully automated.

Hypothesis (H1): cropping to the pancreas and training at 1.0mm instead of 1.5mm substantially improves lesion Dice over the whole-scan baseline, because the tumor is now many more voxels and the model is not diluted by irrelevant abdomen.

Null (H0): no meaningful lesion Dice improvement, meaning the ceiling is set by something other than resolution and focus (most likely data volume).

What changes (a bundled package, on purpose): (1) crop to the ground-truth pancreas plus a 20mm margin, and (2) target spacing 1.5mm to 1.0mm. It is intentionally two changes at once because the goal is to prove the concept and measure its ceiling. If it wins, EXP-10a decomposes it by cropping only, still at 1.5mm, to separate how much came from focus versus resolution.

Held constant: same dev_subset and splits, same SuPreM model and bg0 loss, seed 42, 6000 iters, 96 patch, same validation protocol.

Honesty note (important): this is an ORACLE result. It assumes the pancreas region is handed to the model, by the JHU mask now, by a human outline or a stage-1 model later. It must be reported as an upper bound or a semi-automated number, exactly like raw-versus-cleaned, never as the fully autonomous system. That framing is also the real deployed design, where a radiologist provides the outline.

Measurement: full evaluation on the cropped ROIs at n-pos 20 and n-neg 20, passing the same `--spacing` and `--crop-pancreas` at eval so preprocessing matches training. Compare lesion and pancreas Dice against the 96 baseline (`balanced_step6000.pt`) and the 128 result.

Accept H1 if: lesion Dice clears a clear margin over baseline (target +0.05, since this is the big-lever bet). Then adopt the cascade as the capstone direction and report it as the headline "with a provided ROI" number. Reject if lesion Dice is within noise of baseline.

Runbook (de-risk with a 5-minute smoke test first, then the full run):

Sampler note (2026-07-09): the smoke test crashed twice with `No sampling location available` (once at patch 96, once at 64), which ruled out patch size. The real cause is that on a case whose cropped pancreas comes out effectively empty at fine spacing, the pos/neg sampler has no valid location and throws. Fix: when `crop_to_pancreas` is set, training uses `RandSpatialCropSamplesd` (plain random crops) instead of the pos/neg sampler. Inside a cropped pancreas the organ and tumor fill most of the volume so random crops still hit the tumor often, and that sampler cannot raise this error. Runbook uses `--patch 64 --crop-pancreas 30`.

Optimizer/encoder fix (2026-07-09): resuming crashed with an optimizer param-group size mismatch. Root cause: `build_optimizer` only included currently-trainable params, so its shape changed when the encoder unfroze, and as a side effect the encoder was never actually being trained after the warm-up (it never entered the optimizer). Fixed by putting all params in the optimizer and freezing via requires_grad only, plus making checkpoint loading tolerate an optimizer mismatch instead of crashing. CONFOUND to note: this run therefore trains the encoder after step 750, while the 96 baseline (lesion 0.206) was trained under the old frozen-encoder behavior. So a big EXP-10 win is partly attributable to the encoder finally training, not purely resolution. If EXP-10 wins, re-run the 96 baseline with the fixed code for a strictly matched comparison before crediting resolution.

```bash
source .venv312/bin/activate

# 0. SMOKE TEST (~5 min): confirm the pancreas-crop + finer-spacing pipeline runs end to end
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --patch 64 --spacing 1.0 --crop-pancreas 30 --max-iters 50 --no-mlflow --ckpt-every 50

# 1. FULL RUN (only after the smoke test trains cleanly)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --patch 64 --spacing 1.0 --crop-pancreas 30 --ckpt-every 50 \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000 \
  --run-name transfer_roi_pancreas_1mm

# 2. EVAL (must match training preprocessing: same patch/roi + spacing + crop)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --roi 64 --spacing 1.0 --crop-pancreas 30
```

Both prior models are already backed up (`balanced_step6000.pt`, `p128_ctx_step6000.pt`), so this run may overwrite best.pt. Runtime is roughly 4 to 5 hours (small cropped volumes, 64 patch), a comfortable overnight run.

Result (2026-07-09, oracle-ROI `best.pt`, n=20/20, cropped-ROI eval): pancreas Dice 0.726, lesion Dice raw 0.234, cleaned 0.214. Versus the 96 whole-scan baseline (lesion raw 0.206), lesion Dice improved by +0.028, the highest lesion Dice achieved so far. Pancreas came in slightly lower (0.726 vs 0.740), but pancreas was not the target and is scored on the crop here.

Verdict: PROMISING, partial. Lesion Dice improved by a real but modest margin (+0.028), short of the ambitious +0.05 bar but the best result yet, and it supports the cascade thesis directionally. Two honesty caveats: (1) this is an ORACLE result using the ground-truth pancreas mask as the ROI, so it is an upper bound / "with a provided ROI" number, not the autonomous system; (2) this run also got the encoder-training bug fix that the baseline lacked, so part of the +0.028 may be the encoder finally training rather than resolution.

Decision: adopt the ROI/cascade as the capstone direction (best lesion Dice yet, and the mechanism your own reasoning pointed to). The modest size of the gain is further evidence that the dominant remaining lever is data scale, not preprocessing. Next steps: (a) EXP-10b, re-run the 96 baseline with the fixed code to isolate resolution from the encoder fix (if the fixed baseline stays ~0.21, resolution is the driver; if it rises to ~0.23, the encoder fix was); (b) scale up the tumor cases per the Week 3-5 plan, which is the likeliest path to a materially higher number.

---

## EXP-11: Clarity package (crop native, then resample fine) [Track A, tonight]

Motivation: EXP-10 cropped the pancreas AFTER resampling the whole scan to 1.0mm, so detail was averaged away before the crop, and finer spacing on the whole scan is unaffordable. This crops the pancreas in NATIVE resolution first, then resamples only that small ROI to a fine 0.7mm grid. So the model gets the sharpest honest view of the organ, and fine spacing is now cheap because it only touches the ROI.

Hypothesis (H1): cropping native then resampling to 0.7mm beats the EXP-10 oracle ROI (lesion 0.234), because the tumor is both sharper (less pre-crop averaging) and larger in voxels (0.7 vs 1.0mm).

Null (H0): no meaningful lesion Dice gain over 0.234.

Variable (bundled clarity package): crop order (native, before resample) plus spacing (1.0 to 0.7mm). Both serve clarity; if it wins we can decompose later. Transfer-safe: still 1 channel, SuPreM intact. Same 64 patch, bg0 loss, encoder-training fix (same as EXP-10, so this is a clean comparison to 0.234).

Accept H1 if lesion Dice clears 0.234 by a real margin at n=20/20. Reject if within noise.

Runbook (smoke-test first; back up the EXP-10 0.234 model so it is not lost):

```bash
source .venv312/bin/activate
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/roi_1mm_step6000.pt

# smoke test (~5 min)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --crop-native 24 --spacing 0.7 --patch 64 --max-iters 50 --no-mlflow --ckpt-every 50

# full run
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --crop-native 24 --spacing 0.7 --patch 64 --ckpt-every 50 \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000 \
  --run-name transfer_cropnative_0p7

# eval (match: same crop-native, spacing, roi)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 24 --spacing 0.7 --roi 64
```

Result: INCONCLUSIVE, and it exposed an eval bug. Training-time validation ended at pancreas 0.661 / lesion 0.100 (n=12), already below the 0.72 / 0.206 anchors. The full evaluate.py run printed pancreas 0.217 / lesion 0.024, which looked catastrophic, but that was a measurement bug: evaluate.py defined `--crop-native` but never applied it to the config, so the eval ran the whole body through a model trained only on tiny cropped-pancreas ROIs (total train/eval mismatch). The pancreas collapse to 0.217 was the tell (a resolution change cannot move pancreas from 0.72 to 0.22). Bug fixed on 2026-07-09 (evaluate.py now applies `--crop-native`). The trustworthy signal is the in-loop 0.661 / 0.100.

Decision: REJECT the bundled clarity package as run. Even the trustworthy number was below baseline, because four things changed at once and two starved the model: a 64-voxel patch at 0.7mm is only a 45mm field of view (a thin slab of a 150-200mm organ), and the crop path uses random (not tumor-biased) sub-patches, so the rare lesion was seldom centered. Not a verdict on resolution; a verdict on tiny-FOV plus random sampling. This directly motivates EXP-12 (feed the WHOLE box instead of random sub-patches). Baseline to beat stays EXP-10 lesion 0.234.

Track A queue after this: per-ROI intensity normalization; test-time augmentation at eval (free, no retrain); scale up tumor data. Data-integrity: `scripts/audit_masks.py` screens for empty/tiny pancreas masks (run once, optionally `--write-clean`).

---

## EXP-12: Whole-box ROI (feed the entire pancreas box, no sub-patching) [Track A, tonight]

Motivation: EXP-11 confirmed that random sub-patches inside a cropped ROI starve the model (thin field of view, tumor rarely centered). Quinn's idea: draw the axis-aligned bounding box of the pancreas plus a buffer (which is exactly what CropForegroundd already computes), then feed the ENTIRE box to the model as one fixed cube instead of taking random crops out of it. The model then sees the whole organ plus surrounding context every step. This also simulates the product's "radiologist provides the ROI" mode (an oracle ROI, honestly labelled).

Hypothesis (H1): feeding the whole pancreas box as one cube beats EXP-10 (lesion 0.234), because the model always has the whole organ and its tumor in view, removing the FOV starvation and the sampling lottery that hurt EXP-11.

Null (H0): no meaningful lesion Dice gain over 0.234.

Variable: input construction (whole box fit to one cube via ResizeWithPadOrCropd) versus random sub-patch. Held constant vs a fair anchor: SuPreM transfer, bg0 loss, encoder-training fix. Spacing 1.5mm with a 128 cube spans 192mm, so almost no case gets center-cropped (the whole-organ guarantee holds). Transfer-safe: 1 channel, SuPreM intact.

Accept H1 if lesion Dice clears 0.234 by a real margin at n=20/20. Reject if within noise. Secondary read: does pancreas Dice rise above ~0.72 now that the whole organ is always in view?

Runbook (Codex-audited first, then smoke-test, then full run; uses the clean split that excludes the 5 empty-pancreas cases):

```bash
source .venv312/bin/activate
# back up the EXP-10 0.234 model so it is never lost
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/roi_1mm_step6000.pt 2>/dev/null || true

# smoke test (~3-5 min): proves the whole-box path builds, trains, and checkpoints
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 50 --no-mlflow --ckpt-every 50

# full overnight run
# val-limit 20 (not 12): select the best checkpoint on the SAME 20 tumor-positive cases used at
# final eval, per Codex design review — cuts checkpoint-selection noise and lines the two sets up.
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_p128_1p5

# eval (MUST match training: same crop-native, whole-box, roi, spacing)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result (run `transfer_wholebox_p128_1p5`, 6000 iters, best.pt = best-val checkpoint; note this run
executed in `.venv`, not `.venv312`, so it likely did NOT log to MLflow — re-log the numbers):

In-loop val (n=20 tumor-positive): best val lesion-Dice 0.263 (final step val pancreas 0.812 / lesion 0.220).

Full eval, val split, n=20 positive / 20 free:
- pancreas Dice        : 0.807   (vs ~0.72 anchor — whole-organ context)
- lesion Dice (raw)    : 0.263   (BEATS the 0.234 bar — best result to date)
- lesion Dice (cleaned): 0.252
- specificity (raw)    : 11/20 = 55%   (vs 8% on every prior model)
- specificity (cleaned): 11/20 = 55%   (constraint now a near no-op)
- threshold sweep: 0.30 -> les 0.271 / spec 50%; 0.50 -> 0.263 / 55%; 0.70 -> 0.253 / 60%;
  0.90 -> 0.234 / 70%. Monotonic, usable CADe operating dial.

Decision: ACCEPT. First result to beat 0.234, and it wins on all three axes at once (lesion +0.029,
pancreas +0.09, raw specificity +47pp). The mechanism is clean: raw == cleaned specificity and
near-flat cleaned lesion Dice mean the model now stays quiet on healthy scans by itself, so the
anatomical constraint (our old strong lever) has almost nothing left to remove. This is the new
Track-A best base.

Honesty caveats to carry into the writeup: (1) ORACLE ROI ("radiologist provides the box"), not
autonomous. (2) The specificity leap is partly STRUCTURAL: looking only inside the pancreas box
leaves far less tissue to false-alarm on, so 8%->55% is not like-for-like against the old whole-scan
numbers; frame it as "with a provided ROI." (3) Composite change vs 0.234 (spacing, crop order, FOV,
sampling all moved), n=20 (each free case = 5 specificity points), so this is evidence that "whole-box
at feasible resolution" works, not proof any single knob caused it. (4) Shares the encoder-training
fix, same as EXP-10, so that is controlled in this comparison.

Follow-ups: re-log to MLflow (graded deliverable); pick a default CADe operating threshold from the
sweep; the remaining big lever is data scale (capstone). Autonomous version needs a pancreas detector
in front of this box stage (the cascade).

Regeneration (2026-07-14): the original EXP-12 checkpoint was confirmed lost (see the Checkpoint &
logging discipline note), so I re-ran the identical command (seed 42, dev_subset_clean, whole-box,
6000 iters). The clean, uninterrupted re-run REPRODUCED the result within noise: pancreas 0.778 (vs
0.807), lesion 0.257 raw / 0.263 cleaned (vs 0.263 raw), specificity 50% raw / 55% cleaned (vs 55%).
The 55% specificity reproducing is the important part: it was not a lucky draw. Two process lessons
came out of the recovery: (1) an interrupted-then-`--resume`d run produced a badly non-reproducing
checkpoint (lesion 0.096, pancreas 0.723) because resume resets the best-val tracker to -1 and then
overwrote the good shared best.pt with a worse late checkpoint. So keeper runs must run uninterrupted,
and resume needs hardening (restore best_val from the checkpoint; never overwrite a better best.pt with
a worse one). (2) A separately interrupted run's best.pt landed at step 3000 with only 15% specificity,
confirming specificity is the noisier, run-to-run-variable metric (it is not what best.pt selects on),
while lesion Dice reproduces tightly across all three checkpoints (0.236 / 0.257 / 0.263). The per-run
archive is what made recovery possible: every attempt's best.pt survived in its own immutable folder.
Reported EXP-12 numbers going forward use the clean regenerated checkpoint (archive
`transfer_wholebox_p128_1p5__20260713_221119`, pinned as `wholebox_p128_1p5_GOOD.pt`).

---

## EXP-13: Clarity curriculum (train on sharper scans) [Week 3, professor's idea]

Motivation: professor's suggestion. Curriculum learning idea. Weight the training set toward the
CLEAREST scans so the model builds good feature detectors on sharp, easy-to-read images before it
has to cope with the blurry ones. "Clearest" is defined by spatial resolution: native slice thickness
first, then in-plane pixel spacing (thinner and finer = sharper).

Data check (train pool): a genuinely sharp cohort exists. The "15 Sites" collection is sub-millimeter
(0.80mm slices, 0.76mm in-plane) with 163 tumor cases, and there is a clean gradient down to 5.0mm.
Wrinkle 1: clarity and tumor-richness are anti-correlated across cohorts (the sharp cohort is
tumor-poorer than the blurry, tumor-rich "1 Site" group), so we MUST hold tumor count constant or we
would be measuring tumor availability, not clarity. Wrinkle 2: the sharpest scans skew non-contrast,
which is actually harder for tumor visibility, so "sharp geometry" and "good tumor conspicuity" are
not the same axis (we chose the resolution axis deliberately).

Design (single variable = training-set clarity; hold N, tumor count, eval set, recipe, seed constant):
`scripts/make_clarity_splits.py --clear-slice-max 0.8` builds two disjoint 20-case training sets, each
10 tumor / 10 healthy:
- `clarity20` (treatment): 12 from the sharpest scans (<=0.8mm) + 8 spread across the rest. Median
  native slice 0.80mm.
- `repr20` (baseline): 20 drawn representatively across the whole clarity range. Median slice 1.50mm.
Both trained with the EXP-12 whole-box recipe (crop-native 16, whole-box, 128 @1.5mm, SuPreM transfer,
bg0), 4000 iters, best.pt by val lesion Dice on the same 20 tumor-positive val cases. Evaluated on the
identical val set (20 pos / 20 free).

Hypothesis (H1): clarity20 beats repr20 by a real margin (lesion Dice +0.02 OR pancreas +0.03) at
n=20 eval, because sharper training images give cleaner patterns to learn.
Null (H0): no meaningful difference, or clarity-weighting hurts (domain gap: the sharp cohort differs
from the representative val set in more than resolution).

Predicted confounds to write up honestly (this is most of the scientific value):
1. Our pipeline resamples every scan to 1.5mm, which NORMALIZES resolution before the model sees it,
   so it may mute the pure-clarity effect. A null result could mean "clarity does not help" OR "our
   resampling already erased the clarity signal." A finer-spacing follow-up would separate these.
2. The sharp cohort differs from the pool in more than sharpness (specific multi-site collection,
   mostly non-contrast), so any effect is clarity plus domain, not clarity alone.
3. n=20 train and n=20 eval: very noisy (each free eval case = 5 specificity points). This is a
   directional pilot, not proof.
4. Both arms share the eval set, so the comparison is a fair relative A/B even though absolute numbers
   at 20 training cases will be well below the 95-case EXP-12 base.

Runbook:

```bash
source .venv312/bin/activate
python scripts/make_clarity_splits.py --clear-slice-max 0.8   # writes clarity20.txt + repr20.txt

# Arm B: clarity-weighted
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split clarity20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name clarity20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/clarity20_best.pt

# Arm A: representative baseline
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split repr20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name repr20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/repr20_best.pt

# eval both on the identical val set + recipe
for M in clarity20 repr20; do
  echo "===== $M ====="
  PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
    --ckpt outputs/checkpoints/pants-level45/${M}_best.pt \
    --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
    --crop-native 16 --whole-box --roi 128 --spacing 1.5
done
```

Result (eval n=20 pos / 20 free, both best.pt at step 2000; models early-stopped by val since 20 cases overfit fast):

| metric | clarity20 (sharp, median 0.80mm) | repr20 (representative, 1.50mm) |
|---|---|---|
| pancreas Dice | 0.780 | 0.782 |
| lesion Dice raw | 0.204 | 0.189 |
| lesion Dice cleaned | 0.208 | 0.182 |
| specificity raw | 85% (17/20) | 50% (10/20) |
| specificity cleaned | 90% (18/20) | 60% (12/20) |

Sweep: clarity holds ~0.20 lesion Dice at 80-95% specificity (0.70 thr -> 0.196 / 95%); repr must reach 0.90 thr to hit 85% and sits at 55% at 0.50 thr.

Decision: SOFT NULL on the pre-registered accuracy bar, STRONG (but confounded) surprise on specificity. Lesion Dice is +0.015 raw / +0.026 cleaned and pancreas is flat, so it does not cleanly clear the +0.02 accuracy bar. That soft null is consistent with the predicted confound #1: resampling to 1.5mm normalizes native resolution away before the model sees it, so "sharper = more accurate" barely shows up in Dice. The unregistered surprise is specificity: the clarity-weighted model is far less trigger-happy on healthy scans (raw 50->85, cleaned 60->90), a Pareto win here since Dice is tied-or-better too. Treat this as a strong hypothesis-generating result, NOT a confirmed causal claim of sharpness, because (confound #2) the sharp cohort also differs in site and contrast phase (mostly non-contrast), so the gain could be domain/appearance rather than resolution; and n=20 (each free case = 5 pts) means the 7-case gap is directionally credible but wide. Mechanistic read: training on the sharp, mostly non-contrast cohort may give the model a cleaner sense of "normal pancreas," so it hallucinates fewer tumors on healthy scans. Follow-up to isolate the cause: repeat controlling for contrast phase, or at larger n. Note both arms are 20-case models, so absolute numbers sit below the 95-case whole-box base (lesion 0.263); the value is the relative clarity-vs-representative contrast, which is real and large on specificity.

---

## EXP-14: Contrast phase, isolated from resolution [Week 3, follow-up to EXP-13]

Motivation: EXP-13 raised specificity but its sharp cohort was also mostly non-contrast, so clarity and contrast phase were confounded. This isolates contrast phase to answer the question EXP-13 could not: is contrast phase the real driver of the specificity effect?

Design: `scripts/make_contrast_splits.py` builds two disjoint 20-case sets (10 tumor / 10 healthy), both drawn from the slice 1.0-2.0mm + in-plane 0.7-1.1mm band, so both land at median slice ~1.2mm and in-plane 0.80mm. Only contrast phase differs: `nc20` = non-contrast, `pv20` = portal-venous. Both trained with the whole-box recipe (crop-native 16, whole-box, 128 @1.5mm, SuPreM transfer, bg0), 4000 iters, best.pt by val lesion on the same 20 tumor-positive val cases, evaluated on the identical val set (20 pos / 20 free).

Hypothesis (H1, primary and clean = specificity): at matched resolution, non-contrast trains a MORE specific model than portal-venous, because non-contrast tumors are subtle so the model learns to be cautious about calling them. Accept if nc20 specificity beats pv20 by >= 3 healthy cases (about 15 points) at n=20.
Secondary (confounded = sensitivity): portal-venous >= non-contrast on lesion Dice, since tumors are more conspicuous with contrast. Report but do not over-claim (see limitation).

Interpretation either way: if nc >> pv on specificity, contrast phase IS the driver behind the EXP-13 surprise (confirms the reinterpretation). If nc ~ pv, contrast is ruled out and EXP-13's specificity gain came from something else (residual resolution, or site/domain). Both outcomes are informative.

Known limitation, stated up front: tumor SIZE could not be fully matched. At this resolution non-contrast has only ~11 tumors, and they are smaller, so even after a common 1000-20000 mm3 size band the venous tumors stay ~1.9x larger (median 8359 vs 4473). Therefore the SPECIFICITY read (healthy scans, no tumor size involved) is the clean primary result; the lesion-Dice read carries a residual size advantage for portal-venous and cannot separate contrast conspicuity from tumor size at n=10. That non-contrast tumors are both fewer and smaller at matched resolution is itself a finding. n=20 eval (each healthy case = 5 points).

Split facts (seed 42, disjoint): nc20 median slice 1.25mm / in-plane 0.80mm / lesion 4473 mm3; pv20 1.12mm / 0.81mm / 8359 mm3.

Runbook:

```bash
source .venv312/bin/activate
python scripts/make_contrast_splits.py            # writes nc20.txt + pv20.txt

# Arm NC: non-contrast
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split nc20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name nc20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/nc20_best.pt

# Arm PV: portal-venous
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split pv20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name pv20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/pv20_best.pt

# eval both on the identical val set + recipe
for M in nc20 pv20; do
  echo "===== $M ====="
  PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
    --ckpt outputs/checkpoints/pants-level45/${M}_best.pt \
    --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
    --crop-native 16 --whole-box --roi 128 --spacing 1.5
done
```

Result (eval n=20 pos / 20 free; nc20 best.pt step 2000, pv20 best.pt step 1000, both early-stopped by val):

| metric | nc20 (non-contrast) | pv20 (portal-venous) |
|---|---|---|
| pancreas Dice | 0.791 | 0.704 |
| lesion Dice raw | 0.116 | 0.124 |
| lesion Dice cleaned | 0.116 | 0.138 |
| specificity raw | 90% (18/20) | 10% (2/20) |
| specificity cleaned | 95% (19/20) | 10% (2/20) |

Sweep: nc20 holds 90-95% specificity at every threshold (already saturated); pv20 climbs 10% -> 50% only by threshold 0.90.

Decision: ACCEPT H1 (specificity), DECISIVELY. At matched resolution, non-contrast trained a far more specific model than portal-venous: raw specificity 90% vs 10%, a 16-case gap at n=20, cleaned 95% vs 10%. This confirms the reinterpretation of EXP-13: contrast phase, NOT resolution/clarity, is the driver of the specificity effect (EXP-13's clarity cohort was mostly non-contrast). Mechanism: non-contrast tumors are subtle, so the model learns caution and rarely false-alarms on a healthy pancreas; portal-venous tumors are conspicuous, so the model learns "bright pancreatic region = tumor" and over-fires on healthy scans (18/20 flagged). Secondary, size-confounded: portal-venous edges non-contrast on lesion Dice (raw 0.124 vs 0.116, cleaned 0.138 vs 0.116), directionally consistent with contrast raising sensitivity, but the gap is small and pv tumors were ~1.9x larger, so do not over-claim. Pancreas gap (0.791 vs 0.704) is partly a training-time artifact (pv early-stopped at step 1000 vs nc 2000). Caveats: n=20 (but 90 vs 10 is far outside noise); contrast phase is not randomized, it travels with acquisition protocol and scan indication, so it bundles those. Product implication: contrast phase is a real operating-point dial, train toward non-contrast for specificity (screening) or portal-venous for sensitivity (catch-everything); the phase-mixed dev subset (EXP-12, 55% spec) sits between the two extremes. This is the strongest single explanatory result of the project so far and the headline for the Week 3 check-in.

---

## EXP-15: Test-time augmentation at evaluation (free lever, no retrain) [Week 3, queued]

Motivation: TTA is the cheapest lever left. Averaging the model's predictions over label-preserving flips of the input usually steadies segmentation output at no training cost. It is a pure evaluation change on an existing checkpoint, so it either helps for free or it does not, and either way it is a clean thing to report.

What it does (now wired in code): `evaluate.py --tta` runs sliding-window inference on all 8 flip combinations of the three spatial axes, un-flips each prediction back to the original frame, and averages the softmax probabilities before argmax/threshold. The threshold sweep and the anatomical constraint run on the averaged probabilities exactly as before. Implemented in `src/inference/sliding_window.py::predict_probs_tta`; the non-TTA path is untouched.

Target checkpoint: the EXP-12 whole-box best (lesion 0.263 / pancreas 0.807 / spec 55%). This is a single-variable test: same checkpoint, same 20/20 val cases, same recipe, TTA off (EXP-12 numbers) vs TTA on.

PROVENANCE CAVEAT (RESOLVED 2026-07-12): the EXP-12 whole-box checkpoint is confirmed GONE from disk. A second Claude session searched the whole repo tree: the four named backups are other runs (aggressive/balanced = sampling, `p128_ctx` = EXP-08, `roi_1mm` = EXP-10), there is no Jul-10 file anywhere, and the current `best.pt`/`last.pt` are the EXP-14 pv20 model. It was never an MLflow artifact either (EXP-12 ran in `.venv` without mlflow; `log_run_to_mlflow.py` logs only params/metrics, not weights). Only a Time Machine snapshot from before Jul 11 13:18 could recover the exact bytes. Plan: regenerate by re-running the EXP-12 command (`--transfer`, whole-box, run-name `transfer_wholebox_p128_1p5`); seed 42 + unchanged training code reproduces a statistically equivalent model (within n=20 noise of 0.807/0.263/55%), which is all TTA needs. This folds into the EXP-09 night (the transfer arm IS the regenerated EXP-12). Going forward this cannot recur: `train.py` now auto-archives every keeper into `outputs/checkpoints/pants-level45/runs/<run_name>__<timestamp>/` with a `run_info.txt`, plus a `run_ledger.csv` row, independent of MLflow.

Hypothesis (H1): 8-view flip TTA improves the deployable numbers on the EXP-12 model, lesion Dice +>=0.01 OR specificity +>=1 healthy case, without regressing the other.
Null (H0): TTA changes nothing beyond noise (whole-box input is already centered and low-variance, so flips add little).

Accept if: either lesion Dice or specificity improves with no meaningful regression on the other, then adopt TTA as a default at eval (it is free). Reject if flat or if it trades one metric down for the other (then it is not a free win and we leave it off).

Cost: 8x forward passes at eval only. In whole-box mode each case is a single 128-cube window, so 40 cases x 8 views is a few minutes, not an overnight run.

Runbook:

```bash
source .venv312/bin/activate
# EXP-12 baseline (TTA off) for the matched comparison, if not already recorded at n=20/20:
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/<exp12_wholebox>.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5

# same checkpoint + recipe, TTA on (the only change)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/<exp12_wholebox>.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5 --tta
```

Result (2026-07-14, EXP-12 GOOD ckpt `wholebox_p128_1p5_GOOD.pt`, eval n=20/20):

| metric | no TTA (EXP-12) | 8-view flip TTA |
|---|---|---|
| pancreas Dice | 0.778 | 0.756 |
| lesion Dice raw | 0.257 | 0.234 |
| lesion Dice cleaned | 0.263 | 0.238 |
| specificity raw | 50% (10/20) | 75% (15/20) |
| specificity cleaned | 55% (11/20) | 80% (16/20) |

TTA sweep: thr 0.40 -> lesion 0.239 / spec 75%; 0.60 -> 0.220 / 85%; 0.80 -> 0.161 / 90%; 0.90 -> 0.140 / 90%.

Decision: REJECT as an always-on default, per the pre-registered bar (it did not improve one metric with no meaningful regression on the other). TTA raised specificity sharply (+25 points, 55% -> 80% cleaned) but cost lesion Dice (0.263 -> 0.238) and a little pancreas Dice (0.778 -> 0.756), so it is a sensitivity-for-specificity TRADE, not a free win. KEEP it in the toolbox as a genuine specificity lever, though: it reaches an 80-90% specificity regime the non-TTA threshold sweep could NOT (that sweep capped at 55% even at threshold 0.90). Mechanism: averaging predictions over the 8 flips softens the lesion probabilities and suppresses the high-confidence near-organ false positives that a threshold alone cannot remove, so it behaves like a principled confidence-lowering. Product read: TTA joins contrast phase (EXP-14) and the probability threshold as an operating-point dial for the CADe story, use it when screening specificity is the priority and leave it off when lesion-outline accuracy is. Caveat: n=20 (each healthy case is 5 points), so +25pp is directionally strong but wide. Adopted default stays TTA-off for the reported accuracy numbers.

---

## EXP-16: Resolution inside the whole box (finer spacing, matched field of view) [Week 3, running tonight]

Motivation: whole-box (EXP-12) fixed the field of view and the specificity, but lesion Dice has plateaued around 0.26 across every recipe change. Resolution is the one untested accuracy axis that needs no new infrastructure, and EXP-10 hinted finer resolution helps once the whole organ is in view. The current whole box is a 128 cube at 1.5mm = a 192mm span sampled at 1.5mm per voxel. This run holds that physical span constant but samples it finer.

Variable (single = resolution): patch 128 -> 160 AND spacing 1.5 -> 1.2mm together, so the box footprint stays 192mm (160 x 1.2 = 192 = 128 x 1.5) but each voxel is 1.2mm instead of 1.5mm, giving the tumor about 1.95x more voxels. Holding the field of view constant is exactly what makes this a resolution test and not a field-of-view change (the confound that sank EXP-11). Everything else is identical to EXP-12: SuPreM transfer, crop-native 16, whole-box, bg0 DiceFocal, seed 42, 6000 iters, val on the same 20 tumor-positive cases.

Hypothesis (H1): finer resolution raises lesion Dice by >= 0.02 over EXP-12 (0.263 cleaned) at n=20, because the tumor is resolved in more voxels.
Null (H0): no meaningful lesion Dice gain (within +/- 0.02), meaning resolution is not the ceiling and data scale is (consistent with every other null this project).

Accept H1 if: lesion Dice clears 0.283 at n=20 without specificity collapsing. Reject if within noise.

Cost / risk: about 2x the voxels of EXP-12, so more MPS memory and a longer run. Smoke-tested first (50 iters) so a memory failure aborts before the full run rather than wasting the night. If it OOMs, the fallback is patch 144 @ 1.33mm (also ~192mm span, ~1.4x voxels), or keep 128 and drop spacing to 1.2 (smaller 154mm FOV, less preferred).

Runbook (smoke test gates the full run via `&&`, so a broken/OOM config never reaches the overnight run):

```bash
source .venv312/bin/activate
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 160 --spacing 1.2 \
  --max-iters 50 --val-limit 0 --no-mlflow --ckpt-every 50 --run-name smoke_p160 \
&& caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 160 --spacing 1.2 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_p160_1p2

# morning eval (must match training: roi 160, spacing 1.2)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_p160_1p2__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 160 --spacing 1.2
```

Result (2026-07-15, `transfer_wholebox_p160_1p2` best.pt, eval n=20/20):

| metric | EXP-12 (128 @ 1.5mm) | EXP-16 (160 @ 1.2mm) |
|---|---|---|
| pancreas Dice | 0.778 | 0.805 |
| lesion Dice raw | 0.257 | 0.248 |
| lesion Dice cleaned | 0.263 | 0.228 |
| specificity raw | 50% | 55% |
| specificity cleaned | 55% | 55% |

Decision: REJECT H1 (accept H0). Finer resolution at matched field of view did NOT raise lesion Dice: raw 0.248 vs 0.257 (within noise, slightly lower), cleaned 0.228 vs 0.263 (lower), both well short of the 0.283 bar. It DID raise pancreas Dice (0.778 -> 0.805, back to the original EXP-12 level), which makes sense: the large, easy pancreas benefits from more voxels, the tiny lesion does not. Specificity unchanged (55%). Interpretation: resolution is not the lesion-accuracy lever. This is the decisive null the strategy needed. We have now ruled out, for lesion accuracy, every recipe axis available without new data: sampling (EXP-05), loss (EXP-07), field-of-view / context (EXP-08), and now resolution (EXP-16), while the one structural win (whole-box, EXP-12) lifted pancreas and specificity but not lesion Dice. Four independent nulls point the same way: lesion Dice ~0.26 is the honest ceiling at 95 cases, and DATA SCALE is the remaining lever (the disk-cache / capstone direction). Minor process note: cleaned < raw here (0.228 < 0.248), unlike EXP-12, suggesting finer resolution fragments the lesion into pieces the largest-CC/constraint prunes; if resolution is ever revisited, relax largest-CC. Reported base model stays EXP-12 (128 @ 1.5mm, lesion 0.263).

---

## EXP-17: Data scale-up — 3x the tumor cases (the lever every null pointed to) [Week 3/4, running tonight]

Motivation: four independent recipe axes are now ruled out for lesion accuracy (sampling EXP-05, loss EXP-07, context EXP-08, resolution EXP-16), and the whole-box structural win lifted pancreas + specificity but not lesion Dice. Every arrow points at data scale. This is the first test of that hypothesis: hold the winning whole-box recipe fixed and just feed it more tumor cases. No disk cache needed yet — the RAM CacheDataset handles ~300 whole-box cubes (~5 GB); the cost is a longer one-time cache build.

Variable (single = training-set size): split `dev_subset_clean` (95 cases, 50 tumor) -> `scaled300` (300 cases, 150 tumor). A 3x increase in tumor examples, the bottleneck class. Everything else identical to EXP-12: SuPreM transfer, crop-native 16, whole-box, 128 @ 1.5mm, bg0 DiceFocal, seed 42, 6000 iters, val on the same 20 tumor-positive / 20 tumor-free cases. Split built by `scripts/make_scaled_split.py --n-tumor 150 --n-healthy 150` (manifest-only, seed 42, drawn from the 706 tumor / 6494 healthy train pool).

Hypothesis (H1): more tumor data raises lesion Dice by a real margin, clearing 0.30 at n=20 (up from the 0.263 ceiling), because the model finally sees enough tumor variety to generalize rather than memorize ~50.
Null (H0): lesion Dice stays within noise of 0.263, meaning 3x is not enough and the fix is either much more data or the cascade (capstone).

Accept H1 if: lesion Dice >= 0.30 at n=20 without specificity collapsing. Reject if within +/- 0.02 of 0.263. Secondary read: EXP-12/16 peaked early (best checkpoint ~step 2000) then overfit; with 3x data the peak should land later and higher, so watch whether the in-loop val is still climbing at step 6000 (if so, EXP-17b extends to 10-12k iters).

Cost / risk: the cache build loads 300 full scans from the external drive up front (~30-45 min) before training starts, which front-loads the drive I/O (good: training then runs from RAM, less overnight drive exposure) but concentrates drive-drop risk in the first hour, so keep the drive mounted + lid open + caffeinate. Bad-mask cases (empty/tiny pancreas) are handled by the whole-box `PadEmptyCropd` guard rather than crashing, so an audit pass is optional; run `audit_masks.py` only if the cache build errors on a case. 6000 iters held constant for a clean comparison to EXP-12.

Runbook:

```bash
source .venv312/bin/activate
# split already built: outputs/splits/scaled300.txt (300 cases, 150 tumor)

caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled300 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_scaled300

# morning eval (same recipe + val set; use the archived path)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaled300__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result (2026-07-16, `transfer_wholebox_scaled300` best.pt, eval n=20/20):

| metric | EXP-12 (95 cases, 50 tumor) | EXP-17 (300 cases, 150 tumor) |
|---|---|---|
| pancreas Dice | 0.778 | 0.815 |
| lesion Dice raw | 0.257 | 0.313 |
| lesion Dice cleaned | 0.263 | 0.327 |
| specificity raw | 50% | 50% |
| specificity cleaned | 55% | 50% |

Sweep: lesion Dice ~0.31 flat-to-slightly-rising across thresholds; specificity climbs 40% -> 70% (thr 0.90 -> lesion 0.319 / spec 70%; thr 0.80 -> 0.318 / 65%).

Decision: ACCEPT H1 DECISIVELY. Tripling the tumor data moved lesion Dice from 0.263 to 0.313 raw / 0.327 cleaned (+0.05 / +0.064), clearing the 0.30 bar and beating the ceiling that four recipe levers (sampling, loss, context, resolution) could not touch. Pancreas also rose (0.778 -> 0.815). Specificity essentially held (50% vs 55%, within n=20 noise). Two extra wins: (1) CADe post-processing now HELPS (cleaned 0.327 > raw 0.313, the reverse of EXP-16), so the predictions are cleaner; (2) the whole operating curve shifted UP, at threshold 0.90 you get lesion 0.319 AND specificity 70%, a strictly better dial than EXP-12. This is the first result all week to beat 0.263 and it directly confirms the project's central hypothesis: lesion accuracy is DATA-limited, not recipe-limited. Data scale is THE lever. New Track-A best base. Caveats: n=20 (each healthy case ~5 spec points, so 50 vs 55 is noise); the run executed in `.venv` (Python 3.14, no MLflow) so re-log via `log_run_to_mlflow.py`; check the best checkpoint's step, if in-loop val was still climbing near 6000, EXP-17b (more iters and/or more data) likely climbs further. Pinned as `wholebox_scaled300_GOOD.pt` (archive `transfer_wholebox_scaled300__20260715_205005`). Next: Week 4 = build the disk cache to scale past 300 (500-1000 cases) + add a patient-level detection-sensitivity metric.

---

## EXP-17b: Scale further with the disk cache — 600 cases, 6x tumor [Week 4, running tonight]

Motivation: EXP-17 proved data is the lever (0.263 -> 0.327 at 300 cases). This continues up the curve to 600 cases (300 tumor, 6x the original dev subset) and, in doing so, tests the new disk-cache code that makes scaling past RAM feasible and resume-safe.

New infrastructure (built 2026-07-16): `dataset.py` now supports `cache=disk` via MONAI `PersistentDataset`, wired through `train.py --cache disk` and `config training.cache`/`cache_dir`. It caches the deterministic preprocessing to the internal SSD (`outputs/cache/<recipe-tag>/`) once, filling lazily over the first epoch, then every epoch and every future run reuses it. Unlike the RAM CacheDataset (rebuilt each run, capped by memory), the disk cache scales to thousands of cases and survives interruption. Split built by `make_scaled_split.py --n-tumor 300 --n-healthy 300 --name scaled600`.

Variables (not a pure single-variable run, stated honestly): (1) training data 300 -> 600 cases / 150 -> 300 tumor; (2) iterations 6000 -> 8000, because more data warrants more exposure; (3) cache ram -> disk (an infrastructure change that should not affect the model, only speed/scale). The recipe is otherwise the EXP-12/17 whole-box: SuPreM transfer, crop-native 16, whole-box, 128 @ 1.5mm, bg0 DiceFocal, seed 42, val on the same 20/20.

Hypothesis (H1): continued data scaling raises lesion Dice further, clearing 0.35 at n=20 (a real climb above EXP-17's 0.327), because the model is still data-starved.
Null (H0): lesion Dice plateaus near 0.327, meaning 300 tumor cases is near the point of diminishing returns for this recipe and the next gain needs the cascade or richer labels, not just more data.

Accept H1 if: lesion Dice clears 0.35 at n=20 (or clearly beats 0.327 beyond noise) without specificity collapsing. Either way it maps the data-scaling curve, which is the Week 4 deliverable.

Notes / risk: RUN FROM `.venv312` so it logs to MLflow (EXP-17 ran in `.venv` and did not). The disk cache loads the 600 scans off the external drive over the first epoch (spread out, not a giant upfront build), so keep the drive mounted through roughly the first hour; after that training runs from the SSD cache and the external drive is no longer touched. Do NOT `--resume` (best_val reset bug still unhardened) — run uninterrupted. ~8000 iters at MPS ~0.3 it/s is roughly 7-8h plus the first-epoch cache fill, comfortably inside a 12h window.

Runbook:

```bash
source .venv312/bin/activate   # MLflow logging this time

# 0. smoke test the disk-cache path (~2-3 min): confirms it writes to outputs/cache/
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled600 --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 30 --val-limit 0 --no-mlflow --ckpt-every 30 --run-name smoke_disk
ls -la outputs/cache/ && du -sh outputs/cache/* 2>/dev/null   # should show a populated cache dir

# 1. full overnight run
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled600 --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 8000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_scaled600

# 2. morning eval (archived path)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaled600__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result: to fill in.
Decision: to fill in.

---

## EXP-17c: Max data + long training — every tumor case, 15h+ [Week 4, running tonight]

Motivation: EXP-17 proved data is the lever (0.263 -> 0.327 at 300 cases); the per-case analysis (analyze_cases.py, scaled300) then showed the model DETECTS 95% of tumors but OVER-SEGMENTS them (predicted volume 4-8x ground truth on small/medium tumors), which is what caps Dice. This run pushes the data lever to its ceiling and trains long, to answer two questions at once: (1) does more data + more training keep raising lesion Dice, and (2) does it reduce the over-segmentation on its own — or does that need a loss change (EXP-18 Tversky)?

Scale: `scaledmax` = 706 tumor + 706 healthy = 1412 cases — ALL 706 tumor cases in the train pool (14x the original dev subset, and the maximum tumor data the Mini release's train partition offers; val/test tumors are held out). Uses the new disk cache (`--cache disk`, ~22 GB on the SSD) since this far exceeds RAM.

Variables (not single-variable, stated honestly): data 300 -> 1412 cases (150 -> 706 tumor) AND iterations 6000 -> ~24000 (long training). Recipe otherwise fixed to the EXP-12/17 whole-box: SuPreM transfer, crop-native 16, whole-box 128 @ 1.5mm, bg0 DiceFocal, seed 42. Loss deliberately held at DiceFocal so this is a clean test of "data + training time," with the loss (Tversky, to attack over-segmentation) reserved for EXP-18.

Hypothesis (H1): max data + long training raises lesion Dice clearly above 0.327 (target >= 0.36) and the val curve is still climbing at the end (which would justify a multi-day run).
Null (H0): lesion Dice plateaus near 0.327 despite 14x tumor data and 4x iterations — which would mean the remaining gap is the over-segmentation the LOSS must fix (EXP-18), not something more data solves.

Accept H1 if lesion Dice clears 0.36 at n>=20 without specificity collapsing. Read the val-Dice progression: still rising at 24k iters -> a 72h run is warranted; flat by ~12k -> the ceiling is the loss/recipe, not data volume.

Notes / risk: RUN FROM `.venv312` (MLflow). First epoch fills the disk cache by loading 1412 scans off the external drive (~1-2h) — keep the drive mounted + lid open + caffeinate through that window; after it caches, training runs from the SSD and the drive is idle. Do NOT `--resume` (best_val reset bug); run uninterrupted. ~24000 iters at MPS ~2s/step is roughly 13-14h of training + the cache build, landing near morning. best.pt (by val lesion Dice) is archived, so whatever it reaches is safe. Morning: eval at a larger n (e.g. --n-pos 40) for a stabler read, and re-run analyze_cases.py to check whether the over-segmentation shrank.

Runbook:

```bash
source .venv312/bin/activate

# 0. smoke test the disk-cache path on scaledmax (~2-3 min)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaledmax --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 30 --val-limit 0 --no-mlflow --ckpt-every 30 --run-name smoke_scaledmax

# 1. the long run (~15h)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaledmax --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 500 \
  --max-iters 24000 --val-limit 20 --val-positive --val-every 2000 \
  --run-name transfer_wholebox_scaledmax

# 2. morning: stabler eval + over-segmentation check
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaledmax__<STAMP>/best.pt \
  --n-pos 40 --n-neg 40 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/analyze_cases.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaledmax__<STAMP>/best.pt \
  --n-pos 40 --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result (2026-07-17, run `transfer_wholebox_scaledmax`, archive `..._scaledmax__20260716_165439`, logged to MLflow from .venv312): **best in-loop VAL lesion-Dice 0.487** (n=20 tumor-positive), up from EXP-17's 0.327 — a +0.16 jump, the biggest single move of the project, blowing past the pre-registered 0.36 bar and approaching the ~0.53 segmentation SOTA. Pinned `wholebox_scaledmax_GOOD.pt`.

PENDING before this is final: (1) full `evaluate.py` at n=40 to confirm the in-loop number (in-loop has tracked full-eval closely for whole-box, e.g. scaled300 was 0.313/0.313, so 0.487 is expected to hold, but confirm); (2) read the MLflow val-Dice curve — was it still climbing at 24k iters? and (3) analyze_cases to see whether the gain came from tighter outlines (less over-segmentation) or catching more tumors.

FULL EVAL CONFIRMED (2026-07-17, n=40/40): pancreas Dice **0.837**, lesion Dice **0.524 raw / 0.528 cleaned** — HIGHER than the in-loop 0.487 and on double the cases, so this is solid. Essentially at the ~0.53 segmentation SOTA reference (with the provided-ROI-upper-bound caveat). Detection sensitivity 36/40 = 90%; detected-only lesion Dice 0.582. analyze_cases breakdown:
- By size: small <1cm3 (n=7) 0.225 @ 86% det; medium 1-8cm3 (n=23) 0.536 @ 87%; large >8cm3 (n=10) 0.703 @ 100%. Every bin improved vs scaled300 (small 0.054->0.225, medium 0.324->0.536, large 0.609->0.703).
- By phase: non-contrast (n=18) 0.425, arterial (n=6) 0.491, venous (n=16) 0.646 — the EXP-14 conspicuity gradient persists but non-contrast rose from 0.169.
- KEY MECHANISM: the over-segmentation from scaled300 is LARGELY GONE. Predicted lesion volumes are now within ~1-2x of ground truth (e.g. gt 327/pred 344, gt 7574/pred 7685, gt 8522/pred 7952, gt 25917/pred 27439) versus the 4-8x over-prediction at 300 cases. So the +0.20 gain came primarily from TIGHTER OUTLINES, exactly the failure mode the per-case analysis flagged — and data fixed it without a loss change. This makes EXP-18 (Tversky) less urgent.
- Remaining failure modes: 4 misses (detection 90%); a few small tumors detected but localized wrong (0 Dice despite a lesion predicted, e.g. gt 256/pred 820, gt 392/pred 1458); and one giant 94cm3 tumor under-segmented to 0.197 (an outlier likely exceeding the whole-box field of view). Small tumors and non-contrast remain the hard tail.

Decision: ACCEPT decisively (pending full-eval confirmation). What we can already conclude and what we cannot:
- CONFIRMED: the data-scaling curve is still climbing steeply — 0.169 (whole-scan) -> 0.263 (whole-box, 95 cases) -> 0.327 (300) -> 0.487 (1412 + long training). Data scale is not just a lever, it is THE dominant lever, and at max tumor data it has not plateaued.
- CONFOUND: two things changed vs EXP-17 (data 300 -> 1412 AND iters 6000 -> 24000), so this run does not separate "more data" from "more training time." A control (300 cases at 24k iters, or 1412 at 6k) would decompose it. But the practical result is unambiguous.
- CEILING NOTE: we have now used ALL 706 tumor cases in the train pool, so further data gains from the Mini release are exhausted. Remaining levers: more training TIME (iterations) on this max-data set, the loss (Tversky for over-segmentation, EXP-18), and the ROI-leak correction (EXP-19).
- CAVEAT (do not drop): this is still the UNION ROI, so 0.487 is an upper bound inflated by the lesion-extent leak (unquantified until EXP-19). It is a "provided pancreas+lesion ROI, development-validation" number, not autonomous full-volume performance.

72h decision: if the MLflow val curve was still rising at 24k iters, a much longer run on scaledmax (60-80k iters) is justified and likely climbs further — this is the weekend's highest-value move. If it plateaued, the next lever is the loss/ROI, not more time.

---

## EXP-19: Pancreas-only ROI — quantify the lesion-extent leak [Week 4, the audit control]

Motivation: a two-way metrics audit (mine + Codex, 2026-07-17, saved in `docs/codex-metrics-audit.md`) found the "oracle pancreas box" is actually built from pancreas UNION lesion (`_foreground_label` = label>0). When a lesion protrudes past the pancreas mask, it enlarges/shifts the crop, so lesion location leaks into the model's field of view and biases lesion Dice UPWARD. Every result so far (EXP-10/12/16/17/17b/17c) used this union crop, so the RELATIVE conclusions hold, but the absolute lesion Dice is an upper bound on the provided-ROI setting. This control measures the leak.

Fix implemented (2026-07-17): `preprocessing.roi_source` = `union` (legacy default, unchanged) | `pancreas` (organ mask only). `ComposeLabeld` now keeps the original pancreas mask as `panc_roi`, threaded through orientation/crop/resample, so the crop can be built from pancreas alone. Wired as `train.py --roi-source pancreas` / `evaluate.py --roi-source pancreas`, with its own disk-cache tag so it never collides with union caches.

Variable (single): `roi_source` union -> pancreas. Everything else matched to EXP-17 (scaled300, SuPreM transfer, whole-box, crop-native 16, 128 @ 1.5mm, bg0 DiceFocal, seed 42). Anchor to compare against: EXP-17 union = lesion 0.327 cleaned.

Hypothesis (H1): pancreas-only ROI lowers lesion Dice materially (>= 0.03 drop), i.e. the union crop was inflating the number and the honest provided-pancreas-ROI figure is lower.
Null (H0): lesion Dice is within noise of 0.327, i.e. lesions are almost always inside the pancreas mask so union ~ pancreas and there was effectively no leak.

Either result is publishable and important: it tells us how much (if any) of our headline was ROI leak, and the pancreas-only number becomes the honest one to report going forward.

Runbook (smoke-test FIRST — this exercises the new crop path, which has not run live):

```bash
source .venv312/bin/activate
# smoke (~2-3 min): confirms the pancreas-only crop + panc_roi threading works end to end
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled300 --transfer --cache disk --roi-source pancreas \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 30 --val-limit 0 --no-mlflow --ckpt-every 30 --run-name smoke_panc_roi

# full run (matched to EXP-17 except roi_source)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled300 --transfer --cache disk --roi-source pancreas \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_scaled300_pancROI

# eval (MUST pass --roi-source pancreas so eval matches training)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaled300_pancROI__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5 --roi-source pancreas
```

Result: to fill in.
Decision: to fill in.

---

## EXP-20: Autonomous cascade — predicted ROI, the comparable-to-published number [Week 4, the credibility run]

Motivation (the credibility problem, raised 2026-07-17): every lesion Dice to date — including the EXP-17c headline 0.528 — was measured on a crop built from the GROUND-TRUTH pancreas. That is an oracle ROI: the model is handed *where the pancreas is* before being asked *what is in it*. Published whole-scan pancreatic-tumor numbers get no such gift, so our number is not comparable to anyone else's, which undercuts its credibility. The instructor's bar, stated directly: if the model produces the same result when the crop comes from a *predicted* pancreas instead of the ground truth, the results can be taken seriously. This experiment builds that autonomous pipeline and measures it.

Design — a localize-then-segment cascade, both stages full-volume sliding-window, NO retraining:
- Stage 1 (localizer): a full-scan pancreas model predicts the pancreas on the whole CT; take the largest connected component; read off its bounding box + a buffer. Its job is COVERAGE (contain the pancreas and the tumor), not accurate segmentation, so a ~0.75-Dice pancreas model is enough. Reused checkpoint: `p128_ctx_step6000.pt` (EXP-08, full-scan patch-128, pancreas Dice 0.747). Fallback if coverage is poor: stock SuPreM (32-class, segments pancreas natively) or a quick dedicated localizer.
- Stage 2 (segmenter): the EXP-17c whole-box model, UNCHANGED, run on the predicted crop.

Single-variable harness (`scripts/cascade_eval.py --roi-from`), everything downstream of the crop identical:
- `gt-union` — crop from GT pancreas UNION lesion. Matches how EXP-12/17/17c were scored, so it must REPRODUCE ~0.528 and thereby validate this harness. If it does not, nothing else here is trusted.
- `gt-panc` — crop from GT pancreas ONLY (an inference-time read on the ROI-leak of EXP-19, on the existing model, no retrain). Gap gt-union -> gt-panc = the lesion-extent leak.
- `pred` — crop from the LOCALIZER's predicted pancreas box. The autonomous number. Pancreas-only by construction (the localizer never sees a lesion), so also leak-free. Gap gt-panc -> pred = the pure cost of imperfect localization.

Metrics: lesion + pancreas Dice on tumor-positive cases (raw + cleaned), specificity on tumor-free cases, threshold sweep — all matched to `evaluate.py`. PLUS localizer coverage: fraction of the GT pancreas and GT tumor that falls inside the predicted box, and a count of cases where the box clips >10% of the tumor (the cascade's main failure mode — a clipped tumor cannot be segmented).

Hypothesis (H1): the autonomous (`pred`) lesion Dice lands within noise of the oracle (`gt-union`) number — within ~0.05 at n=40 — with box coverage of the tumor >~95%. If so, the oracle number was a fair proxy all along and the result is credible/comparable.
Null (H0): `pred` drops materially below oracle because localization clips or mislocates tumors (low coverage), meaning the oracle number was optimistic about autonomous performance.

Either way it is the honest headline. Report BOTH numbers going forward — oracle as the "with provided ROI" upper bound, autonomous as the deployable one — exactly how cascade papers present it, which also lets us decompose error into leak vs localization vs segmentation.

Honest confounds, stated up front:
1. Harness crops AFTER resampling to 1.5mm (one clean code path for gt and pred), whereas training cropped in native space then resampled. The whole-box resize to 128^3 normalizes most of this away; the `gt-union` arm is the check — if it reproduces ~0.528, the crop-space change is harmless.
2. Train/eval crop-source mismatch: the Stage-2 model was TRAINED on GT (union) boxes but is now fed PREDICTED boxes (shifted/clipped). This is deliberately the thing under test (does it transfer?). If `pred` sags, the fix is known and cheap — retrain Stage-2 with random jitter on the training box so training looks like deployment (EXP-21, staged and ready but NOT run until we see whether zero-retrain transfer holds).
3. Buffer size (`--margin-vox`, default 12 @1.5mm ~= 18mm) trades clip-risk against drifting back toward a whole-scan input; test sensitivity if `pred` underperforms only from clipping.

Runbook (tonight — eval-only, ~1-2h for 40+40 cases through two SW stages; SANITY one case FIRST):

```bash
source .venv312/bin/activate   # or .venv; no MLflow needed for eval
SEG=outputs/checkpoints/pants-level45/wholebox_scaledmax_GOOD.pt
LOC=outputs/checkpoints/pants-level45/p128_ctx_step6000.pt

# 0. SANITY: one tumor-positive case, saves an overlay PNG — eyeball the crop before trusting aggregates
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from pred --sanity <a_tumor_positive_val_case_id>

# 1. HARNESS CHECK: must land near the oracle 0.528, else stop and debug the harness
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from gt-union --n-pos 40 --n-neg 40

# 2. THE AUTONOMOUS NUMBER (the credibility result)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from pred --n-pos 40 --n-neg 40 --sweep --lesion-within-pancreas-mm 10

# 3. (optional, same harness) the leak control, EXP-19 inference-time read
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from gt-panc --n-pos 40 --n-neg 40
```

Read in the morning: if `gt-union` ~= 0.528 (harness valid) AND `pred` is within ~0.05 with tumor coverage >95%, the number is credible and we build on it. If `pred` drops, the coverage line says whether it is a localization/clip problem (low coverage -> bigger buffer or better localizer) or a crop-shift robustness problem (good coverage but lower Dice -> the EXP-21 jitter retrain). Do NOT launch a 15h run tonight; this eval answers the question first, and the fix (if needed) is a targeted overnight run tomorrow with full information.

### EXP-22 (sub-run of the cascade): a dedicated full-scan pancreas LOCALIZER [Week 4, launched 2026-07-18 overnight]

Goal: replace the reused `p128_ctx` (0.747 pancreas, trained on ~95 cases) with a stronger Stage-1 localizer trained on all 1,412 `scaledmax` cases. A better pancreas model gives tighter, more reliable boxes, so containment needs less buffer. Full-scan patch training (NOT whole-box): standard SuPreM transfer, patch 96, the pancreas channel of the 3-class output is the localizer. Loss stays DiceFocal (pancreas is easy; recall is obtained at inference via the low-probability-threshold box, `cascade_eval --loc-thresh`). Validation off (`--val-limit 0`) because train.py selects best.pt by LESION Dice, which is the wrong metric for a localizer — use the archived `last.pt`. A recall-oriented loss (Tversky, penalize pancreas false-negatives = "dock for missing pancreas") is the reserved next lever IF the containment audit shows the buffer alone is insufficient.
Command run: `train.py --split scaledmax --transfer --cache disk --patch 96 --num-samples 2 --max-iters 16000 --val-limit 0 --run-name localizer_fullscan_scaledmax`.
Then (tomorrow): `cascade_eval.py --audit-coverage --loc-ckpt <last.pt> --loc-roi 96 --loc-thresh 0.1 --margin-vox 16 --n-audit 1000` to certify containment, and re-run the accuracy arm with the new localizer.

Result (2026-07-18): trained (16000 iters, full-scan patch-96, SuPreM transfer, scaledmax; `last.pt` in archive `localizer_fullscan_scaledmax__20260717_235833`). Containment audit n=300:
- The new localizer BEATS the reused p128 on a matched cohort: 88.7% fully contained vs 77.7%, tumor 100% vs 95.5%. More data helped the localizer.
- RECALL mode (`--loc-thresh 0.1 --dilate 2`) REJECTED as the lever: barely moved containment (262->266) but doubled oversize boxes (42->110). Low-threshold inflates boxes without fixing the misses.
- KEY DIAGNOSIS (`--diag-localizer`): most "containment failures" are BROKEN GROUND-TRUTH LABELS, not localizer misses. Examples: PanTS_00000610 gt=32 voxels (near-empty; localizer correctly found a 14k-voxel pancreas elsewhere), PanTS_00000398 gt=46 vox, PanTS_00000817 gt=132,113 vox spanning z 6-125 (~446 cm3 over 119 slices — corrupt/over-inclusive; the localizer's compact prediction is MORE correct than the label). The control PanTS_00000029 (normal gt 23,942 vox / 46 slices) scores containment 1.00. This extends the earlier data-integrity finding (broken pancreas masks) into the val set.
- FIX (code, no rerun): added a GT-quality gate to `--audit-coverage` (flags pancreas GT outside 3,000-90,000 vox or z-span >95 slices as implausible, scores the localizer on VALID-GT cases only, lists broken labels separately). Tomorrow's single audit run now returns the honest localizer number instead of one polluted by bad labels.

Decision: localizer is stronger than the raw 88.7% implied — a large share of failures are label defects. Next (tomorrow): (1) re-run `--audit-coverage --n-audit 800/1000` with the GT gate for the clean containment number + rule-of-three bound on valid-GT cases; (2) size the buffer from the worst REAL (valid-GT) clearance; (3) add the automated plausibility fail-safe (flag/expand when the localizer output OR the input scan is implausible — the deployment safety net); (4) if any real localizer misses remain, test stock SuPreM as a more robust localizer. Then re-run the autonomous accuracy arm (EXP-20 pred) with the new localizer + locked settings.

HONEST CONTAINMENT NUMBER (2026-07-18, `--audit-coverage --n-audit 800 --margin-vox 16`, GT gate on):
- GT-quality gate excluded 76/800 = 9.5% of val cases with implausible pancreas GT (many are literally 0 voxels in our pipeline).
- On VALID-GT cases (n=724): pancreas containment mean 0.9932, **fully contained 685/724 = 94.6%**; tumor containment mean 0.9987, **86/87 = 98.9%**. Worst per-face clearance -88.5mm; the remaining 39 failures (5.4%) are MODERATE clips (-37 to -88mm), not the gross -213mm mislocalizations (those were all broken labels).
- OVERSIZE 220/800 = 27.5% at margin 16: the box exceeds the 128 cube and gets center-cropped. This + the 39 clips share ONE root cause — a 128^3 @1.5mm cube (192mm span) cannot hold a big pancreas + buffer. Motivates EXP-23 (resize-to-fit).
- OPEN QUESTION (must resolve before calling it a data defect): the 0-voxel cases still list `pancreas` + head/body/tail in the manifest's `available_structures`, so either the mask FILES are empty/corrupt (data) or our MONAI load/orient/resample drops them (harness bug). `scripts/audit_masks.py` (raw nibabel voxel counts) settles it — run FIRST. If the files are fine, this is a loading bug in the cascade `pre` pipeline, not bad data, and the 94.6% is pessimistic.
- Models are safe: `transfer_wholebox_scaledmax` (segmenter) and `localizer_fullscan_scaledmax` (localizer) are both logged in MLflow (FINISHED) and archived on disk (`runs/.../best.pt`+`last.pt`).

---

## EXP-23: Resize-to-fit whole-box — never clip the pancreas [Week 4, the containment fix]

> **REMEMBER THIS (the core idea):** don't grow the buffer — grow how the box maps into the cube. Resize the whole pancreas box to FILL 128³ instead of center-cropping it, so the entire pancreas is always inside no matter its size. One retrain. Fixes both the tail-clips and the 27.5% oversize boxes at once.

Motivation: the containment audit (EXP-22) showed the pipeline loses part of the pancreas on ~5% of valid scans and center-crops the box on ~27%, both from ONE cause — the fixed 128^3 @1.5mm cube (192mm span) is too small to hold a large pancreas plus a safety buffer, so `ResizeWithPadOrCropd` center-crops the overflow. A bigger buffer only trades tail-clips for more center-cropping. The principled fix decouples containment from the cube size.

Change (single variable): in the whole-box path, replace `ResizeWithPadOrCropd` (pad small / center-crop large) with a true `Resized` to 128^3 — every pancreas box, whatever its size, is scaled to fill the cube. Small boxes are up-sampled, large boxes are down-sampled, NOTHING is discarded, so the whole organ + buffer is always inside by construction. Applied to BOTH train and inference so they match (this is why it needs a retrain, not just an eval change). Label uses nearest-neighbor interpolation to stay integer.

Hypothesis (H1): full pancreas containment rises from 94.6% toward ~99% and oversize→0, with lesion Dice within noise of EXP-17c's 0.48-0.52 (resolution was already ruled out as the lesion lever in EXP-16, so per-case rescaling should not hurt).
Null/risk (H0): per-case scale variation (a big pancreas shrunk, a small one enlarged) confuses the segmenter and lesion Dice drops materially (>0.03); if so, fall back to a bigger cube (160^3 @1.5mm = 240mm) instead of rescaling.

Runbook (after EXP-22b data cleaning; retrain the whole-box segmenter with the new resize, then re-audit + re-eval):
```bash
# (code change: transforms.py whole_box branch -> Resized(128) behind a `whole_box_mode: resize` flag)
# retrain the segmenter on the CLEAN scaledmax split (empty-GT cases removed)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaledmax_clean --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --whole-box-mode resize \
  --max-iters 24000 --val-limit 20 --val-positive --run-name transfer_wholebox_resize_clean
# then: cascade_eval --audit-coverage (containment) AND --roi-from pred (accuracy) with the new ckpt
```
Result: to fill in.

## EXP-22b: Data-quality cleaning — remove empty/corrupt pancreas labels [Week 4, prerequisite]

Motivation: the containment audit flagged 9.5% of val cases with 0-voxel or degenerate pancreas GT despite the manifest listing a pancreas. If the mask files are truly empty, those cases are in the training splits too, teaching the models "no pancreas here" and hurting both the localizer and the segmenter. Resolve file-vs-harness first, then clean.

Steps: (1) `python scripts/audit_masks.py --write-clean` over the full manifest — raw nibabel voxel counts settle whether the files are empty (data defect) or our MONAI pipeline drops them (harness bug). (2) If data: write clean splits (excluding empty-pancreas cases) and rebuild `scaledmax_clean`; quantify how many of the 1,412 training cases were affected. (3) If harness bug: fix the load/orient/resample path in `cascade_eval.py`'s `pre` and re-audit (the 94.6% would rise). Either outcome is a real finding and improves the honest numbers.

Result (2026-07-18, `audit_masks.py --split val --write-clean`, raw nibabel): the combined `pancreas.nii.gz` is genuinely EMPTY/tiny for 110/1800 val cases (min 0.00 mL) — so it is NOT a MONAI orientation/resample bug on a good mask. Also found OVER-INCLUSIVE labels (max 855 mL vs normal ~150). `val_clean.txt` written (1690 cases). NEW LEAD (likely the real story): PanTS stores the pancreas as a combined file AND as `pancreas_head/body/tail`; the config loads only the combined file, so an empty combined mask may still have the organ in the subregions. Extended `audit_masks.py` (`--max-panc-ml`, subregion volumes, `RECOVERABLE_FROM_SUBREGIONS` flag) to test this; re-run pending. If recoverable, the fix is to union head+body+tail in `ComposeLabeld`/`source_masks` and RECOVER the cases (not discard them), and the 94.6% containment is pessimistic.
RESOLVED (2026-07-18, enhanced `audit_masks.py` on val n=1800): 117 flagged = 101 truly-empty + 9 recoverable-from-subregions + 7 oversized/corrupt-combined. Full picture:
- Combined `pancreas.nii.gz` empty on 110; subregion union empty on 116; they DISAGREE (15 combined-only, 9 subregion-only); 6-7 have a corrupt-HUGE combined (445-855 mL) but NORMAL subregions (~60 mL). On normal cases subregion/combined volume ratio is median 1.00 (they reconstruct each other).
- The 101 truly-empty are ALL healthy (has_lesion=False), CT present, and CLUSTERED: 84/101 = one cohort (site CH / SIEMENS / years "2012;2016;2020"). So one contributing site lacks pancreas organ labels — a real dataset gap, not our bug, and harmless to lesion learning (no tumor cases affected).
- FIX (mask source, robust for the eventual JHU 10k): build pancreas = union(combined, head, body, tail), but DROP the combined file when implausibly large (>300 mL) so the corrupt-huge ones fall back to subregions. Recovers ~15 val cases and hardens the loader. Implement in `ComposeLabeld` / `configs/level45.yaml source_masks.pancreas` (add head/body/tail; add the >300mL guard). The 101 both-empty cases stay excluded via `_clean` splits.
Decision: (1) implement the union+guard mask source; (2) rebuild clean splits (val_clean done = 1683; build scaledmax_clean the same way) excluding the truly-empty + un-fixable-corrupt cases; (3) EXP-23 trains on the clean, recovered data. Separately note: the empty-label thread is DISTINCT from the containment-clip thread (EXP-23 cube fix) — both are real Week-4 items.

---

## ⚠ CODEX FULL-SYSTEM AUDIT (2026-07-19) — CRITICAL VALIDATION LEAKAGE. Headline numbers WITHDRAWN. (`docs/codex-audit-week4.md`)

The Week-4 adversarial audit found — and I VERIFIED against the split files — that **every scaled dataset leaks validation cases into training.** `make_scaled_split.py` sampled from the manifest `split=="train"` column (the raw ImageTr *source folder*), not the carved `train.txt` fold, so:
- scaled300 ∩ val = 54, scaled600 ∩ val = 109, **scaledmax ∩ val = 266**.
- **30/40 positive + 5/40 negative** of the deterministic headline-eval cohort were in `scaledmax` training. Both the segmenter (EXP-17c) AND the localizer (EXP-22) trained on them.
- Canonical `train.txt` ∩ `val.txt` = 0 (create_splits was fine); the bug is only in the derived scaled splits.

CONSEQUENCE — treat these as CONTAMINATED / not held-out until a leakage-free rerun:
- EXP-17 (0.327), EXP-17c (0.528 provided-ROI), EXP-20 (0.483 autonomous), EXP-22 (94.6%/98.9% containment), 90% detection. The data-scaling gains and the autonomous≈oracle claim both need a clean rerun before they can be stated.
- Relative results on the ORIGINAL disjoint dev_subset (EXP-04/05/07/08/09/12/16, transfer≫scratch) are NOT affected by this bug — they used dev_subset, not scaled splits.

OTHER VERIFIED FINDINGS (see report for file+line):
- Containment 94.6% is measured on the PRE-resize box, before the 128³ center-crop truncates the 27.5% oversized boxes → optimistic; must measure effective Stage-2 containment (C2).
- The mask-source fix needs CODE (build_records + ComposeLabeld), not just YAML `source_masks` (nothing reads it) (H1).
- The localizer is a 3-class model (sees lesion supervision); "pancreas-only / never sees a lesion" is FALSE. No oracle at inference, but the framing was wrong (H3).
- `--resume` still unsafe (H4); `_cache_tag` omits HU/orientation/mask-policy → stale-cache risk after the planned changes (H5); several config keys advertised but unwired (M4).
- Confirmed correct: label precedence, same-box crop for image+GT, SW stitching, empty-GT Dice/ignore_empty, SuPreM load, models archived+logged.

FIX ORDER (Codex top-3): (1) rebuild all scaled splits from `train.txt` + startup disjointness assert + invalidate caches + RETRAIN both models + rerun headlines; (2) shared config-driven pancreas resolver (union+guard) in code; (3) effective Stage-2 containment + abstention fail-safe, then EXP-23. Do NOT tune hyperparameters against the contaminated cohort. This audit is exactly why we ran it — the fix is clear and it's caught before the final report / external validation.

FIX IMPLEMENTED (2026-07-18): `make_scaled_split.py` now samples the pool from `train.txt` (not the manifest `split` column) and asserts 0 overlap with val/test at build time. `train.py` now has a startup LEAKAGE ABORT guard (any training split ∩ val/test → assert). Rebuilt `scaledmax_clean` (706 tumor + 706 healthy = 1412, verified ∩val=0 ∩test=0) and `scaled300_clean`. Both compile; splits verified in-sandbox. dev_subset/dev_subset_clean were already clean (∩val=0), so all the ORIGINAL dev-subset experiments are unaffected.

---

## EXP-24: leakage-free scaledmax rerun — the REAL provided-ROI number [Week 4, correctness rerun]

Single variable vs EXP-17c: the training split. Identical whole-box recipe (SuPreM transfer, crop-native 16, 128³ @1.5mm, bg0 DiceFocal, 24k iters, seed 42), but on `scaledmax_clean` (disjoint from val) instead of the leaked `scaledmax`. In-loop val (20 tumor-pos) is now genuinely held-out, so best.pt selection is honest too. Then eval provided-ROI on val n=40/40.
Hypothesis: the real held-out lesion Dice is LOWER than the contaminated 0.528 (the model no longer trained on 30/40 of its eval cases). How much lower is the actual finding — it tells us how much of the headline was memorization vs generalization. Accept nothing until this lands; report this as the honest provided-ROI number going forward.
Note: this is the SEGMENTER (provided-ROI). The localizer must ALSO be retrained on `scaledmax_clean` for a clean autonomous/containment number (next run). Mask-resolver + resize-to-fit are deliberately NOT changed here — single variable = leakage only.
Result (2026-07-19, run `transfer_wholebox_scaledmax_CLEAN`, archive `..._CLEAN__20260719_012104`, MLflow): **best held-out in-loop val lesion Dice 0.407** (n=20 tumor-pos), pancreas 0.836. Vs the CONTAMINATED EXP-17c in-loop 0.487 → the leak inflated the in-loop number by ~0.08. The clean number did NOT collapse (would have if the model were mostly memorizing), so the data-scaling result is REAL at an honest magnitude — most of the 0.52 was generalization, ~0.08-0.10 was leakage. Full provided-ROI eval (n=40/40, `evaluate.py`) PENDING = the number of record. Next: retrain the LOCALIZER on scaledmax_clean, then re-run the autonomous cascade (EXP-20) + containment (EXP-22) leak-free.

FULL EVAL DONE (2026-07-19, provided-ROI, val n=40/40, clean best.pt step 18000): pancreas **0.817**, lesion **0.415 raw / 0.412 cleaned**, specificity **15% raw / 18% cleaned** (sweep: thr 0.90 → lesion 0.404 / spec 28%). THE HONEST NUMBERS. Vs CONTAMINATED EXP-17c (0.528 lesion, and cascade-era spec ~30-38%): the leak inflated BOTH — lesion by ~0.11 AND specificity roughly 2x. Mechanism: a leaked healthy val case was memorized-as-healthy in training, so the model stayed quiet on it; remove it → the model over-fires → true specificity ~15%. So the REAL remaining problem is OVER-PREDICTION / low specificity, worse than we thought once leakage is gone. Lesion Dice 0.415 is real and solid (~0.53 reference). CAVEAT: development-validation (best.pt selected on the first 20 val pos, evaled on first 40); official 901-test still reserved. Levers for the low specificity: (1) MORE HEALTHY training data — current 1:1 tumor:healthy hugely over-represents tumor vs the ~10% prevalence, and only 706 of 6494 train-healthy were used; (2) stratify/report specificity by contrast phase (EXP-14: non-contrast high, PV low); (3) threshold/TTA/Tversky-loss. Next runs: analyze_cases for detection sensitivity + size/phase breakdown (no retrain); then a healthy-ratio experiment (specificity) and the clean localizer retrain (autonomous number).

## EXP-18: Tversky loss — stop the over-segmentation, lift Dice + specificity together [Week 4, tonight 2026-07-19]

Motivation: the clean model (EXP-24) DETECTS tumors well (95%) but OVER-SEGMENTS them 3-13x (gt256→pred1620, gt392→pred5110), which caps lesion Dice at 0.415 and drives specificity to 15% — the same "paints too much lesion" failure on both fronts. DiceFocal has no explicit false-positive penalty. Tversky index = TP/(TP + alpha·FP + beta·FN); raising alpha above beta punishes over-painting directly.

Change (single variable vs EXP-24): loss `dice_focal` -> `tversky` (alpha 0.7, beta 0.3). Everything else identical (scaledmax_clean, SuPreM transfer, whole-box, crop-native 16, 128³ @1.5mm, 24k iters, seed 42). Wired as `train.py --loss tversky --tversky-alpha 0.7 --tversky-beta 0.3` (also `tversky_focal` = Tversky + focal, for a follow-up that guards small-tumor recall). Baseline to beat: lesion 0.415 raw, specificity 15%.

Hypothesis (H1): penalizing false positives tightens outlines → lesion Dice rises above 0.415 AND specificity rises above 15%, WITHOUT detection collapsing below ~90% (there is recall headroom at 95%).
Null/risk (H0): alpha 0.7 over-corrects → the model under-segments, small tumors get missed, detection drops and small-tumor Dice falls. If so, lower alpha (0.6) or switch to `tversky_focal` (keeps the focal term for small/rare lesions).
Accept if lesion Dice or specificity improves materially with detection held; report both. The disk cache from EXP-24 (`scaledmax_clean`) is reused (loss doesn't affect preprocessing) so no cache rebuild → ~14h pure training.
Result (2026-07-19, pure `tversky` alpha 0.7): REJECTED — over-corrected. At step 8000 the PANCREAS collapsed to 0.000 (vs ~0.8 under DiceFocal) and lesion was only 0.146. Mechanism: a global FP penalty at alpha 0.7 makes the large pancreas class not worth predicting (its boundary FP penalty outweighs the TP reward, and missing it is a cheap FN at beta 0.3), so the model abandons the pancreas entirely. The over-segmentation to fix is on the LESION, but pure global Tversky punished the (fine) pancreas too. Killed the run. Lesson: the FP penalty must be gentle and must NOT sink the pancreas → EXP-18b.

## EXP-18b: Tversky-Focal (mild), keep the pancreas alive [Week 4, 2026-07-19 overnight]

Change vs EXP-18: `tversky` -> `tversky_focal` and alpha 0.7 -> 0.6, beta 0.4. The FOCAL term is a per-voxel misclassification penalty that punishes dropping the pancreas, counteracting the collapse; the milder Tversky (0.6, closer to Dice's 0.5) leans gently on lesion over-painting instead of steeply. Single change vs the EXP-24 DiceFocal baseline is the loss family + the FP tilt. `train.py --loss tversky_focal --tversky-alpha 0.6 --tversky-beta 0.4`.
Hypothesis: pancreas stays healthy (>0.7), and the mild FP penalty tightens lesion outlines → lesion Dice and/or specificity improve over the 0.415 / 15% baseline with detection held near 95%.
Safety gate: check the first val (step 2000) — if pancreas is climbing it is cured; if pancreas ~0.000 again, the focal term did not save it, kill and go milder still (alpha 0.55) or build a true lesion-only FP penalty.
Result (2026-07-20, full eval val n=40/40): pancreas 0.821 (collapse CURED — focal worked), lesion 0.399 raw / 0.365 cleaned, specificity 20% raw / 22% cleaned, detection 98% (39/40). Vs DiceFocal baseline (EXP-24: 0.415/0.412, spec 15%/18%, det 95%). MODEST WIN in the intended direction on every axis at once: spec +5pp raw, detection +3pp, whole threshold sweep shifted up ~4pp (thr 0.90 → spec 32% vs 28%), for a lesion-Dice cost of 0.016 (within n=40 noise). So penalizing FP genuinely made the model more precise/less trigger-happy. CAVEATS: (1) the gain is SMALL — 20% specificity is still poor (model still false-alarms on ~80% of healthy scans); (2) the loss lever is shallow and we can't crank alpha (0.7 collapsed pancreas, and even 0.6 started UNDER-segmenting some tumors — that's why CLEANED dropped to 0.365: model under-paints, then largest-CC + anatomical constraint prune real lesion). Report RAW (0.399) for this model, not cleaned. Decision: KEEP as a modest operating-point improvement; the loss lever is largely tapped. The remaining specificity gap is a DATA problem (model over-calls on healthy tissue) → EXP-25.

## EXP-25: more healthy training data — the specificity lever [Week 4, pre-registered]

Motivation: specificity is low (~15-20%) because the model over-predicts lesion on HEALTHY scans. All runs trained on a 1:1 tumor:healthy ratio (706 tumor + 706 healthy) while real prevalence is ~10% tumor, so the model is biased toward calling tumor. We have ~6,494 healthy cases in the clean `train.txt` fold and used only 706. Feeding far more healthy scans directly teaches "normal pancreas = no lesion," which should raise specificity more than any loss tweak.
Change (single variable vs EXP-24): healthy count 706 -> larger (e.g. 706 tumor + 2,118 healthy = 1:3, split `scaledmax_h3`; or push toward all 6,494 = ~1:9 realistic prevalence). Build with `make_scaled_split.py --n-tumor 706 --n-healthy <N>` from `train.txt` (disjoint-asserted). Same whole-box + DiceFocal recipe (or stack on tversky_focal). 
Hypothesis: specificity rises materially (toward 40-60%+) as the healthy ratio grows; watch that lesion Dice / detection don't fall off a cliff (too much healthy can suppress the rare tumor). Sweep the ratio (1:1 -> 1:3 -> 1:9) to find the knee. Accept the ratio that best trades specificity for a small detection cost.

LAUNCH (2026-07-23, LOCKED before any results). Run the extreme first: full realistic prevalence, 706 tumor + all 6,494 healthy (~1:9), split `fullhealthy`, fresh from the SuPreM init, the SAME whole-box recipe as the EXP-24 baseline (crop-native 16, 128³ @1.5mm, DiceFocal bg0, union ROI, 24k steps) — ONLY the healthy count changes, so it is a clean single variable vs the 0.415 model. ~14-18h (7,200-case first-epoch cache fill on the drive). Eval on the SAME frozen official test cohorts (`test_pos.txt` 151 / `test_neg.txt` 750) used for the 0.474 baseline. **PRE-REGISTERED ACCEPT BAR: specificity rises materially (test 17% -> ~30%+) AND detection sensitivity stays >= 90%.** If detection drops below 90%, the 1:9 ratio is too aggressive -> fall back to a 1:3 run (706 + 2,118). Compare against the EXP-24 test baseline: lesion Dice 0.474 [0.42-0.52], pancreas 0.827, detection 96%, specificity 17%. Expectation: specificity up, lesion Dice ~flat (tumor data capped), maybe a small detection cost.

Result (2026-07-24 launch → 2026-07-25 eval, run finished ~14h, checkpoint `transfer_wholebox_fullhealthy__20260724_133810/best.pt`, val lesion ~0.29 in-loop; scored on the FROZEN official test cohorts `test_pos.txt` 151 / `test_neg.txt` 750, same as the 0.474 baseline): **REJECTED on the detection floor.** The specificity half of the bar cleared decisively, but detection missed the ≥90% floor, so by the pre-registered rule this is a reject — no goalpost-moving (mirror of the EXP-26 lesson: a result that just misses the bar is a miss).

| metric | EXP-24 baseline (headline) | EXP-25 fullhealthy | pre-registered bar |
|---|---|---|---|
| specificity (mask-neg @50mm³) | 17% | **46%** (47% cleaned) | ≥30% → **PASS** |
| detection sensitivity (≥50mm³) | 96% | **88%** (133/151) | ≥90% → **FAIL** (3 cases short of 90.1%) |
| lesion Dice (all pos) | 0.474 [0.42–0.52] | 0.374 | — |
| lesion Dice (detected-only) | — | 0.424 | — |
| pancreas Dice | 0.827 | 0.827 | — |

Mechanism (analyze_cases, n=151, --whole-box --crop-native 16 --roi 128): the +29pp specificity was bought by making the model conservative, and the price landed almost entirely on **small tumors** — small (<1cm³) detection fell to **56%** and their Dice collapsed to **0.013** (the model essentially stopped drawing them); medium 0.368 Dice / 93% det, large 0.531 / 97%. By phase: arterial 0.445/93%, non-contrast 0.412/100%, venous 0.354/86%, delay 0.269/67% (n=3). Threshold sweep confirms the model itself is structurally more specific, not a threshold artifact: even at the most permissive thr 0.30, specificity is 40% (vs baseline 17%); thr 0.90 → 67% spec / 0.355 Dice.

Decision: **REJECT as a headline replacement.** For a CADe tool whose job is to not-miss tumors, trading 8pp of detection — concentrated in the hardest, most important-to-catch small-tumor class — for specificity is the wrong trade. **The EXP-24 0.474 / 96%-detection model stays the primary.** BUT this is a valuable rejection: it proves the low specificity is a real, movable *data* property (not a fixed flaw) and it precisely locates the cost (small tumors), exactly as EXP-05/07 predicted the lever would be data-scale. The pre-registered fallback (1:3 run, 706 + 2,118) is the direct next step, plus a lower detection-threshold sweep to test whether a few small tumors can be recovered while keeping most of the specificity gain (the 40% spec at thr 0.30 suggests an operating point that may beat baseline on BOTH axes) — a new, clearly-labeled exploration for Week 5, not a retroactive bar change. Checkpoint archived at `outputs/checkpoints/pants-level45/runs/transfer_wholebox_fullhealthy__20260724_133810/`; per-case CSV `outputs/test_fullhealthy_percase.csv`.

ANALYZE_CASES (2026-07-19, clean best.pt, n=40): **detection sensitivity 38/40 = 95%** (STRONG — finds almost every tumor; 2 misses = a 500mm³ non-contrast + a 1313mm³ arterial), detected-only Dice 0.437. By size: small<1cm³ 0.110 (86% det), medium 0.428 (96%), large 0.599 (100%). By phase: venous 0.582 / arterial 0.458 / non-contrast 0.252. **KEY: the model OVER-SEGMENTS small/medium tumors 3-13x** (gt256→pred1620, gt392→pred5110, gt1215→pred3743, gt1647→pred4566) and under-segments the giants — this over-painting is what caps Dice AND drives the 15% specificity (same "too much lesion" behavior on healthy scans). Note: this is the SAME over-segmentation EXP-17c appeared to "fix" — that fix was partly leakage; on clean data it persists. Clear lever: a precision-oriented loss (Tversky / Focal-Tversky penalizing false positives, the reserved EXP-18) to tighten outlines → should raise Dice AND specificity together; plus more-healthy-data for specificity. Model saved: MLflow `transfer_wholebox_scaledmax_CLEAN` [FINISHED] + archive `..._CLEAN__20260719_012104` (best.pt/last.pt).

Result (2026-07-18, `cascade_eval.py`, n=40 pos / 40 neg; localizer `p128_ctx_step6000.pt` @0.747 pancreas, segmenter `wholebox_scaledmax_GOOD.pt`):
- Sanity (PanTS_00000029): pancreas coverage 1.00, lesion coverage 1.00, lesion Dice 0.790 — overlay confirms the crop + mapping are correct.
- HARNESS CHECK (`gt-union`): pancreas 0.833, lesion 0.496 raw / 0.484 cleaned, specificity 30% (raw=cleaned). Reproduces the EXP-17c oracle (pancreas 0.837, lesion 0.524/0.528) within ~0.03. The small dip is confound #1 (crop-after-resample + margin-12 vs training's native crop), so the harness is VALIDATED: within-harness comparisons are trustworthy, and its absolute lesion Dice reads ~0.03 below the native-crop oracle.
- AUTONOMOUS (`pred`): pancreas 0.819, lesion **0.483 raw** / 0.456 cleaned, specificity 38% (raw=cleaned; sweep reaches 48% at threshold 0.90 for only -0.007 lesion Dice). Localizer coverage pancreas 0.992, tumor 0.979; only 2/40 cases clip >10% of the tumor; 0 full localizer misses.
- THE KEY NUMBER: within the same harness, autonomous (0.483) vs GT-box (0.496) is a **0.013 lesion-Dice gap — inside n=40 noise**. The predicted pancreas box gives essentially the same result as the ground-truth box. Coverage 98% confirms the localizer almost never clips the tumor.

Decision: **ACCEPT H1 DECISIVELY.** The pipeline is now autonomous and the headline is credible/comparable: lesion Dice ~0.48 with a PREDICTED ROI, ~equal to the provided-ROI result, at 98% tumor coverage. No jitter retrain (EXP-21) needed — zero-retrain transfer held. Report going forward as two numbers: autonomous lesion Dice ~0.48 (deployable, comparable to the ~0.53 published reference) vs provided-ROI ~0.52 (upper bound).
- Corollary on the ROI leak (EXP-19): the autonomous arm is leak-free by construction (the localizer never sees a lesion) yet matches the leaky `gt-union` arm, which implies the lesion-extent leak was small. Running `gt-panc` would quantify it exactly (optional, same harness), but the practical conclusion is the leak was not materially inflating the headline.
- HONEST caveat (the real specificity, finally measured): this is the first proper specificity read on the max-data model — ~30-38% at n=40 (tunable to ~48% by threshold), MODERATE and lower than the small-data models' 50-55%. More data bought a large lesion-Dice gain and 90% detection, but not higher specificity. Specificity stays an operating-point dial (threshold / TTA / anatomical constraint) and a capstone data problem; detection sensitivity (90%) remains the CADe headline.
- Next: fold the autonomous number into the report/UI as the deployable figure; optionally run `gt-panc` to close the leak decomposition; the remaining accuracy lever is small-tumor localization + specificity (both data/curriculum problems for Week 4 / capstone).

---

## EXP-26: Anatomy-aware auxiliary supervision — head/body/tail as an auxiliary task [Week 4, 2026-07-20/22, REJECTED at convergence (24k); 12k ACCEPT was a false positive]

Hypothesis: adding **auxiliary head/body/tail (pancreas subregion) supervision** to the whole-box SegResNet+SuPreM model raises **lesion Dice** without diluting the tumor objective, by teaching the model within-pancreas anatomical position. First step toward the richer multi-structure (Level-5 / capstone) model. Full design: `docs/spec-exp26-anatomy-aware.md` (v4, approved after 4 adversarial review rounds); readiness dossier `docs/exp26-pretraining-readiness.md`.

Single variable: **`λ_anat`** (auxiliary-loss weight). 26A control = 0.0, 26B treatment = 0.3. Everything else identical — same 5-class model (bg/head/body/tail/lesion), same SuPreM-initialized head loaded from ONE hashed init file (`exp26_init_5ch.pt`, sha `8c9af5eb…`), same frozen cohorts, ROI, seed, deterministic per-step data order + augmentation, LR-schedule horizon (24k), 12k operational stop, and val-selection. The primary loss is a deliberate probability-based reformulation (collapse the 5-class softmax to bg/pancreas/lesion, `p_panc=p1+p2+p3`, soft Dice + foreground focal on the collapsed probs — NOT MONAI DiceFocal), so 26A is the sole baseline (no causal claim vs the 0.415 EXP-24 number). The auxiliary is masked per-class Dice for head/body/tail over non-lesion pancreas voxels.

Held constant / controlled: mutually-exclusive single-label design (audit-validated, see below); collapsed 3-class metrics so numbers stay comparable to prior work; frozen, hashed, disjoint cohorts (train 1249 / val20 20 / report40 40 / report40_neg 40, `configs/cohorts/exp26/`); resume verified identity-checked + strict optimizer/scheduler; determinism confirmed (two 40-step runs matched to MPS float noise; a Ctrl-C at step 21 resumed at 21 and continued).

Accept bar (pre-registered, spec §14): paired 26B−26A **mean** lesion-Dice diff > 0 with bootstrap 95% CI excluding 0 (target ≥ +0.02), AND mean pancreas Dice regresses by ≤ 0.01.

DATA AUDIT (step 0, `scripts/audit_subregions.py`, gates the experiment): of 1,512 → full val pool, **420 cases excluded** (empty head/body/tail masks; CT/mask affine inconsistency e.g. LAS CT vs LPS mask + zeroed origin; pancreas-union <20 mL). Frozen cohorts re-audit to **VERDICT: PASS** (1,349 cases, 0 fatal/overlap/volume). Two findings worth banking regardless of EXP-26: (1) **head/body/tail have 0.00% mutual overlap** across the cohort → the single mutually-exclusive label is provably lossless for the aux domain; (2) the `head∪body∪tail` resolver caps pancreas volume at 20.2–278.7 mL with **no corrupt-huge masks**, i.e. the union resolver fixes the corrupt combined-mask defect.

Result (2026-07-21, report40 held-out, n=40 pos / 40 neg, 12k steps each, collapsed 3-class):
- **26A control (λ=0):** lesion Dice 0.145 raw / 0.168 cleaned, pancreas 0.668, specificity 15% (6/40).
- **26B treatment (λ=0.3):** lesion Dice 0.185 raw / 0.178 cleaned, pancreas 0.676, specificity **42%** (17/40).
- **Paired 26B−26A (`paired_bootstrap.py`, report40): lesion mean diff +0.041, bootstrap 95% CI [+0.007, +0.074] — CI EXCLUDES 0**, beats the +0.02 target. Pancreas +0.008 (CI includes 0 → no regression). Win/loss/tie 18/6/16 (median +0.000 — the mean gain is concentrated in a subset of cases, not a uniform lift).
- Bonus: 26B **dominates the entire threshold sweep** (better lesion Dice AND specificity at every operating point; e.g. thr 0.30 → 26B 0.236/35% vs 26A 0.156/5%). Anatomy supervision made the model both more accurate and more specific.
- In-loop val20 (n=20, noisy): 26A best 0.142, 26B best 0.141 — near-tied, which is why the n=40 report40 read (above) is the one we trust.

12k INTERIM decision (LATER OVERTURNED — see the 24k result below): at the 12k stop the paired result met all pre-registered criteria (+0.041 lesion, CI excluding 0, no pancreas cost), which *looked* like ACCEPT. Both arms were clearly UNDERTRAINED at 12k (26B val lesion climbed 0.034→0.141 still steeply; EXP-24's best was ~step 18k), the absolute (0.185 vs 0.415) was depressed by the 5-class reformulation + undertraining (controlled out, both arms), and the win was concentrated (18/6/16). Because we do not trust intermediate reads, we ran both arms to the pre-registered 24k horizon before deciding. That was the right call.

Result (2026-07-22, report40 held-out, n=40 pos / 40 neg, **24k CONVERGED**, collapsed 3-class):
- **26A control (best.pt @ step 24000):** pancreas 0.730, lesion 0.290 raw / 0.290 cleaned, specificity 38% raw / 40% cleaned.
- **26B treatment (best.pt @ step 19500):** pancreas 0.716, lesion 0.314 raw / 0.318 cleaned, specificity **48%** raw / 48% cleaned.
- **Paired 26B−26A (report40): lesion mean diff +0.023, bootstrap 95% CI [−0.007, +0.057] — CI INCLUDES 0** (not significant at n=40). Win/loss/tie 14/13/13 (a dead heat; median +0.000). Pancreas mean diff **−0.014, CI [−0.023, −0.007] — CI EXCLUDES 0** (a small but statistically-significant regression).
- Both arms recovered to ~0.29–0.31 lesion at 24k (from ~0.15–0.19 at 12k), confirming the 12k numbers were undertraining, not a ceiling.

Decision: **REJECT — DO NOT ACCEPT 26B.** At convergence, neither pre-registered criterion holds: the lesion improvement (+0.023) is a point estimate whose CI includes 0, and it comes with a significant −0.014 pancreas regression. **The 12k "ACCEPT" was a false positive**: the anatomy arm appears to converge *faster* early, so at 12k it looked significantly ahead, but by 24k the control caught up and the advantage washed out. This is the value of pre-registering the bar and training to convergence rather than reporting the flattering intermediate.

Honest nuances (cut both ways, not spin): (1) the lesion point estimate stays mildly positive and **26B is clearly more specific — 38%→48% raw** — and edges the control across most of the threshold sweep, so anatomy supervision *shifts the operating point toward specificity* rather than delivering an accuracy win; (2) the pancreas regression is mechanistically sensible — splitting the pancreas into head/body/tail spends capacity on a distinction that slightly hurts the merged-pancreas Dice; (3) 26B's best.pt is step 19500 (it peaked and val-selection held there), 26A's is 24000.

Conclusion for the project: **anatomy-aware auxiliary supervision is not the lever for lesion Dice** — reject it for the headline metric. It remains potentially useful as a *specificity dial* or as groundwork for a genuine multi-structure model (capstone), but it does not beat the plain whole-box recipe on accuracy and costs a little pancreas. The real levers remain data scale + the whole-box framing. Checkpoints archived: `exp26A_lam0__20260721_182106` (24k complete, val 0.378) and `exp26B_lam03__20260721_224437` (24k complete, val 0.343); per-case CSVs `outputs/exp26A_percase.csv` / `exp26B_percase.csv`.

Process note (documented per the "science not a beauty pageant" rule): the 24k continuation was interrupted by a double-launch and a wrong-venv (3.14) run mid-afternoon; recovered cleanly by restarting 26A from its clean 12k checkpoint entirely in `.venv312`, so both arms' 12k→24k trajectories are single-environment. The archive + strict-resume identity guard + atomic saves held throughout (no lost or contaminated checkpoint). Determinism means resuming from 12k reproduced the same trajectory, so the ~1 h of redone compute did not affect the result.

---

## Backlog: designed but not yet run

- More data, scaling past the 100-case dev subset. The EXP-05/07 null results point at data volume as the real ceiling; this is the main Week 3/capstone lever and needs a persistent/disk cache to replace the RAM `CacheDataset` (not yet wired — see `configs/level45.yaml` `training.cache`).
- Harder-negatives sampling (`sampling.strategy: classes`), already coded, to be tried only if it becomes the priority; sampling proved a weak lever in EXP-05.
- ROI cascade (coarse locate then fine segment), the autonomous version of the EXP-12 whole-box stage: a pancreas detector in front of the box stage; capstone.

Now formalized as experiments (moved off this backlog): transfer-vs-scratch = EXP-09; test-time augmentation = EXP-15.

## Checkpoint & logging discipline (added 2026-07-12, after losing EXP-12)

The EXP-12 whole-box best (lesion 0.263) was lost because every run shared one `best.pt`/`last.pt` and the manual "copy it after the run" step was skipped, so the EXP-13/14 runs overwrote it; it also ran without MLflow, so no metrics were live-logged either. Two code fixes now make both failure modes structural rather than dependent on memory:

1. Per-run archive (in `train.py`). Alongside the shared `best.pt`/`last.pt`, every run writes immutable copies into `outputs/checkpoints/<experiment>/runs/<run_name>__<timestamp>/` with a `run_info.txt` recording the recipe (split, mode, patch, spacing, whole_box, crop, loss, seed). No later run can touch a previous run's folder, so a keeper is never clobbered and never an orphan. Point eval at the archived path, not the shared `best.pt`, for anything you care about.
2. Persistent, MLflow-independent ledger. Every run appends one row to `outputs/checkpoints/<experiment>/run_ledger.csv` (timestamp, run_name, split, mode, iters, best_val_lesion, archive_dir). If MLflow is unavailable, `train.py` now prints a loud banner instead of a quiet one-liner, so an unlogged run cannot slip by unnoticed.

Rules of thumb: always launch from `.venv312` (has MLflow); the archive/ledger live under `outputs/` (git-ignored, local safety net) while `experiments.md` stays the committed record; periodically prune archive folders of rejected runs to reclaim disk (each is ~110 MB).

## How to add the next entry

Before a run: write the hypothesis, the single variable, what is held constant, and the accept/reject bar. After the run: paste the MLflow name, the training-time val, the full evaluation numbers, and the decision. Never edit a past result; add a new experiment if something changes.

---

## EXP-27: PANORAMA tumor injection — break the 706-tumor ceiling [CAPSTONE, PRE-REGISTERED 2026-08-02, NOT YET RUN]

**Status: pre-registered before any PANORAMA data has been downloaded, looked at, or trained on.
Nothing below may be edited after the first result is read.**

### Motivation
Data scale is the only lever that has ever moved lesion Dice (EXP-17: +0.05 from tripling tumor
cases). Four recipe axes have been ruled out — sampling ratio (EXP-05), loss background (EXP-07),
context/patch (EXP-08), resolution (EXP-16) — and anatomy supervision was rejected at convergence
(EXP-26). But we are now **out of tumors**: `train.txt` contains **706** tumor-positive cases and
`scaledmax_clean` already uses **all 706**. Scaling within PanTS adds only healthy scans, which is
EXP-25, already run and **rejected on the detection floor**.

PANORAMA's public training set supplies **578 tumor-positive scans that are verifiably not in PanTS**
(2,238 total − 194 MSD − 80 NIH = 1,964 usable; 676 PDAC − 98 MSD-derived PDAC = 578). See the
overlap protocol in `docs/capstone-planning.md`. That is an **82% increase** in tumor-positive
training data and the only route to more tumors that exists.

### Hypothesis
**H1 (primary):** Adding 578 non-overlapping tumor-positive scans raises lesion Dice on the frozen
PanTS official test cohort, because the model is tumor-data-limited rather than recipe-limited.

**H2 (pre-registered expectation, NOT a success criterion):** Specificity will **fall**. PANORAMA is
portal-venous only, and EXP-14 established that PV-trained models over-fire (raw spec 10% PV vs 90%
non-contrast). We predict this *before* seeing the result so that observing it is a confirmation
rather than a rationalization.

### Change — single variable
Training cohort only. Everything else identical to the **EXP-24 clean baseline**: SegResNet +
SuPreM transfer, whole-box (crop-native 16 → 128³ @1.5 mm), DiceFocal `include_background: false`,
`roi_source=union`, seed 42, 24k steps, same LR schedule.

| | baseline (EXP-24, `scaledmax_clean`) | treatment (`panorama_mix`) |
|---|---:|---:|
| tumor-positive | 706 (PanTS) | **1,284** (706 PanTS + 578 PANORAMA) |
| tumor-free | 706 (PanTS) | 1,284 (706 PanTS + 578 PANORAMA) |
| total | 1,412 | 2,568 |

Ratio held at **1:1** — the established convention (EXP-17, EXP-24) and justified by EXP-05, which
proved sampling ratio is not a driver. Holding it constant keeps "more tumors" the single variable.

### Evaluation — unchanged, and deliberately PanTS-only
Scored on the **same frozen official PanTS cohorts** used for every headline number:
`test_pos.txt` (151) and `test_neg.txt` (750). **No PANORAMA case appears in evaluation.** This asks
the right question — *do foreign tumors improve performance on home turf?* — and keeps annotation
shift out of the measurement.

Report: lesion Dice (all positives) · pancreas Dice · detection sensitivity · specificity ·
threshold sweep · **paired per-case comparison vs the EXP-24 baseline** with bootstrap 95% CI and
win/loss/tie counts (the EXP-26 protocol — a mean difference without a CI is not a result).

### ★ PRE-REGISTERED ACCEPT BAR
**ACCEPT if BOTH hold at the 24k horizon:**
1. **lesion Dice improves by ≥ +0.02** on `test_pos` (baseline **0.474**), **and the paired bootstrap
   95% CI on the per-case difference excludes 0**;
2. **detection sensitivity ≥ 96%** (baseline 145/151 — no regression permitted; EXP-25 died here).

**Specificity is explicitly NOT part of the accept bar** (H2 predicts it falls), but a **floor of
10%** applies: below that the model is unusable regardless of Dice, and the run is rejected.

**REJECT** if lesion Dice moves < +0.02, or the CI includes 0, or detection drops below 96%, or
specificity falls under 10%.

**Report at the pre-registered 24k horizon only.** No intermediate reads — EXP-26's 12k "ACCEPT" was
a false positive produced by exactly that mistake.

### Confounds — acknowledged in advance, not discovered later
"More tumors" arrives bundled with three other changes. This experiment **cannot** attribute a win to
tumor count alone, and the writeup must say so:
1. **PDAC only** — PanTS covers PDAC + IPMN + PNET; the added tumors are all PDAC.
2. **Portal-venous only** — phase distribution shifts (the H2 mechanism).
3. **AI-generated pancreas masks** (Alves et al.) on the PANORAMA cases — the whole-box crop would
   use a **silver-standard** organ mask for those. Prefer the **482 expert-annotated** PDAC lesions;
   if 482 suffices, use only those and drop the 194 AI-annotated (a cleaner, smaller treatment arm —
   **decide before running, record the choice here**).

Follow-up arm if H1 accepts (**EXP-27b**): re-run with PANORAMA cases matched to the PanTS phase
distribution, to separate "more tumors" from "more portal-venous."

### Prerequisites — code before compute
- [ ] label remap `PANORAMA {1=PDAC, 4=parenchyma} → ours {2=lesion, 1=pancreas}`, **config-driven,
      with a unit test** (reversing this silently poisons training)
- [ ] exclusion list for the 274 MSD/NIH cases, **asserted at load time** — same guard pattern as the
      leakage abort in `train.py`
- [ ] **pin the `panorama_labels` commit hash** (live repo; unpinned = irreproducible) and record it
      in this entry
- [ ] storage plan (~200 GB raw, 4 Zenodo batches) — one batch (49 GB) is enough to smoke-test
- [ ] **smoke test 50 iters** on a mixed cohort before the long run (EXP-11 was lost to a
      train/eval mismatch that a smoke test would have caught)

### Record before running
- PANORAMA labels commit: `________`
- Treatment arm used: `all 676 PDAC` / `482 expert-only` → `________`
- Launch timestamp: `________`

---

## EXP-28: Literature-derived gate features vs. hand-picked [CAPSTONE, PRE-REGISTERED 2026-08-15, NOT YET RUN]

**Pre-registered before the corpus is built and before any feature is implemented.**

### Motivation
The tumor-presence gate needs input features. The obvious approach is to hand-pick them from
intuition and prior experiments (predicted lesion volume, connected-component count, contrast phase).
A second source exists: 8,422 indexed papers on pancreatic CT. Reading them should suggest
image-derivable properties an engineer would not think of unaided.

The specific failure this targets: **diffusely enlarged but healthy pancreata get flagged as tumor.**
Nothing in the current feature set distinguishes *"this whole organ is large"* from *"there is a
discrete mass in this organ."*

**This is not retrieval-augmented inference.** The LLM never runs at prediction time and never sees a
patient scan. It reads literature and proposes candidate features; a human implements the computable
ones; the gate is trained on numbers. **No circularity** — the corpus influences the model through
engineering decisions, not through runtime text.

### Hypothesis
Features suggested by the pancreatic imaging literature improve the tumor-presence gate over a
hand-picked feature set, measured as patient-level AUC on the frozen official test cohort.

### Method
1. Retrieve ~50 abstracts on distinguishing PDAC from chronic pancreatitis and normal variation.
2. Prompt the local LLM: *"From these passages, list image-derivable properties of a pancreas CT
   that distinguish pancreatic ductal adenocarcinoma from chronic pancreatitis and from normal
   anatomical variation. For each, state what would need to be measured."*
3. **Record the raw output verbatim in this entry before implementing anything.**
4. Mark each suggestion computable / not computable from our segmentation output. Implement the
   computable ones.
5. Train the gate under three feature sets, everything else identical.

| arm | features |
|---|---|
| **A — hand-picked** | predicted lesion volume, connected-component count, max probability, organ volume, contrast phase |
| **B — literature-derived** | whatever step 4 yields, and only that |
| **C — union** | A + B |

### Evaluation
Frozen official test cohorts (`test_pos.txt` 151 / `test_neg.txt` 750). Primary metric:
**patient-level AUC** (baseline 0.804; volume alone 0.843). Secondary: specificity at fixed 96%
detection. Paired bootstrap CI on per-case scores.

### ★ PRE-REGISTERED ACCEPT BAR
**ACCEPT B or C over A if patient-level AUC improves by ≥ 0.02 and the paired bootstrap 95% CI on the
difference excludes 0.** If C wins but B alone does not, the honest conclusion is that literature
features are *complementary*, not superior — report it that way.

**REJECT** if neither B nor C clears the bar. A null result is still informative: it says
domain-literature feature engineering does not beat an engineer who has stared at the failure cases.

### Confounds and honesty notes
- The LLM's suggestions depend on which abstracts are retrieved. **Fix the retrieval query and record
  it**, or arm B is not reproducible.
- Some suggestions will be un-computable (labs, patient history, prior imaging). Record what was
  discarded and why — the discard list is itself a result.
- Arm B may include features that overlap arm A. That is fine, but note it rather than claiming
  novelty.
- Success here is **not** evidence the assistant improves prediction at inference. It cannot, and the
  writeup must say so.

### Record before running
- retrieval query: `________`
- corpus snapshot date / commit: `________`
- LLM model and version: `________`
- raw LLM output: `________`
- features implemented / discarded: `________`

---

## EXP-29: Organ-shaped anisotropic patch — spend the voxel budget on detail, not padding [CAPSTONE / BREAK, PRE-REGISTERED 2026-08-15, NOT YET RUN]

**Pre-registered before any run. This is the THIRD resolution-adjacent experiment after two nulls;
the prior probability of success is low and that is stated up front deliberately.**

### Background — why this is being revisited at all
Two previous attempts at finer resolution failed to move lesion accuracy:

| exp | change | lesion Dice | verdict |
|---|---|---|---|
| EXP-10 | crop to pancreas + 1.0 mm isotropic | 0.234 vs 0.206 | +0.028, but **confounded** — the same run picked up the encoder-training fix |
| EXP-16 | 160³ @ 1.2 mm, matched field of view | 0.248 vs 0.257 | **worse** — rejected |

Meanwhile EXP-17 changed only the amount of data and moved lesion Dice 0.263 → 0.313. The standing
conclusion is that **data is the lever and resolution is not.** This experiment does not dispute that.
It tests a *different* claim: not "finer is better," but "the current input geometry wastes most of
its voxels, and redistributing them is free."

### Three measurements that motivate it (all taken 2026-08-15)

**1. Isotropic resampling discards real detail and fabricates fake detail.** Across all 9,901 scans:

| | p5 | p25 | median | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|
| in-plane spacing (mm) | 0.64 | 0.74 | **0.81** | 0.98 | 1.50 | 5.00 |
| slice thickness (mm) | 0.78 | 0.80 | **1.25** | 2.50 | 5.00 | 10.00 |
| anisotropy (z / in-plane) | 0.78 | 1.00 | 1.19 | 2.86 | 6.40 | 14.22 |

Resampling everything to 1.5 mm isotropic therefore:
- **discards acquired in-plane detail on 83.6% of scans** (in-plane finer than 1.5 mm)
- **interpolates z on 31.1% of scans** (thickness coarser than 1.5 mm), manufacturing slices that
  carry no information — 11.2% are coarser than 3 mm

The dataset is **bimodal**, not uniformly anisotropic: most scans are near-isotropic thin-slice,
about a third are thick-slice. Any single isotropic target is wrong for one regime.

**2. The pancreas occupies ~11% of the input cube.** Measured on 113 randomly sampled pancreas masks
in native millimetres:

| axis | median | p90 | max |
|---|---:|---:|---:|
| x | 135.1 mm | 167.1 | 195.0 |
| y | 73.1 mm | 89.0 | 136.5 |
| z | 80.2 mm | 102.5 | 166.2 |

Bounding-box volume against the current 192 mm cube: **11.2% at median, 21.5% at p90.** Roughly
nine-tenths of every input tensor is not pancreas.

**3. Clipping is NOT happening — hypothesis tested and rejected.** The concern that a 192 mm cube
truncates larger organs was checked and is false: **0.9% of cases exceed 192 mm in x, 0% in y, 0% in
z.** The current pipeline is not silently losing anatomy. Recorded here because it was a real
suspicion and the measurement settled it.

**4. Supporting evidence that the padding is waste, not context.** EXP-08 compared 128³ against 96³
at matched field of view — i.e. *more* surrounding tissue — and was rejected: lesion 0.187 vs 0.206.
More context made accuracy worse. If surrounding tissue were useful, that result should have gone the
other way.

### Hypothesis
Holding the voxel budget approximately constant, an organ-shaped anisotropic patch at finer in-plane
resolution improves lesion Dice over the isotropic cube, because the same compute is spent on
acquired detail instead of on padding and interpolated slices.

### Change — single variable (input geometry), everything else fixed

| | A — current baseline | B — organ-shaped anisotropic |
|---|---|---|
| patch | 128 × 128 × 128 | **192 × 144 × 80** |
| spacing | 1.5 × 1.5 × 1.5 mm | **1.0 × 1.0 × 2.0 mm** |
| field of view | 192 × 192 × 192 mm | 192 × 144 × 160 mm |
| voxels | 2,097,152 | 2,211,840 (**105%**) |
| in-plane detail | coarsened on 83.6% of scans | preserved on most |
| z interpolation | on 31.1% of scans | on far fewer |

All three dimensions divide by 16, so the four-level encoder is unaffected and the SuPreM checkpoint
still loads (patch geometry is transfer-safe; changing `init_filters` would not be).

Everything else identical: SegResNet + SuPreM transfer, DiceFocal `include_background: false`,
`roi_source=union`, same cohort, same seed 42, same step count, same LR schedule, fp32.

### Evaluation
Frozen official test cohorts (`test_pos.txt` 151 / `test_neg.txt` 750). Report lesion Dice, pancreas
Dice, detection sensitivity, specificity, threshold sweep, and **per-case paired bootstrap CI**.

**Additionally report containment** — the fraction of ground-truth pancreas and tumour voxels that
survive the crop, measured *after* the final resize, not on the pre-resize box. This is the metric
that tests the geometry claim independently of accuracy, and it is the measurement a previous audit
flagged as optimistic and never corrected.

### ★ PRE-REGISTERED ACCEPT BAR
**ACCEPT if either:**
1. **lesion Dice improves by ≥ 0.02** with the paired bootstrap 95% CI on the per-case difference
   excluding 0; **or**
2. **containment improves measurably with lesion Dice flat** (within ±0.01) — a pipeline that loses
   less anatomy at equal accuracy is the better pipeline and should be adopted.

**REJECT** otherwise. Report at the pre-registered step horizon only — no intermediate reads. EXP-26's
12k "accept" was a false positive produced by exactly that mistake.

### Confounds and honesty notes
- **Three things change together**: patch shape, in-plane spacing, and z spacing. A win cannot be
  attributed to any one of them. If B accepts, a follow-up isolating spacing from shape is required
  before claiming which mattered.
- **This is compute-neutral, not cheaper.** An earlier estimate claimed ~42% of current compute; that
  was based on a wrong guess at organ dimensions (y and z assumed 50–80 mm; actual maxima are 136 and
  166 mm). The corrected figure is 105%. Recorded so the error is not repeated.
- **Cache invalidation**: the preprocessing config hash changes, so the warm cache must be rebuilt.
  Confirm the cache tag includes spacing and patch shape before running, or a stale cache will
  silently serve arm A's tensors to arm B.
- **Smoke-test first** (50 iters). EXP-11 was lost to a train/eval geometry mismatch that a smoke test
  would have caught, and this experiment changes geometry on both sides.
- `--roi` must set sampling patch size *and* inference ROI together; that has been the same bug class
  twice (EXP-11, EXP-08).

### Why run it despite low expected value
If it wins, every subsequent model gets a free upgrade and the fix is a config change. If it loses,
the resolution question is closed with **three** independent nulls rather than two, which is a
defensible thing to state at defence rather than an open question a reviewer can poke. Either way the
containment number gets measured correctly for the first time.

**Scheduled as break-time work, not inside the ten weeks.**

### Record before running
- cohort used: `________`
- cache tag / config hash: `________`
- containment measured (arm A): `________`  (arm B): `________`
- launch timestamp: `________`

---

# ★ JHU PUBLISHED CHECKPOINTS — WHAT THEY ACTUALLY DID (investigated 2026-08-15)

Read from the HuggingFace model cards for `AbdomenAtlas/MedFormerPanTS` and
`AbdomenAtlas/R-SuperPanTSMerlin`. Recorded because it changes what is worth testing next.

## The two checkpoints

| | MedFormerPanTS | R-SuperPanTSMerlin |
|---|---|---|
| architecture | **MedFormer** (transformer) | **MedFormer** (same) |
| training | masks only — the "segmentation baseline" | + **report supervision (R-Super)** |
| data | PanTS public | 1.8K pancreatic lesion reports from **Merlin** (Stanford) + 0.9K PanTS masks |
| license | **MIT** | not stated on the card |
| benchmark | P-Sen 80.8 · T-Sen 75.2 · Spe 90.0 · AUC 0.924 · DSC 52.9 | P-Sen 80.1 · T-Sen 80.1 · Spe 93.2 · AUC 0.903 · DSC 53.4 |
| code | `github.com/MrGiovanni/R-Super` | same |
| paper | arXiv:2510.14803 (Oct 2025), MICCAI 2025 best-paper runner-up for R-Super | same |

## ★ FINDING 1 — they output 26 classes; we output 3

Both checkpoints predict **26 structures simultaneously**:

```
adrenal_gland_left, adrenal_gland_right, aorta, bladder, colon, common_bile_duct,
duodenum, femur_left, femur_right, gall_bladder, kidney_left, kidney_right, liver,
lung_left, lung_right, pancreas, pancreas_body, pancreas_head, pancreas_tail,
pancreatic_lesion, postcava, prostate, spleen, stomach,
superior_mesenteric_artery, veins
```

**This is the largest structural difference between our model and the leaderboard.**

Critically, it is **not** what EXP-26 tested. EXP-26 added *pancreas subregions* (head/body/tail) and
was rejected at convergence. These models add **surrounding organs** — duodenum, common bile duct,
SMA, veins, postcava, stomach, spleen. Different hypothesis, untested by us.

The PanTS paper separates the two effects explicitly: gains are *"directly attributable to the 16x
larger-scale tumor annotations and **indirectly supported by the 24 additional surrounding anatomical
structures**."*

Mechanism is plausible in a way subregions were not: subregion labels describe the *inside* of the
organ; surrounding organs describe where the organ **ends** — which is precisely where our model
over-paints. The duodenum wraps the pancreatic head; the SMA and veins define the boundary a tumour
invades.

**We already have these labels.** PanTS ships 28 structures per case, on the drive, unused.

## ★ FINDING 2 — they independently use our anatomical constraint

From the inference documentation:

> `--organ_mask_on_lesion` will use organ segmentations (**produced by the R-Super model itself, not
> ground-truth**) to remove tumor predictions outside its organ.

This is the `constrain_lesion_to_pancreas` post-processing we arrived at independently — the lever
that moved specificity 8% → 42% and was reconfirmed on two models. They ship it as a flag on their
SOTA checkpoint, and they use the **predicted** organ mask, which is the autonomous form we need
anyway. **Cite this at defence:** our strongest post-processing lever matches what the dataset authors
do on their own leaderboard model.

## ★ FINDING 3 — R-Super's reports are EXTERNAL, confirming the NLP scope decision

R-SuperPanTSMerlin is trained on reports from **Merlin (Stanford)**, not from PanTS. This confirms the
2026-08-02 analysis: report supervision works because the text is an *independent* source of
information. PanTS's own `structured report` field is template-generated from the masks and carries
nothing new.

**Merlin is publicly available** from Stanford AIMI, which means R-Super is reproducible in principle.
Large scope addition — logged as a research direction, **not scheduled**.

## Other differences worth noting
- **MedFormer (transformer) vs our SegResNet (CNN).** Architecture is a confound in any comparison.
- **`fold_0_latest.pth`** implies cross-validation folds; we train a single split.
- Inference expects `BDMAP_XXXXXXX/ct.nii.gz` directory layout — a small adapter is needed to run it
  on our data.

## Standing decision, reaffirmed
These checkpoints remain **reference-only**. Distilling MedFormerPanTS into our SegResNet would make
our headline derivative of theirs, and the leaderboard claim depends on the model being ours. Using
them as a **diagnostic** is fine and valuable — see EXP-31.

---

## EXP-30: Surrounding-organ auxiliary supervision [CAPSTONE, PRE-REGISTERED 2026-08-15, NOT YET RUN]

### Motivation
Our model over-segments tumours 3–13x and false-alarms on healthy scans. Both failures are about not
knowing where the pancreas **ends**. EXP-26 tried to fix this from the inside (head/body/tail) and
returned a null at the pre-registered horizon: lesion +0.023 with CI [−0.007, +0.057] including 0, and
pancreas −0.014 with the CI excluding 0.

The JHU leaderboard models take the opposite approach — 26 classes covering the organs *around* the
pancreas — and the PanTS paper attributes indirect gains to exactly those 24 surrounding structures.
That hypothesis is untested here and the labels are already on disk.

### Hypothesis
Auxiliary supervision on **surrounding organs** improves lesion Dice and/or specificity by teaching
the model the pancreas boundary, where over-painting occurs.

### Change — single variable
Auxiliary loss weight `λ_organs` on a set of neighbouring structures. Control = 0.0, treatment = 0.3
(matching the EXP-26 protocol so the two are directly comparable).

Auxiliary classes, chosen for anatomical adjacency rather than completeness:
**duodenum · common bile duct · superior mesenteric artery · veins · stomach · spleen**

Everything else identical to the EXP-24 clean baseline: SegResNet + SuPreM transfer, whole-box
(crop-native 16 → 128³ @1.5 mm), DiceFocal bg0, `roi_source=union`, seed 42, same cohort, same steps.
Reuse the **AnatomyAwareLoss** and collapse-aware evaluation built for EXP-26 — that infrastructure
already exists and was verified.

### Evaluation
Frozen official test cohorts (151 / 750). Primary: lesion Dice with paired bootstrap CI. Secondary:
pancreas Dice, specificity, detection, and **over-segmentation ratio by tumour size** (predicted
volume ÷ ground-truth volume), which is the mechanism this is supposed to fix.

### ★ PRE-REGISTERED ACCEPT BAR
**ACCEPT if lesion Dice improves by ≥ 0.02 with the paired bootstrap 95% CI excluding 0, AND pancreas
Dice does not regress by more than 0.01** (the regression that partly sank EXP-26).

A secondary win counts and must be reported as secondary, not headline: if lesion Dice is flat but the
**over-segmentation ratio on small tumours drops materially**, that is mechanistic evidence worth
keeping even under a formal reject.

**Report at the pre-registered horizon only.** EXP-26's 12k "accept" was a false positive from reading
an intermediate; the anatomy arm converges faster and looks better early.

### Confounds
- The six auxiliary classes were chosen by anatomy, not by search. A different set might do better;
  this tests the hypothesis, not the optimum.
- PanTS surrounding-organ masks have not been quality-audited the way the pancreas masks were. **Check
  for empty and corrupt masks first** — the pancreas set had 0-voxel and 7 corrupt-huge cases.
- Adding classes changes the output head, so SuPreM head re-initialisation applies as in EXP-26. Use
  the same hashed shared-init file protocol.

### Record before running
- auxiliary classes actually used: `________`
- empty/corrupt mask audit result: `________`
- shared init hash: `________`

---

## EXP-31: Comparative error analysis against MedFormerPanTS [CAPSTONE / BREAK, DIAGNOSTIC — not a training experiment]

### Purpose
Not a hypothesis test. A **diagnostic** that answers a question no amount of self-analysis can: on the
cases we fail, does the published SOTA model also fail?

- **Failures overlap heavily** → the limit is the data, and no architecture change will help.
- **Failures diverge** → the difference is architecture or multi-organ context, and EXP-30 becomes
  higher-value.

Either answer redirects effort. Cost is one inference pass and no training.

### Method
1. Download `AbdomenAtlas/MedFormerPanTS` (MIT licensed) and the R-Super inference code.
2. Write an adapter from our layout to their expected `BDMAP_XXXXXXX/ct.nii.gz` structure — symlinks
   are sufficient, per their documentation.
3. Run on a targeted subset rather than everything: the **6 tumour cases we miss**, the **worst 20 we
   over-segment**, and **30 healthy scans we false-alarm on**.
4. Score their output with **our** evaluation harness so numbers are comparable.
5. Build a per-case comparison table and eyeball the disagreements as overlays.

### What to report
Per-case: our Dice vs theirs, our predicted volume vs theirs vs ground truth, agreement on the
patient-level call. Plus the summary — of our 6 missed tumours, how many does MedFormer find?

### Honesty constraints
- **This does not improve our model and must not be presented as if it did.** It is error analysis.
- Their numbers here are **not** a benchmark comparison: different preprocessing, different
  architecture, and a hand-picked adversarial subset. Do not quote a Dice from this as "MedFormer
  scores X."
- Distillation from this checkpoint stays **out of scope** — it would make our result derivative.

### Record
- checkpoint sha / download date: `________`
- adapter script path: `________`
- cases evaluated: `________`

---

# ★★ MEDFORMER-PanTS TRAINING CONFIG — read from the released checkpoint (2026-08-15)

`MedFormerPanTS/pants_pancreas_release/config.txt` ships with the weights. This is the actual recipe
behind the 52.9% DSC leaderboard entry. Recorded verbatim-derived; nothing inferred.

## Their recipe vs ours

| | **MedFormer-PanTS (52.9 DSC)** | **ours (0.474, provided-ROI)** |
|---|---|---|
| architecture | MedFormer — hybrid CNN + transformer | SegResNet (pure CNN) |
| **pretraining** | **`pretrain: False`, `pretrained: None` — from scratch** | SuPreM transfer |
| base channels | `base_chan: 32`, `chan_num [64,128,256,320,256,128,64,32]` | `init_filters: 16` |
| conv / transformer mix | `conv_num [2,0,0,0,0,0,2,2]`, `trans_num [0,2,4,6,4,2,0,0]`, `num_heads [1,4,8,10,8,4,1,1]` | all convolutional |
| norm | `in` (InstanceNorm) | GroupNorm (to match SuPreM) |
| **patch size** | **`training_size: [128,128,128]`** | **128³ — identical** |
| sliding window | `[128,128,128]` | same |
| classes | `classes: 42` (label yaml lists 26) | 3 |
| **optimizer** | AdamW, **`base_lr: 0.001`**, betas [0.9,0.999], **`weight_decay: 0.05`** | AdamW, LR 1e-4 transfer / 2e-4 scratch, **wd 1e-5** |
| warmup | 5 epochs | 2 epochs → cosine |
| **schedule length** | **100 epochs × 1000 iters = 100,000 steps** | 24,000 steps |
| **EMA** | **`ema: True, ema_alpha: 0.99`** | **none** |
| deep supervision | `aux_loss: True, aux_weight [0.5, 0.5]` | none (would break SuPreM load) |
| loss | `ball_dice_last` (R-Super ball + dice) | DiceFocal, `include_background: false` |
| class weighting | `class_weights: False`; `weight [0.5, 1, 1, …]` — background at 0.5 | bg excluded from loss |
| **pos/neg balancing** | **`balance_pos_neg: False` — none** | 1:1, extensively tuned |
| tumour cropping | `crop_on_tumor: True` | positive-biased sampling |
| augmentation | `rotate [30,30,30]`, `gaussian_noise_std 0.02`, scale and translate **disabled** | — |
| precision | `amp: False` (fp32) | fp32 |
| batch | 2 per GPU, 4 global, 2 GPUs | 1 |
| validation | `val_freq: 20000` | every 5 epochs |
| cross-validation | `k_fold: 10`, `split_seed: 0` | single split |

The training log (`fold_0.txt`, 16,370 lines) shows the released weights were **resumed from epoch 20**
and run to 100 — so this checkpoint is a continuation, not a single clean run.

## Five differences worth acting on

**1. They trained from scratch.** No SuPreM, no Models Genesis, no CLIP pretraining. Our EXP-09 found
transfer beats scratch decisively (+0.13 lesion) — but that was at **95 cases**. They have 9,000 and
100k steps. Pretraining matters most when data is scarce; this does not contradict EXP-09, it bounds
where its conclusion applies.

**2. EMA of weights (`ema_alpha: 0.99`) — we do not do this.** Exponential moving average of
parameters is a well-established, nearly free gain in segmentation. Roughly ten lines of code, no
architecture change, no extra compute of consequence. **Cheapest untested idea on this list.**

**3. Weight decay 0.05 against our 1e-5 — a 5,000x difference.** Ours is a conservative fine-tuning
value; theirs is the standard modern AdamW setting.

**4. Base LR 1e-3 against our 1e-4 — 10x.** With warmup and a 100k schedule.

**5. No positive/negative balancing at all.** We spent EXP-05 and EXP-25 on sampling ratio. With 9,000
cases they simply do not balance. Consistent with our own finding that ratio was not the driver.

## ⚠ Caveat — do not cherry-pick from a coherent recipe
High LR (1e-3) + high weight decay (0.05) + long schedule (100k) + EMA is **one recipe**, tuned
together. Lifting the learning rate alone onto a 24k-step run with wd 1e-5 would likely diverge or
overfit. If any of this is tested, test it as a **coherent block** or change one variable with the
others held at our values and expect a null.

## What this validates
- **128³ patch size is identical to ours.** Independent confirmation of that choice.
- Their `--organ_mask_on_lesion` flag is our anatomical constraint (already recorded above).

## Open item
`classes: 42` in the config against 26 entries in `labels_pants.yaml`. Unexplained — possibly
sub-classes or padding in the head. Resolve before drawing any conclusion about output structure.

---

# ★★ CAPACITY QUESTION — CLOSED (2026-08-15). Do not reopen without new evidence.

MedFormer-PanTS measured precisely from the checkpoint: **37,886,548 parameters (37.9 M)**, plus an
identical `ema_model_state_dict` and 75.8 M of AdamW optimizer state. Trained to **epoch 100** — the
full schedule. Ours is **4.7 M**, so theirs is **8.1x**.

**Capacity is NOT our bottleneck, and we already proved it.**

**Stage 0 is the proof.** We deliberately overfit a tiny subset and reached pancreas Dice 0 → 0.888
and lesion 0 → ~0.7. A model that can memorise its training set has sufficient representational
capacity. Underfitting presents as high *training* error; ours approaches zero. The binding constraint
is generalisation, not width.

Three supporting arguments:
1. **Widening breaks SuPreM transfer.** `init_filters` is not checkpoint-compatible (recorded since
   Week 1). EXP-09 measured transfer at **+0.13 lesion Dice** over scratch at our data scale. Widening
   trades a measured gain for a speculative one.
2. **Their 38 M spans 26 classes** — lungs, femurs, bladder, prostate. Per-class capacity is nowhere
   near 8x ours.
3. **38 M on 706 tumours would overfit hard.** They have ~10x the cases *and* 26-class supervision on
   every one — call it ~30x the effective supervision signal. Their capacity is sized to their data.

**Conditional reopen — one case only.** If EXP-27 succeeds and the tumour count roughly doubles
(706 → 1,284), the scratch-versus-transfer trade may shift, and scratch training would allow free
widening. Their config is the existence proof that at 9,000 cases, scratch + 38 M wins. Revisit **only**
with that data increase in hand, and re-run EXP-09 first.

---

## ★ EXP-32: EMA of model weights [CAPSTONE, PRE-REGISTERED 2026-08-15, HIGH PRIORITY — MUST NOT BE DROPPED]

### Motivation
The JHU leaderboard model uses `ema: True, ema_alpha: 0.99` and ships a separate
`ema_model_state_dict`. Their training log states plainly: **"Use EMA model for evaluation."** We have
never used EMA and have never tested it.

Exponential moving average of parameters is a long-established, near-free improvement in
segmentation. It costs one extra copy of the weights in memory, a single lerp per step, and no extra
gradient computation. It is the **cheapest untested idea in this entire log**.

### Change — single variable
Maintain `θ_ema ← α·θ_ema + (1−α)·θ` each optimiser step, α = 0.99. Evaluate with the EMA weights.
Everything else identical to the current best baseline.

Both checkpoints are saved so the raw and EMA weights can be scored separately from **one run** — the
comparison is free.

### Evaluation
Frozen official cohorts (151 / 750). Score raw and EMA from the same run: lesion Dice, pancreas Dice,
detection, specificity, paired bootstrap CI on per-case differences.

### ★ PRE-REGISTERED ACCEPT BAR
**ACCEPT if EMA weights beat raw weights on lesion Dice with the paired bootstrap 95% CI excluding 0,
and detection does not regress below 96%.** Any positive effect is adopted permanently, since the cost
is negligible.

### Notes
- α = 0.99 at 24k steps gives an effective averaging window of ~100 steps. If the schedule lengthens
  (EXP-33), consider α = 0.999. **Record which α was used.**
- Do not start EMA at step 0 from random weights — begin after warmup, or the average is polluted by
  the initial transient.
- EMA interacts with early stopping: best-checkpoint selection must be made on the **EMA** metric if
  EMA is what gets deployed.

---

## ★ EXP-33: Schedule length — are we reporting under-trained models? [CAPSTONE, PRE-REGISTERED 2026-08-15, HIGHEST PRIORITY]

### Motivation — this one may invalidate prior conclusions
JHU trains **100 epochs × 1,000 iterations = 100,000 steps**. We train **24,000**.

That 24k was chosen in Week 3 when a run took ~16 hours on MPS. It was a **throughput decision, not an
empirical one**, and it has never been tested. We do not know whether our models are still improving
when we stop them.

**Why this outranks everything else:** if 24k is short of convergence, then every null result in this
log is suspect. EXP-05, EXP-07, EXP-08, EXP-13, EXP-16, EXP-26 all compared two arms at 24k. Two arms
that both stop before convergence can look identical **because neither finished**, not because the
change did nothing. EXP-26 already demonstrated the adjacent failure — the anatomy arm converged
faster and looked ahead at 12k, which is why the pre-registered horizon exists.

### Hypothesis
Lesion Dice continues to improve materially beyond 24,000 steps.

### Change — single variable
Schedule length. Train the current best configuration to **72,000 steps** (3x), with the LR schedule
stretched to the new horizon rather than truncated. Checkpoint and fully evaluate at
**24k / 36k / 48k / 60k / 72k**.

This produces a **training curve on the frozen test cohort**, not a single number — that curve is the
deliverable.

### ★ PRE-REGISTERED ACCEPT BAR
**ACCEPT longer training if lesion Dice at 72k exceeds 24k by ≥ 0.02 with the paired bootstrap 95% CI
excluding 0.**

**If accepted, the consequence is not optional:** the standard horizon changes, and the nulls listed
above must be labelled **"tested at a horizon now known to be short"** in this log. That is a
correction we commit to in advance.

**If rejected** — the curve flattens by 24k — that is equally valuable: it confirms every prior
comparison was made at convergence and closes the question permanently.

### Cost
Roughly 3x a normal run. On MPS that is prohibitive; this is a **cloud-GPU or Windows-CUDA job**, or a
long unattended break run. Either way it must be uninterrupted — `--resume` is hardened but still not
verified end to end.

### Confounds
- Longer training with weight decay at 1e-5 may overfit where JHU's 0.05 would not. If the curve rises
  then falls, that is an **overfitting signature**, and the follow-up is weight decay, not more steps.
- Run **with EMA enabled** if EXP-32 has already accepted, and record it — otherwise the two changes
  are entangled.

### Record before running
- start checkpoint / cold start: `________`
- LR schedule horizon: `________`
- EMA enabled: `________`
- evaluated at steps: `________`

---

## ★★★ EXP-34: Train/test generalisation gap — RUN THIS FIRST [PRE-REGISTERED 2026-08-15]

**This is the first experiment to run once the capstone is approved. Everything about the capacity
question, and the priority of EXP-32/33, depends on its answer.**

### Why it comes first
The capacity question was closed on 2026-08-15 using Stage 0 as evidence: the model overfit a tiny
subset (pancreas 0 → 0.888, lesion 0 → ~0.7), therefore capacity is sufficient. **That reasoning is
weaker than stated.** Stage 0 proves 4.7 M parameters can memorise *a handful* of cases. It does not
prove 4.7 M can represent the true function across 706 diverse tumours. The capacity note is therefore
**conditional, not settled**, and this experiment settles it.

### Method
Score the registered model on a random sample of the cases it **trained on** (n ≈ 100), using
`evaluate.py` with the identical harness, thresholds, and post-processing used for the test set. No
training, no new code — an evaluation pass over a different case list.

### The decision table — written before the result

| training Dice | test Dice | interpretation | consequence |
|---|---|---|---|
| ≈ 0.80 or above | 0.474 | **overfitting.** The model already fits what it is shown; the gap is generalisation | Capacity question CLOSED for real. More parameters would make it worse. Data (EXP-27) and EMA (EXP-32) are the levers. |
| ≈ 0.55–0.70 | 0.474 | **partial fit** | Ambiguous. EXP-33 (schedule length) becomes the tiebreaker — an undertrained model looks like a small one. |
| ≈ 0.50 or below | 0.474 | **underfitting.** The model cannot fit its own training data | Capacity question REOPENS. Scratch + wider + long schedule becomes a live option, not a conditional one. |

### Also record
- training Dice by tumour size band (small / medium / large). If small tumours score poorly **on
  training data**, that is underfitting on the hardest class specifically, which is a different and
  more actionable finding than a global gap.
- training-set specificity. If the model false-alarms on healthy scans it has *seen*, the specificity
  problem is not a generalisation failure at all.

### Constraints
- Use the **same** evaluation code path as the test harness. A bespoke script would reintroduce the
  EXP-11 class of error.
- Sample the training cases randomly and record the list. Cherry-picking easy cases inverts the result.
- This is a **measurement, not a hypothesis test** — there is no accept/reject bar, only the decision
  table above, which is binding.

### Record
- checkpoint evaluated: `________`
- training cases sampled (list or seed): `________`
- training Dice: `________`   test Dice reference: 0.474
- by size band: `________`
- training-set specificity: `________`
- verdict per decision table: `________`

---

# ★★ SCOPE CHECK — ARE WE SOLVING THE PROBLEM JHU IS MEASURING? (2026-08-15)

Researched against arXiv:2510.14803, the PanTS benchmark table, and the R-Super inference docs.

## What they actually measure
The published leaderboard reports **P-Sen · T-Sen · Spe · AUC · DSC**, and the 2025 paper's headline
claims are **sensitivity and specificity**, not Dice: *"improved sensitivity by +13% and specificity
by +8%, surpassing radiologists in detecting five of the seven tumor types."*

**The bar being set is detection performance against human readers, not segmentation overlap.** Our
project already treats detection as the headline, so the framing is aligned.

## ✅ Our 3-class scope is sufficient for the pancreas benchmark
Their models predict 26 structures, but every reported metric concerns `pancreatic_lesion`. The other
25 classes are **means, not ends** — anatomical context that helps the tumour prediction (EXP-30) and
supplies the organ mask for their `--organ_mask_on_lesion` constraint. We predict pancreas and lesion,
so we can compute every metric on their table.

## ⚠ THREE REAL SCOPE MISMATCHES

### 1. Largest-connected-component post-processing breaks tumour-wise sensitivity
Our pipeline keeps the **largest connected component**. Their T-Sen definition: *"a tumor is a true
positive only if correctly localized. Patients with multiple tumors can contribute multiple true
positives."*

**A largest-CC filter structurally caps us at one tumour per patient.** On any multi-lesion case we
cannot score above 1, regardless of what the model actually found. This is not a tuning issue — it is
a design decision that is incompatible with the metric.

**Action:** T-Sen must be computed *before* largest-CC, and largest-CC must become optional at
inference. Add to the EXP-31 / submission-prep work.

### 2. Specificity is the metric that will be tested hardest, and it is our weakest
The OOD suite includes **RSNA Abdominal Trauma, 4,706 cases** — trauma patients, overwhelmingly
without pancreatic cancer. At our current 17% specificity we would falsely flag roughly **3,900 of
them**.

**This reframes the gate from an improvement to a precondition.** Submitting at 17% specificity would
produce a published number that is indefensible, on the largest of their four test sets.

### 3. The field has moved to multi-tumour
The 2025 paper covers seven tumour types and adds spleen, gallbladder, prostate, bladder, uterus, and
oesophagus. We are pancreas-only. That is **fine** — the pancreas benchmark still exists and is what
we are targeting — but it should be stated as a deliberate scope choice rather than left implicit.

## ★ A reframe worth keeping: our masks are worth more than they sound
From the abstract: *"When trained on 101,654 reports, AI models achieved performance comparable to
those trained on 723 masks."*

**101,654 reports ≈ 723 expert masks** — roughly 140 reports per mask. We hold **706 expert
tumour masks**, and PANORAMA adds **382 more**. On their own exchange rate, our mask corpus is worth
on the order of 100,000 clinical reports.

Our data position is far stronger than "706 cases" makes it sound. What we lack is not annotation
quality — it is quantity of *scans*, which is a different problem with different solutions.


## 2026-09-28 — Capstone engineering diagnostic: localizer CPU learning/recovery

Pre-execution plan: [synthetic learning plan](capstone/operations/LOCALIZER-LEARNING-PLAN-2026-09-28.md).
This is a synthetic engineering check, not a CAP-EXP real-data experiment or model-selection result.
First attempt `localizer-learning-a04795a9-193f-43c1-8ec8-fa01451ceb0a` stopped at checkpoint publication
because the supplied store root was relative; four synthetic updates preceded the rejection. Evidence
is preserved. Corrected attempt `localizer-learning-d1716414-bc04-4ffd-9dbd-ab5e22f21dc5` passed:
20-step trajectory, 40 total updates including restart/comparison, loss 1.485633 → 0.703371 and exact
CPU resumed weights/reloaded predictions. SIGTERM after step 4 tested fresh-process recovery.
[Full results, hashes, test counts and limitations](capstone/operations/LOCALIZER-LEARNING-HANDBACK-2026-09-28.md).
Retain scratch model, binary target and verified geometry; next measure MPS and bind the production
run/checkpoint roots before freezing the real smoke recipe. No real CT or protected evaluation used.


## 2026-09-28 — Capstone engineering diagnostic: MPS resource profile

Pre-execution [plan](capstone/operations/LOCALIZER-RESOURCE-PROFILE-PLAN-2026-09-28.md), D-272.
Synthetic only, no CAP-EXP real-data launch. Package
`localizer-resource-3eeec52b-d8e6-4451-9db1-f2453558adff` passed on its first attempt: two warm-ups,
six measured 96³ updates (median 0.73616 s), four CPU-stitched full-volume inference passes
(0.37–0.48 s each), diagnostic checkpoint save/reload and one resumed update. Automatic CPU fallback
was disabled; reload probability difference was zero. No raw source reads or external writes.
[Full evidence and provisional budget](capstone/operations/LOCALIZER-RESOURCE-PROFILE-HANDBACK-2026-09-28.md).
Retain 96³/batch-1/fp32 for the candidate local smoke; do not enlarge the scope from this result.
Next bind the real cohort/MPS/run/checkpoint path and verify keeper restore before freezing CAP-EXP.


## 2026-09-28 — Qualified-input bridge and backup/recovery diagnostic

Pre-execution [plan](capstone/operations/LOCALIZER-RUN-BRIDGE-PLAN-2026-09-28.md), D-273. First attempt
`localizer-bridge-82b808b7-f79e-4850-9e98-53ad3829de08` failed before case reads/checkpoint writes on
the macOS internal Data mount heuristic. Native mount-table verification corrected the check; failure
is preserved. Successful attempt `localizer-bridge-447b7a35-9f76-415c-8c7c-dc8259834e05` verified
both cases' MPS forward path with no changed weights, two synthetic updates, external checkpoint,
independent internal backup, fresh-process restore with primary reads refused and a third synthetic
update. Restored fixed-probe probability difference0; overall50.58s;1,062 native tests pass.
[Full receipts, limits and findings](capstone/operations/LOCALIZER-RUN-BRIDGE-HANDBACK-2026-09-28.md).
No real-data training happened; rehearsal weights are excluded from future initialization.

## CAP-EXP-001 — Two-case scratch pancreas-localizer smoke

**Status: completed under D-275; mechanics passed, learning criterion failed.** See the result entry below.
Pre-launch design record: [Finalized launch design](capstone/operations/CAP-EXP-001-LAUNCH-PLAN-2026-09-28.md)
records exact cohort/recipe pins, scratch SegResNet, seed42,96³/batch1/fp32, AdamW0.003/cosine100,
100-update ceiling, before/after full-volume loss/Dice/native-grid review, checkpoints every25 and
terminal independent backup/restore. Limits:600s updates,1,200s total,16GiB memory,1GiB output reserve.
The bounded update/evaluation/export executor is complete and synthetically verified under D-274.
The specific pinned request awaits actual launch approval. No real experiment result/start is claimed.


### D-274 executor rehearsals — synthetic engineering evidence, not CAP-EXP-001

[Plan](capstone/operations/LOCALIZER-EXECUTOR-PLAN-2026-09-28.md) was recorded before execution.
Three successful, preserved native two-update rehearsals verified the initial path, added timing/
memory reporting, then independent update-phase supervision. They used invented volumes and fresh
scratch weights; no real source payload was trained. All run IDs, receipts, test corrections and
exact controls are in the [handback](capstone/operations/LOCALIZER-EXECUTOR-HANDBACK-2026-09-28.md).
Final run `f3f2512d-8a34-4b72-bf3e-a1bd449e9a3c`: mean full-volume loss1.603314→1.245815,
Dice0.016713→0.855610; native masks/contact sheets checked, independently restored probe difference0.
17.54s overall, sampled RSS1.30GiB and overlapping MPS driver2.31GiB.1,074 native tests pass.

Retain exact100-update recipe for the real smoke; change only the explicitly approved data mode,
real qualified input binding and horizon/cadence from the two-step fixture. Do not reuse rehearsal
weights. Request `f0943201-0e6d-4c7d-b140-61c7bb4f1efa` is prepared and pending; earlier
`b8756c5a-fa82-4506-8e6a-7924c71a995d` is superseded by the final source revision. The next question
is whether qualified CT targets also support finite tiny-set learning and recoverable outputs.
Actual launch is the remaining decision; neither learning nor generalization on CT is claimed.

### CAP-EXP-001 launch authorization — D-275

Quinton approved the exact prepared request `9b54a25d3ad014ca325464d35046496357f2e7969c9f4b2ddbd04e1ba2196452`.
Source/environment/plan bindings rechecked unchanged. Execute one fresh scratch attempt under the
frozen100-update/600s-update/1,200s-total limits; retain and report failure/null learning as well as
success. Authorization SHA `d7d5adfb333a1bb79364676b1a460f465eb1871d58c2d5a0d768ef9ee5520207`.
This entry records authorization before execution, not a successful outcome.


### CAP-EXP-001 outcome — completed, null foreground learning

[Full result and evidence](capstone/operations/CAP-EXP-001-RESULTS-2026-09-28.md).
One exact authorized run `localizer-smoke-c5f0d7d6-47f6-455b-adb7-e70c63d71bd3` completed100 updates
(50/case), full-volume before/after evaluation and all scheduled checkpoints. Receipt
`a470008bf2bf45cda5f3aaf1de451c64efe3b17687227486d750f232ca26f34a`.

Mean full-volume loss1.545844→1.026209, but mean foreground Dice0.000976→0; both cases have empty
final masks. **Mechanical checks passed; preset learning indicator failed.** Backup and fresh-process
MPS recovery passed, fixed-probe difference0. Total234.25s, update phase173.98s, sampled RSS3.35GiB;
overlapping MPS driver2.31GiB. Four overlays inspected and export geometry/binary checks passed.

Sampling selected44 foreground centers/56 background centers, so no all-background-center failure.
Even a patch containing the entire target has at most0.315%/0.375% foreground in these cases. Class
imbalance/optimization/horizon are hypotheses, not proven causes. No probability-distribution or
per-class gradient diagnosis is claimed from hard masks. Keep cases and protected roles unchanged.

Next recommendation: same-case controlled optimization diagnostic with probability/per-class-loss/
patch-composition telemetry, then a single-factor comparison such as lower LR. Freeze a separate
CAP-EXP-002 plan before compute; no automatic extension, restart or new run is authorized/launched.
Retain this null result, frozen recipe and evidence as the baseline for that discussion.

### D-276 pre-run optimization investigation plan

Read-only follow-up to CAP-EXP-001, not a new training experiment. Replay its100 crops and inspect
steps0/25/50/75/100 on cases3/26, separating foreground probability, CE/Dice terms and local logit
gradients.10 full-volume plus10 fixed-patch passes; zero optimizer updates. Bounds600s/16GiB/256MiB.
[Exact questions and limits](capstone/operations/LOCALIZER-OPTIMIZATION-INVESTIGATION-PLAN-2026-09-28.md)
were recorded before execution. Threshold points are diagnostic only; original Dice outcome stays0.


### D-276 optimization investigation outcome

[Findings](capstone/operations/CAP-EXP-001-OPTIMIZATION-FINDINGS-2026-09-28.md). Diagnostic
`localizer-optimization-2da20e71-6a17-4f1a-824d-8fb1a3337521`, receipt
`bc5ad7a35e8f39d726f7be1857b11056fc09934d3ac3ca3f833d854e3392b386`, completed51.45s with zero
optimizer updates. Replayed100 exact crops (all positive), inspected five checkpoints, reproduced
original endpoint metrics and verified unchanged weights.1,079 native tests pass.

Final mean foreground probability inside/outside target: case3 0.05694/0.02742, case26
0.07359/0.03053; global maxima0.08935/0.09675. This is weak separation beneath the original argmax
boundary, not literally zero foreground probability. Diagnostic threshold0.05 gives poor Dice
0.06125/0.02941 with extensive predicted foreground; no threshold was selected/promoted.
About99.6% of net loss decrease is accounted for by background CE contribution. On fixed positive
patches, CE's net common foreground-logit-shift derivative is positive and exceeds Dice's opposing
net derivative by35.4×/26.4×. This is not a per-parameter gradient dominance or AdamW-step claim.

Update next-experiment reasoning: prioritize a **single change to CE class balance**, retaining cases,
seed, LR/schedule, crops and100-update horizon, over the earlier tentative lower-LR-first idea.
[CAP-EXP-002 proposal](capstone/operations/CAP-EXP-002-PROPOSAL-2026-09-28.md) specifies equal per-class
CE means plus the unchanged foreground Dice term, objective-aware telemetry and bounded implementation.
Still a proposal, not a launched experiment or approved new recipe. Preserve CAP-EXP-001's null outcome.

### D-277 CAP-EXP-002 implementation and pre-launch verification

Version4 run/config/checkpoint identity now binds `balanced_ce_dice_v1`; legacy loss dispatch remains
exact and older checkpoint identities reject introducing a new objective. Every25 steps, telemetry
reports original and balanced objectives, probability/class contributions and both logit derivative
terms. The initial real scratch digest must match CAP-EXP-001 without loading its weights. A prepared
request is consumed through an exclusive launch-claim file to prevent duplicate execution.

Native suite:1,086 passed,2 existing warnings. The first finite-difference check used nondeterministic
float32 subtraction too close to its tolerance; replaced with fixed float64 inputs, not a looser test.
A pending-authorization test exposed changed error ordering; pending authorization again rejects
before experiment routing. Full-suite hash tests also inherited PyTorch high-water memory above512MiB;
in-process unit RSS is now deterministic, with explicit boundary and unchanged native subprocess tests.
Production memory limits were not relaxed.

Balanced two-update native rehearsal `localizer-smoke-b68b3f67-f4cc-4c46-80fd-d78466744ede` completed,
including intermediate telemetry, terminal persistence and fresh-process independent restore;
fixed-probe difference0. Receipt `f126ffe93d9237b0e1e6fa329a4864d576fce4c281cf3234361a155c39ebfb38`.
Whole rehearsal19.12s; no real CT training in this check. Its weights will not initialize the comparison.
Concrete [CAP-EXP-002 launch plan](capstone/operations/CAP-EXP-002-LAUNCH-PLAN-2026-09-28.md) is written
before request preparation/real execution. D-277 authorizes the bounded overnight comparison.

### CAP-EXP-002 prepared launch — D-277

Request SHA `51e7bf8afc41375284634532ae4c5e9ce26ee0c8aa83698ab3a8cf5cc5cb7287`, directory
`localizer-launch-request-1068e2ee-acdc-4f7a-8964-e76a51236227`. Source/environment match the verified
balanced native rehearsal. Authorization SHA
`5607d7766a385e3d7a57aca0a4b758dd2cd032e8fb99df4790b2f3b7ed557dbf` cites Quinton's D-277 overnight
scope. Launch one100-update comparison with no extensions; retain/report all outcomes.

### CAP-EXP-002 outcome and CAP-EXP-003 pre-run question

[CAP-EXP-002 result](capstone/operations/CAP-EXP-002-RESULTS-2026-09-28.md):100 updates completed;
mean balanced loss1.807322→1.166945, Dice0.000976→0.054974. Both predictions are roughly35× target
volume. Indicator failed; mechanics and independent recovery passed (probe difference0). Exact same
scratch digest and100 crop traces as CAP-EXP-001. Receipt
`c4991d60f045ba24ca29b02ccf0e6915134ad323de49425cf49216ffb1a4e65a`.256.10s overall.

D-278 uses overnight authority to test only LR0.0003 versus0.003 in a new100-step balanced run. Keep
all other settings and same preset endpoint/indicator; do not infer causality from weak intermediate
Dice fluctuations. [CAP-EXP-003 plan](capstone/operations/CAP-EXP-003-LAUNCH-PLAN-2026-09-28.md) recorded
before execution. No reuse of CAP-EXP-002 weights and no extension of its consumed request.

### CAP-EXP-003 verification before preparation

Registered experiment/config matching rejects substituting the lower LR into CAP-EXP-002's identity.
Native suite1,087 passed,2 existing warnings. Lower-LR synthetic rehearsal
`localizer-smoke-8cb87506-d018-4d7b-b48a-c567cacf98d9` completed19.46s, independent restore probe
difference0. Receipt `821afd8c473ebaff646224c890c8aab82ce472bb55d7309a3a2e60f6556fdf23`.
This is a synthetic routing/preservation check, not the real comparison and not reused initialization.

CAP-EXP-003 request `2e04914fa5daf14d153a2a674ac58ad0d770a937191c888cfb91bda06fa6958a` is prepared;
source/environment match its native rehearsal. D-278 authorization SHA
`34ada1dcc0b1b607e400127e8d0c90eab13a969916303b011b13153cb08ce245`. Launch exactly once under the
frozen600s update/1,200s overall budget and preserve the terminal result regardless of learning.

### CAP-EXP-003 outcome and final overnight question

[CAP-EXP-003](capstone/operations/CAP-EXP-003-RESULTS-2026-09-28.md) completed100 updates; mean Dice
0.109935, balanced loss1.807322→1.167455. Preset indicator passes, but masks remain16–18× reference
volume. Same scratch digest/all100 crops; recovery probe difference0. Receipt
`bc9131fd77383ed3e2ef5cdd095cfaf61637556ce0ce2451132b1657a83ab7f9`;257.74s overall.

D-279 selects one final overnight comparison:300 fresh lower-LR balanced updates with matched cosine
T_max300, same data/seed/loss/LR. This jointly changes duration and schedule horizon, not an identical
LR-prefix continuation. Stages0/75/150/225/300, same600s update/1,200s total ceiling. [CAP-EXP-004 plan](capstone/operations/CAP-EXP-004-LAUNCH-PLAN-2026-09-28.md) is recorded before compute. Stop after
reviewing this attempt; do not extend its budget or automatically continue the search.

### CAP-EXP-004 implementation verification

Balanced configurations may now explicitly contain at most300 steps; legacy configurations remain
capped at100. Real300-step use is limited to registered CAP-EXP-004 with cadence75. Tests verify
scheduler/checkpoint binding at the longer horizon, reject301 and preserve the legacy ceiling.
Full native suite1,089 passed,2 existing warnings. Final-route two-update synthetic rehearsal
`localizer-smoke-6884eb5c-1e5f-4581-9c3e-1010e1ab330c` completed22.96s and independently restored
with probe difference0. Receipt `d4666db453c74f4e64d93cb4102749bbf5270f26e6e9bc65f1574b612e14e9d8`.
Rehearsal verifies routing/operators/persistence; it is not a measured300-step real run. Same
600s update/1,200s total ceilings remain; no automatic extension if the real run hits its cap.


CAP-EXP-004 exact pre-launch request: `a4d5a6ab403f0da59645132f9c244afbd4d1abfa803c30cda9e1d0446a4c3bf3`; authorization D-279 `0c7c0471e3f07db0a364898d0cf0059d9951832e32645d9c01acb42b63af1c2c`. Native rehearsal source/environment match; one launch only, unchanged ceilings.


### CAP-EXP-004 final overnight outcome

[Full result](capstone/operations/CAP-EXP-004-RESULTS-2026-09-28.md): all 300 updates completed,
150 per case. Mean full-volume processed-grid Dice 0.000976 → 0.445999; balanced loss
1.807322 → 1.048862. Final reference recall 1.0 on both training cases, precision 0.281/0.293,
predicted volume 3.55×/3.42× reference. Preset minimal indicator passes; excess foreground remains.
Update phase 518.49 s, total attempt 577.91 s; no stop, extension or retry. Independent backup
restore at step 300 has fixed-probe difference 0. Source/environment and first 100 crop traces
verified unchanged/matching; 15 local and 21 terminal receipt members rehashed. Receipt
`1de1d74746ed79c365beadeee528a60fd6f3b61fc2b3d0e429a96ee8c9d39f2c`.

Training stopped after this planned final comparison. No checkpoint selected from intermediate
results and no generalization claim. [Morning handoff](capstone/operations/MORNING-HANDOFF-2026-09-29.md)
summarizes the implementation, evidence and proposed next discussion.


### September 29 — D-280 localization usefulness and candidate progression

[Plan](capstone/operations/LOCALIZATION-TARGET-2026-09-29.md) defined stronger per-case mask and
pre-mapping ROI screens before the new measurement. Read-only CAP-EXP-004 diagnostic reproduced
terminal counts/Dice with unchanged weights; two forwards, zero optimizer updates. Both masks have
one component, so largest-component cleanup is ineffective. With 10 mm requested physical margin
(12 mm realized on the grid), boxes retain 100% reference pancreas in 6.79%/5.38% of scan volume.
Masks fail the stricter fit screen; boxes pass the provisional ROI screen. This supports progressing
to varied cohorts rather than making two-case contour perfection a prerequisite. No final ROI policy
or full Stage 2 containment claim. Receipt
`c8ca6ce913f25a50a1104fcc1e6f1eaca8a6e695636492f3ddd9d335a49670f4`, 45.19 s.

Deterministic metadata-only candidate selection started at 16 train / 8 validation; eight validation
slots omitted three thin-slice strata. Preserved that package and revised to 16/12 before source reads
or model observations. Current receipt
`3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1` covers all available strata.
No eligibility granted. Header-only preflight read 56 files, 229,376 compressed bytes, no arrays;
8.22 s, receipt `950a113e6d18d795b90fe1bce7f68555a5e302b48e88de8b97b8651b9e4e73ad`.
Pair geometry agrees throughout; candidate 6350 has unknown units in both headers. Preserve it
pending evidence; old two-case unit assessments are not revoked by generic header flags.

Verification: 1,107 native tests passed; two existing warnings. The restricted initial suite failed
two existing process-monitor tests because /bin/ps was blocked; native rerun passed. The new header
test caught gzip buffering beyond the intended cap; max-output streaming zlib fixed it before reads.
No training or held-out model evaluation in this step. See
[results](capstone/operations/LOCALIZATION-PROGRESSION-RESULTS-2026-09-29.md) and
[next implementation packet](capstone/data/LOCALIZER-COHORT-EXPANSION-PACKET-2026-09-29.md).

### September 29 — D-281 role contracts and candidate content job

Qualification v2/cohort v3 add purpose-specific annotation use, protected role and explicit
optimizer/evaluator consumer checks. The old two-case runtime remains unchanged. Synthetic tests
caught and fixed a missing operation guard in the new entry point before real consumption.
Corrected the D-280 prose: 27 CT headers declare mm; all pancreas headers have unknown units.
The original pinned header facts were correct. Case 6350 still lacks either unit anchor.

The exact 56-file content request is prepared at
`outputs/prowl/localizer-content-request-6063bb74-a6d7-4234-a2e0-968877203044`, SHA
`29a365b6380d7d793cbb43390a827a75f874c197b2ec6151b3c3bd2384963f75`.
It captures plan/source/environment/selection and uses D-281's bounded evidence-only scope.
No optimizer, qualification promotion or candidate replacement. Preserve outcome and inspect all
alignment evidence before any real qualification decision.

Completed once: 56 files/28 cases, 44.65 s, peak RSS 4,626,972,672 bytes; all full gzip/finite CT/
strict-binary nonempty target/geometry checks passed. No exact CT-byte duplicates among candidates.
Case 6350 alone has an automated physical-unit hold. All 28 limited alignment sheets reviewed;
partial coverage in 4965/3717 and visible noise remain descriptive evidence, not easy-case filters.
Content receipt `224795f966a25733c7c1198e22dfa34fc525ef56be4e023ebdaa48ef8af0e3a9`;
review receipt `cb556a1086d665cb8584f9a8f404c89953445401bb9afc7c958f4e498560b8a4`.
1,122 native tests pass, two existing warnings. No new qualification/cohort or training yet.
[Results and next bounded implementation](capstone/data/LOCALIZER-CANDIDATE-CONTENT-RESULTS-2026-09-29.md).

### September 29 — D-282 expanded qualification and cohort freeze

[Scope and assessment](capstone/data/LOCALIZER-EXPANSION-QUALIFICATION-2026-09-29.md) pins the
28 reviewed candidates and permits purpose-specific private development use after qualification.
No model experiment or raw-source reread is part of this step. Implement the separate deterministic
expansion builder, preserve unrelated old holds and all split identities, then publish/replay one
bundle containing separate train/validation cohorts under the existing cohorts-area capability.

The first preparation produced 27 qualified/1 held and preserved all 13 old issues. It is retained at
`outputs/prowl/expansion-candidate-0050e048-34b8-4fe8-bd73-483edae47d52` but will not be published:
prepublication review added a frozen actual preparation timestamp for new issue records (replacing
a fixed date boundary) and extended producing-code pins for imported storage/policy controls.
A new preparation captures those corrections; old artifacts remain untouched. Native full suite
passed 1,131 tests before this small hardening; focused expansion tests passed again afterward.
The final publication/readback result will be recorded separately.

D-282 completed: final candidate
`outputs/prowl/expansion-candidate-1e1e331d-c385-410b-97ee-a6e1478a1e70` published as
`cohort-bundle:pants-localizer-expansion-0001:v1`, 20,827,107 payload bytes; completion
`7f5517feb00bef599261e432af9d7a293cf3f44086d1acbcba8de0e36bab0dcc`.
Fresh-process readback replayed the persisted package and returned 16 optimizer/11 evaluator
members, zero source arrays. 27 qualified, case 6350 held; all 13 prior issues and complete original
membership preserved. Validation lacks arterial/thin-slice coverage; no refill. Final full native
suite: 1,131 passed, two existing warnings, 16.19 s. Old runtime unchanged; no new training.
[Results](capstone/data/LOCALIZER-EXPANSION-FREEZE-RESULTS-2026-09-29.md) record exact pins.
Next: [expanded loader/preprocessing](capstone/data/EXPANDED-LOCALIZER-LOADER-PACKET-2026-09-29.md),
because 14 qualified scans exceed the old source-voxel limit and eight its compressed-file cap.
Those are runtime-boundary requirements, not evidence for dropping difficult or large cases.

### September 29 — D-283 expanded loader/preprocessing verification

[Exact job](capstone/data/EXPANDED-LOCALIZER-PREPROCESSING-JOB-2026-09-29.md) implements the next
D-282 input-readiness step. Separate v2 loader/preprocessing preserves v1, enforces role/permission,
checks full source bytes and projected allocations, and reports every frozen case. No model run.

Prepared request `outputs/prowl/expanded-preprocessing-request-2ad3c49a-58cf-45be-8ae2-7674667557c2`,
SHA `c9b07b7666f61777013193a0d8fbc7e25efa6a6da1456a0ad875f3f6f48f90f8`, pins source/environment,
recipe, capability and header-only projections. Exact 54 files total 684,668,314 compressed bytes;
maximum conservative projected output is 3,105,675 voxels, below the 8-million cap. Native tests
must pass before execution. Limits remain 20 minutes/16 GiB, 1 GiB compressed/4 GiB expanded,
256 MiB output and 100 GiB internal free floor. No held-case read, refill or automatic retry.

First attempt stopped on a review-sheet affine-list TypeError after first-case processing;
`expanded-preprocessing-41bcb797-9a69-44e8-ba04-21da7f6c8c20` is preserved incomplete. Supervised
180.92 s, exit 1, sampled peak RSS 1,848,770,560 bytes. Corrected the display conversion and added
a full synthetic three-row rendering regression. Also automated the manually verified live decoder
hash check against qualified lineage. No source or cohort change. Final native suite **1,146 passed**,
two existing warnings, 16.22 s. The recorded revised attempt uses new request
`expanded-preprocessing-request-39db165d-0d0e-432d-8806-1cbdc16fc5e9`, SHA
`810ff1bcfb7a39bab0717fc1fc89a37771343a8a3790145c345c9b6bd8b21e65`, same cases/recipe/budgets.

D-283 corrected diagnostic completed: 27/27, exact 54 files, zero failures/updates; 237.48 s,
peak sampled RSS 12,417,138,688 bytes. Round-trip reference Dice 0.8171–0.9553 (median 0.9285),
not model accuracy. All 27 sheets reviewed; partial/noisy cases retained. Receipt `8a9274a5815d6acfd466487e5d17c7c1d5f6fd5463dd1d9373daf155d3ab0bff`;
separate visual review receipt `f6314db209999bb282b37a236ea4312edd4df0c3aac7dc0b2cb3f1669fce82f7`. All 64 payload hashes and 54 source receipts verified.
[Results and next implementation](capstone/data/EXPANDED-LOCALIZER-PREPROCESSING-RESULTS-2026-09-29.md).
Next: expanded runner/resource/checkpoint readiness, then a frozen fresh scratch run.

### September 29 — D-284 expanded runner readiness

[Plan](capstone/operations/EXPANDED-RUNNER-PLAN-2026-09-29.md): bounded processed RAM cache,
role-specific full-volume evaluation and checkpoint identity/continuation. Native suite 1,154 passed
(two existing warnings,17.63 s). CPU synthetic resumed update matched exactly. First MPS synthetic
attempt stopped at a bitwise next-update parameter assertion; its sampling/loss equality had passed.
No real inputs were read. Investigate/report maximum float32 parameter difference; use an explicit
1e-6 absolute continuation tolerance with exact saved-state probe recovery required separately.
This is numerical continuation equivalence, not a claim of bitwise reproducibility on MPS.

Synthetic MPS follow-up passed: next-update parameter max difference 3.725290298461914e-9;
exact sampling/loss trace, four actual synthetic updates (one replayed continuation), three completed
steps in saved state. Checkpoint receipt `324f523042fc70a3f84db0f313374402ea5fa43d7691f470454cd35086317b8b`,
`outputs/prowl/expanded-synthetic-ee42cf80-2321-4b7f-a645-f12115ee55a4`.
Real forward-only request prepared at `outputs/prowl/expanded-profile-request-b9644313-c69e-4339-93c0-ae7c45207bac`,
SHA `e88dddb361b73092e693700ea1dc70d4287f399bce0f68034621b4fb5b067c8d`.
Frozen D-284 plan:54 files, complete16/11 cache and full-volume forwards; zero real updates.

D-284 profile complete:54 files/27 cases,200,844,985-byte cache,209.28 s load/verification,
15.45 s full-volume forwards,227.31 s supervised total,5.53 GiB peakRSS,zero real updates.
Profile receipt `0a5f3335a46beabed727b4f2d4f662d80043873c94636b399e1ae64d2e8d99da`.
Synthetic step3 and real-input step0 fresh-process MPS recovery probes both exact (difference0).
Both checkpoints independently published/backed up/restored byte-identically using registered
storage verification roots; detailed receipts in [D-284 results](capstone/operations/EXPANDED-RUNNER-RESULTS-2026-09-29.md).
Final native suite1,155 passed,two existing warnings,17.77 s. All15 profile payload hashes verified.
CAP-EXP-005 proposed288 updates/18 equal cycles; launch transaction/metrics/exports still to finish.
No new real training or case filtering; old two-case runtime unchanged.

### September 29 — D-285 expanded transaction preparation

[Exact design](capstone/operations/CAP-EXP-005-LAUNCH-PLAN-2026-09-29.md) fixes 288 updates,
evaluations0/144/288, checkpoints0/96/192/288, all27 final exports and independent backup recovery.
Implementation adds a separate executor and schema2 expanded run identity; old schema1 readiness
and two-case run behavior remain. CPU fixture transaction and injected step3 interruption pass;
last complete step2 checkpoint survives and no terminal is published after interruption. Empty and
fragmented masks retain explicit metrics. Next native synthetic rehearsal uses16/11 invented cases,
four updates, full evaluation/export/backup/primary-forbidden recovery. No real images or updates.

First complete native rehearsal passed: `expanded-execution-a9930a35-73ad-4c7b-b91b-8b5a5ee56711`,
receipt `bc7cb4cdfc874e1165da6a6d32bbafb469c38bae52898b41dc8d8837e0099c84`.
31 artifacts (three checkpoints,27 case exports,terminal) backed up and restored in a fresh process
with primary reads forbidden; fixed probe difference0. Total89.88s,peakRSS1,884,143,616 bytes.
Review then tightened cross-phase storage accounting: the recovery process now reuses the initial
worker's absolute quota ceilings, rather than recomputing an increment after backup. The first
rehearsal remains valid evidence for its source snapshot; rerun the final source after this change.

D-285 final source:1,170 native tests passed,two existing warnings,27.14 s. Final synthetic MPS
rehearsal `expanded-execution-8801ec48-45ca-4b47-a5e2-2ba46c0a09fd` completed in87.36 s,
peakRSS1,998,815,232 bytes; all31 artifacts independently restored with primary reads blocked,
probe difference0. Receipt `748ad87d5100b2d42277408ec77d1e39d6ae60bc0320ccfd1c3e5db4737ecda6`;
all14 evidence-file hashes checked. Zero real updates/source arrays.

Exact CAP-EXP-005 request frozen at
`outputs/prowl/expanded-launch-request-7d7dea23-ed27-4d00-9f11-8798f79e70cc`, SHA
`2fa5f7f20916fb047ddcc54c3aede63e5f1c57566227cec1ef07a1d9756ae456`.
Source/environment match the successful rehearsal; unapproved authorization rejected, no claim.
[Final handback](capstone/operations/EXPANDED-EXECUTOR-HANDBACK-2026-09-29.md) records exact
settings and limits. Next: Quinton's approval for this specific288-update launch, then one bounded
run and all-case training/validation review. No further input qualification is needed for this run.

### September 29 — CAP-EXP-005 authorized launch (D-286)

Quinton approved the exact request: “Yeah, go for it.” Code/environment preflight still matches.
Request `2fa5f7f20916fb047ddcc54c3aede63e5f1c57566227cec1ef07a1d9756ae456`;
approval `outputs/prowl/CAP-EXP-005-APPROVAL-2026-09-29.json`, SHA
`578b42bb36e6adfcc87e74716177c82938dcb3f7f6543054c2cbd3082066f258`.
Run the frozen 288-update plan once, preserve all outcomes, then review all-case metrics/exports
and independent recovery. No recipe or source-code changes before/during execution.

CAP-EXP-005 completed exactly288 updates/18 per training case, no retry/extension. Mean full-volume
training Dice0.0006→0.0647→0.1262 and validation0.0009→0.0845→0.1512 at0/144/288.
All27 predictions nonempty;0 mask-fit passes; ROI screen13/16 train,9/11 validation. Large excess
foreground remains (median volume ratio13.08/12.56); all five ROI failures exceed the scan-volume
cap. Difficult/partial/noisy cases retained; no model-performance eligibility filtering.
605.85s total,247.46s update phase,peakRSS9,245,540,352 bytes. All32 artifacts backed up/restored;
primary reads forbidden in fresh recovery, fixed probe difference0. Job receipt
`13ebf8e9423d60d62ef105f65eef088331268cff9df9c656d8650216849ef2ed`.
All-case derived metrics and27 overlays reviewed; [full results](capstone/operations/CAP-EXP-005-RESULTS-2026-09-29.md).
Next hypothesis: longer fresh duration/schedule horizon, same cohort/objective/initialization.
576 updates needs a separate bounded configuration and approval; none launched. Code unchanged.

### September 29 — CAP-EXP-006 sustained learning plan (D-287)

Quinton approved proceeding after the training regroup. Before compute: [frozen design](capstone/operations/CAP-EXP-006-LAUNCH-PLAN-2026-09-29.md).
CAP-EXP-005 both-role improvement motivates2400 fresh updates on the same16/11 (150/train case),
keeping objective/model/preprocessing/sampling fixed. Duration AND cosine horizon change.
Final validation mean Dice is primary (+0.05 practical bar), with mean recall drop<=0.02 and no
additional boxes below99.5% reference coverage; report per-case/volume/ROI tradeoffs. No best-step
selection, data filtering or claim of significance.50min update/60min total; retain every scheduled
checkpoint/backup and evaluation. Implementation/rehearsal and exact request freeze precede launch.

CAP-EXP-006 verification before launch: native suite1180 passed/two upstream warnings; initial
sandbox run1177 passed/two process-monitor permission failures, corrected by native execution.
New tests cover301-update checkpoint continuation, sustained-budget/legacy caps, exact controls,
evaluation journal and backup-failure stop. Synthetic MPS rehearsal completed4 fixture updates,
31 independently backed/restored artifacts, fixed-probe difference0,100.58s,peakRSS1.76GiB.
Receipt `e42692ed6ac67728fa09c3f317e1ef7a95834ad35da2836e65241e4a69dbf999`.
Frozen request `expanded-launch-request-bb413397-e1a1-463d-8aba-1edf0887129c`, SHA
`024fb5b495d78a4ad4686846ec113c3ecc9d8c023cd298a189cafc3c304cf01e`.
Exact approval record binds D-287 authorization to this request; no second confirmation required.


### CAP-EXP-006 outcome — completed, tighter masks but validation coverage failure

[Full result](capstone/operations/CAP-EXP-006-RESULTS-2026-09-29.md).2400 updates/150 per each16
training members, zero validation optimizer members. Final train/validation Dice0.7481/0.4529;
median volume ratios1.50/1.09. Validation recall falls0.9490→0.4606 versusCAP-EXP-005;7 validation
boxes newly miss99.5% reference coverage. ROI screen16/16 train,2/11 validation;strict fit1/27.
Primary Dice bar+0.30168 passes; both coverage safeguards fail. **Tradeoff, not accepted localizer
improvement.** Between1600 and2400 train Dice rises0.674→0.748 while validation falls0.470→0.453;
validation loss rises1.778→2.252. Consistent with limited-cohort overfitting/generalization gap,
not a unique causal diagnosis or proof of convergence. No retrospective best-step selection.

2444.27s total/2062.75s update phase,peakRSS8.26GiB. All35 artifacts independently backed/restored,
terminal step2400,fixedprobe difference0. All27 overlays reviewed; difficult cases retained.
Receipt `900c05364910507ba4f927733f1bf3225a900c85fabc4a99a6bcba306c0c9567`.
Reporting-only matplotlib absence retained in review log; no dependency changes or reruns.

Next recommendation: bounded read-only coverage-failure audit, then broader representative
qualified cohort and a newly frozen controlled experiment. More duration alone on these16 is
not the priority. No additional launch, automatic continuation, eligibility change or final-test use.


### September29 — D-288 CAP-EXP-006 coverage inspection

[Plan frozen before reads](capstone/operations/CAP-EXP-006-COVERAGE-INSPECTION-PLAN-2026-09-29.md).
[Results](capstone/operations/CAP-EXP-006-COVERAGE-INSPECTION-RESULTS-2026-09-29.md).
No training or inference.54 qualified source files/27 pairs and54 saved005/006 exports independently
checked on native grids. Mean validation recall0.9492→0.4594;006 native Dice0.4525, close to processed.
No shape/affine/units/content/role mismatch found. All27 source overlays reviewed. Single-component
misses and distant-FP box inflation are distinct; deleting components cannot fix7 deficient boxes.
278.46s,peak3.94GiB,receipt `e9c74c6972d98570c8b047f60a40e8a5a319be6d994f69207d30b93eb1aa8da1`.

Important separate correction: prior scan_fraction included zero-padded tensor volume. Same-box
mapping to acquired source bounds changes5 CAP-EXP-005 size checks. Additive source_crop_geometry
and positive acquired-volume size gate now emitted by evaluator; original fields explicitly labeled
and historical artifacts unchanged. This does not explain/reverse006 validation recall failure.
Source audit and later metadata correction have separate pinned evidence; no audit rerun.

Next proposal:128 train/48 development-validation candidates, retaining prior cases/holds and adding
coverage floors plus proportional common-stratum exposure. Not selected/qualified/frozen. Consider
an explicit probability-only audit to distinguish low-confidence coverage from near-zero scores
before choosing an operating policy; hard masks cannot answer that. No new launch/automatic resume.


### September29 — D-289 preparation after CAP-EXP-006

Prepared a128 train/48 development-validation metadata candidate expansion, retaining all28 prior
candidates and unresolved6350. Hybrid coverage-floor/proportional selection adds148 cases without
using model scores or presumed label quality. Selection is not qualification or executable membership.
Exact metadata replay passes;1,211 native tests pass. No new source payloads or training.
See [candidate results](capstone/operations/LOCALIZER-CANDIDATE-EXPANSION-RESULTS-2026-09-29.md).
The [fixed probability-audit plan](capstone/operations/CAP-EXP-006-PROBABILITY-AUDIT-PLAN-2026-09-29.md)
is the next diagnostic on006; no inference has run and no threshold has been selected. Data breadth
remains the leading training intervention, with exposure/compute budget deferred until qualification
and resource profiling. Existing006 evidence and consumed request are preserved.


### September29 — D-290 fixed probability audit, no training

CAP-EXP-006 terminal masks exactly reproduced on all27 qualified cases; model unchanged and no
optimizer steps. Five predetermined thresholds show only partial validation recovery: mean processed
recall0.4606 at0.50 to0.6047 at0.01, with mean Dice0.4529→0.4275 and larger false foreground/crops.
All11 baseline-missed-reference probability medians are<0.006. No threshold was chosen or added.
Broader training exposure remains the leading next intervention; this does not establish its causal
sufficiency.1,220 native tests pass. [Full results and all-case evidence](capstone/operations/CAP-EXP-006-PROBABILITY-AUDIT-RESULTS-2026-09-29.md).
Next prepare qualified expanded inputs via the exact148-case/296-file header job (currently prepared,
not executed), bounded qualification, cohort freeze and new consumer/resource checks. No training
request is pending; CAP-EXP-006 and the probability audit requests are consumed.


### September29 — D-291 candidate header preflight, no training

148 new candidates/296 bounded headers inspected; all CT/target header grids match.14 CT unit
questions remain unresolved and5 grids exceed64M voxels. All candidates preserved. No voxel arrays,
qualification or training;1,230 native tests pass. [Results and15-batch content proposal](capstone/data/LOCALIZER-EXPANSION-V2-HEADER-RESULTS-2026-09-29.md).
Next implement/test a versioned content-evidence consumer and run the first standard pilot; larger
cases need separately tested diagnostic resource limits. Do not substitute candidates based on
units/resource difficulty or change the existing16/11 training consumer.


### September29 — D-292 content pilot, no training

Batch01's16 new training candidates/32 source files pass integrity, finite CT, matching geometry and
nonempty strict-binary checks. All16 limited alignment sheets reviewed. Inferior scan-boundary
contacts56/150/1250/1396/1462 remain explicit visible-target observations, not exclusions.41.53seconds,
peak3.42GiB;1,242 native tests. No qualification or model execution.
[Evidence and next recommendation](capstone/data/LOCALIZER-EXPANSION-V2-CONTENT-PILOT-RESULTS-2026-09-29.md):
continue remaining nine standard batches/127 cases within unchanged caps, then separately verify
five larger cases. Keep all176 candidate identities and unresolved units; complete qualification,
cohort freeze and consumer/resource checks before training.


### September29 — D-293 complete expanded content evidence, no training

Nine remaining standard batches/127 candidates and five separately gated large cases completed.
Synthetic96M allocation/decode rehearsal passed at3.48GiB; largest real peak5.20GiB.132 cases/264
files,246.59seconds summed real job runtime. All124 available alignment sheets reviewed; eight empty
references have no target-centered sheet and remain unresolved. No gross displacement flagged in
limited overview; noise, sparse references and source-face contacts preserved as observations.

All176 candidate identities and roles reconciled against frozen selection;8 empty-reference and15
CT-unit holds (including old6350),153 without automated content holds (113train/40validation).
These counts do not grant qualification. No exact compressed-CT duplicates across176; biological
identity remains unresolved.1,264 native tests; no model/optimizer/eligibility changes.
[Results and evidence](capstone/data/LOCALIZER-EXPANSION-V2-CONTENT-RESULTS-2026-09-29.md).
Next record supported purpose-specific qualifications, preserve every hold/issue, freeze/replay new
role cohorts and profile a separately versioned consumer before training. All14 requests consumed.


### September29 — D-294 broader purpose qualifications and role freeze, no training

153 positive qualifications (113 train/40 development-validation),23 held and176 original candidates
accounted for. The new immutable bundle published and independently resolved exactly. All23 prior
issues and28 prior annotation identities retained. Difficult and all five large scans remain eligible
for visible-reference localization; whole-organ completeness is not established. Six arterial/thin-slice
validation cases fill the previous gap, but this stratified development cohort is not population data.

1,284 native tests pass. Two slow unpublished preparations were stopped for bounded validation
optimizations; a completed intermediate preparation was superseded for an additional JSON-shape guard.
All such history is documented; no failed or superseded attempt published. No raw arrays or model work.
[Results](capstone/data/LOCALIZER-EXPANSION-V2-FREEZE-RESULTS-2026-09-29.md) retain hashes and replay.
Next implement the [consumer packet](capstone/data/LOCALIZER-EXPANSION-V2-CONSUMER-PACKET-2026-09-29.md):
306 permitted source files, preserved3mm starting recipe, verified preprocessing and measured cache/
streaming/CPU/MPS costs before a fresh scratch-run request. Existing16/11 consumer unchanged.


## 2026-09-29 — D-295 broader input verification (no training)

The113/40 frozen cohort now passes a separately versioned role-safe loader and3mm preprocessing.
All306 exact source files checked;153 limited transformation sheets reviewed; all targets nonempty.
Native suite1,307 passes. Successful job durations sum448.307s; maximum CPU RSS6.57GiB; tensor
payload1.07GiB, not a retained cache or MPS budget. Five large scans retained and handled separately.
Initial pilot failed before raw reads because the store validation callback returned the wrong report;
fixed,tested,rehearsed and explicitly retried with a new capability attempt, preserving old evidence.
No model inference/updates or new CAP-EXP launch. All15 successful requests consumed.

Important null/limitation: nonempty does not mean faithful supervision. Tiny boundary reference6110
has only0.45956 native round-trip recall;2727 has0.76471. These are preprocessing reference metrics,
not model results. Keep the cases and investigate target representation before training; do not filter
them to improve scores. Next: role-safe cache and no-update MPS runner/resource/recovery integration,
with focused tiny-target checks alongside it. The3mm recipe and old16/11 runtime remain unchanged.

Evidence: [D-295 results](capstone/data/BROAD-LOCALIZER-PREPROCESSING-RESULTS-2026-09-29.md).


## 2026-09-29 — D-296 target-fidelity diagnostic (no training)

New two-label job6110/2727 exactly reproduces D-295. Nearest2mm improves native-reference recall
from0.45956/0.76471 to0.90441/0.88235;1.5mm recovers both1.5mm-source references exactly.3mm
foreground-center splat increases recall but expands volume2.721×/2.588×,so it is not adopted.
This supports coarse-grid representation loss,not a reason to remove tiny/partial cases. No CT/model
reads or optimizer updates.11.806s/1.26GiB;1,312 native tests pass. Development-validation exposure
for preprocessing debugging is recorded;these are not model/generalization metrics.

Header-only projections across all153 cases: uniform2mm would exceed current8M output ceiling for15
members,maximum15.046M,and~3GiB tensor payload upper bound. Next propose/test a separate16M candidate
output envelope and qualify2mm across the cohort before choosing the final cache recipe. Preserve3mm
baseline and all cases;no automatic production recipe or launch change.

[Full findings and next qualification scope](capstone/data/TARGET-FIDELITY-RESULTS-2026-09-29.md).

### September 30 — D-297 uniform 2 mm input qualification (no model run)

Following the tiny-reference investigation, tested a separate 16M-output recipe and qualified all
113 train/40 development-validation cases through 15 bounded requests. All 306 files passed,
153 sheets reviewed; 1,337 native tests. Mean reference Dice train 0.916724→0.943803, validation
0.909228→0.947150; mean recall 0.916135→0.944986 and 0.915132→0.947109. Dice improved in148/153,
recall147/153; all regressions and difficult cases retained. 6110 still has imperfect reference
recovery. These are reference-resampling measures, not model performance.

511.861 seconds summed job time; 6.664 GiB peak CPU RSS. Tensor payload2.902GiB,2.711×3mm.
No tensor cache/model updates. Optional matplotlib plot failed because dependency is absent;
no dependency changes. Next: physical-context/MPS profiling, role-safe cache and independent
checkpoint recovery before a fresh bounded training request. A96³ patch now spans192mm rather
than288mm, so old patch settings cannot be treated as the same physical context.

[Full results](capstone/data/TWOMM-LOCALIZER-PREPROCESSING-RESULTS-2026-09-30.md).

### September 30 — D-298 synthetic context profile

Compared96³/144³ at nominal2mm using the same model/balanced loss. Both passed finite updates,
CPU-stitched forward and same-process reload (probe delta0). Median update0.8253/2.6839s;
same invented volume inference2.1263/3.1594s; sampled MPS driver2.306/4.822GiB. Recommend144³
candidate for preserved288mm input span. This is not a learning comparison or real run, and fixed
convolution receptive-field scale still changes. Production96³ guard remains. Native1345tests pass;
initial sandbox supervisor failures retained. Next versioned cache/adapter, fresh bounded real
zero-update profiling and independent recovery. No training launch or model promotion.

[Evidence and limitations](capstone/operations/LOCALIZER-CONTEXT-PROFILE-RESULTS-2026-09-30.md).

### September 30 — D-299 persisted cache and patch mechanics (synthetic only)

Implemented separate4GiB payload persisted cache and144³ adapter.1,379 native tests pass;
synthetic two-role cache reopens and exactly replays four completed-step crop boundaries.
Validation cannot reach the optimizer sampler; extra patch padding is excluded from center
selection, while existing preprocessing padding remains eligible. This changed sampling policy
must be recorded with the future experiment. No optimizer/state recovery claim yet.

Retained D-297 reports yield proposed113/40 binding and153 temporary-padding projections,
all<=16M; no raw reads or filtering. Next fresh supervised real cache build, zero-update MPS,
source-grid/padding checks and independent checkpoint recovery before an exact training request.

[Results](capstone/operations/TWOMM-CACHE-ADAPTER-RESULTS-2026-09-30.md).

### September 30 — D-300 real persisted input cache (no model run)

Built8-case pilot then145remaining under fresh single-use authority; all306 source files verified.
Assembled full113train/40development-validation cache from retained parts with zero new raw reads.
Every final serialized image/label hash matches its part; every target count and transform agrees
with D-297. No cases dropped, no23hold changes, no model forward/updates. Final cache2.903GiB;
peak10.967GiB;1,388 native tests. Full reopen1.784s on warm OS cache, not cold-disk throughput.
Next versioned144³ session/checkpoint qualification, fresh zero-update MPS run and independent
backup recovery before a finite training request. All three D-300 requests consumed.

[Cache identity and evidence](capstone/operations/TWOMM-CACHE-BUILD-RESULTS-2026-09-30.md).


### September30 — D-301 runner/checkpoint readiness (synthetic only)

Game plan: separate144³ cache-bound session; test strict checkpoint refusal and synthetic next-update
replay, then exercise actual SegResNet/MPS and independent backup recovery. No CAP-EXP launch.

Outcome:1,406 native tests. Step2 independently restored in a fresh process with primary reads blocked;
probability delta0,next-crop trace exact,next-loss delta0,next-weight maxdelta7.45e-9. Four synthetic
optimizer calls total; no real cases. Producer/recovery13.094/6.425s,peakRSS1.028GiB, sampled driver4.822GiB.
All attempts passed; retained receipts and limitations in
[session results](capstone/operations/TWOMM-SESSION-RESULTS-2026-09-30.md).

Next: implement/test and freeze8-case real-cache inference/export pilot, then145remaining. This
qualifies actual input resource/geometry behavior before training; it does not establish learning.
Native-reference evaluation access still needs an explicit bounded pathway; processed targets are
not substitutes for original references. No model promotion or automatic training continuation.

### September30 — D-302 cached inference pilot game plan

Exercise the eight retained edge cases through the new144³ session, export predictions to their native
grids, verify unchanged initial weights, and independently restore an actual-cache-bound step0
checkpoint. No optimizer updates or native-reference scoring. This checks resource and geometry
readiness; random initialized predictions cannot support a model-quality conclusion.

Exact cases, controls and safety limits: [pilot plan](capstone/operations/TWOMM-INFERENCE-PILOT-PLAN-2026-09-30.md).
Tests precede a fresh single-use source/environment-pinned request; failures remain evidence.

D-302 outcome: single native attempt passed all eight inference/native-export checks and independent
actual-cache-bound step0 recovery (probe delta0). Weights unchanged throughout; no real updates or
raw reads. Profile/recovery workers53.480/3.942s,peakRSS4.498GiB;31 output members rehashed.
1,437 native tests pass. [Full evidence](capstone/operations/TWOMM-INFERENCE-PILOT-RESULTS-2026-09-30.md).
Remaining145 projection ~8.2minutes including reserve supports retaining proposed20minute/16GiB/4GiB
limits, subject to a separate tested/frozen continuation request. This is engineering readiness,
not a localization or native-reference accuracy result. No automatic training/model promotion.

### September30 — D-303 full-cache inference continuation game plan

Run the exact145-member complement of the passing eight-case pilot through the same initialized144³
model and native export/recovery path. Bind pilot evidence and fresh source/environment; consume a
new request, never the pilot. Reconcile153 unique members and identical initial weights. Preserve all
holds and observations. [Plan](capstone/operations/TWOMM-INFERENCE-CONTINUATION-PLAN-2026-09-30.md).
This is zero-update readiness, with no native-reference quality claim or real training launch.

D-303 outcome: single continuation attempt passed145 cases; all153 original113/40 members reconcile.
Independent review rehashed337 package files and reopened153 native exports. Weights unchanged and
independently restored probability probe exact. Profile/recovery409.212/4.418s,peakRSS3.031GiB;
1,460 native tests. No raw source reads or real updates; both inference requests consumed.
[Full results](capstone/operations/TWOMM-INFERENCE-FULL-RESULTS-2026-09-30.md).

Next: target-only native-reference reader and96M-safe metrics that retain oversized prediction failures,
then the bounded training executor. Existing cached CTs suffice; no new cohort selection is needed.
The [completion packet](capstone/operations/TWOMM-TRAINING-COMPLETION-PACKET-2026-09-30.md) proposes
300updates and45minutes for a first broader diagnostic, subject to implementation/rehearsal and exact
launch freeze. No learned-model improvement or promotion is inferred from initialized predictions.

### September30 — D-304 native-reference baseline game plan

Score existing initialized native exports against exact qualified original pancreas references, using
one target-only pass in8+145 cases and a new96M metric path that retains dense/empty failures. Preserve
all153 members, original23 holds and partial-reference caveats. Tests precede frozen real read jobs;
no CT/model/optimizer work. [Plan](capstone/operations/NATIVE-REFERENCE-SCORING-PLAN-2026-09-30.md).

D-304 outcome: both native jobs passed;153 labels,21,942,279compressed/4,398,868,031expanded bytes,
zero CT reads or model/optimizer work.12.078s pilot +67.179s continuation,peakRSS5.817GiB;1,491 tests.
All113/40 retained. Initialized native Dice0.001700/0.002053,recall0.018415/0.024605;ROI0/113 and0/40.
Boxes cover nearly the entire scan, explaining100% box-reference coverage without useful localization.
Three dense predictions and five >64M grids remain in the results. No case/threshold selection or
trained-model claim. [Evidence](capstone/operations/NATIVE-REFERENCE-SCORING-RESULTS-2026-09-30.md).

Next: implement the actual bounded training loop and new checkpoint/authorization/progress contract,
rehearse synthetic recovery, then freeze the exact request. Native-reference scores are available for
a matched initialized baseline; reusing them requires explicit equality checks. Repeated evaluation
reads require a new stage-specific budget because both D-304 source-read requests are consumed.

### September30 — D-305 training transaction rehearsal

[Game plan](capstone/operations/TWOMM-TRAINING-TRANSACTION-PLAN-2026-09-30.md): separate144³ training
identity and deterministic per-pass sampling, native before/mid/after scoring, completion-last journal,
strict nonzero checkpoint and independent recovery. Native invented fixture includes a15,007,744-voxel
volume. Preserve113/40 memberships and23holds; no real-data updates or fresh source reads. Three
producer updates plus one restored replay and one deliberately interrupted update. The exact real
launch remains to be frozen after the complete transaction/resource checks.

D-305 outcome: separate transaction/recovery/keeper path passes1,539 native tests. Three evolving
native synthetic rehearsals passed and are retained (15 total synthetic update calls including replay
and interruption injection). Final source-matched worker total46.010s,peakRSS2.570GiB/driver4.853GiB;
intermediate/terminal probes exact,next-update weights3.73e-9. Six keepers independently restored;
48 final package files rehashed. [Results](capstone/operations/TWOMM-TRAINING-TRANSACTION-RESULTS-2026-09-30.md).

CAP-EXP-007 is prepared,not launched:300updates,113/40,144³/2mm,fresh baseline and terminal plus
validation at113/226,45min total. New exact386-label read scope,no CT reads. Request SHA
`b13ebbce1731090a65dd5fe6c8327963f8e50203e39c25aa8ee6c88f903d85b3`;
[launch design](capstone/operations/CAP-EXP-007-LAUNCH-PLAN-2026-09-30.md).
Metadata preflight and cache verification passed; no real update or original source-array read.
Keepers cover checkpoints/evaluation records; native masks remain explicitly unbacked derived local
scratch. Next authorize this exact request,run once,and inspect native coverage/size alongside Dice.

### September30 — CAP-EXP-007 authorized launch (D-306)

Quinton approved the exact prepared request: “Great, I approve this exact run.” Launch once from
fresh seed42 under [the frozen game plan](capstone/operations/CAP-EXP-007-LAUNCH-PLAN-2026-09-30.md):
300updates,113train/40development-validation,144³/2mm,balancedCE+Dice,AdamW0.0003,cosine schedule;
full baseline/final and validation at113/226.45min total including recovery,16GiB memory,4GiB outputs,
AC/100GiB free floor,386 label-only reads. No extension or model promotion. Record learning and
native coverage/size failures as well as Dice. Exact request SHA
`b13ebbce1731090a65dd5fe6c8327963f8e50203e39c25aa8ee6c88f903d85b3`.

CAP-EXP-007 outcome:all300updates and386 native evaluations completed,33.082min,peakRSS5.638GiB,
driver4.799GiB. Full baseline reproduced all153 D-304 metric records. Validation mean Dice
0.002053→0.061027→0.082020→0.098701 at0/113/226/300; recall0.024605→0.959212→0.984972→0.982700.
Final training Dice0.097323,recall0.978471. Validation mean crop fraction0.42185 and median volume
ratio18.50×;ROI only1/40 (train2/113). Coverage remains high, but excess foreground prevents useful
localization for most cases. Training7604 still has box coverage0.92208; tiny6110/2727 stay included.
All300 exposures replayed:39members twice,74 three times;146foreground/154background centers.

Nine keepers independently restored with primary reads blocked,terminal probe0.805 package files and
386exports verified; eight selected sheets inspected. No original reference reread in posthoc review,
new CT read,filtering,qualification change or model promotion. Source unchanged;1,539-test baseline.
[Full results and immutable receipts](capstone/operations/CAP-EXP-007-RESULTS-2026-09-30.md).
The request is consumed and no run remains active. Recommend a longer fresh duration/schedule
comparison on this same cohort with explicit coverage safeguards; no next experiment is authorized.


## 2026-10-01 — CAP-EXP-008 game plan (D-307)

Quinton authorized running the proposed fresh1,200-update experiment after the strategy discussion.
[Design](capstone/operations/CAP-EXP-008-LAUNCH-PLAN-2026-10-01.md): same113/40 qualified cohort,
2mm cache,144³,seed42 scratch initialization,balanced CE+Dice/AdamW. Cosine horizon1200 changes
LR history; this is a duration/schedule diagnostic, not a duration-only control or formalG5 claim.
Question: can additional optimization reduce excessive foreground while retaining native reference
coverage? CAP-EXP-007's median validation volume ratio18.497x/Dice.098701/recall.982700/ROI1of40
motivates it. CAP-EXP-006's coverage collapse motivates numeric checkpoint stops.

Checkpoint/evaluation cadence0/300/600/900/1200; full113/40 first/last,validation40 intermediate.
Stop from300 for mean recall<.95,minimum<.65,box>=.995 count<38of40 or mean recall drop>.03 from
best active prior checkpoint. No filtering, threshold tuning, warm start or automatic continuation.
Fresh426-label maximum:58,621,113compressed/11,763,565,147expanded bytes;zero originalCT reads.
90min total including recovery,16GiB RSS/driver,4GiB local output,AC/100GiB free floor; existing
keeper/backup ceilings unchanged. Exact request/source/test/rehearsal evidence will be linked after
preparation. Stop/failure outcomes will be recorded with their actual step rather than called1200.


CAP-EXP-008 attempt01: request294c26b8 consumed; stopped before label bytes/updates because the
external drive's ephemeral device number changed after remount. One cached inference export,
step0 keeper and failed journal preserved. All153 label paths retain the same UUID/inode/size/times.
The experiment's bounded replacement adds a frozen mount receipt and UUID-verified device-only
observation rebinding; original inventory/cohort/cache hashes and all other source checks unchanged.
Affected tests/native rehearsal are rerun before a new request. No reused consumed request.

### CAP-EXP-008 actual outcome — stopped300, not1200

The replacement request843fd09a ran once and stopped at the first active coverage review:mean native
validation recall0.911146<0.95,minimum0.055399<0.65. The frozen guard prevented updates301–1200
and the planned terminal training evaluation. The stopped transaction/recovery verified successfully.

Same40 validation cases at300:Dice0.077905 vs CAP-EXP-007's0.098701;recall0.911146 vs0.982700;
median volume23.738x vs18.497x;ROI2/40 vs1/40. All40 boxes cover the reference in both runs, but
the scattered oversized masks still miss reference pixels.38 Dice scores decreased,2 increased.
All153 initial metrics reproduce D-304 and all300 sampling traces match CAP-EXP-007. Recorded LR
after300 is0.000256066 instead of0;this is schedule sensitivity evidence,not a duration-only control.
Lower final patch loss does not establish improved localization. Benefit beyond300 remains untested.

300updates/113train/40validation,39 cases two exposures and74 three;146 foreground/154 background
centers.193 label reads,zero originalCT reads;22.729min,5.200GiB RSS/4.799GiB driver. Five keepers
independently restored with primary reads blocked,terminal probe0;415 package files/193 exports
rechecked,seven selected sheets viewed. No post-update training metrics or new7604/6110 claim.
All153 members/23 holds retained;source/environment unchanged;1,574 native tests before freeze.
[Results and immutable receipts](capstone/operations/CAP-EXP-008-RESULTS-2026-10-01.md).

No run is active/pending and neither consumed request may be replayed. Keep CAP-EXP-007 as the
stronger retained coverage reference without promoting it. Next discuss a fresh schedule comparison
that retains earlier decay behavior and the patch-level loss/sampling evidence. Do not relax guards
after this result or filter difficult cases. Formal G5,lesion cascade and sealed evaluation remain open.

## 2026-10-01 — D-308 schedule/patch/loss audit complete

[Findings and immutable evidence](capstone/operations/CAP-EXP-008-OPTIMIZATION-FINDINGS-2026-10-01.md).
No scheduler ordering defect:007/008 both match installed PyTorch,while008's first300 applied-rate
sum is1.8945x007. Saved LR is the next rate after the completed update. Blindly continuing the old
cosine beyond300 would raise its rate again;current version1's bound prevents that future hazard.

All300 patches exactly replayed from the113-member cache.295 contain foreground despite146/154
foreground/background centers;only5 are fully negative. Median target0.303%,extra padding32.64%,
247 patches contain the entire cached reference. Eight background centers lie outside native
geometric support. Balanced CE functions as implemented;median per-voxel coefficient ratio329,
up to248831 on tiny6110's12-voxel patch. These common concerns cannot alone explain the difference
between007/008 and do not justify filtering tiny/partial cases or promoting held negatives.

16 no-update MPS forwards from two independent-backup step300 models reproduced six native masks
exactly. Selected foreground CE/recall worsens while average background CE improves;matched6449
patch loss and soft Dice improve while hard Dice worsens. Lower aggregate loss is an insufficient
progress signal. Gaussian6186 blending does not rescue the failure. No running BN/dropout mismatch
found;25 group norms in each model. Context,loss,negative exposure,padding and duration remain open.

CPU10.332s/2.235GiB RSS;MPS47.901s/2.945GiB RSS/1.461GiB driver. Zero original source/primary reads,
real optimizer updates or model changes. Source/runtime unchanged;1,574-test production baseline.
One CPU helper exact-float assertion was corrected to tolerance,with the failed log preserved;
no production correction. Audit23-member receipt8ae38155aa54a126ba55539a99c5fc4ca0dae175f0fe4f818ca1a9974a53fc86.

[Proposed600 matched-prefix/low-rate-tail experiment](capstone/operations/LOCALIZER-SCHEDULE-NEXT-PROPOSAL-2026-10-01.md)
preserves007's first300 applied rates,then uses0.00001 for300 additional updates. Same153/23holds,
loss,sampler,geometry,prediction and guards. Separate versioned schedule,tests,native recovery and
budget/request freeze are required. This is a proposal,not approval or an active/pending launch.


## 2026-10-01 — CAP-EXP-009 preparation held on native fresh-prefix qualification

D-309 authorized the fresh600-update matched-prefix/0.00001-tail design. Version3 implementation and
47 new tests are complete;1,621 native tests pass. **No real training request was prepared or run.**

Native original/original synthetic controls differ in model weights by0.000178389 after2updates,
with identical histories/losses and one exact validation mask. Original/new separate-process and
final source-matched differences0.000144208/0.000080405 also exceed the1e-6 criterion. CPU toy300
updates match exactly. This shows an unmet fresh native qualification; it does not identify the
exact gradient/kernel cause or predict40 real masks/300 real steps. The launcher refuses request
preparation rather than treating a stopped synthetic transaction as a completed matched rehearsal.

Final refusal/recovery and separate invented tail transition passed:64.346s workers,2.180GiB RSS,
4.845GiB driver;next-update weights1.862645e-9,probes0. Six unique keepers/seven restore operations,
80 final members rehashed;439 retained files indexed. No original CT/label reads, real updates,
cohort changes or model promotion. [Evidence](capstone/operations/CAP-EXP-009-PREFLIGHT-RESULTS-2026-10-01.md),
audit receipt f30b0e65c05cd1368afd5db02dbc14c1c7013b014df695badbf9779c069c26e9.

[Proposed parented tail](capstone/operations/LOCALIZER-PARENTED-TAIL-PROPOSAL-2026-10-01.md) would
start from the exact007step300 model/AdamW state and absolute sampler position300, then test300 new
updates. This is a design proposal requiring review, not an authorized continuation or new run.
The fresh design remains held;153members/23holds and previous consumed requests remain unchanged.

## 2026-10-01 — CAP-EXP-010 approved parented low-rate tail, qualification in progress

D-310 authorizes a new child of independently backed-up007step300, preserving model/AdamW history,
with300 new updates at fixed0.00001 and sampler indices300–599. Same113/40,144³/2mm,loss/model,
prediction policy and153members/23holds. Coverage guards apply from the imported baseline.
[Frozen design](capstone/operations/CAP-EXP-010-LAUNCH-PLAN-2026-10-01.md).009 fresh replay stays held.

Version4 import/records/loop/budgets/recovery implemented;1,652 native tests pass with two existing
torch.jit warnings. Source-matched invented MPS rehearsal preserves imported weights/moments and
independently restores seven keepers, probes0,next weights1.862645e-9;27.742s producer/13.964s recovery.

Zero-update parent qualification request422156cf, SHA
7ed04c3e1c32a9c085921dcb04b5338c488f7d3bb6059986467b63569b6b288c, is launched under D-310.
Scope40 validation references/noCT,900s/16GiB/1GiB; session refuses updates. All40 native masks,
imported weights and old terminal probe must match; three keepers must recover independently.
Successful source/runtime-matched qualification precedes a separate233-label/300-new-update request,
45min/16GiB/4GiB including independent recovery. No repeated launch approval is needed.
No real child updates yet, automatic extension, promotion, Git publication or Claude dispatch.

The first preparation invocation used relative rehearsal paths and was refused before request
creation or source-label reads; corrected absolute paths produced the frozen qualification request.

Real qualification completed: all40 native masks exact, three independent restores, probe0.
126.535s worker/141.998s including recovery,4.931GiB RSS/1.410GiB driver;40 label reads/noCT.
Qualification receipt3f2c561741c58784de081f9ea4166b855ab16d0015ce515e9e15ab9868a0e45b.
Exact300-new-update requesta2593f26, SHA f37f07ad891ea29406e099f1b46d15188e4eb748dcbd295f31fc6b263a796562,
authorized under D-310 and launched once;233 label reads/31,766,649 compressed/6,376,087,421 expanded
bytes,noCT.45min includes recovery. No automatic extension.

## 2026-10-01 — CAP-EXP-010 / D-310 complete

[Results and immutable receipts](capstone/operations/CAP-EXP-010-RESULTS-2026-10-01.md).
Exact007step300 model/AdamW parent imported;300 new constant0.00001 updates,absolute sampler300–599,
113/40,144³/2mm. Real zero-update and child0 qualification reproduce all40 native parent masks.
Final validation Dice0.110417/recall0.975863/median volume16.541x/ROI2/40 versus0.098701/0.982700/
18.497x/1/40. All40 Dice improve/masks shrink;coverage guards pass,useful-shrinkage target fails.
Final training Dice0.108541/recall0.979678/ROI2/113.3115 recall0.706283 and7604 box0.860597 retained;
7684 sole training Dice regression.153members/23holds unchanged,no exclusions/promotion.

25.600min,5.888GiB RSS/4.853GiB driver,233 label reads/noCT;seven keepers independently restored
with primary blocked,probe0.501execution files/233exports verified,ten paired sheets reviewed.
300 exact cached crops:155/145foreground/background centers,290 positive/10 empty,median target
0.303%,padding31.25%,class-coefficient ratio324.643. CPU118.085s/2.212GiB,no original source reads/model forwards/updates.
Combined600patch exposures give78members five/35six. Source/runtime unchanged;1,652 native tests.
Execution receipt84a16cc4e39409140404e8639daead08abce7fce9fee9f400effdccef548eee8.

Both new requests consumed;no active/pending run,extension or promotion.009 fresh replay held.
[Next proposed foreground/objective audit](capstone/operations/LOCALIZER-FOREGROUND-NEXT-PROPOSAL-2026-10-01.md)
uses fixed training patches/independent models before selecting a controlled loss comparison.
No new loss, sampler, request, threshold or training is adopted by that proposal.

## 2026-10-01 — D-311 frozen-model foreground/objective audit complete

Quinton authorized the investigation following010: “Great, check that now. Continue on.”
[Frozen pre-execution design](capstone/operations/LOCALIZER-FOREGROUND-AUDIT-PLAN-2026-10-01.md);
[results](capstone/operations/LOCALIZER-FOREGROUND-AUDIT-RESULTS-2026-10-01.md).
This notebook entry is appended after execution;the plan/request and fixed patch selection were
frozen before logits. That notebook timing deviation is retained,not retroactively relabeled.

Eight identical training-only144³ cached patches through independently backed-up007step300 and
010childstep300/logical600 models:16forwards,zero optimizer updates/original-source/primary reads.
Current CE+Dice favors uniform foreground shrinkage7/8 in each;the6-voxel5286patch favors expansion
at497663x per-voxel coefficient.010improves that patch's reference probability0.427→0.516/recall0→5/6
while shrinking201243→187479predicted voxels. This is not a universal expansion bias or a parameter
gradient. The illustrative cap50 favors shrinkage8/8 but cuts the6-voxel foreground contribution
about4514x,raising sparse-target concerns. No cap/voxel-mean loss adopted. Native-support arithmetic
strengthens background shrinkage on five padded patches without sign changes. The empty probe
still predicts179928voxels despite proper background-only pressure;010exposure290positive/10empty
remains a separate sampling concern. Held empty references remain held.

After the fixed audit, Codex proposes0.25foreground/0.75background class-mean CE+sameDice,sole-class
means unchanged. Post-hoc saved-component arithmetic favors shrinkage8/8 while retaining50–53%
foreground contribution;five invented autograd/finite-difference checks pass. This is a proposal,
not a prospective native treatment,optimal weight or training result.27prelaunch math tests pass;
native decomposition maximum discrepancy7.19836e-8. Total17.396s,RSS1.823GiB/driver1.371GiB,
weights/source/runtime unchanged;1,652-test production baseline,153members/23holds unchanged.

Frozen request dff832472a74618b6e3ca5a689811863b04f397ab91715796f3bf4757981b02a consumed;
execution receipt e90e8b1b72a7d83ff93f5068237b5083e37afbadd2491c2a0bd2d70ed8e02f7f;
42-member review receipt d4b1f0bc0c0be5a0acde60e1b878bf5df538c3e070d71097680f4af4cf59e74c.
No native audit/training pending,loss adoption,promotion,Git publication or Claude dispatch.
[Proposed matched comparison](capstone/operations/LOCALIZER-CLASS-MEAN-REBALANCE-PROPOSAL-2026-10-01.md)
retains007parent/AdamW,300new updates/0.00001/sampler300–599/cohort/geometry/coverage guards,
changing onlyCEclass-mean balance. Discuss the formula before versioned implementation,
native qualification and a new exact launch;sampling/support masking remain separate factors.

## 2026-10-01 — CAP-EXP-011 / D-312 approved, implementation and qualification

Quinton approved the25/75class-mean comparison: “Great, continue with that. Great work.”
[Prospective launch design](capstone/operations/CAP-EXP-011-LAUNCH-PLAN-2026-10-01.md), motivated by
[D-311](capstone/operations/LOCALIZER-FOREGROUND-AUDIT-RESULTS-2026-10-01.md).
Exploratory matched intervention against010's retained control. Exact independent-backup007step300
model/AdamW parent;300new updates at0.00001,absolute sampler300–599,same113/40/144³/2mm. Only mixed
patch CE class means change0.5/0.5→0.25/0.75foreground/background;sole-class CE/Dice behavior unchanged.
No cap50,support mask,sampler/geometry/cohort/threshold change,promotion,extension,Git or Claude action.

Question: can stronger background pressure yield useful shrinkage while preserving reference
coverage? Predeclared endpoint median validation volume<=13.872506x,ROI>=10/40,mean recall>=0.962700,
all40boxes>=0.995. Existing coverage stops and0/150/300cadence retained,initial masks exact007.
Tiny/partial/regressing cases stay in accounting. One control/treatment is not formalG5 or a
replicated causal estimate;known native variation and inherited optimizer moments remain limits.

New version/loss identity and changed-factor record,synthetic arithmetic/learning/interruption/
independent recovery precede40-reference zero-update real qualification. Successful source-matched
qualification precedes fresh233-reference training request,45min including recovery/16GiB/4GiB,
nooriginalCT. Exact requests and approval bindings will be appended after qualification;no real
011updates yet. Preserve each attempt,actual stopped prefix,and independently recovered keepers.
The first targeted test pass found one stale expected CE value after its test changed the target;
the expectation was recomputed against the new target. Failed log retained;no real request existed.

Implementation verified by1,706native tests. Native invented transaction/recovery passes,seven
independent keepers,probes0,nextweights1.862645e-9,uncertain interruption refused. Producer31.510s/
recovery13.934s,peakRSS2.424GiB. Receipts b13dbafd /bcce7d59. Exact zero-update qualification
request3ec13a6e, SHA7575c72690540ff8992ccc45d6986a9296294b694d703b695e46102cc2ec2923,
is authorized and launched once underD-312.40references/noCT,900s;updates explicitly refused.
Source99a64ed0/runtime dd1b62c4 frozen. No real011training updates yet. Future training request
requires successful40-mask parent qualification plus independent recovery under the same source.

Real qualification completed:all40native007masks exact,three independent restores/probe0,
97files/40exports verified.126.544s worker/140.925s total,4.530GiB RSS/1.410GiB driver;40label
reads/noCT. Receipt337187433952cf7aff0031cbf8db1cd37f4485930b7cf4c5c5fbf1864ab88d8c.
Exact training request6b94ab00, SHA562733c43722a5d3588f9f282ea0d26eb7431a8803a06c803f14ae3c31c2ef20,
is frozen/authorized underD-312 and launched once.233label reads/noCT,45min including recovery;
initial40native masks checked again before first update. No extension or gate relaxation follows.

### CAP-EXP-011 actual outcome — stopped150,not300

[Results and receipts](capstone/operations/CAP-EXP-011-RESULTS-2026-10-01.md). The25/75class-mean
intervention shrank all40validation masks and improved all40Dice scores versus010at the matched
150boundary,but mean recall0.948096<0.95and drop0.034604>0.03from parent triggered required stop.
Minimum0.672303/all40boxes pass. Updates151–300and final113train evaluation prevented.
Native Dice0.140680versus matched0100.098067,median volume12.853xversus18.906x,ROI17/40versus0/40;
mean recall0.948096versus0.984547.38recalls decline/2tie/none improve. Parent-relative median
shrinkage30.509%;interim volume/ROI/box utility criteria pass but recall fails,and300endpoint is
not completed. This is shrinkage/recall mechanism evidence,not model acceptance or formalG5.

6186recall0.672303,31150.685326,272745/51native voxels retained;6534passes ROI screen despite
recall0.871806. Six same-cache parent/control/treatment sheets viewed. No new6110/7604/7684
training outcome.150actual traces match010;child78foreground/72background centers/112members,
combined450exposures cover all113(111fourtimes/2threetimes).153members/23holds preserved.
80actual label reads/noCT/9,824,370compressed/1,977,219,390expanded bytes,no final153reads.
10.801min,5.231GiB RSS/4.853GiB driver;five independent restores/probe0,192files/80exports verified.
Source/runtime unchanged,1,706-test baseline. Execution receipt77fbe303affeda26694d94e74f4c3deec7eb0cf3811e20021191b83c972cd780;
33-member review receipt b5f08446451a64381d0131775d1c2d4e279a13aa327850cf5f96437028ccd9f9.

Both qualification/training requests consumed;no active/pending run,resume,extension,promotion,
Git publication or Claude dispatch. [Proposed midpoint37.5/62.5comparison](capstone/operations/LOCALIZER-GENTLER-BALANCE-PROPOSAL-2026-10-01.md)
would retain75%of original foreground CE pressure/increase background25%,same007parent/AdamW,
0.00001/300new/sampler300–599/cohort/geometry/guards. New design decision,version/native qualification
and fresh exact request required. Do not relax guards or claim011's unexecuted300outcome.

## CAP-EXP-012 prospective plan — October 1, D-313

Quinton approved the37.5/62.5class-mean midpoint and its complete qualification/run sequence.
[Launch plan](capstone/operations/CAP-EXP-012-LAUNCH-PLAN-2026-10-01.md). Hypothesis: retain more
reference than011while reducing007's excessive foreground. Same007step300/AdamW parent, constant
0.00001,300newupdates/sampler300–599,113/40,144³/2mm,seed42, unchanged sampling/geometry/argmax.
Mixed-class CE .375foregroundmean+.625backgroundmean, sole-class full-strength mean, sameDice.
Only loss changes scientifically; version6 explicitly isolated. Compare010at150/300and011at150.
Coverage remains active0/150/300:mean>=.95,min>=.65,>=38/40boxes>=.995,mean drop<=.03frombest
previous boundary including0. Utility at300:median volume<=13.8725059808,ROI>=10/40,mean recall
>=.9627000322,all40boxes>=.995. If stopped,report actual prefix and prevent future reads/updates.
Synthetic math/learning/refusal tests and native invented recovery precede fresh40-label/noCT
zero-update qualification(900s/16GiB/1GiB). Successful source-matched qualification precedes exact
233-label/noCT request(2700s including recovery/16GiB/4GiB/AC/exclusiveMPS/100GiB free).
Mandatory views6186/3115/6534/2727and,if terminaltrain evaluation occurs,6110/7604/7684.
No pending exact request yet; no model promotion, automatic extension, eligibility change orG5claim.

D-313 implementation verified:1,763native tests pass(57new,twoexisting torch.jit warnings).
Independent loss formula/gradient, sparse/empty learning, parent preservation/absolute sampler,
interruption/refusal and version isolation tested. Exact factor check:only adapter/session common
mechanics gain gated version6 support,eight new production modules;old data/model/loss code unchanged.
Only loss_id changes scientifically against010;plan fields match aside from required versions.
SourceSHA94b77f49fb18ce3547a91a32d08bd52a787c6f8f86441cfbbd0d0d7a31b9293d;
runtimeSHA dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31.
Native invented recovery is now running;no real012qualification request or updates yet.

D-313 qualification exact request bound to existing design approval: `outputs/prowl/twomm-training-febb98c7-41e0-45b7-9025-25d878b8a96c`,
SHA `49afaf63e44fb057ad55c5dd999f27e6e5211d6d4ca12623e3b026aa53934406`; approval SHA `736d364ec9a49c0ce0b932232cbaf63eb508d2e8e47717dd01c0ee10e4cddfe8`.
40fresh pancreas labels/4912185compressed/988609695expanded bytes,noCT;
900s including recovery,16GiB RSS/driver,1GiB output,AC/exclusiveMPS/100GiB free.
Source `94b77f49fb18ce3547a91a32d08bd52a787c6f8f86441cfbbd0d0d7a31b9293d`,runtime `dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.
Binding applies approved D-313 design after verified gates;not a claim of prior user review of generated bytes.
One launch only; no extension, promotion or guard relaxation.

D-313 real zero-update qualification passed:all40native007masks exact,three independent keepers restored,primary blocked/probe0;97files/40exports rechecked. Worker129.394s,total144.740s,RSS4.673GiB,driver1.410GiB.40label reads/noCT. Qualification receipt`bcb8064fe24f86ff55885ca18442d18a2bf4cdda0d1864632efd1ac354057f12`. Source/runtime unchanged;fresh training preparation follows.

D-313 training exact request bound to existing design approval: `outputs/prowl/twomm-training-a0636d70-2ea5-4e5f-9167-db28bff562ba`,
SHA `06cecda421626271eeb6fae5f02679d7fc9650b5afd0861ce39fce5ed0612218`; approval SHA `4ea46c04f41c22c8fafa89f86a3ddaf75a31c7d9e9effc611406d08cfe772920`.
233fresh pancreas labels/31766649compressed/6376087421expanded bytes,noCT;
2700s including recovery,16GiB RSS/driver,4GiB output,AC/exclusiveMPS/100GiB free.
Source `94b77f49fb18ce3547a91a32d08bd52a787c6f8f86441cfbbd0d0d7a31b9293d`,runtime `dd1b62c4469320084e2798c6b5dd1129422ede31fad1a02a7bcaef5597589c31`.
Binding applies approved D-313 design after verified gates;not a claim of prior user review of generated bytes.
One launch only; no extension, promotion or guard relaxation.

### CAP-EXP-012 actual outcome — completed300,utilityfailed

D-313 CAP-EXP-012 complete:300newupdates/logical600,37.5/62.5CE+sameDice,exact007model/AdamW parent,
0.00001/113/40/144³/2mm. Native validationDice0.129078,meanrecall0.962519,
minimum0.674440,medianvolume14.2596x/22.907%belowparent,ROI15/40,
boxes39/40. Every0/150/300stop passes,but utility fails volume/meanrecall/all40boxes;no promotion.
Against010at300all40Dice improve/masks shrink,38recalls decline.3115newvalidationboxfailure,
756/6822newtrainingboxfailures,7604persistent;150trainingrecall.4630isworst andonlytrainingDice regression.
TrainingDice.126738/recall.968681,ROI36/113,boxes110/113. All113members retained,combined600
exposures78five/35six times;155foreground/145backgroundcenters.300crops exactly match010.
Actual233labelreads/noCT;25.312min,RSS6.252GiB/driver4.853GiB,seven independent
keepers restored/primaryblocked/probe0.502executionfiles/233exports,13selectedpairedsheets and
trajectorychart reviewed,52reviewmembers rehashed.1,763-testsource/runtime unchanged.
Executionreceipt`2ca47e685f28d8007c34db51410482dc77b5b34da56598f4a645314ef1991926`;reviewreceipt`9f69df5f1d80acf845f89fde52fa6cc4b06a5ca9ac9a78f055b3e8be097e78a6`.
[Results](capstone/operations/CAP-EXP-012-RESULTS-2026-10-01.md). Both requests consumed;no pendingrun/extension/
promotion/eligibilitychange/Gitpublication/Claudedispatch.153members/23holds unchanged.
Next recommendation is a timeboxed retained-prediction structure/box-extent audit and smallStage2
qualification planning,not another weight guess or approved job. Fresh reference scoring requires
new scope;oldreadrequests may not be recycled.


### October 1 — retained structure audit and Stage 2 planning

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-314|Timebox the retained native-prediction component/box audit and prepare the small Stage 2 qualification packet.|Quinton: “Great, continue with that.” after the D-313 recommendation.|Compare completed 010 and 012 at child step 300 on all 40 development-validation members plus retained training failures 150/756/6110/6822/7604/7684. CPU only; frozen retained exports/records, no CT or original target arrays, inference, updates, component-policy adoption or model promotion. Native references would require a new read scope. Stage 2 work here is planning; lesion qualification and real reads are not inherited from localizer permission. Preserve 153 members/23 holds and all sealed evidence.|

Owned new files: bounded structure helper, diagnostic script/tests, one local audit output directory,
operations audit plan/results and Stage 2 qualification/implementation packet. Update only shared
checkpoint/decision/notebook navigation. Acceptance: independently checked component arithmetic,
26-connectivity/ties/empty/dense/physical bounds, frozen exact input pins, one-shot request consumption,
all requested cases visible and old masks unchanged. Audit has no target truth per component;
hypothetical largest-component box cost is not a validated ROI or pancreas-containment result.
Prospective plan: [structure audit](capstone/operations/LOCALIZER-STRUCTURE-AUDIT-PLAN-2026-10-01.md).


D-314 diagnostic readiness: 26 new synthetic/helper/runner checks pass. Dense 96-million-voxel
CPU profile passes in 1.362 seconds, peak RSS 604,438,528 bytes. Exact retained-only request
`outputs/prowl/LOCALIZER-STRUCTURE-AUDIT-20261001/request.json`, SHA
`f5d455d9eb514f213c11cb8be1be84a90c22e6d4a03870a6954bbcda58de2054`, pins 92 masks,
21,606,141 compressed bytes and 2,436,199,082 uint8 voxel payload bytes, 1,200 seconds/8 GiB/50 MiB.
Original-reference/CT reads, model inference/updates and adopted cleanup remain prohibited.
Exact scope binds Quinton's approved D-314 diagnostic after preparation; it does not claim he
reviewed these generated bytes. Full native suite is running before the one-shot audit.
Stage 2 packet prepared: [qualification/cascade slice](capstone/operations/STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md).
No Stage 2 eligibility, read request or training authorization follows from that planning document.


D-314 complete: 92 retained native masks/46 paired cases (all40 validation + train150/756/6110/6822/7604/7684),
010/012 child300,26-connectivity/10mm. CPU33.239s,RSS1.464GiB; no original arrays, forwards or updates.
012 largest foreground share median99.394%, mean crop31.684%→hypothetical21.961%;30/40boxes change,
size-only15→31/40,not new ROI passes. Main region remains median13.328×reference; count-only guaranteed
excess median92.69%.3115/756/7604boxes unchanged;6822's smaller box cannot repair existing containment.
Five012/eight010 validation count-only component recall lower bounds are0;actual overlap unmeasured.
1,789native tests pass(26new,twoexisting warnings); initial sandbox ps restriction preserved in test log,
complete native rerun passed.96M dense synthetic profile1.362s/0.563GiB.184selected inputs and audit
source modules rehashed unchanged. Requestf5d455d9 consumed;executionb58ff84c;review63fb49bb,
105files/3,046,235bytes. [Audit results](capstone/operations/LOCALIZER-STRUCTURE-AUDIT-RESULTS-2026-10-01.md).
[Stage2 packet](capstone/operations/STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md) prepared including
bounded synthetic purpose records/metadata proposal, then lesion qualification/shared geometry/synthetic
learning/real zero-update/exact smoke/matched provided-predicted modes. No realStage2 permission/cohort/
reads/model/job. [Component coverage proposal](capstone/operations/LOCALIZER-COMPONENT-COVERAGE-PROPOSAL-2026-10-01.md)
needs new scoped reference-read decision;largest-only remains diagnostic. No pending training, promotion,
consumer/cohort change,Git publication orClaude dispatch.153members/23holds unchanged.


### October 1 — Stage 2 synthetic purpose records and metadata proposal

|ID|Decision|Authority|Boundary|
|---|---|---|---|
|D-315|Implement Phase A's separate segmenter-purpose qualification/cohort contracts on invented evidence and produce the retained-metadata candidate proposal.|Quinton: “Amazing work, continue.” after D-314's recommended next step.|New versioned dual-target records, synthetic resolver tests and metadata-only candidate/hold accounting; proposed 8 train/4 validation list, not a real cohort. No source arrays/stat jobs, real Stage 2 permissions, cohort publication, model execution, downloads or training. Old localizer rules/consumers and original membership/153 members/23 holds remain unchanged. Component-reference proposal still needs a separate fresh-read scope.|

Owned files: new `segmenter_qualification_v1.py`, `segmenter_cohort_v1.py`, retained inventory CLI,
new tests and dedicated schemas if needed. Generic manifest/annotation formats already support two
structures; preserve them and the existing localizer schemas. New purposes are explicitly
`pancreas_lesion_segmenter_training` and `pancreas_lesion_segmenter_validation` under a distinct policy.
Records must bind both annotations/all three inputs, exact evidence hashes, issues and original roles;
empty lesion masks do not infer negative status. Tests must reject stale/changed/omitted evidence,
wrong roles/purposes, unsupported units/mapping, duplicate/overlapping membership and silent refill.
Metadata reads are bounded to pinned retained JSON/CSV/split bytes; no legacy file path is resolved.
Packet: [Stage 2 qualification/cascade](capstone/operations/STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md).


D-315 complete: separate dual-target segmenter qualification/cohort/paired-lesion-inventory contracts,
47 new synthetic tests; full native 1,836 passes/two existing warnings. Old source snapshot remains
CT/pancreas-only; no shared schema widening. Four shared data modules/two old schemas match D-294 pins.
Retained metadata proposal exactly replays in a fresh process:176 candidates/153 localizer-qualified/
23 held, plus historical31/78/266 contexts retained. New Stage2 qualifications0; original7200/1800/901 unchanged.
Proposed train3/26/6110/2973/2232/6238/5821/4965; validation2514/5641/2727/7265. Six train/two validation
positive legacy hints; zero hints are not verified negatives. Current40validation has only two positive
hints, so a later broader lesion-positive validation proposal is needed for stable performance estimates.
31,571,267 metadata bytes,1.307s/0.326GiB RSS,zero source stat/array calls or models. CandidateJSON
2f38464f;metadatareceipte83c27e1;sealedreviewb25f3e20,15files/483,620bytes. All input/code pins verified.
[Results](capstone/operations/STAGE2-METADATA-RESULTS-2026-10-01.md) and
[contracts](capstone/data/STAGE2-PURPOSE-CONTRACTS-2026-10-01.md). Proposed next:
[M1 source stat/availability](capstone/operations/SEGMENTER-SOURCE-VERIFICATION-PROPOSAL-2026-10-01.md), then
fresh headers/content, purpose dispositions/cohort freeze/shared geometry. No M1 capability/request/run
or real Stage2 permissions issued here. Component-reference job still needs separate fresh scope.
No training/promotion,old consumer or eligibility change,source rewriting,Git publication orClaude dispatch.

## October 1 — D-316 segmenter source availability, identity and native header checks

Question: are the proposed8 train/4 validation files present, stable and geometrically pairable before
new lesion-content checks? **All36 exact paths present;24 companion hashes and two historical lesion
hashes match.** Twelve lesion headers match qualified mm CT. Five scaled int8 labels require semantic
binary decoding; six unknown target units have matched byte-bound qualified CT context. Neither headers
nor legacy zero/positive hints establish current foreground, negative status, completeness or permission.

M1:1.867s/0.100GiB RSS,zero payload reads. M2:7.618s/0.100GiB,276,002,660compressed hash bytes plus
49,152compressed header bytes; only348decompressed bytes per lesion, no arrays/model updates. All source
observations and mount checks stable. First sandbox M1 failed at DiskManagement before candidate stats,
request consumed/preserved; native fresh attempt and separate M2 completed. Successful receipts9a1e5c9c/
bec0f3b3 consumed. Final1,869native tests/33new fault checks; two existing warnings. Four initial fixture
failures from historical pytest RSS were corrected in fixtures, with real budgets unchanged. Review
b90cbf06 (22members/91,259bytes) preserves every attempt and independently checked pins.

[Results](capstone/operations/SEGMENTER-SOURCE-VERIFICATION-RESULTS-2026-10-01.md).
[Next content/alignment plan](capstone/operations/SEGMENTER-CONTENT-ALIGNMENT-PACKET-2026-10-01.md):
synthetic largest-case qualification, fresh four-case native-array pilot3/26/2973/5641, review, then
remaining eight under their own request. Companion expanded sizes/dtypes were recovered from exact-byte-
matched retained content evidence, avoiding new sizing reads. Proposal total953,056,392expanded bytes;
separate full hash+decode compressed budgets. No arrays, real Stage2 permission/cohort, training,
cleanup adoption or component-reference scope in D-316. Current153/23 and protected membership unchanged.

## October1 — D-317 first segmenter native-content/alignment pilot

Train3/26/2973 and validation5641:all12 exact files pass fresh hash+fullgzipCRC/length/header/grid checks.
Strict semantic binary decoding yields lesion counts1055/7244/124/47190,one26-connected component each.
Lesion-outside-pancreas-mask counts0/431/3/47190 retained.2973 has124voxels on one7.5mm source slice;
carry it into target-fidelity checks.5641's masks are disjoint but selected outlines look adjacent/
complementary. Exact-byte-bound retained pancreas box contains its whole lesion extent; same for all4.
No gross transform mismatch observed in all4 native sheets. Source annotation relationship is still
open; no expert target certification or permission inferred. Do not clip/union masks or exclude5641.

New source-content helper/supervised pilot;41new synthetic checks/full native1,910passes,twoexisting
warnings,65.16s. Initial test-factory sform/pixdim inconsistency corrected before profiling; allattempts
retained. Largest46,219,264voxel rehearsal passes dense/empty/392fragmented/boundary cases in15.406s,
0.830GiB RSS. Real pilot6.777s/0.963GiB;185,422,674compressed hash+decode/317,547,616expanded bytes.
Requestb27b26ab consumed;source2f972c5c,profile14eaa7e0,independent sealedreviewb4cc90d5.38sourcemembers/
2,851,981B;19reviewmembers/91,382B. No arrays reopened for box checks/final review. Native-display
orientation/tiny-detail oracles pass; no source rewrite or model execution. Old implementation unchanged.

[Results](capstone/operations/SEGMENTER-CONTENT-PILOT-RESULTS-2026-10-01.md).
[Next eight-case continuation](capstone/operations/SEGMENTER-CONTENT-CONTINUATION-PACKET-2026-10-01.md)
needs a separate tested24-file consumer and fresh exactrequest; proposed366,582,646compressed/
635,508,776expanded bytes. No continuation arrays/freeze ortraining here. After all12 reconciled,
purpose dispositions/paired inventory/annotation transitions and cohort remain separate,then shared
pancreas-only ROI geometry,fresh three-class learning/recovery/MPS/exact smoke.153members/23holds unchanged.

### October 1 — D-318 segmenter content continuation (no training)

Separate native 24-file consumer completed the eight remaining cases; all eight source sheets
reviewed. 1,931 native tests / 21 new checks pass. Largest synthetic reader/analyzer/new renderer
14.450 s / 0.830 GiB; exact source job 12.343 s / 0.912 GiB, 366,582,646 compressed hash/decode and
635,508,776 expanded bytes. Source request f378e8d3 consumed; source receipt eeb5d3b0,
profile56ceb670, reviewfb483be6 (24members/143,111B); no source arrays reopened for review.

Full12 ledger: six train/two validation nonempty references and four empty unknowns. No verified
negative or permission granted. Case6238 lesion reaches source boundary; all eight nonempty lesion
extents fit retained pancreas-only boxes.5641's disjoint annotation relationship remains open;
2973 single7.5mm-slice challenge retained. No clipping/union/refill or lesion-dependent ROI repair.
Empty sheets now contain three truthful context views; original pilot/version remains unchanged.

[Results](capstone/operations/SEGMENTER-CONTENT-CONTINUATION-RESULTS-2026-10-01.md).
[Next purpose dispositions](capstone/operations/SEGMENTER-PURPOSE-DISPOSITION-PACKET-2026-10-01.md)
require paired inventory, explicit reviewed use/target receipts and preserved annotation/issue
transitions before any real cohort. Shared ROI/three-class geometry, synthetic learning/checkpoint
recovery and fresh zero-update MPS/resource qualification still precede an exact training launch.
153 localizer members/23holds,176 candidates and original membership unchanged.

### October 1 — D-319 dual-target purpose ledger (no training)

Twelve exact lesion sidecars and independently replayed purpose qualifications: six train positives
(3/26/2973/2232/6238/5821), one validation positive(2514), five holds.5641's annotation relationship
remains unresolved;6110/4965/2727/7265 empty masks remain unknown. No refill or verified negatives.
All old184annotations/247issues, pancreas identities, protection/source/subject records preserved;
new manifest196annotations/260issues.3/26 quarantined lesions remain alongside reviewed successors.
Difficult nonempty targets/source boundary contacts/outside-pancreas voxels retained.

25new checks/1,956native passes in67.43s. Local package7334b71e, input9f45cdf7, manifest31c7239d,
transition62447d63; fresh full rederivation57.591s/0.958GiB,exit0. Supplementary time-wrapper sysctl
failed after successful publication; complete receipt verified without repeating publication.
Independent oracle checks all twelve outcomes/current source counts/sidecars and preserved history.
Review81ee950a,19members/245,703B,all attempts/snapshots retained. No raw source reads, cohort or
model operations. One validation positive is an engineering reference, not a generalization estimate.

[Results](capstone/operations/SEGMENTER-PURPOSE-DISPOSITION-RESULTS-2026-10-01.md).
[Next6/1 cohort freeze](capstone/operations/SEGMENTER-COHORT-FREEZE-PACKET-2026-10-01.md) must require
independent transition/package pins and registered artifact publication/recovery. Then shared ROI/
three-class target geometry/fidelity, synthetic learning/checkpoints, zero-update MPS/resource and
fresh exact smoke launch.153localizer members/23holds,176candidates and original roles unchanged.

### October1 — D-320 registered segmenter cohort freeze (no training)

Exact6train(3/26/2973/2232/6238/5821)/1validation(2514) frozen with original7200/1800protection
parents;test901 and full9901unchanged. All12/fiveholds,184oldannotations/247issues retained.
Full D-319 purpose/transition rederivation required; no bare-manifest promotion/refill/negative inference.
New exact capability0b89b9a9, unchanged roots/provider/source settings. Seven covered members/
28,722,760B,completion73e7e034,plan49b11f37,code03f0d1e4,descriptorscd52c555. Publication
263.044s/1.004GiB; fresh registered replay155.396s/0.962GiB; independent direct byte/descriptor/CT
oracle passes.31new checks/1,987native passes, two existing warnings,70.56s. Reviewf6897492,
27members/207,038B,all attempts retained. No independent keeper/source arrays/real updates/launch.

[Results](capstone/operations/SEGMENTER-COHORT-FREEZE-RESULTS-2026-10-01.md).
[Next shared geometry/loader](capstone/operations/SEGMENTER-GEOMETRY-LOADER-PACKET-2026-10-01.md)
requires independent synthetic physical oracles and a fresh bounded21-file zero-update fidelity
request;2973single-slice and6238boundary retained. Then fresh three-class learning/recovery,MPS
resource and exact smoke launch. One positive validation/no negatives supports engineering only;
153localizer members/23holds and176candidates unchanged. No pending training request.

### October1 — D-321 segmenter geometry and source restoration (no model)

D-321 complete: shared portable physical mapper and registered role-safe triple loader;75new/
2,062native tests, two existing warnings,72.04s. Real exact6/1all7screens pass; all14native/nearest
sheets reviewed. Provided-pancreas10mm/1mm intermediate/144³/zero-jitter recipe accepted only for
engineering subset; nearest lesion recall0.9678–0.9920,union0.9711–0.9962,continuous-reference
argmax0.9516–0.9839. Tiny2973retains123/124nearest,118/124continuous;6238boundary and every
outside-mask reference retained. No model performance/negative/autonomous claim or case filtering.
Fresh scope01619662/profile5cdef929;11synthetic fixtures13.973s/4.567GiB, losses truthfully retained.
Exact request07d3bb4f consumed once:21files,145,701,969hash/145,701,969decode/544,986,944expanded
bytes;183.580s/4.173GiB,receipt5c958ac1(33members). Original wrong/canonical transport pins rejected
before consumption; producer/reader corrected to persisted-byte hashes, regression and fresh
scope/profile/request retained.53producer members independently verified with no new source reads.
Acceptanceb3ff4db9/recipe2382855d; reviewd0d94625(35members/451,678B),all attempts and snapshots.
Old code/schemas/roots and6/1/all12/fiveholds/history unchanged;153localizer/23holds unchanged.
No retained tensor cache/independent keeper claim, training/model updates or pending launch.
[Results](capstone/operations/SEGMENTER-GEOMETRY-RESULTS-2026-10-01.md),
[next learning/recovery packet](capstone/operations/SEGMENTER-LEARNING-RECOVERY-PACKET-2026-10-01.md): fresh
three-class synthetic learning/CPU+MPS transaction and independent recovery, then new exact real
zero-update cache/model/export qualification and measured short launch. Original requests are not
reusable; formal baseline jitter and autonomous cascade remain separate.


### October 1 — D-322 synthetic segmenter learning/recovery

Five controlled fresh scratch comparisons on invented24³full-ROI train fixtures;seed42,constant
LR0.003,SegResNet1→3,complete-ROI sampler. Unweighted CE/120updates and16×lesionCE/120both
collapse positives.256×/120produces excess foreground and misses multiple lesions. Same256×/
360hits every component but disconnected Dice0.64fails unchanged0.65bar;fresh480passes all positive
lesion Dice/recall1,all five components,negativeFP0,pancreasDice0.9954–1.0,lossratio0.010739.
All original criteria/configurations/source snapshots/failures retained;no threshold or case changes.
Fixture images directly encode class cues:mechanics evidence only,not real CT performance.

CPU interrupted/uninterrupted trajectories exact;successful worker55.086s/0.880GiB. Native144³
MPS three committed synthetic updates,dirty fourth transaction refused,25.458s/2.950GiB RSS/
4.879GiB driver. Cold MPS recovery9.812s/2.772GiB/4.949GiB driver;prediction delta0,nextweights
1.49e-8,nextloss0,exact invented40.5M-voxel inverse. All six current CPU0/30/480,MPS0/2/3
keepers restored with primary access blocked;216physical files/30diagnostic members checked.
Failed trial weights remain local scratch.85new/2,147native tests,two existing warnings,75.61s.
Reviewb85ceed5,63members/494,485B;acceptance8a061fdb.2,407synthetic optimizer calls excluding
tests;zero real arrays/updates.6/1/all12/fiveholds,original protection and153localizer/23holds fixed.

[Results](capstone/operations/SEGMENTER-LEARNING-RECOVERY-RESULTS-2026-10-01.md).
[Next packet](capstone/operations/SEGMENTER-ZERO-UPDATE-QUALIFICATION-PACKET-2026-10-01.md):
role-safe persisted cache/new21-file scope,all7zero-update MPS/native exports,separate14-target
original scoring and real-input recovery before exact short training. v3loss is synthetic engineering
candidate;historical checkpoint inventory/real optimizer consumer still open. No synthetic weights
as real initialization,no source activation/new eligibility/pending training or automatic extension.


### October 2 — D-323 segmenter cache (no model updates)

Exact6train/1validation cache published/cold replayed;all7transforms/fidelity/counts match D-321;
all7cached target/image views inspected,tiny2973and boundary6238retained.16members/104,576,736B,
rawpayload104,509,440B;completion90b8cc94,bindingcdd7c707.68new/2,215native tests,73.73s.
Optimizer closed;image-only consumer returns no target. Original12/fiveholds and153localizer/23holds
unchanged,no source activation or eligibility promotion.

First consumed request88568c20stopped at initial stat guard before source open/hash/decode.21-path
metadata receiptb0574622records only volatiledevice16777243→16777239,same APFS UUID and sizes/
inodes/times/modes. Old evidence retained;newwrapper permits only this pinned metadata refresh,
all original hashes unchanged. Fresh requestd84cdcdc consumed once,21hashes match;145,701,969B hash/
same decode,544,986,944B expanded;193.053s/3.413GiB. Cold replay156.701s/0.986GiB,zero rawreads.
Largest syntheticprofile1.209s/1.875GiB;boundarycomponent recall0.25,total0.625loss preserved,
not real qualification. All failed attempts and snapshots retained.

28diagnostic/18physical files independently audited,cacheacceptance8b21315b;reviewf7440f39,
42members/797,102B. Cache/review are derivedlocal,no independent keeper claim. No real model/
optimizer update or training request. [Results](capstone/operations/SEGMENTER-CACHE-QUALIFICATION-RESULTS-2026-10-02.md).
[Next](capstone/operations/SEGMENTER-REAL-INFERENCE-PACKET-2026-10-02.md): fresh scratchstep0,
all7zero-update MPS/native exports/task keeper recovery,then separately scoped original-reference
scoring. Historical checkpoint inventory/import denial and realoptimizer transaction precede a
short exact launch;one validation positive/no verifiednegatives is engineering only.

### October 2 — D-324 prospective step0 segmenter inference qualification

User continues after D-323. New inference-only scratch task; no imported or learned synthetic weights,
optimizer or original source reads. Exact6/1cache images only after synthetic native qualification.
Prospective plan: operations/SEGMENTER-INFERENCE-QUALIFICATION-PLAN-2026-10-02.md. All native masks,
checkpoint/controls and image/probability probe protected on separate physical medium; recovery blocks
primary reads and requires probability delta≤1e-6 and exact native mask. Serial AC/MPS,1200s,
12GiB RSS/driver,1GiB evidence/additional bytes per domain,100GiB free. Freeze absolute quota ceilings
before first publication. Synthetic largest40,547,328grid plus empty/dense/sparse/fragmented outputs;
no foreground/component failure filtering. Original14-target scoring remains a fresh later scope.
58new rejection/oracle tests pass; full native2,273pass,two preexisting warnings,77.67s. No real
forward/update yet. Hold metadata/cohorts and D-319–323 producers remain unchanged.

D-324 synthetic request98c47c55 consumed once:10.937s,3.169GiB RSS,1.400GiB sampled driver,
6protected members/107,172,246B. Empty/dense/sparse/fragmented native cases retained (no foreground
cap). Independent fresh-process recovery4.156s/2.980GiB,all6members,primary blocked,probe0/nativeexact.
Profile packagefe013fff verified including successful semantic recovery before real requestfreeze.
Real requestcfac9e1afd8e4324713557f5e816a62e8d09c477fed756dc4760d42a22850f50 is exact7cache
images,6train/1validation,zero updates,1200s/12GiB RSS/driver,1GiB outputs. Same frozen absolute
quota ceilings as synthetic attempt; required all7native masks+controls+state+probe keeper. Authorized
by D-324 continuation scope; no original CT/target arrays or training approval inferred.

D-324 complete: realrequestcfac9e1a consumed once,all7image-only MPS forwards and nativeexports;
177.563s/5.312GiB RSS/1.400GiB sampled driver. Scratchweights3ee49a53unchanged,zero updates/
originalarrays/imports. All12members/202,895,580B protected,rawnative136,244,888B;7sheets reviewed.
Initial probeexact but absolute-path guard insufficient for dir_fd walks. Supplementalguard first
fails on valid anonymous subprocess pipe (b82ef16e preserved);new regression detects/fixes it.
Attempt02 synthetic guardedrestore passes,realduplicatecopy refused by two-payload retry reserve;
e1a6ff1a partialretained. No quotareset/increase/deletion. Attempt03 cold reads existing independent
restore+backup under strengthenedguard,all12exact,probe0/nativeexact,3.463s/1.877GiB;no registered
storagewrites. Final2,287native/72new tests,2existing warnings,73.53s. 89physical/47jobfiles and18cache
files independently checked;acceptance7cb2ba5d,review11a11afe(28members/1,407,176B). Source/cohorts/
holds/roots unchanged. No nativeDice,traininglaunch or automaticextension. Next fresh14-target
originalscoring packetecae4dea,then historicalimport inventory/realoptimizer transaction.
See operations/SEGMENTER-INFERENCE-QUALIFICATION-RESULTS-2026-10-02.md. Futurekeeper budgets
must include repeatedcopy/retry reserve,not just raw payload. All failed/partial attempts preserved.

### October 2 — D-325 prospective original-native segmenter scoring

Quinton explicitly requests scoring now. Separate target-only reader/metric/source receipt contract,
no CT/model forward/update/import. Exact6train/1validation accepted D-324 masks;all12/fiveholds,
protectedroles/153localizer/23holds unchanged. Truth original lesion-over-pancreas; all components
and empty/dense/wrong/fragmented predictions remain scores. Plan:
operations/SEGMENTER-NATIVE-SCORING-PLAN-2026-10-02.md. 65new analytic/decoder/role/grid/forgery
checks pass. Initial fixture expected one26component for points two voxels apart; that test expectation
was corrected to two and an actual corner-neighbour test added. Scoring code/formulas unchanged.
Fresh14path stat-only metadata4a0320f7:all observations identical,zero sourcearrays/hash/decode,
4.705s. Original hashes remain fixed. Next maximum40547328grid CPU gzip-decode/metric profile,
then exact1,265,220Bhash/decode and272,494,704Bexpanded source request after qualification.
Prospective1200s/8GiB RSS/32MiBevidence/100GiBfree;new64MiBdomain scoring capability,absolute
ceilings frozen before publication including required keeper/restores and retry reserve. No launch
of source scoring yet;D-319–324 producer/registry pins verified unchanged.

D-325 native suite2,352passes,65new,twoexisting warnings,79.67s. Syntheticmaximum40547328grid
profilea90ca032:9.793s/0.7345GiB RSS,all392reference components retained across four failurepatterns.
Exact fresh source request9525baef9004ed568f365a5701cba931bfdb14c3aa433e8d8a45322457e15111
prepared after stat/profile qualification. Exactly14targets,1,265,220Bhash/same decode,
272,494,704Bexpanded;zeroCT/model. Newstoragecap4528cf8b,ceilingsprimary67,108,864B/
independent whole-root10,312,653,981B;64MiB additional includes retry reserve and metrickeepers.
User's explicit scoring instruction/D-325 authorizes this exact job once; no training inferred.

D-325 request9525baef was consumed but stopped before original payload open/hash/decode.
The transport encoder omitted the canonical newline: saved hash9525baef versus canonicaldc2d55b7.
All first-reservation counters remain zero; no native scoring publication. Failure package
d0ed2d57 and all seven producing source/test/capability snapshots are preserved separately.
Attempt02 saves canonical transport bytes without changing old producers; seven new regression
checks prove saved/protected/request-guard identity and pre-open refusal. Absolute original
64MiB additional-domain ceilings are retained rather than reset on preparation. Fresh stat-only
metadatae47864af and maximum-grid profile8c865fdc (10.497s,0.734GiB supervisor peak) pass;
no real reads, CT/model forwards or updates in either qualification job.

D-325 repaired native suite:2,359passes,72new,two existing warnings,90.63s. Fresh attempt02
requeste24cef49a5d0eb57932217fd045a868bbce7c924f8c65b66244418040cf240b4
uses identical canonical transport/guard/protected bytes; exact same14targets/read budgets,
1200s/8GiB/32MiB/100GiB free and frozen original storage ceilings. User scoring scope authorizes
this replacement request after the consumed zero-read failure; no request reuse or model work.

D-325 complete: original-native step0 baseline accepted; all seven cases and fourteen original
pancreas/lesion references, no CT/model forward/update/import. 72 new / 2,359 native tests pass,
two existing warnings,90.63s. Training macro lesion Dice0.001779/recall0.012986; one validation
Dice0.000061/recall0.000532. Three train lesions have zero overlap; validation one TP voxel.
Tiny2973, boundary6238 and all original components/outside-pancreas voxels remain in denominators.
First9525baef request failed its transport/canonical hash guard before original payload reads;
consumed failured0ed2d57/source5274f03b retained. Canonical-byte repair tested before fresh
requeste24cef49 completed once:183.935s/1.951GiB RSS; fourteen hashes and exact1,265,220B each
hash/decode,272,494,704B expanded. Five protected members/101,447B cold independently restored
with primary denied,1.140s/75.45MiB; original64MiB domain ceilings retained. 27physical/27jobfiles
independently audited. NumPy/Python macro floating difference≤1.39e-17 recorded and review corrected,
integer counts/per-case formulas exact; scores unchanged. Acceptancef4bfcaf0/review945d1e50,
14members/98,480B. D-319–324 code/registry/6/1/all12/fiveholds/153localizer/23holds unchanged.
Both source requests consumed,no training request/promotion. Results and next transaction packet:
[Native scoring results](capstone/operations/SEGMENTER-NATIVE-SCORING-RESULTS-2026-10-02.md);
[next training transaction proposal](capstone/operations/SEGMENTER-REAL-TRAINING-TRANSACTION-PACKET-2026-10-02.md).
One validation positive/no negatives and random weights support an engineering before baseline only.

### October 2 — D-326 prospective training transaction qualification

Continue from accepted D-325 native scratch baseline. New optimizer consumer/session and checkpoint protocol, bounded historical byte-hash inventory and invented CPU/MPS transaction/recovery checks. No real updates or original arrays. See capstone/operations/SEGMENTER-TRAINING-TRANSACTION-PLAN-2026-10-02.md. All predecessors/cohorts/holds/registry fixed; exact real rate/duration/launch remain later measured choices.

### October 2 — D-326 transaction qualification complete

D-326 complete:96 new/2,455 native tests, two existing warnings,84.52s. Historical203 files/
8,240,982,194B pure-byte inventory;17,021 tensor-cache payloads excluded,no weight imports.
Separate qualified6/1 input boundary/session/sampler/checkpoints pass. CPU6 committed/exposure1
all6:18.019s/1.586GiB; cold0/2/3/6 exact probabilities/nextweights:8.484s/1.194GiB.
MPS3 committed/dirty4th refused:47.014s/5.271GiB/4.887GiB driver; cold0/2/3 probability0,
nextweights1.68e-8/nativeexact:22.324s/4.463GiB. Producer MPS4 invented calls plus separate
recovery1; CPUproducer13 plus recovery1. Seven checkpoints/two probes independently restored.
Real7-cache bridge169.576s/1.248GiB, zero forwards/updates/original arrays; roles/targetcounts exact.
Supplemental invented144³ step0 old/new probabilities/native masks exact,3.407s/2.954GiB;
initialweights3ee49a53 supports D-325 before baseline under unchanged policy/cache/geometry.
FirstCPUrequest retired unconsumed/source preserved before completion-bound resume strengthening.
Restricted review DiskManagement unavailable; source/reason retained, native audit then passed:
339physical/60jobfiles,96producing pins/registry exact; primary518,961,193B/independent
11,283,770,932B within new qualification-only frozen ceilings,no older quota reset/deletion.
Acceptancef7a2f6d9,review2a1c24de(18members/251,150B). D-319–325/6/1/all12/fiveholds/153/23
unchanged. Real updates remain denied; all qualification requests consumed,nonepending.
[Results](capstone/operations/SEGMENTER-TRAINING-TRANSACTION-RESULTS-2026-10-02.md);
[next completion packet](capstone/operations/SEGMENTER-SHORT-RUN-COMPLETION-PACKET-2026-10-02.md):
real executor/approval dispatcher,cadence/interruption,trained export/fresh14-target final scoring,
keeper/resource rehearsal before freezing a separate48-update candidate request. Rate0.0003/
48updates remain prospective; no exact real launch,extension,eligibility,cascade/jitter/promotion.

### October 3 — D-327 prospective short segmenter launch preparation

Prepare new executor/native-trained evidence/recovery contracts from D-326; synthetically rehearse exact48updates/0,6,24,48 boundaries before freezing a real request. No real updates or original payloads. Plan: capstone/operations/SEGMENTER-SHORT-LAUNCH-PLAN-2026-10-03.md.

D-327 complete:119 new/2,574 native tests, two existing warnings,92.03s. Full invented144³48-update
producer257.567s/5.495GiB RSS/4.879GiB sampled driver; exposure8 all6,0/6/24/48checkpoints and
all7native exports/scores/views. Cold14-artifact restore50.571s/4.360GiB with primary Python reads
blocked; four probes and7 native predictions exact,nextweights1.49e-8.48invented producer calls
plus1invented cold6→7call; zero real optimizer calls/original payloads throughout. Real cold adds0calls.
387protected physical/29jobfiles audited;111source pins/registry exact. Two read-only review-helper
faults preserved/corrected; no producing code/request changes.14target stats unchanged; real cache
ancestry replayed,no forwards/updates.6/1/all12/fiveholds/localizer153/23 unchanged, no quotareset.
Review09d78ecc (41members/662,196B),acceptance158a5d17,readinesse423cc91. Exact CAP-EXP-013
request `outputs/prowl/CAP-EXP-013-PREPARED-20261003/request.json`, SHA
`eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9`, remains UNCONSUMED/NOT LAUNCHED.
Freshseed42/144³/zerojitter/v3CE256+Dice/AdamW0.0003/48updates; terminal primary;30min total,
20min producer/5min cold/12GiB RSS+driver; final14target hash/decode1,265,220B each/272,494,704B
expanded,zeroCT.14required protected artifacts including selected7image bundle. New real areas
empty;2GiB primary and14,892,449,687B independent whole-root frozen ceilings, separate exact user
approval still required. Learning screens frozen before launch: all6original-native cases/components,
D-325 before baseline,2514separate; no extension/selection/eligibility/formal model promotion inferred.
[Results](capstone/operations/SEGMENTER-SHORT-EXECUTOR-RESULTS-2026-10-03.md); [exact launch review](capstone/operations/CAP-EXP-013-LAUNCH-REVIEW-2026-10-03.md). Next is the separate exact launch decision.

### October 3 — CAP-EXP-013 exact launch approved (D-328)

Quinton approved the prepared48-update,6train/1evaluation-only,144³ three-class segmenter diagnostic: “Yes, full approve. Continue on.” Exact requesteec73450; freshseed42,provided-pancreas ROI,zerojitter,v3CE256+Dice,AdamW0.0003,terminal primary. Final fresh14target scope and independent recovery approved within original30min/12GiB budget. Frozen learning screens unchanged. Preflight then one launch; no extension, imports or promotion.

D-328 complete: exact CAP-EXP-01348realupdates on6train/1evaluation-only,exposure8each,
0/6/24/48checkpoints/evaluations. Native lesion train/validation Dice0.030886/0.025448 and
recall0.994807/0.974468 pass frozen initial signal, BUT all7native pancreas-class counts/overlap0,
lesion volumes35–835×reference; no promotion. Saved tensor pancreas overlap0 bystep6; case3
pancreas probabilities finite but no argmax winners at24/48. Denominator shares suggest possible
loss imbalance,not measured gradients/proved cause. All cases/components/original references retained.
Producer367.416s/4.755GiB RSS/4.879GiB sampled driver; cold32.464s/4.119GiB with primary Python
reads blocked,four probes/7native exact,14artifacts independently restored;0coldoptimizer/originalreads.
403.118s(6.72min) total supervised.14original targets exactly1,265,220B hash/same decode/
272,494,704B expanded;zeroCT.387physical/29jobfiles,111source pins/registry exact; producingcode
unchanged,2,574-test qualification baseline unchanged.7technical views checked;no runtime/review faults.
Requiredpayload583,004,143B,primary583,047,635B/independent13,911,176,703B within unchangedfrozen
ceilings,no quotareset/deletion. Approval9f48d34c,producer23cf88bd,recovery744cf4cc;review633c7e09
(43members/658,643B),acceptance846c4aca.6/1/all12/fiveholds/localizer153/23 fixed. Requesteec73450
and both real jobs consumed;no pending run/continuation/autoextension/imports/source activation/formal registration.
[Results](capstone/operations/CAP-EXP-013-RESULTS-2026-10-03.md); [next proposal](capstone/operations/CAP-EXP-013-CLASS-COLLAPSE-FOLLOWUP-2026-10-03.md): bounded training-only zero-update objective/gradient audit, then select/qualify one loss-balance factor for a fresh same-cohort48-update comparison. No new analysis or training request is frozen/authorized.

## D-329 — CAP-EXP-013 training-only loss/gradient audit (October 3)

Quinton continued the proposed class-collapse investigation. New isolated loss decomposition/CLI/
26tests;2,600native tests pass. Exact attempt02 request97e75261 consumed:6training cases×saved
0/6/24/48,24forwards/48CE-Dice head VJPs,zerooptimizer calls/original payload opens/validation model
evaluations. Fresh qualified cache ancestry; same-run checkpoints only; all transaction state unchanged.

CE's pancreas bias gradient is positive in all24 (plain descent lowers the channel bias), while Dice's
opposing negative term is much smaller. CE/Dice whole output-head gradient norm ratios11.53–84.09.
Mean CE bias0.378104/0.262958/0.241593/0.190048 at0/6/24/48; Dice−0.000939/−0.001234/−0.001758/
−0.002756. Tensor predicted pancreas13,275,068→381→1→0,TP220,723→0→0→0. This supports measured
class competition; does not prove causality or prescribe the complete AdamW/backbone update.

Predeclared arithmetic weights[1,16,256]/[1,32,256]/[1,64,256], current fixed logits: early0/6 bias
upward0/12,6/12,12/12. Provisional64pancreas weight only; unchanged256lesion relative share drops,
so original tiny-lesion and negative learning bars remain necessary. Reconstruction6.11e-8;
no extra forwards/reads/validation. No real recipe changed or new training request prepared.

Native worker200.359s(202.195supervised),1.666GiB RSS/1.571GiB sampled driver. Four CPpayloads
188,625,652B,cache closure104,576,736B; six unique pairs89,579,520B, repeated4×358,318,080B.
Independent56files/810,813B numeric copy/readback verified,whole-root13,911,987,516B, oldceiling
retained;111producer pins/registry/cohorts/holds fixed. Prelaunch hash-print error refused before
consumption and fixed with new qualified attempt02; read-only interpretation NumPy-int error fixed
on a new output. Preserve all prior/failure records; no consumed run retried. CAP-EXP-013 primary48
remains unchanged. [Results](capstone/operations/SEGMENTER-LOSS-AUDIT-RESULTS-2026-10-03.md);
[next qualification](capstone/operations/SEGMENTER-LOSS-REBALANCE-QUALIFICATION-PACKET-2026-10-03.md).

## D-330 — provisional v4 synthetic learning failure (October 3)

Quinton dispatched D-329's qualification packet. Separate `[1,64,256]` objective/synthetic task/codec/
closed CPUrequest path;38new/2,638native tests pass. Frozen CPUrequest7ee8240c consumed once:
freshseed42/24³/AdamW0.003/480updates onfive existing invented class cues; baseline480 and actual
SIGTERM30/fresh450restart,960qualificationcalls,all synthetic. Exactfullmodel/optimizer/RNG/progress/
prediction equivalence. Total55.846s,maxworker0.728GiB; no real/sourcearray/imports.

Original learning bars fail: sparse/multiple/boundary lesions empty; outside-pancreas Dice0.470588/
recall0.333333;four offive lesioncomponentsmissed. Pancreas Dice0.955–0.968,negativeFP0,lossratio
0.258607 pass their bars. This is a learning failure with passing transaction mechanics. Do not advance
v4toMPS or realtraining. Preserve allcases/counts/criteria; no automaticdurationextension/filtering.

Numeric/fullstate review independent. Samefixedweights allocate sparseinventedpancreas93.03%/
lesion1.09% ofCEdenominator,versusv3's17.25%/12.91%; dependenceontargetcounts motivates proposing
per-case present-class meanCE next. Sharesare notgradients/causality and inventedsuccess/failure does
notprove realCTbehavior. v3's retained480syntheticpass wasnotrerun/imported. Nextproposal hasexact
formula/absence/negative semantics/original bars butno newrequestor acceptedloss.

CPUpackaged298c9d3(59files/188,880,118B),tests5f304229,reviewd94295ab;newindependentfailedsnapshot
67files/188,947,673B,manifest a69e1f78,all four8-member CPsdecoded withprimaryPythonreadsblocked,
zeroadditionalmodel/optimizer/originalreads. Whole-root14,100,935,189B, earlierceilingretained;
118pins/registry/cohorts/holds fixed,no unexpectedfaults/noMPS/newrealrequest/promotion.
[Results](capstone/operations/SEGMENTER-BALANCED-QUALIFICATION-RESULTS-2026-10-03.md);
[next proposal](capstone/operations/SEGMENTER-CLASS-NORMALIZED-CE-PROPOSAL-2026-10-03.md).

## D-331 — class-normalized CE synthetic learning failure (October 3)

Separate v5 per-case present-class mean CE + preserved foreground Dice;40new/2,678native tests
pass(100.76s), all118prior producers unchanged. CPUrequestbfd4b3a2 consumed, twofresh480-update
invented paths atseed42/24³/AdamW0.003;960synthetic calls, actualSIGTERM30/fresh450restart exact
fullmodel/optimizer/RNG/progress/predictions. Total58.084s,maxworker0.750GiB,no real/sourcearrays/imports.

Original learning gate fails. PancreasDice0.831–0.848 andlossratio0.353020 pass, but lesionDice
0.021–0.047 failsallfour positives. Sparse/boundary/outside recall1.0 with373/384/496predictedvs
8/8/12reference;multiple4/16TP,onecomponentmissed. Negative368false lesionvoxels/13,824=0.026620
fails0.02. Learningfailure cannot be waived by numerical/restart success. StopbeforeMPS/realrequest.

Independent read-only review reproduces metrics/bars/fullstate equality. Separate10-forward invented
terminalv4/v5 inspection(1.155s/0.582GiB,zerooptimizer/original/real/validationreads) reproduces saved
losses/metrics/nonmutation. v5falsepositives onboth backgroundandpancreas;negative151/217. Saved
last20epochmeans0.757289–1.340302,terminal0.850028,earlierminimum0.516616. No causal LRclaim or
selectedcheckpoint. Nextpacket proposes freshconstantCPU LR0.001, onechangedfactor/same480/
originalbars, notimplemented/frozen/launched. No automatic sweep/extension/filtering/softenedgate.

CPUpackage52211138:59files/188,884,855B;inspection2057c97d:4files/43,371B. Newindependentfull
failedsnapshot73files/189,009,159B,manifest681726f9;allhashes/four8-memberCPdecodes passwithprimary
Pythonreadsdenied,zeropreservationforwards/updates/originalreads. Whole-root14,289,944,348B,
fresh/earlierabsoluteceilingsretained,registry122sourcepins/cohorts/allholdsfixed,no unexpectedfaults.
CAP-EXP-013 remains consumed/terminal48primary; noMPS/realtraining/eligibility/imports/promotion.
[Results](capstone/operations/SEGMENTER-NORMALIZED-QUALIFICATION-RESULTS-2026-10-03.md);
[next packet](capstone/operations/SEGMENTER-NORMALIZED-OPTIMIZATION-PACKET-2026-10-03.md).

## D-332 — controlled low-rate v5 learning and native recovery pass (October 3)

One CPU scientific factor LR0.003→0.001, same v5/seed42/24³/five invented class cues/480/decay/
epoch permutation. All original gates pass: pancreas and positive lesion Dice/recall1.0, all five
lesion components hit, negativeFP0, lossratio0.006461. Two480 paths/960 invented updates, actual
SIGTERM30/fresh450restart exact model/optimizer/RNG/history/predictions;62.786s/maxworker0.748GiB.
Independent numerical/full-state review reproduces results. Last20epochmeans0.014543–0.033322,
terminal0.014543 versus retained failed LR0.003's0.850028. No real CT learning or optimal LR claim.

First sandbox `/bin/ps` fault consumed requestab730d92 before worker/model/updates; sealed fault
package98ff446e retained. Distinct native-preflight attempt02 binds that0-update fault and125source
pins, request7b5e649d/package64b7ae4d; no consumed rerun or old producing edit. Earlier self-import
wiring correction was pre-freeze; added regressions cover actual ancestry and native preflight.

Fresh144³/v5/MPS0.0003 qualification/recovery request089f975e/package3e13f53a: checkpoints0/2/4,
four clean/one dirty/one recovered optimizer call, eight forwards,47.285s/maxRSS2.818GiB/driver4.839GiB.
All three eight-member payloads restore with primary reads denied. Probe/native mask/derived-invented
target scores exact, nextloss0 and weightdelta1.033e-8. Native step2 lesion prediction remains empty
against4,140 invented native voxels; no native learning gate or real-reference claim. Preserve failure
patterns; no promotion.65new/2,743native tests pass,129pins/registry/cohorts/holds fixed.

CPU/fault snapshot87files189,101,113B, native32files227,218,858B, numeric30files175,563B protected
and verified, manifests03973c58/3fd1ed40/4158dbeb. Whole backup root14,706,439,882B below fresh/
retained limits, no cleanup/reset. Only186,009,805B remain under retained D-328 ceiling; nextreal
comparison cannot fit without a reviewed new stage allowance. Real v3/CAP-EXP-013 terminal48 remain
fixed/consumed; no real inputs/updates/eligibility/source activation/import/promotion/registration.
Next proposed real-v5 consumer/recovery/read-scope/screens and explicit capacity/request review;
same6/1/48 and realLR0.0003, separate exact launch approval. No new real implementation/request/run.
[Results](capstone/operations/SEGMENTER-LOWRATE-QUALIFICATION-RESULTS-2026-10-03.md);
[next implementation packet](capstone/operations/SEGMENTER-V5-REAL-COMPARISON-PACKET-2026-10-03.md).

### 2026-10-03 — D-333 isolated v5 executor preparation; native rehearsal not launched

2,933 native tests(190 new),118.03s/two existing warnings. Separate v5 real-capable identities,
exact dispatcher/target scope/backup catalog and fixed-capacity approval gate implemented;129 old
pins preserved,142 total. CPU unit completion/dirty failure/resume/roles/counts/terminal policy pass.
Fresh seed42/144³/48/6+1/0.0003 comparison retains every real case; v5 loss is the only proposed
scientific change. Training-only pancreas/lesion/component screens and FP-volume reporting fixed;
2514 remains report-only. No real/source/processed-real arrays consumed or model promotion.

Exact invented rehearsal request8e2dcc5d/capabilitya318b3b6 prepared,unconsumed; full48native+14
independent restores pending exact capacity review. Backup remains14,706,439,882B/oldceiling14,892,449,687B;
2GiB new allowance/whole ceiling16,853,923,530B proposed only. Bound1,974,853,376B/headroom172,630,272B;
registered20GiB unchanged. No external writes or cleanup. Final suite corrected a pre-freeze control
size-guard error; earlier failed logs retained. No CAP-EXP-014 request/real approval yet.
[Results](capstone/operations/SEGMENTER-V5-EXECUTOR-RESULTS-2026-10-03.md).

### 2026-10-03 — D-334 full invented v5 transaction and recovery pass

48+1 invented calls,6train/1eval,14 artifacts/387 three-copy files,7 native predictions exact; probe0/nextweights7.45e-9. Combined363.490s, producerRSS5.532GiB/driver4.776GiB. All7 sheets reviewed; toy/native mechanics scores are not real performance. Frozen142 pins/2,933 tests unchanged; zero real/source/processed-real reads/updates. Both jobs consumed; no autoextension. Readiness accepted; fresh14-target stat-only scope prepared. Exact real CAP-EXP-014 and actual capacity remain separate approval. [Results](capstone/operations/SEGMENTER-V5-REHEARSAL-RESULTS-2026-10-03.md).

D-334 follow-through: real CAP-EXP-014 requeste63f5613/cap85b9a90c prepared only; accepted processed-cache resolution, no original arrays/forwards/real updates. Base16171162225B/fixed proposed ceiling18318645873B. Await exact separate storage/read/launch approval. [Review](capstone/operations/CAP-EXP-014-LAUNCH-REVIEW-2026-10-03.md).

D-334 bookkeeping correction: actual real capability transport5dfc16d1 differs from canonical85b9a90c. Preparation-review-V2/current launch review identify both; unchanged exact requeste63f5613. Final preservation caught mismatch before writes. No producer change or real launch.

### 2026-10-03 — D-335 / CAP-EXP-014 v5 comparison complete

Freshsame6/1/48/144³/0.0003; numerical factorCEallocation/reduction only. All training screens pass: pancreasDice0.159877 vs v3zero, lesionDice0.055142 vs0.030886, recall0.833063 vs0.994807; all6components hit. Lesion volumes12.78–383.26×, poor precision;2514 lesionrecall0.123936 vs0.974468/Dice0.006397. No generalization/promotion claim.14originaltarget reads/0CT; independent14restores,7native predictions/4probes exact,0cold updates/source reads. Combined525.229s, producerRSS4.790GiB/driver4.776GiB. All7sheets and native arithmetic reviewed;142pins/2,933native-test baseline unchanged. Both requests consumed; no automatic extension. Source/cohort/hold/qualification state fixed. Next discussion: saved training evidence, exact fresh duration/coverage proposal and multiclass expansion readiness. [Results](capstone/operations/CAP-EXP-014-RESULTS-2026-10-03.md).

Saved training-only history audit, no new model/source/cache calls: mean loss2.037188→1.692695; pancreas/lesion tensor Dice at24→48 improves0.106990→0.159272 /0.038591→0.054626. Duration remains a hypothesis requiring a fresh bounded recipe/request; no extra run launched.

### 2026-10-07 — D-351 / R01 duration attempt stopped at48

Quinton explicitly approved the exact fresh scientific request60f3cc51 (DURATION-CAP-EXP-015-192/
DUR_REAL_20261007_R01), after I03 inference-only qualification and metadata preparation. Same
six training members/protected roles/v5recipe/seed42/144³/MPS/0.0003/zerojitter; requested192
updates/screens48/96/144/192,2514terminal report-only. Original DUR-01 coverage/FP stops unchanged.

Actual48updates/68forwards,eight per train member; checkpoints0/48. Native screen48 stops:
lesion macrorecall0.691498 vsD3350.833063/floor0.803063;case3/26/5821 lesion/component recalls fail.
PancreasDice0.181887 vs0.159877,lesionDice0.058952 vs0.055142;meanlesionFP111.866668mL vs162.628931.
All six components hit,tiny2973recall1.0,all interim per-case FP and pancreas checks pass. This
tradeoff does not meet coverage;192duration comparison unanswered,2514not evaluated. Six masks/
views/screen/summary/two checkpoints kept;all six sheets and native arithmetic reviewed.

Twelve original targets/0CT;hash/decode1,173,533B each,expanded253,698,624B. Conditional cold
restores16artifacts with0forwards/updates/original reads;no fresh prediction equivalence test,
full_duration_qualified=false,optimizer resume unqualified. Producer545.335812s/4,870,045,696B
sampled owned RSS; cold35.344273s/2,573,090,816B;helper654.297251s/5,611,421,696B aggregate,
workers reaped/lockreleased/no watchdog fault. Both stages consumed/retired,no retry or extension.
Whole backup20,031,773,929B/R01growth407,564,812B,totaltwo-phase2,689,849,293B;fixed26GiB/original
baseline+8GiB/freefloor preserved;402producing pins unchanged,no production/policy changes.

Retained JSON histories show exactsame48member andimage/targetbatch-hash sequences asD335;
firstloss exact,small differences beginupdate2 and later diverge. Root cause and long-run
significance unproven;no extra model/optimizer/sourcearray/weight calls for that review. No
longer-training failure claim,model promotion,generalization or negative specificity. Next discuss
prospective stop design and coverage/FP/history tradeoff before a new scope. [Reviewed handback](capstone/operations/SEGMENTER-DURATION-R01-RESULTS-2026-10-07.md).

### 2026-10-07 — FULL-SEG-MAC-001 / full_segmenter_suprem_mac_01 — preparation in progress

Quinton requested a long experiment through the new capstone session/executor, selected SuPreM,
and required broader native-size/tilted-geometry support before launch. This is a fresh development
experiment, not R01 continuation, EXP-24 reproduction, or a published PanTS benchmark claim.

Planned recipe: capstone SegResNet (16 initial filters, three-class fresh head), strict transfer from
the publisher's `supervised_suprem_segresnet_2100.pth` (SHA-256 `2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3`),
normalized v5 loss, seed42, 144³ pancreas-only physical ROI/10mm margin/1mm intermediate sampling,
geometry v2 including tilted affines, AdamW LR0.0001/weight decay0.00001,500-update warmup/cosine,
24,000 updates, development every2,000, initial/latest/best checkpoints and saves every500.
No update48 recall stop is inherited. Stop on invalid inputs/numerics, resource/IO/backup failure,
or completion of the configured horizon. Native optimizer continuation is not qualified/enabled.

Candidates are1,412 original-role training members (706 historical positive/706 historical empty)
and80 original-role development members (40/40, deterministic seed42). Final membership will be
frozen after the complete real content/geometry audit; every failed case is an explicit exclusion.
Empty references remain annotation-background targets, not verified healthy patients. No original
test arrays are requested. The primary selection metric is positive-case macro lesion Dice on the
tensor grid; native full-scan evaluation remains separate. Pretraining/selection scan membership is
unverified and recorded as a limitation of this development-only source use.

Engine: `scripts/train_full_segmenter.py` → `segmenter_full_session_v1` /
`segmenter_full_executor_v1`; not `scripts/train.py`. Current allocation:24h upper limit/12GiB
owned worker RSS/32GiB external derived cache/100GiB free floors, external primary checkpoints
with verified internal backups under the existing total ceiling. This is not an ETA.

Real preprocessing is running at `outputs/prowl/full-segmenter-content-mac-20261007/`; it performs
no model forwards or optimizer updates. Model training has **not started** in this registration.
The separate invented native profile and actual CPU SuPreM import are engineering evidence only.
[Implementation and evidence](training-full-segmenter.md).
