# UI polish pass — 2026-10-29

Claude implemented this pass on `main` after a live audit, following Quinton's six-step order. It is ready for Codex review. There is one commit per step:

| Step | Commit | Scope |
|---|---|---|
| 1 Brand | `e53b0a8` | Panther shown as a light silhouette (CSS mask on the unchanged PNG); theme-aware SVG favicon with the PNG as fallback |
| 2 3D | `ae6b7d7` | Matched mesh smoothing for the difference meshes; reference outline shader; opaque difference pancreas; Masks-only default; surface-fit zoom |
| 3 Workbench | `9e439be` | Hero 2D layout; one-line toolbar; "Views" camera menu; colour key while comparing; split-view fixes |
| 4 Assistant | `659c12e` | Compact structure rows; click pop-up with general literature questions; ray-cast 3D picking; conversation-style Ask; widen control |
| 5 Pages | `808b226` | Saved prediction review and Analyze restyled (`styles/pages.css`); header status names its service |
| 6 Studies / narrow | `47d11a8` | Studies table de-duplicated; narrow-width navigation and wrapping |
| Follow-up | `00dd3b1` | Performance fix: skip NiiVue's invisible CT ray-cast in 3D "Masks only" (about 7 ms to under 1 ms per frame) |

## Review focus

The steps above are mostly CSS and layout. These five changes alter behaviour, so they need the closest review:

- **Click picking in 3D.** `pickSurfaceAtClick` in `NiivueViewer.jsx` unprojects the click through `calculateMvpMatrix` and tests mesh vertices within 3 mm of the ray. A lesion hit wins over the pancreas hit. The old crosshair method remains as the fallback. This was needed because "Masks only" (now the default) left NiiVue's depth pick hitting the cut plane.
- **Default 3D view.** `clipProgress` now defaults to 100 (Masks only) in `reviewState.js`, both in the initial state and on reset.
- **Hero 2D layout.** `setPlaneLayout` uses NiiVue `setCustomLayout` for "All 3". It falls back to `clearCustomLayout` and the row layout for single planes or very wide viewers. Plane labels are positioned from `nv.screenSlices`.
- **Scoped questions.** Questions offered next to a structure come from `lib/structureQuestions.js`. They are general literature questions and never about the scan. Choosing one only fills the Ask box through `draftRequest`; nothing is sent. Please check that these questions stay within RF1–RF9.
- **Skipped CT rendering.** `setVolumeRendering` replaces `drawImage3D` on this viewer's NiiVue instance with a no-op while the CT is fully hidden in 3D, and restores it when the CT is shown again or the view returns to 2D.
- **Mesh export.** `scripts/export_case.py` now gives the difference meshes the main smoothing (Gaussian 0.7, 12 Taubin passes). Discrepancies thinner than about one voxel can drop out of 3D, but they stay exact in the 2D difference NIfTI. When a region no longer produces a surface, its mesh is removed.

## Verification

- **Tests.** Vitest: 315 passed, 6 skipped, 1 failed. The failure is `NativeMeasurementPanel.test.jsx › does not turn a measurement into a disease interpretation`, which already failed before this pass. The new `tests/StructurePopover.test.jsx` (4 tests) passes.
- **Build.** `vite build` succeeds.
- **Where the tests ran.** Both ran on a Linux copy of `ui/`, because the macOS `.venv`/node binaries don't run in the agent VM. Please re-run `npm run test:run` and `npm run build` on the Mac.
- **Manual checks.** The pages were checked by hand in the browser at 1440×900, 1100×800 and 375×812: Studies, Workbench (2D, 3D, Split, compare Both and Difference, click pop-ups in 2D and 3D, Ask prefill, widen), Saved reviews, Analyze and Research.
- **Demo meshes.** The prepared case assets under `ui/public/cases/` are git-ignored. Their difference meshes were regenerated locally with `export_case.py --derive-existing` (`display_mesh_version` is now `v3-difference-main-smoothing`). Fresh clones need the same command.

## Not changed

- The literature request and response contract, validation, citations and refusal gates.
- The measurement maths.
- The review-decision storage and the private evaluation code.
- The Research page keeps its full-page Ask layout.

## Codex review on the Mac — October 29

Reviewed all nine commits through `1a96cce`. Keep the visual direction: the larger
2D planes, unobstructed 3D view, compact structure rows, question-prefill shortcuts,
and consistent Saved/Analyze styling improve the review flow.

Three review fixes: show the equivalent-diameter caveat inside the structure
popup; disclose that smoothed 3D difference surfaces can omit thin discrepancies
and direct reviewers to exact 2D overlays; constrain Saved/Analyze grid minimums
so long controls do not clip content at 375px. Original masks/measurements are not
modified. Updated the pre-existing NativeMeasurementPanel assertion to verify the
current numerical-comparison limitations (not a normal-range or diagnostic claim),
rather than expecting the older unsupported-question wording.

Mac verification: full Vitest suite 316 passed, 6 skipped; production build passed
with the existing large-chunk warning. Headless Chromium with software rendering
checked Studies, Analyze and Saved at 1440px/375px and Workbench 2D/3D/Difference;
screenshots inspected. Saved's inner page initially overflowed despite the document
width appearing normal; after the fix both page and content widths fit. Structure
question prefill worked without submission. No answer model or inference launched.
Teacher repository pins all matched and its supervisor/worker remained active.
Claude's frame-time measurement was not independently benchmarked in this review.
Git-ignored generated demo assets remain local and require regeneration on a fresh
checkout as described above; they are not added to Git by this review.
