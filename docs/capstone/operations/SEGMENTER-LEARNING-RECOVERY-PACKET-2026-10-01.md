# Next slice — fresh three-class segmenter learning and recovery

Proposed after D-321, completing PhaseC of [Stage2 qualification](STAGE2-QUALIFICATION-AND-CASCADE-PACKET-2026-10-01.md). Geometry/loading and exact seven-case reference fidelity are complete; the segmenter model and training transaction are not yet implemented or launched. This packet is a concrete next implementation proposal, not a real source-read or training request.

## Immutable inputs and scope

Use [D-321 results](SEGMENTER-GEOMETRY-RESULTS-2026-10-01.md), the registered D-3206/1 cohort and full D-319 purpose/transition replay. All12candidates/fiveholds, original protected roots and old153/23localizer pool remain fixed. Train3/26/2232/2973/5821/6238, validation2514. One validation positive/no verified negatives is an engineering reference only.

Geometry acceptance: `outputs/prowl/SEGMENTER-GEOMETRY-REVIEW-20261001/accepted-geometry.json`, persisted SHA-256 `b3ff4db94b49f1ea9b44d57afd975c17f16309c9929df35fa3e0d9f7e67e7384`. Recipe hash `2382855d8414a5d52a9f80813eb00093835adc3cd21690fd787b58aa6017d488`; exact request `07d3bb4f8e49220a721b5d79efb66595f0f22350ca1a1f75c25c9d34195cc476`, completed evidence `5c958ac1877c52c2eefd55e3cfe0824428322ca72dbd12ad52043c02e1d8fe1f`. These pins qualify provided-reference ROI, zero-jitter144³/1mm intermediate/10mm margin only. Per-case effective spacing differs with the uniform scale; it is not a fixed1mm tensor. Preserve the exact portable transform pin per input and inverse.

The D-321 request is consumed. No tensors/native arrays were persisted for future model use. Do not reread its21files under that old request or treat its output as a model cache. A later cache/model-profile adapter needs a new stage-specific source/reference capability, resource qualification and request.

## A — model input, objective and scratch identity

Add a separate versioned SegResNet-family three-class model/configuration/session. Follow [model lineage](../imaging/MODEL-LINEAGE-AND-TRAINING.md). Start fresh scratch for this mechanical diagnostic; do not warm-start localizer/prior-project/unknown weights, use teachers or download pretraining. Record architecture/tensor signature, initialization/seed/initial-weight hash, code/runtime/configuration, cohort/descriptors, geometry acceptance and sampler/optimizer/loss identities. Historical checkpoint hash denial must cover unauthorized imports and task-head confusion.

Inputs are float32 CT tensor with one channel and exact three-class integer target0/1/2 from the shared mapper. Require finite values, shape/classes, matched case/role/geometry and portable inverse record. Independent tests verify class2 means lesion and class1 means pancreas excluding lesion. Image-only prediction must consume a fixed provided/predicted region without reading lesion references. The two ROI origins retain different identities; accepting provided geometry does not qualify autonomous localization.

Propose and freeze a simple loss after inspecting the retained class counts and invented positive/verified-negative behavior. Test background, pancreas and sparse-lesion gradient contributions explicitly. Avoid blindly importing the localizer's experimental class-mean formula. A candidate could combine categorical cross-entropy with separately weighted foreground Dice, but exact reductions, absent-class behavior, weights and smoothing must be justified and tested before freezing it. Use development/train evidence only, never publisher-test or validation-based weight tuning.

Propose a deterministic complete-ROI case sampler for the six-case engineering run, recording member order, completed updates/exposure and RNG state. Do not quietly replace it with lesion-centered patch selection. Geometry zero jitter remains diagnostic; formal development-derived jitter is a later, separately qualified baseline policy. No final architecture/loss/LR/update duration is approved by this packet alone.

## B — independent synthetic learning checks

Use invented small volumes for fast CPU checks and the actual144³ input for the MPS rehearsal. Cover pancreas with a sparse lesion, disconnected lesions, boundary/outside-pancreas lesion and a separately labeled verified-negative fixture. Invented negatives do not create real negative permissions. Specify numeric learning/retention and gradient-finiteness criteria before observing results; preserve failed configurations and do not weaken thresholds afterward.

Check class mapping/precedence independently of the training assembler, all supervised train-case exposure and absence of evaluator inputs in optimizer batches. Show loss decreases and the three-class head can learn sparse/multiple lesions without merely predicting background or inflated pancreas. Report per-class counts/Dice/recall and pancreas-or-lesion union separately; component accounting must retain vanished positives. Independent synthetic target fields should not duplicate the implementation's own transform code as the only oracle.

Make native inference restore continuous probabilities first, check normalization/source grid, then argmax. Synthetic known logits/probabilities should catch channel swaps, stale/wrong source transforms, padding errors and missing background outside ROI. The D-321 nearest reference fidelity metrics are not model Dice.

## C — checkpoint transaction and independent recovery

Checkpoint identity must bind the segmenter task/architecture, exact initialization, geometry acceptance, role cohort/descriptors, configuration/code/runtime and loss/optimizer/sampler. Save model/optimizer/RNG/sampler position, completed-update count, evaluations/selection history and immutable checkpoint bytes. A partial optimizer step must not be declared committed; resume from the last complete transaction, retaining interruption/failure events. Atomic publication and completion-last records must refuse mixed model/optimizer state, modified bytes, wrong model task, missing lineage and repeated consumed launches.

Test save/reload prediction probes and next-update equivalence on CPU, then actual native MPS within predeclared numeric tolerances. Interrupted runs must retain best/last history and exact future case exposure; never reset selection state on resume or overwrite immutable keepers. Qualify independent keepers in a different failure domain and restore in a fresh process with primary access blocked. Restore every declared required checkpoint/configuration/evaluation artifact, not only weights. Record what remains local scratch and what the keeper protects.

## D — bounded native synthetic profile and exit

Propose a separate synthetic MPS budget before execution. Measure full144³ forward/backward, optimizer state, checkpoint serialization/reload, probability restoration and native evaluation/output envelopes. Profile the worst supported native grid synthetically; do not infer peak memory from tensor payload. Pin actual MPS availability, CPU RSS, allocated/driver memory, time/disk ceilings and cancellation; supervise allocations performed by native extensions. Preserve CPU-only and actual-MPS evidence distinctly. Stop on nonfinite loss/gradients, class collapse, resource overflow, invalid lineage or recovery failure.

Run targeted regressions and the full native suite after implementation. Exit requires tested adapter/model/objective/session, independently demonstrated synthetic learning, interruption/save/reload and keeper recovery, actual MPS resource evidence, and a versioned handback with all failed attempts. Keep old localizer consumers/checkpoints/limits and D-319/D-320/D-321 producing code fixed.

After that, prepare a separate exact7-case zero-update model-input/cache/MPS/native-export qualification with fresh reads and reference budget. Inspect every case and independently restore the production checkpoints. Only measured readiness can produce a short real scratch launch packet with exact members, objective/sampler/schedule/updates/evaluation/resource/stop/selection rules. That launch needs the later exact run decision. No long-scale run, final baseline/jitter, formal model promotion or autonomous cascade claim follows from PhaseC.
