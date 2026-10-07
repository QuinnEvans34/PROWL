# Segmenter duration comparison — review draft, October 6

**October6 decision:** Quinton accepted the recommended192-update planning settings and four-file
DUR-01 invented-count implementation: “Yeah, I think that would be fine.” He also requested review
of `docs/experiments.md` and reuse of successful methods/outlined experiments. The3-point macro/
10-point case/component allowances, tiny95%floor,20%Dice/FP targets and60minute/12GiB planning
envelope are accepted for this policy slice. Earlier proposal-state wording is historical. The
envelope still needs measured native/storage qualification; no longer-run executor or launch is
authorized. Historical methods are being reconciled before any further recipe/data changes.

T02 drafting is approved; the numerical choices, new consumer, qualification and real launch are
not approved by that drafting authority. D-335/CAP-EXP-014 remains complete and consumed.

## Question and recommendation

Does additional training improve native pancreas/lesion overlap while retaining coverage and
reducing excess foreground? Recommend one **fresh 192-update** v5 run, compared with retained
terminal48. This gives each of the six training members 32 exposures, versus eight at48, and is
long enough to test the still-improving training trajectory without opening an indefinite run.
Alternative:96 updates/16 exposures is a smaller, cheaper first probe. Do not run both as an
automatic sweep; settle one duration before implementation.

Evidence supports a duration hypothesis, not a conclusion. D-335's eight epoch mean losses fell
2.037188→1.692695 (last/first0.830898), with improving late tensor overlap. Native lesion precision
is still poor and report-only2514 lost lesion coverage. More updates may sharpen foreground,
overfit the six cases or worsen coverage. This remains a provided-region engineering experiment.

Sources: [D-335 result](CAP-EXP-014-RESULTS-2026-10-03.md), retained
`outputs/prowl/CAP-EXP-014-TRAINING-HISTORY-20261003.json` (SHA-256
`04bf025d0f4db3d35e78d09f2bdef01a0044a028b102bcec014aa4cc5672ae0e`), and
`CAP-EXP-014-BEFORE-AFTER-20261003.json` (SHA-256
`256e84a302165f044e698cd057b7e8112fe5d857aeb5f1dd4635fac951ba1a11`). Only these retained
numeric/control records were read for this draft; no model, CT, target or prediction array was opened.

## Fixed versus changed factors

| Factor | Proposed specification |
|---|---|
| Changed scientific factor | Fresh total update budget48→192; terminal192 primary |
| Initialization | Scratch seed42, initial weights `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`; no trained checkpoint import |
| Training / report-only | Exact3,26,2232,2973,5821,6238 /2514; existing protection/qualification/ancestry fixed |
| Objective / optimizer | Existing v5 present-class mean CE + unchanged foreground Dice; AdamW0.0003/decay1e-5, constant schedule, batch1 |
| Geometry | Existing provided-pancreas10mm/1mm→144³, zero jitter; same cache/native transforms |
| Sampler | Existing seeded per-epoch permutation; first48 exposures/order identical under qualified parity, then continue that policy to192 |
| Output decision | Existing three-class native restoration/argmax and raw-mask rules; no selected cleanup/threshold |
| Primary comparison | Terminal192 versus sealed D-335 terminal48; intermediate checkpoints are trajectory/stop evidence |
| Selection prohibition |2514 selects no duration, recipe, checkpoint or acceptance bar; all difficult cases/failures retained |

A fresh run is required; do not append144 updates to CAP-EXP-014's consumed request or load its
terminal weights. Equivalent fresh initialization plus the same first48-update recipe controls
the duration comparison. First48 parity must be qualified before launch with named exact/numeric
tolerances; unexpectedly changed behavior makes the duration-only claim inconclusive.

## Cadence and requested-case accounting

- Durable checkpoints at0/48/96/144/192. Each is complete model/optimizer/RNG/sampler/history/control
  state and independently protected before advancing. Dirty state cannot become a keeper.
- Training tensor diagnostics at those five points. **Native training screens at48/96/144/192**,
  covering all six cases, all native reference components and separate pancreas/lesion/union counts.
  Tensor overlap cannot substitute for native coverage or false-positive screens.
-2514 receives a terminal image-only prediction followed by separately bounded report-only scoring.
  Its result is displayed even if poor; it cannot trigger a recipe/checkpoint choice.
- A screen/resource fault stops before the next optimizer update. Preserve the failed request,
  committed count, last independently durable checkpoint and all failure artifacts. No automatic
  restart, replacement case, later-checkpoint search or duration extension.
