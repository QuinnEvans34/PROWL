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

## Mac reconstruction alternative

Quinton chose to keep Lenovo's 48k continuation first and use the Mac for the replay if it qualifies. The [Mac reconstruction runner](../../../scripts/diagnostics/reconstruct_mac_stunet_32k_masks_20261111.py) inherits the frozen 128³/64 physical reconstruction and MPS cache-release path from the earlier 24k study. The first two scans qualify the replay and its remaining time estimate. Keep AC, the exclusive MPS guard, CPU fallback disabled, 8 GiB MPS, 12 GiB combined RSS, existing free-space and backup limits, and a four-hour bounded reconstruction. The largest case starts the pilot. A positive-case Dice difference above .01 from the corresponding Lenovo report stops the attempt. This is a gross-drift check. The paired outliner result uses a separately archived and independently verified **Mac 32k raw baseline**.

The Mac can initialize MPS in the experiment runtime. Both architecture sources are present, the local Expert has no resident model, and the 70-case worst-case packed archive is 1.053 GiB including metadata reserve. Projected total retained backups were 25.908 GiB under the existing 26 GiB cap, with about 71.78 GB of internal free space after that reserve. Recheck at launch. Nine focused tests passed including geometry, class packing, and drift rejection. No masks were reconstructed.

The private input is pending explicit transfer authorization. The proposed packet contains only `model-only.pt`, the byte-identical `native-32000.json`, and `manifest.json`. The manifest records `step`, `source_checkpoint_sha256`, `independent_checkpoint_sha256`, `tensor_equality`, `report_sha256`, and `model_sha256`. The model envelope contains `step`, `parent_sha256` and `model`. The full checkpoint and optimizer remain on the Lenovo. Verify the outer packet SHA and regular members before extraction, then the exact file and source identities. The automatic approval review blocked the proposed Lenovo-to-Mac transfer because the artifact and destination needed specific authorization. No alternate transfer was attempted.

## Authorized private receive

Quinton explicitly authorized the Magic Wormhole transfer of the model-only
32k weights, original validation report and verification manifest between his
Lenovo and Mac. No CT, reference mask, optimizer state or other payload is in
scope. The [packet importer](../../../scripts/diagnostics/import_mac_stunet_32k_packet_20261111.py)
accepts only the three authorized regular files, checks the outer archive and
member hashes before extraction, and creates an import receipt in a fresh
private directory. Eleven focused tests passed, including rejection of extra
or unsafe archive members. No model bytes were read as part of these checks.

The Lenovo confirmed the 48k continuation was advancing and that the registered
36k checkpoint scored .4293 raw Dice. The new phase's first scheduled evaluation
is at 38k. The Mac received the 232,765,440-byte packet on November 11 and verified
the three file identities against the sender's manifest and original report. The
archive SHA-256 is `27fc428553fe360c0f914eea99829c5c250216b66af62a5d66369d7b24d88309`.

The Mac started one replay in `stunet-32k-mac-replay-20261111-a01`. The idle AI
Expert released its GPU lock and switched to source search during replay. The
supervising wrapper restores live answers when replay exits. A single CPU
comparison is queued for `stunet-32k-mac-outliner-20261111-a01` and requires a
verified replay closeout with a matching independent copy. No paired scores are
available yet.

Both pilot scans passed and their independently reopened masks matched the
written masks. The positive pilot had zero Dice drift against the Lenovo report.
The pilot projected 74.5 minutes for the remaining 68 scans, including the
runner's 1.5× margin. Peak MPS memory through the pilot was 6.02 GiB. The next
scan started in the same owned worker.
