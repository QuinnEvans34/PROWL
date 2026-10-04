# CAP-EXP-014 results — v5 recovers pancreas predictions; contours remain poor

D-335 approved the exact request, fresh14-target read scope, cold recovery and2GiB allowance. The once-only 48-update producer and zero-update independent recovery completed. All five predeclared training-only screens passed. This is a limited engineering result: native training pancreas Dice0.159877 and lesion Dice0.055142 remain low, predictions are substantially oversized, and report-only2514 lesion recall falls to0.123936. No usable-contour, specificity, generalization or promotion claim. No pending run or automatic extension.

## Fixed comparison and interpretation

Same six training members3/26/2232/2973/5821/6238, report-only2514,144³/batch1/seed42, fresh initialization, zero jitter, provided-pancreas-reference ROI, AdamW0.0003/decay1e-5/constant,48updates/eight exposures per training member, checkpoints/evaluation0/6/24/48 and terminal48 primary. Exact input controls, initializer and original-reference hashes match CAP-EXP-013. Config differences are schema version and loss ID only. CE changes from lesion256-weighted voxel reduction v3 to per-case present-class mean CE v5; foreground Dice remains unchanged. No weight import, continuation, case filtering, threshold selection or best-checkpoint selection.

|Role|Native macro metric|Initialized D-325|CAP-EXP-013 v3 step48|CAP-EXP-014 v5 step48|
|---|---|---:|---:|---:|
|train|pancreas parenchyma dice|0.084136|0.000000|0.159877|
|train|pancreas parenchyma recall|0.510133|0.000000|0.568033|
|train|lesion dice|0.001779|0.030886|0.055142|
|train|lesion recall|0.012986|0.994807|0.833063|
|validation|pancreas parenchyma dice|0.082410|0.000000|0.333197|
|validation|pancreas parenchyma recall|0.254381|0.000000|0.742709|
|validation|lesion dice|0.000061|0.025448|0.006397|
|validation|lesion recall|0.000532|0.974468|0.123936|

V3 collapsed pancreas predictions to class2. V5 produces positive pancreas overlap in every training case and exceeds the initialized pancreas Dice baseline0.084136. Lesion macro Dice improves versus v3, but lesion macro recall decreases from0.994807 to0.833063. All training reference lesion components have at least one predicted lesion voxel; that criterion does not mean complete coverage. Report-only2514 chooses nothing: its pancreas Dice improves to0.333197 while lesion Dice declines0.025448→0.006397 and recall0.974468→0.123936. A single fixed case is not a generalization estimate, but this large coverage loss remains visible and prevents interpreting the training pass as overall success.

## Frozen training screens and excess foreground

Pancreas macro Dice>0.08413627515978402; positive pancreas TP in each training case; lesion macro Dice≥0.03088619116270695; macro lesion recall≥0.8; every training lesion component hit. All five pass. No new numerical false-positive-volume acceptance bar is introduced after seeing results. The following full-source native numbers preserve oversizing and tiny/boundary failures rather than filtering them out.

|Case|Role|Pancreas Dice|Lesion Dice|Lesion recall|Lesion precision|Predicted/reference lesion volume|Lesion FP mL|
|---|---|---:|---:|---:|---:|---:|---:|
|3|train|0.1870|0.0590|0.7905|0.0306|25.81×|132.57|
|26|train|0.1670|0.0835|0.5751|0.0450|12.78×|174.89|
|2232|train|0.1660|0.0676|0.8262|0.0352|23.46×|147.24|
|2973|train|0.1342|0.0052|1.0000|0.0026|383.26×|215.90|
|5821|train|0.2062|0.0573|0.8258|0.0297|27.82×|160.32|
|6238|train|0.0989|0.0584|0.9807|0.0301|32.61×|144.86|
|2514|validation|0.3332|0.0064|0.1239|0.0033|37.75×|150.92|

The tiny2973 target remains included:383.26× lesion volume is particularly poor even though its component is hit. Boundary6238 remains included with its native component and acquired-source-boundary contact. False-positive volumes use determinant of native affine, independently recomputed; mm³→mL divides by1,000. Pancreas-only targets exclude reference lesion voxels; union metrics are reported separately. No negative-case specificity inference: this real pilot has positive lesion references. Earlier invented negative checks validate mechanics only.

## Native execution, target scope and recovery

