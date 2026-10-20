# 09 — Acceptance and delivery checklist

Use IDs in Claude's handback. Status values: passed, failed, blocked by named dependency, not exercised.
A screenshot proves appearance, not backend readiness. Never mark an unimplemented dependency passed.

## Milestone A — shell and visual system

- A01: PROWL branding and original panther; approved graphite/silver/violet hierarchy recognizable.
- A02: Studies, Workbench, Research share shell; active study survives navigation/back-forward.
- A03: Browser titles and user-facing branding updated; historical scientific IDs remain unchanged.
- A04: No production anatomy replaced by prototype drawings; no fixture claims in ordinary review.

## Milestone B — real workbench

- B01: Prepared and native saved packages still validate/load; failures are explicit, resources released.
- B02: Actual CT in 2D/3D with working slice, plane, pan/zoom, contrast, fit, anatomy and layer controls.
- B03: Optional reference behaves correctly: present, absent, incompatible, and not allowed by mode.
- B04: No-reference study reaches review summary; no required comparison step or reference-only metrics.
- B05: Empty predicted lesion differs from missing prediction/failed analysis; no healthy conclusion.
- B06: Geometry and source/prediction identities stay attached to measurements; unavailable values stay unavailable.
- B07: Typing in assistant/summary does not remount viewer or reset its supported view state.
- B08: Split works with supported synchronized data or is explicitly recorded as blocked, not faked.

## Milestone C — assistant and research

- C01: Existing written-answer and source-search paths still pass their distinct validation tests.
- C02: Loading/cancel/retry/unavailable/insufficient states; input and available evidence survive failures.
- C03: Study switch during request cannot attach late evidence to another study.
- C04: Claims link to exact passages and attribution; no invented sources, confidence, medical findings.
- C05: Literature-only capability is visible; no implication of image understanding or conversational memory.
- C06: Opening source and returning preserves study, viewer, and draft.
- C07: Demonstration scenarios are explicitly labeled, isolated, and never an automatic live fallback.

## Milestone D — import and summary

- D01: DICOM series-selection/error UI, cancellation, duplicate/invalid input and service-unavailable states.
- D02: Live import only succeeds through real validated adapter; missing conversion is documented blocked.
- D03: Prepared cases remain accessible when import/inference is unavailable; upload does not start analysis.
- D04: Summary derives only available facts; no observations fabricated before a prediction exists.
- D05: Human edits/notes preserved across tabs and study changes; stale target handled explicitly.
- D06: Reset/regenerate cannot silently discard edits; dirty navigation has clear discard/stay handling.
- D07: Session draft distinguished from durable save; failure retains draft; Saved requires actual receipt.

## Milestone E — presentation and handback

- E01: Desktop 1440×900 and 1280×720; 1024 wide; small viewport; 200% zoom. No clipped essential controls.
- E02: Keyboard-only import, assistant, source drawer, summary; modal Escape/focus restoration checked.
- E03: Contrast measured for text/actions/focus; selected/error states not conveyed by color alone.
- E04: Reduced motion respected; no layout jump or scan disappearance while assistant is pending.
- E05: Screenshots of studies, actual workbench, no-reference review, assistant/source, import and summary.
- E06: Actual test commands, result counts, console/network errors, limitations and dependencies reported.

## Validation execution

Use the supported Node version from `ui/.nvmrc` (24.21.0 at packet preparation), not an arbitrary
system Node. Read `ui/README.md` and current test configs. Preserve lockfile unless a justified
explicit dependency change is required. Install from lockfile only when needed.

From `ui/`, appropriate existing commands include `npm run test:run`, `npm run build`, and
`npm run test:e2e`. Inspect what each test starts before invoking it: browser configs use local
fixture services and fixed ports. Coordinate port ownership rather than killing existing services.
Use targeted tests while implementing, then the appropriate final UI regression set. Do not run
training or unrelated massive Python suites for a layout change.

The default browser fixture stubs NiiVue: passing it does not verify real CT rendering, geometry,
or 3D performance. Inspect at least one permitted prepared CT and the native saved-view path where
available. If data/drive/service is unavailable, report exactly which verification remains blocked.
Use synthetic fixtures to exercise unsafe-to-trigger failure states; never induce actual data loss.

## Required final handback

Create `IMPLEMENTATION-HANDBACK.md` here with: milestone/acceptance ID status, file/commit summary,
working features, explicit fixture-only features, named backend dependencies, test outputs, screenshot
locations, known issues and integration guidance. Preserve failed-check evidence; no completion claim
based only on a build passing. Do not include patient data in screenshots or public outputs.
