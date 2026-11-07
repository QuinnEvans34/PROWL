# STU-Net interim saved-native metadata — November 7

The adjacent JSON exports all 70 cases at each completed 2,000, 4,000 and 6,000-update validation. The 8,000-update validation was not complete at capture and is omitted. Training is untouched. This is an interim metadata export, not scientific closeout or a model-selection verdict.

| Update | Positive-case mean lesion Dice | Detected / 36 | Empty-case alarms / 34 |
| --- | --- | --- | --- |
| 2,000 | 0.144179 | 28 | 33 |
| 4,000 | 0.222087 | 26 | 29 |
| 6,000 | 0.347182 | 30 | 26 |

Every report contains 70 unique development aliases matching the frozen input receipt, with 36 positive and 34 empty references. All report backups match; immutable source reports were rehashed after export. The JSON includes per-case metrics verbatim, full denominators, CT/pancreas/lesion identity hashes from the frozen input JSON, native geometry, report hashes, checkpoint identities from journal receipts, metric-producer pins and the launch receipt hash. No checkpoint bytes were read.

The retained November 2 Mac selected-control identity handoff matches all 70 aliases and all 210 CT/pancreas/lesion hashes. This establishes matching with that retained handoff only. The final November 5 KD treatment/control report bindings are not available in the inspected local locations, so final cross-model reference equivalence remains unverified. Mac should join this export against both final arm receipts before interpreting matched differences.

Recall, precision, explicit FP/FN voxel counts, explicit missed-component counts, individual component assignments, connectivity and size-band thresholds are not stored in the inspected reports. They are flagged as missing, not generated. Existing target/predicted/overlap voxel counts, reference/detected/predicted component counts, size bands and volume fields are preserved. Empty/empty Dice is null; it must not be silently changed to one or zero. The export checks Dice arithmetic, positive-case aggregation, detection/alarm booleans, exact cohort membership and backup equality.

No scans, masks, tensors, inference, scoring, threshold sweep, GPU work, producing-pin changes, monitor changes or new launch. Unknown pretraining exposure and provided-pancreas-region scope remain explicit. Improvements across this ongoing run do not establish an isolated cause or justify launching another experiment.
