# R01 — controlled real-data duration comparison

**Ready for the separate scientific launch decision. Not launched.** Quinton approved I03 and
conditional PREP-01; both finished. That preparation approval does not authorize this real run.
The [preparation handback](SEGMENTER-DURATION-REAL-PREP-RESULTS-2026-10-07.md) records passed checks,
the retained private identifier failure and the corrected frozen request. No new architecture,
SuPreM source work, full invented producer or recovery-tolerance amendment is needed for this pilot.

## Question and fixed experiment

Does a fresh192-update version of the existing recipe improve native overlap relative to retained
D-335 terminal48, while preserving lesion coverage and controlling false foreground?

| Item | Exact proposed scope |
|---|---|
| Experiment / attempt | `DURATION-CAP-EXP-015-192` / `DUR_REAL_20261007_R01` |
| Request SHA256 | **`60f3cc516f4d5a6be3337080df5ab5643592f23bb91b2e550f6ac6402ad067a8`** |
| Fresh model | Scratch SegResNet,seed42; three classes;background,pancreas,lesion; no weight imports |
| Fixed recipe | v5 present-class mean CE+foreground Dice; AdamW LR0.0003/decay1e-5; constant schedule; batch1; fp32/MPS;144³ provided-pancreas ROI; zero jitter |
| Training membership | PanTS3,26,2232,2973,5821,6238; original protected roles and difficult cases retained |
| Report-only member | PanTS2514 at terminal192 only; selects neither model nor policy |
| Evaluation | Checkpoints0/48/96/144/192; all six training cases screened natively at48/96/144/192;2514 added at192 |
| Comparison | Terminal192 versus retained D-335 terminal48; no interim-best selection or extension/replay of D-335 |
| Producer limit |192 optimizer updates/253 forwards maximum; a quality stop may finish earlier |
| Cold limit |30 forwards/zero real optimizer updates; primary reads blocked; independent kept predictions/masks/views/checkpoints checked |
| Original source |50 logical original target reads,14 unique pancreas/lesion files; zero original CT reads |
| Target bytes |4,785,819 B for hashing and4,785,819 B decoding;1,033,590,576 B expanded, across12+12+12+14 stage reads |
| Cached inputs | Accepted cache104,509,440 B payload; exact accepted source ancestry and member pins, separate from original target reads |

I03 verified saved predictions on the invented rehearsal: five zero-difference probability
comparisons and25exact masks/validated views. **Optimizer continuation remains unqualified.**
This run is fresh and uninterrupted; an interruption retains incomplete evidence and permits
evaluation of its checkpoints, with no automatic resume or restart. Small finite replay differences
are not declared harmless. This provided-ROI seven-member pilot cannot establish broad model
strength, negative specificity or an autonomous localize-then-segment result.

## Unchanged quality stops

Enforce DUR-01 at every scheduled native screen. Preserve macro recall within0.03 of D-335;
each case/class/component recall within0.10; maintain positive component hits and tiny-case recall
at least0.95. Interim per-case lesion false-positive volume cannot exceed1.25×baseline. Missing,
invalid or ineligible evidence stops execution; preserve the failed screen and do not drop a case.

Terminal192 must additionally preserve pancreas macro Dice, improve lesion macro Dice by at
least20%, lower mean lesion false-positive volume to at most0.80×baseline, and keep each case's
volume at most1.10×baseline. Zero baseline false positives permit zero only. The unchanged policy
and native count baseline are included in the pinned request. A completed but insufficient
terminal result remains a valid recorded experiment, without model promotion or a fabricated pass.

## Resource allocation and start conditions

Hard cap60minutes total: up to45producer,10cold and5preflight;12 GiB sampled owned RSS/MPS driver;
AC power; one accelerator owner/shared lock throughout;100 GiB filesystem free floor.

Keep the approved26 GiB whole-backup ceiling27,917,287,424 B and original baseline17,341,924,636 B.
At most8 GiB new bytes cover the already spent native rehearsal and this one pending real attempt.
Full internal phase reservation4 GiB includes two children up to2 GiB each and64 MiB controls;
current backup+reservation23,919,176,413 B fits; reserved internal free110,861,144,064 B exceeds
the100 GiB floor. Fresh launch admission must recheck this fit, volumeUUIDs/devices/APFS/registry,
AC/MPS/runtime, idle owner, namespace absence, current402source pins and the exact certificate.
Changed prerequisites refuse the launch; no pruning, deletion, new cap or silent old-control rebind.

Fresh areas, only after final approval, are:
`segmenter-duration-20261007-r01-real`, `...-real-keepers`, `...-real-restores` and `...-real-controls`.
Primary uses the registered external artifact root; keeper/restore/controls use the registered
independent internal backup root. No areas or payload writer have been enabled by preparation.

## Concrete command and final decision

The inactive orchestration helper is
`outputs/prowl/SEGMENTER-DURATION-REAL-PREP-P02-20261007/launch-r01-INACTIVE.py`,
SHA256 `0e6a17e848eaa43f62d91b6863cbd4680579b7c80ec98f9d457716fdf4c45cda`.
It requires a separately supplied actual job approval with the exact request/identity/scope, then
performs fresh admission, creates exclusive areas, copies the canonical request and pauses for
independent frozen-control review. It dispatches the existing qualified fixed CLI once per stage:

```text
.venv-prowl/bin/python scripts/diagnostics/segmenter_duration_launch.py dispatch
  --request <absolute registered R01 controls>/request.json
  --request-pin 60f3cc516f4d5a6be3337080df5ab5643592f23bb91b2e550f6ac6402ad067a8
  --dest <absolute registered R01 controls>
  --approval <absolute registered R01 controls>/approval.json
  --approval-pin <SHA256 of Quinton's actual request-bound launch answer>
  --storage <absolute registered R01 controls>/storage-authority.json
  --storage-pin <SHA256 of actual capability-bound storage authority>
  --stage producer
```

The conditional second invocation changes only `--stage cold`; the qualified dispatcher binds
the completed matching producer receipt. Approval/storage pins cannot be finalized before the
human answer exists. Both active control hashes and the exact absolute command must be reviewed
before entering the helper's `DISPATCH_R01` gate. A producer failure stops with retained evidence;
a normal early quality stop permits only its bounded saved-checkpoint recovery. No automatic
retry, sweep, second experiment, unbounded overnight loop or public publication follows.

**Requested decision:** approve one scientific `DUR_REAL_20261007_R01` under this exact request,
source/cache/target scope, quality stops and resource allocation, including fresh admission,
exclusive storage preparation, one producer and its conditional cold prediction recovery.
Quinton can reply **“Approve R01 real-data training.”** This is the final launch decision required
by the approved tonight plan; the already approved26 GiB budget is not being requested again.

After approval, allow about5–10minutes for fresh admission/control review before the first update.
Budget about25–45minutes for producer work; the total remains bounded to60minutes and can stop
earlier on quality/resource failure. Report actual start, meaningful checkpoints, stop/completion,
results and exact next point. Include readiness status in each human-facing response.
