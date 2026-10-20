# PROWL visual prototype — Concept 01

Created October 18, 2026 on `codex/prowl-ui-redesign` for Quinton's design review.
This implements the first visual prototype milestone locally; it does not implement the production redesign.

## Open

Open `index.html` in a browser, or serve this directory locally:

```sh
python3 -m http.server 5191 --bind 127.0.0.1
```

Then visit `http://127.0.0.1:5191`. The active review server was started on this port by this chat.
Stop that owned process before starting another on the same port. No production service was replaced.

## Files

- `prowl-workbench.html`: editable, self-contained interactive fragment; also rendered inline in Codex.
- `index.html`: standalone preview generated from that fragment using the visualization skill renderer.
- The original repository-root `PROWL_LOGO.png` is embedded unchanged as a data URI. Preserve the original.

The generated wrapper provides optional host state handling. Product interactions need no backend,
network calls, external model, or patient files. The source fragment has no external dependencies.

## What to try

1. Workbench: switch 2D/3D/split, reveal reference, hide prediction, inspect the example measurement.
2. Studies: open study 002 without a reference or study 003 without a candidate region.
3. Ask PROWL: choose a suggested question, see the pending state, inspect the example source card.
   Use Demo state to explore unavailable and insufficient-evidence outcomes; cancel or retry.
4. Summary: edit generated draft and notes; keep the draft, switch studies, and return.
5. Import CT: use the synthetic folder, select the localizer for an error, then choose the valid series.
   Open the example and choose example analysis separately.
6. Research: preview a general question and return to the retained study.

## Boundaries

All anatomy, measurements, patient-independent study metadata, responses, and source cards are
explicit synthetic examples. The artwork is an illustrative SVG, not a CT, spatially valid mesh,
or medical depiction suitable for interpretation. Plane selection changes the label only; the
slice slider changes the illustration rather than sampling voxels. 3D is an illustration, not an
interactive reconstruction. DICOM import reads no files. Analysis calls no model. The source card
is not a paper or supporting medical evidence. No clinical decisions or patient data are involved.

Drafts remain in memory while this preview is open; they are not durable clinical records and are
cleared on reload. Optional host state retains only navigation/layout choices, not notes or questions.
No production files, scientific contracts, service configurations, or concurrent literature edits changed.

## Review focus

Evaluate the overall hierarchy, dark graphite/violet palette, panther placement, image/assistant
balance, study continuity, and summary destination. Quinton approved Concept 01. The next task maps this design to existing React/NiiVue components using the parent implementation packet.

## Verification performed

- JavaScript syntax check and source/link inspection.
- Browser: rendered synthetic 2D and 3D, panther on silver, reference toggle, source-card interaction.
- Browser: reference-free study, reviewer notes retained after switching away and back.
- Browser: simulated DICOM series rejection, valid series selection, import and analysis transition.
- Browser: narrower desktop and mobile reflow inspected; root had no horizontal overflow at
  observed content widths 977px and 328px. Normal viewport restored after checks.
- Browser: simulated assistant failure and cancellation preserved the question; no browser error logs were observed.
- This is not a production accessibility, medical geometry, imaging, or end-to-end backend qualification.
