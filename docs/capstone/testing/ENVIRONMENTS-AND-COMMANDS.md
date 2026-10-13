# Test environments and command contract

**Status:** Approved design; foundation lock implemented, current reproduction limits below\
**Decisions:** P09-01, P09-02, P09-04, P09-09, P09-10, and P09-17 through P09-19  
**Last reviewed:** 2026-10-13

## Current implementation and reproduction

Python 3.12.13 / pip 26.1 on macOS arm64 installs from the hash-checked
`requirements/locks/macos-arm64-py312.txt`; see [setup instructions](../../../requirements/README.md).
This is the foundation/test environment, not the full historical training environment.
Use Node **24.21.0**, pinned in `ui/.nvmrc`; the October 13 clean run used npm **11.19.0**.
Select the version explicitly with `cd ui && nvm use`, then verify `node --version` and
`npm --version` before `npm ci`. The ambient Node 20 shell is not the supported UI baseline.

[October 13 reproduction evidence](REPRODUCTION-2026-10-13.md) records clean installation,
UI checks and Python collection/skip reconciliation. Fresh Python installation succeeds, but
full current-source portability remains open because tests depend on ignored local evidence.
The commands below are design intents where wrappers have not yet been implemented; do not assume
a `verify` executable exists. Actual default Python selection is defined by `pytest.ini`, including
the exclusion of `local_evidence`. No Linux lock or cross-machine execution is qualified here.

## Supported baseline

- Python 3.12 in a new clean capstone virtual environment.
- Node 24 LTS and its recorded npm version.
- macOS/Apple Silicon for authoritative local scientific verification.
- Linux/Python 3.12/Node 24 for GitHub fast portability checks.

The implemented foundation uses `.venv-prowl` and the platform lock above. `.venv312` remains
historical evidence. Preserve existing environments; reproduce in a separate clean source export.

## Dependency layers

### Python runtime

Only packages needed to operate the corresponding capstone components. Training, retrieval, serving,
and document/report utilities may become named groups if a single environment proves too fragile.

### Python development/test

Initial minimum:

- `pytest`;
- `pytest-cov`;
- `jsonschema` plus format validation dependencies;
- `httpx` for FastAPI/HTTP tests;
- existing runtime libraries needed by selected tests.

Do not add parallel runners, random-order, snapshot, property-testing, flaky rerun, or reporting
plugins until a test requirement proves their value.

### UI development/test

Initial minimum:

- Vitest;
- React Testing Library and DOM Testing Library;
- `user-event`;
- jsdom;
- Playwright test with Chromium;
- axe integration for selected states;
- optional V8 coverage support.

Exact versions are committed through `package-lock.json`; installation uses `npm ci` in formal runs.

## Command contract

The eventual wrappers must expose these stable intents even if internal flags change:

```text
verify fast
verify contracts
verify integration <component>
verify ui
verify browser
verify local-real <component>
verify release
```

The implementation may be a small Python entry point plus npm scripts. It must print underlying
commands, preserve non-zero exits, write a test-run record for formal modes, and refuse unknown
components.

## Direct runner expectations

### Python fast

Equivalent selection:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q -p no:cacheprovider
```

Strict marker registration and strict xfail behavior apply. Results may additionally write JUnit and
coverage, but those outputs cannot change exit status.

### UI unit/build

```text
npm --prefix ui ci
npm --prefix ui run test:run
npm --prefix ui run build
```

Watch mode is convenient for development but never used as formal evidence.

### Browser

```text
npm --prefix ui run test:e2e
```

The command starts controlled local fixture services, runs the single Chromium critical-flow project,
and stops services even after failure. Playwright traces/screenshots are retained on failure.

### Local real/MPS

The wrapper first validates:

- root aliases/mount identity;
- source snapshot and fixture manifest hashes;
- free space and write target;
- Python/package/device identity;
- requested cohort/artifact IDs;
- that publisher-test data is not entering a non-final test.

Missing prerequisites produce a failed preflight record, not a skip.

## Time budgets

Freeze budgets after the first clean measured run:

- fast Python plus UI unit/build: target minutes, not tens of minutes;
- component integration: short enough to run during the owning implementation session;
- browser critical flow: one bounded local run;
- local-real/MPS: explicitly scheduled and component-selectable;
- release: may be long, but has a manifest, resumable independent suites, and no hidden work.

Any suite crossing its budget is reclassified or optimized; its tests are not deleted to meet time.

## Upgrade policy

- Dependency updates are intentional batches with lock diff, affected suite, and rollback.
- Scientific/runtime upgrades rerun relevant tolerance/geometry/model compatibility checks.
- Browser/UI updates rerun build, component, browser, accessibility, and visual checks.
- Node 22 LTS is the named fallback if Node 24 exposes an incompatibility that cannot be resolved
  within the bounded setup period.
- No environment uses `latest` as its recorded identity.
