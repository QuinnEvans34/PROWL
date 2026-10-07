# Predicted-ROI adapter contract v1

Bounded invented-input implementation approved October 6, 2026. This is an engineering building
block for Plan 05 / REQ-M01, M02, M05, M10 and E02/E03. No real cascade policy or operating
threshold has been selected. Existing provided-region consumers and the shared mapper are unchanged.

## Inputs and trust

`plan_predicted_roi` accepts an in-memory native-grid binary pancreas prediction, affine, explicit
study/CT identity, prediction record and independent trusted prediction-record SHA-256. The optional
tensor shape supports smaller invented fixtures; production-shaped default is 144³. No annotation,
lesion, source path, checkpoint loader or model-forward argument exists.

The exact prediction-record fields are:

| Field | Required meaning |
|---|---|
| schema_version | Literal `1.0.0` for this adapter's local control format |
| task | Literal `binary_pancreas` |
| prediction_id / run_id | Nonempty identities, pinned by the caller's trusted record |
| model_sha256 | Lowercase SHA-256 of the declared localizer model artifact |
| source_identity | Exactly study_id and ct_sha256; must match the separately supplied image identity |
| native_shape / native_affine | Exact grid of this already native-restored prediction; must match the source grid |
| units / full_volume | Literal mm / true; the external trusted producer must establish those facts |
| binary_mask_sha256 | SHA-256 of C-order uint8 binary mask bytes; shape/affine are bound separately |

Records must be finite canonical JSON, without extra reference fields. The trusted record pin must
come from independently established controls, rather than an untrusted payload's adjacent digest.
The adapter verifies mask bytes and grid/record consistency. It cannot authenticate CT file bytes,
confirm historical model eligibility or prove a producer's full-volume/physical-unit assertion.
Those remain caller qualification duties before any real integration. Replacing a run/model/record
requires a new independently accepted pin; matching shape alone is insufficient.

## Fixed diagnostic and output

Policy ID: `predicted-pancreas-all-support-10mm-diagnostic-v1`. Keep every binary prediction component;
take its complete RAS support box, expand by 10 mm per axis with ceil coverage and clip to the
acquired source grid. Use the unchanged geometry-v1 1 mm sampling, uniform letterbox, symmetric
padding and HU window [-100,250]. A boundary-contact/margin record reports clipping; no reference
can enlarge the crop. No plausible-size threshold or largest-component cleanup is adopted here.

The JSON plan includes component/schema/policy identity, the original prediction record and its pin,
margin telemetry, the shared predicted-region transform and its independent full-record hash.
The caller separately pins the complete plan using `content_hash(plan)`. Both preparation and
restoration require that trusted plan pin and revalidate the derived physical transform.

`prepare_predicted_image` requires the same study/CT/grid declaration and fixed plan. It maps and
normalizes only the CT. `restore_predicted_probabilities` accepts three finite normalized class
probabilities and restores them to the plan's exact source grid; outside the ROI the vector is
[1,0,0]. No final operating threshold, contour acceptance or measurement publication is added.
Inputs and control records are not mutated.

Support is limited to signed-permutation axis-aligned affines, as in the existing mapper. Oblique/
sheared, singular/nonfinite grids and source/sampling/tensor envelope violations are refused.
All-support boxes can be too large or sacrifice effective resolution; successful mapping does
not mean a useful localization or safe anatomical contour.

## Failure contract

`PredictedRoiError` is a ValueError with a stable `reason` and readable detail. Reasons include
source identity/mismatch, prediction record/pin/lineage/grid/payload, invalid prediction,
empty localization, unsupported geometry, unsafe ROI, plan record/pin/policy/geometry,
invalid image and invalid probabilities. An invalid prediction is not converted into an empty
success, reference box or whole-volume fallback. Callers must retain failed requested cases in
their execution/evaluation denominator; this pure adapter does not own a case ledger.

## Verification and next real boundary

Invented tests establish independent physical bounds/world coordinates for axis permutations,
reversal, anisotropy, nonzero origins, odd padding and all six source faces; all-component support;
payload/provenance/grid rejection before cropping; immutable input, HU clamping and exact/simple
probability restoration; and an outside-ROI reference component retained in the test denominator.
The existing mapper/loader/qualification tests are regression checks, not new real-data qualification.

A real zero-update packet must separately specify exact members, purpose permissions, matched
source/grid/model/prediction/policy identities, trusted controls, source/reference access budgets,
failure/coverage/scale/foreground reporting, resource/storage limits, native overlays and independent
recovery. It must distinguish this diagnostic from the development-selected final ROI policy and
provided-region results. No real operation is enabled by this contract.
