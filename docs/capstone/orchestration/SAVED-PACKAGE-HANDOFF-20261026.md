# Saved-package integrity handoff — October26,2026

The first production-facing workflow adapter consumes an explicitly pinned existing saved prediction
package. It verifies the production ReviewStore manifest contract and every named file's size/hash,
then produces the exact case-package/prediction IDs used by the review service. The source stays
read-only. No inference, voxel decoding, literature generation or review decision occurs.

`src/operations/saved_package_workflow_v1.py` supplies integrity → handoff stages to the selected
repository executor. Reuse rechecks external source bytes, not merely a cached descriptor. A changed
manifest/member or replaced source directory blocks downstream execution. Research-local artifacts
cannot silently be relabeled synthetic (or vice versa) during reuse.

The handoff explicitly says measurements were not evaluated, literature was not attached, and no
review decision was made. This is source integrity and target identity, not segmentation accuracy,
full geometry validation, diagnosis, UI migration or complete case-package assembly.

## Evidence

107 focused/existing tests pass in2.73s, including package/manifest mutation, wrong pin, source-root
replacement, sensitivity mismatch, unchanged source bytes and equivalence with actual ReviewStore
review-target IDs. Existing artifact/research/review regressions and subprocess recovery still pass.
Two existing Starlette/FastAPI deprecation warnings remain.

The CLI was also run against the existing local native-measurement development package. First run
completed integrity/handoff; explicit repeat revalidated and reused both. Receipts are retained at
`outputs/prowl/saved-package-workflow-20261026/summary.json` and adjacent logs. The adapter produced
small metadata artifacts, not another copy of the CT. No human review was synthesized.

## Use

Use a dedicated existing workflow directory; keep the source separate. Obtain the manifest hash
from the intended package's trusted handoff, then supply it explicitly:

```sh
.venv-retrieval/bin/python scripts/diagnostics/qualify_saved_package_workflow.py run \
  --root PATH_TO_WORKFLOW_DIRECTORY --source PATH_TO_SAVED_PACKAGE --manifest-sha256 EXPECTED_SHA256
```

`plan` is read-only; with `--resume-of UUID` it validates prospective reuse. `resume` requires the same
explicit source/pin and a parent UUID. `inspect`/`status` require only root and `--run-id UUID` and
report recorded state without asserting current source validity. Failed run IDs are printed for
inspection. The default50GB reserve remains in force. The command is not connected to live services
and does not launch or restart them.

Next integration boundary: consume this verified identity in the broader package workflow alongside
an explicitly captured, validated literature response. A live answer or model job must retain its
own admission/resource policies. W04-01 remains In Progress; this does not close all G3 requirements.
