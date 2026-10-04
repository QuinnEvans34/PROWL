# D-324 — real-input scratch segmenter inference qualified

All seven accepted cache images completed fresh step0 three-class MPS inference and original-grid exports. Weights are unchanged. All seven sheets were reviewed, and every required checkpoint/probe/control/native-mask member is independently protected. Strengthened fresh-process recovery reproduces probabilities and the native probe mask exactly while denying primary paths and directory-relative opens. **2,287 native tests pass**,72new,two existing PyTorch warnings,73.53s.

Authority: Quinton's “Great, continue on.” after D-323, [prospective plan](SEGMENTER-INFERENCE-QUALIFICATION-PLAN-2026-10-02.md), D-324 in DECISIONS. Exact train3/26/2232/2973/5821/6238,validation2514;all12/fiveholds, protected original roles and old153/23localizer unchanged. D-319–323 producers/registry remain immutable. No original CT/target arrays, optimizer updates, weight imports, eligibility changes or source activation.

## New inference-only contract

`src/training/segmenter_inference_v1.py` adds task `pancreas_lesion_segmenter_step0_inference_v1`, independently reconstructed scratch seed42 SegResNet1→3/16filters/GroupNorm8/down[1,2,2,4]/up[1,1,1],float32,144³. No optimizer/sampler or import API. The codec checks exact task/config/cases/context/signature and scratch weight hash; synthetic trained/localizer/imported/mutated state cannot become this task. The initialization/final hash is `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`.

Model forward consumes only image-only cache access with explicit role and per-case image/transform hashes. Target-bearing, held, wrong-role, changed image/geometry, wrong head and nonfinite probabilities are refused. Whole-cache validation checks stored targets, but no target reaches forward. Fresh registered cohort/purpose ancestry is replayed before the cache resolves. Cache completion90b8cc94/bindingcdd7c707 and accepted D-321 geometry remain exact.

Continuous three-channel probability inverse precedes original-grid argmax. Every uint8 NPY export is paired with exact source shape/affine, full protected transform, image/probability/mask hashes and class counts. Outside ROI is background. Reference-oriented foreground/component limits do not exclude dense/empty/wrong/fragmented prediction failures. NPY allocation headers, dtype/shape/order/exact byte length are checked before loading.

Tests cover role/target/head/geometry/weight drift, optimizer/import closure, required-member loss, unsafe arrays, source affine/count/outside-ROI faults, analytically counted native empty/dense outcomes, completion-last failure, scoped capability refusal and recovery access paths. Native synthetic profiling covers largest40,547,328sourcevoxels plus dense/wrong/sparse/fragmented output cases. Earlier full runs2273/2285 remain recorded; final2287 includes pipe and closed-descriptor regressions.

## Exact execution and resources

|Stage|Worker seconds|Peak worker RSS|Outcome|
|---|---:|---:|---|
|Synthetic144³MPS/maximum native export/keeper|10.937|3.169GiB|6members/107,172,246B; all failure patterns retained|
|Seven real cache images/registered ancestry/native exports/keeper|177.563|5.312GiB|12members/202,895,580B; zero updates|
|Initial independent real recovery|5.752|2.057GiB|All12 restored,probe0/nativeexact; initial path guard limited|
|Stronger synthetic independent recovery|4.288|2.980GiB|All6 restored; absolute/component/relative probes denied|
|Stronger real cold independent-copy replay|3.463|1.877GiB|All12 checked against backup; probe0/nativeexact; no registered-storage writes|

Sampled post-operation driver maximum1.400GiB; this is sampled telemetry, not a claim of continuous driver peak. Per-process MPS allocation ceiling and worker checks remain12GiB; supervisor covers wall time/RSS,AC and disk reserve. Serial batch1, fallback0,exclusive MPS lock,1200s per producer/recovery,12GiB RSS/driver,100GiBfree,1GiBevidence. Both inference requests are consumed; no repeat or automatic extension.

|Case|Role|Native background|Native class1|Native class2|
|---|---|---:|---:|---:|
|3|Train|6,758,100|138,796|13,304|
|26|Train|14,600,581|381,698|30,585|
|2232|Train|14,523,787|284,741|38,832|
|2973|Train|10,972,976|243,342|27,202|
|5821|Train|37,955,231|291,973|38,724|
|6238|Train|38,723,988|1,680,465|142,875|
|2514|Validation|9,139,165|227,599|30,924|

Raw native masks136,244,888B. All shapes/affines/counts/outside-ROI controls pass direct saved-byte checks. Seven sheets compare cached image/target views with source-grid prediction projections; these are not original-CT prediction overlays or native reference accuracy. Tiny2973 and boundary6238 remain present. Scratch foreground is broad/noisy; retain all failures. No native Dice/recall is reported until original targets are read in the separate scoring transaction. One validation positive/no real negatives remains engineering only.

## Recovery correction, failures and quota