- Predeclare six requested train cases and one report-only case. Failed/empty/abstained cases remain
  in that accounting. Emit null metric with failure reason where no valid native output exists;
  never average only successful cases. All required-case completion is itself a pass condition.

Metrics use native TP/reference/predicted voxel counts. Dice=2TP/(reference+predicted),
recall=TP/reference, precision=TP/predicted (zero predicted foreground on a positive case reports0),
FP volume=(predicted−TP)×abs(det(affine3×3))/1000 mL. Macro means use all six training cases;
pooled counts are separate. Components use all retained native references and the established
matching/accounting semantics; one hit is not adequate full coverage. No real negative case exists,
so neither this run nor invented tests can support a real specificity estimate.

## Proposed coverage and foreground rules — not yet accepted

These engineering thresholds are intentionally explicit for Quinton's review. Their rationale is
to test overlap improvement without hiding shrinkage/missed-lesion regressions or larger false
foreground. They are not clinical acceptance criteria. Freeze exact retained baseline values and
this policy before the new run; do not relax them after seeing candidate output.

| Rule | Proposed interim stop at48/96/144/192 | Proposed terminal192 success |
|---|---|---|
| Completion/finite output | Any missing required train case, invalid output or unsafe inverse fails | All6train+1report-only outputs valid; report-only quality remains separate |
| Pancreas TP | Positive TP in every train case | Same |
| Pancreas recall | Macro≥0.5380330552117256 (baseline−0.03); each case≥its baseline−0.10 | Same plus pancreas macro Dice≥0.15987701499875498 |
| Lesion recall | Macro≥0.8030629874365885 (baseline−0.03, also above retained0.8); each case/component≥its baseline−0.10 | Same; every component has positive TP |
| Tiny2973 | Component recall≥0.95 (baseline1.0) | Same; report its tiny volume and FP explicitly |
| Excess lesion foreground | Each case FPmL≤1.25×its D-335 FPmL | Mean FPmL≤0.80×D-335 mean; each case≤1.10×its own baseline |
| Overlap improvement | Report every class/union Dice; coverage/FP stops govern early termination | Lesion macro Dice≥1.20×0.05514229629361542; pancreas macro Dice does not decline |
| Reporting | All per-case precision, predicted/reference volume ratios, component recalls, failure counts, boundary/size strata | Same, plus paired per-case changes and macro/pooled separation |

The proposed20% overlap gain and20% mean-FP reduction are useful engineering-change targets, not
power calculations or calibrated uncertainty bars. The 0.03 macro/0.10 per-case recall allowances
make the coverage tradeoff visible; Quinton can choose stricter no-loss rules before qualification.
Both improvement targets and every coverage rule must pass; a better mean Dice alone is insufficient.
If limits pass but the gain is smaller, the result is inconclusive/insufficient for that target.
Stopping early produces a stopped result, not a successful terminal192 comparison.

Baseline native values are retained per case. Boundary6238 lesion recall0.980706961683756 gives a
proposed0.880706961683756 per-case floor; tiny2973 uses the stricter0.95 override. Case26's already
weak lesion recall0.575096631695196 remains visible, with a proposed0.475096631695196 floor; this
does not describe good coverage. The next varied-data evaluation must improve on this weak pilot.

## Implementation and qualification prerequisites

Read-only source review confirms the current v5 session caps steps at48 and its executor pins
CAP-EXP-014,48 updates and0/6/24/48 cadence. This proposed192/cadence/interim-native-screen task
**cannot be launched by changing a config number**. It needs a separately reviewed, versioned
consumer/request/comparison/target-budget/recovery scope; preserve old v5 producers and receipts.

Before any real launch:

1. Settle duration and numerical stops; define the separate implementation file allowlist.
2. Add invented tests for exposure/cadence, role denial, native-screen accounting, pre-next-update
   stops, resource/dirty faults, consumed-request refusal and same-run recovery. No evaluation-only
   member may optimize. Native preflight/rehearsal is separately scoped before accelerator work.
3. Qualify full native-sized producer, interim screens, independent keeper restoration and next-update
   recovery on invented arrays, with producing code/runtime/current pins. Measure time/storage/memory.
4. Freeze new target/source/cache/model-consumption budgets. Training-native scoring at48/96/144
   needs12 original targets each; terminal192 adds14. That is50 logical target reads across four
   scoring stages, plus any separately justified preparation/qualification reads. Exact compressed/
   expanded byte limits must be calculated from current stage-specific controls, not guessed here.
   Zero original CT arrays for the cached producer; neither prior target grant may be reused.
