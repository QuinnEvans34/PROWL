# PanTS coverage preserving intake implementation plan

## Objective and authority

Restore full annotated lesion field coverage, preserve useful spatial detail and verify the
actual model inputs before the next scientific experiment. This plan authorizes implementation
and bounded intake qualification under the user's October18 request, not a long training launch.
It is a staged implementation plan, not yet a frozen scientific recipe or a claim of readiness.

## October18 implementation candidate freeze (before real pilot)

Preliminary native-windows-1 pilot (a01) completed12/12, exact oracle reconstruction,
148.94supervised seconds,2.46GBpeakRSS,workersreaped. Before complete-cohort qualification,
strengthen the sampling gate: native-windows-2 (a02) cycles guaranteed whole-annotation
bounding-field cover windows before component-jitter windows; every fourth visit remains
uniform CT. On reference-empty cases, cover the entire provided pancreas and use one
pancreas anchor. Measure actual union coverage over18visits and require100% of annotated
lesion voxels (or pancreas for empty cases), not just component-center exposure. All671
training lesion bounding boxes require at most2cover windows at144native voxels. a01
producing sources/results retained separately; a02 repeats the bounded pilot for changed
sampling, not dataset admission or duplicate research. This amendment supersedes the
component-only sampling text below. Native spacing/inference design remain unchanged.

Stage1 completed671/671:43clipped,22below90%coverage,10below50%; minimum3.0675%.
Evidence: `E:/PROWL/readiness/training-coverage-inventory-20261018-a01/results.json`.

Candidate `native-windows-1` supersedes the provisional1mm resampling design below:
retain acquired spacing and obliquity, with lossless closest-RAS permutation/flips only;
144cubed windows,72voxel stride, edge-anchored final windows, high-side zero padding only
when an axis is shorter than144. Full CT inference tiles depend only on CT shape, never
pancreas or lesion labels. Blend softmax probabilities using strictly positive separable
triangular weights (floor0.001), then argmax and invert the lossless axis transformation.
No full resampled cache: load one case on demand, retaining original data/cache unchanged.
HU[-100,250], previous augmentation, architecture, loss and optimizer stay unchanged.

Tradeoff: exact acquired detail and100%field support at modest disk cost, but variable
physical field of view and no new through-plane detail. Overlapping windows do not give
the network whole-organ context in a single forward pass. Full-CT inference also changes
background distribution versus the former provided-pancreas crop. This is a bundled
input/coverage intervention, not a pure causal test of cropping alone or promised Dice gain.

Training retains seeded full-cohort case permutations. Within each case, three visits use
round-robin actual lesion-component voxel anchors (provided-pancreas component anchors for
reference-empty cases), then one visit samples a uniform full-CT window. Seeded jitter keeps
the anchor inside the patch. All source components remain available, and component exposure
is measured over18visits, the minimum case exposure in a24k/1333case run. This does NOT claim
every lesion voxel is seen during those18visits or that a large lesion fits one patch.
Inference never uses these training-only anchors. Audit failures remain visible.

Pilot reuses the12previously selected training cases without development-driven reselection;
it includes the severe known clipped case and tiny12voxel lesion. Worst inventory cases are
also covered in the later complete intake audit. Gates: exact native target round trip,
all components retained, physical alignment, gap-free full-field tiling, deterministic
component exposure, measured resources and visual inspection. Readiness is not yet asserted.

The prior augmented run and all original source data, cache, roles, model weights, reports and
tracking histories remain immutable. Lower learning rate follows the coverage experiment rather
than being bundled into it. No PANORAMA, duplicate rediscovery, protected-test reads, source-label
edits, automatic exclusions, automatic retries or scheduled AI monitoring.

## Order and completion gates

| Order | Work | Required evidence before advancing |
|---|---|---|
| 0 Now | Preserve reference and identify exact source masks | Baseline selected18k/native0.4237607557, final24k/native0.3937226670; approved cohort and source hashes; no active producing job modified |
| 1 First | Training-only coverage inventory and annotation linkage | All671positive training masks accounted for, hash/geometry/semantic checks, complete native lesion count inside/outside original box, bounding extent and required symmetric margin, failures retained |
| 2 After inventory | Select the representation and quantify resource cost | Written policy decision using training geometry only; coverage/resolution/patch exposure/storage/GPU tradeoff; review any source ambiguity; freeze candidate parameters before development qualification |
| 3 After policy freeze | Implement a versioned loader and native reconstruction | Synthetic affine, clipping, sampling, padding, tiling and role-isolation tests; old path unchanged; deterministic saved identities and transform records |
| 4 Before cohort preparation | Bounded real-data pilot | Reuse12selected training cases, include worst coverage/extents; original-versus-new overlays and round-trip metrics; measured time, RAM, disk and GPU cost |
| 5 Only after pilot passes | Prepare and verify new intake separately | All1333training and70development cases accounted for; no missing/wrong-role data; full-field support and fidelity checks; no silent exclusions; development outcomes do not tune per-case geometry |
| 6 Before readiness receipt | Exercise actual training and inference paths | At most4nonpromotable CUDA updates and1cold next-update check; deterministic restoration, valid loss/gradients, correct native reconstruction, independent backup and worker cleanup |
| 7 Before scientific launch | Review and freeze | Human-readable evidence report, exact config/code/cohort/cache hashes, MLflow/dashboard registration plan, resource budget and explicit readiness result; discuss findings with Quinton |
| 8 Separate launch approval | Coverage experiment, then LR experiment | No long run starts from passing engineering tests alone |

