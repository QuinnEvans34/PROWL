# Prepared model comparison and PANORAMA evidence handoff

**Status:** Request prepared; explicit additional cross-chat permission requested and pending.
Recipient: *Plan capstone experiment workflow* on Quinns-Laptop. This expands beyond the completed
three-case step6000 request; it is not a retry or checkpoint transfer.

## Request text

Please return already-saved development reports/metadata only for two work items. Do not start
inference/training, interrupt a run, load arrays/weights, transfer checkpoints or change producer code.

**AI-05:** inventory completed native evaluation reports for the current pancreas-assisted run.
Baseline is raw step6000, report SHA c70d3fd952efbbec3dffb1dd7fb6428f243927761c6b21cdd921ec4a22b0398f.
Before looking at quality, designate the highest-step fully completed raw native report from this
same run as the comparison candidate; identify step, variant, source/checkpoint lineage and report
digest. If none exists beyond6000, report that; do not run one or substitute EMA/another architecture.
Return baseline/candidate70 per-case metrics and reconstruction metadata in compact JSON, definitions,
membership/failure accounting and source/policy bindings. Retained counts permit recall, false-positive
volume and per-class volume-error derivation; report missing boundary/coverage measures explicitly.
Mention previously selected historical models as context only unless matched cohort/policy and full
retained metrics establish comparability. No hidden test results or protected arrays.

**W03-01:** provide existing PANORAMA source/label mapping, method/allowed-use policy, declared-import
exclusions, patient/cross-source duplicate and role controls, geometry/content qualification, and
mixed-source smoke evidence. Include producing versions/hashes, coverage/failure denominators and
exact unresolved items. Do not conduct a new voxel audit or smoke run for this request. Local Mac
records already show acquisition/extraction and a4,480-file transfer; acquisition alone is not G2
integration. State explicitly if production adapter, eligibility manifest or smoke evidence is absent.

## Predeclared comparison decision

Compare only common, provenance-compatible development cases, retaining all70 expected outcomes and
any failures. For positive references report mean/median lesion recall and lesion absolute volume
error; for annotation-empty references report false-alarm count and mean/total false-positive volume;
for pancreas report absolute volume error separately. Include size-stratum and fixed-subset cases
29/84/927/139/514/698 without substitution. Derive volume from saved native voxel volume, not sampling
spacing. Dice and any-overlap detection remain contextual metrics, not stand-ins for adequate recall.

A candidate is preferred for a later bounded local comparison only if cohort/policy are comparable,
there are no new missing cases, positive mean lesion recall improves, empty-reference total FP volume
does not increase, and mean absolute lesion/pancreas volume errors do not worsen. Otherwise report
reject or inconclusive with tradeoffs. These are prospective development-selection criteria after
observing the baseline's failures, not a pristine experiment or clinical accuracy threshold.
Missing boundary evidence does not become a pass: a selected candidate still needs native local
outline/coverage and measurement qualification before any UI promotion. No local run is authorized
merely by this request or recommendation; the current guard remains.
