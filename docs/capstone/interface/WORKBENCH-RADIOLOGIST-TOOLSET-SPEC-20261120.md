# Workbench radiologist toolset — spec

November 20, 2026. Builds on the visual refresh (`WORKBENCH-VISUAL-REFRESH-SPEC-20261119.md`).
Scope: the two native-resolution demo studies, PanTS_00009005 (predicted lesion) and
PanTS_00009016 (no predicted lesion). Other studies keep working without the new assets.

Purpose: move the Workbench from "segmentation viewer" to a pancreas-specific review tool.
Comparable platforms segment the pancreas, duct, veins and arteries for planning (Fujifilm
Synapse 3D Pancreas Analysis), colour vessels by distance to the tumour (MeVis), and quantify
tumour–vessel contact in degrees, the basis of resectability grading. Radiologists also use
curved reformats along the pancreas/duct and the SAR/APA structured reporting template.

## Honesty rules (apply to every item)

- **Model output** = the saved prediction (pancreas + lesion). **Reference anatomy** = PanTS
  dataset annotations (vessels, ducts, pancreas subregions). They are labelled differently in
  every view. A deployed system would need its own anatomy model (e.g. TotalSegmentator).
- Contact, distance and location values relate the *model* lesion to *reference* anatomy. They
  are review aids, not a resectability or diagnostic call. Copy says "for review".
- Every derived number records its method in `insights.json`.

## 1. Surface quality (3D)

- Rebuild prediction and reference surfaces from the native-grid masks: marching cubes at the
  0.5 level of a lightly Gaussian-smoothed (σ = 0.8 mm) mask in physical space, then Taubin
  smoothing (no shrinkage). Pancreas and lesion are extracted from the same smoothed field so
  they share a consistent boundary. Difference surfaces are rebuilt the same way.
- Display: pancreas semi-transparent (35%) whenever a lesion is shown so the lesion reads as a
  solid object inside it; lesion opaque.

## 2. Reference anatomy and vessel relationship

- Assets: `anatomy.nii.gz` on the CT grid (1 SMA, 2 celiac, 3 veins (portal/SMV/splenic),
  4 aorta, 5 IVC, 6 common bile duct, 7 pancreatic duct) and surfaces per structure. Vessel
  surfaces are split into distance bands to the predicted lesion: < 2 mm (contact/near
  contact), 2–5 mm, 5–10 mm, > 10 mm (MeVis convention). Ducts keep their own colour.
- Contact angle per vessel: on each axial slice, the share of the vessel's outer boundary within
  1 voxel of the lesion, expressed in degrees around the vessel centroid. Report maximum angle,
  slice, and category: none, abutment (≤ 180°), encasement (> 180°).
- UI: "Anatomy" layer toggle (2D light outlines + 3D surfaces), distance legend in 3D, and a
  "Vessel relationship" card in Findings.

## 3. Lesion characteristics and structured summary

- Longest axial diameter and its perpendicular, on the native axial slice with the largest
  lesion diameter (Feret diameter of the cross-section).
- Location: majority overlap with reference head/body/tail subregions.
- Attenuation: mean HU of the lesion vs the remaining predicted pancreas; ≥ 10 HU lower =
  hypoattenuating, within ±10 = isoattenuating, higher = hyperattenuating.
- Ducts (reference): maximum calibre of the pancreatic duct and common bile duct (twice the
  maximum inscribed radius). Upper normal used for flags: duct 3 mm, CBD 7 mm.
- UI: "Lesion characteristics" card plus "Copy structured summary", a SAR/APA-shaped text
  (morphology, location, size, duct, vascular relationship) marked "draft for review".

## 4. Curved pancreas view

- Centreline of the *predicted* pancreas (skeleton longest path, smoothed). A straightened curved
  reformat samples the CT perpendicular to the centreline (± 30 mm, 0.5 mm steps), head on the
  left, tail on the right. Prediction contours drawn on the same grid.
- UI: new viewer mode "Curved" with the reformat, contour toggle and a millimetre scale.

## 5. Confidence map

- The saved model is rerun on its own prepared input with 8 flip views. Uncertainty = entropy of
  the averaged softmax; shown only where it exceeds 0.2 and near the prediction. Sanity gate:
  the un-flipped argmax must reproduce the saved prediction (≥ 99.9% voxels).
- UI: "Confidence" layer toggle in 2D (warm heat overlay) with a legend.

## 6. Outline editing

- "Edit outline" view: axial CT with the prediction loaded as an editable drawing. Tools: paint
  lesion, paint pancreas, erase, brush size, undo, reset. Live volume change readout. Export
  edited mask as NIfTI. Edits never overwrite the saved prediction.

## 7. Presentation polish

- 3D "Record turntable": 360° orbit captured from the canvas to a WebM download.

## Acceptance

Both studies show all new layers without console errors; 9016 states "no predicted lesion"
where lesion-dependent values do not apply; existing tests pass and new behaviour has tests;
headless screenshots of 2D, 3D, Curved, Edit and Findings.

## Implementation record (2026-11-20)

