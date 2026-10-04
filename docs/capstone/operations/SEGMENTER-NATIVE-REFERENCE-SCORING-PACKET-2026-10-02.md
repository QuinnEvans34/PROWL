# Next slice — original-native segmenter baseline scoring

Follow D-324 scratch step0 inference/export qualification. This packet proposes implementation and qualification, not a frozen source request or training launch. Keep exact6train3/26/2232/2973/5821/6238,1development-validation2514, all12 candidates/fiveholds, protected ancestry and old153/23localizer pool. D-319–324 producers/requests remain immutable. No model forwards or optimizer updates are needed for this scoring job.

## Exact inputs and fresh read gate

Use accepted D-324 native prediction exports, complete source shape/affine/transform and scratch identity. Read retained scope proposal `outputs/prowl/SEGMENTER-INFERENCE-REVIEW-20261002/native-reference-scope-proposal.json` and the independently sealed D-324 acceptance. Replay registered purpose/role/cohort ancestry before the native-reference consumer. Four empty unknowns/5641 annotation hold remain absent; no fabricated negatives or substitutions.

Exactly14original targets: pancreas and lesion for each of the7members. No CT or other source files. Compressed hash1,265,220B; compressed decode1,265,220B; expanded272,494,704B. Preserve original hashes and old observations. Before freezing, verify source APFS UUID/registry/root and perform a bounded14path stat-only inventory. Reconcile remount-device changes explicitly; other observed changes stop the job. Metadata is not content verification. The fresh one-shot source request must perform original complete hash/decode with independent byte/hash pins and source observations before/after, strict approved binary decoding/scaling/units and matching CT-qualified native grids.

Implement a separate target-only reader; do not call the triple reader and discard CT. Reject wrong stage, absent/held/wrong-role, extra files, stale scope, quota overflow and consumed request. Record reservations, actual hash/decode/expanded accounting and failures. No reuse of D-321/D-323 consumed requests and no global source activation.

## Metric contract and failure oracles

Original pancreas/lesion truth is three-class lesion-over-pancreas: lesion outside pancreas remains class2, never clipped. Score pancreas parenchyma, lesion and pancreas-lesion union per case/role: original count, predicted count, true positives, Dice and recall. Preserve integer numerators/denominators. Include every original26connected lesion component, its native count, hits/recall and missed status. No nearest/continuous round-trip target can substitute for original model truth. All predictions, including dense/empty/wrong/fragmented masks, must be scored without reference-oriented foreground/component caps. Unknown empty holds are not eligible negatives and receive no invented perfect lesion Dice.

Synthetic tests before original reads: small analytically counted multiclass/precedence examples, missed tiny/disconnected/boundary/outside-pancreas components, dense/empty/wrong-role failures, geometry drift, state0 provenance, binary scaling, corrupt/hash/byte/scope/consumption refusal. Profile CPU/maximum40,547,328nativevoxels and original target decoding/resources before freezing. Proposed serial/two threads,1200s,8GiB RSS,100GiB free,32MiB evidence; adjust prospectively only from measured profile. No model or CT work.

Publish complete scoring/source-reference controls with a new scoped capability; independently restore all required metrics/component/hash/control members using the descriptor-aware primary-read guard. Large original truth/prediction arrays can remain rebuildable scratch if declared; D-324 already protects native predictions independently. Seal direct count/byte/ancestry/source/runtime oracles and all scores, including failures. Store all consumed/incomplete requests; do not silently retry or change reference membership.

## Training remains a separate transaction

After accepted native scores, audit historical checkpoint hashes/import denial and qualify the real optimizer/sampler/learning-rate/evaluation/export/interruption/keeper transaction with synthetic data under the real task's contract. Decide a bounded short-run recipe from evidence, then freeze exact inputs, schedule/objective/update count, baseline/post-evaluation, budgets and recovery inventory. One validation positive/no verified real negatives remains an engineering smoke; formal jitter, larger validation/specificity, autonomous cascade and promotion are later experiments. No automatic training or extension is authorized by this packet.
