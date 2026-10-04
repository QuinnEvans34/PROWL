# D-330 — v4 synthetic qualification fails lesion learning

The isolated `[1,64,256]` candidate passes numerical/transaction checks but **fails the unchanged synthetic lesion learning gate after480updates**. Three positive fixtures predict no lesion; the fourth reaches only0.333recall. All pancreas Dice values exceed0.95. Exact interrupted/restarted optimization reproduces the failure. No MPS stage or real-training request was prepared or launched.

Authority: Quinton's “Great, continue to the next” dispatching the [qualification packet](SEGMENTER-LOSS-REBALANCE-QUALIFICATION-PACKET-2026-10-03.md), bounded by the [D-330 plan](SEGMENTER-BALANCED-QUALIFICATION-PLAN-2026-10-03.md). Keep the original bars, fixtures/counts and difficult cases. Current real recipe remains v3; the candidate is not accepted for real training. CAP-EXP-013 remains completed/consumed, terminal48 primary. All6/1cohorts/12candidates/fiveholds and localizer153/23 are unchanged.

## Learning outcome

Fresh seed42,24³ SegResNet1→3, five invented intensity-class-cue fixtures, constant AdamW0.003/decay1e-5, same permutation and480updates. One path uninterrupted; another actually terminated after30committed updates, restored in a fresh process and completed450more.960qualification optimizer calls total, all synthetic; unit-test calls excluded. No real input, original CT/target reads, weight import or model promotion.

|Fixture|Reference lesion voxels|Predicted /TP lesion voxels|Pancreas Dice|Lesion Dice /recall|Components hit|
|---|---:|---:|---:|---:|---:|
|Sparse|8|0 /0|0.955473|0 /0|0/1|
|Multiple|16|0 /0|0.960974|0 /0|0/2|
|Boundary|8|0 /0|0.968493|0 /0|0/1|
|Outside pancreas|12|5 /4|0.963666|0.470588 /0.333333|1/1|
|Verified negative|0|0 /0|0.960356|Undefined|No reference lesion|

Mean fixed-fixture final/initial loss ratio0.258607 passes the0.8bar. All five pancreas Dice pass0.8 and negative lesion FP fraction0passes0.02. All four positives fail lesion Dice0.65 and recall0.8; sparse/multiple/boundary fail component-hit requirements. Four of five reference lesion components are missed. The overall learning screen fails; neither lower scalar loss nor a mechanics pass waives that result.

The retained D-322 v3 run achieved all four positive lesion Dice/recall1.0 at the same480update/seed/fixture/optimizer settings, with pancreas Dice0.995–1.0. Its consumed request was not rerun and its weights were not imported. This comparison is synthetic training mechanics, not real CT evidence or validation performance. The CPU qualification LR0.003 differs from the later real recipe's0.0003; no real outcome is inferred from this synthetic failure alone.

## Why another fixed weight is questionable

D-329's saved real training counts gave provisional64pancreas weighting a pancreas CE denominator share41.9–56.5%. The same weighting behaves differently on the small positive invented fixtures:

|Fixture|v3 `[1,1,256]` pancreas /lesion share|v4 `[1,64,256]` pancreas /lesion share|
|---|---:|---:|
|Sparse/boundary|17.25% /12.91%|93.03% /1.09%|
|Multiple|15.24% /22.88%|92.00% /2.16%|
|Outside pancreas|16.23% /18.19%|92.54% /1.62%|
|Negative|19.85% /0%|94.07% /0%|

These are exact target-weight denominator shares, not measured gradients or causal proof. They show substantial class-allocation dependence on target volume and motivate a different normalization policy. Keep targets and thresholds unchanged rather than improving results by removing tiny/boundary fixtures or cases. [Next proposal](SEGMENTER-CLASS-NORMALIZED-CE-PROPOSAL-2026-10-03.md) defines per-case means over present true classes, giving each class equal CE allocation, with the original foreground Dice and explicit negative penalty. It is not implemented/accepted/frozen/launched; it requires its own scalar/gradient/learning/recovery qualification.

## Implementation and verification

