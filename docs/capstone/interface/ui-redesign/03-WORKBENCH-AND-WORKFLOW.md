# 03 — Workbench and workflow specification

> Approval update: Concept 01 is approved as the UX baseline. The production refinements and integration requirements in 08 take precedence over prototype shortcuts.


Status: approved Concept 01 UX baseline; see 08 for production refinements and dependencies.

## Application structure

Persistent shell: Studies, Workbench, Research. Compact PROWL identity, useful service status,
settings/help access. Comparison lives inside Workbench, not a competing destination.
Study identity stays visible while reviewing. Use a study ID in demos; never invent patient details.
Maintain a concise research-use indicator without repeating oversized disclaimers in every panel.

```text
┌─ PROWL ─ Studies / Workbench / Research ─────────── service status ─┐
│ Study / series identity        prediction version    draft status │
├────────────┬───────────────────────────────────┬───────────────────┤
│ Study list │ 2D / 3D / Split    Layers / Tools │ PROWL Assistant   │
│ collapsible│                                   │ Context / scope   │
│            │             CT viewer             │                   │
│            │                                   │ Findings / Ask /  │
│            │       minimal anchored labels     │ Review summary    │
│            │                                   │                   │
│            │ slice navigation / orientation    │ composer/actions  │
└────────────┴───────────────────────────────────┴───────────────────┘
```

This is a structural wireframe, not a final visual mockup. Proposed desktop dimensions: 56px
global header, 44px study bar, optional 200px study list, 360px resizable right panel. At 1280 wide,
collapse the study list by default; retain substantial space for the viewer. At narrower widths,
offer a full-width drawer instead of squeezing three columns. Content and controls must remain
reachable at 200% zoom. No promise of full mobile diagnostic-style review.

## Studies and import

- Default entry: compact study table, search/filter, recent studies, Import CT, Open prepared example.
- Distinguish image-ready, analysis-running, prediction-ready, review-draft, and saved review states.
- Do not sort by inferred disease risk or decorate studies with fake patient identities.
- DICOM flow: choose files/folder → validate → group by study/series → select CT series → inspect
  available metadata/preview → confirm import → convert/load → open workbench.
- Display available modality, series description, instance count, orientation/spacing information.
  Do not presume all are present or all series can be merged.
- Explicit states for unsupported format/modality, ambiguous or incompatible series, incomplete
  input, conversion failure, cancellation, duplicate study, and storage/service unavailability.
- Selecting files must not start model inference silently. Show the study before Analyze.
- NIfTI/prepared-case access remains available. Only expose functional import affordances for
  supported adapters; development mock imports must be visibly labeled and isolated.
- PACS/scanner connection is future scope, not a button implying a working integration.

## Workbench behavior

- Open CT immediately when valid and available; analysis status stays outside the imaging canvas.
- Primary tools: plane/layout, window/level, pan/zoom, fit/reset, source/layers, anatomy focus.
- Keep orientation labels, slice position, and source legend visible. Tooltips supplement labels.
- Proposed layouts: axial/coronal/sagittal, single enlarged plane, 3D, and 2D+3D split.
- Preserve crosshair and meaningful focus across supported mode changes; unsupported mapping must
  not pretend to preserve an exact location. Do not reconstruct the viewer on every chat update.
- Make structure selection update an inspector. Selecting evidence may offer Show in viewer only
  when there is a validated geometry target. Literature alone has no spatial target.
- Hover/click measurement cards must not obscure the anatomy; support keyboard activation, pin,
  dismiss, and an equivalent inspector view. Avoid spontaneous pop-ups during slice navigation.

## Optional reference masks

Normal mode works with CT and prediction only. Reference absent is not a failure or missing step.
Show Compare with reference only when a compatible reference is available and the package permits it.
Prefer the user-facing label Reference annotation over Source of truth; preserve source provenance.
Prediction/reference layers have distinct labels and styles, with a persistent legend in comparison.
Never show Dice, true-positive/negative labels, or discrepancy metrics without eligible reference data.
Incompatible geometry gets an explicit comparison-unavailable state. Do not silently overlay it.
Keep the established explicit reference-reveal behavior for validation demos, not as a required step
in every operational review. Reference availability and mode permission are separate conditions.

## Review summary

Proposed sections: study/prediction identity, available model-derived observations and measurements,
limitations, linked literature where applicable, and reviewer-authored notes.
The radiologist edits the draft. Mark generated suggestions and preserve sources for derived values.
Do not automatically turn a literature statement into a patient finding. Do not auto-insert invented
normal ranges, diagnostic impressions, or reassurance from an empty prediction.
Regeneration must preserve user edits or offer an explicit diff/replace choice. Persist draft state
only through a declared mechanism; saving fails visibly and retains edits. A local draft is not a
signed clinical report. Exact persistence/export formats and review-event relationship remain open.
