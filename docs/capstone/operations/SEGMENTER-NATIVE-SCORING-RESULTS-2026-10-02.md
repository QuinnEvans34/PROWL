# D-325 — original-native segmenter baseline accepted

All seven saved D-324 step0 predictions have been scored against the original pancreas and lesion references. The original-native scorer, target-only reader, immutable evidence publication and independent recovery passed. **2,359 native tests pass**, including 72 new checks; two existing PyTorch deprecation warnings remain. This is the before-training baseline for random scratch weights, not evidence of a trained segmenter.

Authority: Quinton's “Great, score them now. Continue on.” and the [prospective scoring plan](SEGMENTER-NATIVE-SCORING-PLAN-2026-10-02.md). Exact six training cases and one development-validation case, all twelve candidates/five holds, original protected ancestry and old localizer 153 members/23 holds remain unchanged. There were fourteen original target reads and no original CT reads, model forwards, optimizer updates, weight imports or global source activation. Accepted D-319–324 producing source and the storage registry remain exact.

## Original-native scores

Truth uses the original binary references with lesion-over-pancreas precedence, including lesion voxels outside the pancreas annotation. Pancreas parenchyma is class 1; the pancreas/lesion union includes classes 1 and 2. Neither mapped tensor targets nor reference round trips replace original truth. All prediction failures and original 26-connected lesion components are retained.

|Role; cases|Parenchyma Dice / recall|Lesion Dice / recall|Union Dice / recall|
|---|---:|---:|---:|
|Training; 6, case macro|0.084136 / 0.510133|0.001779 / 0.012986|0.084955 / 0.515303|
|Training; pooled voxels|0.098326 / 0.602515|0.003585 / 0.024415|0.099866 / 0.617346|
|Development-validation; 1|0.082410 / 0.254381|0.000061 / 0.000532|0.078030 / 0.258889|

Macro averages give each case equal weight; pooled scores derive from summed integer confusion matrices. The one validation case is an engineering check, not a generalization estimate. There are no verified real negatives and no real specificity claim.

|Case|Role|Original lesion voxels|Predicted lesion voxels|True positives|Lesion Dice|Lesion recall|
|---|---|---:|---:|---:|---:|---:|
|3|Train|1,055|13,304|0|0|0|
|26|Train|7,244|30,585|69|0.003648|0.009525|
|2232|Train|3,867|38,832|13|0.000609|0.003362|
|2973|Train|124|27,202|0|0|0|
|5821|Train|3,399|38,724|0|0|0|
|6238|Train|7,412|142,875|482|0.006414|0.065030|
|2514|Development-validation|1,880|30,924|1|0.000061|0.000532|

Each case has one original reference lesion component. Three of six training components have zero overlap: cases 3, 2973 and 5821. The other components' hit flags only mean nonzero voxel overlap; in particular, one hit voxel in validation case 2514 is not meaningful lesion coverage. No component threshold or prediction-density filter removes failures.

The largest training component, boundary case 6238, remains in the denominator; its 1,603 outside-pancreas lesion voxels are retained. The 124-voxel case 2973 remains a missed tiny lesion, not an exclusion. All predicted lesion volumes exceed their references, ranging from approximately 4.2× to 219×. These poor random-weight scores do not justify cohort filtering or a learning-rate change. They establish the baseline against which a controlled learning diagnostic can be compared.

## Qualification, execution and preserved failures

The separate reader accepts only the exact original pancreas/lesion pair after registered purpose/cohort replay. It rejects CT/extra/missing/duplicate files, wrong-role/held inputs, changed descriptors/geometry/hashes/bytes, incorrect task/stage and stale request identity. It reserves the pair's complete read budget before opening a payload, verifies no-follow source observations, full compressed SHA-256, exact gzip decoding/CRC, header/type/geometry/scaling and approved strict binary semantics. Original truth arrays remain disposable scratch.

A largest-grid invented profile used 40,547,328 native voxels, full gzip decoding and four prediction patterns: empty, dense/wrong, sparse and fragmented. All 392 invented reference components were retained. The replacement profile completed in 10.497 seconds with about 0.734 GiB supervisor peak RSS. Fresh fourteen-path stat-only observations were identical to retained evidence; no source metadata refresh was needed.

The first consumed request `9525baef…` stopped before its first original payload open/hash/decode. Saving used an encoder without the canonical newline while the read guard hashed the canonical encoding. The guard refused the different bytes. Its zero first-reservation counters, traceback, complete failed package and seven source/test/capability snapshots are preserved. No scores or scoring artifact were published by that request.

The repaired producer saves the exact canonical bytes used by the read guard and protected request payload. Seven additional regressions verify saved-request identity, unchanged frozen budget, and pre-read refusal for changed hash, stage or CT/update permission. Existing accepted producers were not edited. Native suite: 2,359 passes in 90.63 seconds; focused scoring tests: 72 passes in 0.33 seconds.

Fresh replacement request `e24cef49…` was frozen after the repaired stat/profile/test qualification and consumed once. It completed in **183.935 seconds**, peak CPU RSS **1.951 GiB**. Actual accounting exactly matches the frozen fourteen-target scope:

