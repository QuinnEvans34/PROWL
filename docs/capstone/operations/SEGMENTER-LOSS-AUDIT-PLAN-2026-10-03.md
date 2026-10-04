# D-329 — training-only objective and head-gradient audit

Quinton's “Great, continue on” dispatches Phase A of the CAP-EXP-013 follow-up. Implement and qualify a separate read-only consumer, freeze its exact request, then execute the bounded diagnostic. It grants no real optimizer calls or changed-loss training. Accepted producing sources, target permissions, cohorts, holds and CAP-EXP-013 evidence remain fixed.

## Questions and measurements

Decompose accepted v3 weighted CE `[1,1,256]` and present-foreground Dice with the original reductions and epsilon. Check scalar and analytic logit-gradient parity against the accepted objective and autograd on invented examples, including absent classes, tiny/boundary lesions and lesion precedence. Refuse malformed/nonfinite tensors and protected-role substitutions.

For each of six training members at saved steps0/6/24/48, retain all target counts, weighted denominator shares, per-true-class CE scalar contributions, per-present-class Dice values, conditional probabilities/margins/confusion, and CE/Dice/total logit gradients by true/output class. Measure final 1×1 convolution weight/bias gradients for CE and Dice separately, their norms, channel components, dot product and cosine. These are head gradients; they are not full-backbone gradients or AdamW's eventual update direction. Observational gradients cannot prove causality.

## Exact numerical boundary

24 case/checkpoint diagnostic transactions, each with one forward and two explicitly counted vector-Jacobian queries (CE and Dice): 24 forwards/48 VJPs, zero optimizer calls. This spells out the earlier proposal's “24 forward/backward evaluations”: each evaluation contains both objective terms; it does not add cases or checkpoints. Total head gradient is the sum, without a third backward query. Use an eval-mode analysis clone with gradients enabled only for the final convolution. The accepted architecture uses GroupNorm and no dropout; training/eval forward parity is checked on invented inputs. Do not claim full training-graph profiling.

The independent decomposition must match the accepted objective within float32 numerical tolerance. Analytical gradients are checked against autograd on small CPU tensors; the maximum-shape rehearsal also compares analytic and autograd logit gradients on MPS. Model state, CPU/MPS RNG and all `.grad` fields must remain unchanged. No session update, UpdatePermit, optimizer step, model registration, selection or checkpoint publication is allowed.

## Qualification and execution

New audit module, CLI and tests only; accepted producer files remain immutable. CPU tests precede an invented144³ MPS rehearsal covering six fixtures. Freeze source/runtime pins and rehearse before publishing a real request. Real scope is the existing same-run checkpoints and freshly resolved qualified cache. Exclude validation from numerical analysis and recipe selection. The accepted ancestry resolver may verify metadata and the complete seven-member cache; those verification reads are separately accounted, not additional model evaluations. No original `.nii`/`.nii.gz` opens are allowed.

Limits: 900s total,12GiB CPU RSS and sampled MPS driver memory,100GiB free on primary data/system volumes,32MiB local numeric job output. Checkpoint reads are bounded to four validated nine-member payloads (each state≤96MiB); cache closure≤128MiB, six consumed image/target pairs≤96MiB. Monitor and interrupt on limits; preserve failed/consumed attempts with no automatic retry. The frozen request records exact checkpoint references, cache control hash, protected member list, accepted111 producing pins plus new audit pins and runtime. Each real request is single-use.

Numeric summaries are compact, contain no original images or masks, and are independently copied to a new D-329 folder under the already approved backup root after verification. Bound that new folder to16MiB and account against existing whole-root occupancy; do not reset earlier frozen storage ceilings or reuse CAP-EXP-013's write capability. Preserve a hash manifest and verify independent readback. Local detailed analysis is derived scratch until this copy succeeds.

## Exit and next decision

Report all24 rows and measured limitations, native tests/resources, nonmutation evidence, exact consumed request and independent numeric verification. Use training evidence to propose one candidate loss factor and its invented qualification; no changed-loss real launch follows automatically. Keep terminal48 primary and retain tiny2973/boundary6238 and all difficult cases.