- Producer worker448.744s; supervised468.026s. Cold worker35.638s; supervised57.203s. Combined525.229s (8.754minutes), within30minutes/20producer/5cold.
- Supervisor sampled producer RSS4.790GiB; worker-reported peak4.822GiB; sampled MPS driver4.776GiB, both below12GiB. AC/free-space/MPS fallback/native monitor checks passed.
- Exactly48 real optimizer calls; each of six training members8exposures, evaluator never optimizes. Four checkpoints/seven native exports/image-probe-summary bundles:14artifacts, 387 physical files across three copies, required one-copy payload583,041,786B. Primary, independent keeper and restored required bytes match exactly.
- Fresh terminal-stage14original targets: hash1,265,220B, decode1,265,220B, expanded272,494,704B, exactly scope; zero original CT arrays. Producer performs image-only inference before target-only scoring; independent integer oracle agrees with native confusion counts. Original arrays are not reread for the audit.
- All14artifacts cold restore with primary Python path/descriptor reads blocked; cooperative guard is not an OS unmount. Four checkpoint probability probes have delta0; all seven native predictions reproduce exactly. No original CT/target reads or optimizer calls in real cold recovery. Native score arithmetic is independently audited from retained evidence; original references are not reread in recovery.
- Clarification retained: real cold recovery makes no next update and `next_weight_max_difference` is null. The separate accepted invented rehearsal previously proved next-update recovery to7.45e-9. No fabricated real next-update claim or new update added to frozen code.
- Frozen142 producing/test pins and2,933-native-test baseline unchanged; no source edits or unnecessary suite rerun. No unexpected producer/recovery fault. A live read-only progress query initially looked for top-level state rather than the journal event envelope; corrected query only, no worker change.

## Visual review and evidence

All seven saved sheets were inspected, including tiny2973, source-boundary6238 and report-only2514. Class1 is present again, but scattered foreground extends far beyond references; class2 overlap varies and excess class2 persists. These observations agree with low precision and large volumes; they do not certify a contour. Gray displays reconstruct normalized cached ROI, not original CT outside it. Sparse selected planes are not a complete-volume review; unseen components remain in numeric accounting. No disease/subtype/management interpretation.

- Exact request: `e63f5613085bf202bbb1157616afc7492f84e0855e81d243dd3981ed41ec4a10`.
- Actual capability transport: `5dfc16d148d159d4edb2b5fcd2109957deb519821871f118c958e8a9b9e53b51`; canonical85b9a90c remains a separate semantic identity.
- Storage authority: `d0f99c36c800014c6a4cbf5518a905119cc29c9e01f6344198f84716d5881520`; launch authority: `7ba6ff6a99a932f81b0ad37f294ab4a0435329aab031fabbcdb28f7bde2dd2ef`.
- Producer package: `94e4e3daff66d50c582bd30b66a78259d2ef1597af74c764269155c45939c260`; cold package: `d52c445ddc1646c6d352dff5585118bb50ac73ca812dafc700a8738fd655c687`.
- Terminal weights: `6e63d135eea06bf8f60c21a66214890a0734406a614a9a2302691ca84f5096a3`.
- Records: `outputs/prowl/CAP-EXP-014-INDEPENDENT-AUDIT-20261003.json`, `CAP-EXP-014-BEFORE-AFTER-20261003.json`, `CAP-EXP-014-VISUAL-REVIEW-20261003.json`, `CAP-EXP-014-LAUNCH-PREFLIGHT-20261003.json`, `CAP-EXP-014-CONTROL-PRESERVATION-20261003.json`.

Fixed whole-backup ceiling18,318,645,873B and registered20GiB stay unchanged. After artifact restoration, whole root17,338,477,614B; control/source/approval/view review preservation is counted additionally under that same ceiling and64MiB review reserve. Preservation record gives final exact inventory; all older/failed evidence stays intact. Source terms, source activation, original membership, qualifications/holds and formal experiment-registration status are unchanged. No Git commit/push or Claude lane edits.

## Recommended next discussion

The saved terminal keeper was inspected without new model/source/cache calls: epoch mean losses2.037188,1.856565,1.810204,1.772105,1.776859,1.742606,1.736169,1.692695; last/first0.830898. Training tensor pancreas Dice at0/6/24/48 is0.031194/0.007578/0.106990/0.159272, lesion Dice0.001238/0.012272/0.038591/0.054626. Tensor diagnostics are separate from original native metrics. The objective is still falling and training overlap still improves at the last measured checkpoint; these observations support a duration hypothesis, not proof of convergence or a longer run’s success. `outputs/prowl/CAP-EXP-014-TRAINING-HISTORY-20261003.json` preserves all member losses and training-only cadence.

This resolves the immediate class-collapse comparison but does not justify broad long-duration training yet. Recommend discussing a fresh, longer same-cohort duration comparison, with a predeclared pancreas/lesion coverage policy, false-positive reporting and exact resource/storage proposal. Keep all six training members, including tiny and boundary cases; keep2514 report-only rather than tuning against its result. Confirm the planned route to a varied, separately qualified multiclass train/development cohort and realistic ROI/negative-case evaluation before a scale-up. No follow-up model forward, optimizer call, original-target read, duration expansion or new experiment is authorized by this recommendation. Preserve terminal48; don't extend or rerun its consumed request.
