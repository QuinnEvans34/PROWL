# D-322 — synthetic three-class learning and independent recovery

The separate segmenter model, loss/input checks, deterministic sampler, checkpoint transaction and independent keeper path are implemented and qualified on invented data. All 2,147 native tests pass (85 new checks; two existing PyTorch warnings, 75.61 s). Full 144³ native MPS forward/backward, source-grid probability restoration and cold recovery pass. No real source arrays or real-data optimizer updates occurred; there is no training request or model promotion.

Authority: Quinton's “Great, continue to the next.” after D-321 and standing autonomy, within the [prospective plan](SEGMENTER-LEARNING-RECOVERY-PLAN-2026-10-01.md) and [Phase C packet](SEGMENTER-LEARNING-RECOVERY-PACKET-2026-10-01.md). Exact 6/1 cohorts, all twelve candidates/five holds, original protected membership, old localizer 153/23 and registry remain unchanged. D-319/D-320/D-321 producing code pins remain exact. D-321 geometry acceptance is context, not real-input permission for the new synthetic task.

## Learning evidence and controlled revisions

Five fixed 24³ invented training fixtures cover eight-voxel sparse, two disconnected components, boundary, outside-pancreas and verified-negative targets. Image intensities directly encode synthetic class cues. These are training-mechanics fixtures, not realistic CT or a real generalization test; invented negatives create no real negative qualifications. An explicitly synthetic evaluator remains optimizer-ineligible.

Every fresh trajectory uses the same scratch SegResNet architecture, seed 42, AdamW (weight decay 1e-5), constant LR 0.003, complete-ROI batch 1 and deterministic five-member epoch permutation. Preserve all failures, configurations and checkpoints. Each duration comparison is a fresh consumed invocation, not an extension of an old one.

|Fresh candidate|CE weights; updates per trajectory|Final/initial fixed-fixture loss|Observed lesion behavior|Original screen|
|---|---|---:|---|---|
|1|[1,1,1]; 120|0.220116|All four positive lesion masks empty despite pancreas Dice 0.996–0.999|Fail|
|2|[1,1,16]; 120|0.246545|All four positive lesion masks empty|Fail|
|3|[1,1,256]; 120|0.318299|Three lesions gain recall 0.875–1.0 but Dice only 0.161–0.193; multiple lesions missed|Fail|
|4|[1,1,256]; 360|0.063393|All components hit; disconnected-lesion Dice 0.64 because of 18 extra voxels|Fail|
|5|[1,1,256]; 480|0.010739|All four positive lesion Dice/recall 1.0; all five components hit; negative lesion FP 0|Pass|

The original bars never changed: loss ratio <0.8; each positive lesion Dice ≥0.65 and recall ≥0.8; each pancreas Dice ≥0.8; every lesion component hit; negative lesion FP fraction ≤0.02. Candidate 4's 0.64 was not rounded up. Every attempt had exact CPU interruption/restart and save/reload prediction equivalence even when its learning screen failed.

Read-only candidate-1 probes show weak lesion separation, not a geometry/threshold explanation. Independent fresh sparse-fixture true-class CE gradient masses (background/pancreas/lesion) are 0.537/0.122/0.000530 unweighted, 0.533/0.121/0.00840 at 16× and 0.468/0.107/0.118 at 256×. This justified a prospectively recorded objective comparison, followed by duration comparisons with the 256× objective fixed. No validation or publisher-test evidence selected weights, duration or thresholds.

Accepted synthetic engineering objective `voxel_ce_lesion256_present_foreground_dice_v3`: standard weighted voxel CE with weights [1,1,256] and denominator equal to total target weight, plus mean Dice loss over each case's present foreground classes, smooth 1e-5. Absent Dice is excluded; CE still penalizes false foreground. Prior v1/v2 objectives remain readable for historical checkpoints. This acceptance establishes mechanics only; real lesion fractions differ and the weighting is not established as an optimal real objective or formal baseline.

