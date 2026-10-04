# CAP-EXP-002 — equal-class CE, fixed two-case comparison

D-277 authorizes implementation and bounded execution under Quinton's overnight direction. This
plan is frozen into the exact prepared request after verification; do not edit it after preparation.

Only scientific factor changed from CAP-EXP-001: CE becomes the arithmetic mean of foreground and
background class means when both occur. Single-class patches use the available class mean. Stable
logits CE plus the unchanged foreground Dice term; loss ID `balanced_ce_dice_v1`, identity schema4.
The prior voxel-averaged loss and schema2/3 checkpoint loading remain available unchanged.

Keep exact frozen cohort3/26, input/recipe pins, protected train roles,96³ patches,batch1,fp32 MPS,
seed42,AdamW0.003/weight decay1e-5,cosine100,100 alternating updates,no augmentation/cache/workers.
Scratch parameter digest must equal original step0
`365306b1aec77681bd651a1e87ca7902b10efffef38607f1618303220d20954e` without loading old weights.
Class-balancing is computed per sample. No tuning of the0.5/0.5 class weights or inference threshold.

At0/25/50/75/100, evaluate both full volumes image-only and retain separate balanced and legacy
losses, foreground Dice, counts and probability summaries. Probe the same fixed recorded positive
patches (case3 sampler step2;case26 step3). Probe gradients are local logit diagnostics, not model
parameter gradients. A final trajectory record contains all five stages. Before/after native masks
and contact sheets remain included. Intermediate evaluations are observational, never change training
or select a checkpoint. Preserve fixed-step final result even if an intermediate result is better.

Learning indicator: at least10% decrease in the **balanced evaluation objective's own** before/after
mean and foreground Dice gain≥0.10; compare experiments on common Dice and legacy objective, not
on unlike absolute loss values. Report false-positive foreground/volume ratio and both cases even
if the indicator passes. These are training-case measurements, not generalization.

At most100 updates,600s update phase including intermediate evaluations,1,200s overall;16GiB RSS and
MPS limits,1GiB new bytes/domain,100GiB internal floor and existing external headroom,AC and exclusive
MPS owner. Checkpoints0/25/50/75/100; terminal independent backup and fresh-process restore with
primary reads refused, fixed-probe probability tolerance1e-5. No automatic retry, continuation,
threshold promotion, checkpoint reuse, global activation or raw-source modifications.

First execute a two-update synthetic rehearsal using the same version4 objective/persistence path.
Prepare source/environment/input/plan hashes only after tests and rehearsal pass. The authorization
record must cite D-277 and bind those exact controls. Launch claims prevent duplicate execution of a
prepared request. Preserve failed/partial attempts without automatic rerun. Results determine the
next bounded action; this plan itself authorizes only this comparison and its rehearsal.
