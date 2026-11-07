# CAP-EXP-020 — proposed STU-Net lesion-confidence screen

**State: PROPOSED; NOT AUTHORIZED OR QUALIFIED FOR EXECUTION.**
Prepared November 7 at Quinton's request to get ahead of the current training run.
This is an exploratory development inference-policy comparison, not training,
formal G5 acceptance, a frozen launch receipt or an automatic successor.
The [machine-readable proposal](CAP-EXP-020-PROPOSED-20261107.json) records unbound
identities and gates explicitly. No RUNNING MLflow record or new training hours.

## Question and motivation

Can suppressing weak lesion-class winners improve positive-case macro DICE by at
least .02 without losing detected reference components, small-case recall or
material pancreas quality? The [interim analysis](STUNET-INTERIM-ERROR-ANALYSIS-20261107.md)
finds both excess predictions and misses. At 6k, 10/36 positive cases predict at
least twice reference volume; cases 2028/1347 have near-complete recall and low
precision. These observations motivate a cheap policy screen before another
multi-day training run. They do not establish that low confidence causes the errors.

The five small-total-lesion cases average only .047820 DICE, and three have no
overlap. This candidate can only remove raw lesion voxels, so it **cannot recover
a raw miss**. Small-lesion preservation is a guard, not a promised benefit. If
misses remain after the full run, a later training-only size-balanced sampling
question may be justified. No sampler, loss or longer training run is queued here.

## Fixed parent and evaluation role

- Sole proposed execution host: Lenovo, **after** the existing launch02 finishes
  all 12k updates/six complete 70-case validations and tracking, independent
  backups, producing pins and worker/GPU cleanup pass. The Mac owns analysis and
  synthetic preparation. Do not repeat the failed Mac STU-Net-B memory probes.
- Parent: the completed run's selected checkpoint, highest mean lesion DICE over
  all 36 positives across six validations, earlier step on ties. Record its exact
  checkpoint, selected-report, source/receipt and environment hashes before any
  scientific inference. Never substitute the currently best 6k checkpoint.
- Same complete 70 exposed development cases, 36 positives/34 empty references,
  fixed CT/pancreas/lesion hashes and native geometry; no exclusions or test reads.
  Same supplied-pancreas regions, normalization, 128-cube/64-stride reconstruction,
  model/weights, FP32 and inference settings. This is not an autonomous baseline.
- Unknown pretraining exposure, inherited unit policy and unresolved patient
  linkage remain explicit. No PDAC-TAGS image/mask use or publisher-test access.
  Case IDs/counts do not establish independent patients. No independent-patient
  interval or causal architecture/pretraining claim.

## One changed factor

Use a single reconstructed three-channel probability field per case for every
arm; never run the network once per threshold. The reference policy is the exact
raw multiclass argmax. Channel order: background, pancreas, lesion.

Three candidates use fixed lesion thresholds **.40, .50, .60**. A voxel remains
lesion only if it was already a raw lesion winner and its lesion probability is
at least the threshold. A suppressed lesion winner takes the highest-probability
nonlesion class. Existing nonlesion winners and argmax tie behavior stay unchanged.
Apply at the existing reconstruction's class-decision point; do not threshold
individual tiles or move interpolation/orientation. Softmax confidence is not
calibrated disease probability.

Do not add component-size filtering, largest-component selection, morphology,
an extra pancreas mask, TTA, an ensemble or any training change. Native metrics,
reference roles and the current region policy stay fixed.

## Signal, guardrails and selection

The primary outcome is macro lesion DICE over **all 36 reference-positive cases**,
including zero-overlap misses. Report all 70 dispositions, all four policies and
both case/component detection and empty-case alarms. Empty/empty lesion DICE is
null and excluded from the positive-only primary mean. Undefined precision must
retain its denominator. This is exposed development selection, not held-out proof.

A candidate provides a useful screen signal only if **every** check passes:

1. Primary DICE improvement versus the fresh raw-policy arm is at least .02.
2. No case or reference component detected by raw becomes missed. Report every
   affected alias; an aggregate count cannot hide a trade between cases.
