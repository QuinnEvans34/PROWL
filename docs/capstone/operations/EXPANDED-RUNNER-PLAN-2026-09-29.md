# Expanded runner and readiness profile — D-284

Quinton requested the next step after D-283. Implement a separate bounded role-aware processed
RAM cache, deterministic multi-member schedule, complete-role full-volume evaluation and checkpoint
codec. Preserve old runtime and frozen cohorts. This slice verifies integration; it does not launch
CAP-EXP-005. No new cases, source mutation, literature edits or Git publication.

Acceptance: wrong roles/membership, altered inputs/identity/progress and over-budget allocations
are refused; retrieval returns copies; complete train cycles use every member once; validation never
updates. Checkpoint binds both role inventories, preprocessing, source/environment and configuration;
restore verifies optimizer/scheduler position and the next scheduled member. Compare uninterrupted
and restored synthetic updates. Keep the 300-update existing configuration ceiling.

Profile after tests: exact D-283 54 files, 16 train/11 validation, one source pass, processed cache
at most 512 MiB (float32 image/uint8 target). No real updates. Fresh seed42 balanced model, LR0.0003,
96-cube patches; full-volume forward on all 27 cases. Synthetic MPS scheduling and checkpoint
recovery exercise uses invented arrays only. Separate identities prevent synthetic weights being
used for the real forward profile. Profile time limit 1,200 s, RSS16 GiB, evidence256 MiB,
internal free floor100 GiB. No automatic retry or run extension. Record measured cache size,
per-role evaluation timing, failures and recovery. Prepare the next training plan from results;
production artifact publication/independent-device restore must be verified before training launch.

MPS continuation qualification: exact next-member/crop/loss trace; parameter max absolute
difference <=1e-6 after an additional update. Require exact fixed-probe recovery of the saved
checkpoint in a fresh process. First bitwise continuation check failed; measured follow-up
difference was 3.725290298461914e-9, documented in the experiment log.
