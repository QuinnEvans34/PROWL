# Week 2 protected portable cohort delivery

**Date:** October 12, 2026. **Card:** [W02-01](https://trello.com/c/8WvBwmi7).
**Result:** portable metadata package and protected development-evaluator consumption implemented
and verified on Mac. No training code changes, new model run, test payload reads or membership changes.

## Gap and change

The existing fixed-cohort evaluator pinned payloads but accepted a free-form cohort name and case list.
Its version 1 plans did not enforce the protected registry. Existing small historical cohort registries
have different fixed populations; they cannot simply be presented as the full 1,408-member admission.

`src/data/portable_cohort.py` derives a portable snapshot from the accepted October 7 full-cohort
review, pinned manifest/split files, and individually hash-pinned prepared metadata. It reuses
`protected_identity.py` for approved base memberships, PanTS identities and group/role checks.
It copies source hashes already established by preparation; it does not rehash/decode image arrays.
Root alias plus relative path replaces source absolute paths in portable member records. Local root
maps remain outside the package. Device/inode/timestamp observations are not treated as portable identity.

Version 2 evaluation plans embed the package, its digest, current review pin and local root map.
Prediction and scoring validate the exact complete 75-member development population and CT/reference
identities before work. References and cohort metadata remain outside the CT-only worker request.
Changed roles, membership, content bindings and review identities refuse admission. Files are verified
against source hashes by the existing prediction/scoring workers when used. Compatible saved-output
reuse retains its prior checks and does not imply a fresh read of original CT/model payloads.

Version 1 remains available for historical/synthetic workflows; it is **not protected cohort
qualification**. Use a generated version 2 plan for the new development-cohort workflow. This does
not retrofit or authorize the training consumers, which belong to the other laptop/chat.

## Retained result

Evidence directory: `outputs/prowl/portable-cohort-20261012/` (local, ignored; not asserted published).

- `cohort.json`: 1,333 train / 75 validation-role development cases. Original protected bases retain
  7,200 train / 1,800 validation / 901 test identities; no test image or annotation is opened.
- Package SHA256: `0e63126be7df03072b0064e9740c9fe6ca7efec766f2324e79a49ddde278d8e2`.
- Accepted review SHA256: `24c12c5ed107c8ed0ce8fcc1ecba9ed196bab07b5b8ebfb6e1ae9b62a655f771`.
- Two builds are byte-identical. All 75 CT and reference hashes match the retained October 9
  development plan. All 75 CT paths are present; this is a presence check, not a fresh content audit.
- Generated `evaluation-plan.json` and independently CLI-generated `evaluation-plan-cli.json` match:
  `9d2694433ed18e3480dfec3e92dfe74c86a5cc8cfa0540d4678d0d137976092c`.
- `verification.json` records counts, comparisons, source presence and limitations. The real metadata
  build opens zero payloads and invokes zero models. `verify_metadata.py` retains exact inputs.
- `tests.txt`: **58 passed**, including 21 new portable-cohort tests, existing evaluator integration
  (including its tiny synthetic model path), and protected identity/group tests. Two existing upstream
  TorchScript deprecation warnings. No full repository test-suite claim.

The first real build refused the legacy manifest's `development` spelling. An explicit adapter maps
that term to the original `validation` role; pinned membership must still match. Its dedicated test
passes. No split file or original evidence was edited, and the refused attempt wrote no package.

## Usage

Build with `scripts/prepare_portable_cohort.py build --help`. Inputs are the current reviewed admission,
its trusted SHA256, exact manifest/selected/base-role files, original source root and prepared metadata
root. The output path must be new. A copied metadata directory may use a different local cache path;
each record is still checked against the admission pins. No cache arrays are needed to build metadata.

Resolve on either machine with an absolute local mapping, for example a JSON file containing
`{"pants_source": "/absolute/local/extraction-root"}`. On Windows use the appropriate native absolute
path. The selected extraction root must contain the same relative layout and file contents. Traversal
and symlink escape are refused. Actual Windows/Lenovo execution has not been tested here.

Prepare an inference settings file with exactly `inference` and `limits` from the evaluator settings
contract; model paths/device are local. Then:

```sh
.venv-prowl/bin/python scripts/prepare_portable_cohort.py plan \
  --package /path/to/cohort.json --package-sha256 TRUSTED_PACKAGE_SHA256 \
  --current-review-sha256 CURRENT_REVIEW_SHA256 \
  --roots /path/to/roots.local.json --settings /path/to/settings.local.json \
  --output /path/to/new-evaluation-plan.json
```

The command validates metadata and prints the new plan digest; it runs no model. Use that digest with
existing `scripts/evaluate_autonomous_cohort.py predict --plan ... --plan-sha256 ... --output-dir ...`,
then its separate score stage. That later execution needs its own selected model/runtime scope.
Plan hashes change with local paths/settings; **package identity remains constant**. Do not compare
machine-local plan hashes as though they were the portable cohort identity.

Trusted package/current-review pins must come from reviewed evidence, not be regenerated to accept
an unexpected change. An older accepted snapshot does not prove there are no newly reported holds:
if the admission review changes, rebuild and re-admit rather than substituting its digest. This adapter
preserves the supplied admission; it is not an automatic policy/revocation service.

## Acceptance and limits

| Criterion | Evidence |
|---|---|
| Repeatable frozen population/content identity | Two complete real metadata builds match |
| Root portability | Different temporary roots resolve identical package hashes and differing local paths |
| Protected roles and grouping | Exact approved base hashes; member ancestry; existing source-group tests |
| Wrong role/member/hash, missing labels, stale review | Consumer-level rejection before output/worker; scoring also rejects |
| Consumer connection | Version 2 reaches existing prediction runner with CT-only requests; generated real plan validates |
| Original/test protection | Original inputs unchanged; only test membership text inspected |

PanTS retains `study_as_subject_fallback` / `unverified_unique`: biological-patient independence is
not established. Reference-empty labels are not verified healthy controls. Model pretraining/selection
independence and annotation expertise are not established by this package. Seven source-unit issues
remain in W02-02; they are retained in the fixed population rather than silently dropped. Remote
execution remains unverified and is not required to claim the demonstrated local root-remapping test.

The scoped W02-01 package/consumer delivery is complete with these explicit limitations. Next:
W02-02 source/failure disposition, then W02-04 saved prediction viewer integration.
