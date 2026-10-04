# CAP-EXP-006 sustained localizer learning curve

D-287: Quinton approved moving to the next experiment after the sustained-training regroup:
“Great. I agree. Good call. Move onto the next experiment then.” This authorizes preparation,
verification and one bounded next experiment. Codex selects the exact implementation parameters
below under that instruction; they are not represented as numbers Quinton individually specified.
No additional experiment, automatic retry, extension or checkpoint continuation is authorized.

## Question and comparison

Does substantially greater training exposure reduce excess foreground while retaining pancreas
coverage on the frozen 16 training / 11 development-validation cohort? CAP-EXP-005 reached mean
Dice 0.1262/0.1512 after 288 updates, with median volume ratios 13.08/12.56 and no strict fit passes.
Both roles improved at its last evaluation. Duration alone is not known to solve this behavior.

Fresh seed42 SegResNet, two outputs, fp32 native MPS/fallback disabled, 96-cube patches, existing
3mm preprocessing/HU[-100,300], balanced CE + foreground soft Dice, AdamW LR0.0003/wd0.00001.
Keep exact source files, frozen 16/11 roles, original member order and equal pancreas/background
center sampling. All difficult/partial cases remain. No validation optimizer inputs, augmentation,
threshold search, largest-component filtering, architecture change or old-checkpoint initialization.

**2,400 updates =150 equal cycles over16 training members.** Cosine horizon stretches from288 to2400;
this is a duration/schedule-horizon experiment, not identical learning-rate history. Step288 in this
run is descriptive, not a matched-schedule replication of CAP-EXP-005. Fresh weights must match the
same frozen initialization digest. This is an exploratory pancreas-localizer experiment, not the
formal autonomous baseline, lesion training or a generalization claim.

## Frozen endpoints and interpretation

Full-volume evaluation of all27 cases at0/288/800/1600/2400. Final endpoint at2400, no best-checkpoint
selection or performance-based stopping. Preserve per-case results and all intermediate curves.
Primary comparison: final mean development-validation pancreas Dice versus CAP-EXP-005 final.
Operational evidence of improvement: at least+0.05 absolute mean Dice; mean mask recall must not
fall more than0.02 and no additional case may fall below99.5% prediction-box reference coverage.
Report train values, per-case differences, mask precision/recall, volume ratios, empty outputs,
box scan fraction, ROI screens and strict fit screens alongside this criterion. Do not equate a
pass with useful contour quality, statistical significance or generalization.

If the Dice bar passes but a coverage guardrail fails, report a tradeoff; do not call it an accepted
localizer improvement. If neither bar passes, reject the practical improvement hypothesis at this
horizon. Missing/incomplete execution is inconclusive. A small final slope is descriptive, not proof
of convergence. No performance result changes eligibility or removes a difficult case.
Existing limitations: tiny nonrepresentative validation (no arterial/thin-slice stratum), unverified
study-as-subject identity, partial references in training and no lesion-containment evaluation.

## Resources, preservation and interruption

Checkpoint at0/400/800/1200/1600/2000/2400; independently back up each before further updates.
Persist evaluation records immediately, including before terminal publication. On interruption,
retain last completed checkpoint, independent backup receipt and journal; no automatic restart.
Resume would require a new explicit plan/authorization. All27 final source-grid binary NIfTI,
processed-grid overlay, transformation and metric records, plus terminal record, must validate.
Restore all35 artifacts from independent backup in a fresh process with primary Python reads
blocked; require terminal step2400 and exact fixed prediction probe. This is not a physical unplug test.

Maximum50min update phase (including intermediate evaluations/checkpoint backups),60min total
including loading/export/backup/recovery. Existing16GiB RSS/MPS cap,512MiB RAM cache,1GiB new bytes
per domain,96MiB/artifact,256MiB local evidence,100GiB internal free floor remain. Exact54 source
files,1GiB compressed/4GiB expanded input budget. No new data qualification/source modifications.
Previous288-update phase took247s; linear extrapolation is about34min for2400 before changed
checkpoint/evaluation overhead. This is an estimate, not a guarantee; limits are never extended.
AC power and exclusive cooperative accelerator lock required; nonfinite values, power loss,
resource/storage or integrity failures stop the attempt and preserve evidence.

## Qualification and request

Explicit sustained_localizer_v1 budget allows at most2400; legacy configs retain100/300 caps.
CAP-EXP-005 exact controls remain available without widening their scope. CAP-EXP-006 checks exact
configuration, cadence, time limits, inputs and bound approval. Test refusal of changed controls,
complete synthetic transaction, evaluation persistence, checkpoint backup failure, interruption and
checkpoint restoration. Native suite and synthetic MPS/independent recovery must pass before launch.
Freeze exact source/environment, inputs, recipe, capability and this plan. Bind approval to the
prepared request digest under D-287; consume once. No unrelated retrieval edits or Git publication.
