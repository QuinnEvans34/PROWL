# Week 2 clean-environment reproduction — October 13

## Scope and identity

Verified a clean source export of commit `69a77c36a0b83da9f301b0489ce3c881b4f1055c` on
macOS 27.0.1 arm64. The export begins without Git metadata, ignored `outputs/`, or local
`configs/local/roots.yaml`. A new `.venv-prowl` and `ui/node_modules` were installed inside
that export; the working checkout's environments were preserved. No external corpus processing,
real-data experiment, native MPS qualification or training run was launched.

Python **3.12.13**, pip **26.1**; Node **24.21.0**, npm **11.19.0**. The existing hash-enforced
macOS Python lock installed all **58** packages with exact version agreement and `pip check`
passed. UI installation used `npm ci` with the committed lockfile. Cached downloaded wheels
are compatible with a clean installation: no installed site-packages were reused.

Evidence: `outputs/prowl/testing/reproduction-20261013/`. `identity.json` records commit,
platform and lock/configuration hashes. Install, inventory, collection, test, build and audit logs
are retained alongside the isolated source export. Local runtime files are not Git deliverables.
The suite commands have 600-second Python and 180-second UI/browser invocation bounds.

## Results

- Clean Python installation and dependency consistency: **pass**.
- Clean UI installation: **pass**.
- UI unit tests: **37 passed**, four files, 1.01 seconds reported by Vitest.
- Production build: **pass**, with the existing large-chunk warning.
- Synthetic Chromium browser checks: **2 passed**, 3.2 seconds. These verify fixture API/UI
  behavior, not native CT rendering or an independent browser-binary installation. Existing
  Playwright Chromium installation was used.
- Default Python collection: **fails**; 4,935 selected / 4,943 collected, eight deselected,
  one collection error. This prevents a normal full-suite run.

`tests/test_segmenter_duration_readiness.py` reads ignored
`outputs/prowl/SEGMENTER-DURATION-DUR03-20261007/dispatcher-blocker.json` at module import.
The file is unavailable in a clean checkout. Its `accepted` fixture also reads historical local
qualification receipts. This is a test portability defect, not a package installation failure.
Do not copy the whole local outputs directory into the export or treat a local-only pass as a fix.

A diagnostic invocation uses `--continue-on-collection-errors` to inventory remaining failures;
it retains the collection error and cannot qualify the fast gate. Final counts are recorded below.

## Reproduce

From an isolated export of the stated commit, with a verified Python 3.12 interpreter:

```sh
python3.12 -m venv .venv-prowl
.venv-prowl/bin/python -m pip install -r requirements/locks/macos-arm64-py312.txt
.venv-prowl/bin/python -m pip check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv-prowl/bin/python -m pytest tests --collect-only -q -p no:cacheprovider
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
cd ui
nvm use
node --version
npm --version
npm ci
npm run test:run
npm run build
npm run test:e2e
```

Keep `PROWL_NATIVE_RESUME_TEST` unset. `pytest.ini` excludes slow, licensed-data,
local-evidence, MPS, network, browser and release tests from the default fast selection.
Browser tests start their own local fixture services and use the export's `.venv-prowl`.
If Chromium is absent, install it separately using the documented Playwright command; that
installation was not exercised by this check. No package or lock upgrades were made.

## Dependency audit and remaining limits

`npm audit` reported **10 affected package entries: 4 moderate, 4 high and 2 critical**.
Critical entries: `vitest` and transitive `tinypool`; other entries: `vite`, `@vitest/mocker`,
`baseline-browser-mapping`, `browserslist`, `esbuild`, `nanoid`, `postcss`, `source-map-js`.
These are audit results, not ten independently verified exploitable paths in PROWL.
Keep `ui-audit.json`; assess applicability and upgrade the relevant tooling in a separate,
reviewed dependency change with UI/build/browser regression checks. Do not run an automatic
force fix during environment qualification. npm also reported esbuild/fsevents install-script
approval notices; the actual build and browser checks succeeded.

The current shell defaults to Node 20.20.1. Explicit Node selection is required; the earlier
Node 24.19.0 result remains historical, while this run verifies the committed 24.21.0 pin.
No Linux/Windows lock, Lenovo execution, model quality, full release gate or human hours are
certified. W02-05 remains open for portability repairs and Sunday acceptance.

## Final Python reconciliation

Diagnostic result: **4,934 passed, 1 skipped, 8 deselected, 1 collection error**, 247.41 seconds,
exit 1. There were no execution failures among the collected tests. The one skip is the explicit
native MPS optimizer-continuation qualification (`PROWL_NATIVE_RESUME_TEST` unset); it is not a
missing-package skip. Eight `local_evidence` tests are intentionally deselected by the existing
marker policy. Sixteen warnings remain in the retained log. The failed readiness module is absent
from the collected count, so 4,934 passes do not cover that module or qualify the full fast gate.

Next bounded repair: separate the readiness module's portable source-path/refusal tests from
historical receipt integration. Use a reviewed committed script-name fixture for portable tests;
move genuine retained-receipt checks behind the existing explicit local-evidence selection, with
reads inside fixtures rather than module import. Preserve all assertions and historical source pins;
do not rewrite old scientific receipts or weaken production source guards. Verify the repaired
collection in a fresh export, then rerun the affected portable tests and fast gate. This repair is
not implemented by the environment audit.
