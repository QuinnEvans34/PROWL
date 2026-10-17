# Windows training checkout integration with current Mac work

## Outcome and source identities

Quinton requested the new augmentation experiment specification and the latest code from the other
machine on October17. This integration brings all52 incoming commits published on `origin/main`
through `7e6796c66ef3d421680a5a6be69fcbb1e75e750a` into `codex/windows-training-readiness`.
It preserves the Windows trainer, completed-run evidence and local configuration. It does not fetch
uncommitted or unpushed files from the Mac, copy private artifacts, launch training or publish a push.

The pre-integration safety commit is `3f9b64a`: completed72k/EMA and selected-native reviews,
their scripts/tests, notebook entries and agent handoff. The last previously published Windows
snapshot was `1e427dd`. The shared merge base was `8d64dda`; incoming changes touch216 paths.
No force, reset, rebase, dependency reinstall or alternative checkout was used.

Before merging, the Windows process inventory showed only the read-only dashboard Python service,
not a trainer or evaluator. Both selected-native evaluation workers had completed. The old prohibition
on editing producing files under the active72k run therefore no longer blocked this requested merge.

## Reconciliation

The only Git content conflict was `AGENTS.md`: both machines had prepended distinct execution history.
Both histories were retained, with a new current Windows summary above them. Source code merged
without conflicts. Earlier LIVE entries are historical, not permission to resume those jobs.

Relevant incoming capabilities now present:

- CT-only autonomous cascade, independent native scoring and reference isolation tests.
- Predicted-region geometry, largest-component crop policy, crop diagnostics and explicit spatial-unit reviews.
- Portable cohort binding and fixed-cohort evaluation with complete failure accounting.
- Saved native-prediction viewer and the crop-variation experiment handoff.
- Research/evidence workflow, retrieval work, UI updates and test-portability improvements.

The current Windows session, executor, prepared-input provider, CUDA safeguards, EMA implementation,
MLflow integration and training entry points are unchanged from `3f9b64a`. In particular, newer Mac
code did not replace the Windows trainer with an older MPS-only route or remove local training files.
`MACHINES.md` now reflects the existing Windows qualification instead of its imported inventory-pending
assumption; the old pre-inventory notes remain labeled historical.

Two shared producing geometry modules did change:

1. `localizer_preprocessing_v4.py` permits explicitly configured output caps up to64million voxels.
   This does not change the PanTS segmenter's cached training inputs or silently enlarge a configured cap.
2. `segmenter_geometry_v2.py` exposes an optional sampling cap, retains the default16million cap,
   records provided versus predicted ROI origin and adds image-only preparation. Default provided-ROI
   numerical outputs remain unchanged on the synthetic comparisons described below.

Old execution receipts retain their original code hashes and must still reject a changed checkout.
Do not repin old receipts, resume a finished experiment, or present synthetic parity as new real-data
qualification. The successor needs its own receipt and bounded qualification for the changed augmentation
path; existing cohorts, source audits, caches and settled overlap decisions are reused.

## Windows portability adjustments

The imported source-path inventory has a fixed SHA256. Git's Windows CRLF conversion changed its disk
bytes despite equivalent JSON. `.gitattributes` now fixes LF for that one fixture, and its working copy
was mechanically normalized to the original published checksum:
`53ec2b70bb7bdd646a4fbe26e2760a826652b30a550a247a963866c82780cf45`.
No expected hash was weakened or changed.

One imported test used `/absent/...` as an absolute path, which is not fully absolute on Windows.
It now uses absent paths beneath pytest's platform-native temporary root, preserving the test's
assertion that compatible prediction reuse needs neither the relocated CT nor model payloads.

A real symlink-escape test cannot create symlinks without Windows privilege1314 on this host.
It now explicitly skips only that capability failure and retains the real escape assertion on capable
hosts. Other errors still fail. No Windows privileges were changed and no production path guard relaxed.

## Verification and limits

- Workspace sanity check passed at `C:/Users/quinn/Desktop/PROWL`.
- Before merge:18 existing EMA/review tests passed.
- After merge:100 training/geometry/cascade/checkpoint/MLflow tests passed,1 explicit native MPS skip.
- After portability adjustments and the new plan:56 evaluation/cohort/viewer/specification tests passed,
  2 skips (MPS `fcntl` unavailable and symlink privilege unavailable). This is156 distinct focused passes
  and3 declared skips in the merged checkout, not a full-repository test claim.
- Direct comparison against the `3f9b64a` geometry implementation: all returned arrays, transform
  records, hashes and fidelity fields exactly match for three synthetic affine cases (0,.03,.4radians).
  No real CT payload or checkpoint was loaded for this comparison.
- The new structured experiment and existing control-report/development/config checksums were read back.
  No scientific metrics were regenerated and no historical report was modified.

The initial broader portability attempt failed during collection: the old Mac duration-readiness
dependency chain imports Python's Unix-only `resource` module. It was not bypassed, weakened or
represented as passing. This legacy path remains unqualified on Windows and is separate from the
current full CUDA trainer whose tests passed. The first incoming evaluation test run also retained
the two failures above before their scoped portability correction (45passed,2failed,1skip).

The full Python repository suite, frontend dependency installation/build, live research services,
Mac runtime and real-CUDA successor qualification were not exercised. Incoming Markdown contains
intentional two-space hard breaks reported by `git diff --check`; they were preserved. New local
changes have no whitespace errors. No browser/dashboard service was restarted.

## Experiment handoff

The next plan is [PanTS lesion outlining with varied training views](PANTS-AUGMENTED-VIEWS-24K-20261017.md)
with its structured JSON companion and portable consistency tests. It takes priority over crop
variation for the immediate provided-ROI Dice question. Crop variation remains available for the
separate autonomous-localization question. Specification is complete; augmentation code, CUDA recovery
qualification, changed-factor audit, new frozen receipt and explicit scientific launch remain separate.

No new model run, scheduled monitoring, test-set evaluation, dataset download, duplicate audit or
public push occurred during this integration.
