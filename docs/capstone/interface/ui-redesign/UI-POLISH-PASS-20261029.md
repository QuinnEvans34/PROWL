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

## Follow-up: 3D scene, peel and navigation (same day)

Quinton asked for the full scan to be the default, a simpler set of view settings, and easier rotation, zooming and peeling. He chose to keep the cut fixed front to back, and to keep the Rotate/Move buttons for trackpad users. This was done in eight small commits:

| Commit | Change |
|---|---|
| `33bfa3f` | 3D scene selector (Abdomen / Region / Surfaces). Abdomen is the default and opens at a fixed 1.45× zoom; the peel starts at 0% |
| `436996a` | View settings reduced to Mask strength, CT visibility in 3D, the 2D-only Full abdominal CT option, and Restore default display |
| `7c58cf5` | "Peel (front → back)" bar: a clickable pancreas marker computed from the 3D scene, a percentage, Peel to pancreas / Restore CT, and `[` `]` keys |
| `d9366b2` | Keyboard shortcuts: 1–6 and 0 for camera views, + and − to zoom, F to fit |
| `282f26c` | Double-click a surface to orbit around it, by wrapping `setPivot3D` on the viewer's own instance |
| `8e02d7f` | NiiVue orientation cube in the 3D view |
| `e826c38` | "?" button that opens a viewer controls card for 2D and 3D |
| `e4cea06` | Half-resolution rendering during 3D drag or zoom on high-DPI screens when the CT is visible |

Points to review:

- **Wrapped NiiVue methods.** Two NiiVue methods are now overridden on the viewer's own instance: `drawImage3D` (skipped while the CT is hidden) and `setPivot3D` (custom orbit centre). Check both after any NiiVue upgrade.
- **Pancreas marker.** `peelRevealPercent` treats the lowest y of the scene as the front face at clip depth −0.5, which matches the ray test at azimuth 0.
- **Resolution switch.** The lower resolution is applied on `pointerdown` so that NiiVue's `mousedown` records the drag start at that resolution. Full resolution is restored after `pointerup`.

Verification: Vitest 316 passed, 6 skipped, 0 failed, and `vite build` succeeds. Both ran on a Linux copy. Each feature was checked by hand in the browser pane.

### Codex follow-up review on the Mac

Reviewed the nine follow-up commits through `6c92307`. Keep the scene selector,
help card, orientation cue and navigation shortcuts. Fixed one concrete issue:
“Peel to pancreas” used a guessed 50% before geometry was available; it now stays
disabled until a pancreas marker is available (manual peel and Restore CT remain).
Added a component regression covering missing geometry, Surfaces/Region controls,
help, keyboard peel and restoring CT. The new test passes.

The initial full Mac suite passed 316 tests with six skips. A high-DPI real-viewer
check in CPU software Chromium timed out on the full-abdomen render; a diagnostic
attempt saturated that renderer and was stopped, with only its verified test
processes terminated and their cleanup confirmed. This is not evidence that the
hardware-rendered viewer fails, nor a verified performance result. Resolution
restoration and double-click orbit still need an independent hardware-browser
walkthrough; Claude's manual observations above remain attributed to Claude.
Teacher pins matched and its worker continued; no answer or training model launched.
Final verification after the fix: 317 tests passed, six skipped; production build
passed with the existing large-chunk warning.

## Codex responsiveness follow-up

Installed NiiVue setters (`setMeshProperty`, `setMeshShader`, `setOpacity`) each call
`updateGLVolume`, which rebuilds volume textures and draws. Batch synchronous
presentation changes and initial mesh styling into one refresh. A synthetic test
reduces 30 setter refresh requests to one, preserving final state and restoring
methods after exceptions/nested batches. This is a work-count improvement, not an
FPS claim. Dispose NiiVue observers/listeners and delayed resolution timers on
unmount; prevent wheel restoration during a held drag and restore on window blur.

The real small-window walkthrough also found the help card could extend above the
viewer and put its close button underneath the toolbar. Constrain its height/width
and scroll its contents. A browser regression exercises opening/closing it at
800x600 with the overlay panels closed.

Verification: 320 UI tests passed, six skipped; production build passed with the
existing bundle-size warning. Software Chromium loaded the real saved case at
800x600, exercised drag, Abdomen/Surfaces/Region switching, peel shortcut, camera
and Fit, and help dismissal without JavaScript errors. At 2x DPR, the canvas went
1600x592 -> 800x296 while dragging -> 1600x592 after release. Initial help check
failed before the CSS correction; the synthetic test initially left overlay panels
open, which correctly intercepted viewer clicks, and was corrected to close them.
Backend localhost:8000 remains unavailable while saved assets work; no service
restart or answer-model call was performed. Existing reviewer save/reopen and
citation attachment regression tests passed, but this is not a new live end-to-end
clinical or answer-quality acceptance. Double-click surface orbit still needs a
human hardware-browser check; no speed percentage is claimed. Teacher attempt13
remained active and advanced to tile75/120 of its next case after 1007 completions.

## Evening zoom and redundant mesh-work correction

User reported remaining lag and excessive magnification. Full-abdomen initial/reset
scale is now1.0 (was1.45); cropped surface framing uses0.85 times the scene/mesh
ratio capped at1.8 (was1.15 capped at3.2); compact initial scale1.1 (was1.55).
Double-click zoom increases15% instead of35%. Existing session camera choices remain
preserved; Reset viewer applies the new defaults without reloading the page.

NiiVue NVMesh.setProperty calls updateMesh even for equal values. Compare scalar
opacity and RGBA contents before calling its public setters, and retain the last
applied shader per mesh entry. Real changes still use the public API. This avoids
redundant geometry/buffer work; it does not claim a measured FPS increase.

321 UI tests passed, six skipped; build passed with the existing bundle warning.
Real saved-case software Chromium walkthrough passed drag, scene switching, help,
peel, camera and Fit with no page errors. Saved-case availability is separate from
the unavailable localhost:8000 live analysis service. Teacher attempt13 remained
running,1123/1333 at the check; no answer model, inference or training was launched.
Morning review: judge default framing and perceived drag/zoom responsiveness on the
hardware browser. Live assistant latency remains a separate GPU-free comparison.
