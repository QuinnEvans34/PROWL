# Fixed 70-case autonomous baseline: prepared proposal, not launched

Prepared request: `E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a01/request.json`.
SHA256: `853faa584b3abc87e5b16b25c186af9cdbd5e1bbe69b08de208d5ecabe083cbc`.
All producing pins verified November 3. No restoration, inference or training launched.

## Scope and evidence limits

Exactly the existing 70 development patients, autonomous arm only. Reuse five retained predictions; the request inventories 65 new predictions and 65 missing CTs (2,266,786,215 bytes). No optimizer overlap with segmenter or localizer training is recorded. All 70 influenced segmenter checkpoint selection; three influenced localizer selection (2514, 5194, 7687). Teacher and SuPreM patient membership remain unknown. This is exposed-development, exploratory evidence, not independent generalization. Selected control KD maximum weight is zero.

The previous numerical comparison remains FAIL/UNQUALIFIED: 169 probability differences, identical hard masks. The human exception covered four cases only. Extending it to this scope requires an explicit decision; no tolerance is changed.

## Preserve the 5592 failure and denominator

The first metadata preparation failed at the existing localizer resampling cap. Its source and failure receipt are preserved at `E:/PROWL/readiness/week05-full-baseline-preparation-20261103-attempt01-failure.json`. Additive v2 records the failure rather than suppressing it: patient 5592 conservatively requires 235 x 215 x 398 = 20,108,950 output voxels, above the frozen 16,000,000 cap. No CT arrays or model forwards were used for this proposal.

Recommendation: retain the cap and record this patient as a preflight resource-limit failure in the full 70-case denominator. Do not exclude it, assign an invented Dice, or raise capacity. Thus the proposed accounting becomes five reused predictions, up to 64 new predictions and one declared failure. Report successful-case metrics alongside 69/70 maximum execution coverage and the failed ID; never present them as complete 70-case performance.

The frozen prepared executor deliberately rejects unresolved preflight failures. After approval, a separately versioned controller/request must explicitly implement this failure-accounting policy and qualify it before launch. The current receipt is not launch-ready and must not be edited in place.

## Time and resource proposal

Estimates conservatively retain the original 65-new-case inventory (before the recommended one-case resource failure). They use four-case measured throughput, not guarantees:

| Phase | Estimated time | Hard limit |
| --- | --- | --- |
| Restore missing CTs from nine archives | 46–84 minutes | 2 hours; 2 GiB RSS; 3 GiB extracted CTs |
| New autonomous inference | 75–155 minutes | 600 seconds per worker |
| Separate native CPU scoring | 28–38 minutes | 600 seconds per worker |
| Independent backups | 9–28 minutes | Included in evaluation budget |

Total projected phase time is approximately 2.6–5.1 hours, plus admission/header checks and overhead. Evaluation including scoring/backups has a proposed 42,000-second (11h40m) ceiling; restoration has its separate 7,200-second ceiling. A cap is not an expected duration.

Inference: 12 GiB owned RSS, 6 GiB GPU, 96 million source/region voxels, 512 tiles maximum; existing localizer 16-million-voxel cap remains. Free-space floors remain 100 GiB on C: and E:. No automatic retry/resume; preserve failed and pending cases, and require a new receipt for any later continuation using remaining budget and exact completed outputs.

Retain the existing float32 probability output contract. Full-volume upper bounds are 25,537,638,420 bytes of probabilities plus 4,256,273,070 bytes of prediction/localizer masks. Propose 32 GiB outputs and 32 GiB independent backups. Existing backups measured 30,736,550,123 bytes; the old 40 GiB combined cap cannot hold this conservative retention budget. Explicitly approve a 64 GiB combined backup cap. Projected disk space passed the unchanged free-space floor at preparation; recheck before actual work.

A masks-only retention variant could reduce storage, but is not implemented or qualified and is not necessary to return this proposal. No existing probability outputs will be deleted or downcast.

## Exact remaining decision and execution order

Approve the exploratory numerical exception for exactly these 70 patients, autonomous only; the resource/time/storage ceilings above; bounded CT restoration; and explicit 5592 failure accounting with the frozen cap retained. Then prepare and test a separately versioned failure-accounting controller/request, restore only required missing CTs, verify exact original identities and native headers, freeze the source-admission receipt, and launch once under that receipt. Keep every patient in the reporting denominator. No training, test-set reads or Mac KD interruption.

## Completed native review

Six native CT overlay sheets were reviewed on Windows and reported reviewed on Mac. Missed components 4681 (0.206 mL) and 6755 (0.682 mL) remain unoverlapped in both arms despite complete input-region containment. False-positive components are also visible away from the reference pancreas; provided-region predictions are not consistently better. Four cases cannot support a model-acceptance verdict.

Review evidence: `E:/PROWL/readiness/week05-native-review-20261103-a01`; independent C: backup retained. Both private transfers completed. The 2028 packet hash is `35d0e97d35ea0266facceb29f243510f417b810c75fa6c0d0c1757e3c5642126`; the six-sheet gallery hash is `3ebf4af3d2667bc9abe9eec3e11f9328df83d88f720ddcf62927bfdd4af0e0dd`. Exact observed physical-record schemas and review documentation were pushed in fe4d7c6. No clinical review decision was fabricated in the registered package.
