# Teacher overnight operation — October 26

The user explicitly authorizes hourly checks, operational repairs and continuation of this teacher
through the night. This supersedes the historical no-schedules instruction for this run only.
Heartbeat `keep-prowl-teacher-running` is ACTIVE, hourly in this chat. Stay quiet on healthy
progress; report recovery, completion, safety failures and needed user action. Respect any later
operator pause. This is teacher target generation, not student scientific training.

## October 27 authorized resume

The user paused attempt05 at503/1333 verified targets, then explicitly authorized resume and
reactivation of hourly checks. Pause receipt: `rsuper-operator-pause-20261027-01/receipt.json`.
Attempt05 is stopped/reaped; preserve it. The current continuation is `rsuper-full-targets-06`,
launchd label `com.prowl.rsuper-targets-20261027-06`, using additive
`scripts/diagnostics/resume_rsuper_targets_v2.py`. This preserves the existing pause verification
and unchanged prediction worker, but retains the repaired v2 guardian/watchdog rather than
reverting to the old process sampler. Six supervision tests pass. Remaining active budget
is221215seconds; no scientific changes. Startup verifies prior pins and all503 targets before
creating the new request. Inspect the new process/progress files before claiming fresh inference.

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
