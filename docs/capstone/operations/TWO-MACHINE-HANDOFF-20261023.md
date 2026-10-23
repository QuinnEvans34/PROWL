# Two-machine source handoff — October 23, 2026

The user requested publication of all pending laptop source work to main and
discussion of parallel experiments. This is not authorization to launch a second
scientific run. Windows remains on its frozen training checkout; integration was
performed in a separate checkout without changing its producing files.

## What a pull transfers

Source, tests, experiment specifications and written results are versioned.
CTs, masks, caches, teacher weights and external licensed teacher source,
checkpoints, detailed local readiness evidence, MLflow SQLite databases and the
phone dashboard installation outside this repository are not transferred by Git.
Windows absolute paths and readiness receipts are not portable Mac launch receipts.
Acquire or privately transfer required assets with identities and roles preserved;
reuse existing overlap/coverage evidence, not another duplicate-data audit.

## Recommended parallel work

Prioritize exploratory knowledge distillation on the second machine while the
current Windows varied-focus experiment finishes. Start with environment and
bounded teacher/student pilot qualification, not a scientific training launch.
Read MACHINES.md and the teacher-distillation plan and review protocol first.
The current new-path qualification is Windows/CUDA-oriented; Mac/MPS execution,
operator support, restore behavior, runtime and memory are unverified.
Do not bypass the Windows pilot's active-parent guard; create a separately scoped
Mac qualification with its own resource budget and evidence if approved.

For a causal KD comparison, use a matched no-KD control on the same backend and
recipe, or explicitly report cross-backend comparisons as exploratory and
confounded. Keep cohort roles, native evaluation and checkpoint selection fixed.
Teacher membership remains unknown: no independent-generalization claim.
Separate machine-tagged artifacts, MLflow run IDs and local tracking stores;
never share a live SQLite file or have two writers use the same cache/checkpoint.

The false-positive verifier remains a separate future experiment. It requires a
frozen segmenter and leakage-safe out-of-fold/calibration candidates. It cannot
recover lesions absent from the segmenter's candidates. Parallel engineering is
possible, but the existing sequential experiment plan has not been rewritten or
launched by this Git handoff.

No scientific job, paid completion polling or automatic handoff was started.