Candidate 5 took 55.086 s, 944,603,136 B RSS (0.880 GiB), with two exact 480-update trajectories (960 optimizer calls). Per-fixture pancreas Dice: sparse 0.998536, multiple 0.997980, boundary 1.0, outside-pancreas 0.995424, negative 0.998540. Across five trials there were 2,400 learning optimizer calls, plus two CPU keeper next-step replay calls and five native MPS calls (including one deliberately failed transaction): 2,407 synthetic calls total, excluding unit tests; zero real updates.

## Implementation and failure handling

New production files: `src/training/segmenter_session_v1.py`, `src/operations/segmenter_run_storage_v1.py`, `src/operations/segmenter_backup_v1.py`, `scripts/diagnostics/segmenter_learning_rehearsal.py`; tests: `tests/test_segmenter_session.py` and `tests/test_segmenter_recovery.py`. Old localizer/session/consumer APIs are unchanged.

Architecture: MONAI SegResNet, one input/three output channels, 16 filters, GroupNorm 8, down [1,2,2,4]/up [1,1,1], dropout 0, float32. Image-only prediction consumes no target. Synthetic update accepts no caller-supplied batch; imported weights and arbitrary real updates are refused. Versioned 24³ configuration caps remain 120/360/480; 144³ is capped at four committed synthetic updates. A deterministic scratch initial hash/signature and task-specific identity prevent warm starts and head confusion.

Checkpoint payloads protect eight members: identity, initialization, inputs, source, environment, geometry, progress and model/optimizer/RNG state. Strict decoding checks tensor signature/dtype/finiteness, AdamW policy/steps/moments, scratch identity, sampler/exposure/history/evaluation reductions and best-selection history. Dirty state begins before forward/backward/optimizer and commits only after the owned RNG transaction completes. Failed steps cannot infer, update or publish; reload uses the last complete state. A deliberate failure after the actual fourth MPS optimizer call left step 3 committed and dirty state correctly refused continuation/publication.

Tests include independent CE/gradient oracles, sparse/negative gradients, precedence and component/count metrics, wrong inputs/configurations, deterministic sampling and evaluator exclusion, exact RNG/restart, dirty-step and RNG-commit faults, invalid checkpoint fields/weights/optimizer/history, import denial, altered backup/catalog/member/domain data, storage caps and one-shot stage consumption. Native diagnostic learning uses the actual SegResNet; fast codec unit fixtures also use a small Conv3d model.

## Native MPS and independent recovery

Full 144³ MPS uses fresh synthetic scratch, LR 0.0003 and the v3 objective, fallback disabled. It is a resource/transaction rehearsal with three committed updates, not a full-resolution learning demonstration. An invented 512×402×197 native grid (40,547,328 voxels) tests continuous three-channel inverse mapping and source-grid argmax without any real CT.

|Worker|Seconds|Peak CPU RSS|Peak MPS driver|Outcome|
|---|---:|---:|---:|---|
|Native producer|25.458|2.950 GiB|4.879 GiB|Steps 0/2/3 published and independently backed up; dirty step refused|
|Cold native recovery|9.812|2.772 GiB|4.949 GiB|All three restored with primary reads blocked|
|Current CPU keeper supervisor|6.088|0.974 GiB observed|—|Steps 0/30/480 protected and cold restored|

Native restored probability difference 0; next-update weight difference 1.4901161193847656e-8 (bar 1e-6), next-loss difference 0 (bar 1e-5), exact sampling/exposure and native probability/argmax hashes. CPU keeper replay reproduces step-30's next update exactly and all terminal learning counts. Every current checkpoint's eight payload members restored byte-exactly. Recovery processes block external primary opens/listing; independent physical devices are verified. Backup/restore records additionally protect source completion/events/catalog, eleven members each.

