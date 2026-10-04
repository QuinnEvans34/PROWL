# D-332 — lower-rate v5 learning and native recovery pass

**The controlled LR0.001 comparison passes every original synthetic learning gate.** At480 updates, all five pancreas Dice values are1.0; all four positive lesion Dice/recall values are1.0, every component is hit, and the verified negative predicts zero lesion voxels. The actually interrupted/restarted path agrees exactly. Fresh144³ native MPS mechanics and independently protected recovery also pass. No real input or real optimizer call occurred; the current real recipe remains v3.

Authority: Quinton's “Great, continue on with that” dispatching the [optimization packet](SEGMENTER-NORMALIZED-OPTIMIZATION-PACKET-2026-10-03.md), under the [D-332 plan](SEGMENTER-LOWRATE-QUALIFICATION-PLAN-2026-10-03.md). Original cases, targets, criteria and consumed requests remain preserved. Segmenter6/1, all12 candidates/five holds and localizer153/23 are unchanged. CAP-EXP-013 remains complete and consumed, terminal48 primary.

## Controlled learning comparison

One scientific factor changes from D-331: constant invented CPU AdamW LR0.003→0.001. V5 per-case present-class mean CE plus present-foreground Dice, seed42,24³ SegResNet1→3, five intensity-cue fixtures, batch1, permutation, decay1e-5 and480 updates are unchanged. New low-rate task/config/session/checkpoint identities preserve all previous producers and the pinned v5 numerical function. No learned weight import or old request rerun.

|Fixture|Reference / predicted / true-positive lesion voxels|Pancreas Dice|Lesion Dice / recall|Components hit|
|---|---:|---:|---:|---:|
|Sparse|8 / 8 / 8|1.0|1.0 / 1.0|1/1|
|Multiple|16 / 16 / 16|1.0|1.0 / 1.0|2/2|
|Boundary|8 / 8 / 8|1.0|1.0 / 1.0|1/1|
|Outside pancreas|12 / 12 / 12|1.0|1.0 / 1.0|1/1|
|Verified negative|0 / 0 / 0|1.0|Undefined|No reference lesion|

Mean fixed-fixture final/initial loss ratio0.006461 passes0.8; negative FP fraction0 passes0.02. All unchanged pancreas0.8, positive lesion Dice0.65/recall0.8 and component-hit bars pass. Terminal480 remains the comparison point; no intermediate checkpoint was selected. Each fixture receives96 exposures per480-update path.

D-331's retained LR0.003 result failed with lesion Dice0.021–0.047, one missed component and negative FP0.026620. The lower-rate result shows optimization sensitivity in this controlled invented task; it does not establish a suitable real CT LR or generalization. Saved last20 five-update epoch means fall to0.014543–0.033322, terminal0.014543, versus D-3310.757289–1.340302/terminal0.850028. This comparison uses the same objective and saved histories, with zero new model queries for the history review.

The exact attempt02 request runs fresh480 uninterrupted and actualSIGTERM30/fresh450restart: **960 invented qualification optimizer calls**, excluding unit-test calls. Complete model/AdamW/CPU-RNG/progress/history, terminal predictions and verdict match exactly. Independent review recalculates integer metrics and target counts, exposure accounting, all gates and full-state equality without forwards or updates. Terminal CPU weights: `d5151ac1a257339692500ae27eb06b5ec09139426b4de0be4ce0e62091ca9f70`.

|CPU stage|Worker seconds|Supervised seconds|Worker peak RSS|
|---|---:|---:|---:|
|Uninterrupted480|26.329|29.528|802,750,464B (0.748GiB)|
|Planned interruption30|2.311|4.339|Supervised635,781,120B|
|Restored450 + comparison|24.437|27.601|800,997,376B (0.746GiB)|

Total supervision62.786s; sampled maximum803,209,216B, within the original180s/2GiB trajectory and400s combined budgets. Planned SIGTERM exit−15 is required evidence, not an unexpected learning failure.

## Preserved execution fault and correction

The first request was consumed, then sandbox execution denied the supervisor's `/bin/ps` after0.016s. Its child exited−15 before the required worker-start marker/model construction: zero optimizer calls or original reads. It is a retained execution fault, not a failed learning result. No automatic approval-review rejection occurred.

The consumed fault package remains sealed,12 files/100,781B, receipt98ff446e. The first wrapper/session/tests and125 source pins were not changed. A separately versioned attempt02 wrapper/destination/run identity binds this zero-update fault, checks native memory-monitor availability before preparation and consumption, and rejects reuse. Native tool permissions verified the monitor before the fresh request. Scientific settings and budgets did not change. Preflight also corrected an initial ancestry self-import before the first request was frozen; added regressions check the actual predecessor and failed-parent boundary.

## Fresh native mechanics and recovery

Conditional native request uses fresh seed42/144³/v5/MPS/AdamW0.0003/decay1e-5, no fallback and no CPU learned initialization. This is a separate device/geometry mechanics rehearsal; it is not480-update learning at144³ or evidence that0.0003 optimizes real CT successfully.