Status: implemented for the two native demo studies (PanTS_00009005, PanTS_00009016). The other
ten prepared studies are unchanged and simply do not show the new layers (every feature is gated
on its file being present in `results.json`).

Pipeline: `scripts/build_workbench_insights.py` (≈ 30 s per case on CPU), run per case:

```
python3 scripts/build_workbench_insights.py --case-dir ui/public/cases/<id> \
  --labels <PanTSMini_Label>/<id>/segmentations --results ui/public/cases/results.json \
  --checkpoint <runs/transfer_wholebox_scaledmax_CLEAN__20260719_012104/best.pt>
```

Writes smoothed meshes (originals kept in `mesh_prepared/`), `anatomy.nii.gz` + anatomy meshes
(distance-banded when a lesion is predicted), `confidence.nii.gz`, `cpr_*.png`, `insights.json`
(schema `prowl.workbench.insights.v1`) and the matching `results.json` entries.

Measured values (for review, not clinical): 9005 lesion 36.1 × 29.4 mm, pancreatic body (88%),
hypoattenuating (−35 HU); celiac artery 228° contact (encasement by the 180° convention); veins
1.2 mm without contact; pancreatic duct 6.2 mm and CBD 8.6 mm (above the 3 / 7 mm flags); curved
view 130.5 mm with the lesion at 40.5–73.5 mm. 9016: no predicted lesion, curved view 152.1 mm,
pancreatic duct not annotated. Confidence gate: un-flipped reproduction agreement 1.000 on both.

UI changes:
- `NiivueViewer.jsx`: anatomy label volume (outlined) and confidence volume in 2D; anatomy meshes in
  3D with distance bands (> 10 mm band muted slate at 0.38 opacity so the pancreas and near bands
  read first); translucent pancreas; `record-turntable` command (8 s WebM).
- `ReviewWorkspace.jsx`: Curved viewer mode, Edit outline mode, Record turntable button, Anatomy and
  Confidence layer toggles, distance-band and uncertainty legends, insights passed to Findings;
  viewer-only controls hidden in Curved/Edit.
- New: `CurvedView.jsx`, `OutlineEditor.jsx`, `FindingsInsights.jsx`, `lib/studyInsights.js`,
  `styles/radiologist-tools.css`.
- Toolbar wrap now follows the centre column width (container query) instead of the viewport, which
  fixes overflow at 1680 px with the assistant panel open.

Fixes found while verifying: NiiVue's draw LUT only resolves built-in colormap names, so the editor
passes its colormap as an object; the confidence ramp keeps amber RGB on transparent entries to
avoid a dark fringe from texture filtering.

Verification: vitest 606 passed / 7 skipped (13 new in `tests/radiologistTools.test.jsx`); vite
build clean; headless screenshots of 2D (anatomy + confidence), 3D bands, Curved, Edit, Findings
and 9016 3D; turntable WebM downloaded (VP9; MediaRecorder leaves the duration header empty, so
some players cannot seek).

Known limits: contact angle is axial-only and depends on the reference vessel annotation;
the editor works on the axial plane only; edits export as NIfTI but are not stored server-side.

## Follow-up (2026-11-20, afternoon): Region scene and load time

- **Region was showing the whole body.** Native studies keep a body-width `ct` for 2D, and the
  3D Region scene reused it. `scripts/optimize_workbench_assets.py` now writes `ct_region.nii.gz`
  (native CT cropped to the saved prediction's pancreas box + 25 mm in-plane / 15 mm slices; no
  reference labels) and `preparedViewerCtPath` uses it for 3D when present. 9005: 192 × 145 × 41
  of 491 × 294 × 62 voxels; 9016: 222 × 117 × 47 of 400 × 325 × 68. Surfaces scene also uses it.
- **Load time.** (a) All surfaces are converted to gzipped MZ3 (NiiVue binary): 9005 8.5 → 2.1 MB,
  9016 5.0 → 1.2 MB; OBJ files are kept. (b) Reference anatomy (2D volume and 3D meshes) now
  loads after the scan is on screen, queued on the scene chain so it can never interleave with a
  newer scene. (c) The confidence volume is fetched only the first time Confidence is turned on.
  Headless (software WebGL) 3D Surfaces time-to-ready: 57 s → 32 s; absolute numbers on a GPU are
  far lower, the ratio is the useful part.

## Anatomy on CTs outside PanTS (probe, one case)

The anatomy layer uses PanTS reference masks, so it exists for PanTS studies only. Probe of the
original SuPreM SegResNet head (32 channels, sigmoid > 0.5, 1.5 mm RAS, HU −175..250) on
PanTS_00009005 against the PanTS masks: IVC 0.94, pancreas 0.87, portal/splenic veins 0.64,
celiac 0.22, aorta 0.06 (channel at a 178 HU vessel offset ~18 mm from the dataset mask;
unresolved), SMA 0.00, CBD 0.01, pancreatic duct 0.04. SuPreM's 25-class map has no SMA, CBD or
pancreatic duct. A model-generated anatomy layer for arbitrary CTs therefore needs a model trained
on the PanTS anatomy labels (the planned Level 5), not the pretrained head.
