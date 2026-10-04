# Next slice — qualify the real segmenter training transaction

This is an implementation proposal following D-325 original-native baseline scoring. It is not a training request or launch approval. Finish and accept D-325 before acting on its result. Preserve accepted D-319–325 producers, requests, checkpoints, source observations and storage registry; add separate versioned consumers rather than opening existing readiness interfaces.

The goal is a short, interpretable real-data learning diagnostic on the existing six training cases and one development-validation case. Long training, formal jitter, autonomous predicted ROI, broader validation and model promotion remain later experiments. Provided pancreas-reference ROI and positive-only engineering validation must remain explicit in every run record.

## 1. Initialization and historical checkpoint audit

Read the approved model-lineage contract. Inventory retained prior-project checkpoint identities, byte counts and hashes from existing verified records first; resolve missing hashes through a separate bounded file-only inventory if necessary. Do not recursively deserialize arbitrary checkpoint files or scan unrelated projects. Distinguish prior-project trained weights, capstone localizer weights, synthetic-trained segmenter weights and accepted scratch step0 controls. None is a permitted warm start for this diagnostic.

Create the real training task from deterministic fresh random initialization. Bind seed 42, exact 1→3 SegResNet architecture/tensor signature, source/runtime identity and initial weights hash. Verify initial weights equal the independently accepted D-324 scratch hash `3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`, so its D-325 scores are a valid before-training baseline. Hash equality proves initialization equivalence; it does not authorize loading D-324 weights. Refuse external weight-import APIs, wrong task/head, synthetic learned state, localizer state and unknown provenance. Checkpoint resume may load only complete same-run training state with exact lineage, and must be distinct from initialization.

Test these refusals on invented records and wrong-task checkpoint fixtures before real training. Record the coverage and any missing historical inventory evidence rather than claiming an exhaustive audit from filenames.

## 2. A separate role-safe optimizer consumer

Use the accepted D-323 cache and D-320 registered purpose/cohort replay, D-321 geometry and original ancestry. Exact optimizer members: 3, 26, 2232, 2973, 5821, 6238; evaluator member: 2514. Preserve all twelve candidates, five holds, original roles and the old localizer pool.

Existing `InputCache.get` permits inference/evaluation only. Existing synthetic `Session.update` rejects external inputs. Keep both contracts unchanged. Add a distinct qualified training cache/session boundary that validates immutable cache/binding/member hashes, registered optimizer descriptors, task/geometry/target state and explicit operation before returning optimizer inputs. An arbitrary image/target tuple or an evaluator result must not qualify itself for optimization. Reject validation-as-training, held/absent members, stale descriptor/cache/geometry, altered arrays and extra members. Inference still returns images without targets.

Use full normalized 144³ ROI, batch one, unchanged lesion-over-pancreas targets including outside-pancreas lesions, and zero jitter. Do not exclude tiny, boundary or difficult cases based on baseline scores. Trace every consumed training member, epoch and update. A deterministic permutation of all six training members each epoch prevents a hidden change in exposure; resume must restore the exact next member.

## 3. Objective, schedule and selection records

D-322's synthetic v3 CE weights `[1,1,256]` plus present-foreground Dice demonstrated mechanics on explicit class-cue fixtures. It did not establish the best real CT objective or learning rate. Specify exact CE reduction, foreground terms, absent-class behavior, smoothing and gradient checks for the new real task. Justify the candidate from training class counts and synthetic evidence; never use the single validation case to tune class weights or thresholds.

Recommend one fresh scratch, constant-rate, complete-epoch short diagnostic as the first comparison. Exact learning rate, epoch/update count, checkpoint intervals and wall-clock cap remain proposals until the new 144³ optimizer/resource profile passes. Do not inherit the synthetic 0.003 rate or localizer schedules without a recorded decision. A future comparison must change one named factor and use a fresh request.

