# D-276 — bounded optimization investigation after CAP-EXP-001

Quinton requested investigation of optimization behavior and other necessary factors. Start with
retained evidence and read-only model diagnostics; do not extend CAP-EXP-001 or start a comparison
training run as part of this diagnostic. Original source, targets, checkpoints and receipts remain
unchanged. Codex owns the diagnostic helper/tests and separate evidence/report; retrieval untouched.

## Questions and measurements fixed before execution

1. Replay all100 recorded crop choices on the two qualified cases. Verify exact trace equality,
   foreground counts/fractions and coverage, rather than infer target presence from center class.
2. Resolve the exact retained steps0/25/50/75/100 through their receipt/identity validators. On each
   case, run image-only full-volume inference and record foreground/background probability
   distributions, CE contributions, foreground soft Dice loss, argmax counts/Dice, and diagnostic
   threshold points0.01/0.05/0.1/0.25/0.5. Threshold points describe training-case behavior, not a
   tuned operating threshold or a change to the frozen experiment's evaluation.
3. At each checkpoint inspect one fixed recorded foreground-centered patch per case (first such
   patch in the actual sequence). Separate CE/Dice gradients with respect to the foreground-minus-
   background logit. Report per-class signed sums and magnitudes. These are local logit derivatives,
   not parameter gradients or proof of the effect of a future AdamW step. No optimizer updates.
4. Compare loss against constant-probability baselines; inspect saved scheduler/LR trajectory and
   verify model bytes unchanged after inference. Reproduce original step0/100 metrics within1e-5.

## Scope and bounds

Exactly the frozen3/26 cohort and four source files, loaded once per case via the qualified loader;
retain the two processed arrays in RAM for this diagnostic only. Replay100 patches without model
updates;10 full-volume forward passes and10 fixed-patch forward passes maximum. Native MPS fp32,
fallback disabled,2 CPU threads, exclusive existing accelerator lock, AC,600s overall,16GiB RSS and
MPS driver/allocator bounds,256MiB new internal diagnostic output,100GiB internal free floor.
Resolve existing artifact roots with creation disabled. No new primary/backup writes, global root
activation, remote work, installs, threshold promotion or checkpoint selection. Parent supervisor
retains partial logs/failures and enforces time/power/memory; no automatic retry.

Test decomposition against hand-computed CE/Dice and finite differences, validate inputs, and ensure
zero logit updates. Preserve original model source/environment alongside diagnostic source/control
hashes. Capture exact request and each checkpoint receipt in the result. If these diagnostics support
an optimization comparison, document the concrete single-factor proposal and its remaining limits.
