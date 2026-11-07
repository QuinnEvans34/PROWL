# STU-Net corrected training launch - November 6

Launch is VERIFIED. One corrected attempt was explicitly approved with the unchanged 12,000-update recipe and 60-hour wall limit. Original failed a01 and FAILED MLflow 2159a2c44093427ea75748f3feecbc04 remain preserved; that attempt had zero updates.

- Title: Fine-tune pretrained STU-Net with complete lesion coverage.
- Artifact: E:/PROWL/artifacts/pants_stunet_base_transfer_12k_20261106_launch02
- Ready: E:/PROWL/readiness/stunet-scientific-launch-20261106-a02/ready.json
- Ready SHA256: 59e8188d60d70840eabb8752f0be5d5c1f818bc51e3cdcf81d16c74c79cf3e68. All 237 pins verified unchanged.
- Owned session 80176, supervisor 48492, worker wrapper 42604. Verify process identity/descendants, never redispatch.
- MLflow 243ccf3f71c34417be60362af35187d1 RUNNING. Actual updates advanced from 14 to 18 and beyond; stored loss at step18=4.135213375091553 verified.
- Initial checkpoint 232741431 bytes independently rehashed E/C: bb1d20247f04747080307de2d8e7717a33558ab4905b4eb5f1b809a4ce311ec1.
- Dashboard configs switched after old-config hash checks/backups; every historical run retained, prior pending verifier moved into history. API reports running, next validation2000, no invented Dice. Total964588.11seconds/totals_complete=true at step18 observation. Private access unchanged.

## Hourly monitor ACTIVE: do not create a duplicate

Automation monitor-stu-net-training-and-morning-dice is an ACTIVE hourly heartbeat targeting Lenovo chat01a12c40-1490-7cf2-8e20-6498c71bf685. First creation call failed for missing destination; corrected destination=thread call SUCCEEDED and saved automation.toml verified ACTIVE/hourly. No Mac fallback needed. Historical varied-focus remains PAUSED.

Keep quiet during healthy progress. Monitor exact journal, native reports, owned processes, stored MLflow losses, resources, independent backups and phone API. Do not infer stalls during advancing validation/checkpoint I/O. No automatic retry/resume or successor. At the first check after10hours actual elapsed, save/report all available complete validation points, best/latest Dice, steps/runtime, missed lesions/false positives where computed, tracking/backup/resource status. No score guaranteed at an exact time. On completion verify12k updates, six full70 validations, selected/terminal reports, independent checkpoint/report/journal backups, workers successful/reaped, MLflow FINISHED and12k stored losses; report and pause. Pause/report a blocker requiring a user decision. Respect later user pauses.

## Frozen scope

STU-Net-B pretrained, FP32/batch1/128cube, native-detail provided-pancreas regions,1333train/70dev. 2978coverage windows +6022component-jitter +3000context. AdamW1e-4/wd1e-5,500warmup then cosine; checkpoint500 and nativevalidation2000. Limits60h includingvalidation,12GiB combinedRSS,6GiB CUDA,64GiB C backups,32GiB E cache,100GiB C/E free floors. Unknown pretraining exposure remains exploratory, no independent-test or causal-pretraining claim. Pilot scores are not scientific results. See STUNET-PILOT-REVIEW-20261106 for qualification and failed-attempt history. Launch JSON contains machine-readable observations.
