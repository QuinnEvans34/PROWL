# Predicted-ROI adapter handback — October 6, 2026

**Finished:** T01's invented-only adapter/contract and affected regression checks.
**Checks:** 58 new adapter checks + 75 unchanged geometry/loader/qualification checks = 133 passed,
zero failed/skipped, 0.58 seconds on native Python 3.12.13. No real source/cache arrays, model
forwards/updates, accelerator execution, request consumption, registry or external-drive writes.
**Decision needed:** none within T01. Real input/policy qualification remains a separate packet.
**Next:** the approved T02 duration-comparison draft, then T03/T04; no scientific launch.

## Change and evidence

New [adapter](../../../src/data/segmenter_predicted_roi_v1.py),
[tests](../../../tests/test_segmenter_predicted_roi_v1.py) and
[contract](../imaging/PREDICTED-ROI-ADAPTER-CONTRACT-V1.md). The planning
[packet](PREDICTED-ROI-ADAPTER-PACKET-2026-10-06.md) records Quinton's October 6 approval.

The adapter binds exact image/prediction identity, native shape/affine, independent record/plan
pins and binary prediction payload. It keeps all predicted components with the named 10 mm
diagnostic and reuses the existing physical mapper. Empty/unsafe, nonbinary/nonfinite, stale
identity and wrong-grid cases fail explicitly. CT preparation and three-class native restoration
remain image-only; inputs are immutable. An invented outside-ROI lesion remains uncovered and in
the independent test denominator. No reference can choose or repair the ROI.

First targeted run: 126 passed in 1.00 seconds. Code review identified that non-JSON/nonfinite
control metadata needed a stable adapter failure reason. Added explicit serialization handling
and malformed-pin, HU-clamp/no-file-open and exact probability-roundtrip checks; final 133 passed.
No failed test run was discarded, and no old mapper or test was repaired to accommodate this code.

Command:

```text
.venv-prowl/bin/python -m pytest -q tests/test_segmenter_predicted_roi_v1.py tests/test_segmenter_geometry.py tests/test_segmenter_geometry_loader.py tests/test_segmenter_geometry_qualification.py --junitxml=outputs/prowl/WEEK-01-EXECUTION-20261006/adapter-tests-final.xml
```

Private local evidence directory: `outputs/prowl/WEEK-01-EXECUTION-20261006/`; initial/final JUnit
records are retained. This directory is a local review record, not an independently protected keeper.
The check scope is four invented test modules, not the current full project suite.

| Source/check | SHA-256 |
|---|---|
| New adapter | `06ea6bb4dee1fd4d87261807e6b95dcac9eb8b9cc68b4dd1274850e2f0db302b` |
| New test module | `7b75d328057073275045a66e5ad5f416c332a7d427d9b33f3a42fe02311e6ce2` |
| Shared mapper, unchanged | `01833209fefd61b4b86417071ece5eed4ebfa8c44aa509d6be29806ff3e284ca` |
| Existing geometry tests, unchanged | `88fe43ca46f2158541107b7788d40350eedc33619d5a3e6d61a4de6bb3cfa020` |
| Existing loader tests, unchanged | `a4962dbd74fa8cb01b1a063b94f7710e8105f6a42b65d19a2a6568ae05e3b516` |
| Existing qualification tests, unchanged | `114b997e43915885804852d09c84d9eb4b0dd6ff8a2d6eec012267dedf311dae` |

## Limits and next real-input boundary

The trusted caller must establish CT file identity, model eligibility, native grid/units and
full-volume prediction provenance. The adapter proves internal binding, not those facts' authenticity
or permitted use. Full native-size resource/overlay qualification is not included. Existing geometry
envelopes are retained, and oblique/sheared grids are unsupported rather than approximated.

All-support/10 mm is a diagnostic, not the development-selected cascade policy. Fragmentation or
false foreground can produce a large, coarse region; successful mapping proves neither containment
nor useful contours. Existing inference/training consumers are not switched to this adapter.

A proposed next zero-update packet needs exact matched study/model/prediction/policy controls,
purpose permissions, source/reference access budgets, failure and effective containment accounting,
memory/time/storage limits, native overlays and independent recovery. Ground truth must remain in
a separate evaluation join. D-335 remains the imaging experiment checkpoint; its requests, cohorts,
holds and fixed backup ceiling are unchanged. No commit/push or retrieval-owned edit.
