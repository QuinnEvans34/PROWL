# Single matched-runtime Windows qualification

Quinton authorized one new bounded Windows diagnostic following d974f7e. No
four-case batch, training, automatic retry or tolerance change is authorized by
this follow-on. Mac KD must continue independently and is not controlled here.

## Isolated environment and producing code

Fresh runtime root: C:/Users/quinn/.cache/prowl-week05-matched-20261102-a01.
Setup evidence: E:/PROWL/readiness/week05-matched-runtime-setup-20261102-a01.
The existing training venv, prior diagnostic, Mac reference and original failed
comparison are preserved. The new environment has no inherited system-site packages.

The exact Mac Python3.12.13 is available from managed CPython; the exact scientific
package versions are available for Windows. Target versions:

| Package | Windows target | Mac reference |
| --- | --- | --- |
| Python |3.12.13|3.12.13|
| Torch |2.13.0+cu130|2.13.0|
| MONAI |1.6.0|1.6.0|
| NumPy |2.5.1|2.5.1|
| NiBabel |5.4.2|5.4.2|
| SciPy |1.18.0|1.18.0|

The remaining intended differences are platform/compiler and CUDA13.0 versus MPS
backend/build. Existing Windows NVIDIA596.58 reports CUDA13.2 support; no driver
update is performed. PyTorch2.13.0+cu130 is from the official PyTorch CUDA index;
other packages come from PyPI. Install reports record wheel URLs and hashes.
The new launcher refuses changed Python/package versions rather than substituting.

Additive code: qualify_matched_physical_cascade_20261102.py,
cascade_trace_forward_v1.py, matched_cascade_comparison_v1.py and
compare_matched_week05_reference_20261102.py. Original producers are unchanged.
The comparison retains every original numerical limit; only the bound Windows
request/root and matched-environment checks differ. Original failure remains
fd7be15a0745e5acdec22fdf738c9b6d4a95be35dbaaf555fd56906ad083c974.

## Trace and safety scope

Exactly two preselected ordinary segmenter calls are traced: index0/origin[0,0,0]
and index39/origin[216,0,170]. The wrapper saves input tensors and pre-softmax
logits; it returns the SAME output tensor and adds no model forwards or RNG use.
The actual full grid/call count must reconcile before success. Four .npy arrays
and trace.json are preserved within the output, with hashes and independent copies.
No reference labels enter the autonomous worker.

Ceilings remain600s inference wall including startup,12GiB owned RSS,6GiB CUDA,
2GiB output plus2GiB independent backup;40GiB combined backup and100GiB free
C/E floors. Exclusive GPU lock, AC, existing drive identity, owned Windows Job
Object cleanup and no-retry gates remain. Environment setup has a12GiB root cap;
availability/download/setup time is separate from the600s inference attempt.

Fresh request/output root:
E:/PROWL/readiness/week05-matched-qualification-20261102-a01.
Independent backup:
C:/Users/quinn/PROWL-Backups/week05-matched-qualification-20261102-a01.
Fresh comparison:
E:/PROWL/readiness/week05-matched-comparison-20261102-a01.

Before request freeze, verify installation/CPU tests and safe strict model loading.
Request pins include core installed compiled libraries, preprocessing/model sources,
Python executable and setup reports as well as CT/model/source/configuration identities.
Only then run the single authorized diagnostic; preserve any failure and report.
The final outcome must distinguish execution completion from the strict comparison
verdict. Even a pass under this message does not dispatch the four-case batch.

## Actual outcome: CPU qualification blocked before inference

The later delegated instruction conditionally authorizes the fixed four-case batch
only after ALL readiness and unchanged comparison gates pass. That condition is
not met. No matched GPU diagnostic, frozen request, comparison or batch was started.

Installation completed. Python and all five scientific packages exactly match the
table above; pip check reports no broken declared requirements. Safe CPU strict
loading passed for both models (4,700,914 localizer and 4,700,931 segmenter parameters).
All 272 original repository pins match. Runtime occupies 3,433,310,415 bytes,
below its 12-GiB cap. CUDA was not initialized by the environment check.

