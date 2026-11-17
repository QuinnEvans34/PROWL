# PanTS CADe — 3D Viewer (React + NiiVue)

## Charcoal toolbench

The Workbench uses three persistent CT planes with individual slice, zoom, fit,
hide and maximize controls. Crosshairs can be linked while pan and zoom remain
independent. Drag the dividers to resize planes, the study list or the expert
panel; keyboard arrows also operate focused dividers. Restore layout changes
presentation preferences without clearing imaging settings or review drafts.
Use **Lock framing** to preserve pan and zoom while browsing slices or changing
the window. Two-finger scrolling over a Workbench CT image zooms the active
plane. Drag the slider below an image to browse slices, or focus it and use the
arrow keys for single-slice steps.

Focus workspace hides surrounding panels. Full screen uses the browser display
mode where supported, hiding browser controls and the study header. It requests
the entire display; Focus workspace fills only the current window. If the host
cannot enter native full screen, PROWL explains that without changing layouts.
Escape exits either mode.
Viewer instances remain mounted through these display changes. Layout choices
are saved locally; CT positions, measurements and review text are not included in
the layout preference record. Narrow screens open their drawers only on request.

Pancreas-outline and total-lesion volumes come from the displayed saved mask,
with geometry, units and coverage checks. Unavailable values never fall back to
legacy manifest volumes or a sphere-equivalent diameter. The saved/native result
page reuses verified package measurements. These are model-outline volumes, not
verified whole-organ measurements or a diagnosis. The legacy prepared-study live
scoring endpoint does not replace the saved contours; fresh native inference
remains available through Analyze when its model worker is connected.

On a prepared study with prediction surfaces, enter **3D** (use **Surfaces**
to remove the surrounding CT) and click a predicted lesion. Findings promotes
the matched component, with its dimensions in cm and outline volume in mL.
**Select in 3D** in Findings is the keyboard alternative. **Inspect measurement**
opens the exact source CT slice and draws the two centered calipers. The cross
follows the view and disappears when you leave that slice. If the viewer cannot
reproduce the measurement plane, the dimensions remain visible without a jump
action. Calipers measure the predicted outline, not a maximum diameter.

In **3D** or **Split**, click a predicted lesion or select it from the **Lesion
review** strip above the scan. The strip shows the dimensions beside **Show
calipers** and **Inspect CT slice**. Once shown, the 3D cross stays on while you
click surrounding tissue or move between views. **Hide calipers** turns it off,
and switching studies clears it. **Face calipers** rotates the 3D view so both
arms are visible. In 2D, the cross appears only on the measured
slice; **Go to measured slice** returns there after browsing nearby tissue.
Saved reviews and Analyze results offer **Inspect measurement** for 2D.

Regression checks: `npm run test:run`, `npm run build`, and
`npm run test:e2e -- --config=playwright.toolbench.config.js`. Synthetic browser
checks prove controls and draft lifetime; real CT rendering also needs browser inspection.

## Capstone test foundation

Use Node 24.21.0 (`nvm use` in this directory), then `npm ci` and `npm run test:run`.
Verified tooling: Vite 8.3.4, Vitest 5.0.4, React plugin 6.1.2, npm 11.19.0.
See [the tooling update and browser verification](../docs/capstone/testing/UI-TOOLING-UPDATE-2026-10-13.md).
For the synthetic Chromium smoke test, run `npx --no-install playwright install chromium` then
`npm run test:e2e`. `npm run build` builds locally; it does not publish a site.
The browser fixture stubs NiiVue, blocks case/network access except its local server and a stubbed
font stylesheet, and contains no patient data. It proves control behavior, not CT rendering.
See [the baseline evidence and outstanding security/accessibility work](../docs/capstone/testing/UI-FOUNDATION-2026-09-20.md).

## Historical demo instructions

Static-first viewer for the pancreas / lesion segmentation demo (design in `docs/ui.md`).
The 3D hero: the CT volume rendered in 3D with the pancreas (green) and lesion (red)
surface meshes overlaid, rotatable, with a cut plane to move through all three axes.
No backend — it just serves files from `public/cases/`.

## Run it

```bash
cd ui
npm install
npm run dev          # opens http://localhost:5173
```

It boots on a synthetic `sample` case so you can test immediately, before any real export.

## Load real cases

1. Export showcase cases from the trained model (drive mounted):

   ```bash
   PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/export_case.py \
     --ckpt outputs/checkpoints/pants-level45/wholebox_p128_1p5_GOOD.pt \
     --case <ID> --crop-native 16 --whole-box --roi 128 --spacing 1.5
   ```

2. Copy the exporter output into the app's static folder:

   ```bash
   cp -R outputs/ui_cases/* ui/public/cases/
   ```

   The exporter's `results.json` merges cases; overwrite `public/cases/results.json` with it
   (or merge) so the case picker lists them.

3. Reload the dev server — the new cases appear in the picker.

## Controls

- Drag to rotate, scroll to zoom.
- **Contour source**: toggle model prediction vs ground truth (great for the wrong-prediction case).
- **CT volume opacity**: fade the scan in/out to reveal the organ/tumor meshes.
- **Cut plane**: slice through the 3D volume along any axis (depth / azimuth / elevation) while staying 3D.

## Notes

- Meshes are world-aligned in `scripts/export_case.py`. If a real case shows the mesh offset
  from the volume, it's the MONAI RAS affine handling — fix in `export_case.py::get_affine`.
- This is the Week 5 UI, started early. Clinical-vs-validation split follows `docs/ui.md` §"Two audiences".
