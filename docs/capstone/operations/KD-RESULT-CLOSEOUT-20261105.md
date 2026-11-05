# Mac KD result reporting

The additive `report_mac_kd_results.py` command prepares current evidence while
training continues, then verifies execution closeout when the full run is present.
It never starts, stops, restores or changes a model. Outputs must be fresh and
outside every producing/backup directory. Earlier attempts remain intact.

```sh
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies \
  .venv312/bin/python scripts/diagnostics/report_mac_kd_results.py \
  --root /Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/mac-kd-treatment-resume-20261105-01 \
  --ready-sha256 38b8f8a83a4ca3d6ceab76cdb8d34fe2681d71e16c4e50a9460b9240da359049 \
  --output outputs/prowl/kd-results-NEW-UNUSED-DIRECTORY
```

The actual live invocation is retained at `outputs/prowl/kd-results-20261105-01`:
control has all12validations; treatment has ten through20k, missing22k/24k.
Status is `PENDING_TREATMENT_COMPLETION`; execution closeout is false, endpoints
are absent and no hypothesis/practical verdict or confidence interval is emitted.
The existing same-update error reader supplies full70-case component/voxel error
counts and keeps supplied-region KD separate from the autonomous baseline.

After the full horizon, the same command in a fresh directory requires:

- All12completed native validations in each arm, coherent continuation boundaries,
  unchanged ordered cohort/reference geometry/component identities, and independent
  native-report/component backup hashes.
- Selection from the full series with earliest ties and an explicit24k terminal
  endpoint. Selected steps may differ across arms; these are policy-selected
  endpoints, not a falsely relabeled same-update comparison.
- Matching result/selected/terminal reports and component sidecars, byte-hashed
  selected/final checkpoint backups, exact final journal backup and completion
  receipts. Checkpoint bytes are hashed without tensor loading; this is not a new
  numerical cold-restore qualification.
- Successful/reaped treatment supervision, no cleanup survivors or tracking warning,
  observed absence of owned workers/process groups and supervisor, and available
  exclusive GPU ownership. Observations never signal a process.
- Local MLflow opened with SQLite `mode=ro`, correct arm/comparison/run identity,
  terminal loss and every series native metric matching its owning continuation.
  Treatment must be FINISHED. The known control cleanup-only failure and FAILED
  tracking status are preserved under the existing reviewed closeout; they are
  never rewritten as historically successful supervision.

Successful execution closeout is `CLOSED_DESCRIPTIVE_ONLY`. It includes selected
and terminal case-level Dice, missed components, false-positive voxels and summary
metrics. Patient relationships remain unresolved; no independent-patient bootstrap,
H0/practical acceptance or clinical/generalization claim follows. Aggregate counts
do not locate remote false positives or attached boundary spillover.

Tests exercise a full synthetic70-case24k series, real read-only SQLite, incomplete
series/closeout, endpoint selection, corrupt checkpoints/backups, wrong terminal
tracking, missing series metrics, live ownership, wrong filesystem and completion
identity. Test process/filesystem/lock observations are isolated from the real GPU
owner. An initial synthetic closeout correctly refused the held production lock;
the fixture was corrected to use an isolated observation. No device work occurred.
The actual run remains active; real final closeout is still pending completion.

Follow-up:66KD/native-reader CPU tests pass including operator-pause and failed-
execution reporting, so a stopped run is not mislabeled as active pending work.
Reports cannot be written inside producing/backup directories. The actual saved
control passed checkpoint/report/journal backup, selected/terminal, process-absence
and read-only MLflow checks; its FAILED status remains explicit. This separate
control check does not close the still-running treatment or acquire its GPU lock.

The read-only series-tracking check also matched all12control and ten currently
completed treatment native metrics to their owning local SQLite records. That
observation is retained as series-tracking.json beside the pending live report.
