# CAP-EXP-013 — exact short segmenter run ready for launch review

**Prepared, not authorized or launched.** D-327 qualifies the executor and prepares this request. Quinton must separately approve this exact run before the dispatcher creates a real update permit. Missing approval has been tested against the actual prepared request: both authorization and dispatch refuse it before consumption. No approval file exists and the request is unconsumed.

Exact request: `outputs/prowl/CAP-EXP-013-PREPARED-20261003/request.json`.

SHA-256: `eec73450333f345f22d327be8aec93ad71d2b8afbffb91335fd1bf228b1b45e9`.

D-327 sealed review: `outputs/prowl/SEGMENTER-SHORT-REVIEW-20261003`, receipt `09d78eccac6f155d8507eaa5ea07bfb14fccbdc42fc3bc3480e06a26eb3eb018`; qualification acceptance `158a5d17813392f0b13f479b061da1bcdb3e28fa7b06eecabeb7d5247cf83e34`. These local release records are derived review evidence, not a claim of an additional independent keeper copy.

## What the run will do

|Item|Frozen choice|
|---|---|
|Question|Does the candidate three-class segmenter begin learning real supervision in a bounded provided-pancreas-ROI diagnostic?|
|Training members|3, 26, 2232, 2973, 5821, 6238; exactly eight exposures each.|
|Evaluation-only member|2514. No optimizer use or checkpoint/rate/threshold selection.|
|Inputs|Accepted D-323 role-safe cache, freshly replayed D-320 purpose/cohort ancestry; pancreas-reference ROI, float32, batch1, full144³, zero jitter. No original CT rereads.|
|Initialization|Fresh seed42, three-class SegResNet. Initial weights SHA `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`. No imported, synthetic-trained, historical or third-party weights.|
|Objective|Pinned v3 weighted CE `[1,1,256]` plus mean present-foreground Dice; candidate from D-322.|
|Optimizer|AdamW, weight decay1e-5, constant learning rate0.0003.|
|Duration|48 committed updates: eight complete six-member epochs, deterministic seeded permutation per epoch.|
|Checkpoint/evaluation cadence|0, 6, 24, 48. Full model/optimizer/RNG/sampler/configuration/history state, plus tensor diagnostics for all seven members. Terminal48 is primary.|
|Native comparison|D-325 original-native before baseline versus all seven terminal native exports. Continuous three-channel inverse, then argmax; background outside the provided ROI. All components, misses and regressions retained.|
|Final original reads|One fresh terminal-stage read of exactly14 original pancreas/lesion targets. No CT, extra cases or intermediate native reference reads.|
|Total envelope|1800s (30minutes) combined supervised producer/recovery time; producer1200s, cold recovery300s. Human review/waiting between jobs is not runtime.|
|Memory/device|12GiB CPU RSS and MPS driver limits; actual MPS, fallback disabled, two threads, power checks and memory-fraction cap. Driver telemetry is sampled at guarded boundaries.|
|Local/free space|64MiB local job output; at least100GiB free, with the registered domains' stricter checks also enforced.|
|Extension/promotion|None. This request cannot rerun from scratch, extend itself, import weights, change membership or promote a model.|

This is pre-course engineering. One positive validation case and no qualified real negatives do not support a stable generalization or specificity claim. Provided-reference ROI performance does not establish autonomous localizer/segmenter cascade performance. Formal post-October5 model registration remains separate.

## Original-target evidence and protection

Stat-only preparation rechecked all14 paths in0.936s. There were no changed metadata fields; original observations and hashes remain intact. Metadata receipt: `bfc4f22d7187bdf4e61b17d23196f617eecba044e4247d597ee389eb248ebd2a`. No original payload was opened during this preparation.

The separately frozen final-stage scope allows exactly1,265,220 compressed bytes for hashing, 1,265,220 compressed bytes for decoding and272,494,704 expanded bytes. Paired budgets are reserved before source opens; no-follow identity, full hash, gzip integrity, header/scaling and strict binary checks remain required. Source counts and failures are recorded. D-325's consumed request is not reused.

