# Corrected STU-Net continuation: saved-evidence audit

Snapshot UTC 2026-11-08T21:20:02.046043+00:00; global **13983**, **1983 new updates**, 3.31 hours. Same supervisor/worker identities live; MLflow RUNNING, 1983 stored losses match the journal prefix. Latest checkpoint 13500 matches independent backup. Phone API live and total journal hours consistent. No pinned files changed, no data arrays/models loaded and no new inference.

**No completed corrected full70 validation is available at this snapshot.** First is global14000. Original12k reference metrics in JSON are explicitly separate; they are not evidence of corrected-run improvement.

## What the model has seen

1333 distinct training cases; 1000 positive-case updates, 983 empty-case updates. 734 patches contain lesion; 266 positive-case patches contain no lesion. Sampled class fractions background/pancreas/lesion: 95.448818%, 4.208763%, 0.342419%. Counts include zero padding and repeated visits. Coverage/context counts: 1488/495; first component jitter scheduled at global15971. Exact per-case visits and seven corrected-case visits are in JSON.

## Diagnostic interpretation

Saved diagnostic updates: 12001, 12501, 13001, 13501. JSON preserves every available per-scale target count, conditional class CE, soft Dice and body/head gradient norm. Diagnostic trigger is before the update, so actual records are12001,12501,... rather than12500. Loss uses weights16/31,8/31,4/31,2/31,1/31 and CE plus foreground soft-Dice loss; absent foreground classes included. Conditional CE means are not independent weighted loss contributions.

All four diagnostic patches are lesion-empty at every scale. Body/head gradients are nonzero, but these samples cannot test small-lesion survival under deep supervision. All seven corrected cases were visited (10 updates total).

## Evidence limits

Intensity saturation was not logged. No saved input image tensors or histograms were read. Class counts measure sampled targets, not anatomical field completeness. Saved native scalar metrics support Dice, voxel recall/precision, misses and aggregate FP volume, but do not locate FP components or identify unmatched predicted components on positive cases. Component counts use26-connectivity and case size bands use total annotated lesion volume; small means under1000mm3. Mac can separately analyze its existing saved original12k masks.

No hypothesis verdict or future recipe change is justified yet. Await the complete matched70 report; then compare positive Dice and small-case recall alongside empty-case alarms and FP volume.

## Reproducibility

Adjacent JSON SHA256 `cd4112d0856f2b250b7fd6eda74a605765734120c1482ac210043f2d8e2e8628`. It contains the exact journal-prefix byte length/hash, input/plan/ready references, raw diagnostic records, checkpoint backup proof and ten producer source hashes matched to frozen ready pins. The live journal grows after the recorded prefix. This export is descriptive and does not alter the scientific run.
