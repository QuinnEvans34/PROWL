# Review interface and recorded decisions

**Status:** Native saved-review slice implemented October21; broader workstation acceptance and D-208 dependencies remain\
**Target weeks:** 1 and 7  
**Depends on:** Plans 01, 05–07, 09, 10, and 11; D-208 before a reviewer-ordering score is shown  
**Last reviewed:** 2026-09-18 (testing/stakeholder design handoffs)

Quinton approved P08-01 through P08-18 on 2026-09-09. This locks the interface workflow,
migration, persistence, evidence, accessibility, and verification design. It does not authorize UI
implementation before Plans 09/10 complete the named contracts and environment boundaries.

## October21 implementation update

Quinton brought integration forward to finish existing software. The
[native saved-review slice](REVIEW-INTEGRATION-2026-10-21.md) reuses the current viewer and literature
component with local FastAPI append-only decisions, exact prediction retention, reopen/history and
revisions. Its engineering tests pass; human walkthrough and the wider interface requirements
below remain open. Historical browser-only workbench drafts remain explicitly unsaved; this slice
supports native `/saved` and `/predict` packages rather than inventing durable IDs for legacy results.

## Outcome

Extend the existing React/NiiVue application into a trustworthy PROWL review workstation. A reviewer
can open a full-volume autonomous result, inspect the CT and source-space contours, understand
measurements and warnings, request bounded literature evidence, and persist an `accept`,
`edit_required`, or `reject` decision against the exact immutable prediction version.

This is an integration and workflow project, not a greenfield visual redesign. The existing
viewer-first interface is the starting asset. Capstone work replaces historical demo contracts and
browser-only status with the approved case-package, evidence-response, and append-only review-event
boundaries.

## Why this plan exists

The existing interface is visually capable, but its current scientific and persistence boundaries
belong to the preceding project:

- `ui/public/cases/results.json` combines prediction, reference, evaluation, and presentation fields.
- `App.jsx` contains historical case narratives and calls a fixed development FastAPI URL directly.
- `reviewed`/`discussion`/`unreviewed` is stored in `localStorage`; it is not a durable review event.
- the existing live response is not the shared case-package contract;
- references and Dice are central to curated demo cases, while ordinary capstone review must work
  without a reference annotation;
- evidence-response rendering and citation/refusal states do not exist;
- the UI has a production build command but no automated test command.

The capstone should keep the strong NiiVue interaction and visual language while repairing these
boundaries deliberately.

## Core mental model

```text
validated case package
        |
        v
prediction-first inspection ---- optional validation-only reference reveal
        |
        +---- optional structured evidence request --> cited evidence or refusal
        |
        v
review draft --> validated append --> durable receipt --> immutable review history
```

The UI is a renderer and event author. It does not recompute scientific measurements, invent an
ordering score, transform a failed analysis into a blank contour, or decide whether literature is
adequate. Those conclusions arrive as versioned artifacts from their owning components.

## Scope

- Inventory and preserve the working React/NiiVue viewer, reducer, layers, and display assets.
- Replace the historical `results.json` domain dependency with a transport-neutral case-package
  adapter.
- Render autonomous results, measurements, warnings, evidence/refusal, and review history.
- Implement real accept/edit-required/reject semantics and append-only persistence.
- Maintain explicit operational-review and validation/demo modes.
- Define keyboard, accessibility, responsive, loading, failure, stale-version, and offline behavior.
- Prepare representative fixture packages for implementation, stakeholder review, and regression.
- Make only bounded Week 7 visual/workflow changes supported by Plan 11 findings.

## Non-goals

- Rebuilding the application or replacing its visual system.
- Multi-user accounts, permissions, work queues, concurrent annotation, PACS, or clinical deployment.
- In-browser voxel/contour editing in the committed workflow.
- Treating a reference annotation as required input for review.
- Recomputing Dice, volume, diameter, confidence, or evidence quality in JavaScript.
- Showing a reviewer-priority score before D-208 freezes its meaning and operating policy.
- An unrestricted clinical chatbot.
- Hiding failures, difficult cases, missing evidence, or unsupported browser capabilities.

