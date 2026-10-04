# CAP-EXP-008 — fresh broader-cohort duration/schedule diagnostic

Quinton authorized preparing and running the proposed 1,200-update experiment: “Run the experiment
now,” following the October 1 strategy discussion. D-307 records that authority. Codex selects the
bounded cadence, coverage safeguards and resource limits below within that instruction, freezes
the exact request after native verification, and binds the authorization record to its SHA-256.
This does not authorize further extension, a warm start, a different cohort or model promotion.

## Question and comparison boundary

Can longer optimization remove excess foreground while retaining reference coverage on the same
qualified 113 training / 40 development-validation cohort? CAP-EXP-007 used only two or three
sampled patches per training case. CAP-EXP-006 demonstrated that better Dice can accompany severe
coverage loss. Use the new trajectory to measure that tradeoff rather than assuming convergence.

This is a **duration/schedule diagnostic**. Cosine decay to zero at 1,200 changes LR history relative
to CAP-EXP-007's horizon of 300; it is not a duration-only matched control or the formal G5 comparison.
The validation cohort has been repeatedly used in development and is not a sealed test.

## Fixed inputs and recipe

Use the exact D-294 113/40 cohorts and D-300 2 mm persisted cache, without new CT reads. Cache SHA
`b61897ed3176fecd9d8ca143285d9700699c1557537ba15b966a487134342bf7`; binding SHA
`ceb18e13622a73596bfa68305859ff71db8ddf9d01054300ef516ed751da759d`.
Preserve all 153 qualified members, 176 original candidates, 23 holds and partial/noisy references.

Fresh seed 42 SegResNet, 16 filters, group norm 8, down(1,2,2,4), up(1,1,1), dropout 0;
144³ patches at 2 mm; HU[-100,300]; float32 native MPS, fallback disabled; CPU threads 2, workers 0.
Balanced CE + foreground Dice, AdamW LR .0003, weight decay .00001, cosine to zero at 1,200.
The model, loss, sampler, cohort, geometry, export and prediction policy remain fixed.
SHA-256 member order per pass and equal foreground/background center sampling remain unchanged.
1,200 updates means ten full 113-member passes plus 70 more: 43 cases get ten sampled patches,
70 get eleven. Report actual exposures, never call this 1,200 epochs.

Separate adapter/training/plan/request versions 2 allow this bounded horizon. Version 1 retains
its 300-update cap; the readiness interface stays at adapter version 1 and cannot train real inputs.
No prior checkpoint initializes the real run; the fresh seed weight digest is checked.

## Cadence and coverage stop

Checkpoints at 0/300/600/900/1,200. Full 113/40 evaluation at 0 and 1,200; validation 40 at all
intermediate boundaries. Each checkpoint and its evaluation record are independently kept before
the run decides whether to advance. Native prediction masks remain local reproducible scratch.

Starting at 300, stop at the completed checkpoint if any condition holds:

- Mean native validation reference recall < .95.
- Minimum per-case validation reference recall < .65.
- Fewer than 38/40 cases have native box-reference coverage >= .995.
- Mean validation recall falls > .03 below the best earlier active checkpoint in this run.

Step 0 is recorded as warmup and cannot satisfy or trip a learned-coverage claim. Every validation
case enters the guard; missing, duplicate or reordered membership is refused. Existing 10 mm
rounded-axis margins, >= .995 coverage / <= .25 acquired-scan crop screen, argmax prediction and
144³/overlap .25/constant inference stay fixed. No threshold or component search is performed.

A coverage stop is a verified **stopped_coverage_guard** transaction with its actual update count,
completed evaluation/read prefix, terminal keeper and independent recovery. It is never reported as
1,200 updates complete. Future reference stages and updates are not executed. Exceptions or resource
interruptions remain failed/incomplete attempts with their last complete checkpoint preserved.
There is no automatic resume or extension.

These are stop thresholds, not contour acceptance or an adoption policy. Assess shrinkage using
volume ratio, crop fraction and ROI-pass counts alongside all per-case coverage failures. A useful
development signal would be >=25% lower median volume ratio than CAP-EXP-007, >=10/40 ROI passes,
mean recall no more than .02 below .9827 and all 40 box-coverage screens retained. Failing that signal
does not delete a model or case; report which mechanism improved or failed. No promotion follows.
The reference is visible annotated pancreas; lesion containment and the final Stage 2 input remain
separate work, not claims from this run.

## Read and resource envelope

Each native-reference stage opens once and uses the existing qualified label-only reader. Full
completion requires 426 label reads: 153+40+40+40+153, exactly 58,621,113 compressed bytes and
11,763,565,147 expanded bytes; no original CT reads. A coverage stop uses only the completed prefix.
Per-stage 32 MiB compressed / 5 GiB expanded, per-file 128 MiB expanded, 96M source-voxel and
16M processed/padded-voxel bounds remain. No consumed CAP-EXP-007 or D-304 read request is reused.

90 minutes total including independent recovery; 16 GiB RSS and sampled MPS driver; 4 GiB local
evidence; AC required; 100 GiB internal free floor. Existing keeper bounds remain 96 MiB per artifact,
1 GiB new bytes per physical domain and 20 GiB total independent-backup ceiling. Freeze producer and
restore storage ceilings once; no reset between stages. MPS ownership is exclusive.

Measured 144³ updates were about 2.684 seconds: 1,200 would take about 54 minutes for updates alone.
CAP-EXP-007 completed all work in 33.082 minutes with 5.638 GiB RSS / 4.799 GiB driver. The new
90-minute cap allows evaluation, history validation, publication and recovery headroom; it is a
ceiling, not a guarantee. The native rehearsal checks actual MPS memory/state/recovery on invented
variable-volume inputs; CPU tests cross 300 and exhaust 1,200 with a toy network, not accuracy claims.

Five checkpoints, five evaluation record packages and one terminal keeper are planned at full
completion. Restore every published keeper with primary-drive reads blocked, recheck all coverage
decisions from the restored per-case records, and reproduce the actual terminal probe. Record the
reduced inventory honestly if the guard stops early. Final source/environment bytes must match the
frozen request. Source or control drift refuses launch.

## Review and preservation

After completion/coverage stop, independently verify sealed package members, per-case native exports,
source-read totals, exposure history, scheduler/LR, coverage decisions and restored artifact links.
Inspect worst recall, typical/best cases, tiny references and previously problematic 7604. Do not
claim a full visual review from selected sheets. Preserve prior runs, attempts and this outcome.
No change to Claude's lane, dependency installation, source rewriting, Git publication or paid compute
is part of this experiment.


## Attempt 01 and bounded replacement

The first consumed request stopped at step0 after one cached prediction export, before the first
original-label byte read or optimizer update: retained device16777239 vs live16777243. Metadata-only
inspection of all153 labels confirmed that only the ephemeral device changed; APFS UUID,
inodes, sizes, mtimes and ctimes match. Preserve that request/failed attempt and its step0 keeper.

The replacement remains the same1,200-update experiment. Its versioned reference policy verifies
the registered UUID, freezes a153-file mount-observation receipt, and substitutes only the current
mount device in a temporary read observation. The original manifest/cache/descriptor bytes remain
unchanged. Every other stat field, no-follow/cross-device checks, pre/post-read checks and pinned
compressed-content hashes remain enforced. A mount change during the attempt is refused. The
version1/default reader remains strict against the original device. No source file is rewritten,
requalified or exempted. Reverify affected tests/native recovery, then freeze a new single-use
request and authorization under Quinton's instruction to run this experiment. No consumed request
is replayed. Independent recovery never reads the primary drive.
