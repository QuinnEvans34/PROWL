# Full training scale review — October 7, 2026

**Finished: repository-text and retained-result review. No new model job or source payload read.**
Quinton asks why tonight's run was so short compared with his previous roughly 14-hour models,
and requests full training experiments. R01 remains stopped/consumed/retired at48; no job is live.
This document records findings and recommendations, not an approved new recipe, cohort, policy,
resource allocation, implementation packet or scientific launch. All historical evidence remains.

## The scale mismatch

| Experiment | Training scope recorded in the living notebook | Meaning and limitation |
|---|---|---|
| EXP-03/04/05 | 6,000 updates; original approximately100-case development subset; SuPreM transfer | Earlier full model-development runs, rather than tiny wiring checks. |
| EXP-17b | Planned600cases/8,000updates; recorded7–8h plus cache fill | Historical scale plan; its result is unfilled in this section and its derived split was later audited. Do not invent a completed outcome. |
| EXP-17c | 1,412cases (706positive/706healthy),24,000updates; recorded13–14h plus cache fill | Recorded.524raw/.528cleaned lesionDice was WITHDRAWN:30/40positive evaluation cases overlapped training. Methods and failure lessons remain useful. |
| EXP-24 | Leakage-repaired1,412-case training split; SuPreM/whole-box128³/1.5mm/DiceFocal/24,000updates | Recorded development lesionDice.415raw/.412cleaned; selected best checkpoint at18,000. Provided-ROI, development selection and historical provenance remain explicit. |
| EXP-26 | 1,249train; paired24,000-update arms | An apparent12,000-update auxiliary-task win was overturned at24,000. Do not judge a full-horizon comparison from its intermediate trajectory. |
| D-335/CAP-EXP-014 | Six positive train/one report-only; fresh scratch144³/v5CE+Dice/48updates | Qualified engineering pilot; lesionDice.055142 on training. Not a prior-quality reproduction or broad baseline. |
| R01 | Same six train; maximum192updates, stopped48 | 48actual updates/68forwards, eight exposures per member. LesionDice.058952/recall.691498 failed the unchanged coverage stop.192duration question unanswered. |

The [living notebook](../../experiments.md) is the source for these historical accounts; this review
does not independently re-score or validate old weights. 24,000 is500times48 and125times192;
even the proposed192 was only0.8% of the older24k update budget. Different data/geometry/loss/
initialization/batch conventions prevent treating these ratios as equivalent compute or exposure.

The old [training entry](../../../scripts/train.py) supports an explicit `--max-iters` and checkpoint/
validation cadences. The historical [configuration](../../../configs/level45.yaml) has100epochs×250
iterations=25,000 by default. This is a configured loop unit, not a claim of100 complete passes through
the cohort. The current duration session/executor instead explicitly restricts native jobs to192
steps and six members. Changing a number in a legacy YAML cannot turn that qualified consumer into
a full-scale trainer. No legacy command was executed or offered as current launch authority.

## Where the disconnect started

1. **September18 capstone reset:** preserve old methods and lessons, but create new capstone models,
   protected memberships and evidence. [D-003](../DECISIONS.md) and
   [model lineage](../imaging/MODEL-LINEAGE-AND-TRAINING.md) prohibit old course-trained weights;
   they do not prohibit reusing appropriate code or learning from the old experiments.
2. **September28 readiness plan:** explicitly targets a1–4case scratch pancreas smoke before class.
   That was a reasonable pre-course wiring goal, separate from the full model-development objective.
   [Plan](TRAINING-READINESS-IMPLEMENTATION-PLAN-2026-09-28.md).
3. **By October3:** localizer and three-class segmenter mechanics worked, but broad multiclass
   qualification/generalization were still missing. [Retrospective](PRECOURSE-RETROSPECTIVE-2026-10-03.md).
4. **October6:** the historical review explicitly recognized the prior24k/larger-cohort recipe and
   recommended varied-data/pretraining readiness. Separately, the duration proposal selected48→192
   with six cases, engineering20% relative improvement targets and a60minute budget. That is where
   the next training milestone remained much smaller than Quinton's intended full training sessions.
5. **October7:** missing SuPreM source/selection evidence motivated the scratch192 fallback; engineering
   preparation became the main activity. R01 then stopped at its first48screen. Calling that path
   “ready for training” without repeatedly stating its small scale obscured the remaining gap.

Codex should have made the experiment class and expected training scale explicit when Quinton asked
to train through the night. Actual training was launched, but the selected scope did not meet that
full-model intent. This is a planning/communication mismatch, not an established hardware or loop fault.

## Correct the next scientific objective

**Recommendation for discussion: prepare a new full development baseline, not another192-step
extension as the main model-development milestone.** The useful finish is a sufficiently trained
new model on a varied registered training cohort, evaluated on separate development data with
lesionDice, detection/coverage, excess foreground and verified-negative specificity reported.
More hours alone do not establish strength, and long fitting of six cases cannot establish it either.

Proposed baseline planning envelope, not yet frozen:

- Use a **24,000-update maximum** as the historical starting reference. Decide the schedule with
  initialization/cohort/loss, measure throughput and freeze its actual time/memory/storage budget.
  This is not an optimal/converged horizon established for the new scratch recipe.
- Plan a cohort in the **hundreds of qualified cases**, with explicit positive and verified-negative
  representation and **dozens of train-disjoint development cases**. Review whether an initial
  approximately300-case baseline or a larger cohort is feasible from retained metadata before
  selecting exact IDs/counts. Do not silently reuse historical1,412 memberships or assume empty masks
  are negative. Preserve every original role, hold, difficult case and failed outcome.
