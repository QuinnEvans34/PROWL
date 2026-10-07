# Duration policy v1 — native-count contract

Quinton approved DUR-01 and its192-update planning settings on October6,2026. This contract
describes a pure standard-library module, not a trainer, reference reader or execution permit.
It supports the same6train/1report-only engineering comparison proposed in
[the duration plan](../operations/SEGMENTER-DURATION-COMPARISON-PROPOSAL-2026-10-06.md).

## Public operations

- `record_digest(record)`: SHA-256 of UTF-8 JSON, sorted keys, compact separators, no ASCII escaping
  and no nonfinite values. Independent control pins must come from the trusted caller.
- `build_policy(baseline, *, trusted_baseline_sha256, tiny_case_id, boundary_case_id)`: verify the
  baseline and return a deep-copied, fixed192-step policy. It does not load D-335 records itself.
- `validate_policy(policy, *, trusted_policy_sha256)`: verify the independent policy pin and exact
  reconstructed fixed policy. Invalid controls raise `DurationPolicyError`, with `.reason`.
- `cadence_plan(policy, *, trusted_policy_sha256)`: expected checkpoint/screen/report/exposure
  events at0/48/96/144/192; exposure counts0/8/16/24/32 are planned, not measured optimizer events.
- `assess_screen(policy, screen, *, trusted_policy_sha256)`: assess numeric outcomes and return
  a result ledger. Invalid trusted policy raises; an invalid/incomplete screen returns `stopped`.

## Exact JSON records

Baseline fields: `schema_version="1.0.0"`, `kind="duration_native_count_baseline_v1"`, `cases`.
Cases are exactly six distinct ordered `train` rows and one distinct `report_only` row. All baseline
rows must be valid. The tiny and boundary IDs must be different training members; the boundary row
must explicitly report source-boundary contact. Invented tests use invented IDs. Future real binding
must supply the frozen D-335 identities, including2973/6238 markers and report-only2514.

Each row has only `case_id`, `role`, `status`, `reason`, `counts`, `reported_metrics`.
Statuses are `valid`, `failed`, `empty`, `abstained`. Valid rows have null reason and numeric counts;
other statuses require a nonblank reason and null counts/summaries. A valid zero prediction on a
positive reference is numeric evidence with zero Dice/recall/precision, distinct from failed output.

Counts have only:

| Field | Meaning / validation |
|---|---|
| `confusion_matrix` | Native3×3 nonnegative integer matrix; rows reference, columns predicted; codes0background/1pancreas parenchyma/2lesion. Boolean/float counts refuse. Total1–46,219,264. |
| `components` | All ordered IDs1..N, each with `component_id`, positive `reference_voxels`, bounded `true_positive`. Totals equal lesion reference and TP. |
| `voxel_volume_mm3` | Positive finite native voxel volume≤1e9mm³; future producer obtains it from abs(det(native affine)). |
| `source_boundary_contact` | Boolean source-contact marker, retained unchanged from baseline. It does not independently prove geometry. |

This positive-pilot slice requires nonempty pancreas and lesion references. Unknown empties and
real negatives cannot be introduced through this interface. Candidate native total, per-reference-class
counts, component IDs/sizes, voxel volume and boundary marker must equal the baseline. No target
arrays, paths, model parameters, masks or source-read grants are accepted fields.

Optional `reported_metrics` must exactly equal the canonical JSON of recomputed metrics for all
three classes. Metric names: `target_voxels`, `predicted_voxels`, `true_positive`, `dice`, `recall`,
`precision`, `false_positive_ml`, `predicted_reference_ratio`. Boolean aliases are rejected.
Union TP includes within-foreground class confusions; union counts are not the sum of separate TP.

Policy records embed baseline/pin, ordered case IDs/markers, fixed cadence/rules and false flags
`promotion_allowed`, `specificity_claim_allowed`, `execution_authority`. Unknown fields or altered
rules/cadence/permissions refuse even with a newly supplied self-pin. Authentic marker/source
selection remains the trusted caller's responsibility; these checks are not a provenance oracle.

Screen fields: `schema_version="1.0.0"`, `policy_sha256`, `baseline_sha256`, integer `step`,
`outcomes`. Steps are48/96/144/192. Interim screens require all six train rows; terminal192 also
requires the report-only row. Order may differ; IDs/roles cannot. Extra/duplicate IDs refuse.

## Arithmetic and decisions

Dice=2TP/(reference+predicted), recall=TP/reference, precision=TP/predicted (zero if no positive
prediction), FPmL=(predicted−TP)×voxel_mm³/1000. Rational arithmetic controls thresholds exactly;
JSON outputs use floats. Macro values average all six cases. Pooled Dice/recall/precision use summed
counts; pooled FPmL sums each case's physical volume. Report-only values never enter those means.

At each screen: complete valid output, pancreas TP>0 in each case, pancreas macro recall≥baseline−.03,
lesion macro recall≥max(.8,baseline−.03), each class/case and each lesion component recall≥baseline−.10,
all components TP>0, tiny-case components≥.95, each lesion FPmL≤1.25×baseline. Zero baseline FP
requires zero candidate FP; no epsilon denominator or allowance is invented.

Terminal success additionally requires pancreas macro Dice≥baseline, lesion macro Dice≥1.20×baseline,
mean lesion FPmL≤.80×baseline and every case FPmL≤1.10×baseline. The1.10rule is a terminal
improvement bar; the1.25screen guard still applies at192. Report-only quality remains separate,
while a missing/invalid report prevents complete terminal success.

Results include step/identity, every named check, requested-case `ledger`, valid `per_case` metrics/
components/boundary markers, all-six-case `aggregates`, separate `report_only`, reasons and false
claim/authority flags. If any required outcome is missing/invalid/failed/abstained, aggregate remains
null; a successful-subset mean is never substituted. Valid individual evidence remains available.

| Decision | Meaning |
|---|---|
| `continue` | Complete intermediate screen passes all guards; a future executor still needs its own permission and stop integration. |
| `stopped` | Invalid/incomplete screen or a coverage/interim-FP guard fails. |
| `terminal_insufficient` | Complete terminal coverage passes, but at least one terminal improvement target fails. |
| `terminal_pass` | Every terminal completion/coverage/improvement condition passes. Engineering result only. |

The60minute/12GiB proposal and storage/keeper limits are not enforced by this pure module. Future
consumer work must authenticate scorer/source/role lineage, stop before the next optimizer update,
enforce resources and prove independent recovery. This slice does not make that consumer or a
real request, import prior weights, change protected membership, select a held-out result or run MPS.
