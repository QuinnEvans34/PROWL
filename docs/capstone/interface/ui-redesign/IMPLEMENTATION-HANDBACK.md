# PROWL UI redesign — implementation handback

Version 1.0 · October 18, 2026 (America/Denver) · Implemented by Claude with Quinton.
Branch: `claude/prowl-ui-implementation`, created from `96c7943` on `codex/prowl-ui-redesign`
(includes design handoff `70ad7a2` and the four later literature commits, all preserved).
Local commits only. Nothing pushed, merged, or deployed.

| Commit | Milestone |
|---|---|
| `ebf30cc` | A — Shell, tokens, branding, Studies |
| `9fc1abc` | B — Real NiiVue workbench, optional reference, Split |
| `0034224` | C — Integrated Ask PROWL assistant, Research in shell |
| `6a5dcc3` | D — DICOM import boundary, editable session summary |
| (this commit) | E — Verification fixes, screenshots, this handback |

Decisions confirmed with Quinton during implementation:
- New branch with one local commit per milestone.
- Verify real CT through the existing dev server on port 5180, viewed in the desktop app's browser pane.
- Keep the curated three-case presentation as an optional **validation layer**.
- Build Split as **two linked NiiVue instances**.

## What changed

**Shell (A).** `AppShell` provides the PROWL wordmark, Studies / Workbench / Research navigation, live-analysis status, an About dialog, and a slim research-use footer. A history-backed router (`lib/router.js`, no new dependency) keeps `/research` and `/saved` deep links working and stores the active study in `?study=`. Back/forward and reload restore it. The Workbench stays mounted while the reviewer visits Research, so the viewer, layers, questions and drafts survive the round trip. Concept 01 tokens live in `styles/tokens.css`. The legacy `index.css` variables are remapped onto them, and the Google Fonts import is replaced by the system stack. `PROWL_LOGO.png` is copied byte-identical to `ui/public/brand/prowl-panther.png` and framed with CSS only. Studies is the entry page: welcome section with the panther on silver, a searchable and filterable table, thumbnails, honest status labels and draft flags.

**Workbench (B).** The layout is a collapsible study list | study bar, toolbar, full-bleed viewer, layer bar, slice and cutaway bars | PROWL Assistant (Findings / Ask PROWL / Summary). All existing viewer behavior is preserved: the reducer, navigation commands, clip, focus and Go to. Controls moved out of overlays that covered the scan.

Reference states:
- **absent** — "review is complete without one"
- **locked** — hidden until a prediction is shown on prepared studies
- **permitted** — Compare with reference available
- **ready** — Both / Model / Reference / Difference controls, Dice in Findings
- **incompatible** — explained, never overlaid

Findings show validated values only:
- Pancreas volume reads "Not published in this prediction package."
- Lesion: predicted mask volume, plus an equivalent spherical diameter labeled *derived*.
- The peak model score sits under provenance, marked "not a probability."
- An empty prediction says it does not establish absence.

Split mounts two NiiVue instances (2D planes and 3D surfaces) that share layers, selection, Go to, reset and window. The 3D camera is independent. NiiVue's multiplanar layout is pinned to ROW, which fixes a pre-existing bug where tall viewers switched to a 2×2 grid and the plane labels sat over the wrong views.

**Assistant and Research (C).** `LiteratureSearchPanel` gains `variant="panel"`. The answer path (`/literature-search/answer`) and source-only path (`/literature-search/query`) keep their separate validators, request IDs, 90 s timeout and error semantics unchanged; all 47 existing tests pass untouched. The panel adds:
- a scope line: "Literature only · Scan context not connected"
- a stated limit: no memory of earlier questions
- suggested general questions that target reviewed comparisons and never auto-submit
- a panther halo and Ask-tab indicator while a request is pending
- study-switch cancellation (late results discarded, question kept), with earlier general answers labeled "not about the current study"

The Research page sits inside the shell with retained-study context and a return button. The older guided and fixture demos are behind an explicit **Show demonstrations** entry. Validation comparison (`?layout=compare`) shows prediction, reference and combined overlay views with Dice for validation examples, one plane at a time.

