# STU-Net training completion — November 8

Fine-tune pretrained STU-Net with complete lesion coverage completed all 12,000 updates and six complete native-resolution 70-case validations. Selected and terminal checkpoint are both step 12,000: positive-case mean lesion Dice **0.371633**, pancreas mean Dice **0.789740**, 35/36 positive cases detected, 41/45 reference components detected, and 27/34 empty-reference cases with false alarms. This is exploratory provided-pancreas-region evaluation; unknown pretraining exposure remains unresolved. No hypothesis acceptance or cross-model superiority claim is made here.

| Step | Lesion Dice | Detected / 36 | Empty alarms / 34 |
| --- | --- | --- | --- |
| 2,000 | .144179 | 28 | 33 |
| 4,000 | .222087 | 26 | 29 |
| 6,000 | .347182 | 30 | 26 |
| 8,000 | .328011 | 35 | 33 |
| 10,000 | .346184 | 34 | 27 |
| 12,000 | .371633 | 35 | 27 |

Run elapsed time including validation: 105,530.188 seconds (29.31 hours); supervisor 105,557.984 seconds, below the 60-hour cap. All 237 producing pins match. All 12,000 contiguous finite update losses match the 12,000 stored MLflow losses exactly; MLflow 243ccf3f71c34417be60362af35187d1 is FINISHED. All six reports contain exactly the frozen 70 case IDs and zero reconstruction gaps. Earliest-tie best-checkpoint selection verified.

All 34 execution files, including 25 checkpoints, six native reports, journal, result and selection receipt, match independent C backups by fresh SHA256. The adjacent JSON records exact hashes. Supervisor exited successfully, workers reaped and verified absent; GPU idle. Peak owned RSS 3,539,070,976 bytes. Phone API reports completed. Initial failed a01 remains preserved and contributes no training updates.

The completed hourly monitor was deleted after verification to avoid further credit use. No automatic successor was launched. CAP-EXP-020 remains proposed and requires separate readiness and authorization.
