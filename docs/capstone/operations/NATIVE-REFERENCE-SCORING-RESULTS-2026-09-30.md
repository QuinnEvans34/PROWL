# D-304 — original native-reference scoring completed for all153 cases

Implemented and verified a target-only source reader and bounded96M native metric API. The8-case
pilot and145-case continuation both passed, reading exactly153 qualified pancreas labels once.
All113training-fit and40development-validation members reconcile; original membership and23 holds
are unchanged. No CT source files, model forwards, optimizer updates or source rewrites occurred.

## Initialized-model baseline

These are case-level means for the fresh initialized144³/2mm model, before training. References are
original native-grid labels, with preserved visible-reference/partial-coverage limitations. This is
not a trained-model result or a population/generalization estimate.

| Measure | Training fit (113) | Development-validation (40) |
|---|---:|---:|
|Mean native Dice|0.00170046|0.00205342|
|Mean foreground recall|0.01841491|0.02460534|
|Mean predicted/reference volume ratio|40.5190|142.3141|
|Mean box reference coverage|1.0|1.0|
|Mean acquired-scan crop fraction|0.99716423|1.0|
|ROI diagnostic passes|0/113|0/40|
|Empty predictions|0|0|

The boxes cover the reference because they span nearly the entire acquired scan; all fail the
existing maximum25% scan-fraction diagnostic. Their large coverage alone does not establish useful
localization. Volume-ratio means are sensitive to tiny references. No threshold was tuned and no
case removed because of these results. Each case and its original limitations remain in the record.

Three predictions exceed the old4M foreground diagnostic ceiling; five native grids exceed the old
64M size ceiling. The new path scored all of them. Old APIs stay unchanged. Metrics use16-slice
binary checks/counts and axis reductions, not full foreground-coordinate lists. Empty predictions
are explicitly represented; aggregate box coverage counts them as zero. Optional component details
are marked `not_computed` and do not suppress the required metrics.

## Reads, resources and tests

| Job | Labels | Compressed bytes | Expanded bytes | Total seconds | Peak process RSS |
|---|---:|---:|---:|---:|---:|
|Pilot|8|2,169,179|460,358,260|12.078|5.817GiB|
|Continuation|145|19,773,100|3,938,509,771|67.179|4.248GiB|
|Total|153|21,942,279|4,398,868,031|79.258|5.817GiB maximum|

Both jobs stayed within20minute/16GiB/128MiB-output limits, AC and100GiB internal-free floor. Qualified
bundle/role/target permissions, source volume/root, original compressed-file hash, source shape/affine,
retained unit interpretation and unchanged strict-binary implementation were checked. Only the target
file is opened by the new reader; a synthetic test removes its CT file and still succeeds.

1,491 native tests pass (31 new), with two existing upstream warnings. Tests include96M dense grids,
predictions above4M foreground, empty/tiny/fragmented cases, signed/permuted anisotropic axes, invalid
arrays/affines, changed reference identity/source/decoder/geometry, old capability refusal, request
controls and consumed batch/worker refusal. The initial synthetic fixture needed the decoder hash
added to reflect the existing qualified-descriptor contract; production policy was not weakened.

Independent post-run review verified175 scoring-package members, unique153 reference paths and exact
113/40 membership. It replayed summaries and metric arithmetic from saved counts, checked target
counts against the decoder's independent sum and prediction counts against D-302/D-303 exports,
matched every descriptor to the frozen binding, and reverified prediction-package hashes. This was
record/count replay, not an additional reread of original labels. The full read budgets reconcile exactly.

## Retained records

Capability: `docs/capstone/data/NATIVE-REFERENCE-CAPABILITY-2026-09-30.json`, SHA-256
`90967ebe492234a0dabcfaaf6c1daf8c3d54ab25fc15c559d787b4b18e0c8e70`.

Pilot directory: `outputs/prowl/native-score-0f1c4da9-6657-44c6-b7e3-cbf2ac333bd3`.
Request: `e101806ebbc24ad868a5eed103e0e0a1aa6aeb6d2fe5015e4790a32fbca7c500`.
Completion: `e46a39fca9f58ffed442f57cbd59be9942a338f4acc5e9cb14d903762e716946`.

Continuation: `outputs/prowl/native-score-5fc8ec34-7b14-4474-bf36-be67b85593f0`.
Request: `8baf2f285913991522cbd2d365e80f0a608b2f88f8039731828a71929790598f`.
Completion: `83f7b725202ffa1303b0fd2a7dd6ec43a46d7dd17018625ac2aecfdc5a516f7f`.

Review: `outputs/prowl/native-score-review-20260930`, containing all153 case records, aggregate
summary and native test log. Review completion:
`f136d5d0408024cd0829fb4f5fcf5f98cf35e19517b8ec9abe94a768de408981`.
Both source-read batches and requests are consumed. No active worker remains. Results are reproducible
local evidence; this scoring step created no new independent backup artifacts.

## Next: the training executor

The input, full-volume inference, native export and original-reference scoring paths now work for
this full cohort. Continue with section2 of the
[training completion packet](TWOMM-TRAINING-COMPLETION-PACKET-2026-09-30.md): separate authorized
training identity/loop, role-safe sampling, progress, checkpoints, evaluation and interruption recovery.
Keep the current readiness API unable to update real cases.

D-304 grants one consumed reference pass, not indefinite evaluation reads. A future training request
must explicitly budget its evaluation stages and reference reads. Existing baseline scores may be
reused only after exact fresh-initialization/cache/prediction-policy/reference identity checks; this
does not load learned weights. Otherwise request a fresh baseline pass. The proposed300updates and
45minute envelope still require the actual loop rehearsal and a frozen launch request.