New scoped storage/backup adapters and [capability](SEGMENTER-INFERENCE-STORAGE-CAPABILITY-2026-10-02.json) use distinct segmenter-inference-runs/keepers/restores on unchanged physically independent registered APFS domains. Frozen quotas: primary1,073,741,824B, independent whole-root10,591,937,061B; additional1GiB per domain,512MiB per transaction. Actual primary310,075,422B and independent whole-root10,245,545,117B fit ceilings, including prior controls/failed attempts. Whole input cache/local sheets/sealed review remain derived scratch; all12transaction members, including every native mask and one exact image/probability probe, are keeper-covered.

Initial recovery's Python audit hook checked absolute prefixes but omitted dir_fd context. No primary read was observed; its original denial claim is limited. Supplement `src/operations/segmenter_primary_read_guard_v1.py` checks path components and file/list descriptors, resolves directory-relative os.open with macOS F_GETPATH and denies symlink aliases. It permits only pathless anonymous pipes when F_GETPATH fails; invalid/unknown descriptors fail closed. Fresh workers actively test absolute, component, nofollow directory walk and dir_fd denial. This is a cooperative Python read guard, not an OS unmount or sandbox claim.

First supplemental attempt failed before restore publication: macOS F_GETPATH returns EBADF for valid subprocess pipes. Its log, source snapshots and receiptb82ef16e are retained. The new pipe regression failed before repair, then passed; a system-Python helper lacking numpy stopped before its preservation writes, and the correct project interpreter completed them. Attempt02's stronger synthetic restore passed; its additional real restore was refused before publication by the store's **two-payload retry reserve plus2MiB**, not lack of physical disk space. Retain partial receipte1a6ff1a and the new synthetic restore.

No quota reset, deletion or producer/request edits followed. Attempt03 reads the existing complete independent real restore and backup, validates every member/catalog/completion/event and their exact equality, then decodes scratch state and recomputes the image/probability/native inverse in a fresh MPS process under the stronger guard. All12members/202,895,580B pass,probability delta0/nativeexact; no new registered-storage copy. Original real inference was not repeated. Future budget profiles must include the full keeper/restore inventory and publication retry reserve, not just raw payload bytes.

## Evidence and next

|Record|SHA-256|
|---|---|
|Storage capability|`35ccc397c163b91b5e4f4accedf85653519d53534a996b24b81f3e29c702731f`|
|Synthetic exact request|`98c47c55f5cd1c96c73912d2345ec6d1e21a9a905c54de7f0b346e225d8ac94b`|
|Synthetic producer/initial recovery package|`fe013fff7060da23752912bb7da39587522a09b62a607eb07c463088c9d34bd6`|
|Real exact request|`cfac9e1afd8e4324713557f5e816a62e8d09c477fed756dc4760d42a22850f50`|
|Real producer package|`e1324f5b612d7d2c2366147343cc0d21b15400578abfd668f641c06b42864be5`|
|Real primary completion|`5c3d2f1d06d5e16ad4ff377d3cacda1bb4aeeb06a7bf7d6c58dcd16ec76260f5`|
|Real independent keeper completion|`0984c95074efbe366f35b9cc508baf437418529a42d0a366660964aaa3c1584f`|
|Initial real recovery package|`5a0c6bc8328c0e8ef9564fed273316cb56b72e1a996126c5d248d50cfe0c3f51`|
|Stronger real cold replay package|`1aac45ce1fef0ea1f02d6f9acdbba9e0afb324bbeb35519dc7039eef5f8b20e0`|
|Acceptance|`7cb2ba5da7ce47b1bdc5e681da662cf14567c2d472871bb03e4b3f121dd14e40`|
|Sealed review|`11a11afe66baadbe8df2bce3391cb2d0b236228167183d238771dc615c0dfdae`|

Review `outputs/prowl/SEGMENTER-INFERENCE-REVIEW-20261002`:28covered members/1,407,176B. Independent audit checks89physical inference artifact files,18accepted-cache files,47diagnostic job members,all seven native count/geometry/image oracles, source/registry pins and actual scoped capacity. All failed/partial attempts retained; sealed review is local scratch, not itself independently backed up. New files: inference task/storage/backup/qualification modules, descriptor guard/recovery helper,3test files, capability/plan/results/next packet and review output directories. No unrelated files or Claude retrieval lane changed.

[Next original-native scoring packet](SEGMENTER-NATIVE-REFERENCE-SCORING-PACKET-2026-10-02.md),SHAecae4dea84d6a16c6b937b3ef0d87d6cc267a5d6eca4b568e8c9d582ba4a1861. Scope proposal8b462a81 preserves exactly14target paths/hashes:1,265,220compressed hash/decode bytes each,272,494,704expanded. Fresh14path observations and a separately tested target-only consumer/resource request are still required; no CT or consumed-scope reuse. Then historical checkpoint/import-denial inventory and real optimizer/sampler/evaluation/interruption qualification before freezing a short exact training request. No pending training launch, generalization/cascade/formal-jitter promotion or new eligibility.
