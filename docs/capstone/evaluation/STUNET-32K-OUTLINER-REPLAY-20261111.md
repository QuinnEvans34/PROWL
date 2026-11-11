# Small-lesion outliner on the 32k STU-Net masks

The Lenovo's complete 32k report contains scores for 70 development scans and zero reconstruction gaps. Validation discarded its voxel masks after scoring. At 3:00 p.m. Mountain on November 11, the Lenovo independently verified the 32k checkpoint and report on E: and C:. The 36k validation still owned the GPU. There is no measured 32k outliner score yet.

- Checkpoint SHA-256 `6de354d26cad3672e14998e5ad90e95603dbd69ef47125abb2f8441597574754`.
- Original `native-32000.json` SHA-256 `b2f0c6eb08beb497e472085b24633e1f05e8a2cef15f1054ab8e8362a0638f99`.
- Baseline 32k raw positive-case mean Dice **0.410898**, all-scan false-positive volume **189.965 mL**, reference-empty alarms **25/34**.

## Reconstruction and handoff

Use the frozen 32k model and the original Lenovo validation preprocessing, supplied pancreas region, 128³ physical windows, stride 64, reconstruction and native-affine mapping. Run a separate inference-only exporter in a free Lenovo GPU window, estimated at about 90 minutes for all 70 scans. Keep the original validator, checkpoints, and reports unchanged. Match every saved per-case metric and tile count before accepting the export. The original masks have no saved hashes, so exact metric agreement verifies replay consistency and cannot prove voxel-for-voxel identity with the discarded masks.

Privately hand off only the native three-class masks, manifest and original report. The manifest uses schema `prowl.stunet.native-mask-export.v1`, step `32000`, `checkpoint_sha256`, `independent_checkpoint_sha256`, `report_sha256` and a `cases` list. Each case has `case_id`, `source_sha256` for CT, pancreas and lesion, `native_shape`, `native_affine`, `tiles`, `mask_file` and `mask_sha256`. Each `<case_id>.npz` contains `shape` and a one-dimensional uint8 `packed` array with consecutive native C-order voxels in low and high nibbles. Classes are 0 background, 1 pancreas and 2 lesion. Padding nibble is zero. No CT, reference labels or checkpoint need to leave the Lenovo for this path.

## Paired Mac evaluation

The [CPU evaluator](../../../scripts/diagnostics/evaluate_native_small_lesion_outliner_20261111.py) binds the exact report and checkpoint hashes, verifies all 70 source identities and native geometries, and requires exact raw per-case metric replay. It selects every predicted 26-connected lesion component from 10 to under 1,000 mm³ using the native affine, including false candidates on reference-empty scans. It uses a point inside the predicted component as the prompt. The frozen 2,400-step outliner sees a native CT crop. A supported contour can replace the candidate, or trim it by intersection with the original. Both edits preserve the predicted pancreas and reject empty, disconnected or merged replacements. Reference labels enter after edits. Score raw and fixed 5 mm arms with the matched controls, reporting overall Dice across the 36 positive scans, small-component hits, recall, pancreas Dice, false-positive volume and empty-scan alarms.

The CPU evaluator passed eight focused synthetic and existing refiner/postprocessing tests. The verified mask packet is the remaining input. The Lenovo has a separately requested 48k continuation, so this reconstruction is pending a noncompeting GPU window and no new GPU job was started from the Mac.
