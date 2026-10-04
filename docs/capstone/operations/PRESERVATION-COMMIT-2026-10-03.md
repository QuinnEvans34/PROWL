# Local preservation checkpoint — October 3, 2026

## Agreed action

Quinton asked: “Great, lets settle the preservation commit and monday wording.” This authorizes
the local preservation commit and final wording edits. Public push remains a separate decision.
The commit identity and post-commit verification are recorded in Git history and the ignored local
receipt under `outputs/prowl/PRESERVATION-COMMIT-20261003/`.

The [final scope manifest](PRESERVATION-COMMIT-SCOPE-2026-10-03.json) governs the actual commit.
It includes all 617 files from the reviewed V2 proposal, six completed Plan 07 support documents,
and this record/manifest: **625 files**, 20 modified tracked files and 605 new files. The only later
content changes are documentation: Monday wording, current navigation/queue, and the completed
D-336–D-340 reconciliation appended by the separate support task, plus a reviewed new Claude
running-log entry. No code or test changed after
the verified export run.

The first review and V2 review/manifests remain historical evidence. Their exact byte snapshots
remain local; the final manifest identifies the differences rather than rewriting old inventories.
Same-disk review snapshots are not independent backups.

## Retrieval handback reconciliation

The completed [L1–L6 handback](../retrieval/CODEX-PLAN07-L1-L6-HANDBACK-2026-10-03.md) is its task's
stop point. D-336–D-340 record prior P2 approvals and lane ownership. Include its S1 storage
proposal, S2 draft, checkpoint addendum/file manifest and integration options so the decision
references remain complete. These documents propose later execution; preservation does not
approve storage setup, sizing, downloads, installs, signatures, cleanup or database work.
A later Claude log entry records separate S1/S2, cleanup and integration decisions, and S2 dispatch
in its cloud workspace. Preserve that record without starting those actions in this task; new S2
implementation is outside this frozen checkpoint. The earlier support manifest pins the pre-dispatch
log bytes, which still match the V2 snapshot; the final manifest pins the reviewed appended log.

The accepted P3's 30 hashes and foundation handback still match. Claude's planning/implementation
ownership remains intact; no lane file was edited by this preservation task. Exact current hashes
are checked before staging, and staged blobs are checked against the final scope before committing.
Later writes, if any, remain separate unstaged work rather than being silently folded into the commit.

## Evidence and scope

- The [portable fast suite](TEST-PORTABILITY-RESULTS-2026-10-03.md) passed 2,933 tests in an export
  without local outputs/registry. Eight separately selected original-evidence checks passed.
  Documentation-only settlement does not justify repeating the full suite.
- Current production/test files match the tested snapshot. D-335's original 142 pins remain sealed;
  seven current test sources differ and 135 match. Future experiments need fresh qualification.
- Preserve difficult cases, holds, failed attempts, consumed requests and original memberships.
  No imaging/tensor/model/cache payload, private evaluation, credentials, local root configuration
  or executable machine-specific approval enters the commit.
- The 66 initial exclusions remain untouched. Two separately proposed cleanup leftovers remain
  untouched. Public repository visibility and intentionally local evidence links are disclosed in
  the [V2 review](GIT-CHECKPOINT-REVIEW-V2-2026-10-03.md).
- Final checks cover exact file hashes/modes, JSON/Python parsing, local imports and links,
  bounded credential/private-field scans, staged whitespace and staged-byte equivalence. After
  commit, verify the parent, exact changed-path set and committed blob bytes; save a local receipt.

Staged whitespace review found only extra final blank lines in the S2 draft, P2 decision sheet
and `tests/test_segmenter_v5_executor.py`. Their existing bytes are preserved to respect lane
ownership and sealed test provenance. These three formatting exceptions are recorded; all other
Git whitespace checks pass with `blank-at-eof` excluded. No test/source hash is changed for formatting.

## Monday wording and next starting point

[Monday's account](COURSE-START-SUMMARY-2026-10-05.md) leads with demonstrated training/export/
recovery, then weak contours and the still-unbuilt autonomous cascade. It identifies concrete
Week 1 priorities without equating test count or design approval with completed model/product gates.
It has not been submitted or sent. Actual course requirements and due times still need confirmation.

Next discuss the fresh R-03 duration packet and R-04/R-05 ROI/cohort qualification path in the
[remote queue](WEEKEND-AND-REMOTE-WORK-PLAN-2026-10-03.md). No experiment is launched by this commit.
Before a later approved public push, inspect the remote tip and reconcile any intervening changes.