A failed gate stops advancement. Preserve evidence and explain the failure; do not silently raise
limits, rerun failed work or replace a missing case. If a necessary choice changes the scope,
return to Quinton with the options before proceeding.

## Timing and progress

The inventory is first and should be measured before estimating the rest. Its initial bound is
30minutes,8GiBprocessRSS,100GiBfreeC/E and64MiBoutput; it reads compressed labels, not CTs.
Typical expected effort for this metadata/label stage is minutes, not a multi-day data audit,
but the bound is not a promised completion time. Publish actual completed counts and elapsed time.

Implementation and synthetic checks follow the policy decision. Real-data preparation ETA must
come from the pilot's measured per-case cost and projected disk use, not an invented fixed number.
GPU qualification is last. Give a revised ETA after stages1and4, identifying CPU/IO preparation
versus GPU work. Do not claim the entire fix is complete while later gates remain pending.

## Stage 1 source and coverage measurements

Reuse admitted1333training/70development roles and the five existing exclusions. Only671positive
training lesion masks are newly read in the inventory; prior27-case diagnostic remains evidence,
not permission to select policies from individual development labels. Confirm the known clipped
case's lesion file is the manifest's pancreatic-lesion file and matches the original source hash.
The approved semantic binary decoder applies NIfTI scaling; never interpret publisher class28
as the foreground value in a separate binary file. Existing publisher-provenance review is reused.
Byte/semantic linkage does not establish radiologist correctness of an unusual contour.

For each mask record original lesion voxels, original-box retained voxels, fractional coverage,
native lesion bounding box, source spacing and a sufficient native-axis symmetric margin from
the pancreas bounding box. Derive the latter using the existing margin-zero selection rule on
the pancreas mask if required; do not infer it by subtracting10mm from a source-clipped box.
The first inventory may report required extra margin beyond the existing box instead: label
that metric explicitly and do not conflate it with total pancreas margin.

Determine whether clipping is isolated or distributed. Any unexpected mask identity, target
state, component total or affine mismatch is a hard stop, not a reason to normalize it away.
Do not reclassify unusually large lesions as erroneous from appearance alone. Ask for qualified
review only when source/geometry evidence cannot resolve a material ambiguity.

## Candidate representation to qualify

Preferred technical direction is full retained native CT field on a fixed physical grid, with
overlapping3Dwindows where a whole region exceeds memory. This avoids a lesion-dependent
inference box and squeezing every large region into144cube. Retaining all acquired CT support
does not restore anatomy outside the acquisition. No body-mask or intensity-threshold cropping
may silently remove field support.

Candidate starting settings are1mmRAS sampling,144cube windows and50%inference overlap with
weighted probability/logit blending followed by one final classification. These are pilot
settings, not frozen commitments. Preserve source anisotropy in evidence: interpolating thick
slices to1mm does not create new acquired detail. Prefer one direct source-to-working-grid
resampling over source→1mm→fitcube. Score predictions against unchanged original native masks.

Training may use annotation-guided window sampling; inference window placement must depend
only on CT geometry and a fixed rule. Design a deterministic schedule that gives every lesion
component exposure and retains reference-empty cases/background. A case remains the role and
sampling identity; record window origins, sampled physical volume, component exposure and padding.
Do not pretend one patch is a full patient, or that independent patches share global context.
Whole-pancreas views can be considered if they fit, but adding a second scale or sampling mixture
is another explicit component of the representation policy.

Before implementation freeze the exact spacing, patch dimensions, window starts/edge handling,
overlap/blending, padding/loss support, training window probabilities and deterministic exposure
schedule. Hold the same model, originalSuPreM+freshheadseed42,augmentationpolicy,DiceFocal,
AdamWLR1e-4/weightdecay1e-5 and24k horizon where feasible. If grid or window policy invalidates
the current augmentation assumptions, version/test the changes and disclose them rather than
claiming identical numerical inputs.

If full-field storage or inference is infeasible, stop for a policy decision. A train-derived fixed
pancreas margin is a lower-cost alternative but cannot guarantee unseen lesion coverage. Do not
silently fallback to a GT-lesion box on development. No enlarged-field fit-to144 shortcut.

## Quality acceptance contract

Hard conditions before readiness:

- Exactly the intended cases and roles; masks, CT and transforms resolve to pinned sources.
- No nonfinite CT, invalid label codes or unmatched CT/label grid under the existing contract.
-100%native annotated lesion field coverage across the retained region or exhaustive inference
  window union. Check physical voxel-cell extent at edges, not just center coordinates.
