# Candidate content and alignment results — D-281

The bounded evidence job completed for all 16 training and 12 validation candidates. This
closes the requested content-read and limited visual-review step, not real qualification,
cohort publication or a training launch. Original membership and earlier artifacts remain intact.

## Measured result

| Check | Result |
|---|---|
| Files | 56 complete CT/pancreas files, all gzip EOF/CRC checks passed |
| Arrays | All CT arrays finite; all pancreas targets nonempty and strict-binary decodable |
| Geometry | All 28 CT/mask grids agree |
| Physical units | 27 CT headers declare mm; all mask units unknown; case 6350 has both unknown |
| Exact duplicates | No repeated compressed CT SHA-256 among these 28 candidates |
| Resources | 44.65 seconds; peak RSS 4,626,972,672 bytes; 693,588,981 compressed bytes; 1,781,743,817 expanded bytes |
| Visual review | All 28 five-plane contact sheets reviewed; no obvious gross displacement in sampled views |
| Qualification/training | No new positive qualifications, executable cohorts or optimizer updates |

Exact-file duplicate checks do not establish biological patient uniqueness or detect all
re-encoded duplicate scans. The existing study-as-subject limitation remains.

The CT headers, rather than the mask headers, provide the available mm anchors. A matching mask
grid may be interpreted in that CT coordinate system after the corresponding evidence is bound
to qualification. No header was rewritten. Case 6350 remains held for unresolved physical units;
appearance does not supply the missing measurement. This corrects the reversed header-kind prose
in the prior D-280 summary; the retained header evidence itself was correct.

## Difficulty and coverage observations

The five predetermined planes are first/middle/last foreground axial and median foreground
coronal/sagittal views, shown with and without the reference overlay. This is limited engineering
alignment evidence, not expert contour certification or exhaustive inspection of every slice.

- Case 4965 has a small visible target at the inferior volume boundary, canonical axial indices
  0–4. Its limited coverage must be retained in the record. Reference containment measures coverage
  of the visible annotation; it cannot demonstrate whole-organ localization.
- Case 3717 also has boundary-contact foreground and coarse through-plane appearance. Whole-organ
  coverage is not established by these views.
- Cases 8037, 3239, 3104, 8443 and 8855 show visible noise, particularly 8037. Noise alone is not
  an exclusion criterion. Do not replace them with visually easier cases.
- Missing phase metadata, including case 3188, remains missing; this review does not infer phase.
- Case 6350's limited alignment review does not resolve its unit hold.

These are descriptive observations, not a complete or expert-assigned difficulty taxonomy.
All candidates remain accounted for. Under the current pancreas-present development scope,
partial coverage should be represented explicitly and evaluated against the visible reference;
it should not silently become a whole-organ benchmark or be removed for model convenience.

## Retained evidence

- Candidate receipt: `3e961f4c3285107d765d2176050c2d57aeb29d0ab8d5893ba1fa3b6db97a26e1`.
- Single-use request: `outputs/prowl/localizer-content-request-6063bb74-a6d7-4234-a2e0-968877203044`,
  request SHA `29a365b6380d7d793cbb43390a827a75f874c197b2ec6151b3c3bd2384963f75`.
- Content package: `outputs/prowl/localizer-content-264c2d12-3367-40ae-805a-fe74b1ac3b72`,
  receipt SHA `224795f966a25733c7c1198e22dfa34fc525ef56be4e023ebdaa48ef8af0e3a9`.
- Separate review: `outputs/prowl/localizer-candidate-review-65e9f44a-f597-43ef-b11b-d889aeeb6947`,
  receipt SHA `cb556a1086d665cb8584f9a8f404c89953445401bb9afc7c958f4e498560b8a4`,
  review SHA `5af5a19e0ad6de9edfbe36ef3169c6b1d52b90bd6f126dcdc39d0afb65b7528d`.

All 62 content-package members were rechecked against their recorded lengths and SHA-256 before
publishing the separate review. The original result's pending-review field remains historical;
the review references it without mutating the completed evidence package.

## Implementation and verification

Isolated purpose-qualification v2 and cohort v3 add train-target versus validation-reference
permissions, protected-role checks, full ancestry and explicit optimizer/evaluator operations.
The old qualification/cohort versions and fixed two-case loader retain their prior behavior.
The new bounded NIfTI reader verifies no-follow source identity, compressed/decompressed limits,
header allocation bounds, complete gzip CRC and before/after file state. The diagnostic captures
source, environment, selection and resource controls before execution.

Native full suite: **1,122 passed**, two existing upstream torch.jit warnings. New regressions
cover wrong roles/uses, stale evidence, held members, ancestry/count mismatches, cross-role exact
CT duplicates, CRC corruption, decompression/voxel bounds, file changes and symlinks. An initial
synthetic test exposed a missing operation guard; it was fixed before real data consumption.

## Next bounded implementation

1. Bind these facts and this review to a new manifest and explicit purpose-specific annotation
   decisions, preserving the old manifestations, source/use evidence, issues and full split ancestry.
   Retain case 6350 as held and the coverage/noise observations as descriptive records.
2. Build and independently replay each qualification. If the remaining source/use checks pass,
   the expected executable proposal is 16 train / 11 validation, with the original 12 validation
   candidates still accounted for and one held. This count is not yet a frozen cohort.
3. Publish new role-specific cohort artifacts and implement a source-byte-verifying consumer.
   The new pure record consumer is not a filesystem loader. Do not alter the fixed two-case
   resolver's constants to bypass its scope.
4. Verify preprocessing on every consumed case, including boundary-contact and noisy cases;
   freeze a compute-budgeted scratch run with separate validation and per-case coverage reporting.

No further broad candidate search is needed before this implementation. No final-test payload,
literature work, source rewriting, remote upload, dependency change or Git publication occurred.
