# PROWL presentation assets

Screenshots and video for the capstone deck, captured on November 20, 2026.

- **Location:** `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL/presentation-assets/`
- **Slide outline:** the "PROWL capstone presentation plan" in the Claude project.
- **How they were made:** from the live Workbench with `ui/scripts/capture-presentation.mjs` on the Mac's GPU. The page was 1920×1080 and saved at double resolution, so full-screen images are 3840×2160.
- **Clean-capture changes:** the crosshair and the orientation cube are hidden during capture only.
- **Layout:** finished files are in this folder; untouched originals are in `raw/`.

## Rules for every slide that uses these images
- Add the credit **"CT data: PanTS, Johns Hopkins."** to any slide with a scan.
- All studies are from the PanTS **test set**.
- The pancreas and lesion outlines come from **PROWL's model**.
- Vessels and ducts ("Anatomy · ref") are the **dataset's expert annotations**, not model output.
- Contact angles and measurements are review aids, not a diagnosis or a resectability call.
- **Colours on screen:**
  - Model: teal = pancreas, red = lesion.
  - Expert reference: dashed sky blue = pancreas, dashed amber = lesion.
  - Vessel distance to the lesion: red < 2 mm, orange 2–5 mm, yellow 5–10 mm, slate > 10 mm.

## Files by slide

| File | Slide | Suggested caption / use |
|---|---|---|
| `A1b_hero_3d_9005_front.png` | 1 Title (recommended) | Front view taken from the turntable: see-through pancreas, red lesion, vessels coloured by distance. Brightest and most striking hero. Background matches the slide charcoal (#191A1C). |
| `A1_hero_3d_9005.png` | 1 Title (alternate) | 3D pancreas (teal) with the predicted lesion (red) and nearby vessels coloured by distance to the lesion. Background matches the slide charcoal (#191A1C). |
| `A2_hero_3d_9016.png` | 1 or 10 (alternate) | A healthy pancreas with its surrounding vessels. |
| `B1a_ct_no_overlay_9005.png` | 3 Challenge | "Where's the pancreas?" One CT slice, no help. Show first. |
| `B1b_ct_model_outline_9005.png` | 3 Challenge | The same slice with PROWL's outline: pancreas teal, lesion red. Show second (before/after). |
| `B2_lesion_closeup_model_vs_expert_9005.png` | 3 "Outlines, not circles" | PROWL's lesion outline (solid) over the expert's (dashed). Lesion Dice on this study: 0.916. Enlarged 3× from the screen capture, so use it at up to about half a slide. |
| `C1_turntable_9005.mp4` | 4 "Let me show you" | 8-second 360° loop, 1920×1080, 30 fps, H.264, charcoal background. Set to loop and start automatically. |
| `C2_workbench_overview.png` | 4 / demo backup | The whole Workbench: three CT planes, outlines, reference anatomy, findings panel. |
| `D1_studies_page.png` | Demo backup 1 | Studies page: 12 prepared CT studies. |
| `C2_workbench_overview.png` | Demo backup 2 | (Reuse) 2D review at the lesion slice. |
| `D3_3d_vessel_bands_9005.png` | Demo backup 3 | 3D view with the vessel distance legend in the bottom bar. |
| `D4_findings_panel.png` | Demo backup 4 | Findings panel: lesion characteristics and vessel relationship. |
| `D4a_card_lesion_characteristics.png` | Demo backup 4 (zoomable) | 3.6 × 2.9 cm, pancreatic body, hypoattenuating (−35 HU vs pancreas). |
| `D4b_card_vessel_relationship.png` | Demo backup 4 (zoomable) | Celiac artery 228° contact (encasement by the 180° convention); bile duct 8.6 mm and pancreatic duct 6.2 mm, both flagged dilated. |
| `D4_findings_cards_full.png` | Demo backup 4 (context) | The same cards shown inside the full Workbench. |
| `D5_compare_with_reference_9005.png` | Demo backup 5 | Compare with reference: pancreas Dice 0.901, lesion Dice 0.916 (bottom right). |
| `D7_review_summary_9005.png` | Demo backup 7 | Review summary panel: the radiologist writes the conclusion; PROWL drafts from findings. |
| `D8_curved_view_9005.png` | Optional extra | Curved view: the pancreas straightened head to tail, with the lesion span marked 41–74 mm from the head. |
| `D9_outline_editor_9005.png` | Optional extra | Outline editor: paint, erase and export corrections; volumes update live. |
| `D10_confidence_2d_9005.png` | Optional extra | Confidence map: orange marks where the model is unsure of the boundary. |
| `E2_training_page.png` | 7 How it was built | Training page with the run history. **The numbers on it are a live snapshot; recapture before the December 4 number freeze.** |
| `F1_difference_closeup_9005.png` | Backup: Dice explained | Difference view. Lavender = model and expert agree; rose = model only; amber = expert only. |
| `F2_false_positive_9220_workbench.png` | Backup: false positive | A scan the reference marks as healthy, where the model drew a lesion (about 52 mL). |
| `F2_false_positive_9220_axial.png` | Backup: false positive (close) | The same, one slice. Prepared 1.5 mm study, so outlines look blocky. |
| `F3_failure_small_lesion_9687_workbench.png` | Backup: failure case | Small lesion: expert 2.2 mL vs model 7.0 mL in the wrong place (lesion Dice 0.03). Shown with the reference. |
| `F3_failure_small_lesion_9687_axial.png` | Backup: failure case (close) | The same, one slice. Prepared 1.5 mm study. |
| `F4_confidence_closeup_9005.png` | Backup: confidence | Close-up of the confidence map around the lesion. |

## Still to capture
- **D6 Ask PROWL answer with a citation open**, and the Ask PROWL thumbnail for the architecture slide (E1). These need the local AI expert, which waits for the GPU to be free from training.
- Workbench and Training thumbnails for the architecture diagram (E1) can be cut from `C2_workbench_overview.png` and `E2_training_page.png`.

## Recapturing
With the UI running (`cd ui && npm run dev`), run this from `ui/`:

```
node scripts/capture-presentation.mjs [IDs]
```

New originals land in `raw/`. Run it without IDs to capture everything; IDs are the prefixes above, such as `A1 D5`.