New files: `src/training/segmenter_balanced_loss_v1.py`, `src/training/segmenter_balanced_session_v1.py`, `scripts/diagnostics/segmenter_balanced_qualification.py`, `tests/test_segmenter_balanced_candidate.py`. The v4 transaction derives from the existing synthetic implementation in a distinct file, with new task/config/session/progress/state identities,96MiB checkpoint-state cap and the separately versioned v4 objective. Accepted v1/v3 source, consumers and checkpoint decoding are unchanged; no monkey-patching. Real-domain/raw optimizer input/weight-import APIs remain closed.

38new/2,638native tests pass,93.01s,two existing PyTorch deprecation warnings. Tests include independent scalar/autograd oracles, present/absent-class batch reductions, legacy codec isolation, exact restart, mutated checkpoint/optimizer/RNG/role refusal, actual post-optimizer dirty failure, request scope/criteria/source tampering, exclusive creation and persisted-byte request hashes.

|CPU stage|Worker seconds|Supervised seconds|Worker RSS|
|---|---:|---:|---:|
|Uninterrupted480|25.370|26.814|722,714,624B (0.673GiB)|
|Planned interruption30|2.255|3.485|Supervised662,388,736B|
|Restored450 +comparison|23.971|25.492|781,615,104B (0.728GiB)|

Combined55.846s; supervised maximum782,008,320B, within2GiB and180s percomplete trajectory. SIGTERM exit−15 is the deliberately planned interruption, not an unexpected job failure. No unexpected runtime/review faults occurred. Initial weights3ee49a53 equal the earlier scratch initialization by deterministic construction, not an import. Terminal weights `c8a4ba7cc9cedb4b3e3b7fe71e518b15297437aa1ad3d8004e04cda5d6bb49ac` match both paths exactly. Independent read-only review reproduces every integer metric/failed criterion, weighted denominator and complete model/optimizer/CPU-RNG/progress equality, with no model forwards or optimizer calls.

## Preserved evidence

The CPU package has59files/188,880,118B, including four complete8-member checkpoint payloads (uninterrupted480, restart0/30, restored480), source snapshots, invocation, consumption, logs and summaries. All are retained; no failed artifact is deleted or rewritten.

Fresh D-330 preservation capability copies the full failed qualification plus numeric review/source/plan records:67files/188,947,673B in registered independent `segmenter-balanced-D330-20261003`. All hashes and four checkpoint semantic decodes verified with cooperative primary Python reads blocked, zero model forwards/optimizer/original reads. This is not an OS sandbox/unmount. Whole-root13,911,987,516→14,100,935,189B; new256MiB scoped allowance stays below the unchanged earlier14,892,449,687B whole-root ceiling. Registry/old capacities remain fixed; no cleanup or quota reset. Documentation/results/next proposal remain repository records; the full failed CPU payload and preservation inputs are independently protected.

|Record under `outputs/prowl/`|SHA-256|
|---|---|
|CPU exact request, consumed|`7ee8240c59c546f1613911b97af3fb89d04eb9a0d52f5ff2b5f589ae3e52e53b`|
|CPU package receipt|`d298c9d325337503e82e267e313fda9291fd3d64b04eb0299c834152bca21986`|
|Native tests|`5f30422941eb5c0f01ffc2bf9406e3d1f0aebcc500267a5ebb635ba337dede9e`|
|Independent numeric/full-state review|`d94295abfa1febad1c14c3c90ce997a374c0d9249061993afa40d07dff023373`|
|New backup capability|`0a3a0eaf701d4ebd5ff74df0ced9e6a6b0b01e187e42c5844f05f779f81a3ddb`|
|Independent snapshot manifest|`a69e1f78dd6b9a9009d9574b04eeef8f607fee0e052fd44b72b120f429f0c6df`|
|Preservation/decode report|`7a783b2675c29be834fd8de1e1f8fd8a78f27379f5f338420413cf9235640022`|

The CPU request and all three stages are consumed. There is no pending MPS/real request, automatic extension, new eligible member or accepted loss change. Next discussion/implementation direction: test the separately specified class-normalized CE candidate with the same original synthetic learning bars before another real comparison.
