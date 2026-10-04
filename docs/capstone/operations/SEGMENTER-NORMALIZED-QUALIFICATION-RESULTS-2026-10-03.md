# D-331 — class-normalized CE passes mechanics, fails synthetic learning

The isolated v5 objective passes numerical, identity and restart checks, but **fails the unchanged learning gate after 480 synthetic updates**. Sparse, boundary and outside-pancreas lesions reach recall 1.0 with very oversized predictions. The multiple-lesion fixture misses a component, and the negative exceeds the false-positive limit. Stop before MPS and real training. The failed outcome and all four checkpoints are independently preserved.

Authority: Quinton's “Great, move onto the next,” following D-330's [class-normalized proposal](SEGMENTER-CLASS-NORMALIZED-CE-PROPOSAL-2026-10-03.md). The [D-331 qualification plan](SEGMENTER-NORMALIZED-QUALIFICATION-PLAN-2026-10-03.md) preserves the original learning bars and makes MPS conditional on a CPU learning pass. Current real recipe remains v3; CAP-EXP-013 remains complete and consumed, with terminal48 primary. Segmenter6/1, all12 candidates/five holds and localizer153/23 remain unchanged.

## Exact candidate and implementation

Loss ID: `per_case_present_class_mean_ce_present_foreground_dice_v5`.

For each case, average voxel CE separately within each present true class0/1/2, average those class means equally, then average cases across the batch. Add the unchanged mean Dice loss over each case's present foreground1/2, epsilon1e-5. Absent true classes do not enter the present-class denominator, but still compete in softmax and receive CE suppression on present classes. All-background Dice is zero. No fixed global class multipliers, target edits, organ clipping or new sampling.

Four new files isolate the objective, synthetic session/task/codec, closed CPU request and tests: `src/training/segmenter_normalized_loss_v1.py`, `src/training/segmenter_normalized_session_v1.py`, `scripts/diagnostics/segmenter_normalized_qualification.py`, `tests/test_segmenter_normalized_candidate.py`. Accepted v3/v4 producers and old checkpoint decoding stay pinned. New task/config/session/progress/state identities refuse wrong-loss/task resume. Real/raw optimizer input and weight-import APIs remain closed.

40 new tests and **2,678 native tests pass**, 100.76s, with two existing PyTorch deprecation warnings. Tests independently check scalar CE and analytical logit gradients, mixed class-presence batches, all-background/only-lesion cases, tiny targets and negative suppression; they also check codec isolation, restart identity, actual dirty updates, request/source/criteria tampering and exclusive persisted-byte requests. Nominal equal class allocation does not mean equal actual scalar loss, gradients or AdamW updates.

## Learning outcome

Fresh seed42, 24³ SegResNet1→3, the same five invented intensity-cue fixtures, constant AdamW LR0.003/decay1e-5 and epoch permutation. One trajectory completes480 uninterrupted; another receives actual SIGTERM after30 committed updates, restores in a fresh process and completes450. **960 qualification optimizer calls**, all invented; unit-test calls excluded. No real inputs, original CT/target opens or imported initialization.

|Fixture|Reference lesion voxels|Predicted / true-positive lesion voxels|Pancreas Dice|Lesion Dice|Lesion recall|Components hit|
|---|---:|---:|---:|---:|---:|---:|
|Sparse|8|373 / 8|0.846402|0.041995|1.000000|1/1|
|Multiple|16|362 / 4|0.846546|0.021164|0.250000|1/2|
|Boundary|8|384 / 8|0.831368|0.040816|1.000000|1/1|
|Outside pancreas|12|496 / 12|0.847255|0.047244|1.000000|1/1|
|Verified negative|0|368 / 0|0.848125|Undefined|Undefined|No reference lesion|

Mean fixed-fixture final/initial loss ratio0.353020 passes0.8. All five pancreas Dice pass0.8. All four positive lesion Dice fail0.65; multiple recall0.25 fails0.8, with one component receiving zero true positives and the other4/8. Negative lesion false-positive fraction368/13,824 = **0.026620**, above0.02. Four of five reference lesion components are hit. Overall learning fails; lower scalar loss or high recall in three fixtures cannot waive Dice, component or negative failures.

The retained v4 outcome learned pancreas well but missed most lesions. V5 instead produces substantial excess lesion foreground. Retained v3 passed the same invented480-update task at LR0.003. Those consumed requests were not rerun and their weights were not imported. These are synthetic qualification observations, not evidence of real CT generalization or a clinical threshold.

## Failure inspection and next hypothesis

A separately frozen single-use CPU inspection evaluates the retained v4/v5 terminal checkpoints on the same five invented fixtures: **ten forwards, zero optimizer calls**, with original/real/validation opens blocked. It reproduces every saved fixed-fixture loss/metric and verifies complete model/optimizer/progress/global CPU-RNG nonmutation. Worker1.155s, peak625,065,984B (0.582GiB), within60s/2GiB/8MiB. No new threshold or selected checkpoint.

