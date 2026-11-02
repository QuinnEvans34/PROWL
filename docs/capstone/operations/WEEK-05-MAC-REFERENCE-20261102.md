# Mac autonomous reference — November 2

User authorized the one-case Mac check before restarting KD, explicitly requesting
more than ten minutes if needed. KD remains cooperatively paused at720; its saved
checkpoint/backup are unchanged. No training or label reads are part of this check.

Imported the exact laptop physical cascade/region bridge/access-policy sources and
its focused executor tests from bd0393e without merging the training branch. Added
an MPS launcher with the existing v3 Mac supervisor/guardian and GPU lock.26CPU tests
pass,4Windows lifecycle checks skipped; actual Mac synthetic normal/timeout/cancel
cleanup passed. Initial broader collection encountered a laptop-only verifier-test
import; that unrelated bridge test was not brought into the Mac checkout. No
production dependency or inference failure was hidden by the focused test selection.

Request: /Volumes/PROWL-Data/PROWL/artifacts/week05-mac-reference-20261102-a01/request.json
SHA256:2a0c7bfb09eb53807967ac6efee8d78554fd4b36cf726528a27bad370b75510e.
Only PanTS_00001070; original localizer and selected control20k inference exports;
all-support localization, same physical144/72 pipeline. Request binds code, weights,
recipe, CT/header and runtime. No AMP, MPS CPU fallback, TTA or tuning.

Limits:3600seconds,12GiB owned RSS,6GiB MPS allocation allowance,2GiB outputs and
2GiB independent backup. Mac existing50GB decimal internal/100GiB external reserves
and26GiB total backup cap apply; Windows100GiB internal floor was only a proposal,
not an override of the already approved Mac policy. AC/exclusive GPU gates retained.
Ollama reports no loaded models. Backups go to the independent internal drive.

The laptop's pre-result numerical rule is retained as a conservative engineering
comparison: exact identities/grid/bounds, affine atol1e-5/rtol0, probability
atol1e-5/rtol1e-4, hard-code disagreement<=0.001, finite normalized probabilities
(sum tolerance2e-5), valid codes and no reconstruction gaps. This is not a clinical
accuracy tolerance or evidence of equivalent model quality. Cross-backend float
variation may fail it; preserve that failure and investigate, never relax after
seeing results. No successful comparison is claimed before receiving both outputs.

Launchd label com.prowl.week05-mac-reference-20261102-a01, KeepAlive=false. Initial
registration exited78 before Python/worker launch because of the external log/
working-directory setup; retained initial plist/status. Using the established
internal logs and home working directory started the same frozen request. This
was a pre-execution dispatch repair, not another inference attempt. Supervisor6410
and worker6522 observed live. Do not duplicate or edit producing sources. Completion,
cleanup, exact backups and return transfer must still be checked.

## Completed Mac reference

One inference completed successfully:60physical windows,65.568924seconds inner,
76.563865supervised,1,580,040,192B peak owned RSS and1,726,922,752B sampled MPS
allocation. Worker exited0, reaped, no survivors/cleanup error; GPU lock released.
All12 backup pairs rehashed exactly against the independent internal copies.
Native shape426x301x157/mm; bounds[0,44,0]:[425,301,157], matching Windows.
Prediction SHA6567fe103be9f88ee3f3efd5cd6f8c1643704ad774840de509b0a99a9a265d15
and localizer SHA471a38046762bcf1d58315b6e22228257e6db0e053bf96a2467690aa44854703
are identical to the laptop diagnostic exports. Probability array SHA
37590dc566e466bfb3996bfea5ec3af33d2cc4b56f38cb76cf9bf1bc9bf0f096 differs as expected
for potential floating-point differences; numerical comparison still pending.
No Dice or model-quality acceptance claimed. KD stays paused720 during handoff.
