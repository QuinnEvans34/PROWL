# Teacher overnight operation — October 26

The user explicitly authorizes hourly checks, operational repairs and continuation of this teacher
through the night. This supersedes the historical no-schedules instruction for this run only.
Heartbeat `keep-prowl-teacher-running` is ACTIVE, hourly in this chat. Stay quiet on healthy
progress; report recovery, completion, safety failures and needed user action. Respect any later
operator pause. This is teacher target generation, not student scientific training.

## October 28 power and drive unavailable — latest check

17:45 UTC: macOS still reports battery power (78%, discharging), and PROWL-Data
is no longer mounted. `diskutil list external physical` lists no external disk.
No teacher supervisor/worker is active; launchd09 remains exited. No restart or
mount/repair attempted. The prior708-target hash verification remains historical;
outputs cannot be rechecked until the drive is connected. Reconnect both AC and
PROWL-Data before verifying inputs and preparing a qualified continuation.
Hourly monitoring remains enabled; preserve the171727-second remaining allowance.

## October 28 AC interruption — prior check

At the 16:48 UTC hourly check, attempt09 had stopped at708/1333 after the
Mac switched to battery. worker.log ends with `RuntimeError: AC power required`.
resources.json records2240.634101s,2162606080B peak owned RSS,exit1 and
workers_reaped=true. Supervisor19823/worker21772 are absent; launchd09 has no
live PID and the exclusive GPU lock is released. All340 repository producing
pins and request7184607c... still match. No restart on battery, no student run.
Charge2241seconds, leaving171727seconds of the previous173968-second allowance
for a later qualified continuation. Preserve attempt09 and all previous attempts.
Hourly monitoring remains enabled; AC restoration is required before continuation.
Verification receipt: outputs/prowl/teacher-ac-stop-20261028/verified.json.

## October 28 qualified affine continuation — historical launch

User approved qualifying the geometry-aware path, retaining all cases, then resume.
New one-shot launchd label com.prowl.rsuper-targets-20261028-09 runs additive
resume_rsuper_affine_checked_v1.py from attempt08 into rsuper-full-targets-09.
Startup must verify all prior pins and699 completed outputs before dispatch.
Inspect request/process/tiles before claiming fresh inference. Never redispatch09.

Qualified source loader preserves the entire source affine for the two explicit
exceptions03067/04348, resampling onto an enclosing orthogonal grid using the polar
basis, source column-norm spacing, linear interpolation and outsideHU-1024.
This is an explicitly approved two-case preprocessing extension, recorded in the
request and each new output's source_loading. Ordinary cases retain SimpleITK
loading and frozen v2 preprocessing/prediction/reconstruction; old producing files
are unchanged. No cohort exclusion, tolerance relaxation or source file alteration.

Evidence: teacher-affine-qualification-20261028-01 under the artifact root.
Both exceptional real scans pass preprocessing/grid/native-coverage/finite/tile
checks. Two ordinary real scans02331/07555 produce exactly equal arrays, grids
and normalization metadata versus the old path. CPU qualification13.895seconds,
2,683,944,960bytes peak RSS, no inference. Synthetic world-coordinate ramp tests
cover shear and reflection;36focused tests pass9.05s, final2worker tests5.11s.
Reviewed central source planes show no gross displacement/reflection/truncation;
interior roundtrip mean absolute HU differences0.387/0.367. This limited visual
check is NOT segmentation accuracy evidence or a complete clinical image review.

Original remaining teacher budget173968seconds retained;30GiB perattempt output,
32GiB combined cache,12GiB RSS/MPS,AC/storage/exclusive-GPU gates retained.
Prior attempts and699 outputs preserved. Full1333 geometry accounting is1331
unchanged-header passes plus2qualified exceptions. Hourly keeper remains ACTIVE.
No student training. Code commit00eba2a.

Admission verified: supervisor19823/worker21772, launchd09. Request SHA256
7184607c129217650f1043c4893d489d9a5ba8296a2696a05c5af9a3071dd956;
all340 repository pins match,699 verified reusable members,173968seconds budget.
Fresh inference verified: all699 saved members reused in234.411worker seconds,
then the original failing casePanTS_00002331 reached25/60tiles. Supervisor19823
and worker21772 remain live under launchd09; no resources/guardian failure.
This confirms resumed prediction rather than merely startup/reuse. Hourly keeper
is ACTIVE. Do not duplicate this run or edit its340repository producing pins.

