# Saved cross-device discrepancy investigation

**The original strict probability gate still fails.** All169 failing values are at
169 distinct voxels that BOTH runs classify confidently as background. None is
close to an argmax change. This is evidence about numerical stability of these
saved predictions, not anatomical correctness, Dice, independent generalization or
permission to waive the gate.

This gate blocks the autonomous four-case evaluation (W05-09/W05-01). It does
**not** block or invalidate the separately running Mac KD treatment (W05-08).
No Mac process, training environment, inference output or tolerance was changed.

## What the saved evidence establishes

Original comparison SHA remains
fd7be15a0745e5acdec22fdf738c9b6d4a95be35dbaaf555fd56906ad083c974.
The new analysis binds/rechecks original reports, probability arrays and failure
coordinates. All169 rows now include every class probability on both hosts,
winner/margin, original native voxel and world coordinates, tile contributions,
distance to ROI/tile faces and distance to another predicted class.

| Quantity | Result |
| --- | --- |
| Failed values / unique failing voxels |169 /169|
| Failed channels |167pancreas,2lesion; none background|
| Winning class at all169 |Background on BOTH devices|
| Winning probability: min / median / max |0.749741 /0.944380 /0.996013|
| Winning minus runner-up margin: min / median / max |0.502727 /0.889637 /0.992030|
| Failed channel probability: min / median / max |0.003983 /0.053655 /0.247014|
| Largest twice-all-channel-error / winning margin |0.000193020; every value is well below1|
| Windows failure-channel values relative to Mac |126lower,43higher|
| All-array mean absolute / RMS difference |4.362794e-9 /1.494764e-7|
| All-array minimum top-two margins, Windows / Mac |1.299381e-5 /1.403689e-5|

The last row matters: near-tie voxels exist elsewhere, but the169 strict failures
are not those voxels. Both full native hard-code arrays and localizer masks are
exactly identical, so there is no observed class flip anywhere in this case.
Background probability can differ while still passing its larger relative-error
allowance; zero failed background channels does not mean background floats are
bitwise equal.

For each failing voxel, the observed class-wise perturbation is far smaller than
half the winning margin. That directly explains the unchanged argmax for this
pair of outputs; it is not a bound on future executions or other cases.

## Spatial location and confidence

Failures occupy19connected clusters using26-connectivity, with largest sizes
83,27and25voxels. Their closest-RAS ROI coordinate bounding range is
[77,70,0] through[323,141,154], inclusive. They are not all on a crop or tile edge:
3touch an ROI face;18are within one fine-grid voxel of a contributing tile face.
Median nearest tile-face distance is12fine voxels; contributions range2–9tiles.
Median ROI-edge distance is16native voxels. This distribution does not establish
or rule out a blending contribution, but it contradicts an all-failures-at-edges
explanation.

Distance to the nearest differently predicted ROI voxel center ranges0.666–19.360mm
(median3.396mm). This is a distance to the MODEL'S class map, not to annotated anatomy.
Spatial closeness to a predicted boundary is distinct from a small class-score margin.

The two lesion-channel failures are neighboring ROI voxels[297,91,154] and
[298,91,154]. Mac lesion probabilities0.09816694 and0.12362415 differ from Windows
by2.195686e-5 and2.339482e-5. Their background probabilities are0.88597375 and
0.86238986, with winning margins0.78780682 and0.73876572. Neither becomes a lesion.

Worst tolerance ratio occurs at ROI[94,92,16], source voxel[331,164,16]:
pancreas probability0.0762057379Windows versus0.0762429535Mac. Absolute error
3.721565e-5 exceeds allowed1.762429e-5 (ratio2.11161); background still wins with
probability0.91645437 on Mac and margin0.84021142. The maximum absolute error over
ALL probabilities remains4.851818084716797e-5, not necessarily this worst-ratio row.

## Arithmetic and implementation review

- Re-evaluating the original atol1e-5 + rtol1e-4*abs(Mac) formula in float64 on
  the saved float32 values still produces exactly169failures. Reversing which
  saved side supplies the relative term also yields169. Comparator subtraction,
  float32 threshold rounding and reference-side asymmetry do not explain away the
  failed count. This audit does not replace the original comparison.
- Exact CT and weight identities, class order, native grids/transforms, all-support
  localization, ROI bounds, tile grid and core source equivalence were established
  by the retained comparison. Saved outputs were reconciled with their own argmax
  and embedding; finite/normalized checks and zero-gap checks passed.
