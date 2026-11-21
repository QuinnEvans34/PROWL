# Proposed transfer experiment — design for review, not a launch receipt

> Initial audit snapshot. Read [the later clearance follow-up](09_clearance_followup.md) for newly verified publisher checksums, historical test-use evidence, sidecar plans and candidate-image findings. The initial release is preserved.

## Question, scope and claims

Does original TotalSegmentator initialization improve **pancreatic-lesion segmentation under a fixed PROWL training recipe**, compared with the identical STU-Net-B architecture initialized randomly? The initialization comparison is primary. Historical SegResNet/KD results provide context, not a matched architecture control.

No training is authorized by this document. Membership/exposure review, preprocessing qualification, real-device engineering checks, measured budget, backup/recovery and explicit scientific approval must precede a frozen launch. This design does not call any current development scan an unseen patient.

## Arms

| Arm | Initialization | Role |
| --- | --- | --- |
| Existing PROWL SegResNet control and KD | SuPreM, with/without train-only teacher targets | Historical contextual results; report existing selection and terminal scores |
| STU-Net-B random | Entire network random; seed 42 | Primary matched control |
| STU-Net-B pretrained | Exact audited 58,157,984 body parameters; identical seeded fresh heads | Primary treatment |
| Anatomy-aware STU-Net-B | Separate later approved target/loss design | Optional ablation, not part of primary comparison |
| Distilled smaller student | Separate train-only outputs from a selected qualified teacher | Optional later experiment with zero-KD control |

Baseline pretrained exposure is disclosed. Do not label SuPreM-initialized SegResNet as scratch or present the Universal four-case screen as a new training gain. Compare STU-Net arms on the same hardware; cross-device timing differences are not model speed effects.

## Membership and independence

Preserve all 1,333 train and 75 development registry members. Reuse the qualified **70-case** development scoring subset for historical alignment; report all five remaining cases and why they are outside that scoring scope. Do not quietly reintroduce them or remove poor-performing/overlap cases after seeing model results. The registry has 671/662 training positive/reference-empty and 38/37 development positive/reference-empty; the 70-case subset has 36/34. These are annotation-based counts.

Record exposure classification for all 75. Any source-matched or unresolved evaluation cases may support **exploratory exposed-development** results only. A prospectively defined non-overlap subgroup is supplementary, not a newly independent test. Removing exact duplicates does not establish that remaining patients are independent. Train/dev subject groups and pretraining selection exposure need original crosswalks or independently sourced evaluation.

The public 901-case benchmark remains protected. This audit neither reads its images/labels nor proves a complete history of non-use. Before using it once as a locked benchmark, complete the prior-usage ledger and a separate model-source overlap assessment. Prefer the author-administered external datasets after confirming hospital/patient separation and intended evaluation permissions. Do not tune repeatedly on external feedback.

## Candidate fixed recipe to qualify

These are explicit proposed settings, not measurements of a qualified implementation:

- One CT input; six-stage STU-Net-B, widths 32/64/128/256/512/512, depth one, 3³ kernels. Five fresh three-class heads. Seed 42 for matched head initialization and input/exposure schedule; save all RNG states.
- **128³ patch, batch one, 12,000 optimizer updates per arm.** No gradient accumulation. Checkpoint every 500; full native 70-case development scoring every 2,000 and at terminal. Both arms receive the same batches, augmentations, exposures, optimizer schedule and validation cadence. Do not treat 4,000 upstream epochs as 4,000 PROWL updates.
- Candidate 1.5-mm training grid with CT-only resampling/cropping and per-case z-score after a fixed CT-only foreground crop. This choice is pending small-lesion/field-preservation audit; it is not accepted merely because upstream used it. Fit any dataset-level transforms on training cases only. If geometry preservation fails, redesign and freeze **both** arms before training; do not switch one arm or modify a producing pin.
- Mutually exclusive labels: lesion priority over pancreas; background otherwise. The body/lesion source masks remain immutable. Full CT inference or a separately frozen CT-only localizer; no development/reference pancreas mask may locate an inference crop. Report provided-region historical results separately.
- AdamW, learning rate 1e-4 for all body/head parameters, weight decay 1e-5; 500-step linear warmup then cosine to zero at 12k. Full fine-tuning in both arms. No EMA or teacher loss in the primary pair.
- Foreground Dice (pancreas parenchyma and lesion) plus three-class cross-entropy, equal summed terms; background excluded from Dice, included in CE. Define exact epsilon/reduction in implementation before freeze. Five-scale deep-supervision weights proportional to 1, 1/2, 1/4, 1/8, 1/16 and normalized to sum one; categorical nearest target downsampling. Audit that deep supervision does not silently remove all signal from small lesions.
- Sampling: 75% lesion-focused / 25% context opportunities; lesion-focused selection uses positive **training** annotations only, context selection cycles the entire training cohort, including reference-empty cases. Freeze the complete exposure trace, component-selection policy and coverage accounting. Do not infer that random sampling guarantees every patient is covered.
- Augmentation proposal: axial flips p=0.5 per axis; rotation within ±15 degrees; isotropic scale 0.9–1.1; intensity shift ±0.1 and multiplicative scale 0.9–1.1 after normalization. Use the same sampled transforms in both arms. Masks use nearest interpolation; no development fitting.
- Inference: no TTA, 128³ windows / 64 stride, fixed Gaussian probability blending, three-class argmax, inverse mapping to native grid. No minimum-volume/component filter for the primary analysis. Freeze all interpolation, padding and outside-field behavior.