## October 28 diagnosed geometry blockers — historical

User requested diagnosis, fix and restart. AC/drive restored. No restart performed:
full training-header audit02 checked1333,1331passed,2failed. The original case
PanTS_00002331 uses NIfTI spacing1.5 but affine norm1.49999998, causing332 vs331
rounded slices. Additive header validator checks frozen source shape/world corners
(atol1e-4mm) and native-region coverage, then predicts the unchanged ITK geometry.
Actual failed-case CPU preprocessing matches332x237x285/max affine difference
3.55e-15. Synthetic/continuation/watchdog tests:27pass9.27s. Commitab2303a preserves
all old producing files. Worker comparison test confirms only validation changes.

Audit also found rounding differences forPanTS_00001772 andPanTS_00007638.
Two independent blockers remain: PanTS_00003067 has direction orthogonality error
7.004908e-5 (existing preprocessing limit1e-5); PanTS_00004348 is rejected by ITK
at header read with no orthonormal definition found. Do not exclude cases, loosen
thresholds, or start the prepared continuation against a failed audit. User decision
requested for a separately qualified geometry-aware loading path. Frozen recipe,
original173968second remaining budget and all699 targets remain unchanged.

Evidence under artifact root: teacher-header-audit-20261028-02/result.json and
cases.jsonl; teacher-header-real-check-20261028-01.json. Audit01 partial evidence
preserved: header-reader error escaped its loop before summary. Additive auditv2
reused the completed prefix and captured remaining reader errors; no inference.
Prepared resume_rsuper_header_checked_v1 requires a complete passing audit and
real-case proof; NOT dispatched. Hourly keeper remains active but must not restart
while these geometry blockers remain. No new teacher or student process launched.

## October 28 geometry stop — historical

Attempt08 stopped after699/1333 at the preprocessing geometry assertion in
`build_rsuper_full_targets_v2.py:42`, before prediction for the next ordered case,
`PanTS_00002331`. Actual preprocessed shape/affine did not satisfy the comparison
with `metadata_grid(parent_geometry)`; the traceback does not identify which part
mismatched. Root cause remains unqualified. Do not bypass the assertion, exclude
the case, change geometry or blindly continue this attempt.

Resources report exit1, workers_reaped=true,29372.424736 supervised seconds and
3749167104bytes peak owned RSS. Supervisor76252/worker77956/guardian are absent;
launchd08b is stopped. All330 repository producing pins match. Original cumulative
budget remaining is173968seconds after charging ceil(elapsed). AC and both drives
are available; this is not an AC/storage stop. Preserve all outputs and failure
logs. Hourly checks remain active but must not retry this unresolved geometry failure.
All699 completed records/payloads passed SHA256, size, uint16 dtype and native-shape
verification using the existing completed_members checker. The initial checker
invocation lacked the existing jsonschema dependency path and read no payloads;
the corrected environment completed successfully without installing anything.
Next: bounded comparison of the failing scan header, frozen metadata and geometry
calculation before proposing any separately qualified correction. No student launch.

## October 27 post-demo resume — historical

User explicitly authorized resume and hourly overnight checks. New one-shot launchd
job `com.prowl.rsuper-targets-20261027-08b` invokes the additive
`scripts/diagnostics/resume_rsuper_targets_v3.py`, previous attempt07 and verified
`rsuper-demo-pause-20261027-01/receipt.json`, output `rsuper-full-targets-08`.
Startup verifies all previous pins and579 completed targets before worker dispatch;
inspect process/progress evidence before claiming fresh inference. Same frozen
teacher/cohort/geometry; original cumulative budget203341seconds remains.

Hourly keep-prowl-teacher-running is ACTIVE again. The one-time professor-demo
pause automation stays PAUSED. No Ollama models were loaded at resume, AC attached.
Do not duplicate this job or alter producing pins. Prior pause instructions below
are historical; this new explicit resume supersedes them for teacher generation.

