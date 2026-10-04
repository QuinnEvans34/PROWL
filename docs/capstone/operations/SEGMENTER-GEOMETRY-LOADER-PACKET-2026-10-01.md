# Next slice — shared segmenter geometry and qualified triple loader

Proposed after D-320. This is a bounded implementation proposal, not a source-read request or training launch. Authority remains the Stage2 PhaseB plan, Plan05 ROI/spatial contracts and protected6/1 cohort. Final tensor resolution, resource envelope and scientific operating policy remain to be measured.

## Goal and inputs

Connect the independently resolved segmenter cohort to one physical-space forward/inverse geometry path. Training/provided-region inference uses the pancreas reference alone to choose a region; autonomous inference later supplies a predicted region to the same mapper. Preserve CT, pancreas and every lesion component on the native grid. Return explicit transform records and fidelity outcomes before any model is trained.

Use the D-320 completion, capability, producing-code, purpose/transition and cohort pins recorded in [freeze results](SEGMENTER-COHORT-FREEZE-RESULTS-2026-10-01.md). Exact members are train3/26/2973/2232/6238/5821 and development-validation2514; original12/fiveholds remain in the bundle. Reject held or wrong-role requests before resolving source paths. One validation positive/no verified negatives supports engineering only. Old localizer loaders/caches/schemas/weights stay independent.

## Phase A — synthetic consumer and transform contract

Add a separate versioned metadata-to-array adapter whose input is a fully replayed frozen bundle, never a bare manifest/qualification. Explicit optimizer/evaluator roles, exact CT/pancreas/lesion descriptors, source-version/split/use/annotation pins and a stage-specific read capability are required. Source reads remain disabled during synthetic development; the current registry is not globally activated.

The future native reader must refuse path traversal/symlinks/nonregular files, substituted bytes or lengths, absent targets, oversized/decompression-bomb payloads, nonfinite values, invalid affine/shape and unsupported dimensionality. Verify each compressed identity before decoding; bound both compressed passes and decompressed bytes. Use the approved strict semantic binary policy for scaled targets. Target units may use the exact context-qualified mm CT grid, never a guessed header rewrite. Future worker reads only the exact21 source files (seven triples), with role and byte accounting; existing consumed content scopes are not reused as authorization.

Assemble native classes0(background),1(pancreas excluding lesion),2(lesion), with lesion-over-pancreas precedence. Record pancreas parenchyma and pancreas-or-lesion union separately. All lesion components and voxels outside the pancreas mask remain reference evidence; never clip lesions to pancreas or enlarge the box from lesion extent. An empty or vanished positive is an explicit fidelity failure, never negative supervision.

Implement source→canonical RAS→pancreas-only physical box with requested/realized mm margins→declared physical sampling grid→uniform aspect-preserving scale→deterministic symmetric pad. Pin grid extent/voxel-center convention, endpoint rounding, interpolation and odd padding. Raw anisotropic voxel counts do not establish physical aspect preservation. Source clipping records every boundary face; normalization must preserve the entire chosen ROI, without center-cropping. Shear/oblique support must be implemented/tested or explicitly refused, never treated as diagonal geometry silently.

For this initial diagnostic propose zero jitter and a10mm starting margin, labeled provided-pancreas-region engineering. These are candidates, not a final cascade policy. Tensor size/spacing is a measured choice; do not inherit localizer144³/2mm limits blindly. Formal baseline jitter is a separate development-derived choice; lesion extent cannot influence jitter acceptance or repair.

Restore continuous three-class probabilities by removing exact pad, reversing scale/ROI/orientation and sampling onto the exact source shape/affine. Outside ROI use background1, other classes0. Check finiteness, normalization and interpolation provenance; only then apply source-grid argmax. Reference label round trips use nearest interpolation, distinct from continuous prediction restoration. Copying an affine onto a misaligned array is not a valid inverse.

## Independent synthetic acceptance

|Test|Required evidence|
|---|---|
|Identity/nonzero origin/flipped and permuted axes|Analytic world-coordinate landmarks and exact source restoration, independent of the mapper's own inverse|
|Anisotropic spacing and long thin ROI|Physical lengths/scale agreement; one scale and full ROI retention|
|Odd padding/all six source faces|Deterministic pad sides and requested/realized margin/clearance|
|Tiny single-slice and disconnected lesions|Per-component presence/counts/round-trip loss retained; a lost positive fails readiness for that recipe|
|Lesion outside pancreas and lesion perturbation|Native precedence preserved; pancreas-only ROI is invariant to lesion changes|
|Empty verified-negative invented fixture versus unknown/held real reference|Semantics preserved; no inferred negative qualification|
|Empty/invalid predicted region|Explicit failure; no reference repair or hidden whole-volume fallback|
|Train/provided-region/image-only mapping parity|Identical CT sampling and transform from the same fixed box without lesion access|
|Stale source/cohort/role/use/transform pins|Refusal before source read; no automatic refill|
|Singular/nonfinite/unsupported affine or dimensions|Bounded preflight failure, retained diagnostic evidence|

Freeze numeric landmark/serialization tolerances from the chosen coordinate convention before real results. Test intentional axis/crop-offset faults. A good round-trip Dice alone cannot prove correct geometry. Run appropriate full native regressions before any real source request.

## Phase B — exact real geometry request and review

Prepare the seven-case metadata request only after synthetic tests/resource rehearsal pass. Derive exact compressed/hash+decode/expanded budgets from frozen file descriptors and headers, plus any separately needed native reference reads. Freeze code/runtime/source/capability/case/recipe pins, CPU/RSS/output/disk/time ceilings, serial-worker behavior, cancellation and completion-last records. Qualify the largest consumed geometry on synthetic data first. Separate resource exceptions from qualification; preserve all selected cases without replacement. Issue the concrete request before execution.

The initial real job is zero-update CPU geometry/fidelity only: no model, GPU, training cache promotion or checkpoint. Review all seven native overlays and original→tensor→native target outcomes. Report physical crop fraction, effective spacing, class counts, all components, source boundary contacts, box containment and effective containment after normalization. Keep complete denominators and failures.

Case2973's124voxels on one7.5mm slice is mandatory for the fidelity review. Case6238 reaches nativeZ=0 and has lesion pixels outside the pancreas mask; preserve boundary context. Outside-mask pixels in26/2232/5821 stay visible. Held5641 is not consumed; its disjoint-mask question remains in the ledger. Do not retune resolution by dropping a case. If a recipe erases a lesion, compare a new measured recipe with a new identity/budget and preserve the failed candidate.

## Exit and following phase

Exit: fully role-safe triple loading, shared portable geometry with independent oracles, and a complete reviewed real zero-update fidelity receipt for all seven members. Freeze a usable diagnostic recipe only from that evidence; if fidelity/resource requirements conflict, document the next candidate rather than weakening the gate or membership.

Then create a fresh three-class segmenter/model/loss/optimizer/sampler identity; synthetic sparse/multiple-lesion learning and checkpoint interruption/independent keeper recovery; native MPS zero-update/resource/export qualification; one exact short scratch training request. No localizer checkpoint reuse, pretraining download, autonomous-policy promotion or long-scale training is authorized by this packet. Wider validation and verified negatives remain required for later performance claims.
