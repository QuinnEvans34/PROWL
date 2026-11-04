# Two-machine work handoff

This is the shared entry point for Mac and Lenovo work. Each machine publishes
its own short status file after meaningful work; Git history keeps older entries.
Detailed experiment reports and frozen receipts remain authoritative. A status
file is a timestamped handoff, not a live process monitor or launch authorization.

| Owner | Published status | Branch |
| --- | --- | --- |
| Mac chat | [MAC.md](https://github.com/QuinnEvans34/PROWL/blob/main/docs/capstone/coordination/MAC.md) | `main` |
| Lenovo chat | [LENOVO.md](https://github.com/QuinnEvans34/PROWL/blob/codex/week05-cuda-readiness/docs/capstone/coordination/LENOVO.md) | `codex/week05-cuda-readiness` |

The Lenovo link resolves after its first status publication. Its file lives on
its branch; absence from `main` does not mean there is no update. Each owner edits
only its own status. The Mac owns this guide/template. Record any future branch
change here and notify the peer before relying on a different ref.

## At the start of a work session

1. Inspect `git status --short` and the current branch. Preserve existing work.
2. Run `git fetch origin` to refresh remote refs without changing working files.
3. Read the peer's status directly from its remote ref, then inspect the cited
   commits/reports before relying on a conclusion. A pushed branch makes work
   visible; it does not mean that work has been reviewed or integrated.

Mac reads Lenovo:

```sh
git show origin/codex/week05-cuda-readiness:docs/capstone/coordination/LENOVO.md
git log --oneline main..origin/codex/week05-cuda-readiness
```

Lenovo reads Mac:

```sh
git show origin/main:docs/capstone/coordination/MAC.md
git log --oneline HEAD..origin/main
```

Both may inspect a report or commit without checkout:

```sh
git show REF:repository/relative/report.md
git show --stat COMMIT
git show COMMIT -- repository/relative/file.py
```

These commands work in zsh and PowerShell when placeholders are replaced. If
fetch fails, state the last successful peer revision/time; do not claim freshness.
Do not pull, merge, rebase, reset or switch the checkout underneath a running job.
Source integration is a separate reviewed operation when safe, or in an isolated
checkout. Never overwrite or repin a producer to make branches agree.

## At a meaningful milestone or before handing work back

- Update the owner status using [TEMPLATE.md](TEMPLATE.md): work delivered, exact
  code revisions, validation scope, active job/receipt, limitations, next action
  and the peer revision actually read. Use an observation time in UTC.
- Review `git diff` and `git diff --check`; stage only named source/tests/docs.
  Commit coherent changes and push the owner's branch. Do not pad commit counts
  with unchanged polls, timestamp-only updates or invented progress.
- Check that local HEAD equals the remote branch tip after pushing. A commit
  cannot contain its own hash: record the delivered code revision and observation
  time; the status file's enclosing Git commit identifies the publication itself.
- Tell the peer which commit/path changed and what action, if any, it needs.
  The peer fetches, reads and records that revision in its next meaningful update.
  Acknowledgments alone need not trigger another endless round of commits.
- Update existing Trello cards with the result/evidence, without marking incomplete
  acceptance work complete. Messages/Trello point to Git; do not maintain competing
  copies of the full technical log.

## Existing uncommitted work

Inventory and review it before staging. Group completed source/tests/reports into
meaningful commits, retaining failed attempts and scope limitations. Do not blanket
`git add .`: exclude CTs, masks, weights, checkpoints, SQLite databases, private
transfer codes, secrets and generated local artifacts. List any unresolved drafts
or unattributed edits in the owner status, with a reason; do not delete or silently
claim they were published. Adding unchanged bytes to Git must not change an active
producer's file contents. Any needed source repair follows a separate qualified
continuation rather than an in-place edit.

## What this system does and does not synchronize

Git shares source, tests, plans, sanitized results and evidence identities. Private
data/checkpoints and live MLflow databases stay local; transfer only through the
existing verified private handoff when needed. Keep per-machine run IDs, artifact
roots and backup identities distinct. Missing local data is not repaired by pull.

Each agent reads at session start and publishes at useful milestones. There is no
new timer, background polling or automatic merge/launch installed by this guide.
Existing KD monitoring remains separate. For urgent coordination, use the existing
authorized chat message, then record the consequential decision in Git. Current
job receipts and direct process checks supersede stale prose.

Historical context: [two-machine source handoff](../operations/TWO-MACHINE-HANDOFF-20261023.md)
and [machine register](../../../MACHINES.md). Exact current runtime settings come
from the run receipt rather than older inventory examples.
