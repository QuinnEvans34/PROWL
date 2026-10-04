# Proposed next experiment — gentler foreground/background class-mean balance

**October1 update:** Quinton accepted this proposal underD-312: “Great, continue with that. Great work.”
[CAP-EXP-011 prospective design](CAP-EXP-011-LAUNCH-PLAN-2026-10-01.md) now governs bounded
implementation/qualification/launch. Original pre-approval status and recommendation below are
retained as history;no gate is waived and no old consumed request is resumed.

**Proposal for discussion; not approved, implemented, request-frozen or launched.**
[D-311 audit](LOCALIZER-FOREGROUND-AUDIT-RESULTS-2026-10-01.md) is complete and consumed.
All previous recipes and153members/23holds remain unchanged. Reserve a new CAP-EXP identity only
after the next design decision; do not modify or resume007/010's consumed requests.

The evidence supports increasing background pressure while preserving useful sparse-target
pressure. Current CE+Dice already favors uniform foreground shrinkage on seven of eight fixed
probes, so the hypothesis is not that current loss always expands masks. A hard cap50 nearly
eliminates CE pressure on the six-voxel cropped reference. The gentler alternative below keeps
class-mean protection while changing one factor. Its observed scalar directions are hypothesis
generation, not proof of improved optimization or an optimal balance.

## Proposed exact formula

Let `F` be foreground target voxels, `B` be background target voxels and `p` the existing two-class
softmax foreground probability. On patches containing both classes:

```text
CE = 0.25 * mean(-log(p[F])) + 0.75 * mean(-log(1-p[B]))
DiceLoss = 1 - (2*sum(p[F]) + 1e-5) / (sum(p) + |F| + 1e-5)
Loss = CE + DiceLoss
```

Compute CE stably from logits, not clipped probabilities. On empty targets use background mean
CE alone and omit Dice, matching current behavior. On all-foreground targets use foreground mean
CE alone plus the same Dice. Fixed sole-class normalization prevents accidentally scaling empty
patches by0.75 or all-foreground patches by0.25. Validate binary nonempty targets and finite logits.

This changes the current0.5/0.5 **class means** to0.25/0.75. It is not per-voxel class weights0.25
and0.75. For mixed patches the equivalent foreground/background voxel coefficient is
`|B|/(3*|F|)` under weighted-mean normalization. Large ratios on tiny targets persist, but their
aggregate foreground contribution is reduced moderately rather than by thousands of times.
The same Dice coefficient/smoothing remains1/1e-5. No support masking or hard weight cap is added.

## One changed factor and matched reference

Start from the exact independently backed-up007step300 model **and AdamW state**, as010 did.
Use300 new updates at constant0.00001, absolute sampler300–599, same113train/40development-validation,
144³/2mm cache, seed42, batch1, architecture, weight decay0.00001, precision and padding.
Keep argmax/native export/10mm margin/metrics/checkpoint selection policies unchanged.
Only CE class-mean weighting changes. No negative sampler, threshold tuning, new cohort,
augmentation, preprocessing or geometry change is coupled to this test.

Compare against010's frozen0/150/300 native records; the candidate starts from007, not010logical600.
Do not label this a fresh600-update replay. This is an exploratory matched intervention with an
existing single control run, not formalG5 or a replicated causal estimate. D-309's native fresh-run
variation is relevant; exact imported initial weights/masks do not prove subsequent stochastic
trajectory parity. Preserve inherited AdamW moments; resetting them would introduce another factor.

## Coverage and usefulness before candidate execution

Retain010's existing checkpoint cadence0/150/300 and validation guards. At initial0 reproduce
all40 imported007 native masks exactly. At active150/300 boundaries stop if:

- mean native validation recall is below0.95;
- minimum validation recall is below0.65;
- fewer than38/40boxes retain at least0.995reference coverage; or
- mean validation recall drops more than0.03from the best previously evaluated checkpoint,
  including imported0.

Proposed usefulness target retains010's frozen parent-relative criterion: median validation volume
at most13.872506x (25%below007's18.496675x), at least10/40ROI screens, mean recall at least0.962700
and all40boxes retaining at least0.995reference coverage. Also report matched per-case differences
against010 at150/300, native Dice/precision/recall/box/crop/volume and actual stopped prefix. A candidate
does not become better merely by achieving a smaller scalar loss under a different formula.

Keep tiny/partial cases and their evidence. Explicitly inspect validation3115/2727 and previously
passing6534; training7604/7684/6110remain mandatory terminal inspection examples if completed.
Aggregate pass does not hide an individual regression. Do not relax guards after seeing treatment.
No model promotion or automatic duration extension follows a passing exploratory result.

## Bounded implementation after the design decision

1. Add an explicit versioned loss/config identity and dedicated dispatch; keep old constructors,
   records, checkpoints and consumer behavior byte-compatible. Reject implicit substitution of a
   new objective into010 or an old checkpoint's declared recipe. Verify a machine-readable
   changed-factor comparison and inherited optimizer/model digests.
2. Test arithmetic/finite parameter gradients on invented sparse/dense/empty/all-foreground and
   extreme-logit inputs, including incorrect voxel-weight interpretation and sole-class scaling.
   Verify background-only optimization and sparse-target learning retain meaningful gradients.
   Add only meaningful refusal/recovery regressions appropriate to the new version.
3. Run a native invented MPS learning/checkpoint/interruption/independent-recovery transaction
   under the new loss identity. Prove the saved objective/config replays and continuation refuses
   mismatched loss, ancestry, sampler position or consumed requests. Model/AdamW import retains
   exact parent state; new objective does not retrospectively alter the parent's identity.
4. Freeze a separate zero-update real-cache qualification request, reproduce all40 imported native
   masks and independently restore its keepers. New loss must not change initial inference.
5. Prepare a fresh stage-specific training/reference/resource request only after qualification.
   Proposed budgets match010: qualification40reference reads/noCT,900s; training233reference reads
   (40initial+40middle+153terminal),45min including recovery,16GiB RSS/driver,4GiB output,AC/exclusive
   MPS/100GiB free floor. Revalidate exact compressed/expanded bytes and storage receipt identities;
   these are proposed ceilings, not a reusable read authorization or current frozen request.
6. Bind the next explicit design/run authorization to that immutable request, launch once, preserve
   any stopped attempt, independently recover all keepers and verify native exports. Record results
   and next decision before any further experiment.

CurrentD-311 authorizes detached audit/postprocessing and this discussion document, not these real
updates or production loss implementation. The next decision is whether to test this specific
25/75 class-mean alternative. Sampling/support masking remain separate later factors; held empty
references cannot be used as convenient negatives. Lesion/cascade work, formalG5 and untouched
holdout evaluation remain separate project work, with no requirement to finish literature first.
