# Mac matched KD comparison and launch checklist

October 23, 2026. The user authorized completing the comparison design, review
checklist and launch-requirement assessment while the teacher pilot runs.
**Design fixed; operational bindings and launch qualification pending. No launch authority.**
This additive Mac design preserves the active Windows experiment and Mac pilot.

## Comparison selected

Run two fresh, sequential **Mac/MPS float32** arms: supervised control, then KD.
The current Windows run is contextual evidence only, never the sole matched control.
One seed/pair measures this experiment, not seed-to-seed reproducibility. Both arms
use `DistillationSession`; weight zero delegates to the ordinary supervised update
without reading teacher targets. Do not continue either arm from the other's weights.
The design files in `configs/experiments/mac-kd-comparison-20261023/` differ only in
`distillation.max_weight` (0 versus 0.1). They are not inputs to an authorized launcher.
Assign distinct output paths and tracking IDs during operational freeze.

| Fixed factor | Both arms |
| --- | --- |
| Student | Existing production three-class SegResNet, one CT input channel |
| Initialization | Fresh SuPreM; SHA256 `2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3` |
| Cohort | Exact transferred 1,333 train / 70 development; no test access |
| Updates | 24,000 per arm, seed42, same case order and per-case focus counters |
| Sampling | Existing varied-focus policy, three focused views to one context view; full reserved coverage bank |
| Geometry | Existing provided-pancreas region, 144-cube windows, physical-detail-windows-1; unchanged margins/inference |
| Augmentation | Existing stateless flips/rotations/intensity policy; exact same per-case/update trace |
| Optimizer/loss | AdamW1e-4, weight decay1e-5; DiceFocal; 500-step warmup and 24k cosine horizon |
| Evaluation | All70 native cases every2,000 updates; no early success declaration |
| Selection | Highest positive-patient macro native Dice among all12 scheduled checks; earliest tie; terminal24k also reported |
| Runtime | Same pinned Python/Torch/MONAI/NumPy, MPS float32, CPU fallback disabled |

KD uses the existing loss: maximum weight0.1, temperature2, 1,000-update ramp;
lesion Bernoulli KL, annotation agreement mask, equal nonempty tissue-stratum
weighting, padding excluded. All manual supervision remains. The teacher is fixed
EMA MedFormer, channel19 sigmoid. Teacher input is full CT; labels never select
teacher tiles. Teacher targets are transformed with the student's spatial trace.
Unknown teacher membership means teacher-assisted/exploratory results throughout.

**Before dispatch:** bind full train/development source identities (only12 pilot
cases are Mac-bound so far), target manifest, SuPreM provenance review, runtime,
source and evaluator hashes. Validate real-data zero-KD equivalence, positive-KD
restore and exact case/view traces on this backend. The current scratch synthetic
restore is useful engineering evidence, not this full-recipe qualification.
Freeze both arms before observing either result. A runtime/recipe change requires
an explicit new comparison version; do not silently rebase the control.

## Review checklist, ready for actual pilot outputs

Reuse `PANTS-DISTILLATION-REVIEW-PROTOCOL-20261023.md`, sections2A–D and its
case-specific emphases. `pilot-review.json` records the same12 cases/order, all
pending. Fill records only after inspecting actual artifacts; preserve reviewed
image/probability hashes and unresolved observations.

- **Geometry:** CT/mask identities, ITK/NIfTI world alignment, three physical
  planes, full native probability support, no gaps/seams/flips or hidden zeros.
  Check region reconstruction and quantify boundary-cell extension and uint16 error.
- **Missed lesions:** recall and missed extent; every26-connected lesion component,
  especially the12-voxel case and multi-component case. Patient-size bins cannot
  substitute for component detection. Record undefined denominators explicitly.
- **False positives:** predicted volume and precision, including the one negative
  pilot case; inspect extra predictions inside/outside pancreas. One negative case
  cannot establish specificity. Derive precision from retained intersection/counts
  only when prediction volume is nonzero.
- **Outline quality:** inspect lesion extremes and each component, not only the
  three representative planes. These PNGs may leave detail unresolved; request
  bounded supplemental views from saved probabilities rather than rerun inference.
- **Teacher usefulness:** q>=0.9 contradictions and q<=0.1 suppressed lesion voxels,
  stratified by tissue and component; eligible KD support after quantization.
  These summaries are not currently emitted by the Mac pilot. They remain required
  supplemental evidence, not a presumed pass or calibrated confidence measure.
- **Resources:** all12 completed, frozen teacher unchanged, worker reaped, measured
  tiles/time/memory/output size. Mac pilot limits are90min,12GiB owned RSS,
  12GiB post-tile MPS driver allocation and2GiB output; the latter allocation check
  is not continuous GPU peak monitoring. Keep Windows limits unchanged.