## Existing assets to preserve

- React 18 and Vite application shell.
- NiiVue 2D/3D viewer integration.
- Explicit `reviewReducer` display-state model.
- Viewer-first Review Workspace layout and collapsible study drawer.
- CT/prediction/reference/overlap evidence modes.
- Direct pancreas/lesion selection, source focus, discrepancy surfaces, display presets, and slice
  navigation.
- Progressive reference reveal for non-curated cases.
- Honest curated positive, negative, and false-positive examples as historical regression material.

Preservation does not mean every component remains untouched. It means refactoring starts from
working behavior and proves parity through fixtures/tests before old code is retired.

## Proposed design decisions

| ID | Proposed decision | Why | Avoids |
|---|---|---|---|
| P08-01 | Extend the existing viewer-first React/NiiVue workspace incrementally. Freeze a current-state interaction inventory and visual baseline before changing domain data flow. | The existing UI already contains the expensive viewer and interaction work. | A rewrite consuming Week 7 and reintroducing solved rendering defects. |
| P08-02 | Make a validated internal view model the only component-facing data shape. Static-file and FastAPI repositories adapt the identical versioned case package into that view model; components never parse historical `results.json` or endpoint-specific fields. | Transport must not change scientific meaning. | Conditional UI logic that silently shows different results in static and live modes. |
| P08-03 | Validate schema version, required identities, relative references, file metadata, and cross-record IDs before scientific content renders. Unsupported or invalid packages fail as packages; partial fields do not become zeros or empty contours. | A polished UI must not beautify corrupt evidence. | Missing data looking like a negative case or valid zero measurement. |
| P08-04 | Separate `operational_review` from `validation_demo`. Operational review never requires or reveals reference labels or Dice. Validation/demo may include a separately labeled reference block and requires explicit reveal when the package says so. | The product task is prediction review; reference labels are evaluation evidence. | Oracle information shaping ordinary review or a demo being mistaken for clinical workflow. |
| P08-05 | Use explicit orthogonal state machines for package loading, analysis, evidence, review persistence, and viewer presentation. Case switching cancels/ignores stale work by request and package identity. | Network/task state and visual evidence state are different concerns. | Late responses, boolean combinations, or a viewer reset corrupting another workflow. |
| P08-06 | Start ordinary review in unmarked 2D multiplanar CT when possible, then show the prediction. Keep 3D as reversible supporting context, not the sole means of inspection or measurement. | Tri-planar CT is the honest source image; 3D meshes are derived presentation aids. | A polished surface being treated as higher-resolution scientific evidence. |
| P08-07 | Keep CT, prediction, reference, and discrepancy visibly distinct using text, source/anatomy labels, state indicators, and color. Direct canvas selection always has an equivalent named control. | Color and canvas interaction cannot be the only carriers of meaning. | Source confusion and mouse-only operation. |
| P08-08 | Decouple measurements from reviewer ordering in the next compatible case-package revision. Measurements can render without a score; the optional ordering object requires a frozen policy ID, value, label, and limitations. Until D-208 resolves, lists use neutral deterministic order. | The current schema incorrectly makes an unresolved score look mandatory. | Fabricated placeholder scores or lesion-risk language appearing before evaluation. |
| P08-09 | Use a bounded structured-question control, not an open-ended chat box. Approved question intents produce the reviewer-question text used by Plan 07; prohibited diagnostic/treatment intents return an immediate scope refusal. | The approved assistant is targeted evidence lookup. | Identifier entry, clinical-chat expectations, and untestable question breadth. |
| P08-10 | Render evidence as a versioned state: retrieving, sufficient, insufficient, conflicting/limited, failed, or unavailable. Each atomic claim links to its supporting passage and source metadata; ranked-passage/refusal fallback remains visible. | Citations need inspectable support, not decorative references. | Unsupported prose surviving because a citation appears nearby. |
| P08-11 | Define actions as: `accept` = usable as proposed for the annotation-assist task; `edit_required` = useful but correction is needed outside the browser; `reject` = unusable or unsafe as a proposed annotation. No action is a diagnosis or ground-truth assertion. | Review labels need one stable operational meaning. | “Edit” implying committed browser drawing or “accept” implying clinical confirmation. |
| P08-12 | Require at least one compatible reason code, require a note when `other` is selected, show the target prediction/model/package IDs at confirmation, and permit failed/localization-failed results to be rejected with an appropriate reason. | Structured reasons make the corrections record analyzable and auditable. | Empty decisions or technical failures being mislabeled as anatomy errors. |
| P08-13 | A review draft is disposable UI state. Success appears only after a local append-only writer returns a durable receipt containing event ID, revision, content hash, and stored location/sequence. Submission failure preserves the draft for retry and never shows “saved.” | Persistence must be true, not optimistic. | The current `localStorage` status being mistaken for capstone evidence. |
| P08-14 | Use the local FastAPI/file-writer path for the G7 persistence demonstration. Static-only mode may export a schema-valid event, but labels it `exported—not recorded` until an authorized importer appends it. Browser storage is convenience only. | Browsers cannot safely append to the governed artifact ledger by themselves. | A static demo claiming durable persistence it does not have. |
| P08-15 | Review revisions append a new event for the same package/prediction and name the exact event they supersede. The interface shows a chronological history and computed current state; it never edits or deletes an earlier event. | D-020 requires correction without erasure. | Mutable “current status” records with no audit trail. |
| P08-16 | Detect stale package, prediction, evidence, and review identities. Switching prediction versions clears incompatible drafts; older reviews remain visible under their original version and cannot silently apply to a new result. | Every human decision belongs to immutable machine evidence. | Accepting a result and later displaying that acceptance beside different weights or thresholds. |
| P08-17 | Target WCAG 2.2 AA for ordinary controls/content, with keyboard completion of the full workflow, visible focus, no keyboard trap, live status announcements, non-color cues, and companion controls/text for the NiiVue canvas. Test desktop layouts at 1440×900 and 1280×720, plus a bounded 1024-pixel fallback. | The workstation is desktop-first but must remain operable and legible. | “Accessible” meaning only an automated scan or a responsive screenshot. |
| P08-18 | Plan 09 selects exact UI test dependencies, but Plan 08 requires reducer/adapter/component tests plus one real-browser critical flow and automated accessibility checks backed by manual keyboard, contrast, zoom, and viewer review. | The current UI has no test command, and canvas behavior needs both automation and human inspection. | Visual-only QA or a large testing framework becoming an unbounded subproject. |

