# Current-scan volume connection — October 20

The local Workbench Ask PROWL panel now handles “How big is this pancreas?” and “What is the size
of the lesion in this scan?” using a deterministic calculation from the selected saved prediction.
This is the first bounded AI-05 development slice, not complete REQ-X01 acceptance.
See the [pre-execution contract](CURRENT-SCAN-VOLUME-CONTRACT-2026-10-20.md).

## Behavior and evidence

- `prepared-mask-volume-v1` checks 3D shape, CT/prediction affine agreement, declared units, labels,
  payload completeness and resource limits. Pancreas extent uses labels 1+2; lesion volume sums
  label 2. Unknown/invalid/edge-touching masks refuse a numeric answer. No mesh estimates.
- Prepared exports omit NIfTI units. A legacy manifest's explicit matching `spacing_mm` declaration
  permits a qualified preview; the source disclosure states this and the missing checkpoint hash.
  Grid agreement does not establish source-space accuracy, organ completeness or mask correctness.
- Whole-organ coverage stays unverified even if no predicted voxel touches a grid boundary.
  Head/body/tail, individual lesion diameter, normal-range and case-disease questions remain outside
  this slice. Zero lesion labels does not establish absence of disease. Live scalar inference results
  are not a bound mask and cannot silently reuse a saved mask as a new prediction.
- Numbers and readable wording are calculated locally; **no local answer-model call** is involved.
  General literature questions retain their existing model/source path. No scan ID, array, mask or
  measurement is added to a literature request. The measurement loader only requests selected CT
  and prediction files; it does not request reference annotations or scientific evaluation inputs.
- Scan/prediction changes abort pending measurement reads and hide completed measurement answers.
  Requests can be cancelled, and transport/decompression each has a 64 MiB cap.
- Hashes identify decoded NIfTI bytes. Browser verification found Vite serves gzip as HTTP content
  encoding, so a compressed-file hash would vary with transport decoding. Canonical decoded hashes
  now agree between compressed and HTTP-decoded inputs; a regression check covers this behavior.

107 focused checks pass across arithmetic/transport, measurement UI, existing Ask panel, literature
search and volume-answer suites. Analytic tests include anisotropy, rotation, reflection and shear,
invalid units/grids/labels, empty masks, boundary contact, stale requests and compound-question
refusals. Production build succeeds; existing large-bundle warning remains. No clinical accuracy or
protected evaluation claim follows from these software checks.

Browser walkthrough of the already prepared demonstration showed pancreas-outline **60.33 mL**
and suspected-lesion total **15.63 mL**. Independent Python counting of that same saved mask gives
17,875 union voxels and 4,631 lesion voxels × 3.375 mm³ = 60.328125 mL and 15.629625 mL.
This is arithmetic/wiring verification on an exposed demo, not held-out assessment. The original
assets were not rewritten. Local screenshot, independent receipt and build output are retained in
`outputs/prowl/current-scan-volume-20261020/` (ignored; no CT/mask payload publication).

The literature API still reports source-literature-answer-v2 / source-linked-literature-search-v2.
No services were restarted, no model was downloaded/called, and no training or full selector ran.
The separate live imaging analysis endpoint remains offline; saved predictions work independently.

## Remaining work

AI-05 stays In Progress: validate native-source geometry and coverage, bind producing model and
artifact lineage, add individual-component measurements and a defined diameter, then verify against
reviewed development references. AI-06 reference eligibility follows; no “larger than normal” or
size-based disease conclusion is enabled here. Return to W03-04/W03-05 after this bounded slice.
The existing Findings and review-summary panels still use their published package fields; they do
not yet consume the new on-demand measurement adapter.

The Workbench integration is committed on the shared UI branch. Publication must preserve the other
chat's unpublished redesign; never push that entire branch as a retrieval-only change. The portable
measurement module/tests and specification can be published separately from that integration.
