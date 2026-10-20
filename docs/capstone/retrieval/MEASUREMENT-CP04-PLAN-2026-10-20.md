# CP04: retained annotation and boundary diagnosis

Quinton explicitly requested resolving annotation representation and inspecting persistent boundary
contact using existing predictions. No new inference, training, protected data, alternate component
selection or measurement/UI promotion is part of this block. CP03 failures remain immutable.

## Source diagnosis and scoring contract

Read-only case927 inspection finds int8 stored values exactly -128 and127 (31,831,003 background,
11,301 foreground). Proxy slope0.003921568859368563 and intercept0.501960813999176 equal
float32(1/255) and float32(128/255). Their decoded endpoints are0 and1.0000000591389835. This is
consistent with a full-range int8 scaled binary encoding; the original writer is not established.

Before scoring, qualify a narrow explicit adapter: hash-bound NIfTI-1, exact CT shape/affine,
millimetre units (retain CP03 derivation chain), int8 dtype, exact canonical float32 slope/intercept,
and only the two endpoint values. Convert -128 to0 and127 to1 in a new uint8 private annotation.
Reject intermediate raw codes, other dtypes, slope/intercept deviations, geometry/identity mismatches
and budget violations. Do not choose a numerical tolerance or apply a generic nonzero threshold.
Preserve every foreground position, affine, original and unit-derivation receipt. Output has identity
scaling and a source/encoding/count/hash receipt. Synthetic preservation and refusal checks precede
real derivation. Keep production comparison strict and unchanged. Score the retained case927 raw
prediction and unchanged largest-union candidate once into a new CP04 directory. Recompute the
five-scored/six-selected summary separately, preserving CP03's four-scored result.

## Boundary audit contract

Case698: verify package, original-reference and CP03 candidate hashes before reading arrays.
Compare raw, existing candidate and provided reference masks on every CT and crop face. Record
unique contact counts, per-face counts, overlap with reference, and inward slab counts at distances
0,1,2,3 voxels. Check6/26-connectivity for whether contact belongs to the main predicted/reference
component. Distinguish crop faces coincident with CT boundaries from internal inference faces.
Render native CT boundary/interior slices plus orthogonal context with explicit prediction/reference
legends and slice indices; inspect locally. No diagnostic interpretation or proof of anatomy beyond
the acquired scan. Reference contact can establish annotated tissue reaches the available boundary;
absence of reference contact alone cannot establish all predicted contact is biologically false.

## Limits and completion

Only927/698 arrays; other cases use retained metrics. Keep existing32M/64MiB compressed/128MiB
per-image limits; stream or integer-decode annotation to avoid float64 expansion. Analysis600s/8GiB
per child, total30minutes; all new patient artifacts on registered PROWL-Data under512MiB growth,
internal100GiB floor. No simultaneous model generation. Stop on unexpected identities or invalid
grids; retain errors. No retry of inference and no modifications to old outputs.

Finish with source-derived binary interpretation evidence, case927 original screen outcome,
case698 face/component/slice review, and concrete next correction hypothesis supported by these
results. Report missing case139 unchanged. Update AI-05, weekly plan/spec/handoff and commits.