Separate engineering pass, teacher usefulness and scientific launch approval.
Do not invent a teacher-Dice cutoff or remove an inconvenient case. A missing
mandatory review item stays unresolved. Diagnostic NPZs are **not** admitted
training targets; identity-bound cache conversion/quantization checks remain.

## Launch readiness and storage

Observed during planning: internal free91.07GB; external free2.065TB; internal
backup logical usage21.197GB. Verified local SuPreM bytes match the specified hash.
Independent synthetic checkpoint backup and fresh-process restore passed; original
checkpoint56,497,531 bytes. Scientific checkpoint size remains to be measured.

| Requirement | Decision / current state |
| --- | --- |
| Internal reserve | Approved50GB decimal after projected writes; passes now |
| External reserve | Retain100GiB; passes now |
| New internal backups | <=4GiB total for this Mac preparation/comparison, including existing synthetic backup |
| Total backup store | <=26GiB; current headroom about6.72GB |
| Retention per arm | Initial state + all12 scheduled native-validation checkpoints + latest2 nonscheduled recovery checkpoints, maximum15 unique files |
| Retention for two arms | Budget30 checkpoints at provisional64MiB each =1.875GiB; plus synthetic backup, journals, reports and manifests must stay within4GiB |
| Recovery pruning | Delete only superseded nonscheduled recovery files after a newer independent backup verifies; preserve scheduled/selected/terminal checkpoints and all failure evidence |
| Backup contents | Model, optimizer, RNG/counters/identities plus journals, all native metrics and component sidecars; teacher-target cache remains external and is hash-bound |
| Cache cap | Preserve32GiB combined relevant student/teacher caches; measure Mac inventory before full generation |
| Raw teacher projection | 30,363,754,614 bytes for1,333 targets; not yet a measured compressed requirement |
| Transferred cache usage | Windows22.957GB is provenance, **not a Mac inventory**; its11.402GB remaining budget must not be treated as local free space |
| Scientific wall budget | Design ceiling96h per arm including validation; feasibility unqualified until actual Mac update/native-evaluation timing is measured |
| Failure handling | Stop/preserve on resource or quality failure; no automatic retry/resume or silently shortened horizon |

Checkpoint budget is provisional: use the largest actual full-recipe checkpoint
and measured report/sidecar sizes before approval. If projections exceed limits,
propose a storage/budget change; do not drop scheduled checkpoints to manufacture fit.
Both arms need the same complete24k horizon for the planned verdict. A pilot timing
estimate is not a training ETA, and these selected12 cases are not an unbiased
full-cohort runtime/compression sample.

## Recording and final decisions

Use separate machine-tagged run directories and distinct MLflow run IDs on a
**Mac-local** tracking store; never open Windows' live SQLite file. Record one
shared comparison ID, arm, source/runtime/config/cohort/initialization/teacher and
target hashes, supervised/KD/total loss separately, sampling traces, actual update
and validation time, resource measurements and exclusions (none newly authorized).
Keep engineering/pilot time separate from scientific training hours. Verify stored
metrics after dispatch and FINISHED status plus reaped workers on completion.
No new MLflow RUNNING record is created by this plan.

Keep the existing statistical protocol: paired10,000-draw bootstrap seed20261023,
36 positive/34 negative cases, selected and terminal comparisons. Practical success
requires Dice delta>=.02 with95% lower bound>0 and all existing detection, alarm,
pancreas, negative-case voxel-burden, recall and <1mL component guards. Missing component
sidecars prevent practical acceptance; the component evaluator still needs
qualification. Retain failures before selecting any next intervention.

**Remaining launch blockers:** finish/review real teacher pilot; supplemental
component/probability evidence; full local cohort/cache binding and target
availability; measured storage/runtime; matched actual-recipe MPS qualification;
qualified native component evaluation; exact operational receipts and explicit
scientific launch approval. Design/checklist preparation is complete; training
readiness is not.

## Pilot observation during this planning work

The first case completed; the second (PanTS_00003615) failed reconstruction with
“Native field outside teacher coverage; investigate, do not zero-fill.” Only one
case report exists. No pilot process was present at the subsequent process check.
The supervisor resources/reaping receipt is missing; do not infer a resource pass
or clean supervisor completion. Both geometry and supervision evidence require
investigation before any separately versioned retry. Original artifacts preserved;
external pilot-failure-observation-01.json records the observation, not a replacement
receipt. No inference or retry was dispatched during this planning task.

First-case threshold diagnostics: Dice0.0599, lesion recall0.0309. These are
training-case diagnostics without visual acceptance, and make teacher usefulness
a serious open question. They do not establish a cohort result or justify dropping
that case. Review the actual saved probabilities and figure before choosing a fix.
