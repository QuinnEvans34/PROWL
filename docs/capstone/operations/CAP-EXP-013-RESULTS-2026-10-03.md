# CAP-EXP-013 — completed; early pancreas-class collapse

**The exact48-update run completed and its independent recovery passed. The model fails three-class separation:** all seven terminal native predictions contain zero pancreas-parenchyma-class voxels and very oversized lesion masks. The predeclared initial lesion-signal screen passes, but this is not a usable three-class result or a promotion. No extension or new run is authorized.

Authority: D-328, Quinton's “Yes, full approve. Continue on.” in response to the [exact launch review](CAP-EXP-013-LAUNCH-REVIEW-2026-10-03.md). Exact request `eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9` is consumed. Approval transport SHA `9f48d34cee8257804ce52995c8df311c77a9a1d89eb7a139366d66f74cc95b53`; launch preflight `cf71b5d433321684430a32b4531576fee94d2345bf5da5d8bd5e1118ac6ae29e` verified current14-target observations, root/storage/source/runtime and power before consumption. No source metadata drift occurred.

## Exact execution and scope

Fresh seed42 three-class SegResNet,144³ float32/batch1, provided-pancreas ROI, zero jitter, v3 weighted CE `[1,1,256]` plus present-foreground Dice, AdamW0.0003/decay1e-5,48committed updates. Six training cases3/26/2232/2973/5821/6238 each received exactly eight exposures. Case2514 evaluated only. Complete checkpoints and tensor evaluations at0/6/24/48; terminal48 remains primary.

Initial weight hash `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`; terminal `20bfe8c800290f4f985a291bc68d51327558b897dfe40d291d99181658a24005`. No historical, synthetic-trained or third-party initialization/import. Cold restores are same-run evidence replay, not new initialization or training.

All14 original pancreas/lesion targets passed full compressed hashes, gzip integrity, headers/scaling/binary semantics, source geometry and retained count/component identity. Exact scope:1,265,220B compressed hashing,1,265,220B decoding,272,494,704B expanded. Zero original CT rereads. All terminal exports use the unchanged continuous-three-channel native inverse before argmax and background outside ROI.

Six/one cohort, all twelve permanent candidates/five holds, localizer153members/23holds and original protected splits remain unchanged. All111 producing pins and the root registry match D-327. No producing source or dependency edits occurred; its2,574-test qualification baseline remains applicable and was not rerun. This turn's verification was the actual native transaction, cold replay, independent artifact/count/metric audit and technical view inspection.

## Original-native before/after result

The before reference is the accepted D-325 original-native baseline, SHA `f4bfcaf0dd63ff066ce8456d66b978e738e8cca8322a6c74fcce23c89b090db2`. Macro training values average all six cases; validation is the one separate case. No case/component was removed.

|Metric|Train before → terminal48|Validation before → terminal48|
|---|---:|---:|
|Lesion Dice|0.001779 → **0.030886**|0.000061 → **0.025448**|
|Lesion recall|0.012986 → **0.994807**|0.000532 → **0.974468**|
|Pancreas-parenchyma Dice|0.084136 → **0**|0.082410 → **0**|
|Pancreas-parenchyma recall|0.510133 → **0**|0.254381 → **0**|
|Pancreas/lesion-union Dice|0.084955 →0.306427|0.078030 →0.312704|
|Pancreas/lesion-union recall|0.515303 →0.867473|0.258889 →0.640682|
|Missed reference components|3/6 →0/6|0/1 →0/1|

The frozen lesion-signal rule required both training macro lesion Dice and recall to exceed the before values. It passes. That screen is an early learning observation, not a sufficient segmentation-quality criterion. The class failure and FP volume remain central results; no screen was rewritten after seeing them.

|Case / role|Original lesion voxels|Terminal lesion voxels|Predicted/reference ratio|Lesion Dice|Lesion recall|
|---|---:|---:|---:|---:|---:|
|3 train|1,055|61,804|58.58×|0.033567|1.000000|
|26 train|7,244|255,794|35.31×|0.055079|1.000000|
|2232 train|3,867|211,878|54.79×|0.034837|0.971813|
|2973 train|124|103,546|835.05×|0.002392|1.000000|
|5821 train|3,399|217,591|64.02×|0.030762|1.000000|
|6238 train|7,412|507,943|68.53×|0.028679|0.997032|
|2514 validation|1,880|142,100|75.59×|0.025448|0.974468|

Every native pancreas-class predicted count is zero. Training pooled lesion counts are23,101reference,1,358,556predicted and22,970TP; pooled Dice0.033250/recall0.994329. All source components/bounds/boundary contacts and outside-pancreas references are retained, including tiny2973's124voxels and6238's1,603outside-pancreas lesion voxels. Independent pure-Python count/formula/aggregate checks passed without another original-target read. The producer's separate nine-intersection oracle agreed with its confusion matrices.

## When the class failure appeared

Saved tensor evaluations, distinct from original-native truth, already have pancreas Dice/recall0 at step6. Training pancreas-class predicted counts are381at6,1at24,0at48; the381and1voxels have zero pancreas TP. Validation counts are20,0,0, also zero TP. Thus the loss of useful pancreas classification occurs during learning, before native export.