Required protected artifacts are four complete checkpoints, seven native prediction/export pairs, an image-only bundle of the seven normalized cached inputs, a checkpoint/probability/step7 probe bundle, and the complete request/journal/native numeric evidence summary: **14 artifacts**. Every required artifact receives an omission-free independent keeper. Original target arrays and rendered views remain rebuildable scratch. The selected image-only recovery bundle is protected so cold replay can work without the primary cache.

New storage scopes provide2GiB additional capacity per domain,192MiB per artifact, and frozen absolute ceilings: primary new run area2,147,483,648B; independent whole-root14,892,449,687B for keeper and restore accounting. Earlier ceilings and failed evidence are unchanged; they do not authorize these writes. The new real areas are still empty. Source/root configuration is not globally activated.

The rehearsal's conservative required payload is730,497,302B, including seven maximum-size native grids; the real seven masks total136,244,888 raw voxels instead of283,831,296. Largest rehearsal artifact174,144,785B, below192MiB. The independent two-copy estimate plus1,000,000B record allowance per copy and350,386,722B publication/retry reserve is1,813,381,326B, below the2GiB addition. Every write still rechecks actual space and quota; this estimate cannot override those checks.

## Rehearsal and launch gates

2,574 native tests pass,119 new focused checks; two existing PyTorch deprecation warnings. The entire invented144³ producer completed48 updates and all final stages in257.567s (259.287s supervised), peak CPU RSS5.495GiB and sampled MPS driver4.879GiB. Cold recovery took50.571s (52.050s supervised), peak RSS4.360GiB; four checkpoint probabilities and all seven native predictions were exact. The one invented next-update difference was1.49×10⁻⁸. Combined supervised time311.337s is about5.19minutes. Adding the prior169.576s real ancestry replay still leaves substantial margin within the producer and total caps; actual guards remain authoritative.

All seven invented native grids were512×402×197, the real cohort's maximum. Independent audit verified387 physical files and29 producer/recovery job files; all copies and semantics matched. Seven technical sheets were reviewed. The tensor class-cue fixtures and independent native reference fixtures intentionally differ: native scores are a mechanics/resource oracle, not a synthetic or real learning-quality claim.

Fresh exact-source readiness SHA: `e423cc91eefcae200e15e5d715720d84ad664829ea7b217dd35d6bc8eaf00793`. The frozen request binds111 producing pins, runtime, both stage capabilities, baseline and metadata/recovery/test receipts. Readiness and conditional storage permission alone cannot authorize optimization.

After explicit user approval of the exact request, record that instruction in a new launch decision and the exact local approval transport. Recheck request/code/runtime/source/storage/power before consuming it once. Then execute producer and independent cold recovery, inspect all seven real terminal views, independently replay the counts/metrics and preserve the result. Any source drift or failed gate stops the launch rather than changing this request.

## Evaluation and interruption policy

Learning screens are frozen in `outputs/prowl/CAP-EXP-013-LEARNING-SCREENS-20261003.json`, SHA `7a60a64643f67d30432df28ab855eaef136f418f277c159f9cea2955acf5ab2a`.

A positive initial training signal means terminal original-native training macro lesion Dice **and** recall both strictly exceed D-325's0.0017785503792387258 and0.012986097499188299. Report every case/component's direction, component hits/misses, parenchyma/lesion/union macro and pooled metrics, and loss/tensor histories. Tiny2973's124 original lesion voxels and boundary6238's outside-pancreas/source-boundary reference remain in every relevant denominator. Report2514 separately against its own before scores. A signal does not authorize extension or model promotion; weak learning remains a retained outcome and triggers an input/gradient/exposure/objective investigation before a named-factor next experiment.

Cancellation, mutation/publication/backup failure or resource violation preserves the dirty-state/failure journal, actual final-reader counters and last verified checkpoint boundary. No automatic restart or continuation is enabled. A separate continuation decision would have to identify committed same-run state and remaining budget; otherwise preserve the interrupted outcome.

Real cold recovery restores all14 required artifacts with the cooperative descriptor-aware Python primary-read guard active, checks exact member bytes/semantics and reproduces all seven terminal predictions. It reads no original targets and performs **zero real optimizer calls**. The invented6→7 recovery probe is qualification evidence; it does not add a real49th update. The guard is not an OS unmount or a security sandbox.