Record terminal plus every predeclared required checkpoint. For this smoke, designate terminal as the primary comparison checkpoint to avoid selecting around one validation example. Preserve any best-checkpoint tracking as a separately declared training criterion, its history and tie rule. Do not claim formal validation selection or promotion. Empty/oversized/wrong predictions remain evaluations, not eligibility changes. Numerical/lineage/resource failure stops the transaction; weak learning is retained as a diagnostic outcome under the predeclared completion rule.

## 4. Before/after native evaluation

Use D-325 accepted original-native counts, confusion matrices and all component baselines only after proving exact scratch and inference-policy equivalence. During training, mapped tensor targets are training supervision and tensor diagnostics; they cannot replace original-native evaluation truth.

Freeze a fresh stage-specific target-only evaluation scope for every planned native evaluation. D-325's fourteen-target request is consumed and cannot be reused. The simplest short smoke can use the protected D-325 before scores and one fresh fourteen-target final scoring pass, provided step0 equivalence is qualified. If intermediate native evaluations or a retained reference cache are proposed, budget their reads/storage explicitly before freezing. No new original CT reads are required when the accepted image cache is unchanged.

For all seven cases, restore three-channel probabilities through the accepted source-grid transform before argmax. Record complete native class counts, pancreas-parenchyma/lesion/union Dice and recall, all original 26-connected lesion component hits/misses, outside-pancreas behavior and failed masks. Use the accepted pure scoring/count oracles in a new task-specific evidence contract. Report six-case training macro and pooled metrics separately from the single development-validation case. No verified real negatives means no real specificity claim. Keep tiny 2973 and source-boundary 6238 in every denominator.

## 5. Transaction, interruption and independent recovery

Bind task, initial weights, exact cache/cohort/descriptors/geometry, objective/optimizer/schedule, sampler, code/runtime and evaluation policy into the run identity. Commit model, optimizer, CPU/MPS RNG, completed update count, next sampler position, learning-rate position and evaluation/checkpoint history together. An exception after optimizer mutation creates a dirty uncommitted state; it cannot publish or advance the committed counter. Reload the last complete checkpoint instead.

Qualify CPU interrupted/uninterrupted equality and actual 144³ MPS save/reload probe and next-update tolerance in fresh processes on invented input under the new transaction contract. Reusing D-322 as evidence is useful but insufficient for the new real-input API and identity. Inject interruption before/after mutation and publication; refuse mixed state, changed controls, duplicate consumed requests and cross-task resume. Qualification must include the production native export/evaluation path, not weights alone.

Protect every declared required checkpoint, configuration, lineage, sampler/history, evaluation/control record and native prediction export on the independent failure domain. Declare rebuildable cache/views/reference arrays separately. Calculate complete artifact sizes plus retry reserve, all checkpoint copies/restores, provenance overhead and preserved failures before proposing a new capability. Do not reset D-324 or D-325 frozen ceilings or remove partial evidence to make space. Restore each required keeper with the accepted descriptor-aware primary-read guard, exact member checks and probability/native-output probes.

## 6. Measured readiness and exact launch packet

Profile full 144³ native MPS forward/backward/optimizer, CPU RSS, allocated/driver memory, serialization and final all-seven native evaluation/export. Include registered ancestry replay, independent backups/restores and maximum native grid in the total budget; per-update timing alone is insufficient. Specify supervision, power/device/fallback checks, free-space floor, cancellation and recovery procedure prospectively.

Run focused rejection/analytic/transaction tests and the full native suite. Seal the failed qualification attempts as well as the accepted results; independently recheck accepted predecessor source pins and registered member bytes.

Only then prepare an exact short-run request: members, immutable initialization/cache/reference pins, loss/rate/schedule/updates, sampler/checkpoints/evaluation points, total time/memory/read/storage ceilings, required keeper inventory, interruption policy and learning screens. Explain what the experiment can establish and what remains open. Present that concrete packet for the separate exact-launch decision. No real optimizer updates or automatic extension are authorized by this document.