3. Macro recall for the small-total-lesion group does not decline. This group is
   not a substitute for an individual-component-size analysis.
4. Overall positive-case macro recall falls by no more than .01, and pancreas
   macro DICE over all defined cases falls by no more than .01.
5. Empty-case alarm count and total lesion false-positive volume do not increase.
   The lesion-subset property should make these monotonic; violations indicate a
   policy/geometry/metric defect and stop the screen.
6. Complete matched references, geometry, cohort, resources and raw/derived
   artifact integrity checks pass. No partial cohort produces the primary verdict.

If several candidates pass, use maximum primary DICE and the lower threshold on
ties. If none passes, retain raw and record a null/failed utility result. Report
the complete curve rather than only the winning point. No candidate is promoted
automatically; G4/G5, broader performance and independent-evaluation requirements
remain separate. These thresholds and guards are prospective proposed settings,
not a retrospective label applied to already observed threshold results.

## Qualification and bounded compute

Metrics alone are not probabilities. The inspected producer did not retain the
needed per-case probability volumes, so no saved-count shortcut can execute this
screen. A separate additive inference adapter/runner and a final qualified receipt
are still needed; the running worker must not be edited to save extra artifacts.

Proposed maximum: **four hours total**, including setup, qualification, inference,
metrics, backups and cleanup; **12 GiB combined owned RSS**, **6 GiB CUDA**,
AC required, both existing 100 GiB free-space floors, 32 GiB combined cache and
64 GiB combined backup limits. These are proposal ceilings, not authority to
expand any existing limit. Verify current combined usage before admission.
Conservative time/storage projection must fit; otherwise hold and return the
specific estimate to Quinton instead of silently extending the cap.

Use one largest-buffer positive case and one largest-buffer empty case for the
bounded qualification, chosen deterministically from the final frozen native
geometry. Qualification checks actual device/memory, strict checkpoint/source
binding, raw argmax parity, unchanged geometry, raw-versus-candidate identity and
backup/reopen behavior. Successful same-identity pilot outputs may be reused;
charge all pilot time to the four-hour cap. Do not rerun failed stages automatically.

The current metadata implies 3,963 inference tiles and 2,128,136,535 native voxels.
Four uncompressed uint8 policy masks plus one independent copy would use about
15.86 GiB before headers, receipts or other retained artifacts. This is an estimate,
not admission. Process one case/policy at a time, release buffers, retain raw and
all three derived masks and hash their identities. Do not retain all 70 full
float32 probability volumes just to run three thresholds. Preserve reports,
source pins, case failures, every attempted stage and verified independent copies.

If the original run lacks raw native-mask hashes, exact old spatial equivalence
cannot be established by matching counts. Check saved raw metrics for consistency,
record that limit, and compare the new raw/candidate outputs from their **same
fresh probability reconstruction**, each with new mask hashes. Do not silently
claim the old spatial output was reproduced voxel for voxel.

## Preparation delivered and remaining gates

`src/inference/lesion_confidence_policy_v1.py` is a pure NumPy candidate, isolated
from producing inference. Fifteen synthetic tests pass: raw identity, class/tie
semantics, exact boundary, unchanged source arrays/nonlesion winners, nested
lesion subsets and invalid-input refusal. These are not real-volume, device,
memory, native-geometry or scientific qualification results.

Before execution: complete/final-review the current run; bind the parent and
cohort/reference hashes; implement and verify the additive native runner; freeze
the exact protocol/metric/environment identities; qualify real resources and
backup recovery; verify exclusive GPU ownership and current safety gates; obtain
the separate launch decision. No watcher, schedule, permit or GPU command was
created by this proposal. Revisions require a new dated version with the original
proposal retained. Target review window: Week 6, November 9–15, not a promised run.

The negative outcome is still useful: if safe suppression cannot improve DICE,
we avoid treating a confidence threshold as the answer and can select a training
intervention from the completed errors. A high mean obtained by dropping lesions
or cases does not satisfy this design.
