# Mac teacher pilot failure diagnosis

October23. CPU metadata/synthetic checks and review of saved first-case output.
No new teacher inference, student update, cohort audit or scientific launch.
Original pilot/source snapshot and failure remain unchanged.

## Coverage failure reproduced

The current resampler retains the origin/direction but rounds `size*spacing` at
1mm spacing. This can leave a native voxel centre outside the resampled grid's
half-voxel boundary. Corner transforms from the transferred source/region affines
reproduce the failed PanTS_00003615 edge: native teacher-index222.656393 on a223-voxel
axis, beyond the allowed222.5 by0.156393mm. PanTS_00005832 would also fail, by0.320313mm.
The other10 pilot regions pass this metadata coverage calculation.

Three synthetic tests pass: metadata grid agrees with actual SimpleITK geometry
for both source orientations; rounded-size edge loss is reproduced. A prospective
centre-covering grid `ceil((n-1)*s/t)+1` covers all12 regions in metadata. This is
NOT an approved or executed preprocessing revision. It also changes some dimensions
by removing existing excess extent. A minimal future correction should preserve
old extent while adding required samples; it must be explicitly versioned and
checked for full source coverage, interpolation, normalization and teacher behavior.
Do not loosen the reconstruction gate, zero-fill missing probability, or drop cases.

An initial suspicion that upstream ignored interpolation was disproved by executing
only its pinned resampling helper on synthetic data. Linear/nearest/B-spline inputs
produce different outputs. There is no demonstrated interpolation-argument bug.
`geometry-failure-review-01.json` preserves these findings, including the negative
result and unapproved candidate projection.

## First case: overlap does not mean a useful outline

Actually inspected `PanTS_00002720.png`. Across its three displayed planes, small
yellow teacher contours occupy only small parts of the large red annotation. No
obvious gross alignment reversal is visible, but these views are not full-volume
or physical-aspect-ratio review. The PNG displays voxel indices with equal pixel
aspect; anisotropic spacing distorts physical proportions. Future review figures
should display physical aspect correctly without changing data or inference.

The saved native probability cache and two hash-verified training masks were read
(no CT voxels or model loads). One lesion component:189,621 voxels;5,858 eligible
positive-KD voxels (~3.09%);120,342 (~63.46%) at q<=0.1. None of the background or
pancreas voxels reach q>=0.9. Quantized probabilities imply rounding uncertainty
near thresholds; these bands are descriptive, not calibrated confidence. The
reported original Dice0.0599/recall0.0309 remain unchanged. Do not attribute this
underprediction to the second case's geometry failure: the first region had
complete reconstruction coverage. Teacher usefulness is not accepted.

Evidence: `first-case-probability-review-01.json`; partial observations and image
hash entered in the existing pilot-review record. `reviewed` remains false because
full component/extent review is incomplete.

## Supervisor evidence is incomplete

No pilot process remained at inspection, and the original exec session is no
longer available. There is no supervisor `resources.json`; cause of supervisor
exit cannot be established from these artifacts. The worker traceback establishes
its geometry exception only. Do not reconstruct resource peaks or a reaping receipt.

Code inspection identifies a lifecycle weakness: the worker is launched in a new
session, and cleanup/reporting live in the supervisor's try/finally. Abrupt loss
of the supervisor can bypass that path and leave the worker without its watchdog.
This is a risk identified from code, not proof of the historical exit mechanism.
Before another real run, qualify a durable supervisor with persisted PID/start
identity, signal-triggered cleanup, worker parent-liveness checks, and atomic
terminal status. Test normal exit, worker failure and supervisor interruption using
short synthetic workers; SIGKILL cannot run finally, so parent-liveness behavior
must be tested separately. Keep owned-process targeting and existing resource caps.

## Next bounded correction

1. Implement/test an additive coverage-preserving resampling policy and fail-fast
   metadata coverage preflight before expensive inference. Preserve originalpolicy.
2. Qualify interruption/cleanup reporting with synthetic processes and correct
   review-image physical aspect. Do not edit the failed pilot's source pins.
3. Present a new bounded pilot request only after these checks. Preserve the same
   cases/order and old failure. Geometry success alone will not establish teacher
   usefulness; review the first-case underprediction separately.

No automatic retry was launched. No full cache or scientific run is ready.
