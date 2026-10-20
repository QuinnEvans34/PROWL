# Saved autonomous prediction viewer — W02-04

Delivered October 12, 2026. Private local display of the retained PanTS_00001070 autonomous
prediction, reusing React/NiiVue. No inference, training, reference-mask reads or metric changes.

## What is delivered

- `/saved` displays the original native CT and the saved 0/1/2 prediction label map. Pancreas and
  lesion visibility are independently controlled; the CT window is −100 to 300 HU.
- Case ID, CT/prediction hashes, both model hashes and inference/result identities are inspectable.
- Files are fetched and SHA-256/size verified before display. Native dimensions, affine and mm units
  are compared with the package after NiiVue decoding; inconsistent overlays stay hidden.
- Loading, unavailable package, missing mask, failed prediction and geometry disagreement are explicit.
  Reload unmounts the old viewer immediately. Late requests cannot replace a newer package.
- Warning text describes unvalidated development predictions. There are no diagnostic or model-quality
  claims. PanTS_00001070 was selected adaptively; this is not representative performance evidence.

## Prepare and run

From the repository root, using a fresh ignored output directory:

```sh
.venv-prowl/bin/python scripts/prepare_saved_prediction_view.py \
  --ct /absolute/path/to/the/pinned/ct.nii.gz \
  --result outputs/prowl/autonomous-real-ct-20261009/prediction-a02/result.json \
  --output outputs/prowl/saved-viewer-20261012/package
```

The actual package already exists; do not rerun into it. The CT path for this case comes from
`outputs/prowl/autonomous-real-ct-20261009/fixed-development-75/plan.json`. The exporter validates
CT and prediction content hashes, case identity, completed CT-only status, native geometry, explicit
mm headers and label values before copying files. Existing output directories are refused.
No model weights are needed. This command reads this one CT and predicted mask, not references.

From `ui/`:

```sh
PROWL_SAVED_PREDICTION_DIR=../outputs/prowl/saved-viewer-20261012/package \
  npm run dev -- --host 127.0.0.1 --port 5180 --strictPort --open false
```

Open `http://127.0.0.1:5180/saved`. The opt-in Vite development middleware serves only three named
files, rejects escaped/symlinked paths outside the package, and disables caching. Keep it bound to
loopback. The private folder is outside `ui/public`; this middleware does not run in production builds
and does not copy patient data into the published bundle. Existing unrelated public demo assets are
unchanged. This is a local review route, not a deployed service or full case-selection workflow.

## Adapter contract

`manifest.json` uses **saved-prediction-view-v1**, a narrow display adapter for retained
`autonomous-cascade-v1` results. It preserves the file-reference/content-identity concepts from
`docs/capstone/contracts/case-package.schema.json`; it does **not** claim to implement that full
case-package contract with measurements, findings and release lineage.

Fields: `case_id`, `status`, `prediction_mode`, `reference_inputs_used`, `files.ct/pred`
(`uri`, `bytes`, `content_sha256`), `geometry` (`shape`, `affine`, `units`), `model_sha256`
(localizer/segmenter), `result_sha256`, canonical `inference_evidence_sha256`, `ct_window`,
label semantics (0 background / 1 pancreas / 2 lesion), and warnings. Files remain native-grid
copies; no resampling or label-based crop is performed. Input evidence hashes identify retained
claims; the adapter does not certify training lineage or biological patient uniqueness.

## Acceptance evidence

Private package and screenshot: `outputs/prowl/saved-viewer-20261012/`.
Native case: **426 × 301 × 157**. Copied CT SHA-256
`90bf329d4a959144dfc453c5f1adce83ac18b1d5493984cb8aaa3911a1f1000f`;
prediction SHA-256 `848a7d053b712700d58b9c2f9d406754d2a7627ae82071638f4d6b1a814939bc`.
Both exactly match the retained source result. Real browser reached ready with zero JavaScript errors;
screenshot inspection shows axial, coronal and sagittal CT with aligned predicted overlays. Alignment
is geometric, not a claim of anatomically correct segmentation.

Focused checks:

```sh
.venv-prowl/bin/python -m pytest -q tests/test_saved_prediction_view.py
# from ui/, with a Node version supported by the installed jsdom:
node node_modules/vitest/vitest.mjs run tests/savedPrediction.test.jsx
node node_modules/@playwright/test/cli.js test --config playwright.saved.config.js
npm run build
```

Seven Python checks and twelve UI checks pass. UI checks include failed/missing identities, changed
payloads, path rejection, geometry/units and stale-request isolation. Three browser checks pass and exercise the
actual local NiiVue/package route, including overlays, reload isolation and failure states. The default
shell Node encountered an existing jsdom/undici compatibility error; the bundled Codex Node ran the
UI checks successfully without changing dependencies. Build warnings for large NiiVue chunks remain.

The seven unresolved source-unit cases and the head-study issue remain tracked under W02-02;
this viewer delivery does not close them. Durable review decisions, full transport-neutral case
packages and routine case selection remain later work.

## October 20 measurement extension

V1 remains display-only. Opt-in `--measurement-provenance` writes a fresh v2 package with original result JSON and canonical evidence JSON, each hash-bound in the manifest. The private middleware also serves these two named files. The viewer adds native mask-volume questions and refuses source/crop-boundary contact; it does not certify full-organ coverage. See [native measurement results](../retrieval/NATIVE-MEASUREMENT-RESULTS-2026-10-20.md) for limits, current local configuration and the historical example’s coverage refusal.