|v5 fixture|False lesion voxels on true background|On true pancreas|Total false lesion voxels|
|---|---:|---:|---:|
|Sparse|145|220|365|
|Multiple|146|212|358|
|Boundary|17|359|376|
|Outside pancreas|259|225|484|
|Verified negative|151|217|368|

False positives occur on both background and pancreas. An organ restriction would not resolve the whole problem and would discard the deliberately retained outside-pancreas target. The saved v5 last20 five-update epoch means range0.757289–1.340302; terminal0.850028 versus earlier minimum0.516616. V4's corresponding range is0.488511–0.734899. Epoch order and differing objectives limit cross-loss comparison; fluctuations do not prove a learning-rate cause or justify selecting the minimum-loss checkpoint.

The [next proposed comparison](SEGMENTER-NORMALIZED-OPTIMIZATION-PACKET-2026-10-03.md) changes only the fresh v5 CPU constant LR from0.003 to0.001, keeping480updates, fixtures, seed, sampler, optimizer decay and original bars. This tests optimization sensitivity before another objective change. It is not implemented, frozen or launched; no automatic sweep, extension, softened gate or real request follows. A new synthetic pass would still require native MPS/resource/independent recovery qualification before discussing a separately approved exact real comparison.

## Runtime and exact recovery

|CPU stage|Worker seconds|Supervised seconds|Worker peak RSS|
|---|---:|---:|---:|
|Uninterrupted480|26.058|27.840|801,374,208B (0.746GiB)|
|Planned interruption30|2.297|3.687|Supervised635,944,960B|
|Restored450 + comparison|24.464|26.294|804,913,152B (0.750GiB)|

Total qualification supervision58.084s; maximum sampled RSS805,076,992B, within2GiB and180s percomplete trajectory. Planned SIGTERM exit−15 is the required interruption. No unexpected runtime/review faults occurred. Both paths exactly match model, AdamW state, CPU RNG, progress/history, terminal predictions and learning verdict. Initial weights3ee49a53 match deterministic fresh construction, not an import. Both terminal weight hashes are `dea8dc358d79be52bc48c977b1002d05443865ce9dccdd17bb57ea9a08c2b895`.

Independent numerical/full-state review recalculates the integer Dice/recall formulas, all failed criteria, loss ratio, target counts and present-class allocations; it compares complete restored states without new forwards or updates. Source122 pins (118 prior + four new), registry and previous storage capabilities remain exact.

## Preserved evidence

CPU package59 files/188,884,855B contains four complete eight-member checkpoints (baseline480, restart0/30, restored480), source snapshots, invocation, consumption records, logs and results. Inspection package four files/43,371B is retained separately. Both requests are consumed; no retry or extension.

Fresh D-331 independent folder `segmenter-normalized-D331-20261003` protects **73 files/189,009,159B**, including the complete CPU package, inspection, native test/numeric review records, helpers and planning inputs. Every copied hash and all four checkpoint semantic decodes pass under cooperative primary Python read denial; preservation uses zero extra forwards/updates/original reads. This is an application guard, not an OS sandbox or an unmount. Whole backup root14,100,935,189→14,289,944,348B stays below the fresh14,369,370,645B ceiling and unchanged earlier14,892,449,687B ceiling. Registry/old capacities remain fixed, with no deletion or quota reset. Results and shared completion records are repository files written after preservation; the full failed payload and inspection/reproduction inputs are independently protected.

|Record under `outputs/prowl/`|SHA-256|
|---|---|
|Consumed CPU exact request|`bfd4b3a213c1c827797222bbb4044a01ad8370baf15dd6a0cc74d3dce793737f`|
|CPU package receipt|`5221113806d5e733527a2b7b0cf03d21a40fed0cb3d7617bc7cd10de0ae15574`|
|Native tests|`c5185bd6bc1c7a70000c775df2151411a6f2a2eb9637a18c4a2da5d9ae129c6f`|
|Independent numeric/full-state review|`59dcf67b17a206eb8ee0f7aa4327ac49033b984edc5536cd1744e7b9cee0fb8c`|
|Consumed inspection request|`9e96470477c4f0bc650932b7529f2c7c914eb5b399cf3d48b103982ed013a3bd`|
|Inspection package receipt|`2057c97d769d1585940accbc68a0f07ed98853defe322e825995032176185d40`|
|New backup capability|`9b8906ec3a6759ad3ec4c07137ef633abfc62bdf547269a0935b23a7ad100268`|
|Independent snapshot manifest|`681726f95b06f63153acc5dbd2dd452516fb9ea69cd0536a19fd0849fec9d826`|
|Preservation/decode report|`62d84fa3c65c5431fa48b9911a48c5d1814d7802e45d40cbc05cbba0ec3db91a`|

No MPS stage, real-training request, real update, eligibility change, source activation, import, promotion or formal registration occurred. Preserve original learning criteria and difficult/negative fixtures. Next direction is the bounded optimization comparison, with a new identity and exact request when dispatched.
