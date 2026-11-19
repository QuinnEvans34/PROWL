# Linked finding review

PROWL opens a study, shows the model’s pancreas and lesion outlines, and lets a reviewer verify a finding against the underlying CT. The Workbench keeps the existing charcoal treatment and gives the image area to the current task.

## 1. An inspection layout for one finding

- Studies open in **3D Abdomen** when the full CT is available, including source CT and studies still awaiting prediction surfaces. Prepared crops open in **3D Region**. Choosing a scene in 2D opens 3D. Changing scenes from Split or inspection keeps the adjacent CT pane.
- **Inspect CT slice** from either the viewer or Findings opens a linked layout. A smaller 3D pane remains visible beside one large CT plane. The selected finding, dimensions in cm, and displayed-outline volume stay in reach. A narrow window can show the two panes in a stack or allow switching between them.
- Open at the exact evidence slice with the recorded caliper endpoints. Give the CT pane a useful initial fit around the finding and surrounding tissue. Mark the lesion’s slice span and the measured slice on the slider when the corresponding grid is known. Provide one action to return to the measured slice.
- **Show slice in 3D** adds an optional plane positioned using the CT’s world coordinates. The plane follows the active CT slice and is independent of the front/back peel. Camera-facing 3D calipers retain their existing behavior and identify the plane on which they were measured.
- Closing inspection returns to the earlier viewer mode, 2D layout, 3D camera, zoom, pan, window, and peel. Switching studies discards inspection state for the previous study. Direct 2D, 3D, Split, full screen, keyboard controls, and reference validation remain usable.

## 2. CT texture and source detail

- **Outline**, **Fill**, and **CT only** are immediately reachable in inspection. Overlay changes leave the slice, framing, and window in place. Show a physical scale bar and a viewport label for the data actually displayed.
- Prepared previews identify their grid and spacing. Use **Source CT** in the active inspection pane when an original series is available from a verified study and prediction artifact. Retain the prepared view as the fast path and explicit fallback. Load source detail on demand in one pane and preserve the current image if loading fails.
- Map location through world millimeters with verified image geometry. Identify the actual source series, plane, and spacing. When the source is on a different grid, show the nearest valid source slice with that label and offer a return to the exact measurement grid. Display caliper endpoints only on their verified physical plane.
- Expose window center and width in HU only for calibrated CT. Preserve source intensities and label interpolation separately from grayscale interpolation. Measurements and their provenance follow the verified prediction mask. Prepared-grid positions are labeled **Prepared slice** and genuine acquisition-grid positions **Source slice**.

## 3. 3D rendering and controls

- Center the initial anatomy view on the predicted pancreas and lesion while leaving enough space to rotate. Use a subdued contextual volume with independent opacity and restrained lighting on the surfaces. Maintain clear color, text, and visual emphasis for the selected finding. Appearance changes affect the display and leave the prediction, physical measurements, and provenance intact.
- Keep pan, rotation, both peel directions, box zoom, anatomical views, and calipers responsive. Use the existing lower-resolution interaction path as the starting point. Restore settled detail after a gesture and profile it on the demo laptop. Give the view a short, descriptive label for the active scene.
- Keep primary actions visible at laptop size. Put less-used controls in View settings and move duplicate measurements out of the image area during inspection. Keep the charcoal surfaces and reserve stronger colors for anatomy and selection.

## 4. Findings, Ask PROWL, and key views

- Identify findings by study, prediction artifact, and component. Give the selected finding one card with the available dimensions, the measurement method, and direct image actions. Keep it visible when the reviewer opens Ask PROWL or Summary.
- Provide **This outline** for verified scan facts and **Published evidence** for literature. A scan answer can reopen the measured slice. Literature answers retain their citations. Study and prediction switches rebind both contexts.
- **Save key view** stores a bounded research-review record using the existing review persistence path where possible. Save the study and prediction identity, finding, plane and world location, window, overlay, view settings, and reviewer note. Use a real captured image for any thumbnail and make the underlying view reopenable. Handle unavailable source and stale predictions explicitly. Store review observations independently from the immutable model output.

## 5. One path from the scan to the same prediction in Workbench

- Open a supported de-identified CT series, select the series, start inference, and open the Workbench on the exact completed artifact. Extend the existing verified Analyze/Saved Prediction path. The series browser should identify source, geometry, and availability before running. Show genuine queued, running, completed, cancelled, failed, and unavailable states from the worker, with a usable saved-study route when live inference is offline.
- Verify that CT, mask, surfaces, measurements, and key views belong to the same study and prediction. Show the selected prediction and model revision in the Workbench. Apply the repository’s existing approved model policies, including the configured pancreas-proximity policy for new model integrations where applicable. Neither the UI nor the import path changes scientific runs or archived validation evidence.
- First integrate a completed, receipt-backed prediction. Then exercise the de-identified import and inference path with an authorized configured worker. Test the full journey with synthetic fixtures where necessary and qualify real-source performance separately. Raw CT, scan packages, and weights stay outside version control.

## Acceptance checks

1. On a saved study, select a lesion once, open the measured slice in one action, see its endpoints over the CT, toggle the overlay, and restore the earlier 3D framing. Repeat for the pancreas and for a different study.
2. Check both peel directions, an oriented 3D camera, pan, cursor zoom, box zoom, 2D frame lock, and independent 2D slice navigation after entering and leaving inspection. Exercise desktop and narrow layouts.
3. Compare the prepared and verified source image at the same world location and physical scale. Exercise missing source, incompatible artifacts, different slice grids, and wrong study IDs. Measurements retain the same source and values across appearance changes.
4. Save a key view, reload the app, reopen it, and confirm the intended finding and image settings. Test prediction changes, failed storage, and unavailable source. Verify that Ask PROWL uses the current study and lets the reviewer return to the image.
5. Run the full UI build and tests after each coherent change. Browser-check the saved-study workflow at laptop resolution and record first image time and drag responsiveness before expanding source data to more panes.
6. With a configured worker, import a de-identified CT, run prediction, open the exact artifact, save a key view, and reopen it. Record which steps were exercised with real data and which were exercised with fixtures.

Design references include [Visage 7 triangulation](https://mhhlehre.visageimaging.com/Lang_Dep/Visage7_Client_OnlineHelp_EN.pdf#page=133), [3D Virtual Pancreatography](https://pmc.ncbi.nlm.nih.gov/articles/PMC8884473/#F10), [3D Slicer volume rendering](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html), and [OHIF measurement tracking](https://docs.ohif.org/user-guide/viewer/measurement-tracking/).