P08-08 is a planned versioned contract correction, not permission to edit the approved v1 schema in
place. P08-18 defines required testing behavior while leaving exact package/version choices to
Plan 09.

## Review modes

### Operational review

- Intended for a new autonomous result.
- Loads CT, prediction, warnings, measurements, and optional literature evidence.
- Does not expose reference masks, Dice, confusion labels, or “source of truth.”
- Supports accept/edit-required/reject against the immutable prediction.
- Remains fully usable when retrieval is unavailable.

### Validation/demo

- Uses a package explicitly marked as containing optional evaluation reference data.
- Starts prediction-first when `reveal_required=true`.
- Reveals reference and overlap only after an explicit action.
- Labels Dice and discrepancy as retrospective evaluation, not clinical truth.
- Uses deterministic curated cases selected under Plan 06—not only favorable examples.

Mode is package/config capability, not a hidden query parameter that can expose reference content.

## End-to-end wireflow

1. Open PROWL and load the case list without loading reference assets.
2. Select a study; validate and render its unmarked CT/package identity.
3. If analysis is not yet available, inspect CT and request the local autonomous run.
4. Track queued/running/failed state outside the immutable package.
5. On successful package publication, load the exact autonomous prediction and warnings.
6. Inspect axial/coronal/sagittal CT and prediction; optionally use 3D context.
7. Review model-derived measurements with units, source, and policy limitations.
8. Optionally select an approved evidence question.
9. Inspect cited claims/passages, limitation, refusal, or unavailable state.
10. In validation/demo only, optionally reveal the reference and discrepancy views.
11. Select accept, edit required, or reject and one or more compatible reasons.
12. Review exact target identities and confirm.
13. Wait for the append receipt; show saved state only after persistence succeeds.
14. Reopen the case and reconstruct history from stored events.
15. If revising, append a new event linked to the prior event.

