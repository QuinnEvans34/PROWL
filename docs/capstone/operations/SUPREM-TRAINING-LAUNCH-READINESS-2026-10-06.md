# R07 draft — SuPreM48 pilot is not launch-ready

October6,2026. Approved drafting complete; **no experiment request or launch approval exists**.
[Live readiness queue](SUPREM-TRAINING-READINESS-QUEUE-2026-10-06.md);
[value/init slice](SUPREM-VALUE-AND-INITIALIZATION-PACKET-2026-10-06.md);
[session/recovery slices](SUPREM-PRETRAINED-SESSION-PACKET-2026-10-06.md).
Tracking: [W01-15](https://trello.com/c/9hAhaaF1), parent[W01-12](https://trello.com/c/fiOfVdBz).

## Phone handback and next move

**Invented device diagnosis delivered:**36native checks pass; original cuda:0/cuda:3/mps:0 storage
tags coexist with CPU FakeTensor/metastorage and zero post-hash storage reads. Only the source-tag
predicate fails in these fixtures. [Result/P03-I proposal](SUPREM-FAKE-DEVICE-PROBE-RESULTS-2026-10-06.md)
is a plausible explanation, not proof of B02's actual failed conjunct or full compatibility.
Next review: versioned invented reader3/tag policy, then a separate fresh actual scope if qualified.
Five substantive gates remain in the diagnostic phone account; no reliable training ETA.

**Current B02 outcome:** the amended corrected CLI ran once and consumed B02. Actual source
hash/size and archive inventory verified; reader refused non_cpu_or_materialized_storage before
full83model inventory. Five diagnostics35,821B retained; 2.061634s/338,296,832B sampled aggregate
peak, owned worker reaped. [Command review](SUPREM-CHECKPOINT-METADATA-COMMAND-REVIEW-2026-10-06.md)
retains the earlier refusal/tests/amendment; no replay/reset or actual values/model/training.
The invented diagnosis is now complete; next proposed scope is P03-I in its linked result.
R04 remains incomplete. Source scientific acceptance/session/current keeper capacity stay open.

**Completed preparation:** B01 actual preflight refused/retired. Diagnostic19, reader2 105 and
dispatcher2 73native invented checks are delivered; [fresh B02 packet](SUPREM-CHECKPOINT-METADATA-DISPATCH-V2-RESULTS-2026-10-06.md)
was explicitly approved and its current command refusal is recorded above. Independent invented
[values56](SEGMENTER-SOURCE-VALUES-RESULTS-2026-10-06.md) and
[typed fresh-head43](SEGMENTER-PRETRAINED-INITIALIZATION-RESULTS-2026-10-06.md) preparation also
passed. Actual metadata/value/initialization/source acceptance/session/recovery/capacity remain
unverified. Training is still not ready. Earlier preparation account below is historical drafting;
its proposals and scientific gates remain unchanged. Actual source access was B02 hash/metadata
only; no model job ran.

R01 separate boundary has89native invented checks. R02 focused research found a generic list but
not the artifact-bound pretraining/selection crosswalk; source use remains unresolved. Three
integration drafts now specify value transfer, fresh-head/session/recovery and this matched pilot.
Training still needs actual-file metadata/value qualification, accepted source evidence, versioned
session/recovery/resource checks and current storage capacity. No model job is running.

**Historical drafting proposal, superseded by current B02 record:** implement/qualify the four-file R04 request dispatcher in the
[R01 result](SEGMENTER-CHECKPOINT-SOURCE-INSPECTION-RESULTS-2026-10-06.md), then—only under Quinton's
reviewed actual scope—freeze preflight controls and inspect the one named checkpoint once.
It can establish compatibility while publisher/source evidence remains pending. Do not read values
or train after a metadata pass. The [publisher questions](SUPREM-PUBLISHER-EVIDENCE-QUESTIONS-2026-10-06.md)
are ready for Quinton; no outreach has occurred.

## Proposed scientific question and matched baseline

Does replacing fresh-random backbone initialization with this accepted general-pretraining
backbone improve terminal native lesion overlap, while preserving pancreas/lesion coverage and
reducing excess lesion foreground? Initialization is the sole proposed changed factor. This is a
small training-only engineering comparison, not a generalization or clinical-validity study.

| Field | Proposed fixed comparison |
|---|---|
| Baseline | Sealed D-335/CAP-EXP-014 fresh scratch terminal48; no replay or continuation |
| Training | Original six:3,26,2232,2973,5821,6238 in frozen controls/sampler order |
| Report-only | 2514, retained development role; chooses no recipe, checkpoint or threshold |
| Target | Three classes:background,pancreas parenchyma,lesion; union separately reported |
| Geometry | Provided-pancreas-reference ROI/10mm margin/1mm intermediate/144³/zerojitter |
| Architecture | Same SegResNet1→3/init16/group8/down[1,2,2,4]/up[1,1,1]/dropout0 |
| Initialization | Accepted SuPreM backbone81entries; exact fresh seed42 two-entry3-class task head |
| Optimizer | New AdamW0.0003/weightdecay1e-5/constant; batch1; no released optimizer/scheduler/epoch |
| Duration | Fresh48updates;8exposures/member; no sweep/automatic extension or192updates |
| Checkpoints/tensor evaluations | 0/6/24/48, same cadence as baseline; terminal48primary |
| Native scoring | Terminal48 all seven full-native predictions, exact fresh14-target scope; no originalCT |
| Output rules | Same inverse/argmax/raw masks; no selected postprocessing/threshold/bestcheckpoint |
| Recovery | All required artifacts independently decoded, primary denied,7native masks exact;0realupdates/0originalreads |

Baseline numeric control read during drafting:
`outputs/prowl/CAP-EXP-014-BEFORE-AFTER-20261003.json`,43,894B,SHA256
`256e84a302165f044e698cd057b7e8112fe5d857aeb5f1dd4635fac951ba1a11`.
Independent audit57550B,SHA256
`bd5968c8871fff5e0ea81d440d5dca42ea5538a6cd46a3dcce3ebf0169651c13`.
No prediction/reference/weight payload was reopened. Future policy must freeze all native integer
counts/components/affines from complete qualified baseline records, not these rounded summaries.

Training terminal pancreasDice0.15987701499875498/recall0.5680330552117256;
lesionDice0.05514229629361542/recall0.8330629874365885;6/6components hit.
Excess lesion volumes12.78–383.26× remain part of the baseline, not an acceptable contour standard.
2514's weak result remains visible but contributes no selection or stopping threshold.

D-335 matching evidence supports this proposal. It does **not** establish parity after new
session/executor code. Qualify unchanged objective, sampler, input roles, seed/head, forward/export/
scorer semantics and update/recovery state through the new path. Unexplained drift means the
initialization-only comparison is inconclusive. Propose a separately authorized matched fresh
scratch control if needed; consumed D-335 requests are never reused. Budget that possible extra
run before it can become a choice. Duration192 remains its separate accepted scratch planning lane.

## New proposed terminal coverage/foreground policy

These **unapproved** rules are specific to this48-update initialization question. They do not
inherit the duration-policy acceptance or retrospectively change D-335's five historical screens.
Freeze and qualify a separate count-only policy before dispatch.

| Terminal48 check | Proposed rule against D-335 |
|---|---|
| Primary lesion overlap | MacroDice≥0.06514229629361542 (baseline+0.01absolute) |
| Pancreas overlap | MacroDice≥0.15987701499875498; everytrainingcase pancreasTP>0 |
| Macro coverage | Pancreasrecall≥0.5480330552117256; lesionrecall≥0.8130629874365885 (each baseline−0.02) |
| Per-case coverage | Each pancreas/lesion recall≥max(0,thatcasebaseline−0.05) |
| Components | Every native reference component hit; each recall≥max(0,itsbaseline−0.05) |
| Tiny2973 | Componentrecall≥0.95; report its exact124native lesionvoxels/volume/FP |
| Boundary6238 | Its retained component/sourceboundary flag; lesion/componentrecall≥0.930706961683756 |
| Excess lesion foreground | MeanFPmL≤0.90×baseline mean; everycaseFPmL≤its ownbaseline (zero baseline requires zeroFP) |
| Accounting | Exact6training+1report-only results; allcounts/precision/volume ratios/missedcomponents/failures reported |

Rationale: +0.01Dice and10%meanFP improvement ask for observable engineering benefit;2pointmacro/
5pointcase/component recall allowances limit benefit obtained by erasing difficult foreground.
These are proposed tradeoffs, not statistical power or medical acceptance criteria. Quinton can
review them before implementation/freezing; a failed check means failed/inconclusive benefit,
not another automatic run. No verified real negative exists; specificity is not estimable here.

Report macro and pooled separately. FPmL=(predictedlesion−TP)×abs(det(nativeaffine3×3))/1000.
Positive cases with zero predicted lesion reportDice/recall/precision0; zero-reference ratios are
null with reasons. Validate confusion matrices/component totals and baseline/policy/result pins.
Missing/failed cases remain in the requested-case ledger and prevent a complete verdict; never
remove them from denominators or replace them with an easier case.

At0/6/24, tensor diagnostics are recorded with the same cadence; they are not native truth or an
early bestselector. This draft proposes **no interim original-target reads**. Numerical/lineage/
resource/dirty-update guards stop immediately. Terminal native benefit bars apply at48; do not
apply them to earlier random-head checkpoints. Additional scientific early-stop screens would
need their own predeclared native reads, counts, policy and approval before launch.

## Proposed run resource/storage envelope and unresolved capacity

Propose the original30min whole/20minproducer/5mincold limits, nativeMPS without fallback,
12GiB processRSS and12GiB driver stops,50ms sampling,ACpower and100GiB available primary/backup
free-space floors. All are future maxima; no pretrained runtime has been measured. Rehearse the
full new transaction/keeper/resource path on invented native-sized inputs before asserting fit.
Current host/volume/runtime pins, free-space floors and ownership observations are pending.

Fixed whole-backup ceiling **18,318,645,873B**; registered20GiB is not permission to exceed it.
Historical post-preservation root17,341,924,636B,remaining976,721,237B,from
`CAP-EXP-014-CONTROL-PRESERVATION-20261003.json`,SHA256
`8bf3fb2563f62a6e526269ddc98779e156f479bcc70937a017e97c5432162071`.
These are historical numbers; no current external-root inventory was performed in this draft.

| Budget item | Historical reference / required next measurement |
|---|---|
| Primary required14artifacts | D-335 onecopy583,041,786B; new lineage/evidence payload ceiling pending |
| Independent keeper | At least all new requiredmembers/receipts; reference583,041,786B; exact pending |
| Full cold restore | Reference another583,041,786B; exact destination/domain/ceiling pending |
| Source/code/environment snapshots | Candidate/source reports and pinned producing-code controls; exact members/bytes pending; no unnecessary raw source-weight copy |
| Qualifications and bridge | CPU/native/full/inference packages cumulatively retained; exact writes pending |
| Scratch/staging/journal/reviews | Separate per-domain allocations including partial transaction members; exact pending |
| Failure reserve | Bound a retained interrupted checkpoint, journal and partialpublication; exact pending |
| Optional matched scratch control | Separate full budget/approval if mechanical parity unavailable; absent now |

Two full independent copies at the historical payload size cost1,166,083,572B, exceeding the
historical remainder by189,362,335B before new qualification/snapshot/failure reserves. Free disk
space is different from this retained-evidence ceiling. This is a **planning capacity conflict**,
not a current measured preflight. Do not delete evidence, raise the fixed cap, omit recovery or
claim the new run fits. Review a separately authorized independent destination or a newly qualified
explicit cold-read protocol if current inventory cannot support full copies. No storage change is
made or selected by this draft. Imaging and retrieval owners must coordinate actual resource use.

## Readiness ledger — measured facts remain null where absent

| Required condition | Current status |
|---|---|
| R01 invented boundary/tuple qualification | Pass89;7.364385s;757,940,224B aggregate sampled peak |
| Actual R04 identity/container/signature/volume report | descriptor/APFS/source SHA/size/archive passed; amended B02 consumed/refused at device/storage guard; full83model/auxiliary inventory null; gate incomplete |
| Artifact-specific rights and protectedpretraining/selection separation accepted | null;R02unresolved;publisherquestions prepared |
| Actual all83finite/strict81backbone/exactfreshhead/target hash | null;invented V01-I56/V02-I43 delivered; actual boundary/R05request absent |
| New session/optimizer/sampler/RNG/dirty transaction | null;S01–S04drafts only |
| CPUlearning/interruption/independentrestore/nextupdate | null;separate qualification requests pending |
| Native144³/completeexecutor/keeper/resource rehearsal | null;notdispatched |
| Actual-source/cache bridge and requiredinference | null;freshactualscopes pending |
| Matched48policy/parity/countcoverage | draft;rules unapproved and policy unimplemented |
| Current code/runtime/source/cache/14targets identity | null;preflight/scope pending;historical pins remain sealed |
| Primary/keeper/restore/currentoccupancy/reserves fit | null;historical capacity conflict above |
| Exact runID/requestSHA/launchcommand/approval/consumption | null;no training request or approved launch |

An eventual closed run request must bind task/domain/identity, all controls and acceptance/source/
initialization/head pins, exact48cadence/membership, exactcache/14targets/scoring policy, resources,
primary/independent/restore volume capabilities and ceilings, failure reserve, recovery policy,
mandatory readiness results, current producingcode/runtime pins and a fresh one-use approval.
Missing fields cannot be filled with optimistic booleans. It is not launch-ready until every row
has checked evidence and Quinton approves that exact command/request.

Preserved text pins reviewed while drafting: v5sessiond6f9059c;normalizedloss0a682a03;
v5executor007e7119;nativescorercd852f3e;v5keeper60704520;v5evidence89b71d5d;
SUP-01source3c206573. Full hashes remain in the pre-code preservation ledger and delivery records.
No source/producer/test/lock change beyond R01, new consumer, actual checkpoint/array read,
forward/update, external writer, experiment dispatch, Git publication or human-hour estimate.

## Delivery checks

Three drafting files reviewed against retained source/control text;58local links resolve across
the batch;new-file whitespace/newlines and scopeddiffcheck pass. All265prior imaging/source/test/
lock pins and historical notebook tail remain exact. W01-15Done/complete/description readback
verified;W01-12To-Do/incomplete withR00–R03complete andR04–R08incomplete. Board42cards preserved;
no weekly archive close or hours estimate. Long parentdescription connector refusals were corrected
within its2,048char limit,then exactreadback confirmed. No active owned qualification worker.
