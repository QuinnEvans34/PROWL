# Mac work status

## November 10 terminal24k audit and tuning preparation

- User requests deep hyperparameter analysis of final24k, not only selected18k.
  [Full report](../evaluation/STUNET-24K-TUNING-ANALYSIS-20261110.md) and
  [bounded strategy](../evaluation/STUNET-TUNING-STRATEGY-20261110.md) delivered.
  All six validations/70cases retained: finalDice.411972 versus selected.430517;
  precision.461849 versus.421671, recall.499250 versus.551734. Small5Dice.111298.
  Per-case errors, specificity denominators and reference-only error budgets
  show a precision/recall tradeoff; no tuned24k score is claimed.
- New count-only checked reader, explicit original-publication adapter, source
  reconciliation and PNG/PDF figures. Peer d5b127d/4d557f7 metadata imported
  byte-for-byte, no merge. Extended native rows reproduce every derived value;
  70identities/210source hashes/native geometry match the qualified parent.
  The original envelope added derived counts; exact core420row equality checked.
- Actual scientific diagnostics:3/10periodic positive patches lose lesions at
  coarsest scale. Training loss declines but later native recall also declines;
  head/body gradients are nonzero in the24sampled diagnostics. These cadence
  samples are not a cohort prevalence estimate or proof of a single cause.
- Neither24k nor18k native masks/probabilities/logits were retained. A measured
  raw/5mm or decision-margin study requires new bounded inference. Mac external
  drive is absent; no arrays, GPU work, MLflow writes or Optuna training here.
  Existing Optuna is4.9.0; historical tuner targets SegResNet, not this STU-Net.
- Lenovo9dd725b verified the separately authorized24k→36k phase running, live
  losses inMLflowdc0b189042704f51af9dbb2deed5f5a6, original24k full-state import
  and522tensor cold replay exact.531pins and current recipe remain untouched;
  first new full validation26k. No competing job or automatic successor.

## November 9 Trello rolled to Week 6

- User explicitly requested Week5 Done only and current Week6 work. Board verified
  12 To Do / 2 In Progress / 1 Done for Week6; Week5's seven completed cards unchanged.
  Renamed/reused old To Do/In Progress list IDs; no archive/deletion or false closure.
- Ten unfinished cards retain IDs/history under W06-03..12; existing W06-01/02
  moved from Backlog. New W06-13 raw/5mm model qualification, W06-14 weekly closeout,
  W06-15 completed reporting/demo preparation. Training card uQpn9fze is now
  W06-11 and remains In Progress until complete validation/backups/tracking/cleanup.
- [Rollover record](../weeks/WEEK-06-TRELLO-ROLLOVER-20261109.md) and adjacent JSON
  retain original full descriptions/deadlines, mappings and readback verification.
  REF-04 now points to Week6 priorities. Dependencies/G3–G7 gaps and personal-hour
  confirmation remain open. No job, source pin, recipe, budget, monitor or schedule changed.

## November 9 degree-chair check-in and Training refresh

- [Talking points](../weeks/DEGREE-CHAIR-CHECKIN-20261109.md) and
  [baseline next-work packet](../operations/AUTONOMOUS-BASELINE-NEXT-WORK-20261109.md)
  prepared. G3/G4, retrieval/answer acceptance, stakeholder feedback and confirmed
  personal hours remain open; the notes do not claim a meeting occurred.
- UI continuation support `a6c9e85`, verified exports/accounting `6cdca20`, cold
  model/service startup repair `7268063`. Peer `4025c4e` source blobs copied exactly;
  no branch merge. See [accounting receipt](../operations/TRAINING-ACCOUNTING-REFRESH-20261109.md).
  Combined 646.1 training-session hours including 177.0 historical estimates;
  teacher targets add 91.0, for 737.1 recorded model-work hours. Neither is human time.
- Current result snapshot at 12:24 p.m. MST: global 22,571, phase 10,571/12,000,
  latest raw 22k Dice .412172, best 18k .430517. Five full 70-case validations;
  final 24k pending. Source age/phase scope and parent deduplication are explicit.
- [Actual demo check](../testing/CHAIR-DEMO-READINESS-20261109.md): live boundary
  answer/citation, native archived CT, 76.36 mL predicted pancreas-mask measurement.
  The source-bound answer still needs scope/clarity review, not an accuracy pass.
  No production review was written; all five original package hashes match.