5. Independently review the exact new request, gates, purpose/role controls and resource/keeper budget.
   Only Quinton's separate exact approval can launch once. No request or permit is created by this draft.

## Resource proposal and current uncertainty

D-335 producer448.744s and cold35.638s; sampled/native RSS about4.8GiB and sampled driver4.776GiB.
Four times the producer duration is about29.9minutes, before new interim-native screens and protection
overhead. This is a rough projection, not a benchmark. Propose **60minutes total,45producer,
10cold recovery,5preflight/control allowance**, with12GiB RSS and12GiB driver hard caps, one MPS
owner, AC power and existing free-space/domain floors. Native rehearsal must show fit; otherwise
review96 updates or a revised budget rather than silently increasing it. Do not interpret the hourly
queue as unattended real-run authorization or change host sleep/power settings here.

Storage reference: retained `CAP-EXP-014-CONTROL-PRESERVATION-20261003.json`, SHA-256
`8bf3fb2563f62a6e526269ddc98779e156f479bcc70937a017e97c5432162071`, records whole backup
17,341,924,636B under fixed18,318,645,873B, leaving976,721,237B **on October3**. This is not a current
mount/free-space audit. The registered cap remains20GiB; the lower approved ceiling stays fixed.

The prior one-copy required payload was583,041,786B for14 artifacts. Additional checkpoints,
interim native outputs, probes/history and protected review evidence change that inventory.
Budget each destination separately: primary, independent keeper, cold restore, recovery scratch,
failure/retry reserve, control/review/log evidence and source/runtime snapshots. Cold restoration
also grows its destination; do not budget only one copy. A new inventoried manifest must show total
occupancy plus proposed writes plus reserve below every domain/whole-root ceiling. Existing failed
evidence cannot be deleted, and ceilings cannot be raised by this draft. If it cannot fit, propose
a separately approved allowance/destination or a smaller scientifically coherent comparison.

## Decisions and exact next step

Review192 versus96, coverage allowances,20% overlap/FP targets and proposed60minute envelope.
The October6 follow-up review recommends retaining192 and the numerical rules above, but Quinton's
request to continue the next step has not settled those choices or authorized a scientific launch.
The first concrete coding scope proposed below is a count-only policy module; the full versioned
consumer and current-storage budget follow under their own concrete scope. Launch comes only after
implementation, native qualification, exact read/resource/keeper
request review and a separate approval. This experiment does not adopt predicted ROIs or expand
cohorts; those are separate changed factors. All D-335 difficult cases/holds and report-only status remain.

## DUR-01 — proposed first implementation slice

**State: approved October6 and delivered;81targeted invented checks pass.** See
[the DUR-01 handback](SEGMENTER-DURATION-POLICY-RESULTS-2026-10-06.md). This separates the comparison
rules from the older sealed producer. The objective is to make the proposed cadence, native-count
arithmetic and stop/result decisions executable on invented records before introducing a longer
training transaction. It is not the longer-run executor and grants no image/model access.

### Exact new-file allowlist and owner

This Codex imaging lane would create only:

1. `src/training/segmenter_duration_policy_v1.py` — standard-library-only policy validation,
   cadence planning and count-based screen assessment. No Torch/MONAI/NumPy, filesystem, network,
   subprocess, model, array loader, optimizer, dispatcher or launch entry point.
2. `tests/test_segmenter_duration_policy_v1.py` — independent invented-count/physical-volume
   oracles and failure/role/cadence tests. No existing local experiment or dataset required.
3. `docs/capstone/imaging/SEGMENTER-DURATION-POLICY-CONTRACT-V1.md` — exact control/input/output
   schemas, provenance obligations, proposed rules, invalid/failure behavior and integration limits.
4. `docs/capstone/operations/SEGMENTER-DURATION-POLICY-RESULTS-2026-10-06.md` — phone-readable
   handback with actual changed-file hashes, targeted results, limitations and next starting point.

All four paths were checked and are currently absent. No old session, executor, scoring, backup,
storage, dispatcher or test file changes are included. The queue, this proposal and its existing
Trello card may receive status/result links; global decisions/checkpoint and retrieval files retain
their existing owners. No dependencies, external directories, request, permit or signature are added.

### Proposed interface and finish behavior