This paired recipe isolates initialization under one finite compute budget; it does **not** establish optimally tuned scratch versus optimally tuned pretrained performance. A later equal-budget hyperparameter study could test differential body/head learning rates, frozen-encoder warmup or upstream optimization. Record it separately rather than selecting the best treatment recipe after looking at results.

## Selection, endpoints and uncertainty

Choose maximum mean native lesion Dice among complete scheduled validations on the 36 annotated-positive development scans; deterministic tie-break to earliest step. Report terminal results and every scheduled validation, not only the selected maximum. Score the same eligible members in both arms and enumerate failures without dropping them from the accounting.

Primary effect: paired difference in mean positive-case lesion Dice. Proposed practical target: +0.02 absolute Dice. Proposed paired guards: component sensitivity delta at least -0.03, no more than one additional positive scan with zero overlap, no increase in reference-empty alarm count, mean reference-empty predicted volume no greater than 1.1 times control plus 0.1 mL, and pancreas/lesion-union Dice delta at least -0.02. These proposed thresholds need approval before freeze. Formal confidence-based acceptance additionally requires justified independent groups; it is unavailable while patient groups remain unverified. Report distributions, paired case deltas, zero-overlap failures, lesion volume/size strata and representative saved contours. A single seed and repeatedly selected development set support descriptive exploration, not definitive generalization.

Additional endpoints: pancreas parenchyma and pancreas/lesion-union Dice; component-wise overlap sensitivity using fixed 26-connectivity; case-level any-lesion sensitivity and reference-empty specificity; alarm counts and predicted mL on reference-empty scans; component false positives, runtime, peak device/host memory, parameter count and total compute. Clinical sensitivity/specificity cannot be inferred from incomplete annotation states. AUC requires a prospectively defined continuous case score and trustworthy case labels; do not derive it from hard masks alone.

Empty reference lesion Dice/recall are undefined, including empty/empty predictions. Positive reference plus empty prediction has Dice zero. Surface distances may be reported only with valid physical units and both surfaces nonempty; list missing/infinite cases rather than assigning zero distance. Use patient-group bootstrap intervals only after valid groups exist; otherwise exploratory case-bootstrap intervals must disclose unverified independence and model-selection bias. Do not silently interpret cases as independent patients.

## Execution and experiment logging gates

Before scientific launch: prove intended loaded/skipped tensors and identical fresh heads; inspect permitted train-only transform/coverage pilot; qualify actual-device forward/backward, full-field native reconstruction and bounded throughput; verify full-state checkpoint/independent backup/cold restore; freeze all sources, data identities, pretrained SHA, runtime environment and scientific request. Stop on integrity/geometry/resource failures. No retry loops or scientific successor are installed.

Proposed per-arm ceiling: 48 hours wall time including validation, 12 GiB owned host RSS, 100 GiB external free floor, qualified device allocation under its existing exclusive-GPU policy; actual storage/backup ceilings must be measured and approved. If profiling cannot fit the proposed recipe, return a revised paired design **before** any optimizer updates. Do not shrink only the treatment arm or silently reduce validation scope.

Create one MLflow experiment group with separate scientific arm runs and nonpromotable engineering runs. Tags: source revision, dataset/cohort/split hashes, exposure tier, patient identity status, checkpoint origin/SHA, initialization, model/target/preprocessing versions, device/environment, seed, permitted scope, selection rule and exclusions. Log scheduled curves, per-case native reports, selected/terminal steps, component/empty-case endpoints, resource totals and checksum manifests. Record interrupted/failed attempts accurately. Engineering time, downloads, teacher generation and optimizer training time are separate compute categories; never count this audit as training.

For external evaluation, the [current PanTS instructions](https://github.com/MrGiovanni/PanTS#external-out-of-distribution-test-set) request a checkpoint, testing script, in-distribution results and a short usage README. Prepare a deterministic inference package and de-identified result manifest, but do not email or upload it without the user's explicit send authorization. Submission and any access conditions remain to be agreed with the authors; availability is not guaranteed by the README.