- 75 UI / 8 accounting / 12 preparation tests pass; production/Sites build passes.
  Demo model, exact owned services and dedicated internal DB stopped after the
  check; GPU lock released. Training page remains open and works from retained
  snapshots without the external drive. Re-prepare live services for the meeting.
- Lenovo's frozen run and monitor unchanged. Peer should inspect these Git commits
  without merging/pulling into its active checkout. Unrelated audit drafts untouched.

## November 8 standing future-model postprocessing rule and CPU findings

- User directs the fixed5mm predicted-pancreas component filter to become the
  default planned postprocessing for future pancreas/lesion models. Root agent
  instructions and shared evaluation/coordination indices now point to
  [the standing policy](../evaluation/SEGMENTATION-POSTPROCESSING-POLICY-V1.md)
  and versioned configuration. Preserve raw outputs/paired scores and qualify
  geometry, class mapping and detection/recall guards per model. Missing
  predicted pancreas keeps raw with an explicit not-applied record.
- Shared future-model entry point:
  `src.inference.standard_segmentation_postprocess_v1.postprocess`;3focused
  tests pass, including the5mm default, raw retention and missing-context path.
  This does not retrofit an active evaluator, training targets or checkpoint
  selection, and is not an automatic scientific/GPU launch.
- Delivered CPU studies/code: `7b011af`, `26bb9d6`, `169428b`, `d715238`,
  `3930284`, `44a0f66`. [Full nine-policy result](../operations/STUNET-POSTPROCESS-RESULTS-20261108.md):
  original12k rawDice.371633→5mm.394938; recall.541016 and35case/41component
  hits unchanged on exposed development; FPvolume−32.55%. All630mask hashes,
  79final backup pairs and108MLflow analysis metrics verified; run
  `e787e84db21d44308385e14f776047fe`FINISHED/excluded from training hours.
  Mac confidence monitor was deleted at user request; no replacement schedule.
- Peer commits`35b9530`/`76c6ebf` imported byte-for-byte. Six exact training-input
  replays expose lesion disappearance at the8³ target in3/4selected positives,
  not full-resolution crop loss. Coarsest-supervision candidate CPU-prepared;
  no scientific training qualification/launch. Normalization did not broadly
  clip annotated lesion tissue in these sampled examples.
- Fresh peer read at2026-11-08 21:53UTC: corrected global14000 validation
  21/70cases,1221/3963tiles, same worker. No full corrected report/newDice yet.
  Current Lenovo worker, frozen pins and hourly monitoring stay unchanged.
- Existing unrelated local drafts under`docs/stunet_audit/`,
  `scripts/stunet_audit/`, `tests/stunet_audit/`, `scripts/audit_stunet_overlap.py`
  and`src/training/stunet_activation_checkpointing_v1.py` remain untouched and
  uncommitted; no claim that those drafts were published.

## November 8 corrected STU-Net continuation RUNNING

- Human authorized correction/qualification/one launch, then explicitly approved
  **88GiB Cbackup allowance**. All other memory/GPU/AC/free-space/cache gates retained.
  [Authorization](../operations/STUNET-CORRECTED-CONTINUATION-AUTHORIZATION-20261108.md).
- Lenovo source`8c9dfbc`/`5295867` fixes seven targets and preserves1326ordinary
  bindings;664positive/669empty. Real seven-plus-two-control loader and actual CUDA
  parent import/five updates/positive+empty native/cold-next-update all PASS.
  Cold comparison522tensors/maxabs0; no model/head reset. Parent12k preserved.
- Failed scientifica01 had zero updates/no new tracking: wrong supervisor Python
  lackedMLflow. Additive`48ea7c5` uses existing tracking environment with unchanged
  qualified model worker and new receipt/root;60s charged,143940s science remain.
  Mac independently passes41CPU tests and reviews the actual source/metadata.
- Peer`6d484c2` launch: artifact`pants_stunet_corrected_continuation_12k_20261108_launch02`,
  ready`d0a291420d0e1ee07e56f1007540797ebb97c9a08ff25cc82111d53f77c4d9f8`,
  MLflow`13c709ae157949988de1d7f8821a03b7` RUNNING. Verified startup51new/global12051,
  50storedlosses exact; firstfive inputs/losses/LRs match qualification. No new Dice
  before full70case global14000 validation; firstnewbackup due12500.