Evidence is optional. Retrieval delay or failure cannot disable review submission.

## State model

| Concern | States | Authority |
|---|---|---|
| Case list | `idle`, `loading`, `ready`, `failed` | Repository adapter |
| Package | `none`, `loading`, `valid`, `invalid`, `unsupported`, `stale` | Schema/integrity validator |
| Analysis task | `not_requested`, `queued`, `running`, `failed`, `published` | Workflow/job adapter |
| Prediction | `completed`, `completed_with_warnings`, `failed` | Case package |
| Evidence | `idle`, `retrieving`, `sufficient`, `insufficient`, `limited`, `failed`, `unavailable` | Evidence response artifact |
| Review | `not_started`, `draft`, `confirming`, `submitting`, `persisted`, `submit_failed`, `stale` | UI draft plus review writer receipt |
| Presentation | evidence mode, anatomy/source focus, view mode, layers, selection | UI reducer |

Presentation changes never mutate package, evidence, or review state. Package changes may reset
presentation and must invalidate a draft whose target IDs no longer match.

## Contract changes required before implementation

The existing v1 examples remain preserved. After P08 approval, Plan 01/09 contract work creates new
versioned schemas or records for:

1. **Case-package minor revision:** move optional review-order information out of required
   measurements; define availability/limitations and policy identity.
2. **Evidence response:** the Plan 07 atomic-claim, passage, sufficiency, refusal, corpus/index, and
   generation identity used by the UI.
3. **Review draft/request:** client-authored action, reasons, note, exact targets, and expected latest
   revision; the writer owns event ID/time/revision.
4. **Review write receipt:** durable event identity, revision, content hash, append sequence/location,
   and target IDs.
5. **Case-list entry:** neutral display metadata and optional frozen ordering object without loading
   scientific/reference payloads.
6. **Analysis task status:** transient workflow state kept separate from immutable terminal packages.

No component is allowed to infer these records from a filename or response shape.

## Review-action rules

| Action | Meaning | Typical compatible reasons | Notes |
|---|---|---|---|
| `accept` | Proposed contours/measurements are usable for this research annotation-assist task | `contour_acceptable` | Does not confirm diagnosis. |
| `edit_required` | Proposal is useful but needs correction outside the browser | `boundary_correction`, `missed_lesion`, `pancreas_contour_error`, `measurement_error` | Corrected-mask reference is optional and future-compatible. |
| `reject` | Proposal is unusable or cannot be safely reviewed | `false_positive_lesion`, `pancreas_localization_error`, `insufficient_image_quality`, `other` | A failed prediction may be rejected; no blank mask is invented. |

The writer revalidates all rules. Client validation improves usability but is not authoritative.

## Evidence interaction

The initial control offers approved intents rather than a general message history:

- CT lesion delineation/contour considerations;
- measurement interpretation and reproducibility;
- pancreas anatomy and subregion terminology;
- known limitations of pancreas/lesion AI segmentation;
- review/annotation workflow considerations.

The control produces one visible question and one response artifact. The UI shows:

- response state and limitation;
- short atomic claims;
- citation/source title, year, persistent identifier, and access link where allowed;
- exact supporting passage and locator;
- corpus/index/response version in details;
- explicit refusal for prohibited or insufficient questions.

