# Workbench polish pass — November 20, 2026

Status: implemented on the main checkout, after Quinton's walkthrough feedback.
Phase: polishing, not building. Earlier record: `WORKBENCH-RADIOLOGIST-TOOLSET-SPEC-20261120.md`.

## Decisions (Quinton, November 20)
| Question | Decision |
|---|---|
| Top navigation | **Studies · Workbench** plus a ⚙ menu |
| Organ names | 2D hover tag + 3D legend with highlight |
| Logo | Panther mark + PROWL wordmark |
| Assistant panel | Redesign in the app, review from screenshots |
| CT brightness/contrast drag tool | Remove (presets stay) |

## What changed
- **Header (`shell/AppShell.jsx`, `shell/Brand.jsx`):**
  - Primary navigation is Studies and Workbench.
  - The ⚙ menu holds the AI expert controls (Prepare AI expert / Check status, the same `LocalExpertReadiness` component).
  - The menu also links to the pages taken out of the bar: Analyze (live inference), Saved reviews, Research and Training.
  - No route or page was deleted; old URLs still work.
  - The wordmark is the silver panther silhouette plus "PROWL"; the "Pancreatic review" descriptor was dropped.
- **Window tool removed:** the drag-to-adjust brightness/contrast mouse tool is gone from the toolbar. A session that still has it selected falls back to Navigate. The window presets (Soft tissue, etc.) remain.
- **2D hover tag (`NiivueViewer.jsx`, `lib/studyInsights.js#hoverStructureNames`):**
  - Names the structure under the cursor, sampled from the loaded label volumes.
  - Model lesion/pancreas are labelled "model"; the reference outline and reference anatomy are labelled "reference".
  - Up to three names, most specific first. It hides during drags.
- **3D structure legend (`structureLegend`):**
  - Lists the drawn structures.
  - Hovering previews a structure and clicking pins it; every other surface fades to 12%.
  - It hides in compact panes and in difference mode.
- **Aorta colour:** red → light silver (#D6DEE9). In 2D the aorta sits beside the lesion and read as a second lesion. The pipeline colour and 9005's existing curved-view overlay were updated to match.
- **Assistant panel (`styles/assistant-refresh.css`, `ReviewWorkspace.jsx`, `LiteratureSearchPanel.jsx`, `ReviewSummary.jsx`):**
  - Slimmer header showing the study ID.
  - The current finding is a slim card with a coloured edge. When findings exist, its second line reads e.g. "3.6 × 2.9 cm · pancreatic body · model proposal".
  - Tabs are a segmented control.
  - Ask tab:
    - Up to three starter questions built from this study's findings (`studyQuestionSuggestions`), worded as general literature questions with no patient details.
    - Two general questions below them.
    - Clicking a starter only fills the composer; it never sends.
    - The scope and privacy notes moved under the composer.
  - Summary tab: shows the structured findings the draft can draw on before "Start draft from findings".
- **2D ↔ 3D:**
  - Studies still open in 3D Abdomen.
  - Once the 3D scene has loaded, the 2D planes mount in the background (after 1.5 s), so the first switch to 2D does not start a fresh load.
  - Both views stay mounted, so slice and camera persist across switches.
- **Capture script:** hides the legend and hover tag in clean captures.

## Not changed, and why
- **Shared in-memory volume cache:** not built. Each viewer instance parses its own NIfTI through NiiVue's loader. Sharing parsed volumes would mean rewriting the load path that 34 viewer tests cover. The background 2D mount gives most of the benefit with no risk.
- **Production-build demo mode** (`vite build` + `vite preview`): possible, but the dev-server plugins (AI expert, saved prediction) would need preview-server hooks and the 280 MB `public/cases` folder would be copied on every build. Deferred.
- **Live inference on stage:** recommended against; the GPU is shared with training. The Analyze page stays in the ⚙ menu.

## Verification
- vitest: 611 passed, 7 skipped. New tests cover:
  - Hover names.
  - Legend keys.
  - Study question wording (no study ID or measurements in the text).
  - Starter questions only fill the composer.
  - Navigation through the ⚙ menu.
- `vite build` is clean.
- Headless checks:
  - The ⚙ menu.
  - 3D legend pin (celiac artery highlighted, others faded).
  - 2D hover over lesion, pancreas, aorta and IVC.
  - Ask and Summary tabs.
  - 2D ready about 5 s after switching, in software WebGL.

## Round 2 (evening, from Quinton's second walkthrough)
- **Ask tab is a real chat:**
  - The thread fills the panel and the composer is pinned below it.
  - The panel widens to 460 px while Ask is open and returns to its previous width afterwards.
  - The reviewer's question is a compact bubble; Edit appears on hover.
  - Replies are plain text with a thin rule. The extra details ("How I understood your question", "About this response", Save, Details) sit in one quiet row under the reply instead of stacked boxes.
  - "Clear conversation" moved to the top of the thread; the service note moved into Search tools.
  - The intro hides once a conversation exists.
- **"This outline / Published evidence" switch removed** from Ask; measurements live in Findings. `FindingAskPanel` stays in the repo, unused.
- **Summary tab says where the draft comes from:** it is assembled by PROWL from the model outline and the dataset reference anatomy. No AI writing; drafts stay in the browser session.
- **Anatomy legend moved off the scan into the layer bar:**
  - The ▴ next to "Anatomy ref" opens a menu naming every annotated structure, with its lesion contact (e.g. "Encasement · 228°", "12 mm from lesion") or duct calibre.
  - Each structure can be hidden.
  - Hovering previews a highlight and clicking a name pins it, in both 2D (others dim) and 3D (others fade).
  - In 2D, hidden structures are removed from a copy of the label data, because NiiVue still outlines zero-alpha labels.
- **Inspect CT slice:** the crosshair is hidden in the single-pane inspection view.
- **"Go to Pancreas / Lesion" removed** from the layer bar. Findings → Inspect measurement still opens the measured slice. The capture script uses that instead.
- **Study naming:**
  - Studies show a name, "Case 9005" by default; the reviewer can rename it with the pencil on the study title (saved in this browser).
  - A descriptor line reads e.g. "CT abdomen · Arterial phase · M, 77", from `scripts/add_study_descriptions.py` (manifest phase/sex/age; blanks are left out, never guessed).
  - The dataset ID stays visible in small mono text and in the tooltip, and is still the identity for routes and files.
  - The "TEST-SET EXAMPLE" badge is replaced by that line; the tooltip says "PanTS held-out test set".
  - Studies search matches names, descriptors and IDs.

Verification: vitest 613 passed / 7 skipped (new: anatomy menu, study names); build clean. Headless checks:
- A mocked two-turn conversation.
- The anatomy menu with the aorta hidden and the celiac artery highlighted.
- The studies list and study bar.
