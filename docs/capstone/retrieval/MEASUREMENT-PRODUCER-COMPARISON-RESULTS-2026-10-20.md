# Retained step6000 producer comparison

**Date:** October 20, 2026  
**Status:** Comparison complete; AI-05 measurement accuracy remains open.  
**Scope:** The user authorized the prepared metadata-only request to *Plan capstone experiment workflow*. Existing raw step6000 reports and local retained comparison JSON only; no weights, patient arrays, inference, training, threshold changes or UI promotion.

## Finding

The original Windows producer and Mac raw predictions have exactly matching target, predicted and true-positive counts for both pancreas and lesion on all three requested cases. All six Dice values also agree. The low lesion recall and false positives were already present in the saved producer evaluation; this comparison demonstrates no Mac-specific count discrepancy.

| Case | Reference lesion voxels | Predicted lesion voxels | True positive | False positive | False negative | Lesion Dice |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 927 | 11,301 | 1,487 | 668 | 819 | 10,633 | 0.104473 |
| 514 | 0 | 2,223 | 0 | 2,223 | 0 | 0 |
| 698 | 0 | 11,123 | 0 | 11,123 | 0 | 0 |

These are raw outputs, not the component-selected candidate. Empty references mean annotation-empty, not clinically verified healthy. Case927's `case_detected` flag means some reference-component overlap; its lesion recall is still only5.91%.

## Verification and provenance

The remote owner verified the unchanged report digest, exact70 development membership, raw/step6000 journal rows and producing source pins. Locally,78 metadata assertions pass:18 class counts,6 Dice values,12 derived FP/FN counts,18 reconstruction fields,3 previously recorded checkpoint identities,9 original source hashes,6 CT shape/affine comparisons and6 available producer source hashes. The executor source is absent from the received bundle; its pin verification is reported by the remote owner, not independently repeated here.

Oriented ROI bounds, tile counts20/18/36, zero uncovered voxels, outside-region background and minimum blend weight all agree. ROI bounds are compared in the oriented grid, not against original-native boxes. Producer physical sampling spacing is distinct from original CT voxel spacing.

- Run: `pants_pancreas_region_24k_20261019`, raw step6000.
- Saved report SHA-256: `c70d3fd952efbbec3dffb1dd7fb6428f243927761c6b21cdd921ec4a22b0398f`.
- Previously verified checkpoint SHA-256: `ac50b534eb5e5334bfb29626743ed626a1d16363d8ac1c3374165140318f397f`.
- Development list SHA-256: `6b69605f49de0dd20346bee9db7fea4842c050cea4cf8d85268775deabc301bf`.
- Receipt transcribed from complete remote command output: `af6cad753674d8fc25822471850b891f9410b113d5795291fe3aa3163ac83b07`; locally serialized bytes also match the remote owner's reported receipt digest.
- Private evidence: `outputs/prowl/measurement-producer-comparison-20261020/` contains `mac-raw-counts.json`, `producer-receipt-transcribed.json` and `comparison.json`.

The original report does **not** embed a checkpoint hash. Checkpoint association relies on the prior verified handoff and retained run/step lineage; weights were not reopened. Matching counts do **not** establish voxelwise masks, probability equality or CUDA/MPS numerical parity. No new accuracy or whole-organ coverage acceptance follows.

## Decision and next work

Keep the current measurement guard and original outputs. CP05 found no demonstrated source preprocessing/class-map mismatch, and this comparison shows the same errors in the original producer. Further adapter rewrites or arbitrary component filtering are not supported by this evidence.

The next useful decision is a controlled model-quality comparison with the training owner: review already-completed development reports before choosing a single candidate for a bounded local comparison. Preserve the fixed subset and source identities; measure positive-case recall, annotation-empty false-positive volume, pancreas/lesion volume errors and boundary contact separately. Do not choose a candidate from Dice alone or silently substitute a newer/best/EMA checkpoint. Any later calibration experiment must balance missed lesions against false positives and preserve a separate evaluation set. No newer report request, checkpoint transfer or new inference was performed in this checkpoint.

Case698's source-boundary contact remains a separate coverage limitation. Even a better segmentation cannot establish anatomy outside the acquired scan; whole-organ volume stays unavailable when coverage cannot be established.
