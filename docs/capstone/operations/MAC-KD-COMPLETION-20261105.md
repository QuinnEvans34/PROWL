# Mac KD completed — November 5

Treatment finished24,000updates and all12complete70-case native validations.
Read-only closeout is **CLOSED_DESCRIPTIVE_ONLY**: selected/terminal checkpoints,
reports/components, final journals and independent backups match; all152producing
pins match; all24control/treatment series metrics match their owning MLflow runs.
No model restoration, new inference or optimizer step was needed for this review.

| Endpoint | Control lesion Dice | KD lesion Dice | KD − control |
| --- | ---: | ---: | ---: |
| Selected, both20k |0.3835928680|0.3890839388|+0.0054910708|
| Terminal, both24k |0.3819640366|0.3834389431|+0.0014749064|

These are positive-case macro Dice values over36positive cases within the same
70-case supplied-pancreas-region development cohort. The selected increase is
about0.55percentage points, not evidence of a large or established practical gain.
Selected component hits are39/45control versus37/45KD; selected reference-empty
alarms33/34in both. Terminal hits remain39/45versus37/45, while terminal empty
alarms are32/34versus29/34. Detection means any shared voxel under the existing
definition, not clinical detection. Adjacent JSON includes precision, recall,
voxel errors, pancreas Dice and volume summaries.

Patient relationships remain unresolved. No independent-patient confidence
interval, hypothesis/practical verdict, clinical or autonomous acceptance is
issued. The control's historical cleanup-only supervision failure and FAILED
MLflow status remain preserved under its prior reviewed closeout.

Current resources:30,852.169589supervised seconds,6,584,041,472bytes peak owned RSS,
exit0/success/reaped true, no survivors/cleanup errors. Supervisor92279, worker92391,
guardian92394 and caffeinate92393 are absent; launchd is no longer running and the
exclusive MPS lock is released. Treatment MLflow1e356a71e4f74d5192a091fc40d3f6b8
is FINISHED. Retained treatment attempts total66.841657supervised hours. Budget
accounting charges240,633seconds of345,600, leaving104,967unused; that bound does
not authorize more training. Engineering qualification/new inference are excluded.

Full local report: `outputs/prowl/kd-results-20261105-final-01/report.json`,
SHA2562679c09ebefc2361cb81122ead80530c48fcbeb99b333d2e526d1723a2e0033b.
Adjacent sanitized JSON retains selected/final checkpoint hashes, tracking IDs,
complete validation steps, resources and summary metrics. Hourly KD monitor is
PAUSED after verified completion. Original attempts and scientific pins remain.

The user separately authorized the [larger-model screen](UNIVERSAL-SWIN-OVERNIGHT-20261105.md).
Lenovo code through5ebc49f,18CPU tests and exact four-case readiness were reviewed
without merge. Different C/E filesystem IDs and physical disks are recorded.
The [one-shot permit](UNIVERSAL-SWIN-PERMIT-20261105.json) binds request
4654d46b730abe8c144b1cc57af607d579154b1c96ff707c37861fbce55fadc5 and specification
259d2e77d8ed1c83a75997b67ce8f02278b97a48f5fd509f5417bb090cd44900.
Permit SHA256b6b76fc7e1667a7b5c3c13e93796e6460105d0f3e8f0023b30e12f8a499f8aba.
This permits one bounded qualification/evaluation after fresh Lenovo resource and
exclusive-GPU checks; it is not a claim of GPU qualification/inference success.
No new Mac GPU job or additional successor is authorized.
