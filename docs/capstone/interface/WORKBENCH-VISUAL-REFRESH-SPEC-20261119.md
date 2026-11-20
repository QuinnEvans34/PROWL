# Workbench visual refresh — spec

November 19, 2026. Owner: Quinton (UI lead review by Claude). Scope: the study Workbench
(`/workbench?study=…`) in 2D, 3D, Split and compare modes, plus the two demo studies
PanTS_00009005 (lesion present) and PanTS_00009016 (no predicted lesion).

The goal is a viewer that reads as a radiology tool: the CT is sharp and dominant, overlays let
the anatomy show through, controls stay out of the way, and the key result is the first thing
in the side panel. No model, scoring or measurement logic changes. Every existing control keeps
working; several move into a smaller toolbar or an overflow menu.

## 0. Ground rules

- No change to model outputs, Dice arithmetic, measurement code or review records.
- Keep every existing `aria-label`, keyboard shortcut and test hook unless a test is updated in
  the same change. Layout preferences stay in `prowl.toolbench.layout.v1` (bump the version
  only if a stored field changes meaning).
- Honest labels: all 12 prepared studies are official PanTS **test-set** cases
  (`outputs/splits/test.txt`). Do not call them validation examples.

## 1. Native-resolution CT for the two demo studies (data)

Problem: `ct.nii.gz` is a 128³ crop at 1.5 mm and `ct_full.nii.gz` is 2 mm. PanTS acquisitions are
about 0.7–0.8 mm in-plane, so the viewer shows roughly a quarter of the in-plane detail.

Export (script: `scripts/export_native_workbench_case.py`):

1. Read the original CT from the PanTS test archive
   (`PanTSMini_ImageTe_00009001_00009901.tar.gz`) and the reference masks from
   `PanTSMini_Label/<case>/segmentations/{pancreas,pancreatic_lesion}.nii.gz`.
2. **Crop without using reference labels.** Slice range = the saved prediction's pancreas extent
   ±40 mm (world coordinates). In-plane = body outline (HU > −500 on those slices) + 10 mm.
   Native voxel spacing and orientation are kept exactly; only the index range changes.
3. **Prediction on the native grid.** The saved prediction (`pred.nii.gz`, 1.5 mm) is resampled
   to the native crop by trilinear interpolation of its one-hot channels followed by argmax.
   This keeps volume close to the original and avoids nearest-neighbour staircase edges. The
   saved 1.5 mm file is retained beside it as `pred_prepared.nii.gz`.
4. **Reference on the native grid** comes directly from the native PanTS masks
   (lesion = 2 over pancreas = 1). Difference volumes use the existing codes
   (1 agreement, 2 prediction only, 3 reference only; pancreas = whole organ including lesion — verified against the old files).
5. **Alignment gate.** Before writing, resample the native reference into the old 1.5 mm grid
   and compare with the old `gt.nii.gz`. Require pancreas Dice ≥ 0.90; otherwise stop. This
   proves the old prediction, meshes and new CT share world coordinates.
6. `results.json` for each study: `files.ct` → native crop, `spacing_mm` → native spacing,
   Dice and predicted lesion volume recomputed on the native grid (displayed numbers must
   match the displayed masks), plus a `display_provenance` block naming sources, crop rule and
   resampling method. Old files remain on disk as `*_prepared.nii.gz`.

Acceptance: both studies open at native in-plane spacing with full axial field of view around
the pancreas; overlays align with anatomy in all three planes; 3D meshes still sit on the
pancreas; the comparison Dice matches the recomputed values.

## 2. Image area (2D)

| Item | Now | Change |
| --- | --- | --- |
| Overlay style | 62% solid fill, outline alpha 0.32 | Outline-first: border alpha 1.0 (`setAtlasOutline(1)`), interior fill 30% default. Slider still controls fill. |
| Compare "Both" | Reference fill covers prediction | Prediction keeps light fill; reference drawn as outline only (fill alpha 0). |
| Crosshair | 1 vx, `[0.46,0.57,0.69,0.78]`, no gap | Thin, 45% alpha, neutral blue-grey, centre gap so the target is never covered. |
| Volume card on image | Floating card top-left of the axial view | Removed from the image. Numbers stay in the bottom bar and side panel. "Volume overlay" toggle retired. |
| Hint text | Overlaps the sagittal image | Bottom-centre of the viewer, fades after 4 s, never over a pane's image. |
| Pane controls | 6 icons × 3 panes always visible | Visible on pane hover or keyboard focus only; title row stays. |
| Orientation letters | Small, partly covered | Larger, bolder, at pane edge midpoints. |

## 3. Toolbar: one row

Replace the viewer toolbar plus the "IMAGING WORKSPACE" button row with a single 44 px bar:

- **Left:** 2D / 3D / Split; then planes (All / Axial / Coronal / Sagittal) in 2D or scene
  (Abdomen / Region / Surfaces) in 3D. Only the group relevant to the current mode shows.
- **Middle:** icon-only tool group (Navigate/Rotate, Pan, Window, Box zoom) with tooltips.
- **Right:** CT window select, Overlay slider, Fit, Reset, then a `⋯` menu holding Linked
  crosshairs, Expert panel, Focus workspace, Full screen, Restore layout and View settings.
- One state style everywhere: active = accent fill and text; inactive = no fill.
- Duplicated "Linked crosshairs" removed from the 2D sub-header.

## 4. Bottom bar: one row

Merge the layer legend, "Compare with reference" heading and measurement strip into one bar:

- Left: Prediction / Reference / Pancreas / Lesion toggles with colour dots.
- Middle (when comparing): Both / Model / Reference / Difference.
- Right: Pancreas and lesion volumes; **Dice when comparing**; Compare / End comparison.
- Go to Pancreas / Lesion moves next to the slice controls as small buttons.

