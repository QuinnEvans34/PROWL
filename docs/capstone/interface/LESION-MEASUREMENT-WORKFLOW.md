# 3D-first review and measured lesion workflow

November 17, 2026 · Implementation plan

Stakeholder feedback: preserve the full predicted contours, make dimensions easy
to read, and make it easy to inspect tissue texture on the source CT. The next
demo should show a reviewer completing a workflow on one study.

## 1. Establish measurement geometry

- Use the verified prediction labelmap on its matched CT grid. A lesion is one
  face-connected component of the lesion label, not a diagnosis. Keep existing
  aggregate volumes and coverage refusals. Never derive size from the mesh,
  display pixels, a bounding sphere, or the AI expert.
- For the first release, use each component's largest native slice by area.
  Place two perpendicular calipers along its native in-plane axes through a
  lesion voxel near that slice's centroid. Extend each arm to the first voxel
  boundary on either side. Call these centered slice calipers; do not call them
  the maximum diameter. Store their endpoints in native voxel coordinates and
  world millimeters. Report the full component's superior–inferior extent
  separately. Withhold the cross for nonorthogonal in-plane geometry.
- Check anisotropy, rotations, separated components, concave shapes, empty
  masks and existing coverage refusals with synthetic fixtures. Tie component
  identities to the mask version when they enter review state.

## 2. Put measurements in Findings and link 3D to 2D

- Default to 3D when a prediction is available; use CT-first for unprocessed
  imports. Keep 2D, split view and the existing layout controls.
- Put the pancreas outline volume and one row per predicted lesion in Findings.
  Lead with centimeters for lengths and mL for volumes, with millimeters in
  details. Give both 3D and 2D the same numbers and prediction identity.
- Selecting a lesion highlights it in 3D. **Inspect measurement** opens the
  recorded slice with its calipers visible. **Show calipers** in 3D is optional
  and off initially; draw on the same physical plane. A native plane that
  cannot be reproduced by the viewer must not show a projected cross on an
  unrelated slice. Keep the cross distinct from navigation crosshairs.
- Verify selection, slice placement and overlay alignment through pan, zoom,
  resize, fullscreen and study changes. Add reviewer-adjusted annotations only
  after automatic placement works; keep edits separate from model measurements.

## 3. Connect import, inference and review

- Start with one de-identified NIfTI CT, preview it locally, and run through the
  existing job flow with explicit start, progress, cancellation and failure.
  Reopen the saved result in the same workbench. Label the existing
  pancreas-assisted path honestly; gate CT-only inference on the qualified
  autonomous pipeline and its existing admission criteria.
- Then connect DICOM folder import: group by study and series, select one
  supported volume, validate geometry, and keep storage local. Check invalid
  files, unsupported series and unavailable worker behavior. No new scientific
  run or model change is part of the measurement work.

## Demo acceptance

Open a known saved prediction, rotate the pancreas, select a lesion, read its
dimensions, inspect the caliper slice and texture, then save and reopen the
review. Show a live import and prediction only after that path is repeatable on
the demo machine. Keep a labeled saved study available if the worker is offline.
