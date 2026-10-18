# 06 — Implementation sequence and acceptance

> Handoff update: the visual prototype milestone is complete and approved. Proceed to real UI implementation under the current 07 prompt and detailed 08/09 specs. This supersedes the earlier future-work-only status below.


Status: implementation sequence; active assignment is the current 07 implementation prompt.

## Sequence

1. **Visual review:** actual logo, workbench mockup, import and summary wireflows; Quinton reacts.
2. **Baseline:** capture current supported viewer behavior, relevant existing tests and screenshots.
3. **Foundation:** scoped design tokens, shared shell, navigation, typography, controls, panel primitives.
4. **Workbench:** reuse NiiVue and existing presentation logic; reorganize controls and responsive layout.
5. **Assistant:** integrate current literature component/validators into the side panel; example-only
   fixtures for missing context; capability-aware states. Preserve backend interfaces.
6. **Import:** implement validated DICOM UX against a real ingestion adapter when available. If not,
   record the dependency and keep prototype behavior explicitly separate. Do not quietly drop DICOM.
7. **Summary:** editable draft, provenance, edit-preserving regeneration and declared persistence/export.
8. **Verification and handback:** scoped regression tests, visual evidence, limitations, integration notes.

Keep steps as small reviewable commits when authorized. Each handback should state changed files,
working versus mocked capabilities, validation, and dependencies. No broad framework rewrite or
NiiVue replacement by default. Do not combine redesign with a scientific schema migration.

## Acceptance scenarios

| Scenario | Expected behavior |
|---|---|
| CT with prediction, no reference | Complete review flow; no fake comparison metrics or required reference step |
| Compatible reference available | Explicit reveal/compare with unmistakable source legend |
| Reference incompatible | Comparison unavailable with explanation; CT/prediction remain usable |
| No lesion prediction | Honest empty result, distinct from failed analysis or missing mask |
| Analysis offline/failed | CT still usable; no fabricated contour or successful completion |
| DICOM multi-series selection | User chooses valid CT series; incompatible inputs aren't silently combined |
| DICOM conversion failure | Recoverable visible error; no half-import presented as ready |
| Assistant lacks scan facts | Scope visible; no answer claiming to inspect this scan |
| Literature response unsupported | Validated insufficient/unavailable state; sources retained where supported |
| Change study mid-request | No late response or measurement contaminates the new study |
| Fixture mode | Example identity obvious in findings, chat, and summary |
| Edited summary regenerated | Human edits preserved or replacement explicitly reviewed |
| Save fails | Draft retained; no Saved state without receipt |
| Navigate Research and back | Active study and supported viewer state retained |
| Keyboard/reduced motion/zoom | Operable controls, clear focus, readable labels, reachable drawers |

## Verification boundaries

Use existing UI unit/browser tests and add meaningful checks for changed behavior. Stub-viewer tests
cannot prove NiiVue rendering or geometry. Verify real prepared CT in 2D/3D separately. Exercise
1440×900, 1280×720, 1024 wide, and 200% zoom; verify contrast before approving tokens.
No production patient upload, training job, corpus modification, or inference run is required to
prove a CSS/layout change. Coordinate actual ingestion/AI integration tests with their owning lane.

## Remaining planning work

Resolved: logo, approved visual prototype, component boundaries, implementation prompt and acceptance scope. Remaining backend dependencies: validated DICOM ingestion, scan-aware assistant context, durable summary persistence, and any unsupported real split-view synchronization. See 08 and report these explicitly.