**Import and summary (D).** `lib/importAdapter.js` defines the frontend adapter contract and error codes. Live mode shows an honest unavailable state, with no file picker. A dashed **EXAMPLE** walkthrough steps through choose → check → series selection (ineligible localizer and dose report, thick-slice warning) → import outcomes (success, conversion failure, duplicate) → cancellation. **Ready** is reachable only through an explicit result; no timers simulate success. Dialogs trap focus, close on Escape and restore focus.

Summary drafts (`lib/summaryDraft.js`, `ReviewSummary.jsx`):
- Keyed by study + series + prediction identity, generated deterministically from validated findings only.
- Human edits and notes are stored separately from the generated text.
- Regenerating over edits requires an explicit Replace or Keep choice; notes are never touched.
- Drafts written for an earlier prediction are kept and labeled.
- Persistence is **session-only**: in memory, never `localStorage`, with an "Unsaved · session only" pill.
- Save review stays disabled until a durable writer and receipt contract exist. Copy and Download .txt work.
- A reload/close warning appears when a draft has human content.

## Working vs example-only

| Capability | Status |
|---|---|
| Prepared CT 2D/3D/Split, layers, Go to, window, cutaway | Working on real CT |
| Show saved prediction (explicit) | Working; labeled "Saved prediction" |
| Live Analyze (`localhost:8000/predict`) | Wired; endpoint offline during verification, so not exercised |
| Reference compare + Dice | Working on real data (e.g. PanTS 9258: pancreas 0.826, lesion 0.907) |
| Ask PROWL answer + Find sources | Working against the live service on 8016 (7 s answer, 5 sources) |
| Research page, validation comparison | Working on real data |
| DICOM import | **Example only.** Live adapter blocked (dependency 1) |
| Review summary | Working, session-only. Durable save blocked (dependency 2) |
| Native saved-package view `/saved` | Route works; failure is explicit. Real package not exercised |

## Acceptance status (09)

| ID | Status | Evidence / notes |
|---|---|---|
| A01 | passed | Logo byte-identical (`cmp`); tokens contrast-measured (below) |
| A02 | passed | Real: Research round trip kept the canvas and slice; back/forward restores `?study=` |
| A03 | passed | Titles "Studies · PROWL", "PanTS 00009005 · Workbench · PROWL"; scientific IDs unchanged |
| A04 | passed | No prototype anatomy; synthetic data only inside the labeled import example |
| B01 | passed (prepared) / not exercised (native load) | `/saved` shows an explicit 404 because `PROWL_SAVED_PREDICTION_DIR` is unset; savedPrediction unit tests pass |
| B02 | passed | Real CT: 2D, 3D, slice, plane, window, fit, Go to, layers. Pan/zoom drag gestures not exercised by hand |
| B03 | passed | Present / locked: real. Absent / incompatible: unit tests (all 12 prepared studies have a reference; none is incompatible) |
| B04 | passed | Unit: no Compare, no Dice, review summary reachable without reference |
| B05 | passed (UI) | Empty vs missing vs failed shown as distinct text; live analysis failure not exercised (endpoint offline) |
| B06 | passed | Values come from validated manifest/live fields only; unavailable stays unavailable |
| B07 | passed | Real: typing 16 characters in notes kept the same canvas and slice with 0 CT refetches |
| B08 | passed (scoped) | Two instances share layers, selection, Go to, reset, window; 3D camera independent; no 3D crosshair |
| C01 | passed | 47 existing literature tests unchanged + live answer validated |
| C02 | passed | Unit: loading, cancel, retry, timeout, insufficient evidence, generation failure. Live failure not exercised |
| C03 | passed | Unit: study switch aborts, discards late result, keeps question |
| C04 | passed | Live: citation [1] focuses the exact source with attribution, CC BY, PMID, DOI |
| C05 | passed | Scope line + "do not remember earlier questions" |
| C06 | passed | Real: source open; URL and viewer unchanged; external links open in a new tab |
| C07 | passed | Demos behind explicit entry; no canned fallback in live paths |
| D01 | passed (example) | Unit + visual: series selection, ineligible, failure, duplicate, cancel, unavailable |
| D02 | **blocked** | Dependency 1: DICOM ingestion service and adapter |
| D03 | passed | Prepared studies always accessible; no file selection exists that could start analysis |
| D04 | passed | Unit: no observations without a prediction; no "normal/healthy/benign" wording |
| D05 | passed | Unit + real: edits survive tab and study switches; earlier-prediction drafts labeled |
| D06 | passed | Regenerate requires a choice. In-app navigation never discards drafts (they live above routes); reload/close warns |
| D07 | passed / durable save **blocked** | Session draft clearly labeled; no Saved state exists without a receipt (dependency 2) |
| E01 | passed (synthetic) / partial (real) | Synthetic UI at 1440×900, 1280×720, 1024, 390, 200% zoom; no page-level horizontal scroll. Real CT checked at about 800 px pane width only |
| E02 | passed | Scripted keyboard: skip link, import dialog trap / Escape / focus restore, assistant tabs with arrows, citation, summary |
| E03 | passed | axe-core 4.10.2: 0 violations on 7 screens; contrast table below; selected state uses an inset bar, not color alone |
| E04 | passed | `prefers-reduced-motion`: animations collapse to 1e-5 s × 1, transitions 0 s; pending state changes only the panel |
| E05 | passed | Screenshots below |
| E06 | passed | This document |