- Repository code clips/normalizes the segmenter CT using NumPy, constructs
  integer-subdivision geometry, uses SciPy linear sampling with nearest boundary
  mode, executes float32 SegResNet and Torch softmax, then accumulates triangular
  weights and resamples probabilities to native centers on CPU. Several numerical
  stages therefore precede the final arrays.
- The Windows installed MONAI source confirms GroupNorm/Conv3D with nontrainable
  upsampling, linear/trilinear interpolation and align_corners=False. CUDA TF32 is
  explicitly disabled in the frozen worker; no AMP/TTA or optimizer is used. The
  inference loader uses weights_only and strict full state loading; unrelated
  legacy transfer-loader functions are not called by this worker.
- Torch2.11.0+cu128 vs2.13.0, MONAI1.6.1 vs1.6.0, NumPy2.5.2 vs2.5.1 and
  SciPy1.18.1 vs1.18.0 differ. Mac installed implementation snapshots and per-tile
  inputs/logits were not retained in this packet. Repository source agreement is
  not evidence that installed library kernels or intermediate float arrays match.

PyTorch documents that floating-point operation ordering and platform/release
differences can change numerical results. That makes such variation plausible;
it does not identify the cause here or make our agreed gate optional.
[PyTorch numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html).

**No saved-evidence bug was found that justifies changing the comparator or
reclassifying the original failure.** Preprocessing/library, forward-kernel,
softmax and CPU reconstruction contributions remain unseparated because the
intermediate values were not saved. No specific backend or release is blamed.

## Smallest proposed next qualification — not executed

Prefer **one fresh Windows diagnostic in an isolated runtime matched to the Mac's
recorded library versions**, compared against the SAME retained Mac result. This
avoids another Mac GPU run and leaves ongoing KD untouched. First confirm compatible
CUDA wheels/driver support; do not silently substitute versions or modify the live
training venv if matching versions are unavailable.

1. CPU-only prepare: freeze the separate environment, exact model/CT/source/config
   identities and original numerical rule; run existing focused CPU checks. Verify
   matching installed model/preprocessing source or document remaining differences.
2. Add a separately versioned, synthetically verified trace-only wrapper. During
   that single full60-window diagnostic, retain inputs and pre-softmax logits for
   two predetermined windows: fine-grid origins[0,0,0] and[216,0,170]. These cover
   the worst-ratio and largest lesion-channel failure, selected by nearest tile
   center with lexicographic tie break. Capture them during the ordinary forward
   calls, not additional forwards. Preserve probability export and operation order.
3. Run the single1070diagnostic once under existing Windows ownership/cleanup gates;
   compare its complete native outputs and ALL three probability channels to the
   retained Mac output. Do not use just the two probes to claim whole-case parity.

Acceptance: exact identity/grid/bounds; affine atol1e-5/rtol0; zero reconstruction
gaps; finite normalized probabilities within2e-5; all51,444,975 values meeting
atol1e-5/rtol1e-4; hard disagreement<=0.001; exact output/backup identities;
successful cleanup. Keep the original failure permanently recorded regardless of
the new result. A pass qualifies only the newly frozen matched-runtime pipeline;
a failure stops again, with the new intermediate evidence available for diagnosis.
No automatic retry, scope expansion or tolerance change.

Budget proposal: one Windows inference attempt,600seconds wall including startup,
12GiB owned RSS,6GiB GPU reservation,2GiB output and2GiB independent backups;
existing40GiB combined backup and100GiB C/E free-space floors. Tracing adds about
96MB for two float32 inputs plus three-channel logits, within the2GiB envelope.
Observed full diagnostic costs were89.4sWindows/76.6sMac including startup;
estimate **2–5minutes for the new Windows run and comparison after setup**, with
the600s hard inference ceiling retained. Environment installation/availability is
separate and not yet measured; do not promise this estimate includes downloads.

This is a proposed NEW qualification, not authorization inferred from the current
saved-output investigation. No environment installation, new model inference,
four-case batch or training was performed. If a matched runtime cannot be prepared,
return that concrete dependency rather than extending to many backend sweeps.

## Evidence

Additive CPU helper: scripts/diagnostics/analyze_week05_saved_differences_20261102.py.
Owned48000 exited0;9.094supervised seconds,1,327,501,312B peakRSS,workers reaped.
Evidence E:/PROWL/readiness/week05-saved-difference-review-20261102-a01 contains
request.json,analysis.json (all169expanded rows),spatial-and-probes.json and installed
source hashes. Input files were hashed before and after; original pins/outputs
are unchanged. Original comparison, tolerances and failed evidence remain preserved.
