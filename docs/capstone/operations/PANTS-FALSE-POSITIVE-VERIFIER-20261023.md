# Reject false alarms without losing small lesions

Date: October 23, 2026. Priority: **after the knowledge-distillation experiment
and its review**, not simultaneous. Status: planned; no verifier training code,
cache, GPU job, launch receipt or running MLflow record created.

## Scientific question

Can a second model reject spurious lesion candidates from a frozen, sensitive
segmenter without sacrificing real lesions, especially small ones?

“Healthy specialist” is shorthand, not a diagnostic label: annotation-negative
CTs are not proof of a healthy pancreas. A verifier must see both true lesions and
false-positive examples, not only negatives. A patient-level hard healthy/unhealthy
gate can erase every lesion when it is wrong. Start with soft candidate-level
verification while retaining the segmenter's complete coverage and candidate
generation; do not skip its CT pass based on a classifier.

This addresses false alarms directly. Suppressing predictions on negative cases
does not by itself increase Dice averaged over positive cases. It may improve
precision, but a higher positive-case Dice must be measured, including misses.
The historical healthy-heavy experiment increased specificity but reduced
detection and outlining; it motivates explicit sensitivity guards, not a claim
that the same numerical result will recur on today's different cohort.

## Proposed setup and leakage controls

- Finish and review KD first. Select and freeze one segmenter and its checkpoint
  before verifier work. Keep the same patient roles and provided-pancreas-assisted
  inference scope. Do not combine architecture/sampling changes in this test.
- Train a candidate verifier using CT context and declared candidate features,
  including true positives, difficult false positives and annotation-negative
  cases. Use patient-grouped out-of-fold predictions for training/calibration;
  in-sample predictions from a segmenter that learned the same masks are not an
  unbiased substitute. Account for this generation cost in the resource plan.
- Use only training-role data for verifier optimization and threshold calibration.
  Freeze the out-of-fold/calibration identities, features, architecture, probability
  combination, threshold rule, component matching and resource budget before
  fitting. Patient/slice/candidate leakage across partitions is forbidden.
- A training-only calibration subset or nested patient-grouped out-of-fold scheme
  must be specified; do not tune the gate repeatedly on the 70 development cases.
  Teacher membership restrictions carry over if the chosen segmenter used KD.
- Compare the **same frozen segmenter alone** with **that segmenter plus verifier**
  on identical native cases. Missed lesions not proposed by the segmenter remain
  misses; a verifier cannot recover them by deleting false alarms.
- Before training a learned ensemble, optionally examine a fixed simple
  probability-combination diagnostic if compatible teacher/student outputs exist.
  This is not a third authorized training run and requires its own documented
  evaluation scope. Complementary errors, not two impressive standalone scores,
  are the reason to expect an ensemble gain.

## Hypothesis and decision rules

Primary endpoint: reduction in annotation-negative patient alarm fraction at a
locked sensitivity-constrained calibration policy. Let improvement be segmenter-
alone alarm fraction minus segmenter-plus-verifier alarm fraction.

- **H0:** improvement <= 0; verification does not reduce patient false alarms.
- **H1:** improvement > 0 without violating the sensitivity guards.
- Reject H0 only if the lower bound of a paired negative-patient bootstrap 95%
  interval is above zero (10,000 resamples, seed 20261023). Otherwise fail to reject
  H0. Reused development data and a single fitted model limit generalization.
- Draft practical target: at least 0.10 absolute alarm-fraction reduction (with
  34 negative development patients, at least four fewer alarm patients).
- Mandatory point guards: no additional missed positive patient; no reduction
  in <1 mL component-detection recall; positive-case macro native lesion Dice
  delta >= -0.01; empty-case predicted lesion voxel burden does not increase.
  Freeze component matching and size bins beforehand. Report denominators and
  uncertainty, not just percentages. Nonestimable groups are not automatic passes.
- Practical support requires the target, positive interval lower bound and all
  guards. A guard failure or an interval upper bound below the practical target
  rejects practical usefulness; otherwise inconclusive. Passing these small-sample
  point guards is not clinical safety validation or statistical noninferiority.

Secondary: positive-case Dice, pancreas Dice, lesion-component precision/recall,
small-lesion errors, per-case changes and end-to-end inference cost. Always
include missed cases; never report only correctly gated or detected positives.
The goal is reduced false alarms with preserved sensitivity, not a presumption
that this is the best way to reach 0.50 Dice.

## Required before training

KD results reviewed; frozen segmenter identity and role-safe OOF/calibration
scheme; exact prospective verifier specification and bounded budget; candidate/
CT alignment and missing-candidate checks; synthetic and real pilot tests; safe
checkpoint restore; independent backups; new hashed receipt and explicit one-run
launch authority. No test-set reads, repeated duplicate audit, dropped difficult
cases or automatic successor chain. MLflow and the existing private dashboard
must describe this as a separate human-named experiment, not silently append it
to KD. Operational handoff follows the paused/no-credit-polling policy in the
[KD plan](PANTS-TEACHER-DISTILLATION-20261023.md).
