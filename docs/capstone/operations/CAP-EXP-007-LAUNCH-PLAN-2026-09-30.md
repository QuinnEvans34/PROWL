# CAP-EXP-007 — first broader 2 mm training diagnostic

Prepared design; no launch authorization. The exact request is frozen after the final D-305 native
rehearsal and tests. The launcher requires a separate Quinton approval bound to its request SHA-256.
No automatic extension, checkpoint warm start, threshold tuning or model promotion.

## Question and fixed inputs

Does scratch optimization remain healthy on the broader qualified cohort, and does native-reference
coverage improve while crops become useful? CAP-EXP-006 improved Dice but lost coverage; assess
recall, box-reference coverage and acquired-scan crop fraction together with Dice and volume ratio.
This changes cohort, spacing and context from CAP-EXP-006 and is not a single-factor comparison.

Use all113 training and40 development-validation cases in frozen D-294 cohorts. Preserve23 holds and
all partial-reference/noise observations. Validation has already been exposed during development;
these results are not sealed-test estimates or whole-organ/lesion/clinical claims. No new CT reads.
Existing D-300 cache pin `b61897ed3176fecd9d8ca143285d9700699c1557537ba15b966a487134342bf7`;
binding `ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d`.

## Fixed model, sampling and cadence

Fresh seed42 SegResNet,16 initial filters, group norm8, down(1,2,2,4),up(1,1,1),dropout0;
144³ patches,uniform2mm,HUs[-100,300],image-only geometry, float32 MPS without fallback.
Balanced CE+foreground Dice,AdamW LR0.0003,weight decay0.00001,cosine schedule to zero at300.
Two CPU threads,zero loader workers. SHA-256 sorted per-pass membership, separate deterministic
50/50 foreground/background processed-grid sampler.300updates means two full113-member passes
plus74 additional exposures; report actual membership counts, not300epochs.

Checkpoints0,113,226,300. Full113/40 evaluation at0and300;40 validation at113and226.
Sliding144³,overlap0.25,constant blending,softmax,discrete argmax restored to source geometry.
No threshold search. Native96M metrics retain empty/dense/fragmented predictions;10mm rounded
voxel-axis box margin. ROI screen requires≥0.995 visible-reference coverage and≤0.25 acquired-scan
fraction. This screen is a diagnostic, never automatic acceptance or qualification.

Fresh native references each stage:153+40+40+153=386 label reads,
53,708,928compressed and10,774,955,452expanded bytes. One label in memory at a time;
per-stage≤32MiB compressed/5GiB expanded; per-file128MiB and96M-voxel caps. Exact qualified
reference hashes, roles, geometry and approved binary mapping verified. Previous D-304 requests
remain consumed. Each new stage can open once; an incomplete stage cannot be skipped/reopened.

## Resource and interruption envelope

45minutes total across worker and independent recovery,16GiB process RSS and MPS driver,
4GiB local evidence,AC required,100GiB internal free floor. Existing storage capability remains:
96MiB per keeper artifact,1GiB new per physical domain,20GiB total backup ceiling. Freeze the two
storage ceilings once for producer and restore; do not reset them between stages.

Planning estimate:300×2.684s≈805s updates, two full evaluation passes at roughly515s each,
plus two40-case evaluations and checkpoint/backup/recovery overhead.45minutes gives measured
headroom, not a runtime guarantee. New native rehearsal uses15.008M processed voxels and the
actual sampler/network; real cohort inference and target-only costs are already measured in D-303/304.
The supervisor stops at a cap rather than extending time or dropping cases.

Claim the exact request once before work. Append/fsync update-started/completed and publication
boundaries. Save optimizer/scheduler/RNG,full crop/member/loss history and immutable controls.
Checkpoint and independent backup must both finish before reporting that boundary complete.
An interrupted/uncertain session refuses further updates and checkpoint publication. Preserve its
attempt; no automatic resume. A later continuation needs a separately reviewed request.

## Evidence retention and launch review

Independently back up four checkpoints, four evaluation record packages and the terminal record.
These nine keepers preserve controls, metrics, reference receipts, crop histories, prediction hashes
and the terminal journal. Restore all nine with primary reads blocked and verify terminal weights
and a fixed prediction probe. The native prediction masks themselves are derived local scratch,
explicitly listed as **not backed up**; they can be regenerated from the kept checkpoints and
verified inputs. Do not claim independent mask-byte recovery or delete their current copies.

After completion, verify all386 evaluation rows/exports and read accounting, inspect learning and
coverage trajectories and per-case failure examples, and preserve null/failed results. Decide on a
longer run only from that evidence. No literature/UI completion is required for this imaging diagnostic.