- No original lesion component disappears entirely on the working grid or from the guaranteed
  training exposure schedule. Partial training patches are allowed; dropping a component from
  the entire case's available training views is not.
- Every reconstructed voxel in the retained field has nonzero aggregation weight; no uncovered
  seams, axis swaps, padding offsets or silent outside-box-zero shortcuts.
- Original reference masks remain full native volumes; never shrink the reference to match input.
- Memory, free-space, output and runtime limits respected; no unrelated processes affected.

Detail measurements are separate from coverage. Record per-case lesion round-tripDice/recall,
volume change and component counts, stratified by lesion size; record pancreas fidelity as well.
The proposed screening rule is manual engineering review for round-tripDice<0.90, recall<0.90,
or a >0.01Dice deterioration from the existing fully covered training representation. These are
engineering review triggers, not clinical cutoffs or automatic exclusions. Investigate tiny
lesions explicitly. Any exception must name its cause, retained evidence and user disposition;
unresolved failures cannot be labeled qualified. Freeze these gates before candidate pilot results.

Visual pilot shows exact tensor pixels, native image/labels and reconstructed targets in matched
physical planes with aspect ratio/orientation labels. Inspect small lesions, giant lesions, thick
slices, oblique scans and volume boundaries; show padding separately. No synthetic images.

## Engineering and resource verification

Unit tests cover nontrivial affines, tilted scans, anisotropic spacing, lesions crossing oldbox
and window boundaries, small/disconnected lesions, empty labels, source-edge coverage, uniform
predictor reconstruction, interpolation semantics, deterministic sampler/RNG and protected roles.
Add a regression that fails under old11.63%coverage acceptance and passes only when alloriginal
annotated field is available. Compare candidate image/target geometry with known physical points.

Use separate versioned output/cache paths and atomic writes with source/code/config hashes.
Do not delete old cache or checkpoints for capacity. Before full preparation, calculate proposed
cache size against existing32GiBcachecap and100GiBdrivefloors; if not feasible, choose a tested
bounded-memory/on-demand strategy or ask to change the storage budget. Existing27,917,287,424byte
backupcap remains. No silent resource-limit increases. CUDA smoke must fit8GiBdevice and12GiB
workerRSS, under an explicit bounded supervisor with AC and process cleanup.

The GPU smoke creates nonpromotable diagnostic weights only. Check finite loss/gradients,
optimizer involvement, exact restored state and next-update tolerance(rtol1.3e-6/atol1e-5),
E:/C:backup agreement and reapedworkers. Full scientific training is not a quality test.

## Scientific interpretation and record keeping

Human run title: **Preserve the full lesion field without squeezing away detail**. This is a
bundled input-representation experiment if sampling/resampling/inference change together.
H0 native selected-checkpoint Dice improvement<=0;H1>0 relative to the augmented18kselected
control(.4237607557). Proposed acceptance:delta>=.02,paired95%lower>0,detectiondelta>=-.03,
alarmdelta<=+.03,pancreasdelta>=-.02,no greater empty predicted-lesion-voxel burden. Mandatory
final24kcomparison uses the oldfinal.3937226670; it cannot replace the primary. Freeze bootstrap
seed and selection rule before launch. Preserve all70referencecases, including misses.

With changed inference field, report the old immutable endpoint and consider an explicitly
secondary common-inference comparison to separate training changes from inference effects.
Do not assume fixed24ksteps gives equalvoxel exposure or runtime; report both. Retain original
model/artifacts regardless of result. Development reuse remains exploratory, not a cleanbenchmark.

Each gate produces a dated result/decision and source hashes in private readiness storage.
Append concise outcomes to experiments.md and AGENTS.md. Log engineering work as diagnostics,
not fake scientific RUNNING entries. The eventual run uses liveMLflow and the existing private
dashboard only after its receipt and explicit launch approval. Images remain private.

## Current status

Plan recordedOctober18. Source linkage for the clipped example resolves to its admitted
`pancreatic_lesion.nii.gz` file, not another organ mask; the focused review already verified
the hash and matching affine. This closes file/decoder identity, not clinical contour validity.
Stage1label inventory is running in owned execution33929; no duplicate inventory should launch.

Metadata-only sizing across1403cases projects199.33GiB for full1mmfloat32CT+uint8target arrays,
versus19.51GiB for current144cubes, before metadata/intermediate/probability storage. With144cube
windows and50%overlap, full-field inference has a median40windows percase(range4–360).
These are geometric projections, not measured inference timing or exact compressed storage.
Full-volume precomputed cache exceeds the existing32GiBcap; qualify a bounded on-demand strategy
or explicitly approve a revised storage budget before preparation. Available drive capacity alone
does not authorize changing a budget. Stages2–7are pending, not qualified.
See [focused input findings](PANTS-INPUT-FIDELITY-20261018.md) for the demonstrated failure.