The first08 dispatch stopped before publishing a request or running inference:
retained NPZs1.047903GiB plus original31GiB output reservation exceed the32GiB
combined ceiling. Logs preserved in the original08 launchd registration/dispatch.
The additive v3 continuation tightens only per-attempt output to at most30GiB;
combined32GiB, RSS, AC, storage, frozen worker and scientific pins are unchanged.
Smaller existing output limits remain smaller. Eleven CPU continuation tests pass
in5.63s; original files remain intact. Replacement08b repeats all admission checks;
never blindly retry a failed stage or change the same producing script in place.

## October 27 professor-demo pause — historical

User scheduled a pause around14:00MDT. Attempt07 was stopped through the existing
identity-checked pause command; normal SIGTERM cleanup succeeded, no forced kill.
Supervisor1351 and worker2683 are absent; resources confirm workers_reaped=true,
exit-15 and11323.165962 supervised seconds. All579 completed targets verified;
remaining cumulative active budget203341seconds. The unfinished case is preserved
but must be recomputed on a later explicit continuation. Receipt:
`rsuper-demo-pause-20261027-01/receipt.json` under the existing artifact base.

Both keep-prowl-teacher-running and pause-prowl-teacher-for-professor-demo are
PAUSED, confirmed by app. Local expert GPU check reports gpu_busy=false. Do not
resume or launch qualification/training during the demo; await explicit user
resume authorization. No model calls were made by this pause. The ACTIVE wording
in the historical entries below no longer describes current state.

## October 27 authorized AC-loss continuation — historical

Attempt06 stopped at529/1333 after `RuntimeError: AC power required`; resources
confirm exit1/reaping and6549.370012 supervised seconds. User explicitly authorized
verification/resume once power returned. Preserve attempt06. Stop review:
`rsuper-power-stop-review-20261027-01/review.json` binds its request/resources/log.

Current generation: `rsuper-full-targets-07`; one-shot launchd label
`com.prowl.rsuper-targets-20261027-07b`; additive entry
`scripts/diagnostics/resume_rsuper_after_power_loss_v2.py` (commit119a541). Same frozen
prediction worker/cohort/geometry and repaired v2 watchdog/guardian; no student launch.
All529 completed payloads verified before new request publication. The previous
attempt charges6550seconds, leaving214665seconds from the original cumulative budget.
Supervisor1351/worker2683 dispatched; inspect their fresh progress before claiming
new inference. All329 repository producing pins match; preserve these files too.

The first dispatch label `com.prowl.rsuper-targets-20261027-07` stopped on missing
`jsonschema` before request publication or inference. Its logs and dispatch directory
remain intact. Replacement07b restores the existing PYTHONPATH dependency directory
`/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies`;
no dependencies were installed. Only07b is live. Launchd KeepAlive remains false.
Hourly `keep-prowl-teacher-running` is confirmed ACTIVE; no duplicate monitor.

## Historical October 27 resume after operator pause

The user paused attempt05 at503/1333 verified targets, then explicitly authorized resume and
reactivation of hourly checks. Pause receipt: `rsuper-operator-pause-20261027-01/receipt.json`.
Attempt05 is stopped/reaped; preserve it. The current continuation is `rsuper-full-targets-06`,
launchd label `com.prowl.rsuper-targets-20261027-06`, using additive
`scripts/diagnostics/resume_rsuper_targets_v2.py`. This preserves the existing pause verification
and unchanged prediction worker, but retains the repaired v2 guardian/watchdog rather than
reverting to the old process sampler. Six supervision tests pass. Remaining active budget
is221215seconds; no scientific changes. Startup verifies prior pins and all503 targets before
creating the new request. Inspect the new process/progress files before claiming fresh inference.

Verified resume: supervisor13779/worker15917 are active. All503 targets reused in228.626
worker seconds; fresh case PanTS_00001612 advanced to25/150tiles. Hourly heartbeat is ACTIVE.
No resources failure present. Keep exactly this one continuation running.

## Historical October 26 handoff