- Compressed hashing: 1,265,220 bytes.
- Compressed decoding: 1,265,220 bytes.
- Expanded decoding: 272,494,704 bytes.
- All fourteen original file hashes and seven native prediction hashes match their accepted pins.
- No CT arrays, model forwards or optimizer updates.

Limits remained 1,200 seconds, 8 GiB RSS, 32 MiB local evidence and 100 GiB free space. Both source requests are consumed; neither can be rerun. No training request or automatic extension is pending.

## Protection, recovery and independent audit

The five required payload members are `request.json`, `scores.json`, `references.json`, `aggregates.json` and `production.json`: **101,447 bytes**. They contain complete case/component counts, source/hash/header/binary decoding controls, code/runtime/ancestry identity and aggregates. D-324 already independently protects the native predictions. D-325 native truth arrays, review material and source snapshots remain rebuildable local evidence; no independent protection claim is made for those scratch files.

A new scoped scoring capability permits 64 MiB additional bytes per physical domain and 32 MiB per artifact. Absolute ceilings were frozen before the first attempt and preserved for the replacement: 67,108,864 primary scoring-area bytes and 10,312,653,981 whole independent-root bytes. They include retry reserve, keeper/restore copies and preserved failures; D-324's budget was not reset. Audited occupancy is 104,435 primary scoring-area bytes and 10,245,761,979 independent-root bytes, within those ceilings.

Fresh-process recovery from the independent keeper, with the accepted descriptor-aware primary-read guard, restored all five payloads with exact byte and semantic validation. It took **1.140 seconds**, peak RSS **75.45 MiB**, with no original target reads or model work. This is a cooperative Python read guard, not an OS unmount or security sandbox.

The independent audit checked 27 physical artifact/provenance files and 27 current job members. It independently recomputed every per-case count-derived metric, prediction column totals, original target counts and reference accounting; compared all component sizes/bounds/boundary contacts against the earlier original-content evidence; replayed role aggregates, code pins and storage occupancy. An initial exact-float macro-mean comparison differed between NumPy reduction and Python summation by at most 1.39e-17. That review script/failure is retained; the corrected audit allows 1e-15 only for aggregate floating reductions. Integer counts and per-case formulas remain exact. No scoring producer or result changed for that review correction.

## Evidence identities

|Record|SHA-256|
|---|---|
|Replacement source request|`e24cef49a5d0eb57932217fd045a868bbce7c924f8c65b66244418040cf240b4`|
|Fresh stat-only metadata receipt|`e47864af4bcc7a4a286a39015b800ac8c213df086c327f433dcb5ac15c9dfde3`|
|Largest-grid synthetic profile receipt|`8c865fdc623b7706f908b21bc5f80966e48574b63ddb7ff1a14d22ffbaead454`|
|Complete real scoring job receipt|`f23afdbee151364b32f74bacee1a4713abf580aa8fd81491c63a0301a3247c0d`|
|Primary scoring completion|`4d94325150fa1a6229ae38aada4b5b875ac8ab6f30844566ea3444acb0b2bec3`|
|Independent keeper completion|`bb1ae0bf68fd7017b9068cfbe10d6f6fce6fec768e6a99a19c9934650f6e72b7`|
|Independent restore completion|`25c0ef2300ca09127a2da686dba99c163b8e03952f7313800abd38d9f14052ee`|
|Cold recovery job receipt|`a9981acc798a76a70f1a24d4a968f3964afe27a2f6d0e8c628cbade9e00edb24`|
|Baseline acceptance|`f4bfcaf0dd63ff066ce8456d66b978e738e8cca8322a6c74fcce23c89b090db2`|
|Review receipt; 14 members / 98,480 bytes|`945d1e50c1a9cf7a8879947a4b4b13222178e42711862531a5644d8eaa1b6a86`|
|Preserved first failed job receipt|`d0ed2d578063904d693fc09684a567dc86b98c5f24a47fa50eb3c3db754e3596`|
|Preserved first producing-source receipt|`5274f03b6fc25f602548ec3f71030201ecc576a60f98c55d640192e04d1933a7`|

Review: `outputs/prowl/SEGMENTER-NATIVE-SCORE-REVIEW-20261002/`. Current metadata/profile/scoring/recovery packages use the `attempt02-20261002` suffix. Original attempts and their observations remain separately retained. Four new runtime modules, two new test modules, a scoped capability and planning/results documentation were added. No unrelated project configuration or shared retrieval work was changed. No Git commit or push occurred.

## Next implementation boundary

The [real training transaction packet](SEGMENTER-REAL-TRAINING-TRANSACTION-PACKET-2026-10-02.md) defines the remaining bounded work: historical checkpoint/import-denial evidence, a distinct qualified optimizer consumer, deterministic six-member sampler, objective/schedule identity, native before/after scoring, transactional interruption/reload and independently recovered production keepers. Existing cache optimizer access and synthetic external-update interfaces remain closed.

Recommendation: qualify that machinery, then choose and freeze one short complete-epoch scratch learning diagnostic. Retain D-325 as the before baseline only after proving identical fresh initialization and inference policy; later native evaluations require fresh target-only read scopes. Exact rate/duration, total resource and keeper budgets still need measured qualification before an exact launch request. No long-scale training, eligibility change, formal jitter, autonomous cascade or model promotion follows from baseline acceptance.
