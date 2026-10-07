# Commit and publication practice

Quinton requested this practice on October 6, 2026: commit after important completed work,
preserve today's work in multiple commits and keep GitHub activity visible to the instructor.
This supersedes earlier no-commit guidance for reviewed, completed work within an approved scope.
It does not authorize new development, scientific execution or changes owned by another lane.

1. Finish the approved deliverable and its appropriate checks. Keep failed attempts and open gates
   in the handback. A commit is a preservation point, not scientific acceptance.
2. Review the exact file list and diff. Include the implementation, meaningful tests, contract and
   handback together when they form one deliverable. Keep unrelated and Claude-owned changes out.
3. Stage explicit paths and verify staged blobs against reviewed bytes. Exclude datasets, model
   weights, patient arrays, local runtime evidence, secrets and executable machine-specific approvals.
4. Make a truthful commit for each meaningful completed unit. Use actual dates; do not backdate,
   manufacture activity or split trivial changes to increase the count. Do not amend shared history.
5. Verify the commit and remaining worktree. Report its SHA, scope, evidence and any pending files.
6. Before publication, verify the destination and the complete outgoing history, including older
   local commits. Use a normal fast-forward push under the agreed publication scope; no force push.
   If the destination/history changes materially or access review refuses, retain the local commits
   and explain the concrete unresolved issue. Local commits alone are not visible on GitHub.
7. Update and read back the existing Trello card at meaningful completion. Record human active time
   separately; unattended agent/test/training runtime does not become credited hours or commit work.

The authoritative checkout's historical JHU-panTS origin URL was verified through GitHub on
October 6 to resolve to the renamed **QuinnEvans34/PROWL**, repository ID1284559550, public/main.
No alternate repository or new remote is implied. This session's reviewed publication scope and
actual outcome belong in [the checkpoint handback](WEEK-01-COMMIT-HANDBACK-2026-10-06.md).

At an idle heartbeat, do not rerun checks or create cosmetic changes to generate commits.
The existing hourly schedule still ends Sunday October11, 21:00 America/Denver.
