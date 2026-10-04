# CAP-EXP-006 probability audit — bounded implementation plan

D-289 plan; D-290 implements and executes on Quinton’s continuation instruction.
**Before execution: freeze the tested request.** This audit separates
probability behavior from the broader-cohort intervention. It will neither update model weights nor
select a production threshold. Existing validation remains development validation.

## Question and fixed scope

Do reference pancreas voxels missed by the final hard mask receive appreciable foreground probability,
and what coverage/crop-size tradeoff results at a few fixed operating points? This can distinguish
weak probability separation from a hard-decision effect, without claiming to determine why it happened.

Use only CAP-EXP-006 terminal step2400 and the existing qualified16 train/11 validation cases.
Run package: `outputs/prowl/expanded-execution-943d4c6d-29b8-4d85-a2e5-fce579116f59`, receipt
`900c05364910507ba4f927733f1bf3225a900c85fabc4a99a6bcba306c0c9567`.
Resolve the terminal checkpoint through its recorded artifact/receipt/derivation identities; reject
missing, substituted or mismatched state. Reuse the exact v2 preprocessing recipe and54-file input
capability. Never feed the new176 candidates into this audit.

Before inference, freeze a new request containing the terminal checkpoint identities, role cohort and
input hashes, preprocessing, code/environment snapshot, this plan hash, resource limits and fixed
analysis settings. Verify the original run's retained source evidence separately: today's diagnostic
code may differ, but the model, input adapter and prediction path must remain compatible. Report any
compatibility difference before proceeding. A failed request is retained, not silently overwritten.

## Fixed analysis

- Predict each full processed volume once, in eval mode with gradients disabled, MPS fp32, two CPU
  threads and no fallback. Baseline uses exact argmax, not an assumed equivalence at probability0.5.
- Reproduce the recorded terminal hard-mask metrics/exports within an explicitly frozen tolerance.
  Pin that tolerance and establish synthetic/restore repeatability before viewing real probabilities.
  A mismatch stops interpretation; it must not be dismissed as model behavior.
- Report foreground-probability distributions inside the reference, outside it, and in reference
  voxels missed by baseline: fixed quantiles0,1,5,25,50,75,95,99,100 percent plus sample counts.
  Processed-grid statistics are labeled as such. No reference-informed component selection.
- Report all fixed thresholds `p_foreground >= {0.01,0.05,0.10,0.25,0.50}` alongside argmax. These
  are descriptive probes, not a sweep from which a best threshold may be promoted. Do not add
  thresholds after seeing results. No margin tuning, largest-component filtering or weight changes.
- For each point, report processed Dice/recall/precision/volume ratio and the fixed10mm-box coverage.
  Map the exact processed box to the acquired source grid using `source-crop-geometry-v1`; use
  acquired source volume for crop fraction. Label processed-reference coverage separately from
  native-reference coverage; do not mix the two to claim a production ROI pass.
- Preserve per-case results and role summaries, empty-mask counts and failures. Show all11 validation
  cases rather than only examples that support a threshold hypothesis. Compare train/validation
  behavior without confidence claims from these small, repeatedly inspected development samples.

## Limits and acceptance

Budget:20minutes wall time,16GiB process RSS,54 source files under unchanged current input limits,
512MiB processed cache,256MiB new evidence,100GiB internal free-space floor. No dense probability
exports; retain scalar distributions and immutable checkpoint/input provenance. Do not open new
candidate payloads, publisher test data, lesion labels or external literature. No dependency changes.
Hash model parameters before and after; step remains2400, no optimizer call is reachable. Retain
request, source/environment snapshot, terminal identity, resource observations, all per-case metrics,
completion/failure record and receipt. Tests must cover nonfinite/out-of-range probabilities, threshold
boundary semantics, empty masks, role binding, exact hard-mask parity and source-box mapping.

Completion yields an explanation and a proposed next experiment, **not a usable localization policy**.
Lower thresholds may recover anatomy while making crops impractically large. If none helps, keep that
null result. If one helps, it still needs a separately fixed policy and prospective development
verification. Broader cohort qualification can proceed independently; do not combine data breadth,
threshold, margin and loss changes into one supposedly single-factor comparison.

## D-290 exact compatibility and parity rule

Hard-mask tolerance is zero: processed confusion counts and box must exactly match the saved
terminal export record, and restored native binary arrays must be byte-for-byte equal as arrays.
Existing independent MPS recovery demonstrated identical probes; new synthetic tests check tie
semantics, exact metric parity and refusal. No tolerance will be relaxed after reading probabilities.
The only changed original captured source file is expanded_executor.py, which adds crop reporting
to evaluate. Prediction/restore dependencies remain byte-identical; the audit additionally checks
AST equality of its original metrics and checkpoint-validation functions.
