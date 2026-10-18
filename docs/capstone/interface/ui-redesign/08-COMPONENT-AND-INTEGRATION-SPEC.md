# 08 — Component and integration specification

Status: implementation handoff v1.0. Concept 01 is approved; exact component names below are suggestions.

## 1. Preserve the system, replace its presentation

React 18, Vite, NiiVue, Lucide React, and custom CSS are the installed UI foundation. Do not introduce
Next.js, another rendering engine, a CSS framework, or a component-library migration just for styling.
Use existing dependencies and ordinary React components. Keep the prototype separate and unchanged.

| Existing seam | Implementation treatment |
|---|---|
| `ui/src/main.jsx` | Place existing routes within shared shell; retain `/research` and `/saved` compatibility |
| `ui/src/App.jsx` | Extract shell/study selection/loading incrementally; preserve real prepared-case loading |
| `ui/src/components/ReviewWorkspace.jsx` | Reorganize existing controls into approved workbench; preserve behavior |
| `ui/src/components/NiivueViewer.jsx` | Keep real image/mesh rendering; avoid rewriting numerical or affine logic |
| `ui/src/lib/reviewState.js`, `viewerLayers.js` | Preserve source/anatomy rules; adapt presentation state carefully |
| `SavedPredictionView.jsx`, `savedPrediction.js`, `nativeGeometry.js` | Retain validated native saved-package loading and cleanup; surface under shell |
| `LiteratureSearchPanel.jsx` | Preserve answer AND source-search flows, validators, request identity, timeouts and error behavior |
| `ResearchDemo.jsx` | Present current research tools inside shell; move older demos behind an explicit demo entry |
| `GuidedEvidencePanel.jsx`, `ResearchEvidencePanel.jsx`, `ResearchWorkflowPanel.jsx` | Preserve supported capabilities; do not merge distinct services into an invented universal endpoint |
| `ui/src/index.css`, `GuidedEvidencePanel.css` | Migrate to scoped semantic tokens; eliminate conflicting historical styles only after parity |
| `ui/tests/` | Adapt selectors deliberately; preserve substantive regression assertions |

Suggested components: AppShell, StudyList, StudyHeader, ImportStudyDialog, ViewerToolbar,
ViewerLayout, LayerControls, FindingInspector, AssistantPanel, EvidenceDrawer, ReviewSummaryEditor,
CapabilityNotice. These are boundaries, not a demand to create a file for every label.

## 2. Shell and navigation

- Use compact PROWL wordmark, persistent Studies/Workbench/Research navigation, active-state underline.
- Studies is the ordinary entry; returning from Research restores the active study and view.
- Workbench without a study offers Import CT or Open example; no invented patient header.
- Keep existing deep links usable. Use URL-backed navigation/history where feasible without replacing
  the app stack. Back/forward must not silently discard a draft. Keep study state above route content.
- Technical hashes live in a provenance disclosure; essential study/series/prediction identity stays visible.
- Preserve a concise research-use indicator; retain material capability/failure notices at the action.

## 3. Visual tokens and logo

Implement the tokens and appearance from 04 and the approved prototype. Extract reusable tokens for
surface, raised surface, border, primary/secondary text, action, focus, danger, and scientific layers.
Use graphite surfaces, restrained violet primary actions, modest radii, and consistent spacing.
Use Lucide icons consistently; replace prototype text glyphs where appropriate with labeled controls.

The approved logo is `PROWL_LOGO.png` at repository root. Copy it into a suitable UI public asset path
without altering the original, then reference it by a deployable asset URL. Silver backing is part
of the approved black-panther treatment. No panther watermark over CTs or scientific exports.
Preview existing asset before changes; preserve aspect ratio. No logo regeneration is needed.

Brand accent does not redefine scientific colors. The prototype uses mint/amber illustrative regions;
retain current actual pancreas/lesion/reference mappings until deliberately checked against legends,
visibility, color-vision differences, and existing tests. Do not silently relabel a red lesion layer.

## 4. Imaging and findings

- Replace the prototype SVGs with the real NiiVue viewer. Keep CT intensity/windowing, source masks,
  native-space geometry checks, slice navigation, orientation labels, pan/zoom, and 3D controls.
- Expose 2D, 3D, and Split layouts. For real Split, synchronize supported crosshair/plane/view state
  through an adapter and avoid duplicating expensive volume loads. If current NiiVue integration
  cannot support this safely yet, keep real 2D/3D and explicitly report Split as an integration dependency.
- Existing multi-planar mode and anatomy jump controls remain discoverable, not lost in the redesign.
- Keep imaging instances stable while typing, receiving an answer, resizing panels, and editing summary.
- Findings selection and inspect-measurement controls target an actual structure only when mapped.
- UI must not calculate new anatomical lengths from a visual bounding box. Use validated source values
  with units, method, source type, target identity, and availability. Missing does not mean zero.
- Never relabel the legacy volume-derived approximate diameter as measured pancreas width/length.
- No derived measurements or candidate regions before prediction publication. Stale predictions remain
  labeled with their actual version; a running job does not replace them with a fabricated new result.

Reference modes depend on both validated availability and the package's allowed mode. Hide compare
when unavailable; display no reference-free Dice or TP/TN claims. Failed localization, empty prediction,
missing mask, and service failure remain distinct. Neither an empty prediction nor an empty reference
establishes healthy tissue. Preserve exact scientific provenance outside the primary reading path.

