# Localizer content verification: ten current files match retained evidence

September 28, 2026. **Completed: bounded content-identity verification.** No decoding, source edits,
annotation promotion, cohort publication, root activation or training.
Specification: [exact job and limits](LOCALIZER-CONTENT-VERIFICATION-JOB-2026-09-28.md).
The original job JSON remains unchanged, SHA-256
`d1707a08c36a29980302294cba66b878ec3a819004605e2422def872a2acc1f8`.

## Result and retained evidence

All ten specified compressed CT/pancreas files matched both the metadata inventory's stat identity
and the retained voxel-audit hashes. **44,195,710 bytes** read in one sequential attempt per file;
wall time **4.67 seconds** including preparation and finalization. No substitutions or retries.
Caching is unknown; this is not a cold-cache benchmark for the entire dataset.

| Cases | Current byte result | Qualification implication |
|---|---|---|
| 3, 26, 31 | CT and pancreas hashes agree | Retained finite-array, nonempty-target and geometry observations remain bound to these bytes; positive qualification is still pending |
| 78 | CT and pancreas hashes agree | Empty-target/coverage finding persists; excluded from this pancreas-present smoke, original membership retained |
| 266 | CT and pancreas hashes agree | Unknown physical units remain unresolved; geometry-dependent training stays held |

Evidence package:
`outputs/prowl/localizer-content-75d83d2d-cdca-4d57-be29-e7801a8b6b36/`.
It contains request/specification, implementation text/hashes, ten per-file results, summary and final
verification receipt: **14 files, 56,064 bytes**. All **13 receipt-covered hashes** were independently
rechecked after execution. Verification receipt SHA-256:
`fe33fa752a49941b512919105528dd9e27a92e5b6da7a6ded15b90de8c2e8ccc`.
Parent peak RSS: **59,572,224 bytes**. Per-worker peak RSS and timing are in the per-file records;
all passed the 512 MiB ceiling. The registered APFS volume identity was rechecked natively.

This proves current byte continuity with retained local measurements, not publisher attestation,
archive-to-extracted equivalence for every member, annotation correctness, or whole-source readiness.
No validation/test payloads, lesion masks, unrelated organ labels or archives were read.

## Implementation and verification

New narrow runner: `scripts/diagnostics/localizer_content_verify.py`.
New synthetic tests: `tests/test_localizer_content_verify.py`.
The runner independently pins the job JSON, checks every control pin, binds the existing registry to
the prior metadata request, and streams only the declared source files. No-follow descriptor walking,
pre/post identity checks and path reopening reject symlinks, replacements and mutations. Read caps,
per-file/overall deadlines, exclusive evidence creation and output limits constrain the job. A parent
supervisor monitors worker RSS; workers also report/check their own peak RSS. Failed attempts retain
partial evidence without a valid successful completion receipt. This remains a local diagnostic,
not the Plan 04 publisher/resolver or a hostile concurrent-writer guarantee.

Commands run natively:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/test_localizer_content_verify.py -q -p no:cacheprovider
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
env PYTHONDONTWRITEBYTECODE=1 .venv-prowl/bin/python -m scripts.diagnostics.localizer_content_verify --run
```

**27 focused tests passed; 920 full-suite tests passed**, with two existing upstream torch.jit
warnings. Tests cover altered controls/specification, wrong role/kind, bad hash, missing/resized/
replaced files, symlink paths, traversal, mutation during streaming, read/RSS/time/output limits and
failure without completion. Real subprocess supervision is exercised on invented files.

The first sandboxed test invocation had 24 passes and three failures because `/bin/ps` was blocked.
Native process access resolved that environmental restriction. The supervisor also now checks an
expired deadline before attempting another memory query. No memory safeguard was disabled and no
dependency was installed. The live job used native disk/process access; no live attempt failed.

## Next bounded task: positive qualification evidence and issue supersession

Do not repeat this audit simply to accumulate checks. Reverify hashes again when a consumer needs
fresh bytes, and preserve this receipt as the current continuity evidence.

Before cases 3/26/31 can receive positive records:

1. Trace the retained source/archive/extraction evidence and exact integrity coverage into the new
   source-readiness assessment. Local content agreement cannot fill an unsupported source assertion.
2. Record release-applicable pancreas provenance and affirmative permission for the specific local
   research training purpose. Preserve source-asserted versus project-verified distinctions and
   separate release restrictions; no blanket rights clearance.
3. Bind the approved strict-binary mapping and reviewed geometry policy to these exact files.
4. Inspect/record target coverage and CT-mask alignment for each proposed consumed case. Retained
   nonempty counts alone do not establish anatomical correspondence or expert contour acceptance.
5. Specify and test the narrow append-only path from each existing hold to its supported new
   assessment. Preserve every old record; the current qualification checker cannot accept a case by
   silently dropping unresolved issues.

Then build the proposed two-member frozen train subset, with shortage rejection and the unchanged
protected parents, and verify the cohort-only consumer. Preprocessing, learning/checkpoint tests and
run authorization remain the next training dependencies. Claude's P2 planning lane was untouched.