Contrast (WCAG ratio on surface `#15181D`): text 15.9, muted 8.2, faint 5.8, accent 8.3, ink-on-accent 8.5, control border 3.5 (3.2 on raised).

## Test results

- `vitest run` (Node 24.21.0, lockfile install): **10 files, 110 tests passed**. Baseline before work: 7 files, 96 tests. New: reference states, Split, Ask panel isolation, summary, import.
- `vite build`: passed. `npm run build`'s `prepare-sites-build.mjs` step was not run in my mirror because it lacked `ui/.openai/hosting.json`. That's a mirror gap, not a code change; please run `npm run build` locally once.
- Playwright `tests/browser/workspace.spec.js`: **1 passed**, using a scratch config that starts only the stub fixture (selector updated deliberately for the inert study list).
- **Not run:** `guided-evidence`, `research-evidence`, `grounded-answer` browser specs (they need the Python fixture services from `.venv-prowl`), plus the `saved-browser` and `workflow-browser` configs. Please run `npm run test:e2e` on the Mac.
- Console on real CT: no application errors. Expected: `ERR_BLOCKED_BY_CLIENT` for the `localhost:8000` probe in the pane. Transient HMR 500s only while files were mid-sync. Dev StrictMode double-loads each volume (cache hits); production loads once.

## Screenshots

- Synthetic UI, committed: `implementation-screenshots/synthetic-*.png` (stub viewer, synthetic manifest, no patient data). Covers workbench 1440/1280/1024/390, Ask idle / answer / source, Research, Summary, Studies with draft, Import live / example series, 200% zoom.
- Real CT, local only (git-ignored): `outputs/prowl/ui-redesign-real-ct/` — Studies, 2D workbench, Split, live Ask + source, validation comparison, and the pre-redesign landing. Not committed, because they are CT images.

## Named backend dependencies

1. **DICOM ingestion service + adapter.** Must implement `capabilities / inspect / importSeries` and the error codes in `ui/src/lib/importAdapter.js`, including series identity, modality, ordering/completeness and geometry validation. Swap `unavailableAdapter` for the real adapter in `ImportStudyDialog`.
2. **Durable review persistence.** A reviewed writer that returns a receipt. Pass `persistence={{ available: true, save }}` to `ReviewSummary`; show Saved only after a verified receipt.
3. **Scan-aware assistant context.** A validated structured-facts endpoint. Until then the scope line stays.
4. **Validated pancreas measurements.** Pancreas volume (and any length/width) published in the prediction package.
5. **Reference compatibility check for prepared packages.** Currently assumed compatible, since the same exporter produces both masks. `referenceCompatibility` is the prop seam.
6. Optional: 3D crosshair in Split (`show3Dcrosshair`), which needs a viewer-options change in `NiivueViewer`.

## Known issues and integration notes

- `index.css` still holds about 4.6k lines of legacy styles, many now unused. Retire them after parity review (08 §1).
- `ResearchDemo.jsx` is no longer imported. It was kept rather than deleted.
- Validation examples preload reference and difference volumes before comparison (pre-existing behavior; not displayed).
- The study list auto-collapses below 1360 px; the assistant is a drawer below 1024 px.
- `NiivueViewer.jsx` changed only by one display option (`multiplanarLayout: 3`). No numerical or affine code changed.
- No backend, model, corpus, dataset, configs, training or service files changed. Only `ui/` and this package were touched.
