# Repository checkpoint review — October 3, 2026

Prepared under Quinton's explicit request to start the repository-checkpoint review. **Review
complete; preservation proposal ready for decision. Public publication is not dispatched.** A
fresh-checkout test-portability defect is documented below; recommend repairing it before publication.
No live-index staging, commit, branch/worktree change, push, experiment or external message occurred.

## Exact preservation proposal

Base: `main` at `21f838cab6299dd02c30bb9326201e11510bb280`, September 28.
Read-only GitHub metadata confirms [QuinnEvans34/JHU-panTS](https://github.com/QuinnEvans34/JHU-panTS)
is **PUBLIC**, with default branch `main`. A push exposes this material publicly.

The [exact manifest](GIT-CHECKPOINT-FILES-2026-10-03.json) defines a proposed **596-file** checkpoint:
592 previously pending files, the reviewed `.gitignore` change, this review, the manifest and the
[weekend/remote queue](WEEKEND-AND-REMOTE-WORK-PLAN-2026-10-03.md). This includes 18 modified tracked
files and 578 new files. The manifest records path, size, SHA-256 and mode for 595 files; its own
path is included without a self-hash to avoid recursion. Its byte hash and reviewed byte copies
are retained in the ignored local review evidence.

| Group | Files | Proposed content |
|---|---:|---|
| Implementation | 300 | Data/geometry/cohort consumers, bounded operations, localizer/segmenter versions, diagnostic dispatchers, preprocessing configs and tests |
| Retrieval | 44 | Accepted P3 synthetic source/tests/contracts/design/handback, Codex reviews and current P2 planning records |
| Evidence and review controls | 252 | Decisions, experimental plans/results and failed-attempt records, data/source scopes, checkpoint/navigation records, review manifest and ignore policy |

Recommend one coherent preservation commit, rather than reconstructing a fictitious series of
past development commits. Suggested subject: `Preserve pre-course imaging evidence and accepted retrieval foundation`.
Many consumers, contracts and records refer to one another; the complete snapshot preserves those
relationships. If fixture repair comes first, regenerate this manifest and recheck its exact scope
before committing. This manifest cannot authorize later changed bytes.

## Inclusion and exclusion review

Expanded initial inventory: 658 pending regular files, 14,231,069 bytes. The original Git status
contained 597 entries because it grouped some untracked directories. All pending tracked changes
were included in the proposed review; no staged changes existed.

The original 592-file candidate set was 6,328,679 bytes. It contains only Markdown, Python, JSON,
plus the final ignore policy; no scan/mask/tensor, model checkpoint, binary deliverable or symlink
is proposed. The complete final byte inventory is in the manifest. Two reviewed text files exceed
250 KB: the 780,710-byte localizer content-batch metadata record and the 310,854-byte experiment
notebook. The batch record contains public release study IDs, source file/header identity and
bounded-job planning; it contains no imaging arrays or private clinical reports.

The manifest lists all 66 initial excluded files and their hashes/reasons. They remain untouched:

- Four machine-specific launch/storage approvals. They are consumed historical local authority,
  not portable permission for new jobs. New narrow `.gitignore` rules now ignore all four without
  changing their bytes. Documented capability/proposal metadata under `docs/capstone/` remains
  included as historical provenance; its presence does not grant execution permission.
- `MedFormerPanTS/`, loose PubMed XML/PANORAMA ID material and downloaded reference content.
- Unreviewed branding/media, proposal/draft binaries, old report/planning/build documents and
  unrelated root scripts. The approved proposal v3.8 and appendix v3.1 are among the local binary
  exclusions; this is not a backup/publication of every capstone source document.
- Already ignored data, model weights, caches, predictions, real receipts, local configuration,
  virtual environments, credentials and private evaluation material stay outside Git. Those items
  are not exhaustively inventoried by the 658-file pending-Git inventory.

Bounded scans of the proposed text found no private-key blocks, common GitHub/AWS/OpenAI token
formats, credential-bearing URLs, long quoted credential assignments or patient-name/birth/accession
field matches. No secret values were printed. These are pattern checks, not a comprehensive security
audit. Local owner/check-out paths, volume identifiers, public dataset IDs/hashes and native evidence
locations remain visible in historical documentation by design, as in the previous checkpoint.

## Ownership and frozen experiment evidence

Quinton confirmed there is no newer Claude work and requested inclusion of the accepted handback.
All 30 P3 file hashes match revision 2, and the handback itself matches its recorded accepted hash.
No retrieval source, test or planning file was edited during this review. Publishing the P2 planning
records preserves their stated draft/provisional status; it does not freeze the seed set, approve
the whole selection policy, sign acquisition, or dispatch another Claude phase.

All **142 current D-335 producing/test source pins match** the recorded control-preservation pins.
The independent D-335 control manifest matches SHA-256
`f7873871de89ddcee42c4be2776a4328192fb289dcabcdc625347016ea431458`; all 200 listed member sizes/hashes
also match. Including the manifest gives the already recorded 201 protected files. This review
verifies small preserved control bytes; it does not repeat the trained-model restore or original
source reads. The current retrospective/navigation additions are later documentation than that
sealed snapshot and are not silently inserted into it.

The local approved source-document hashes still match:

- Proposal v3.8: `00546c805f0f49df2bf11cf452dc29171ede49e6931f23f5186562e39e613612`.
- Appendix v3.1: `6c26f2ae2652c32c0fa444cc10bc608ae4a81aab5c7970c294ce4f031f2b64e3`.

D-335 remains the latest experiment decision. Both CAP-EXP-014 requests remain consumed; its
terminal48 result, membership, holds, source grants and fixed backup ceiling are unchanged. No
production Python, test assertion, schema, environment, dependency or scientific result was changed.

## Verification and fresh-checkout finding

The workspace checker passed at the authoritative root. Candidate Python parses (310 files), JSON
loads (53 files before adding the review manifest), and local imports resolve within tracked HEAD
plus the proposal. `git diff --check` passes. Existing two-space Markdown hard breaks remain; one
single trailing space on unchanged historical experiment line1185 is preserved rather than rewritten.

The exact native suite command was:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

- First attempt under the tool sandbox: 2,931 passed, two failed on denied `/bin/ps` calls,
  two existing upstream warnings, 121.78s. The failed log is retained; no assertion was relaxed.
- Native execution with the monitor available: **2,933 passed**, the same two torch.jit warnings,
  125.85s. This uses the populated local workspace and includes retained numeric metadata.
- Temporary export of tracked HEAD plus proposed files, without `.git`, local outputs or source
  arrays: collection stops at `tests/test_audit_assessment_link.py:9` because it reads ignored
  `outputs/splits/train.txt` at import time. 2,908 other tests collect; this is not a full green
  fresh-checkout result.
- Two targeted exported-tree regressions also fail on missing retained CAP-EXP-013/baseline JSON.
  Additional static review found ignored metadata dependencies in the cache-qualification tests
  and short/v5 fixture builders. The direct-file/package inventory is retained locally; it is a
  bounded dependency review, not an exhaustive runtime capture.

This portability defect matters: another checkout or a future CI worker cannot reproduce the
unmarked fast suite using only Git and the documented dependencies. It does not invalidate the
recorded native CAP-EXP-014 evidence. Do not report this checkpoint as a clean-clone verification,
full G0 closure, release qualification or complete data/evidence backup.

Recommend a bounded follow-up separating committed test-owned synthetic fixtures from explicitly
selected retained-real regression evidence. Preserve all existing role/refusal/coverage checks and
the original experiment snapshots. Then run both the ordinary suite without ignored evidence and
the selected evidence regressions with their original pins. Do not solve the problem by blanket
staging of outputs, silently skipping tests, weakening assertions, or editing frozen historical
manifests. R-01 in the remote queue names the initial scope; fixture conversion is not implemented.

Five candidate Markdown file links resolve to existing intentionally ignored experiment evidence.
They will remain local-only references in a public clone: the CAP-EXP-007/008/010 inspection records,
the CAP-EXP-008 failure record and the CAP-EXP-012 trajectory figure. Other candidate relative file
links resolve against the proposal plus HEAD. The published result summaries retain the relevant
findings, but Git does not contain every linked original evidence file.

## Changes made by this review

1. `.gitignore`: narrow local launch/storage approval exclusions; all four files verified ignored.
2. `AGENTS.md` and `CURRENT-CHECKPOINT.md`: short pointers to this review and the proposed remote
   queue, preserving the current scientific state and all historical prose.
3. This review, the exact JSON manifest and the weekend/remote planning document.

Local logs, initial/final inventories, dependency findings, exact byte copies and a comparison patch
are under `outputs/prowl/GIT-CHECKPOINT-REVIEW-20261003/`; temporary checks are under
`/private/tmp/prowl-git-review-20261003/`. The export is a file snapshot, not another clone or Git
worktree. These same-disk copies are local review evidence, not an independent backup. No external
backup directory, cap increase or deletion occurred. The existing backup-root ceiling remains
18,318,645,873B; its last recorded free allowance is 976,721,237B, not a new capacity measurement.

## Decision and follow-through

Recommend reviewing the fixture-portability repair packet next, then refreshing this proposal
before approval of a local commit and a separate public push. A preservation-only commit can also
be explicitly chosen with the defect disclosed; it must not be labelled portable or release-ready.

Before any approved commit: revalidate HEAD, the live index, every proposed hash/mode, the manifest
bytes and exclusions; inspect any drift. Stage only exact listed paths. A changed or completed
follow-up task requires a newly reviewed manifest. No `git add .`, blanket directory staging,
force-adding ignored evidence, revert, cleanup or history rewrite is authorized by this review.

Before any approved push: compare the remote branch with the proposed local history, reconcile
movement without force, then verify the resulting remote commit. Public visibility was checked;
the remote branch tip was not fetched or assumed equal to local HEAD. Record actual commit/push
identities only after the authorized actions occur.