Artifact base: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023`.
Failed attempt: `rsuper-full-targets-04`, 335/1333 completed. `resources.json` records reaping,
exit-15 and `TimeoutExpired(['/bin/ps', '-axo', 'pid=,ppid=,rss='], 5)` after5826.079s.
Its supervisor20517 and worker21771 were absent at recovery inspection. Preserve this attempt.
New continuation destination: `rsuper-full-targets-05`; launchd label
`com.prowl.rsuper-targets-20261026-05`. Inspect actual dispatch/progress before claiming running.

Additive recovery entry: `scripts/diagnostics/resume_rsuper_after_monitor_timeout.py`.
Uses unchanged frozen v2 prediction worker, teacher, cohort and geometry. Verifies every previous
producing pin and completed payload/type/shape, charges ceil(prior supervised elapsed) against the
remaining original budget and requires AC/storage/cache/exclusive MPS gates. Never overwrite,
repin or duplicate a generation. New targets are written to a new directory.

Teacher-only `mac_teacher_watch_v2.py` samples process-tree RSS every2s rather than using the old50ms polling sleep
after each system-wide query (the failed attempt recorded25,931 samples in5,826s). Isolated5s process-list timeouts retry, with failure on the third consecutive
timeout. Wall deadline is checked before and after sampling; RSS cap is unchanged. At most roughly
15s of missing observations is tolerated, never an unlimited monitoring gap. Resource report records
timeout count. Parent-loss guardian and owned-group cleanup remain active through the additive
`mac_teacher_supervision_v2.py`. Original producing modules remain unchanged.

## Hourly procedure

Inspect launchd status, exact process identity, latest progress/tiles timestamps and resources/result
files. Progress may be within a long case: do not kill solely because the case count is unchanged.
Never run a second teacher alongside a live one. After a stopped job, confirm cleanup and diagnose
its precise error. User authorizes fixes for understood operational errors and new, verified same-recipe
continuations; do not blindly rerun the old command or erase an attempt. Stop and notify on corrupt
outputs, unknown scientific/geometry issues, exhausted original budget, missing drive/AC/storage,
or repeated unexplained failures. Do not bypass guards or start student training. Avoid repeated
recovery attempts without new evidence of the cause. On all1333 outputs complete, verify result and
cleanup, report completion and pause the heartbeat.

Keep Mac on AC with lid open/awake and external drive attached. Launchd ownership survives this
chat ending; scheduled app checks cannot guarantee execution while the Mac is asleep or offline.

Recovery qualification: six synthetic CPU tests passed. Attempt05 verified335 completed members
and froze263412 remaining supervised seconds; supervisor57785/worker58484 started successfully.
Fresh inference progress must still be verified before calling the operational recovery complete.

Fresh inference confirmed: all335 verified targets were reused in119.072 worker seconds, then
PanTS_00006340 advanced to tile25/60. Supervisor57785 and worker58484 were both alive; no
resources failure was present. This is actual new prediction work, not merely launch acceptance.
Heartbeat remains active. The original failed case's incomplete output remains in attempt04.

## Attempt07 fresh inference verification

October27: all529 previous targets rechecked/reused in182.803 worker seconds;
new case PanTS_00002930 reached25/84tiles. Supervisor1351/worker2683 active, no
resources/guardian failure present. New request SHA256
`b2577febe031d21d15fb56f7f46fff406004e270706bdf07e38ece7f3723218b`.
All4615 prior pin values retained; same teacher/train/preprocessing/geometry and
non-time resource limits. Local verification evidence:
`outputs/prowl/teacher-ac-resume-20261027/{continuation,fresh-progress}.json`.
Twenty continuation/watchdog tests passed. Hourly heartbeat remains ACTIVE.


## Attempt08 verified worker handoff

Replacement08b passed startup checks; supervisor76252/worker77956 are launchd-owned.
Request SHA25618bcbff04db5ad1689fa479975e1a2d938a4d36e677b4cd6843329acbb4f1b5a;
all330 repository producing pins match. All579 saved targets were reverified/reused
in212.097 worker seconds. Budget203341seconds, output30GiB/RSS12GiB/MPS12GiB;
combined cache32GiB unchanged. Reuse count is not new inference. Inspect tile journal
for fresh prediction progress. Both older attempts and failed08 dispatch retained.

Fresh inference confirmed: PanTS_00007555 reached25/175tiles after reuse.
Hourly keeper is ACTIVE; demo-pause automation remains PAUSED. No student training.
