# Focused duration recovery diagnosis — D01

**Current outcome:** D01 and fresh D02 completed and are retired. D02 measured weight maximum
3.725290298461914e-9 and optimizer maximum4.3655745685100555e-9; progress and both RNG states
matched exactly. Acceptance remains bit-exact/failed. [Results and limitations](SEGMENTER-DURATION-RECOVERY-AUDIT-RESULTS-2026-10-07.md)
and [the next proposed limited-readiness decision](SEGMENTER-DURATION-REAL-DATA-PREPARATION-2026-10-07.md)
supersede pending/unexecuted wording below. No scientific launch or tolerance amendment occurred.
The original reviewed packet and both frozen controls remain historical evidence, not replay authority.

Quinton selected one bounded diagnosis effort on October 7: identify the mismatch, repair only
a demonstrated cause, use a focused recovery check, and prepare the real-data duration comparison.
The first reporting implementation is qualified by the new model-free DUR-05 checks. This is
the fresh actual diagnostic scope; it is not an N02 retry or a scientific experiment.

## Question and smallest useful job

Does a new continuation of the retained invented step-48 checkpoint reproduce the saved step-49
model, optimizer, progress, CPU RNG and MPS RNG? Report every predicate and numerical differences.
This can identify a reproducible failing component; it cannot reconstruct N02's discarded
in-memory failed state or establish every later checkpoint/export's recovery.

- Attempt: `DUR_RECOVERY_20261007_D01`; exclusive new local receipt namespace.
- Input: only N02's independently kept invented step-48 and expected step-49 artifacts. Two pinned
  completion receipts identify 113,213,038 payload-member bytes. Pinned primary completion and
  events/catalog provenance remain validated from the backups; no external primary is opened.
- Generate the same invented 144³ provider, verify its saved control identity, and reproduce the
  step-48 probe/six-member inference ordering before one next update: seven image-only predictions
  plus one training forward, **eight forwards/one optimizer call**. No 192-update producer repeat.
- Cold comparison uses the unchanged exact predicates. Report at most 16 differences and 32 KiB
  component metadata; no raw weights/optimizer/arrays are saved to the diagnostic report.
- Limits: five minutes, 12 GiB sampled owned RSS and boundary-checked MPS driver memory;
  136 MiB maximum retained payload reads; 4 MiB local control/report/log output; 100 GiB free floor.
  A live worker watchdog, AC-power checks, idle-owner proof and shared MPS lock are required.
- Existing keeper is read-only. No new keeper/restore/external writer, registry/capacity change,
  deletion of existing evidence or acquisition. Original/cache/CT/third-party payload reads zero.
- Freeze the current 400 producing pins and the separate helper hash in the local request; review
  these and the exact source references before the one native invocation. On refusal/failure,
  preserve it and stop; no retry or automatic additional diagnostic calls.

## Frozen controls

The local request is at `outputs/prowl/SEGMENTER-DURATION-DUR05-20261007/diagnostic-request.json`.
Its SHA256 is `f53440052a12a9c0569d3c0e99be8ce3b9e957bde96b4998b1861991218431cb`.
The unexecuted fixed helper is retained locally; its separate hash and exact three input metadata
hashes are in that request. Job admission remains subject to native tool approval review.
All consumed N02 controls/markers and every partial artifact remain unchanged.

## Interpretation and next decision

D01 completed once: eight forwards/one invented update, 9.788469 seconds, 1,162,100,736 bytes
sampled owned RSS; worker reaped. Progress and both RNG states matched; model and optimizer
differed. The model magnitude was not measured because the reporter treated `OrderedDict` as
a scalar structure. Preserve that report and the D01 source snapshot. The demonstrated reporter
defect is repaired without changing the acceptance predicate; 40 model-free checks pass.

Fresh D02 measures the repaired component-wide maxima with the same two pinned inputs and
eight-forward/one-update scope. Its 290-second ceiling keeps D01 plus the maximum D02 below
five minutes. No old job/marker is reset; D02 has its own exclusive namespace and source binding.
Request SHA256: `8e9c492cf3d06117b1be5446ee4d12fd5dd00b22e03d96f1f00a50d65b0ff264`.
The two diagnostics together allow at most16forwards/two invented updates and8MiB local outputs;
no extra independent backup copy, storage-cap increase or scientific authority follows.

A difference is evidence to inspect, not proof of its cause or an acceptable tolerance. A match is
a focused diagnostic result, not full duration-native qualification. Neither outcome writes the
scientific readiness acceptance. Fix only an identified defect and reassess what focused/full
qualification is needed. Any tolerance/protocol amendment requires a separately reviewed decision.

The real-data comparison remains fresh scratch, seed42, six original training members and
report-only2514; only duration48→192 changes. Retain checkpoint/evaluation points0/48/96/144/192,
D-335 baseline, tiny2973/boundary6238, DUR-01 coverage/false-foreground stops, terminal192 primary,
50 original-target reads/zero original CT and the approved26GiB/100GiB-free budget. Its exact read
ledger, current resources and launch controls follow after the recovery decision; no scientific
request or indefinite overnight queue is authorized by this diagnostic.
