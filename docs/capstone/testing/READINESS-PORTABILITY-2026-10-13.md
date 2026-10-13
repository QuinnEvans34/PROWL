# Readiness test portability repair — October 13

## Change

The clean-environment audit at `d27adf3` found a collection-time read of an ignored historical
receipt in `tests/test_segmenter_duration_readiness.py`. The default suite now uses a committed,
hash-checked inventory of the same 28 approved script paths. The inventory contains source paths
only; no patient data, model state or execution authority. Its SHA-256 is
`53ec2b70bb7bdd646a4fbe26e2760a826652b30a550a247a963866c82780cf45`.
The original DUR-03 `dispatcher-blocker.json` remains untouched; its source digest is retained in
`outputs/prowl/testing/readiness-portability-20261013/fixture-origin.json`.

The original module retains 87 portable source-path, hash, provenance-forgery, symlink, hardlink,
size and rejected-payload checks. Historical receipt integration moves to
`tests/test_retained_duration_readiness.py`, marked with the existing `local_evidence` marker.
All 42 original receipt-dependent cases remain, plus one explicit comparison of the committed
script inventory with its historical receipt. Reads happen in test/fixture execution, not at import.
An AST comparison verified that every original function body and decorator is unchanged across
the two modules. This is a boundary repair, not removal of failing assertions.

Production code, launch guards, scientific receipts and historical source pins are unchanged.
Historical pinned launch requests must still reject changed source; no old request was repinned
or requalified. Moving a test does not establish that its historical integration passes today.

## Verification

- Focused default selection: **87 passed, 43 local-evidence cases deselected**.
- Explicit inventory-to-original comparison in the local checkout: **1 passed**.
- The same explicit comparison in the clean export: **fails with FileNotFoundError as expected**;
  missing evidence is neither silently skipped nor replaced with invented data.
- Fresh export collection: **5,022 selected / 5,073 collected, 51 deselected, no errors**.
  The 51 are the eight pre-existing local-evidence cases plus the 43 newly separated cases.
- Final fresh-export fast suite: **5,021 passed, 1 skipped, 51 deselected**, zero failures/errors,
  three warnings, 237.03 seconds; exit 0.

The export uses committed `d27adf3` plus the three changed/new test files, no local roots registry
or historical outputs, and the independently installed environment from the preceding audit.
No dependency upgrade or second install was needed. The initial verification harness mistakenly
resolved the venv launcher symlink to base Python and exited with `No module named pytest`;
`collect.log` preserves that harness failure. Corrected commands keep the absolute venv launcher
path without resolving its symlink; `collect-02.log` and `results-02.json` record that run.

Reproduce from a fresh checkout/export with the locked environment:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv-prowl/bin/python -m pytest tests --collect-only -q -p no:cacheprovider
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Keep `PROWL_NATIVE_RESUME_TEST` unset. Select historical integration deliberately with
`-m local_evidence`; it requires its original receipts and source identities. It is not part of
clean-checkout portability. No native experiment, external corpus lookup or training job was started.
The citation lookup remains paused at 37,630,000 records.

## Additional order-dependent fixture repair

The first full run after the readiness split finished with **5,020 passed, 1 failed, 1 skipped,
51 deselected** in 252.60 seconds. The failure was
`test_mps_lock_refuses_duplicate_before_creating_output`: it opened a lock under the checkout's
`outputs/prowl/` without creating that directory. The initial environment audit ran browser
checks against its export, which created this directory and masked that assumption. Its earlier
4,934-pass diagnostic remains valid for that populated export, not evidence of an untouched
output directory throughout the run.

The lock test now creates an isolated temporary repository/lock directory and monkeypatches the
evaluator's root for that test only. The real flock operation, duplicate refusal, denied worker
callback and no-output assertion remain. It no longer takes the working repository's MPS lock.
All **17 cohort evaluator tests pass**. Production evaluator code remains unchanged. A second
fresh export starts with no `outputs/`, no browser fixture run and no root registry, and runs
only the final default Python suite. The prior full-run failure stays in `fast.log`.

## Final disposition

The final clean-export run passes. One native MPS qualification skip is intentional and unchanged;
51 explicit local-evidence cases remain outside the portable fast selection. This closes the
identified macOS clean-environment collection/fast-suite follow-up, not local historical integration,
Linux/Windows portability, Lenovo cohort verification, dependency security or full release acceptance.
The separate npm audit findings, source-unit/anatomy questions, hours and Sunday review stay open.
No corpus processing was resumed.
