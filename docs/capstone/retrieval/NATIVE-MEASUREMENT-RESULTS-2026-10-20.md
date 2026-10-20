# Native measurement provenance and coverage — October 20

The private `/saved` viewer now supports a separate **saved-prediction-view-v2** measurement package.
It verifies original CT/prediction/result/evidence bytes, cross-checks retained source and model
identities, and checks actual native CT/mask grids against the inference geometry. It calculates
pancreas extent and total suspected-lesion volume only if the outline clears both source-grid and
recorded inference-crop boundaries. See the [frozen contract](NATIVE-MEASUREMENT-CONTRACT-2026-10-20.md).

## Real finding and limits

Repackaged the already exposed October 12 PanTS_00001070 development example into a fresh private
folder; the original package and producing inference were preserved. No model or reference-mask
read, inference execution, training, protected evaluation or source-data rewriting occurred.

The browser verified the native package and displayed its CT/prediction. Asking “How big is this
pancreas?” correctly returned **Measurement unavailable**: the prediction touches the inference crop
boundary. Independent Python inspection confirms 50 foreground voxels on the low-z face, which is
also the CT's low-z boundary. No predicted voxel lies outside the recorded region. This supports a
coverage warning, not a conclusion that the model crop alone caused the issue: source coverage or
segmentation error remains unresolved. This historical, adaptively selected example does not assess
the current training run or representative model performance.

No numeric answer was promoted for this example, no guard was relaxed, and no replacement inference
was launched. The earlier Workbench prepared-mask preview remains a separately qualified calculation
with legacy units/unknown coverage warnings. It is not upgraded to verified native coverage.

## Checks

145 distinct focused UI/library checks pass across native provenance/transport, reload/stale response
handling, original saved viewer, prepared-mask calculation and existing literature/volume answers.
This comprises the retained 141-check run plus four new cleanup/resource/lifecycle checks (the final
35-check affected run also rechecks existing cases). Eleven Python package checks pass, including budget rejection before mask materialization or provenance parsing. The production
build succeeds with the existing large-chunk warning. No clinical measurement acceptance follows.

Synthetic native fixtures validate successful arithmetic, mismatched CT/prediction/result/evidence
hashes, contradictory source/model identities, missing mm units, incompatible geometry, missing
records, invalid region bounds, foreground outside the region and internal crop-edge contact.
The source-boundary-clear/crop-boundary-contact fixture specifically catches the failure that a
source-grid-only check would miss. Reload removes the old answer immediately; late package responses
are released rather than shown. Object URLs are revoked after downstream identity failure.

V2 measurements enforce 32 million voxels, 64 MiB per compressed image, 128 MiB per decoded image,
and 1 MiB per provenance record. Prepared preview limits remain 16 million/64 MiB. Manifest reads
and declared file lengths are stream-bounded; exact original file hashes must match. Existing v1
packages continue as display-only packages. Model hashes are verified against retained inference
records, not against reloaded weights or an independently audited training cohort.

## Operation and next handoff

The shared shell now labels the saved route “Saved package · see model provenance” instead of
showing the unrelated legacy segmenter label. This one-line integration stays on the local shared UI
branch; the native viewer and adapter publish independently.

The local UI was restarted on port 5180, owned session 16310, using:

```sh
# from ui/
PROWL_SAVED_PREDICTION_DIR=../outputs/prowl/native-measurement-20261020/package \
  npm run dev -- --host 127.0.0.1 --port 5180 --strictPort --open false
```

The private middleware now allowlists `result.json` and `evidence.json` alongside the original three
files. It serves only the explicitly configured folder on loopback and does not include those files
in production builds. No retrieval/DB/Ollama restart was needed. Native measurements require no LLM.

The exporter opts into v2 with `--measurement-provenance` and refuses existing output directories.
A current-pipeline output should be handed over as its saved CT, prediction and completed result JSON;
then package it using the same geometry/identity/coverage checks. Do not infer a new model's identity
from a filename or the legacy global UI model label. Review actual anatomical coverage separately:
absence of boundary contact never proves the full pancreas is captured.

AI-05 remains In Progress. Next: admit a saved result from the current coverage-checked pipeline,
review geometry/outline coverage with Quinton, then add per-lesion components/defined diameter and
reviewed-reference validation. Formal RAG acceptance, AI-06 normal-reference eligibility and disease
interpretation remain open. Local evidence: `outputs/prowl/native-measurement-20261020/` (ignored).
