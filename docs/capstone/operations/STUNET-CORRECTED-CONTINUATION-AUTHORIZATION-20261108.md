# Corrected-label STU-Net continuation: user authorization and handoff

Date: November 8, 2026. Execution owner: Lenovo chat, branch
`codex/week05-cuda-readiness`. Mac owns independent review and this handoff.

Quinton's instruction after reviewing the completed analysis was:

> Great, I agree, lets make these fixes, then get it training again.

This authorizes preparation, qualification and one launch of the correction-first
additional 12k phase described in
[the results review](STUNET-RESULTS-AND-NEXT-STEP-20261108.md). The older
analysis-only/no-launch status remains accurate for that completed review but is
superseded for this one newly authorized continuation. This file is authorization
context, not a frozen executable specification, ready receipt or evidence of launch.

## Intended scope

- Parent: `pants_stunet_base_transfer_12k_20261106_launch02`, selected/terminal
  checkpoint12000 SHA256
  `ed000e1ce25829c29f1efea7bf7a5f3684cddf43b0dbcdc5d9f47e8afc8bfa55`.
- Preserve full learned body and output heads. Carry optimizer/RNG/exposure through
  a separately qualified ancestry-aware import; do not relax original restore gates.
- Correct only the seven already adopted upstream annotation errata. All1333train
  cases remain; positivity becomes664/669. CT/pancreas/ordinary labels and70dev
  references stay unchanged. New target/cache and component-focus metadata must
  bind the correction; old cache bindings must fail admission.
- Exactly12,000additional optimizer updates: global12001–24000. Keep architecture,
  loss weights,3:1focus/context ratio, inference and existing geometry policy.
  New deterministic sampling/augmentation addresses rather than replaying12k.
- Recommended LR tail for prospective owner review:500additional-update warmup
  to2e-5, then cosine to0 at the end of the phase. Original LR reached0; a new
  numerical schedule and input identity must be frozen explicitly before execution.
- Six full70case validations at global14/16/18/20/22/24k, checkpoints every500.
  Existing Dice/earlier-tie selection within the new phase; original parent reported
  separately and preserved as fallback. Log class/scale diagnostics as observations
  without changing loss weighting. No protected-test reads or new model downloads.
- This is corrected-label fine-tuning with a new LR tail and more exposure, not a
  duration-only ablation or an independent-patient/leakage-free claim.

## Bounded execution and evidence

Owner handoff requests a40h scientific wall cap: observed29.31h plus20%margin is
35.17h. This is an implementation choice within the agreed additional12k scope;
it does not change update/validation counts. Setup and qualification receive
separate explicit limits in the prospective request, with all attempts charged.
Existing12GiBcombinedRSS/6GiBCUDA, AC, exclusiveGPU,100GiBfree-space floors,
32GiBcombined-cache and64GiBcombined-backup gates remain. No automatic retries,
failure resume, second successor or unbounded engineering loop.

Before launch: publish prospective design; test correction/stale-binding checks;
prove all seven corrected targets and ordinary-target reuse; qualify actual CUDA
parent import/new update and independently backed cold-next-update equivalence;
check a native positive and empty case; verify parent hashes, current storage,
resources, backups and cleanly reaped qualification workers. Freeze source pins
and launch only once after pass. Failed evidence is preserved and reported.

After launch: verify one owned worker, advancing global updates, actual stored
MLflow losses, original-parent binding and independent checkpoint backup. Restore
quiet hourly monitoring for this new identity under the user's standing request;
notify on failure/completion/action required, never automatically restart it.

## Storage review from the existing inventory

**Full-directory admission supersedes the parent-only illustration below.**
Lenovo preflight`a7ff419` establishes that the64GiB gate measures every retained
independent backup under `C:/Users/quinn/PROWL-Backups`; E production artifacts
are not counted again. Current use is67,751,652,648B (63.10GiB). With24newcheckpoint
copies, four conservative qualification copies and64MiB receipts/logs, the projected
total is87,366,699,740B (81.37GiB). This **fails64GiB** even with parent reuse.
Projected physical C free space remains above the unchanged100GiB floor; recheck
at each admission. The actual inventory is in the byte-preserved peer
[preflight](STUNET-CORRECTED-CONTINUATION-PREFLIGHT-20261108.json) and companion MD.

Mac requested explicit human approval for an88GiB C-backup allowance. **Approval
was subsequently granted**, verbatim: "Approve 88 GiB backup allowance."
Apply88GiB only to this new continuation's prospective requests/receipts; the
historical64GiB requests remain unchanged. The100GiBfree floor, memory/GPU limits,
recipe and retained attempts are unchanged. Fresh actual inventory and growth
admission are still required; this approval is not evidence of a running worker.
CPU preparation and bounded qualification may proceed within admitted limits. Parent reuse
avoids redundant files but is not sufficient to clear the full-directory gate.

The completed parent's34saved files total17,000,744,503B per copy. Each mature
checkpoint is698,140,651B. Retaining both parent copies plus24newcheckpoint pairs
projects67,512,240,254B, leaving1,207,236,482B under64GiB **before new journals,
reports and any charged qualification evidence**. Duplicating the parent as a
25th new pair instead projects68,908,521,556B, already189,044,820B over the cap.

Prefer an explicit immutable reference to the existing verified E/C parent pair
for the initial state, with fresh hashes, rather than creating redundant initial
copies. New checkpoints still require independent copies. Lenovo must admit the
actual aggregate inventory and projected remaining growth; this estimate is not
storage clearance. No deletion of old attempts, silent cap increase or missing
backup is permitted. Report a concrete inventory if the existing cap cannot fit.

Source: `STUNET-COMPLETION-20261108.json` backup inventory, imported from peer
`868ded3`; completed analysis main`2e21f54`, omission/proposal main`0c3828e`.