- Five producer optimizer calls: four committed updates plus one deliberately faulted repeat of step4 from a savedstep3 payload. The fault really changes weights, leaves committedstep3 dirty, and refuses another update, checkpoint and inference. Preserve only clean0/2/4 checkpoints.
- One recovered nextstep3 call in a fresh worker: **six invented native optimizer calls/eight model forwards total**. Primary Python path/descriptor reads are denied before payload access; no OS-unmount/security claim. No extra restore copies are persisted.
- All three eight-member payloads restore. Step2 image-only probability replay difference0; native mask/inverse probabilities/derived-target integer scores reproduce exactly. Next loss difference0, next-weight maximum difference1.0332e-8 (bar1e-6), sampler/member exact.
- Known invented native grid512×402×197,40,547,328 voxels, exports uint8 mask. Scoring reference is the pinned inverse of an invented tensor target, not an original annotation or a separate geometry oracle. Step2 lesion prediction is empty against4,140 derived reference voxels, and pancreas Dice0.540608; these outcomes are preserved. They are not a native learning gate or real performance claim.

|Native stage|Worker seconds|Peak RSS|Maximum sampled driver|
|---|---:|---:|---:|
|Producer + independent copy|29.613|3,025,485,824B (2.818GiB)|5,128,585,216B (4.776GiB)|
|Fresh-process recovery|7.608|2,832,285,696B (2.638GiB)|5,195,694,080B (4.839GiB)|

Combined supervision47.285s, within600s/12GiB RSS/driver. AC power and100GiB free-space floors pass. Independently protected native package has32 files/227,218,858B; every primary/backup hash is verified. Independent zero-forward CPU review additionally decodes all three protected checkpoints and recalculates scores (3.726s/0.764GiB, zero MPS sessions/updates/original inputs).

## Tests, versions and preservation

**65 new / 2,743 native tests pass**,94.05s, two existing PyTorch deprecation warnings. CPU initial qualification passes2,717; attempt02 preflight/fault-boundary checks pass2,728; new conditional native tests bring the final count to2,743. Broader checks were repeated only after new wrappers/tests were added. New files: low-rate session, closed CPU wrapper/tests, isolated attempt02 wrapper/tests, conditional native wrapper/tests. All129 source pins (122 prior + seven new) and registry hash remain exact. No accepted producing source or old codec was edited.

Complete CPU/fault snapshot:87 files/189,101,113B, four eight-member checkpoints independently decoded under primary read denial. Native keeper:32 files/227,218,858B, all three payloads cold restored. Final numeric/log/test/control copy:30 files/175,563B, every hash independently verified. Old failed/completed packages and capabilities remain unchanged.

Whole independent root14,289,944,348→14,479,045,461 after CPU, then14,706,264,319 after native, then **14,706,439,882B** after numeric preservation. Fresh CPU256MiB, native320MiB and numeric8MiB allowances are recorded from actual occupancy. The final copy remains below its14,714,652,927B transaction ceiling, native14,814,589,781B and unchanged D-32814,892,449,687B ceiling. No registry-cap increase, cleanup or quota reset. Completed stages' narrower transaction limits stay in their historical records; their requests are not reopened.

|Record|SHA-256|
|---|---|
|Consumed first CPU fault package|`98ff446e5b90784fd7b4b5e00e9bd65f6ddefe02b303f885e822fe392601bc54`|
|Consumed attempt02 CPU request|`7b5e649d23a78e02d400c6ec1101b6b08a8823d0649d4e1408b7b913695d14ec`|
|Passing CPU package|`64b7ae4df8de1201881d73484839e6dad78a8040bd14b1e4609dabbcde0417ec`|
|CPU independent review|`b2c55e83ec74d40dc6ee8e9ea60b2a5141295163b6ce1ce1370ba1d84477981a`|
|CPU/fault snapshot manifest|`03973c581008278b551616c5bd8d39bdbede8464b563da14ec01186beaed08f7`|
|Consumed native exact request|`089f975e1ae1c465857f7f14ac231662eacac2a5ac931486852a27283d669c3b`|
|Passing native job package|`3e13f53adec249ed55a1fe5de7be126ad78e6002536f9ac7f6d9f7d74f26b391`|
|Native independent payload manifest|`3fd1ed4075fa697a4e7d4e190fe37f485efee4a4b3d0847affcf248fa2be8a07`|
|Final native test record|`8f5f1cfbf24e138809641cf12f724fdca3c54b7a5045b87cc8c23ee182e5699f`|
|Native independent numeric review|`a0175ab97cf22af6240050f71af8ba1aa2595ae90e4302de225f781c7532b9a1`|
|Final numeric snapshot manifest|`4158dbeb7c2bb2b350db814539dcf72e6087d150dbd7eec444e5f97e8beba460`|
|Numeric preservation report|`978c772674c0f4bad1ca70147cf541941e8d72c202a0c14233634aae2704d7be`|

All three requests (fault, fresh CPU, native) and their actual worker stages are consumed. No pending run, automatic extension, eligibility/source activation/import/promotion or formal registration. Final results/shared completion files are repository records written after the independent control copy; full scientific payloads, logs and reproduction inputs are independently protected.

## Next bounded work

[Real-comparison implementation packet](SEGMENTER-V5-REAL-COMPARISON-PACKET-2026-10-03.md) prepares a separately versioned fresh6/1/48-update v5 consumer, preserving real LR0.0003 and changing only CE allocation versus retained CAP-EXP-013. It needs full real-task/role/checkpoint/evaluation/recovery qualification, fresh14-target read scope, numeric comparison screens and a new exact request with separate launch approval. No new real consumer/request/launch was produced here.

Only **186,009,805B (177.4MiB)** remain below the retained D-328 ceiling. Another full real run/recovery cannot fit. The next preparation must inventory the exact payload and propose an explicit reviewed stage-specific backup allowance within the unchanged registered20GiB cap, or an additional approved independent destination. Do not silently raise a ceiling, remove failed evidence or reuse a consumed grant. Discuss that capacity change with the concrete new request before external writes/launch.
