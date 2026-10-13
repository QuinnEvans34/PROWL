# PROWL Python foundation environment

This starts the approved Plan 09/10 clean test foundation. It is not yet the full training,
retrieval, orchestration, or release environment. Historical `requirements.txt` and `.venv312`
remain unchanged; do not install into the historical environment.

## Inputs and exact resolution

- `runtime.in`: reviewed direct scientific/config/endpoint imports needed by the existing CPU tests.
  Direct scientific pins match the historical environment to avoid changing these variables during
  the baseline; optional historical dependencies are not automatically adopted.
- `dev.in`: the approved pytest, coverage, JSON Schema format-validation, and HTTP testing tools.
- `locks/macos-arm64-py312.txt`: all 58 resolved packages, exact versions, and wheel SHA-256 hashes
  for the September 19 macOS-arm64/CPython-3.12 resolution. pip itself is recorded separately.

No Linux lock has been generated or validated. Do not reuse the macOS wheel hashes for Linux CI.
MLflow registration is mocked in the existing test: passing it does not prove a working tracker.
MLflow, orchestration, browser tools, and the full imaging runtime will be reviewed with their owning
components rather than silently included here.

## Reproduce

Use a verified Python 3.12 interpreter. `.venv-prowl` must be a new environment when demonstrating a
clean install; never delete or overwrite an existing environment to force that claim.

```sh
python3.12 -m venv .venv-prowl
.venv-prowl/bin/python -m pip install -r requirements/locks/macos-arm64-py312.txt
.venv-prowl/bin/python -m pip check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests
```

The lock enforces binary packages and hash verification. The first clean installation used
Python 3.12.13 and pip 26.1 on macOS 27.0 arm64. Installation reports and test records are retained
locally under `outputs/prowl/testing/foundation-2026-09-19/`; portable interpretation belongs in
`docs/capstone/testing/FOUNDATION-2026-09-19.md`.

## Current-source verification

The October 13 clean install reproduced all 58 locked packages on Python 3.12.13 / pip 26.1
and passed `pip check`. Installation success does not mean every current test is portable:
the fresh source export exposed a collection-time dependency on ignored diagnostic outputs.
See [the current reproduction report](../docs/capstone/testing/REPRODUCTION-2026-10-13.md)
for test results and remaining work. Keep historical September/October 3 results tied to their
original source versions.

## Moving the checkout

Virtual-environment activation scripts and installed command launchers contain absolute paths.
After moving the repository, preserve the old environment and recreate `.venv-prowl` at the new
location from the same platform lock; do not assume that a working Python interpreter means its
launchers work. Keep `.venv312` historical. Confirm the selected editor/project root separately.
Run `python3 scripts/diagnostics/check_workspace.py` from the intended root before setup.
The September 20 relocation is recorded in
`docs/capstone/operations/RELOCATION-2026-09-20.md`.

## Intentional dependency updates

Change the reviewed direct input, resolve in a separate empty environment with a recorded pip
version, review the complete dependency diff, regenerate the platform lock from the resolver's
versions/wheel hashes, and install that lock into a clean environment. Run affected tests and keep
first failures. Record installed inventory separately from the declared lock. A successful package
installation alone never qualifies MPS, real-data training, or G0-verification.