The UI does not merge several evidence responses into a conversational clinical answer.

## Loading, failure, and recovery behavior

- Case-list failure leaves a retry action and no stale “ready” message.
- Invalid package shows identity and validation errors without rendering partial results.
- File hash/size mismatch blocks the affected layer and marks the package invalid or incomplete under
  the frozen validator policy.
- Prediction failure renders its failure/warning record; it never renders a zero mask as success.
- NiiVue failure preserves textual package/warning/review access where safe and exposes retry.
- Evidence failure leaves imaging and review enabled.
- Review-write failure preserves the draft and offers retry/export without claiming persistence.
- A case switch aborts or identity-fences outstanding requests.
- Returning to a case reloads review history from the writer/snapshot rather than `localStorage`.
- Unsupported browser/WebGL state produces an explicit viewer limitation, not a blank canvas.

## Accessibility and responsive boundary

- Every non-canvas control is a native semantic element with an accessible name and visible state.
- The workflow can be completed by keyboard without operating directly on the canvas.
- Focus follows opened dialogs/popovers and returns to the invoking control.
- Status changes use restrained `aria-live` regions; errors use appropriate alert semantics.
- Color is paired with text/icon/pattern or explicit source/anatomy labels.
- Controls do not disappear at 1280×720; the study drawer may collapse first.
- At 1024-pixel width, panels stack or become drawers while the current study and review action remain
  reachable.
- At 200% browser zoom, no action or warning is clipped or covered.
- NiiVue gestures retain named buttons for plane, slice, focus, layer, evidence mode, and reset.
- Automated scans supplement, not replace, manual keyboard/canvas/contrast review.

## Implementation sequence

1. Approve or revise P08-01 through P08-18.
2. Freeze screenshots, interaction inventory, build result, and representative historical cases.
3. Map current components, reducer states, endpoint calls, static fields, and local storage behavior.
4. Create the Plan 08 support fixtures without changing production behavior.
5. Complete Plan 09 UI test-tool decision and establish a baseline test/build command.
6. Approve the case-package minor revision, evidence-response, review request/receipt, list-entry, and
   task-status contracts.
7. Implement pure schema validators and transport-neutral domain adapters.
8. Add static case-package adapter and prove the canonical fixture renders.
9. Add FastAPI adapter and run byte/value parity tests against the same fixture.
10. Replace old `results.json` component dependencies with the validated internal view model.
11. Split workflow state from NiiVue presentation state and add identity-fenced transitions.
12. Implement operational-review mode without any reference requirement.
13. Add warnings, measurements, lineage details, and D-208-aware ordering state.
14. Implement structured evidence controls and sufficient/refusal/limited/unavailable rendering.
15. Implement review form, reason validation, exact-target confirmation, and write receipt.
16. Implement history/revision flow and stale-version behavior.
17. Retire browser review status as authority; retain only explicitly labeled preferences if useful.
18. Run component and critical-browser tests with success/failure/stale/refusal fixtures.
19. Run accessibility, responsive, NiiVue, repeated-switch, and failure-injection checks.
20. Conduct Plan 11 session on the working representative flow.
21. Quinton approves a bounded Week 7 revision list.
22. Implement blocker/important changes, rerun the full Plan 08/09 matrix, and freeze G7 evidence.

Steps 5–6 are hard prerequisites for production refactoring. Steps 20–22 cannot expand into Weeks
9–10 feature work.

## Test matrix

