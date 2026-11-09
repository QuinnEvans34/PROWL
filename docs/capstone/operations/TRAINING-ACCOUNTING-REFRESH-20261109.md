# Training page reconciliation — November 9, 2026

The Training page now uses the completed Mac KD lineage and a new Lenovo export
observed at **12:24 p.m. MST, November 9**. These are recorded compute-session
durations, not human work hours, optimizer-only time or measured GPU utilization.

| Category | Hours |
| --- | ---: |
| Mac training sessions, including historical estimates | 323.498 |
| Lenovo training sessions | 322.613 |
| Combined training sessions | **646.111** |
| Of that combined total: early Mac MLflow timestamp estimates | 177.045 |
| Of that combined total: journal-counter sessions | 469.065 |
| Teacher-target generation, separately counted | 90.963 |
| Training plus teacher-target generation | **737.073** |

Use **646.1 recorded training-session hours**, or **737.1 hours including teacher
targets**, in the check-in. The 177.0 estimated hours are already included. Do not
add the displayed KD subtotal or original STU-Net runtime again. These records
are not a certified exhaustive history: unknown durations, old missing records,
standalone inference, engineering, preparation and downloads remain excluded.

## Verified inputs and arithmetic

- Mac: read-only `outputs/mlflow.db`, three prior full-cohort journals, nine KD
  segments/attempts through the completed November 5 continuation, and twelve
  teacher resource records. The early logical MLflow fingerprint is unchanged.
- Lenovo peer commit `4025c4ec623f4e203a675f534af95dfa4eb8c80c`, copied from Git
  without a branch merge. The old nine exported records are byte-value equivalent
  to the November 3 source. Their 964,509.828 seconds plus original STU-Net
  105,530.110 and continuation 91,365.406 equal **1,161,405.344 seconds**.
- Eleven distinct Lenovo execution keys, with MLflow aliases deduplicated by
  the existing collector. Global step 22,571 means **10,571 new updates** in the
  continuation; the parent is one separate execution. No parent seconds were
  added to the continuation's phase duration. No wall-clock extrapolation.
- The combined collector returned 86 unique records; independent summation and
  the existing alias/refused-reset tests verify the counting boundary. The
  adjacent JSON binds exact imported bytes and the resulting combined snapshot.

## Result snapshot

Five complete raw 70-case validations in the corrected continuation:
global14k .353488,16k .396533,18k **.430517**,20k .408581,22k .412172.
Latest22k overlap35/36 positives, alarms26/34 reference-empty scans. The saved
observation records global22,571/24,000. Final validation is pending. No 5mm
filter was applied; provided-pancreas development scope and unresolved pretraining
overlap remain visible. Best so far is not a final selection or independent test.

The byte-exact peer progress export has additional provenance fields and an
offset-form UTC timestamp. `configs/training-progress/current.json` is an explicit
projection into the existing strict aggregate contract: scores unchanged,
timestamp serialized as UTC Z, `run.starting_step=12000` bound to the hash-checked
ancestry sidecar. All raw peer bytes are retained beside the dated source files.
The original November 7 progress export remains unchanged. The UI shows phase
updates/session duration separately from global validation labels.

## Freshness and portability

The current retained snapshots ship in static builds and remain available when
the external drive or local accounting is unavailable. Local source configuration
points to the new dated Lenovo ledger. Reading or refreshing does not make that
export newer: source dates remain visible. It is not an automatic connection to
Lenovo. Further training will require a later verified export to advance the page.

No active scientific source, receipt, model, inference output or MLflow record
was changed. The existing Lenovo run and monitor continue unchanged.