The exact [D-322 capability](SEGMENTER-SYNTHETIC-STORAGE-CAPABILITY-2026-10-01.json), SHA-256 `a274167129974c73f95150b0fab34e80d2bc1b769dc52d03936e14c2a20ea29c`, permits new external `segmenter-runs` and internal `segmenter-keepers`/`segmenter-restores` only, 96 MiB/checkpoint and ≤1 GiB additional per failure domain. Original quota ceilings cover both current CPU and MPS sets. The global registry remains setup-only/source-inactive with hash `46e3bcd5cbcdf3f9cbcb49fbb42383af680419ecc6e7ff74a4a04defa30e7788`. Failed learning checkpoint weights remain preserved local scratch; independent recovery coverage is the six successful-current declared checkpoints, not every historical trial.

## Saved evidence and qualification limits

|Complete local diagnostic package under `outputs/prowl/`|Receipt SHA-256|
|---|---|
|`segmenter-synthetic-b2682686-8585-4105-a65c-ece30d27569e` (CPU)|`71560377e4897ac04ad9a39cc37451561d8d82f3047d529e4efad537d1815b6f`|
|`segmenter-synthetic-ee61bda1-5637-4309-8d2b-4f9feb5318bc` (MPS)|`258457d421cf7e881ca8067f7fa77c294faa9247a7710e7952603c83d5abd1d6`|
|Same MPS name plus `-recovery`|`82d90d31b053e8d7859b6d2a05f0f5c29f50d93feaec3c6ca4ce920266290dba`|
|`SEGMENTER-CPU-KEEPERS-20261001`|`c594fc25e4f1f062569768848f8c27bd965d15226c6f7ca630ed6ce3ea9da374`|

Independent direct audit checks all 30 covered successful diagnostic files, 216 physical primary/backup/restore files, every receipt/member/event hash, all six keeper inventories, physical domains, final metrics from saved integer counts, original criteria, failures, unchanged producing code and roots. It reads no source arrays and imports neither training objective nor checkpoint codec to calculate the final metric/byte checks. The actual cold recovery workers separately establish semantic decode and probe equivalence.

All intermediate native/targeted tests, failed-learning results/logs and source snapshots are retained. A CPU-keeper helper initially failed importing `src` before any consumed request/destination/publication; its original script/log are retained and the corrected helper uses the explicit repository path. The independent verifier initially used the CPU restore field name for the MPS record and stopped with `KeyError`; both old verifier/log and the corrected passing audit are retained. Neither correction changed pinned production code or repeated consumed diagnostics.

Sealed workspace review: `outputs/prowl/SEGMENTER-LEARNING-REVIEW-20261001`, receipt SHA-256 `b85ceed55d28539c1b69923d2631a6612ae4f60bae522cd898004152a1f8d19b`, 63 covered members/494,485 B. Synthetic-mechanics acceptance SHA-256 `8a061fdbb6cf6ba60b26218363d2b81e55aa292448297a10216e04426a4a98e1`; next-packet SHA-256 `f99a668c265bfebdb9a42901e80c37a19216f62cf6d0458943e5a40420c550ee`. All review members and final producing-code/packet pins independently rechecked. No independent keeper copy of the entire review is claimed. Current checkpoint keepers cover their declared immutable payloads.

## Next

[Qualified cache and zero-update MPS packet](SEGMENTER-ZERO-UPDATE-QUALIFICATION-PACKET-2026-10-01.md): new role-safe persisted cache, fresh exact 21-file source scope, all-seven unchanged-weight inference/native exports, separate original target-only scoring scope and real-input checkpoint recovery. D-321's source request remains consumed; this phase did not create real tensors or read permissions.

Before a short real training launch, finish historical checkpoint hash inventory/import-denial audit and qualify a real optimizer consumer/transaction with measured exact budgets. Synthetic learned weights are not real initialization. One positive validation case/no verified real negatives is engineering only. Formal baseline jitter, broader validation/specificity, autonomous cascade and long-scale training remain subsequent work. No pending training request, automatic extension, new eligibility or model promotion.
