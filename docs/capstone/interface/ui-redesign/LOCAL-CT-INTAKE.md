# Local CT intake and inference handoff

## Available in this branch

From **Studies → Import CT**, open one de-identified NIfTI as a source CT in Workbench. The app validates the volume in the browser and retains it for the current tab session. The route uses a random session identifier. Analysis is available through the existing configured Analyze catalog.

`scripts/prepare_local_ct_intake.py` prepares one explicitly selected de-identified NIfTI on the same workstation. It checks the file, byte budget, three-dimensional grid, millimeter units, affine, and finite scalar intensities. It retains the exact source bytes for a gzip input. For a plain NIfTI it writes a lossless gzip copy with the original NIfTI bytes. The output contains a CT and a manifest with its study identity, source and package hashes, native geometry, and intensity units marked unverified. An intake package is a CT input, and its status is `ct_ready`.

The browser can open an exact completed job from the current Analyze service in Workbench. It binds the route, status, manifest, CT, mask, and measurements to the same job before showing the result. The current service runs an allowlisted development catalog with provided pancreas input.

## Connect CT-only inference

1. Provision a separate loopback intake endpoint for a bounded NIfTI upload and retain the input under an opaque local handle. Apply the same origin and host restrictions as the job service. Assign the study identifier locally and keep file paths, images, and request provenance out of general literature requests. Reuse the intake validator and return the committed manifest with an explicit CT-only preview and an explicit Analyze action. File selection alone stages the CT and does not start a job.
2. Configure an operator-approved CT-only worker with the localizer and segmenter checkpoints, hashes, recipe, permitted device, and time and memory limits. Use the existing CT-only runner in `scripts/predict_autonomous_ct.py` for the specific approved model integration, with the required `predicted-pancreas-proximity-5mm-v1` policy and geometry/label qualifications for new model integrations. Bind the request to the intake CT hash. Keep the existing pancreas-assisted worker contract and development catalog available as a distinct mode.
3. Package the completed native artifact using the existing measurement provenance path in `scripts/prepare_saved_prediction_view.py`. Extend the job publisher and review reader to support CT-only job provenance and bind its manifest to the same job, study, native CT, and mask hashes. Native coordinates and model source roles must agree before CT, measurements, or surface generation is allowed. Use the same artifact from Workbench and retain it through the existing review-receipt service. Exercise both input/output identity mismatches and cancelled jobs with synthetic data before evaluating an approved development CT.
4. Connect DICOM series selection after the CT-only path passes. Qualify a local converter that groups pixels by study and series, rejects unsupported or inconsistent images, and preserves the validated voxel-to-world transform and intensity mapping. Connect the already-defined import adapter to the validator. A DICOM install or source archive alone does not supply that contract.

## Calibrated intensity display

Existing native prediction manifests carry millimeter geometry and a numeric window preset. Those fields establish spatial measurements and a display range. NIfTI slope and intercept give the stored-to-decoded intensity transform. An HU label requires separate evidence that the decoded values are Hounsfield units for the exact CT being displayed.

A qualified producer can verify the acquisition or conversion metadata, retain the scaling evidence and CT content hash in its receipt, and pass that claim into the native prediction manifest. Bind the claim to the copied CT in the prediction and archive validators. Add matching tests for missing, mismatched, or unsupported scaling evidence. Existing archives and locally selected NIfTI data keep the unverified intensity label.