Saved case3 probability probes confirm finite class competition rather than a zeroed channel. Mean pancreas probability falls0.394→0.279→0.266→0.249 at0/6/24/48. It wins8tensor voxels at6 and none at24/48. Terminal maximum pancreas margin against the other channels is−0.082887. These probability statistics concern case3 only; no extra model forwards were made for this inspection.

The objective uses a weighted voxel-mean CE and equal averaging of the present foreground Dice terms. Frozen target counts give pancreas only1.11–1.99% of the weighted CE denominator across training cases, versus lesion3.31–54.92%. These shares are not measured gradients. Together with the early class failure, they make loss balance/class competition a strong hypothesis, not proof of the cause. Both foreground classes are present in the correct training targets; no data filtering or relabeling is warranted from this model outcome.

Mean objective over each complete epoch falls1.9767→1.7202→1.6702→1.6633→1.6645→1.6128→1.5809→1.5280. A falling total loss does not establish useful per-class contours. All seven technical native sheets were inspected: cyan lesion predictions extend far beyond magenta references and include much of the green pancreas; no yellow pancreas prediction. Cached-ROI reconstruction and all source identities remained fixed. This is technical review, not clinical contour certification.

## Resources, protection and recovery

|Job|Worker / supervised duration|Peak CPU RSS|Optimizer / original reads|
|---|---:|---:|---|
|Real producer|367.416 /369.137s|4.755GiB|48real calls;14original targets,0CT|
|Independent cold replay|32.464 /33.981s|4.119GiB|0optimizer calls;0original targets/CT|

Combined supervised time403.118s, **6.72minutes**, below30minutes and both20/5minute stage caps. Sampled producer MPS driver peaks4.879GiB, below12GiB. Cold final driver allocation1.424GiB is a final observation, not a continuous peak claim. Power/free-space/output checks passed. No producer, recovery or review attempt failed in D-328.

Four complete checkpoints, seven native prediction/export pairs, selected seven-image recovery bundle, probability/step7 probe bundle and request/journal/native numeric summary were protected:14artifacts. All were independently restored with primary Python reads blocked. Four checkpoint probabilities and all seven terminal native predictions reproduced exactly. Cold replay made no real49th update and no original-target reread. The guard is cooperative descriptor-aware Python denial, not an OS unmount/security sandbox.

Independent audit verified387physical files and29producer/recovery job files with exact primary/keeper/restore payload, complete/event/catalog provenance and semantics. Required payload583,004,143B; three-copy physical total1,749,258,299B. Largest artifact174,159,090B below192MiB. Primary new-area occupancy583,047,635B and independent whole-root13,911,176,703B remain below frozen2,147,483,648B/14,892,449,687B. No old evidence deletion or quota reset.

D-327 labels in the unchanged executor/capability records identify the preparation contract. D-328's separately pinned user approval in the consumed launch record is the actual real-update authority. Original arrays/views and this local review are derived scratch; required numerical/lineage/checkpoint/prediction evidence has independent keepers. The review contains43members/658,643B including producing/helper snapshots, approval/preflight, complete results/recovery, all audits and the next proposal.

|Record|SHA-256|
|---|---|
|Exact consumed request|`eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9`|
|Producer receipt|`23cf88bd94122a3fe120eedaf8318aa48967bfd00cb1491f0cbf57c531866926`|
|Recovery receipt|`744cf4cc82e30479aca7b842a6ccf991871c14ad5ee5ec1fd056298d6ed1da92`|
|Independent artifact audit|`51cbfc887825e732495e1941c4ab6aaad22f30a2356b1abfd8be232d4932df80`|
|Before/after audit|`9073e9d1a4aaf002888a670f5c7d7068ec8bd897f12014cf1405841b9f1e09c2`|
|History inspection|`c6dfe8813bc31df339ed889603220778b98cce9ecc9a2d9ce58149211ac9b4d0`|
|Saved-probability inspection|`10ec011eac45334d116addf9b6ab22082a656969f0f61a1a36949b4d90667546`|
|Visual review|`65331d15dcf9bdbc24b87781a9ffd3b11df0be77f8ac185f8cad51c4aeaa66a4`|
|Completed evidence acceptance|`846c4aca0ea70e8132cd0790ca3c4ff21e141079c67d3317393cae008b50f501`|
|Review receipt|`633c7e09d621846349aa6f7afab58713f2d970e3f69a37d0d1ec99afdcc390ab`|

## Recommended next step

[Class-collapse follow-up proposal](CAP-EXP-013-CLASS-COLLAPSE-FOLLOWUP-2026-10-03.md): quantify CE/Dice class gradients on a bounded training-only, zero-update scope; select and qualify one loss-balance candidate; then prepare a fresh same-seed/same-cohort/same-duration real comparison. No analysis/training request is frozen for that work yet. Keep the current primary result and difficult cases. There is no pending run, continuation, automatic extension, threshold change, eligibility promotion or formal model registration.

This remains pre-course engineering with a provided-reference ROI, one positive validation case and no qualified real negatives. No autonomous-cascade, generalization, specificity or clinical claim follows.
