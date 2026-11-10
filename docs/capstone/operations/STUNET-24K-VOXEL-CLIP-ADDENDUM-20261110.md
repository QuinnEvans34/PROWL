# Separate secondary hypothesis: trim attached overextension

Frozen November 10 before full-cohort tuning results, after the first capacity
pilot case only. This does not modify the live 54-policy producer, its request,
or its policy selection. The secondary screen is reported separately; the
combined prospective search comprises **60 settings**, not 54.

The whole-component 5 mm rule retains an entire blob if any voxel is near the
predicted pancreas. Our earlier visual review identified overprediction attached
to actual lesions. Test whether removing individual distant voxels helps, rather
than assuming that whole-component rejection can address that error.

Exactly six candidates: margin bias 0 / +.5, crossed with voxel-center distance
limits 5 / 10 / 20 mm from the fixed raw predicted pancreas. Full native affine;
missing predicted pancreas fails open. Removed lesion voxels become background.
References are used only for scoring. A real lesion can extend beyond predicted
pancreas, so every original recall, component-identity, small-case and pancreas
guard remains mandatory. No automatic deployment.

Reuse independently reopened finite-margin native codes from the existing
terminal24k study. **No new inference, training or CT voxel reads.** Reopen only
the admitted, source-hashed pancreas/lesion masks for scoring. Retain raw and
fixed5mm controls from the primary screen; verify all references/counts match.

Run only after successful primary completion and reaping, on CPU with a 4 GiB
combined-RSS cap, at most 20 minutes **within the same original four-hour
deadline**, and the same storage/AC/memory floors. No reset, automatic retry,
new GPU owner, replacement model or protected-test reads. Preserve all attempts.
Store per-case metrics and independent backups; 64 MiB metadata reserve covers
both screens. Only complete70/36/34/45/5 denominators permit a conclusion.

Report the best overall candidate and the best guard-qualified candidate across
all60 settings, including gain relative to the standing5mm control. These remain
selection-biased exposed-development observations; a larger search is not new
independent evidence. Log this CPU hypothesis separately in MLflow, excluded
from training hours, with source-code and primary request/result bindings.
