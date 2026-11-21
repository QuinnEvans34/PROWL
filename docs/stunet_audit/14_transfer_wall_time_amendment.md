# STU-Net transfer wall-time amendment

Recorded UTC: 2026-11-07T00:26:50.094568+00:00.

The user explicitly answered **“Approve a 60-hour cap”** to increasing only the wall-time cap for the single authorized exploratory STU-Net-B transfer run. The total wall-time ceiling is now **216,000 seconds (60 hours)**, including training, validation and checkpoint/backup overhead. This supersedes the 48-hour wall-time statement in the prior launch handoff and the unapproved 50-hour proposal only; it changes no scientific or other resource setting.

Preserve the original 48-hour request and its failed runtime gate. The frozen pilot projected 174,337.14150035218 seconds (48 hours, 25 minutes, 37 seconds): 102,096 seconds conservative training, 68,641.14149998338 seconds conservative validation and 3,600 seconds overhead. This is a conservative estimate, not a completion guarantee. Record the approved ceiling in a new amended request/receipt without rewriting old producing pins or failure evidence.

The experiment remains 12,000 optimizer updates, all 1,333 training members, six full native validations on the qualified 70-case development cohort, and checkpoints every 500 updates. Existing model, initialization, inputs, sampling, geometry, precision, loss and optimization proposal remain subject to qualification and freezing. The 12-GiB host RSS, 6-GiB CUDA, AC, independent backups, exclusive GPU and existing storage gates are unchanged.

Lenovo remains the sole scientific dispatch host. Proceed autonomously with the remaining input, visual, native-validation, cold recovery, backup and launch checks, then launch exactly one run if all gates pass. No automatic retry, successor, protected test use, or leakage-free claim is authorized. This document and the human approval are not evidence of a scientific launch; actual worker, advancing journal, stored MLflow metrics and matching backups must establish that separately.

The exact approval is recorded locally in `outputs/prowl/stunet-transfer-20261106/user-wall-cap-approval-60h.json`. The launch chat received this approval through the authorized chat handoff.
