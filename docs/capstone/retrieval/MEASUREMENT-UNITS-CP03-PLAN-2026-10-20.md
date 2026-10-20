# CP03: CT-linked annotation units and fixed-subset comparison

## Decision before preparation or inference

CP02 selected three positive and three annotation-empty cases before quality inspection.
All 18 original hashes match the current training owner's admitted source identities. Header-only
admission accepts case29; the other five have unspecified mask spatial units. Every mask has the
exact CT shape and affine; there is no observed grid displacement. Case139 additionally exceeds
32M voxels and 128MiB decoded-per-image. CP02 remains an admission-limited attempt, not a completed
cross-case accuracy comparison. No new inference or array decoding occurred in CP02.

Under Quinton's autonomous measurement-comparison request, CP03 introduces only an explicit,
versioned input interpretation: for these hash-bound admitted annotations, an unknown spatial unit
may inherit millimetres from the exact matching CT. This is a declared derivation, not a claim that
the original header contained units. Require matching dimensions and affine exactly, CT millimetres,
unknown mask spatial units, bounded files, and original CT/mask hashes. Reject conflicting units,
NIfTI pair formats, grid disagreement and budget violations. Preserve originals. Stream a private
copy changing only the spatial-unit bits of NIfTI-1 byte123; preserve temporal-unit bits and every
other uncompressed byte. Record both hashes and matching-grid evidence. No resampling, voxel
editing or segmentation correction. Synthetic tests must prove byte preservation and rejection
before any real preparation. Existing production inference and comparison remain unchanged.

## Fixed execution

Retain CP02's six IDs, strata and denominator: positives29/84/927; annotation-empty139/514/698.
No replacements. Case139 remains excluded for size; do not decode or derive it. Reuse case29's
verified prediction/comparison. At most one new inference each for84/927/514/698; no retries.
Use the same raw step6000 checkpoint and unchanged largest-union-26-v1 candidate. Same CP01 screen,
target definitions, metrics and separate empty-reference reporting. No second correction or release.

Sequential MPS float32, existing600s/8GiB worker/32M voxels/64MiB compressed/128MiB decoded-per-image/
132MiB job outputs; cumulative60minute ceiling and2GiB external artifact ceiling,100GiB internal
free floor. Preparation uses streaming1MiB buffers; original/derived hashes checked before inference.
No simultaneous answer generation. New patient artifacts remain on registered PROWL-Data; only
portable code/tests/plans and aggregate result summaries enter Git. No training or protected data.

Inspect every retained case's target/overlap arithmetic, residual lesion components and original
screen failures. Report results with selected6, scored/admitted counts and failure reasons. An
improved metric cannot override another failed screen. This is development diagnosis with provided
pancreas assistance, not independent evaluation, clinical accuracy or reliable-size acceptance.