| Scenario | Required result |
|---|---|
| Static/FastAPI parity | Same package fixture produces the same validated view model and visible scientific values. |
| Invalid/unsupported package | Scientific view is blocked with an actionable error; no missing value becomes zero. |
| Operational review | CT, prediction, warnings, measurements, evidence, and review work with no reference block. |
| Progressive reference reveal | Reference assets and retrospective metrics remain locked until explicit reveal. |
| Prediction failure | Failure/warnings remain visible; no fake contour; reject remains possible with compatible reason. |
| Evidence sufficient | Atomic claims resolve only to returned supporting passages and source metadata. |
| Evidence refusal/failure | Refusal or unavailable state remains visible and does not block review. |
| Accept/edit/reject | Compatible reason rules pass; incompatible/empty submissions fail client and writer validation. |
| Durable append | UI shows saved only after receipt; persisted event matches exact package/prediction. |
| Write failure | Draft survives; no saved state appears; retry creates at most one event under idempotency rules. |
| Revision | New event supersedes exact prior event; earlier event remains visible and unchanged. |
| Stale prediction | Draft is blocked/cleared; old review remains attached only to old prediction. |
| Case switch race | Late case/evidence/analysis response cannot alter the newly selected case. |
| Multi-lesion case | All components remain visible/selectable; no largest-only presentation. |
| Measurement/ordering | Units and source display; ordering remains absent until a frozen D-208 policy exists. |
| Keyboard path | Open case through persisted decision without pointer-only input or focus trap. |
| Responsive/zoom | Core viewer state, warnings, evidence, and review controls remain reachable at approved sizes/zoom. |
| NiiVue failure | Honest viewer error with retry/textual context; no blank-success state. |
| Historical regression | Curated success, true-negative, and false-positive cases retain intended viewer behavior. |

## Quantitative acceptance boundaries to freeze

Before implementation results are inspected, the fixture/test plan records:

- approved desktop viewport and 1024-pixel fallback screenshots;
- maximum allowed new automatically detectable WCAG A/AA violations: zero;
- required keyboard task completion: 100% of the core workflow;
- required review append round-trip: 100% for valid fixtures and 0 duplicate events under the retry
  fixture;
- transport parity: exact canonical control values/IDs and content hashes, with presentation-only URL
  differences explicitly normalized;
- package failure fixtures: 100% fail closed;
- case/evidence request-race fixtures: 100% identity-isolated;
- local representative-case load, viewer-ready, evidence-return, and review-write timing budgets after
  the baseline is measured on the M5 Pro;
- manual CT/mask alignment checks for at least one positive, one negative, one multi-lesion or subtle
  case, and one localization/false-positive failure.

Performance ceilings are frozen after the current UI baseline is measured so the plan does not invent
an arbitrary number. Plan 10 records the hardware, browser, file sizes, warm/cold state, and network
mode.

## Failure modes and fallbacks

| Failure | Evidence/trigger | Primary response | Fallback |
|---|---|---|---|
| Contract migration grows | Components still depend on old fields after adapter slice | Stop feature work; finish one canonical view model | Wrap historical fixtures behind a temporary legacy adapter used only for comparison |
| FastAPI writer delayed | Static package renders but no durable receipt path | Prioritize minimal local append endpoint | Export valid event as `not recorded`; G7 remains open |
| Evidence below G6 | Insufficient groundedness/citation gate | Display passages/refusal/unavailable state | Omit generated summary; imaging/review remain complete |
| Ordering policy unresolved | D-208 still open | Use neutral order and hide score | Show measurement/warning details only |
| NiiVue cannot render a case | WebGL/load/affine failure | Show explicit error and retry; investigate asset | Use tri-planar fallback screenshots for presentation only, disclose limitation |
| Accessibility framework cost grows | Setup exceeds Plan 09 budget | Test reducer/adapters and one critical browser flow | Manual signed keyboard/contrast/zoom matrix plus build verification |
| Stakeholder asks for editor | Request appears in Plan 11 | Record and prioritize against core/schedule | Defer under D-305 unless core gates pass with protected Weeks 9–10 |
| Visual polish threatens schedule | State/persistence tests incomplete entering Week 7 | Freeze current styling | Deliver contract-correct workflow with existing visual system |

## Observability and completion evidence

Record without patient content:

