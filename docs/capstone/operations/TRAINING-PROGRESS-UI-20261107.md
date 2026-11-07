# Training results and saved-export freshness

W05-10 adds aggregate experiment progress to the existing `/training` page while
the Lenovo STU-Net run continues. This is a read-only result consumer, not a
trainer, scoring policy, independent model comparison or live remote connection.

## Input and source

`configs/training-progress/lenovo-stunet-20261106.json` is copied byte-for-byte
from Lenovo commit `1753ae4`,
`docs/capstone/coordination/LENOVO-STUNET-PROGRESS-20261107.json`.
SHA256: `664535b2116b22bdf49ea85bc92457152dd830305145c398490eced023184163`.
It records an observation at 2026-11-07T18:51:06.339094Z, 6,814/12,000 updates,
and three completed native 70-case validations at 2k/4k/6k. This observation is
historical as soon as training advances; it is not a live step counter.

The `prowl-training-progress-v1` contract allows only declared aggregate fields:
source/run identity, UTC observation time, run phase/steps/runtime, cohort counts,
optional in-progress validation counts, and completed validation points. Lesion
DICE is the macro mean over 36 positive cases; pancreas DICE averages all 70;
detection means lesion overlap; false alarm means any predicted lesion on the
34 reference-empty cases. The metric definitions were checked by Lenovo against
the producing summaries. No scans, masks, probabilities, case IDs or private
paths are imported. Unknown fields are rejected.

The validator rejects nonfinite/out-of-range scores, inconsistent denominators,
partial results in the completed curve, missing/duplicated/reordered scheduled
points and unsupported scope. Same-run refreshes cannot rewrite old scores,
change the frozen receipt/cohort or move progress/time backwards. An explicit
new execution identity may replace the displayed run; its curve is never joined
to the previous execution. This contract currently supports only the declared
provided-pancreas exploratory scope with unresolved pretraining exposure.

## Local operation

The Vite development endpoint `/training-progress` reads the retained snapshot.
To read a newer separately delivered, sanitized JSON export, set
`PROWL_TRAINING_PROGRESS_FILE` to its local path before starting Vite. Only this
operator-controlled path is accepted; URLs, query parameters and request bodies
cannot select a source. Files are limited to 128 KiB and parsed/validated before
publication. GET and HEAD are read-only; other methods/paths are refused.

An invalid, unavailable or regressed export retains the last admitted snapshot
and returns an explicit note. Reading a file or refreshing the browser does not
advance its observation time. The browser checks for a newer local export once
per minute, with nonoverlapping requests, timeout and unmount cancellation. It
retains valid results on endpoint errors. Static builds use the retained export
when no development endpoint exists. No network fetch to Lenovo, source timer,
Git auto-pull, extra scientific job or training-hours entry is installed.

## Presentation and limits

Show completed lesion/pancreas DICE curves and a full accessible table, latest and
best completed lesion scores, validation progress and detection/false-alarm
denominators. The next incomplete validation has no invented score. A new run
without a full validation says that results are pending rather than showing zero.

Every state says **at last observation**, identifies the source time and age, and
labels data older than 15 minutes as an older saved observation. A source clock
more than five minutes ahead is flagged as uncertain. Neither age threshold is a
training stall detector. The panel does not infer whether a host is connected or
whether an observed worker still runs. Existing session accounting remains
separate; displayed run elapsed time is not added again to its totals.

The exploratory/provided-region limitations stay visible. Best means highest
completed lesion DICE so far, not a final model-selection decision. No clinical,
autonomous, independent-test, pretraining-gain or practical-acceptance claim follows.

## Verification

Focused contract, endpoint and React tests cover complete/partial/empty curves,
source age/clock skew, immutable results, failed/oversized/invalid reads, request
path/method refusal and late response isolation. Existing accounting tests remain
in the verification command. Build and browser inspection are recorded after
completion in the Mac handoff; fixtures are engineering evidence, not new model
evaluation or participant feedback.
