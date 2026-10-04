# D-301 — 144³ session and independent synthetic recovery

Quinton requested the next step after D-300. Codex owns new `twomm_session.py`, its tests,
and a bounded native rehearsal script. Existing consumers and Claude's retrieval lane stay unchanged.

Implement a separate identity/state version for the 2 mm persisted cache and 144³ adapter.
Bind input, completion, source and environment hashes, objective, patch configuration and sampling
policy. Real cache sessions expose inference only; synthetic updates generate an internal fixture.
Verify unpadding before processed-grid output, cache identity rejection, strict optimizer/scheduler
state, changed checkpoint rejection and nonzero-step replay. No real optimizer API or training launch.

Native rehearsal: actual SegResNet, float32, workers0, threads2, MPS fallback disabled. Two synthetic
updates, prediction, step2 checkpoint, independently backed-up copy, then one reference next update.
A fresh process prohibits primary-drive reads, restores the backup into a new destination, repeats
prediction and the next update. Probability tolerance1e-5; next-weight tolerance1e-6; exact crop trace.
This measures recovery, not learning effectiveness or actual OS interruption during a kernel.

Each process:10 minutes,16GiB RSS/driver,256MiB local output,AC power,100GiB internal-free floor.
The shared D-273 store checks preserve distinct volume UUIDs,20GiB aggregate backup cap and1GiB new
bytes per domain across producer/recovery. Checkpoint artifacts use the new semantic validator.
No raw source reads, real cache reads, label changes, membership changes or remote actions.

After passing, prepare the exact real-cache zero-update pilot (8 retained edge cases), then remaining145.
Those requests must bind D-300 completion/binding, current source/environment and bounded export/time
budgets. Native source-grid prediction exports and complete153 resource coverage remain separate
acceptance gates before a training request. The synthetic rehearsal cannot satisfy them.
