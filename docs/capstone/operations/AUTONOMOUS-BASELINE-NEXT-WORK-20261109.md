# Autonomous baseline: next bounded integration work

November9 metadata reconciliation. G3/G4 remain open. The existing autonomous
localizer path and63score/sevenfailure record are reused; no new model inference,
training, image/header audit or relaxed unit/memory gate was performed.

The seven failures are not one demonstrated software bug. Saved failure codes
show six source-unit admission failures (6011,5780,1823,2935,6901,6115) and one
preflight resource failure (5592). Unknown reference-unit flags also remain on
58completed cases. Fixing only the seven failures would not by itself qualify
the cohort, cross-device probability equivalence or end-to-end recovery.

| Priority | Specific work | Evidence needed to finish |
| --- | --- | --- |
| 1. Units/provenance | Reconcile original source metadata or an authoritative case mapping for the six failed CTs and the unknown reference-unit flags. Preserve originals; any supported normalization belongs in an additive adapter/receipt. | Verified source/transform/affine/unit record; ordinary cases unchanged; missing evidence still rejected. Plausible numeric spacing is not unit evidence. |
| 2. Largest case | Inspect the retained5592 admission calculation and eligible dimensions/bytes. Determine whether a bounded tiled/streamed implementation could fit the current limits. | Forecast and CPU/synthetic tests before any real case read; if unsafe, retain a declared failure rather than increasing a limit silently. |
| 3. Numerical comparison | Reconcile the retained cross-device reports. Existing masks agree on the qualified comparison, but probabilities exceeded its frozen tolerance. | A prospective, explicitly admitted qualification protocol or an agreed narrower descriptive claim; no retrospective passing status or tolerance change. |
| 4. Production graph | Bind qualified CT-only localizer, ROI handoff, segmenter, native export and review-admission stages to immutable inputs/configuration. | Actual execute/reuse, stale-input rejection and explicit stage-failure recovery for the expensive stages; existing three-stage saved-result tests alone do not establish this. |
| 5. Model integration | Select the completed segmenter only after full result/closeout review, then prepare the fixed raw/5mm paired evaluation. | Same-scan predicted pancreas, complete cohort/failure accounting and per-model geometry/detection/recall checks. Supplied-region training results cannot substitute for CT-only inference. |

The next CPU coding task is an adapter for a specifically admitted production
stage, with its real receipt and input roles. It is not another generic scheduler
or placeholder inference step. Start with a source-identity handoff and its
invalidation/recovery tests once the unit/resource decisions above identify the
actual eligible inputs. Existing baseline outputs and all failed attempts stay
unchanged. Do not rerun63completed cases merely to rebuild downstream reports.

The [saved metadata review](WEEK-05-AUTONOMOUS70-METADATA-REVIEW-20261104.md),
[G3 reconciliation](../orchestration/G3-EVIDENCE-REVIEW-20261027.md) and
[saved-result adapter](../orchestration/BASELINE-REVIEW-WORKFLOW-20261105.md)
remain authoritative for their respective scopes. This packet specifies the next
work; it does not close a Trello card, authorize a GPU job or qualify a fallback.
