# Current prediction: boundary investigation

## Finding

The 67 crop-face voxels are four isolated, single-slice pancreas-label components, not
connected to the main predicted pancreas. Both 6-neighbor and 26-neighbor connectivity
produce the same 11 pancreas-union components and seven lesion components. This strongly
supports stray predictions at the crop boundary rather than truncation of the main outline.
It does not prove anatomical completeness or establish why the model emitted those fragments.

| Boundary component size | Native z plane | Minimum distance to main prediction | Minimum distance to provided pancreas |
|---|---|---|---|
| 45 voxels | 5, low face | 89.89 mm | 99.07 mm |
| 6 voxels | 5, low face | 135.02 mm | 134.39 mm |
| 1 voxel | 5, low face | 89.12 mm | 98.55 mm |
| 15 voxels | 98, high face | 113.54 mm | 111.23 mm |

All four have zero overlap with the provided pancreas. Distances are between voxel centers,
using the full affine. Native boxes are half-open. The main component is 46,697 voxels,
box `[116,166,35]–[276,223,66]`; inference box `[7,102,5]–[384,285,99]`.
No main-component crop contact and no predicted CT-exterior contact were found.

## Why deleting the boundary fragments is insufficient

The full prediction contains 51,095 pancreas-union voxels (labels 1+2). Its ten detached
components contain 4,398 voxels; only 67 of those touch the crop boundary. Removing just
those 67 would leave 4,331 detached voxels. Five of seven lesion components, totaling
3,095 of 6,547 lesion voxels, have no overlap with the provided pancreas. Four of those
five components are at least 59.76 mm from that outline. These are suspicious predictions,
not reference-confirmed lesion false positives: no lesion annotation was opened in this audit.

Even a plausible total can conceal spatial errors. The largest component has only 12 fewer
voxels than the provided pancreas, yet omits 4,376 provided-pancreas voxels and adds 4,364
outside it. Its overlap Dice is 0.90643 versus 0.86567 for the full union. The provided
pancreas selected the inference region, so these are descriptive comparisons to an assistance
input, not independent benchmark results or proof of an accurate lesion volume.

No component was removed, no new mask or measurement was promoted, and no crop expansion
or second inference was run. The existing UI refusal remains appropriate while component
selection and lesion accuracy are unqualified. Lack of lesion boundary contact alone is not
enough to release the lesion total.

## Reproducibility and limits

Method recorded on AI-05 before component results: analyze both connectivity conventions,
component sizes/boxes, distinct crop-contact counts, CT faces, overlap and minimum physical
separation; preserve every original label. No size/distance threshold was fitted to the case.
The read-only implementation is `src/inference/boundary_audit.py`, with the package/hash/geometry
adapter `scripts/audit_prediction_boundary.py`. It imports no model and writes a new diagnostic
JSON exclusively. It bounds grid size, foreground point count and component count.

Private input: the previously retained, first-sorted exposed development case and immutable
step6000 model from [activation](ON-DEMAND-ACTIVATION-2026-10-20.md). All four package files and
the provided pancreas SHA-256 matched before analysis; original CT/prediction/reference headers
agree in mm geometry. CT array contents were not decoded. No test cases, lesion reference,
checkpoint load, training, or additional source transfer was used.

- Prediction SHA-256: `75fcf8e07d9a8c2650ce842004ad160e4879912debfcd8df944c778416e2ca49`.
- Assistance SHA-256: `1a556c01eb7d3a0b5e8a451ff4c906dae28b98223941030cb719c7c004f6add0`.
- Private detailed report: `outputs/prowl/on-demand-activation-20261020/boundary-component-audit.json`.
- Eight initial synthetic checks passed: disconnected fragments, connected truncation,
  diagonal connectivity, corner counting, anisotropic/sheared physical distance, empty lesion,
  and invalid inputs. Package verification and UI diagnostics checks follow separately below.

## Next reliability checkpoint

1. Preserve the raw output as baseline. Define an explicit candidate for selecting the main
   pancreas component, with separate lesion-component review; never silently delete distant
   lesions or use the assistance outline as a measured model prediction.
2. Freeze a development comparison packet before further outcomes: fixed checkpoint, cases
   selected from the exposed cohort without quality selection, original versus candidate masks,
   pancreas/lesion reference definitions, volume error and spatial/component recall. Record
   reference overlap conventions and exact acceptance limits before validation. This case is
   exploratory and cannot be reused as independent acceptance evidence.
3. Read and review the corresponding development lesion annotation for this case to distinguish
   true separate lesions from false positives. Do not infer that from pancreas overlap alone.
4. Only promote a versioned candidate after the comparison passes. Keep raw and derived mask
   identities, cleanup method and reviewer decision visible; viewer and measurement must use
   the same chosen outline. Failed or ambiguous cases remain unavailable.

AI-05 stays In Progress. Individual-lesion diameter, reliable whole-organ measurement,
normal-reference comparison and final acceptance remain open.

## Delivered diagnostics and verification

The UI now retains source/prediction/model/result/evidence hashes for boundary refusals and
offers **Why this measurement is unavailable** with separate pancreas-label/lesion-label
counts. It explains that counts alone cannot distinguish fragments from truncation. No
component-selection or per-target measurement admission policy changed; both volumes remain
unavailable for this package. Diagnostic counts include no computed volume.

- **11 Python checks pass**, including synthetic package hash substitution and geometry rejection.
- **93 affected UI/library checks pass** across scanMeasurements, nativeMeasurements,
  NativeMeasurementPanel, OnDemandPredictionView, NativeSavedView, savedPrediction and
  onDemandPrediction; production build passes with its existing large-chunk warning.
- Actual retained package loaded in the browser; asking for pancreas size shows unavailable,
  crop counts67/0, image counts0/0 and low/high-z52/15, matching the independent Python audit.
- Vite5180 now serves this retained current-model package at `/saved`; the original historical
  package remains intact. On-demand8017 remains configured; no new job was launched.
- Private screenshot: `outputs/prowl/on-demand-activation-20261020/boundary-ui.png`.

The saved page's existing shell still reports the legacy analysis endpoint as offline; the
on-demand service8017 is independently confirmed configured. That banner does not describe the
retained result or imply a failed measurement load. No runtime or hours credit is claimed.
