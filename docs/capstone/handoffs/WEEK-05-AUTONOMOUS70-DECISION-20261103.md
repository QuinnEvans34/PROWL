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

## Verified dispatch

Laptop reports durable restore→admit→evaluate supervisor started successfully;
2/64required CTs completed and verified, with archive read activity increasing.
Approval/request/handoff receipts match independent backups. Operational code pushed
as e3f17b4 on codex/week05-cuda-readiness; W05-09 updated. Restoration source root
E:/PROWL/sources/pants/week05-autonomous70-20261103-a02. GPU evaluation has not yet
started; it follows successful/reaped restore and exact source/native admission.
The owned handoff continues after the laptop chat turn ends and stops on a failed
gate without retrying. Do not redispatch an existing stage or alter frozen pins.
Mac KD independently advanced to7802 with teacher targets and stored MLflow metrics;
initial checkpoint backup still matches. Mac source/UI work is committed separately.

## Evening: source-unit failure accounting approved

Restoration completed64/64, but source admission stopped before GPU evaluation:
six CTs retain unresolved spatial units. The first failure was6011; the affected
set is6011,5780,1823,2935,6901,6115. Original admission failure and restored source
bytes remain preserved. A fresh read-only laptop check at5:55p.m.MST confirmed
no training/restoration/evaluation worker and idle GPU; only dashboard servers remained.

After being told the recommendation to evaluate valid cases and keep failures
visible, Quinton explicitly instructed: "Great, lets get the other laptop working
then." This authorizes one fresh bounded continuation with all70 dispositions:
six source-unit admission failures, the existing5592resource failure, and up to63
predictions (five verified reused/up to58new). No fabricated Dice, silent exclusion,
unit inference or source-header changes. Report coverage over70 separately from
quality metrics on successfully evaluated cases, with explicit metric denominators.

The laptop chat accepted preparation/dispatch of this revised request. Preserve
the original failed request, frozen producing files, exact model/settings,
exposed-development label and bounded numerical exception. Keep the original
aggregate time/storage accounting and64GiBcombined-backup allowance; do not reset
budgets or weaken AC/storage/memory/exclusive-GPU checks. Reuse restored sources
after hash/header verification. A fresh receipt and actual advancing inference
evidence are required before claiming the new evaluation is running. No training,
automatic retry or MacKD interruption is authorized by this continuation.
