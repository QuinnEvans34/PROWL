# PanTS CADe — 3D Viewer (React + NiiVue)

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