- Owned99079/supervisor48348/workerwrapper52992/actual32244; use peer commandline/
  creation-time evidence, not PID alone. Exactlyone ownedrun. Phone dashboard shows
  truthful phase-local progress, preserves history/hours. ONE quiet hourly heartbeat
  `monitor-corrected-stu-net-continuation` ACTIVE; no retry/resume/successor.
- [Independent review](../operations/STUNET-CONTINUATION-MAC-REVIEW-20261108.md) and
  byte-preserved [launch](../operations/STUNET-CORRECTED-LAUNCH-20261108.md) capture
  proof/limits. All225repository source identities reconciled to Git, including
  six mixed-EOL snapshots from`f467a43`; no live source/normalization/repin changes.
- [Execution card](https://trello.com/c/uQpn9fze) InProgress; provenance/formal
  comparison cards remain open. All old failures, parent/cache/source and local
  uncommitted audit drafts preserved. No extra Mac GPU/model/data-array work.

## November 8 completed STU-Net review and annotation-policy finding

- Completed 12k and all six 70-case validations; best/terminal lesion Dice
  .371633, overlap35/36, empty alarms27/34, component overlap41/45. Peer completion
  attests FINISHED, all12k stored losses,237pins,34independent backups and reaped
  workers. Its consumed hourly monitor was removed; no successor is running.
- Main `2e21f54` imports peer completion/full native/log metadata and adds a
  completion-binding reader: **33 focused tests pass**, actual saved-JSON CLI
  succeeds. Mac checks metadata consistency, not remote checkpoint bytes anew.
  [Full review and proposal](../operations/STUNET-RESULTS-AND-NEXT-STEP-20261108.md).
- Peer `3ceda41` confirms STU-Net used seven original erroneous lesion targets;
  local metadata crosscheck matches original hashes/counts to the already adopted
  Mac errata overlay.62updates/46lesion-containing patches; none in development.
  Input positivity671/662 rather than corrected664/669. This is an annotation-policy
  integration omission; no measured causal explanation for aggregate Dice.
- Recommend correction-first preparation then a separately specified additional
  12k phase from the selected checkpoint, retaining body and heads. Original LR
  reaches zero and sampler stops at12k; need new LR/sampling identities and strict
  ancestry-aware cold-restore qualification. About29.3h/35.2hwithmargin plus setup;
  fresh24k about58.6h/70.3hwithmargin. These are proposals, not approved budgets.
- No data arrays, GPU work, MLflow writes, cache repair, launch, retry or schedule
  was performed. All historical attempts, source caches and existing audit drafts
  stay preserved; annotation correction does not resolve pretraining exposure.

## November 7 STU-Net early errors and proposed follow-up

- Imported peer `0da40f1`'s native metadata/report byte-for-byte. Export SHA256
  `9528af9e5817f74d3a813c096b261d1e80b4ac688773697c272cd4e1f0e971a9`;
  all 70 cases at 2k/4k/6k. Source inspection reconciles six producer pins: four
  exact Git bytes, two exact LF-to-CRLF serialization. Native metrics/input code
  match exact bytes. These are Git/export checks, not live-pin requalification.
- `e4d8f2f`: [interim analysis](../operations/STUNET-INTERIM-ERROR-ANALYSIS-20261107.md),
  19 metadata tests, actual CLI byte-identical replay and unchanged input hashes.
  Derived 6k recall .452044, precision .380762 on 35 defined positives, six complete
  case misses and nine missed reference components. Small-total-lesion five-case
  DICE .047820, versus medium .383014/large .438158. All 70 retained; no new scoring
  from arrays, model calls or independent-patient inference. KD final-arm reference
  mapping still unverified; no cross-model deltas or promotion.
- `a6e7653`: [CAP-EXP-020 proposal](../operations/CAP-EXP-020-PROPOSED-20261107.md)
  and registry, plus a pure NumPy policy/15 synthetic tests. Proposed one shared
  probability reconstruction for raw versus .40/.50/.60, after current training
  closeout. Requires +.02 DICE and case/component/small-recall/overall-recall/
  pancreas/false-alarm guards. A suppression-only policy cannot recover raw misses.
  Proposed four-hour cap and existing safety limits; no executable launch receipt,
  actual native runner, GPU qualification, timer, MLflow RUNNING record or training.
- Inspected producer returns metrics rather than retaining per-case probability
  volumes, so saved-count threshold screening is unavailable. A separate qualified
  inference pass would be required; do not edit the active producer to add saves.
  Estimated four uint8 masks plus independent copies: 15.86 GiB before other data;
  admission/runtime/current combined storage remain pending. Mac stays on CPU work.
- [Trello proposal](https://trello.com/c/36PNBVVj) is in Backlog, not running;
  W06-01 and the STU-Net/provenance card link the new evidence and limitations.
  Current Lenovo launch02 and its hourly monitor remain untouched. Later training
  ideas are deferred until final evidence, not a second queue of long runs.
  Existing audit drafts remain uncommitted. Earlier Week 5 evidence inventory is
  the retained snapshot at `45bb8ea`, not a live checksum of evolving status files.

## November 7 reviewer verification and weekly evidence handoff

- Reviewer repair `92bf1f5`: returned save decisions must match submitted intent;
  duplicate/broken history is refused and conflict recovery retains the draft.
  Fixed the demonstrated Node JSON import/restart defect. Verification: 164 UI
  tests, 38 backend tests, production/Sites builds and actual isolated browser
  save/reopen/revise across API restart. Both receipt chains and all five original
  package files checked; dedicated test services and browser tab cleaned up.
  [Report](../testing/REVIEWER-FLOW-20261107.md). These are engineering records,
  not production decisions, participant feedback or new contour adjudication.
- Technical Week 5 reconciliation `6ac2e70`:
  [closeout](../weeks/WEEK-05-EVIDENCE-CLOSEOUT-20261107.md) with exact report hashes.
  G3/G4/G6/G7, KD-specific spatial explanations, personal active hours and course
  submission remain explicitly open. Week 5 still ends November 8. The preliminary
  aunt/fallback session is November 14; exact time/role/permission unconfirmed.
- Comparison preparation `37dfa9a`:
  [tool and packet](../operations/WEEK-06-COMPARISON-PREPARATION-20261107.md), 15 new
  metadata tests, actual CLI byte-identical reproduction and unchanged source
  hashes. Original completed KD analysis also reproduces exactly. Full KD curve
  and selected/terminal errors are separate from STU-Net's dated aggregate export.
  No ranking/promotion, patient-independent inference or new GPU work. Equal cohort
  counts do not establish exact case/reference alignment. Even a completed dashboard
  does not establish full closeout. Historical failures remain preserved.
- [Week 6 plan](../weeks/WEEK-06-WORK-PLAN.md) is prepared for November 9–15:
  finish available results/closeout, resolve admitted autonomous baseline and freeze
  the formal comparison, measure retrieval/grounded answers, then actual walkthrough.
  This is planning, not a receipt or automatic queue. W05-07/04/08 and W06-01 have
  evidence updates; broad acceptance cards remain open instead of erasing gaps.
- Lenovo remains sole owner of corrected STU-Net launch02 and its existing hourly
  monitor. No live producer/pin changes, merges, new model calls, tracking writes,
  teacher/KD restart or additional monitor. Existing uncommitted audit work remains
  separate and unpublished. Peer can read these commits with `git show`; do not
  merge or pull under its active frozen worker.

## November 7 results UI and walkthrough reschedule

- Quinton postponed the preliminary aunt/fallback showcase to **Saturday,
  November14**, exact time and role still unconfirmed. Plan11 and W05-03 updated;
  W07-02 retains its broader acceptance requirement. No session/feedback invented.
  Planning commit `4dfd1af` records the current work order.
- W05-10 delivered a read-only Training results panel: all completed lesion and
  pancreas DICE points, best/latest scores, validation progress, detection and
  false-alarm denominators, source time/age and explicit exploratory scope.
  Contract/reader `c2a4295`; UI `8876812`. Invalid or unavailable data retains the
  last admitted results; partial validation is never a score and refresh cannot
  make a saved observation look live. See
  [contract and checks](../operations/TRAINING-PROGRESS-UI-20261107.md).
- Peer read: Lenovo `1753ae4` sanitized aggregate export, copied byte-for-byte
  with SHA256 `664535b2116b22bdf49ea85bc92457152dd830305145c398490eced023184163`.
  At its observation time 2026-11-07T18:51:06.339094Z, STU-Net was training at
  6,814/12,000 updates. Completed positive-case lesion DICE2k/4k/6k:
  .144179/.222087/.347182; latest pancreas.744134, detection30/36, empty alarms26/34.
  These are saved development observations with unresolved pretraining exposure,
  not a current worker check, autonomous acceptance or an independent comparison.
- The one corrected Lenovo run and hourly monitor remain under Lenovo ownership;
  receipt `59e8188d60d70840eabb8752f0be5d5c1f818bc51e3cdcf81d16c74c79cf3e68`,
  MLflow `243ccf3f71c34417be60362af35187d1`, 12k/60h unchanged. No trainer/pin
  edits, GPU work, source merge, inference rerun or extra monitor from this task.
- Verification:156tests/13suites pass, production/Sites build pass, actual browser
  chart/table/freshness and manual refresh inspected. No participant feedback or
  mobile browser acceptance claimed. Browser proof remains local. The dev UI is
  served at5180; the result export is not a live remote feed.
- Next: existing reviewer-flow acceptance checklist for November14, Week5 evidence
  and Quinton-confirmed hours closeout, then Week6 model/answer-quality review.
  Previous uncommitted STU-Net audit/helper work remains separate and uncommitted;
  this publication does not claim that audit drafts were reviewed/published.

## November 6 review handoff

- [Alternative transfer candidates and audit scope](../operations/TRANSFER-CANDIDATES-AND-LEAKAGE-AUDIT-20261106.md):
  prioritize TotalSegmentator-pretrained STU-Net-B58.26M for provenance inspection,
  not GPU launch or a leak-free claim. Original5,050CT and newer~50kCT/MR MONAI
  SSL releases distinguished; both still need image-exposure checks. Two-file
  membership reconciliation verifies1,333same train/75registrydev/70KDsubset;
  preserve922/5105/5370/7299/7523outsideKD. This is not a completed1,408patient
  crosswalk/duplicate audit. Official901IDtest is distinct from authors' external
  OOD evaluation service; neither automatically clears Universal exposure.

- [Scientific-use research](../operations/UNIVERSAL-SWIN-SCIENTIFIC-USE-RESEARCH-20261106.md):
  the screen used an already task-trained publisher model; no PROWL fine-tuning.
  City University of Hong Kong/JHU/NVIDIA authorship verified. Journal methods
  clarify3,410developmentCTs=2,100train+1,310validation; checkpoint membership still
  unknown. Loaded code has shared controller, unlike later journal independent
  MLP extension. Retain attributed baseline scope and conditional adaptation,
  not a new PROWL-trained or independently validated model. No GPU job launched.

- Full KD curve/endpoint/error review committed in6947827. Selected gain is
  +.005491 Dice, terminal+.001475; 16positive cases improve/18worsen/2unchanged
  at both endpoints and component coverage declines39/45to37/45. No promotion,
  independent-patient interval or practical acceptance. See
  [full analysis](../operations/KD-DESCRIPTIVE-ANALYSIS-20261106.md).
- [Universal provenance and next-study draft](../operations/UNIVERSAL-SWIN-PROVENANCE-AND-NEXT-STUDY-20261106.md):
  public-source dataset overlap confirmed; exact four-case/checkpoint patient
  membership unresolved. Lenovo completed metadata-only crosswalk review1e6760f:
  eight named case files and70existing request records do not establish original
  source/patient links; allfour remain unknown. Peer report/JSON copied exactly,
  no GPU/data/duplicate-audit expansion. No successor launched. Inference fit does
  not qualify training fit; unit admission remains unresolved for training and
  negative cases. Larger-model score stays a four-positive exploratory result.
- [Retrospective experiment index](../operations/EXPERIMENT-REVIEW-INDEX-20261106.md)
  links original requests and MLflow identities; no statuses rewritten, duplicate
  training run/hours or retrospective preregistration created. New KD reader
  reproduces source summaries and refuses changed input/overwrite. All existing
  producing pins and evidence remain untouched.

The earlier entries below retain their original observation dates and scopes.

- Observed at: 2026-11-06 03:23 UTC (November5 evening locally).
- Owner / branch: Mac chat, `main`.
- Delivered latest engineering: `388524d`/`716d2f8`; KD evidence/permit `93899ef`.
  The enclosing commit publishes the larger-model result review.
- Peer read: Lenovo `f7ece22e948563e7b737d54f5d7985d5f6e89008`, result/closeout,
  readiness/launch records and producing code through5ebc49f. No source merge.

## Delivered Week 5 work

- **Larger-model screen COMPLETE:** [Mac review](../operations/UNIVERSAL-SWIN-MAC-REVIEW-20261105.md),
  four positive cases mean lesionDice0.710754 vs prior autonomous same-four0.459987;
  three improved/one worsened. No fine-tuning, negative specificity, independent
  acceptance or causal architecture claim. Pretraining overlap remains unknown.
  Lenovo checked5442pins/45backup pairs/tenreapedstages/FINISHEDtracking/GPUrelease.
  Mac checked12local source hashes, prior scores, reference counts and arithmetic.
  Private prediction copy pending reconnection after remote became unavailable;
  originals/independent backups and quantitative Git report are preserved.
- **KD COMPLETE:** [closeout](../operations/MAC-KD-COMPLETION-20261105.md), all24k/
  12native70-case validations, selected20k0.389084/terminal24k0.383439. Final
  backups/152pins/all24stored native metrics/processabsence/GPUrelease verified;
  treatment FINISHED. Hourly KD heartbeat PAUSED. Full report2679c09ebefc2361cb81122ead80530c48fcbeb99b333d2e526d1723a2e0033b.
  Descriptive only; selected control0.383593, terminal0.381964; no CI/verdict.
  Lenovo5ebc49freadiness/runner/tests/nativegeometry reviewed without merge;
  one-shot permitb6b76fc7e1667a7b5c3c13e93796e6460105d0f3e8f0023b30e12f8a499f8aba
  binds request4654d46b730abe8c144b1cc57af607d579154b1c96ff707c37861fbce55fadc5.
  This permits bounded qualification/evaluation, not observed GPU success.
- User authorized one larger-model overnight experiment after KD. Official
  [Universal Swin screen](../operations/UNIVERSAL-SWIN-OVERNIGHT-20261105.md):
  downloaded758,907,945B/exactpublisherSHA; strict CPU load170state entries,
  62,595,315parameters, zero forwards/updates. Audit111608eb4d5efa46ca1c3227dd6c3a770a49b0e74e9f7cec4766ab469189a553.
  Code388524d;34CPU audit/permit/KD-closeout tests pass. One-shot permit requires
  verified completeKD, not merely24kupdates. Lenovo preparing four strictly admitted
  positive cases; missing-unit empty/train cases are NOT_ADMITTED, so no training
  or empty-alarm claim. Source/weights remain external/private. TrelloKhp8LCoP.
  No new GPU stage launched; currentKD final validation52/70at24k, MLflowRUNNING.

- November5 CPU follow-up: [KD closeout reporting](../operations/KD-RESULT-CLOSEOUT-20261105.md)
  atfd34932/6aec2c3,66KD/native-reader tests pass. Actual control closeout and all
  12control/10treatment stored native metrics checked read-only. Live treatment
  remains pending22k/24k/final cleanup; no verdict/CI or new tensor restore.
- [Saved autonomous result workflow](../orchestration/BASELINE-REVIEW-WORKFLOW-20261105.md)
  at7bef5e5, timestamp contract fixfc5ce5f: actual63+7metadata completed3/3,
  reused3/3, and reused3/3 again after explicit identical-source relocation.
  80combinedCPU tests pass, including corrupt/stale-input refusal and preserved
  failure recovery. This does not qualify expensive inference recovery/fullG3.
- [Saturday script/fixture readiness](../implementation/11-stakeholder-validation.md):
  124focusedUI tests and actual2028CPU package loader pass. Fresh engineering-only
  ASGI save/idempotent retry/reopen/revision2/stale-write refusal pass; original
  five files unchanged, no production decision. Exact participant time/role and
  live GPU walkthrough remain pending; no feedback invented.

- [Matched KD error-review preparation](../operations/KD-MATCHED-ERROR-PREPARATION-20261104.md):
  metadata-only adapter reconciles all12control and seven KD native validations
  through14k across eight journal segments/82metadata files, with report/component
  backup equality, recipe/cohort/reference checks and stable append-only prefixes.
 49CPU tests pass, including actual synthetic70-case CLI/partial-horizon handling.
  Original control cleanup-only failure remains explicit. No final verdict/CI.
- [Seven-case visual review](../operations/WEEK-05-MAC-VISUAL-REVIEW-20261104.md):
  Lenovo opened26sheets; Mac verified transport,26image hashes, seven case bindings
  and78plane/world transforms, then inspected nine key sheets across all seven
  cases. Original renderer export failure and separate metadata recovery preserved.
- [Baseline metadata admission](../operations/WEEK-05-AUTONOMOUS70-METADATA-REVIEW-20261104.md):
 63completed/seven declared failures retained; exposed development and original
  numerical-equivalence UNQUALIFIED exception preserved. No independent acceptance.
- Training-hours collector/UI, native reviewer identity/save/reopen checks and
  retrieval prototype remain delivered. See [parallel work](../operations/WEEK-05-PARALLEL-WORK-20261103.md),
  [reviewer follow-up](../operations/WEEK-05-REVIEW-FOLLOWUP-20261103.md) and
  [training accounting](../operations/COMBINED-TRAINING-HOURS-20261103.md).

## Completed Mac KD treatment — retained November5 launch snapshot

The following launch observations are historical; the completed closeout above
supersedes their running/pending wording.

- Root: `/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/mac-kd-treatment-resume-20261105-01`.
- Ready SHA256: `38b8f8a83a4ca3d6ceab76cdb8d34fe2681d71e16c4e50a9460b9240da359049`.
- Explicit user resume from independent pause.pt at20989; actual-MPS producer/cold
  qualification passed/reaped. Scientific20990→21229, teacher accessed/KDweight0.1.
- launchd `com.prowl.mac-kd-treatment-resume-20261105-01`, supervisor92279/worker92391,
  guardian92394/caffeinate92393; one exclusive MPS owner.
- MLflow `1e356a71e4f74d5192a091fc40d3f6b8` RUNNING; stored metrics through21225; initial step21000 loss0.549666405,
  supervised0.547090113/KD0.025762973 stored, no tracking warning. Initial/ready
  independent backups match;152producing pins match.
- Initial checkpoint SHA256`a3d013740827610698026e46d122da474810ab24b286b633017d1b78fb5ba10d`.
- Hourly monitor ACTIVE with new root/receipt; private training-hours source follows.
  Same recipe/teacher/cohort and345600second cumulative cap:209780charged,
  135820remaining. Preserve all attempts; no automatic retry/successor.
- Latest completed20k lesionDice0.389084, pancreas0.772516, positivecases33/36,
  reference-empty alarms33/34. Interim only; final full24k comparison pending.

At matched14k, lesion Dice.294552→.332939 and recall.368768→.533653, but precision
.337540→.301739, empty-case alarms31/34→34/34 and empty lesion voxels103008→239211.
Missed reference components remain8/45in both arms. These are same-update descriptive
point estimates, not completed24k acceptance. Supplied-region KD and autonomous
baseline scopes remain separate. See the [KD runbook](../operations/MAC-KD-LAUNCH-HANDOFF-20261027.md).

## Provenance and next action

Lenovo reviewed17existing records for visually similar6755/2889: serialized source
hashes/lengths differ, native dimensions/spacing agree, coordinates differ by flips
and a derived z-origin shift. Verified patient/study/series relationship mapping was
not found in those records. Both cases and70denominator unchanged; patient
independence remains unresolved. No scan/mask/new-header reads or duplicate audit.
Peer report SHA996be9c75ecc8c0dd0574d211cda8f2cd9ce0216774a95d5eba74b0f56b6bb15.
Do not call case-level bootstrap intervals verified independent-patient uncertainty.

KD is complete; do not restart it. Review its full selected/terminal evidence and
the four-case larger-model screen tomorrow. Patient independence remains unresolved,
and aggregate counts do not establish spatial false-positive causes. No further
filter/verifier/crop/threshold or training experiment was started. Both model runs
are closed; private prediction delivery awaits reconnection. Full G3/reviewer
acceptance and aunt feedback remain open; walkthrough tentatively SaturdayNovember7.