- Record checkpoints/trajectory at useful full-run intervals, tentatively500–1,000updates for recovery
  and1,000–2,000 for development validation; expose6k/12k/18k/24k trajectory. Choose one frozen
  development checkpoint-selection rule/tie-break, or a terminal-only duration design. These are
  different designs; do not mix them or repeatedly tune on publisher-test data.
- Separate **operational/data-integrity stops** (invalid inputs, nonfinite computation, memory/disk,
  ownership or checkpoint failure) from **model-quality acceptance**. Prospectively review whether a
  quality dip during warm-up is descriptive or terminates a new run, with explicit cadence/patience
  and rationale. R01's original stop and failed status remain fixed. Do not waive it retrospectively.
- Reuse existing geometry, cache, scoring, provenance, checkpoint and trainer work wherever it fits.
  Identify the smallest long-run/cohort integration delta before code. No unrelated product feature,
  new framework or repeated full suite is required merely to fill the preparation time.

The historical [EXP-33](../../experiments.md) already proposes24k→72k to investigate undertraining.
Carry forward that question after a stable full baseline; redesign its old publisher-test curve
around permitted development data. EXP-34's training-versus-development gap can then distinguish
fitting from generalization; EMA/anisotropic context/PANORAMA follow as separate selected comparisons.
Do not import the notebook's historical numerical claims about external papers as fresh verification.

## Actual prerequisites and next bounded work

| Dependency | Current evidence | Necessary next work |
|---|---|---|
| Segmenter cohort | Only6qualified positive train/2514report-only;5reviewed holds; no verified negatives | Metadata-first expansion/negative-standard/development-shortage proposal, then qualify selected new members/cache under exact scope.153localizer-qualified members do not grant lesion use. |
| Initialization/recipe | Scratch path works. SuPreM released metadata matches; actual scientific source/selection acceptance still absent | Use a separately planned scratch full baseline unless evidence resolves. A SuPreM-based reproduction remains conditional; no automatic import or publisher outreach. |
| Long-run consumer | General historical trainer exists; current capstone consumer is six-case/192-only | Review reuse of the legacy loop with current cohort/cache/role controls versus extending a reusable capstone runner. Freeze a minimal integration allowlist and only necessary checks. No full reimplementation is presumed. |
| Recovery | I03saved inference qualified; R01stopped artifacts restored. Exact next-update/optimizer resume unqualified | For a fresh uninterrupted full run, declare durable checkpoint retention and honest interruption outcome. Resumable multi-day/day-night operation needs a separately scoped numerical recovery criterion and focused check. Bitwise equality is not silently replaced. |
| Budget |26GiBwhole-backup ceiling remains; N02+R01's two-attempt allocation is spent | Inventory proposed full-run/cache/checkpoint writes and reserve within a new concrete allocation. Preserve originals/failures; no deletion or cap increase is implied. |

[Varied-data inventory](VARIED-MULTICLASS-GAP-INVENTORY-2026-10-06.md) is the existing starting point.
Its retained176candidate pool has only16train/two development positive hints, not qualifications;
2514 is qualified and5641 held. More candidates from original roles may need metadata discovery.
The current six-positive cohort is usable for a long **fit diagnostic** after a fresh approved scope,
but that must be named honestly and cannot stand in for this full development baseline.

**Exact next recommended task:** combine the existing data-gap inventory with a repository-text
long-trainer reuse review into one finite full-baseline readiness packet: proposed cohort/counts and
qualification cost, scratch recipe versus conditionalSuPreM, reusable code/minimal changed files,
full horizon/validation/selection/stops, and measured-budget work still needed. Present that scope
before implementation or new actual-data/model operations. Do not make another micro-run the default.

## Timing and numerical caveats

The notebook's approximately13–16hour runs used a different128³/pretrained/data/loss path. Tonight's
545second producer includes input resolution, native scoring and checkpoint work; dividing by48
does not give pure steady-state step time. We have not measured the new full-cohort run. Its ETA and
tonight launch feasibility are unresolved; no promised1–2hour preparation or14hour runtime follows.

Retained R01/D-335 JSON shows matched case/batch-hash order and loss differences beginningupdate2.
The [PyTorch numerical-accuracy guidance](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html)
explains that mathematically equivalent floating-point computations need not be bitwise identical;
[reproducibility guidance](https://docs.pytorch.org/docs/2.14/notes/randomness.html) describes the wider
controls involved. This is general context, not proof of R01's cause, harmless long-run divergence,
or acceptance of the installed backend. Do not spend another day chasing unproven numerical causes
as a substitute for agreeing on the full training objective.

## Review boundary and handback

Workspace/root/status/checker passed; startingHEAD e71e5f6, clean worktree. Texts reviewed: living
experiments (early runs/EXP17c/24/26/32–34/current boundary), legacytrain.py/level45config, model
lineage, September28readiness, October3retrospective, duration proposal/results, current data gaps
and SuPreM evidence. No successful tests/model jobs were replayed, no arrays/weights acquired/read,
no source qualification/control/capability/job prepared and no numerical/policy/cohort edits occurred.
Human hours remain separate from unattended review/runtime; no clock-out or portal entry inferred.
Reviewed local preservation is allowed; public push is not. New full-training work requires its
concrete scope; this review grants none by scheduling or its completion.

Static review verified local references, whitespace and all402 producing pins; the notebook's
protected marker-to-end history is byte-for-byte unchanged. W01-12's updated description was
read back; its SuPreM task remains To-Do/incomplete and W01-28 remains Done for the retired R01.
