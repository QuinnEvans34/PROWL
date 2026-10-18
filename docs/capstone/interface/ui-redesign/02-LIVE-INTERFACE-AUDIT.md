# 02 — Live interface audit

> Fresh baseline note: this remains the earlier audit, not a claim about the latest service behavior. Literature source-record search subsequently advanced on the same branch; see 10 and inspect current code.


Inspected October 18, 2026 at `http://127.0.0.1:5180` using the Codex in-app browser.
Chrome was requested but unavailable through the browser tool. An existing local server was reused.
This is a live visual/interaction audit, not only a source review or review of old screenshots.

## Observed

| Surface | Direct observation | Design consequence |
|---|---|---|
| Landing | PanTS Review branding, large presentation headline, three curated case rows, project storytelling | Make Studies the practical entry; move showcase storytelling into an optional demo tour |
| Navigation | Five destinations; header wraps to two rows in inspected viewport | Use a compact persistent shell and fewer top-level destinations |
| Library | Large hero and study cards; 12 cached studies; live endpoint offline | Prioritize searchable study list, statuses, import and resume; retain compact preview thumbnails |
| 2D workbench | CT and colored overlay rendered in three planes for PanTS_00009005 | Preserve the working viewer and anatomy/source controls |
| Viewer layout | Header, global notice, case header, evidence tabs, and floating controls consume substantial height | Consolidate controls and maximize usable imaging area |
| 3D workbench | CT/overlay rendered after switching mode; anatomy occupies a relatively small region | Investigate fit-to-content and viewport allocation; do not assume a rendering defect |
| Measurements | 15.63 cm³, 31 mm, and 97% confidence displayed for the selected historical case | Preserve provenance; audit meaning/derivation before carrying labels into redesign |
| Expert access | Multiple evidence accordions beneath the scan | Replace fragmentation with one contextual assistant surface |
| Research route | Separate page with Back to PROWL; free-text literature composer; 14-paper description; old demos below | Keep research in the application shell and use the current free-text capability |
| Return from Research | Back to PROWL returns to demo landing | Restore study/view context when moving between research and workbench |
| Offline status | Prepared results remain visible, live endpoint says offline; library headline still says Score it live | Align primary actions and wording to actual capabilities |

## Interaction evidence and limits

- Opened a prepared positive study from landing; visually observed 2D scan/overlay and 3D rendering.
- Opened Research; entered then cleared a general literature question. Ask became enabled.
- Did not submit an AI request, start inference, upload data, write a review, or export a file.
- Opened Scan library and inspected its offline/cached state.
- No claim of backend answer quality, import readiness, responsive acceptance, keyboard audit, or
  reference-free operational flow verification. Screenshots were inspected in tool output, not archived here.

## Source review corroboration

- `ui/src/main.jsx`: `/research` and `/saved` render independent top-level components.
- `ui/src/App.jsx`: historical branding, curated copy, library logic, and legacy local review statuses.
- `ui/src/components/ReviewWorkspace.jsx`: reusable viewer controls and evidence panel integration.
- `ui/src/components/LiteratureSearchPanel.jsx`: free-text request and cited-answer validation,
  cancellation/timeout behavior, explicit scan-context and measurement-unavailable handling.
- `ui/src/components/ResearchDemo.jsx`: current literature panel plus older guided prototypes.
- `ui/src/index.css`: existing navy/teal custom CSS, not evidence of an installed shadcn/Tailwind system.

Correction to the first conversational assessment: constrained question panels still exist, but
the current Research route also has a newer free-text literature interface. Preserve its validators.