Use three pure operations: validate/build a versioned policy from control records and an independently
supplied baseline digest; return the selected fixed cadence; assess one screen from numeric records.
The contract must define exact fields before implementation. Policy inputs bind the baseline,
ordered training IDs/roles, report-only ID, tiny/boundary case markers, component IDs, selected
terminal step and immutable numerical rules.
192 means checkpoints0/48/96/144/192 and screens48/96/144/192;96 is an alternative chosen before
coding, not an automatic second run or runtime extension. All training members have equal exposure
counts at these epoch-aligned points; the module reports expected counts, not observed optimizer work.

Numeric outcomes contain per-case integer confusion counts, component reference/TP counts and
positive finite native voxel volume in mm³. They also bind policy/baseline, step, case and role.
Recompute class/union counts, Dice, recall, precision and FP mL from the counts; reject supplied
summary values that disagree. Verify component totals against lesion counts. Zero lesion prediction
on a positive reference produces zero Dice/recall/precision; it is not omitted. Reject booleans as
counts, negative/impossible counts, unknown fields, nonfinite quantities, inconsistent component
totals, altered identity/roles, duplicate/unexpected cases and missing required outcomes. Invalid
records return an explicit failed-screen reason; no successful-case-only mean may be substituted.
Unavailable metrics/aggregates remain null with reasons. A zero baseline FP count requires zero
candidate FP under a multiplicative limit; do not invent an epsilon denominator or allowance.

Return all checks, per-case/component metrics, macro and pooled reporting, the requested-case
completion ledger, and a decision: `continue`, `terminal_pass`, `terminal_insufficient` or `stopped`.
Only a complete passing intermediate screen returns `continue`. An interim coverage/FP/validity
failure returns `stopped`; a terminal coverage/completion failure does too. Complete valid terminal
coverage with insufficient Dice/FP improvement returns `terminal_insufficient`. `terminal_pass`
requires every terminal improvement and coverage condition. All outcomes remain engineering
results with promotion and specificity claims disabled.

2514 quality does not enter a training denominator or any acceptance threshold. A valid terminal
report-only output is required for completion, with its metrics reported separately; an invalid or
missing required report cannot become a terminal pass. This module consumes no reference arrays.
Future consumers must prove the numeric records came from the qualified native scorer, and enforce
the returned stop before another optimizer update. Pure policy tests cannot prove either integration
obligation, authentic source identity, resource monitoring or independent recovery.

### Required invented checks and acceptance

- Independent hand-calculated confusion/union/component and anisotropic-volume examples, including
  an invented tiny component and boundary marker, establish arithmetic and reporting.
- Exact threshold and just-below/just-above cases establish each comparison direction, tiny override,
  component/per-case versus macro rules, both improvement targets and baseline-zero FP handling.
- One bad/missing case among otherwise good cases must fail; a good aggregate cannot hide it.
  Report-only quality changes must not alter any training check or denominator.
- Selected cadence/terminal/exposure invariants, policy/baseline digest drift, incorrect stage/role,
  duplicate records and attempted later-checkpoint selection must refuse rather than relax policy.
- Invalid numeric records and failed/empty/abstained outcomes retain an explicit failure ledger;
  immutable caller inputs remain unchanged. A valid low-overlap terminal result is insufficient,
  not an exception or a false success.

Run only `.venv-prowl/bin/python -m pytest -q tests/test_segmenter_duration_policy_v1.py` after the
new slice exists. Add another affected suite only if the implementation imports an existing helper
or a new failure identifies a concrete need. No old successful tests are repeated simply for the
schedule. Report actual counts; do not predeclare them or claim a current full-suite pass.

Finish with source/contract/diff review, targeted evidence and verified Trello readback. Human hours
remain unknown until Quinton supplies them. Stop at this handback: no automatic full consumer,
native-sized rehearsal, real launch or next scientific packet follows from DUR-01 acceptance.

### Choices to settle

Recommendation:192, the proposed3-point macro/10-point per-case or component recall allowances
(tiny2973floor95%), both20% terminal improvement targets and the60minute/12GiB resource proposal.
These allowances are percentage points for recall, relative percentages for Dice/FP. Passing the
20% lesion-Dice target only reaches about0.06617 on this training pilot; useful contours and varied
development evidence are still owed. No fit or generalization is promised by this policy.

Quinton accepted these planning choices and authorized DUR-01, now delivered. His next steering asks
that prior successful methods and outlined experiments inform further development; see the
[October6 living-notebook review](../../experiments.md) before selecting the next preparation scope.
The resource proposal remains conditional on
later measured qualification and fresh capacity evidence; adopting it does not authorize allocation,
source reads, external writes or a run. Preserve the fixed backup ceiling and all historical evidence.
