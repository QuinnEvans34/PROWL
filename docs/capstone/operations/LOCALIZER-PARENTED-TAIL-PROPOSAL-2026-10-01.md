# Proposed parented low-rate tail after the native replay finding

**Latest status:** Quinton approved this parented design under D-310 for CAP-EXP-010. Implementation/qualification precede the exact request and single launch. The proposal below preserves its earlier context.

**For discussion, not authorized, implemented or request-frozen.** D-309 approved a fresh matched
replay. This proposal changes that experimental design and needs Quinton's decision. No consumed
request or stopped session is resumed. See [the native finding](CAP-EXP-009-PREFLIGHT-RESULTS-2026-10-01.md).

## Question and reason

Does another 300 case exposures at fixed LR 0.00001 shrink excess foreground while retaining coverage,
starting from the known CAP-EXP-007 step300 state? The fresh-replay design cannot currently establish
its numerical prefix criterion on native MPS, even for two original-schedule synthetic controls.
Importing an immutable parent removes fresh early optimization as a source of comparison variance.
This does not prove why those native gradients diverge or guarantee subsequent learning improvement.

## Exact proposed experimental scope

Use CAP-EXP-007's independently backed-up step300 checkpoint, identity
`8614cdcc1322ae8b103575b5db9068a82f48df1fe507aca0429763218ac3636f`,
weights `8db271a2f458386e4fd33af7bd3540bade4ebd23a19e79b565c9b8715c8ea988`,
primary receipt `f7f48677a3fadf00a8d280d149089aaef2aea9e99a76c3b91d1800eb36f574bf`,
backup receipt `29fc13699f771e100d48eb0bfdbd17fd9e14a5df087d88ad14bbfa5d763edbb9`.
The actual model weight pin is recorded in the retained reference and must be checked before import;
never reconstruct a parent from a filename or this prose alone.

Preserve every model parameter and AdamW moment/step/weight-decay option. Replace only the next LR
with 0.00001 and use a bounded constant scheduler. Do not reset optimizer moments, reinitialize the
model, run the old cosine past its horizon, or rewrite the parent's identity/history/checkpoint.

Same qualified 113 optimizer / 40 development-validation members, 144³/2mm cache, model, loss,
HU preprocessing, member ordering, center sampler, argmax, sliding windows and 10mm margins.
No simultaneous padding, loss, sampling, threshold, augmentation or cohort intervention. Preserve
all153 members/23 holds. Starting seed42 is ancestry, not a new randomized initialization.

The new run has **300 new updates** and explicitly records logical completed steps300–600. New
update0 samples the member/crop at absolute update index300; update299 uses absolute index599.
Do not restart the sampler at index0. The combined prefix/tail gives 78 members five exposures and
35 six. Preserve the original 300-row history as parent evidence; the new history has 300 rows,
records LR used/next, parent step offset, and absolute sampler positions.

## Required implementation phases

1. **Separate versioned parent contract.** Add a new identity/config/state codec and launcher,
   rather than relabeling a version1 checkpoint as version3. Pin parent artifact/receipt/derivation,
   identity/progress/source/runtime and cache/binding. Explicitly validate model inventory, optimizer
   moments and step counters, constant scheduler, parent offset, and all original controls.
   Restrict this parent and recipe at the real entry point. Retain old version1/2/3 behavior.
2. **Synthetic import and recovery.** Invented parent with a nontrivial AdamW history; import exact
   weights/moments, verify absolute sampler offset, compare the next update, reject wrong parents,
   roles, moments, rate, history offset and forged ancestry. Test interruption after mutation,
   checkpoint exhaustion, guard stops and independent restoration of every keeper. Native
   tolerances must be declared and supported by the measured checkpoint-recovery test, not chosen
   after the real result. A fresh-training replay failure must not be called an import failure.
3. **Real zero-update parent qualification.** Restore the pinned parent from independent backup
   with primary artifact reads blocked. Verify weight bytes and the retained terminal probe.
   On the role-safe cache, reproduce all40 native validation masks before any real update, using
   a new stage-specific reference request. Match the frozen original mask digests/counts and
   coverage record. Preserve failures and refuse launch if this exact import/inference check fails.
   No original CT reads. No other checkpoint may silently replace the parent.
4. **Resource and exact-request freeze.** Prepare an immutable new run ID with the exact parent,
   qualified inputs, source/runtime, cadence, original-reference scope and independent keeper
   ceilings. Measure import/recovery costs natively. Proposed ceiling45min total including recovery,
   RSS/driver16GiB, output4GiB, AC/exclusive MPS/100GiB internal free floor. This is a prospective
   budget to verify, not a measured result or current launch authority.
5. **Single supervised run and inspection.** Run only after the parented design and exact request
   are authorized. Checkpoint/new-run evaluation at0/150/300 (logical300/450/600), independently
   preserve and recover each keeper, review every case's metrics and selected overlays, then decide
   the next intervention. No automatic extension or promotion.

## Evaluation, source reads and stops

Initial new-run evaluation: validation40 only, because all113 training metrics at parent step300
already exist. Intermediate150: validation40. Final300: full113/40. Proposed fresh total233 pancreas
reference reads, zero original CT. Recompute exact compressed/expanded byte totals from the qualified
binding; never recycle the consumed007/008 scopes or the unfrozen009 scope. Imported-model inspection
and training evaluation must identify their stage-specific reads and actual completed prefix.

The parent baseline is an active coverage boundary, not warmup. Before updates require exact40 native
mask reproduction and the original coverage outcome. At150/300 retain mean recall>=0.95,
minimum>=0.65, at least38/40 boxes covering>=0.995, and no mean-recall drop>0.03 from the best prior
active boundary including the imported baseline. Refuse future updates/reads on a stop. These checks
remain coverage safeguards; they do not accept a contour on the reviewer's behalf.

Assess useful shrinkage separately: median validation volume<=13.873x, ROI screens>=10/40,
mean recall>=0.9627, and all40 box screens retained. Report all per-case regressions, tiny/partial
references and native failure metrics. This is one development comparison, not sealed evaluation
or a generalization result. Plan G5 and the lesion cascade still require later work.

Three checkpoints, three evaluation keepers and one terminal keeper are expected for a complete
run. Keep derived native masks as reproducible local scratch and explicitly inventory that omission.
Importing a parent is a **new child experiment**, not permission to continue a consumed request.

## Decision needed

Recommend this parented tail instead of spending a real300-update replay on a prefix criterion that
native qualification has not established. If Quinton prefers fresh training, retain the fresh plan
on hold and investigate/calibrate fresh MPS reproducibility first. Do not silently loosen its
1e-6 bound or exact40-mask requirement. Neither alternative is launched by this proposal.
