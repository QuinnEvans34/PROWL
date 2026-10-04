# CAP-EXP-009 — matched early schedule and low-rate tail

**Latest status: real launch held after native prefix qualification failed.** Read [the preflight results](CAP-EXP-009-PREFLIGHT-RESULTS-2026-10-01.md). No exact real request has been prepared. The approved scope below is preserved; the tolerance is not relaxed.

Quinton approved running the proposed diagnostic: “Great, lets do the diagnostic.” D-309 records
authorization to implement, verify, prepare and execute it once. No repeated launch permission is
needed after routine preparation. Freeze the exact source/runtime/request before execution.

## Fixed experiment

Fresh seed42,600updates maximum,113train/40development-validation from D-294/D-300,144³/uniform2mm,
same SegResNet16/GN8/dropout0,balanced CE+foreground Dice,AdamW0.0003/weight decay0.00001,
MPSfloat32/fallback0,two CPUthreads/no workers. ExistingHUwindow,member/crop policies,constant
sliding-window blend/overlap0.25,argmax and10mm margins remain fixed. All153members/23holds retained.
No loss,sampling,padding,augmentation,threshold,component or cohort change accompanies the schedule.

The explicit version3 schedule decouples prefix duration from update ceiling. Applied LR at
zero-based updatek<300 is0.0003*(1+cos(pi*k/300))/2,using the original recursive cosine implementation.
For k>=300,it is fixed0.00001. Record `learning_rate_used` and `learning_rate_next` separately.
The final prefix update uses the original8.22460e-9 rate;the next rate deliberately becomes0.00001.
Never step the old cosine past300. Version1/2 contracts and consumed requests remain unchanged.

600updates means78cases five exposures and35 six,not600epochs. This single-seed development
diagnostic tests added exposure under a small-rate tail;it is not formalG5,sealed evaluation,
lesion containment,whole-organ certification or model-promotion evidence.

## Cadence, prefix parity and coverage

Checkpoint/evaluation boundaries0/300/450/600. Full113/40 at0/600,validation40 at300/450. Preserve
each checkpoint and evaluation keeper before deciding to advance.

At300,verify against the pinned CAP-EXP-007 baseline:identical first300 member/pass/crop/applied-rate
traces,maximum absolute parameter difference<=1e-6,and all40 native binary validation masks exactly
equal. Baseline identities/backup receipts/mask digests are frozen into the new plan. Checkpoint
comparison uses the independently backed-up model,not a guessed primary path. A mismatch stops at
300 as `stopped_prefix_mismatch`,with actual counts,prefix review,journal and independent recovery.
It must not be represented as a completed600-update or matched-prefix result. Do not alter tolerance
or masks after observing the run. The scheduler/optimizer next-rate fields intentionally differ.

The same coverage policy is active from300:stop if mean native validation recall<0.95,minimum<0.65,
fewer than38/40 boxes cover>=0.995,or mean recall falls>0.03 from the best earlier active checkpoint.
Step0 is warmup. Every validation member enters the guard. A coverage stop retains the complete
checkpoint and read/evaluation prefix as `stopped_coverage_guard`;no later stage is opened. There
is no implicit resume,extension or rerun of a consumed request.

Assess shrinkage separately:median validation volume<=13.873x,at least10/40 ROI screens,mean recall
>=0.9627 and all40 box-coverage screens retained. These are diagnostic targets,not contour acceptance.
Report train/validation results only at stages actually run,plus per-case failures and selected
inspections. Tiny/partial/difficult cases remain visible in all applicable aggregates.

## Read and resource envelope

Fresh stage-specific pancreas-reference budget386reads:153+40+40+153. Exact compressed/expanded
totals53,708,928 /10,774,955,452bytes;no originalCT reads. All qualified descriptors and compressed
content hashes remain mandatory. Freeze a fresh153-file UUID-verified mount observation;the separate
rebound reader preserves original inventory and all non-device/pre/post-read checks. Prefix failure
at300 consumes only193reads;stopping at450 consumes233. No prior training/reference request is reused.

60minutes total including recovery,16GiB RSS/sampled driver,4GiB local output,AC required,100GiB
internal free floor;exclusive MPS lock. Existing keeper96MiB,1GiB new/domain,20GiB backup ceilings
remain. Native synthetic rehearsal must verify the schedule transition,checkpoint/reload,next
update,interruption refusal and independent recovery before request freeze. Prior00733.082min plus
roughly13.5min for300 extra144³ updates supports the60min ceiling;this is an estimate,not a guarantee.
Stop on any resource violation and retain the last complete checkpoint/failed attempt.

Full completion plans four checkpoints,four evaluation keepers and one terminal keeper. Restore
every published keeper with primary reads blocked,recompute coverage/prefix decisions,and reproduce
the actual terminal probe. Native masks remain reproducible local scratch,not independent backups.
Source/runtime must still match the frozen request after execution. No Git publication,paid compute,
dependency installation,source rewrite,Claude dispatch or source/eligibility promotion is authorized.
