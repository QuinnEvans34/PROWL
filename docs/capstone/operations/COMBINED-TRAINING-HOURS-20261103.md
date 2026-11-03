# Combined training-session accounting — November 3, 2026

Snapshot: 2026-11-03 21:55:52 UTC (2:55 p.m. America/Denver).
The retained records support **547.306 training-session hours**, including
**177.045 hours estimated from historical MLflow timestamps**. Teacher-target
generation adds **90.963 hours**, separately: **638.268 hours of recorded model
work** when both categories are combined. These are compute-session durations,
not human working hours or measurements of how long the GPU was busy.

| Machine / work | Hours | Evidence |
| --- | ---: | --- |
| Mac, early MLflow history | 177.045 | 51 timestamp-based estimates, July 3–27 |
| Mac, earlier full-cohort attempts | 19.555 | Three distinct execution journals |
| Mac, KD comparison control | 60.100 | Two execution journals |
| Mac, KD treatment attempts | 22.686 | Five execution journals, including the current attempt |
| **Mac training subtotal** | **279.386** | Early MLflow history is included here |
| **Lenovo training subtotal** | **267.919** | Nine scientific runs, verified exported journal counters |
| **Combined training sessions** | **547.306** | 370.260 counter-based hours plus 177.045 estimated hours |
| Mac teacher-target generation | 90.963 | Twelve supervised elapsed-resource records |

The early Mac history and earlier full-cohort attempts total 196.600 hours,
consistent with the remembered roughly 200 hours. The KD comparison has added
82.786 hours across control and treatment; generating its teacher targets was
another 90.963 hours. The Lenovo's earlier 208.780-hour dashboard subtotal is
already part of its current 267.919 hours and must not be added again.

## Sources and counting rules

- Historical Mac source: `outputs/mlflow.db`, opened in a read-only transaction.
  For training runs, use run start to the last recorded `train/loss` timestamp,
  bounded by run end when present. For Optuna trials, use recorded start/end.
  Four records without training-duration evidence are excluded. Two stale
  `RUNNING` labels are historical records; neither is extrapolated to today.
  Mac attribution comes from the retained local artifact paths, rather than
  independent hardware telemetry. These spans are explicitly estimates.
- Older Mac full-cohort journals: `full_segmenter_suprem_mac_01`, `resume01`,
  and `resume02` under the external artifact root. Count the last recorded
  monotonic elapsed counter for each distinct attempt, excluding unrecorded tails.
- KD: traverse the frozen `ready.json` lineage of
  `mac-kd-treatment-resume-20261103-01`, then include its current treatment
  journal once. The ready SHA is
  `67d10dcfc7f3d1ce14d0a1b736a73da1d4c5fbbf495714455831fe58f4bdd11b`.
  Use journal counters rather than the slightly larger startup/cleanup resource
  totals. Paused gaps between attempts are excluded. Actual updates repeated
  after checkpoint recovery still consumed time and count as separate work.
- Teacher: measured resource durations from `rsuper-full-targets-02` through
  `rsuper-full-targets-13`. Attempt 01 lacks measured resource duration; its
  600-second safety-budget charge is not presented as measured compute time.
  Teacher pilots and qualification are outside this counter.
- Lenovo: verified export supplied by the other chat at branch commit `3a64d03`,
  source `WINDOWS-TRAINING-HOURS-20261103.json`, as of
  2026-11-03 21:44:33 UTC. Export SHA256:
  `c28c3b75cb3582ebd592b657169db5095cc045d37ac610a19a0efd38a30efae6`.
  Its nine journal records total 964,509.828 seconds. Dashboard and MLflow aliases
  describe the same executions and add no additional duration.

Training-session counters include in-run validation, checkpointing and I/O.
Standalone evaluation, CT restoration, data preparation, engineering tests,
unknown durations and human hours are excluded. This is a reconciled inventory
of retained evidence, not a guarantee that every project experiment survives.
Times on the two machines can overlap: this measures combined compute effort,
not elapsed calendar time. No hardware-utilization trace is available to convert
the totals into GPU-active hours.

## Training page and refresh

The application now has a **Training** navigation item at `/training`. It shows
the combined total, each machine, the KD control/treatment breakdown, teacher
generation separately, source freshness, limits and individual execution rows.
The sanitized repository snapshot is
`configs/training-hours/recorded-hours-v1.json`; it contains no patient data or
private source paths.

The local Vite service exposes read-only `/training-hours`. The page checks it
once per minute. A private configuration at
`outputs/prowl/training-hours/source-config.json` selects local sources;
`PROWL_TRAINING_HOURS_CONFIG` can select another operator-owned configuration.
The collector reads metadata/journals only, with no model, CT or checkpoint
loading and no changes to scientific outputs. Update the private current-root
binding after a future authorized KD continuation, and replace the Lenovo export
after verifying a newer one. Lenovo is a timestamped export, not a live remote
connection. Production/static builds retain the packaged snapshot; the live
read endpoint is a local development-service feature.

If sources or the drive are unavailable, the page retains a clearly labeled
snapshot rather than showing zero or inventing elapsed time. Each journal record
includes its complete-prefix SHA256 and byte count for later reproduction while
the live journal continues appending. Conflicting execution identities, aliases
and elapsed-counter resets fail accounting instead of silently summing them.

## Verification

Eight CPU accounting tests cover counter parsing, incomplete journal tails,
invalid/reset counters, duplicate identities/aliases, historical timestamps and
stale MLflow labels. Five UI/service tests cover routing, totals and exclusions,
retained-snapshot fallback and request-path restrictions. Production build passed;
the component-only page was visually reviewed at 1280×900 using software rendering.
The live local endpoint returned fresh journal totals. No model or scan was loaded
for this work; the existing KD worker remained running with tracked updates and
verified independent backups.
