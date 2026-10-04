# Portable test boundary — October 3, 2026

## Decision and outcome

After the first repository review, Quinton asked Codex to continue the recommended review and
necessary work. This dispatched the routine R-01 portability repair and R-02 Monday account.
The repair is complete: **2,933 fast tests pass in a temporary file export with no `outputs/`,
no local `roots.yaml`, and no Git metadata. Eight additional local-evidence tests passed in the
focused checks.** Production consumers, scientific results and historical requests are unchanged.

The export uses the existing Python 3.12 `.venv-prowl` dependency environment. This verifies the
proposed file boundary, not an independent fresh dependency installation or full UI/release gate.
Native process inspection was used for existing supervisor tests; no real-data experiment ran.

## Changes and preserved checks

Default tests now read hash-checked committed fixtures rather than ignored diagnostic outputs.
Two fixture directories under `tests/fixtures/` distinguish retained real numeric metadata from
invented tensors. Their data payload totals 3,924,932 bytes, excluding manifests and README files:

- `retained_segmenter_metadata_v1`: cache/input/target/comparison metadata, the exact consumed
  CAP-EXP-013 request and native baseline, and the exact 7,200-member train compatibility control.
- `retained_diagnostic_metadata_v1`: selected candidate/header metadata, verified batch selections,
  native scoring input metadata, localizer binding/ancestry and the previously sealed probe path/hash.

No imaging, mask, tensor, model, cache or probe payload is included. Extraction denied opens under
`/Volumes/` and array/checkpoint suffixes. Fixtures contain project-generated source identity,
geometry and numeric records, not downloaded papers or private clinical text. Presence of a record
does not qualify a source or authorize a job. The protected train control remains byte-identical;
original membership and eligibility are unchanged.

Existing role, substitution, coverage, request, mutation and storage-limit assertions remain.
Portable candidate tests validate the real retained batch metadata through the unchanged validators;
the original receipt/header reader chains are verified separately. Parent request fault tests use
sealed parent metadata rather than reopening a probe tensor. Storage arithmetic uses an invented
temporary registry with a checked byte hash; refusal tests require no machine-local registry.
The fixtures never fall back silently to local outputs.

`pytest.ini` registers and excludes `local_evidence` from the default fast suite. Explicit tests
compare fixtures with the original compatibility control, baseline/request, verified cache inputs,
metadata refresh, candidate selection chains, native scoring inputs, localizer ancestry and
continuation proposal. Missing local evidence fails these tests; it is not silently skipped.

Four short/v5 request objects (invented and qualified-real metadata domains) remain canonically
byte-identical to those made by the original fixture builders. Production source files and Claude's
accepted retrieval files were not changed by this repair.

## Verification and retained failures

| Check | Result |
|---|---|
| Initial focused repair, including first four local-evidence tests | 207 passed; two existing Torch deprecation warnings; 24.70 s |
| Broader dependency repair, including remaining four local-evidence tests | 233 passed; same warnings; 11.38 s |
| Complete fast suite in export, final attempt | 2,933 passed, eight local-evidence tests deselected; same warnings; 121.03 s |
| Short/v5 request equivalence | Four of four exact canonical byte comparisons |
| Scoped whitespace check | `git diff --check` passes |

The first full export exposed more transitive dependencies: 100 failures and 15 setup errors,
with 2,818 passes. Its log is retained; no test was disabled to hide that result. Dependencies were
traced to candidate metadata, native scoring inputs, localizer parent references and local storage
configuration, then repaired and rechecked. An initial extraction helper import failed before
extraction; setting the explicit project import path resolved it. These are test-review attempts,
not consumed experiment requests or training retries.

Local evidence is retained under `outputs/prowl/TEST-PORTABILITY-20261003/`: fixture extraction
manifests, both focused logs, the failed and successful export logs, exported test hashes and
request-equivalence record. Temporary exports have no `.git`; the authoritative checkout remains
the original PROWL directory. Same-disk review copies are not independent backups.

Reproduction, with the project environment and native process access:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider

env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv-prowl/bin/python -m pytest \
  tests/test_retained_segmenter_evidence.py tests/test_retained_diagnostic_evidence.py \
  -m local_evidence -q -p no:cacheprovider
```

## Historical pin boundary

D-335 still names the original 142 producing/test pins. Seven currently edited test sources differ:
`segmenter_short_fixtures.py`, `segmenter_v5_fixtures.py`, `test_segmenter_cache_qualification.py`,
`test_segmenter_inference_transaction.py`, `test_segmenter_lowrate_native.py`,
`test_segmenter_native_score_transaction.py`, and `test_segmenter_v5_boundaries.py`, all under `tests/`.
The other 135 current pins still match. The original sealed sources and controls remain preserved;
historical manifests/results were not repinned. Old source guards should refuse execution against
changed test sources. A future experiment must qualify its actual sources with a fresh scope.

The [first repository proposal](GIT-CHECKPOINT-REVIEW-2026-10-03.md) remains historical and is
preserved in its local byte snapshot. The refreshed V2 proposal must define any later commit.
No staging, commit, push, external backup write, quota change, experiment, source job or retrieval
phase was performed. [Monday's account](COURSE-START-SUMMARY-2026-10-05.md) and the
[remote queue](WEEKEND-AND-REMOTE-WORK-PLAN-2026-10-03.md) provide the next discussion context.