The focused CPU suite completed with **43 passed, 2 failed in 38.70 seconds**.
Both failures are ModuleNotFoundError: No module named PIL, from the original
control-pipeline imports used by the equivalence tests. This is an omitted Pillow
dependency in the newly assembled isolated environment, not evidence of a model
or probability failure. A clean pip check does not detect undeclared application
imports. The failed tests are test_bridge_matches_existing_control_source_axis_margin_semantics
and test_existing_control_predictor_equivalence_at_multiple_tile_edges.

Evidence: week05-matched-runtime-setup-20261102-a01/matched-runtime-tests.xml,
environment-verification.json and package-install-report.json. The environment
report's PASS applies only to versions/strict loading/resource/pin checks, not full
readiness. Both owned CPU processes exited; no diagnostic Python worker or CUDA
compute owner remained at closeout. No inference traces exist because no inference
was dispatched. Mac KD was not touched.

Per the explicit stop-on-qualification-failure/no-automatic-retry instruction,
no dependency installation or test retry followed this failure. Next decision:
authorize an additive isolated Pillow dependency installation with recorded version
and wheel provenance, then one corrected CPU qualification attempt. Preserve this
failed XML and environment report; new evidence must use new filenames. The original
numerical tolerances, 600-second inference cap and all other gates remain unchanged.

## Authorized dependency correction and diagnostic dispatch

The follow-up clarified that the no-retry rule concerns scientific/GPU attempts,
and explicitly approved the missing Pillow repair and one corrected CPU suite.
Installed Pillow 12.3.0 (same version as the established Windows environment),
without dependencies, into the isolated venv only. Wheel provenance is retained
in pillow-install-report.json. Pip check passed; corrected suite **45 passed in
8.91 seconds**. Prior failed XML and environment report remain unchanged.
corrected-readiness.json binds both attempts and the installation receipt.
Isolated runtime occupies 3,449,473,772 bytes, below the 12-GiB ceiling.

One diagnostic dispatched under request SHA256
641b6db57245c91f682e060c55ca9678f320ca0c1394e0e4d0a2f98c40568a12.
Owned session 58294; follow this owner, never duplicate. All producing files now
frozen. Later conditional authorization permits the fixed four-case evaluation
only if the unchanged comparison and all gates pass. Mac KD remains independent.

## Final outcome: execution PASS, unchanged comparison FAIL

Owned diagnostic 58294 exited0. Inner runtime78.282s; supervisor86.532s,
peak owned RSS1,641,881,600 bytes; GPU reserved1,021,313,024 bytes. All60 windows
completed, two selected input/logit traces saved at indices0/39, zero extra
forwards. All305 producing pins and15 independent backup pairs match. Workers
were reaped; process inspection found no diagnostic workers or GPU compute owner.

The CPU comparison completed and reports **FAIL_ENGINEERING_COMPARISON**:
169 of51,444,975 probability values exceed the unchanged atol1e-5/rtol1e-4 rule;
maximum absolute difference4.851818084716797e-5. Native hard predictions and
localizer masks have ZERO disagreements across20,131,482 voxels. Geometry,
identity, reconstruction and normalization checks passed.

New Windows probabilities are byte-for-byte identical to the original Windows
probability file. Thus matching Python/scientific-library versions did not resolve
the discrepancy; it does not isolate its backend or operation-level cause.
The two new traces provide evidence for a separately scoped matched Mac trace
comparison if later authorized. No new Mac inference was requested or performed.

Comparison SHA256 a37a953820a55637530d30f883394fe4717d444fdebfbfd043cd8f54f5e93ab5,
under E:/PROWL/readiness/week05-matched-comparison-20261102-a01, independently
backed up on C:. closeout.json records exact pin/backup/trace and output identity
checks. Original failed CPU tests and original failed comparison are preserved.
No GPU retry, tolerance change, four-case batch, training or new Dice result.
Conditional batch authorization remains blocked by this scientific comparison gate.
