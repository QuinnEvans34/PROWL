# D-296 — tiny-reference resampling investigation

## Finding

The D-295 losses reproduce exactly and respond strongly to target-grid spacing. Both affected source
grids are isotropic1.5mm. Nearest-neighbour conversion to3mm loses small boundary detail; restoring
that coarse label cannot reconstruct all original foreground. Native1.5mm conversion/restoration
is exact for both cases, supporting a coarse-representation explanation rather than a gross source-grid
orientation/restoration defect. This two-case result does not prove that every other grid is correct.

No CT files or model weights were read. Only the two qualified pancreas labels were read under a new
single-use request:46,320compressed /10,503,092expanded bytes. The diagnostic reused preprocessing
geometry with a zero CT surrogate. It does not establish real-image parity for a new recipe.

## Exact comparisons

Metrics compare supplied labels with resampled/restored labels, not model predictions. Original
source labels and cohort membership are preserved. Native evaluation truth must remain unchanged.

| Case | Method / spacing | Source-reference recall | Precision | Dice | Restored/source volume |
|---|---|---:|---:|---:|---:|
|6110 train |Nearest3mm baseline|0.45956|0.87413|0.60241|0.526×|
|6110 |Foreground-center splat3mm|1.00000|0.36757|0.53755|2.721×|
|6110 |Nearest2mm|0.90441|0.68524|0.77971|1.320×|
|6110 |Nearest1.5mm|1.00000|1.00000|1.00000|1.000×|
|2727 development-validation |Nearest3mm baseline|0.76471|0.39000|0.51656|1.961×|
|2727 |Foreground-center splat3mm|0.94118|0.36364|0.52459|2.588×|
|2727 |Nearest2mm|0.88235|0.95745|0.91837|0.922×|
|2727 |Nearest1.5mm|1.00000|1.00000|1.00000|1.000×|

Case6110 has272 source foreground voxels (918mm³), across native Z indices87–90 with counts
14,14,122,122. Its last source index is90: the reference reaches the acquisition boundary. The3mm
baseline loses147 source foreground voxels;2mm loses26. Case2727 has51 source foreground voxels
(172.125mm³), all on native Z index110, the final source slice. The3mm baseline loses12;2mm loses6.
These are supplied visible references, not evidence of full-pancreas coverage.

The splat experiment maps each foreground voxel center to its nearest coarse-grid voxel. It is not
voxel-volume occupancy, not an expert correction, and does not guarantee full native recall (2727
still misses3 voxels). Its large added foreground makes it unsuitable as an unexamined quick fix.
Recall alone would conceal that tradeoff, especially given CAP-EXP-006's earlier coverage/size issues.

## Resource implications from retained geometry only

No additional source reads were needed to project all153 frozen members. Conservative dimensions
include the existing minimum96 padding plus the existing2-voxel projection allowance.

| Uniform spacing | Maximum conservative output voxels | Cases above current8M cap | Image+uint8-label payload upper bound |
|---|---:|---:|---:|
|3mm|4,539,150|0|1,187,121,715bytes (1.11GiB)|
|2mm|15,045,810|15|3,220,120,620bytes (3.00GiB)|
|1.5mm|35,265,440|60|7,350,756,385bytes (6.85GiB)|

These are geometry/payload projections, not measured process RAM or MPS allocation. Neither finer
spacing fits the current8M output policy for every member. Native1.5mm identity here is expected for
these two matching source grids; it does not mean1.5mm is lossless for every source spacing.

## Recommendation and bounded next step

**Qualify a uniform2mm candidate before connecting the final broad training cache.** It improves both
observed failures substantially without the large target inflation of center splatting, and its
projected payload is smaller than1.5mm. This is a candidate to investigate, not an adopted recipe or
proof of better learning. Preserve the3mm baseline and all153 cases. Do not choose spacing per case
based on these outcomes or remove difficult members to fit a resource limit.

The next implementation should:

1. Add a separately versioned candidate recipe/output envelope (at least the measured15.046M
   conservative maximum; propose16M), preserving source96M and original native evaluation labels.
   Run synthetic largest-output interpolation/restoration and native-image/target-independence checks.
2. Freeze a new bounded qualification request. Recheck all153 target transformations/geometry and
   resource accounting under that candidate, with explicit attention to tiny references and large
   outputs. Existing D-295/D-296 requests are consumed. Validate image-only parity before creating a
   training cache; a label-only probe is insufficient for that claim.
3. Compare retained3mm and candidate2mm fidelity across the unchanged cohort, including worst cases,
   partial-coverage strata, target survival and size inflation. Record any vanished target as a
   failure, not permission to omit it. No universal Dice threshold or eligibility change is introduced.
4. If the candidate passes, explicitly record the uniform recipe choice and resource limits; then
   complete role-safe cache/no-update MPS profiling and checkpoint/backup binding. Training remains
   a new bounded experiment with separate launch identity. If the resource envelope fails, preserve
   that evidence and consider a different implementation or target design without filtering cases.

Case2727 belongs to development-validation and has now been used for preprocessing debugging.
These comparisons must not be described as sealed-test evidence or unbiased generalization estimates.
No threshold/model/loss tuning, clinical interpretation, or expert annotation certification occurred.

## Implementation, verification and retained records

Added `src/data/target_fidelity_diagnostic.py`, `scripts/diagnostics/target_fidelity_probe.py` and
`tests/test_target_fidelity_diagnostic.py`. Production loaders/recipes are unchanged. Five new tests
cover native-grid boundary recovery with a flipped affine, affine-aware center mapping, out-of-grid
refusal and metrics that distinguish added foreground from missed foreground. Native full suite:
**1,312 passed,2 existing warnings,35.86s**. `git diff --check` passes.

Supervised real-label job:11.806s,peak1,348,894,720bytes (1.26GiB),exit0,zero CT files/updates.
Exact baseline reproduction and source identity/byte totals were required. Result receipt entries
were independently rehashed after completion. No failure/retry or active process remains.

- Exact consumed request: `outputs/prowl/target-fidelity-request-0087caaf-d7e4-4145-a183-fc20c8501ec8/`,
  SHA256 `cc090d13c6ab35b38065c497c5eb7e88522df9b27bc14e9ab4a6b16353985c6e`.
- Result: `outputs/prowl/target-fidelity-42c58b94-4cb5-40dc-9566-94e788e472a6/`,
  receipt SHA256 `3197396615701525469f0ee3d1be5a769723cbfae6be90c898e48f384eebb7d5`.
- Review, projected sizes for every case, replay script and native test logs:
  `outputs/prowl/target-fidelity-review-20260929/`,
  receipt SHA256 `b883a38699ee903a9327003bc8aa0ac08e03032de4c6ba2131f2843e2b05bdc3`.

All paths above are relative to the repository root. D-294 qualification,23 holds, historical16/11
runtime and Claude's retrieval lane are untouched. No new training launch request is prepared.
