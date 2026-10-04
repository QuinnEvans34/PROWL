# CAP-EXP-004 — longer lower-LR balanced learning check

D-279 records this final bounded overnight choice under Quinton's D-277 authority. CAP-EXP-003's mean
Dice0.10994 passes the minimal learning indicator but its predictions remain16–18× reference volume.
Question: does a longer optimization budget substantially tighten the predictions on these same cases?

Retain CAP-EXP-003's balanced CE+foreground Dice, LR0.0003, weight decay1e-5, scratch seed42 and
original parameter digest, two-case qualified cohort/input/recipe pins,96³/batch1/fp32 native MPS,
member order/stateless crop keys, no augmentation/cache/workers, image-only full-volume inference and
argmax. No old checkpoint initializes training. Change max_steps100→300 and matched cosine T_max100→300.
The same cosine policy is spread over a longer run: this changes the LR trajectory at a given absolute
step and is not an isolated extra-steps-at-identical-LR-sequence experiment. Report that limitation.

Checkpoint and telemetry stages0/75/150/225/300 (cadence75) preserve the same five-stage budget.
Intermediate probes/evaluation do not update the model or select a checkpoint. Retain both objectives,
class contributions, full-volume foreground Dice/counts/probabilities, fixed patch probes and all
training crop fractions. Native before/after masks/contact sheets and final independent backup/restore
remain mandatory. Verify first100 crop traces match the earlier runs;150 updates/case if complete.

Preserve the same indicator (balanced objective decrease≥10%, Dice gain≥0.10), but interpret outcome
against CAP-EXP-003's remaining overprediction. Passing this weak indicator does not establish useful
contours. No threshold tuning, best-checkpoint replacement, cohort/role change or generalization claim.

Limits remain600s update phase (including interim evaluation),1,200s total,16GiB RSS/MPS,1GiB new
bytes/domain, existing floors,AC/exclusive accelerator ownership. Measured iterations are about1.5s;
300 updates project to450–510s plus staged evaluation/publication, within but closer to the600s phase
ceiling. Stop at the existing limits even if300 updates are incomplete; no automatic extension/retry.
Max300 is accepted only for explicitly balanced configuration; real use is further constrained to
this exact registered plan. Other original recipes and guards stay fixed.

Test300-step scheduler/config/checkpoint binding and rejection beyond the new bounded configuration;
run the synthetic native route; freeze exact request/source/environment and authorization before
compute. After this attempt, inspect and document results and finish the overnight handoff. Any
further training becomes a new daytime plan rather than an unbounded unattended search.