## 5. Side panel: lead with the answer

- Default width 320 px (unchanged), collapsible as today.
- Top **summary card**: lesion predicted yes/no, lesion volume, longest axial diameter when
  available, pancreas volume; Dice pair when comparing.
- Lesion and pancreas measurement cards become collapsible sections, actions as compact
  buttons.
- The multi-paragraph caveat text collapses into one "About these numbers" disclosure.

## 6. 3D

- Open framed on the pancreas region with the predicted lesion visible.
- Orientation cube in muted greys instead of saturated purple/red.
- Volume card removed from the 3D canvas (same as 2D).
- Peel control: labelled, consistent with the other bars.

## 7. Polish

- Minimum text size 11 px in the Workbench; labels in sentence case.
- Study tag reads **Test-set example** / Prepared study.
- Header status and pane titles truncate with a tooltip rather than mid-word.

## 8. Verification

- `npm run test:run` (update tests that assert removed controls or labels).
- Browser check at the docked panel width and at 1440×900: both studies in 2D, 3D, Split and
  each compare mode; no console errors; overlays aligned; no text over images.
- Record before/after screenshots in `docs/capstone/interface/`.

## 9. Implementation record — November 19, 2026

Built on `main` at `138bfca` (after Codex's 3D Workbench merge). Uncommitted for review.

**Data (section 1, done).** PanTS_00009005 (0.863 × 0.863 × 2.5 mm, crop 491 × 294 × 62) and
PanTS_00009016 (0.916 × 0.916 × 2.5 mm, crop 400 × 325 × 68) were rebuilt with
`scripts/export_native_workbench_case.py`. The CTs came from `PanTSMini_ImageTe_00009001_00009901.tar.gz`
by a resumable stream read; nothing else in the archive was extracted. Alignment gate Dice = 1.000 for both.
Prepared CTs store (HU + 100) / 400 (fitted, residual 0.0005), so the native CT is int16 HU with
`scl_slope` 0.0025 and `scl_inter` 0.25 and every window preset still applies. Display Dice on the
native grid: 9005 pancreas .901 / lesion .916 (prepared .855 / .919); 9016 pancreas .894, no lesion
in either. Lesion volume 15.58 mL (prepared 15.63 mL). The legacy pancreas difference file counts
the whole organ including lesion; the export matches that. Previous files are kept as
`*_prepared.nii.gz`, `difference_prepared/` and `results_prepared.json`. The other ten studies are unchanged.

**UI (sections 2–7).**
- Overlays: 30% fill plus crisp SVG contours on the native grid (`ViewerContourOverlay`), reference
  as a dashed outline only when both sources show. NiiVue's own atlas outline was not used: it
  draws borders for structures whose colour alpha is zero, so hidden layers would leave outlines.
- Crosshair thinner and quieter; orientation letters larger. The floating volume card is gone
  from 2D and 3D; volumes and Dice live in the bottom bar.
- Toolbar: the workspace-action row is replaced by a `⋯` menu (Expert panel, Focus, Full screen,
  Restore layout). One row at ≥1680 px; below that, two deliberate rows (view, then tools).
  The 3D scene group stays visible in 2D because Codex's tests define "Abdomen from 2D opens 3D".
  Linked crosshairs stays in the 2D rail, where it is contextual, not in the menu.
- Side panel: finding summary card first (status, lesion and pancreas volume, Dice when
  comparing); measurements in a collapsible section; caveats in "About these numbers".
- Labels: Test-set example, Three-view compare; Studies page names PanTS-te as the source.
- Pane controls appear on hover/focus; the interaction hint sits top-centre and fades after 4 s.

**Not done, by design or for later.** Longest axial diameter (a measurement change, out of
scope). 3D default framing and the orientation cube (NiiVue hard-codes the cube colours; the 3D
open behaviour is Codex's newest merge). The demo still shows the July SegResNet prediction;
re-exporting from the 46k STU-Net native masks on the Lenovo is the follow-up.

**Verification.** `vitest run`: 590 passed, 7 skipped (two test files updated for the summary card
and the `⋯` menu). `vite build` succeeded. Headless Chromium screenshots of both studies in 2D,
compare and 3D at 1440 × 900, 1100 × 760 and 800 × 683 showed no text over images.

## 10. November 20 follow-through

Pan keeps its text label and the 2D rail lets reviewers toggle linked crosshairs.
The comparison uses a reference fill when the CT and reference grids differ or the
active view cannot draw a registered contour. The native exporter validates the
reference grids and results entry before writing files.

Both demo studies opened with native spacing, model contours, and calipers on
their measured axial slices. The higher resolution applies to 2D and 3D Region.
The 3D Abdomen view uses the existing full-volume CT. The UI suite passed 591
tests with 7 skipped, the Chromium suite passed 9 tests, and the production build
succeeded. Synthetic exports verified repeatability, preserved the prepared
backups, and left files intact when the preflight rejected invalid inputs.

## 11. Native full-volume 3D Workbench

The Workbench's 3D Abdomen view uses `files.ct_full_native` when available. The
scene label reads voxel spacing from the volume it actually loaded. Region
continues to use the native crop. Full 2D and Three-view compare continue to use
the smaller `files.ct_full` volume.

To install the local full-volume asset, run the existing exporter with
`--full-only --ct <original-ct> --case-dir <study-directory> --results <results-json>`.
The exporter checks that the original CT matches the installed native crop in
geometry and intensity before publishing the new volume. It preserves the full
acquired grid and the display window calibration. Scan assets stay local.
