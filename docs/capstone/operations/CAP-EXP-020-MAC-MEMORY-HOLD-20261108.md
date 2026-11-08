# Mac confidence experiment: memory hold

The requested Mac experiment was actually attempted with the verified completed
12k checkpoint. It has **no completed native cases, threshold result, confidence
correlation or new Dice result** yet. Do not interpret this resource failure as
evidence against confidence filtering.

The synthetic eval/no-grad128 capacity check passed, but the real native6837
qualification stopped during repeated tiles under the fixed6GiB MPS cap.
The backend reported3.05GiB live allocations plus2.97GiB other allocations and
refused256additional bytes. Owned supervision closed failure after125.190s,
peak RSS1,947,992,064bytes, exit1, all workers reaped. No full native result,
MLflow run or second scan was produced. The one-shot launchd job was booted out.
The original request, source pins, trained checkpoint and independent backup,
process/log/resource evidence remain preserved under `screen-01`.

A separate300s allocation-lifecycle qualification tested whether unused-memory
release could fit unchanged model math under the same6GiB ceiling. It failed
during a real forward before completing its planned equality/reuse checks:
3.05GiB live plus2.71GiB other allocations, requested256MiB. Supervisor duration
4.321s, peak RSS1,177,714,688bytes, exit1, all workers reaped. No passing result
or new screen was dispatched. `cache-release-qualification-01` and the additive
v2 runner remain preserved; do not relaunch them blindly.

The synthetic check was a capacity observation, not a guarantee that repeated
real-volume inference would fit. The cache hypothesis remains unproven.
No MPS high-watermark bypass, memory increase, smaller window, reduced precision,
CPU fallback, crop change, source rewrite or Lenovo GPU interruption occurred.

The required scope decision is whether to qualify **8GiB MPS for this inference
experiment only**, keeping12GiB combined owned RSS, the original four-hour
cumulative deadline, all masks/geometry/weights/policies,26GiB retained backups,
50GB decimal internal/100GiB external reserves,AC and exclusive ownership.
The user was asked explicitly because the saved protocol fixes6GiB. This is a
policy cap, not evidence that the64GiB Mac physically lacks sufficient RAM.

Prepared8GiB scripts require an explicit local approval record and a passing
real-input exact-output qualification before a new native screen. No approval
record has been inferred from elapsed time. If approved, compare repeated
probabilities exactly with/without unused-cache release, then the same two native
extreme cases, full-cohort time admission, and all70 policies. Reuse the already
verified independent checkpoint pair rather than storing another redundant
700MB backup; preserve all attempts and charge all elapsed time to the original
budget. Stop if qualification fails; no unbounded retries or new training.

Implementation and tests remain available on main. The active corrected Lenovo
training and its hourly monitor are unchanged.
