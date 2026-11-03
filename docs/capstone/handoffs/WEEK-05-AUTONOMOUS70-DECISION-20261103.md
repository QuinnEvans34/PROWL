# Larger autonomous baseline decision packet — November3

The user authorized preparation/coordination while Mac KD continues. The laptop
prepared request853faa584b3abc87e5b16b25c186af9cdbd5e1bbe69b08de208d5ecabe083cbc
at E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a01/request.json.
Its source proposal is WEEK-05-AUTONOMOUS70-PROPOSAL-20261103.md on
codex/week05-cuda-readiness (e1a1a72). This proposal is NOT a launch receipt.

## Concrete scope for review

Exactly70 existing development cases, autonomous arm only, fixed localizer and
control20k segmenter/recipe/thresholds. All70 influenced segmenter selection;
2514/5194/7687 also influenced localizer selection. Teacher/SuPreM membership remains
unknown. Report exposed-development baseline, not independent generalization.
Five saved predictions can be reused under exact identity checks. Case5592 exceeds
the frozen16M localizer resampling cap (conservative20,108,950voxels). Retain that
cap and the case as an explicit preflight resource failure in the70-case denominator:
at most69successful cases, five reused/up to64new. No invented Dice for5592.

The original failed cross-device probability comparison remains FAIL/UNQUALIFIED.
Its four-case-only exception cannot silently admit this larger evaluation. Proposed
new exception covers only this fixed autonomous development report, not training,
backend equivalence, protected-test access, tuning or model acceptance.

## Proposed ceilings

- CT restoration: at most7200s,2GiBownedRSS,3GiBrestoredCTs;65missing files total
  2,266,786,215bytes in the conservative inventory (before5592 failure accounting).
- Inference/scoring/backups:42000s aggregate,600sperworker,12GiBownedRSS,
  6GiBGPU,96Msource/regionvoxels,512tiles. Localizer16Mcap retained.
- 32GiBoutputs and32GiBindependentnewbackups;64GiBcombinedbackups replacing40GiB.
  Retained backups currently30,736,550,123bytes; probability upper bound25,537,638,420B
  plus mask upper bound4,256,273,070B. Keep float32 outputs and existing evidence.
- AC,exclusiveCUDA and100GiBfree-space floors onC/E unchanged; recheck at admission.
- No automatic retry/resume; preserve failed/pending cases and original budgets.

Expected phase time2.6–5.1hours plus admission/overhead: restore46–84min,
inference75–155min, scoring28–38min, backups9–28min. These are estimates from the
four-case measurements; hard ceilings are separate from expected duration.

## Preparation before launch

The first proposal refuses unresolved preflight failures. The laptop has been asked
to finish an additive CPU-qualified failure-accounting version and request without
editing the blocked request or its pins. This code preparation is already authorized;
CT restoration and GPU launch await the concrete larger scope/storage decision.
After approval: bounded restore of required files, exact identity/native-header
admission, freeze new receipt, one supervised run. Mac KD remains the sole Mac GPU
owner. No control/KD/teacher weights or scientific training recipe are changed.

## Explicit approval and qualified failure-accounting successor

Quinton approved via the scope question: "Approve the bounded 70-case evaluation
and 64 GiB backup allowance." This includes the fixed cohort/exploratory numerical
exception, five reused/up to64new/5592resource failure, bounded restoration and the
resource ceilings above. It does not approve training, tuning, protected-test reads,
changed models/preprocessing or any relaxed safety floor.

Before this approval, the laptop finished additive CPU qualification: eight tests
passed, including full70denominator, preflight-case inference/scoring rejection and
no fabricated Dice. New prepared request at
E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a02/request.json:
7db98398be4da35bf775976ef81ec73e848e0258e56e760307817a4e5ec48364
(commit75346b1). Original proposal/request retained. Laptop now instructed to record
approval, verify pins/resources/ownership, restore→admit→freeze→evaluate once under
durable bounded supervision. Actual advancement still requires process/journal proof;
this approval entry is not a claim that GPU inference has started.