## 5. DICOM import: designed requirement, integration dependency

The inspected autonomous pipeline explicitly accepts mm NIfTI and requires separate DICOM conversion
(`src/inference/autonomous_cascade_v1.py`, `run_case`). No integrated DICOM uploader was established
by this audit. Do not assume it exists, and do not implement unreviewed conversion inside UI components.

Implement the reusable dialog and state model now:
`idle → selecting → validating → series_selection → importing → ready` with `cancelled` and `failed`.
Use only adapter-reported progress. Never display a timer-driven successful import in live mode.

A proposed FRONTEND adapter (not an existing endpoint) should expose:
- capabilities: supported inputs, local/remote handling, cancellation and import availability;
- inspect(selection, signal): candidate study/series metadata, warnings, eligibility and explanation;
- importSeries(selectedIdentity, signal): validated study handle/package or an explicit failure;
- stage notifications only if the ingestion service can report them.

Series identity, modality, orientation, spacing, instance ordering/completeness and geometry belong
in the ingestion validator. The UI displays its results; it must not repair or guess them. Selecting
files must not send them to an unapproved remote service. Retain NIfTI/prepared-case entry.

If no real adapter exists: render an honest unavailable state with prepared-case entry and a separately
labeled DICOM example walkthrough. Deliver the adapter interface and required backend contract as a
specific dependency. Do not claim the initial DICOM requirement complete. Continue independent work.
No PACS, hospital registration, scanner control, cloud upload, or new conversion dependency is implied.

## 6. Assistant integration

Findings / Ask PROWL / Summary share one panel. Keep current free-text research functionality and its
source-only search, not just the historical two-review demos. Read the newest component before editing.
`/literature-search/answer` and `/literature-search/query` have distinct validators and semantics.
Do not route a source-only result through answer validation, loosen pins, or drop qualifications.

- Display current capability: general literature versus validated scan facts. No scan access is implied
  by being beside the viewer. Do not send image payloads or case context to a literature-only endpoint.
- Surface exact cited passages with attribution/rights, available source links, and a back action.
- Maintain request IDs, abort/timeout handling and late-result rejection; preserve retrieved passages
  when generation fails and the valid response permits it.
- Show actual stages only if supplied. Otherwise use an honest pending indicator with elapsed time,
  cancel, retry, and reduced-motion support. Do not show fabricated percent, ETA or hidden reasoning.
- Preserve current single-question service behavior. A visible history can show independent requests;
  don't imply conversational memory without a backend contract supporting it.
- Static examples belong only to explicit demo mode and synthetic study IDs. Live service errors never
  silently substitute canned answers. Demo state selectors do not appear in normal review mode.

## 7. Review summary and state ownership

Draft key: study identity + selected series + prediction identity, using existing stable IDs. Store
human edits separately from derived observations. The summary can initially be deterministically
assembled from validated structured facts; do not require or pretend LLM generation.

Suggested UI draft fields (FRONTEND model only, not a new scientific schema): target identity,
source-fact references, editable observation text, reviewer notes, evidence references, dirty state,
and persistence status. Do not replace canonical review-event schemas or create fake durable receipts.

- Switching sections retains drafts. Switching studies isolates them; mark incompatible versions stale.
- Reset/regenerate requires an explicit choice if edited. Preserve notes; offer replace/discard choices
  without silently overwriting work. Never insert literature claims as patient observations.
- In-memory drafts may ship if labeled unsaved/session-only; warn on navigation/reload when dirty.
  Do not store patient text in localStorage by default. If a durable writer already exists, use its
  reviewed contract; display Saved only after a verified receipt. Otherwise report durable save as pending.
- No signature, clinical finalization, automated diagnosis, or report-system integration.
- Existing review-decision actions remain available with honest persistence semantics. Summary editing
  is additive; legacy local statuses are not upgraded to durable reviews by a new label.

## 8. Responsive and accessibility behavior

At 1440×900: spacious central viewer, approximately 340–365px assistant, optional collapsed study list.
At 1280×720: avoid stacked marketing/navigation rows; keep core viewer controls visible; use independent
panel scrolling for the production app where needed. Do not shrink anatomy to fit all prose at once.
At 1024 wide: collapse optional study navigator; allow explicit assistant collapse/expansion. Never
silently hide one side of a selected Split layout (a prototype shortcut to improve in production).
At small widths/200% zoom: reflow to viewer then assistant or an accessible drawer; no inaccessible controls.

Keyboard: navigable toolbar, labeled icon buttons, visible focus, dialog focus trap and restoration,
Escape dismiss, no hover-only measurements, logical landmark/headings. Announce async status once,
not each animation frame. Measure text and control contrast; respect reduced motion.

## 9. Work boundaries

Allowed implementation area: UI components/styles/assets, UI test fixtures/config where needed, and
this package's progress/handback notes. Backend APIs, scientific schemas, acquisition, inference,
training, corpus, source policies and patient persistence are dependency work, not implicit redesign scope.
If a narrow integration change is necessary, state the concrete contract gap and coordinate its owner.
Do not roll back current literature work to the audit baseline. Do not copy the prototype's single-file
DOM renderer, simulated timers, or illustrated anatomy into the production React application.