- UI build identity and case-package/evidence/review schema versions;
- package/load/viewer/evidence/review states and failure codes;
- selected package, prediction, corpus/index/response, and review-event IDs;
- transport mode and capability flags;
- timestamps/durations for package load, viewer ready, evidence response, and durable append;
- validation violations and stale-response discards;
- automated test/build results, viewport screenshots, manual QA checklist, and stakeholder finding IDs.

Do not log image pixels, source reports, notes containing identifiers, complete article text, or
credentials.

## Plan readiness gate

Plan 08 may move to `Ready` when:

- [x] Quinton approves or revises P08-01 through P08-18.
- [ ] The current-state inventory and baseline screenshots/build are complete.
- [x] Approved Plan 09 selects the test environment and UI test boundary; installation/execution remains pending.
- [ ] Case-package minor revision and evidence/review request/receipt contracts validate.
- [ ] Plan 10 confirms artifact roots, static/FastAPI file resolution, and local writer behavior.
- [ ] Representative success/failure/refusal/stale fixtures are available.
- [ ] D-208 is either resolved or ordering is explicitly unavailable/neutral.
- [x] Approved Plan 11 defines the Week 7 protocol and fallback path; actual participant/session
  confirmation and findings remain pending and are not an initial UI-development prerequisite.

Design approval can precede these dependencies. Production UI changes cannot.

## Completion gate (G7)

- [ ] A representative user completes inspect → optional evidence → accept/edit/reject.
- [ ] The decision persists through the local writer and survives reload.
- [ ] Event history remains tied to immutable prediction/package versions.
- [ ] Operational review works without reference annotations.
- [ ] Validation/demo reference reveal cannot contaminate autonomous review.
- [ ] Evidence claims cite exact returned passages or the UI refuses/falls back.
- [ ] Success, negative, multi-lesion/subtle, false-positive/localization-failure, evidence-refusal, and
  stale-version fixtures pass.
- [ ] Keyboard, accessibility, responsive, viewer, and transport-parity checks pass.
- [ ] Stakeholder findings and implemented/deferred decisions are documented honestly.
- [ ] UI wording passes the non-diagnostic claim review.

## Planned artifacts

- [`../interface/README.md`](../interface/README.md)
- [`../interface/CURRENT-STATE-INVENTORY.md`](../interface/CURRENT-STATE-INVENTORY.md)
- [`../interface/WORKFLOW-AND-STATE-MODEL.md`](../interface/WORKFLOW-AND-STATE-MODEL.md)
- [`../interface/DATA-ADAPTERS-AND-PERSISTENCE.md`](../interface/DATA-ADAPTERS-AND-PERSISTENCE.md)
- [`../interface/EVIDENCE-AND-TRUST.md`](../interface/EVIDENCE-AND-TRUST.md)
- [`../interface/ACCESSIBILITY-AND-VISUAL-QA.md`](../interface/ACCESSIBILITY-AND-VISUAL-QA.md)
- [`../interface/FIXTURES-AND-ACCEPTANCE.md`](../interface/FIXTURES-AND-ACCEPTANCE.md)
- versioned contract schemas/examples after approval;
- implemented React/NiiVue adapters, components, and tests;
- stakeholder-tested G7 evidence package.

## Technical references

- [WCAG 2.2](https://www.w3.org/TR/wcag/) — accessibility target for conventional web content and
  controls.
- [W3C accessibility principles](https://www.w3.org/WAI/fundamentals/accessibility-principles/) —
  keyboard and operability rationale.
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) — candidate
  user-facing component-test approach for Plan 09.
- [Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing) — candidate
  real-browser and automated accessibility checks; its documentation explicitly notes that automated
  scans do not replace manual evaluation.

## Handoff

Plan 11 consumes the frozen wireflow and fixture tasks, then returns a prioritized revision list.
Plan 09 owns executable verification, Plan 10 owns local artifact/transport operation, and Plan 12
consumes the stable G7 interface as release-candidate input. In-browser contour editing, broad chat,
multi-user features, and unimplemented stakeholder ideas remain deferred rather than silently entering
Weeks 8–10.
