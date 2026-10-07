# Trello structure cleanup — October 6, 2026

Quinton explicitly approved reorganizing the existing board to the instructor's Resources,
Backlog, To-Do, In-Progress, Done and weekly-completion structure, adding five reference cards
and placing the inactive drive-blocked N4 task in To-Do with a named Blocked label. Preserve all
existing cards and their contents. This is board organization, not scientific dispatch.

Canonical board: https://trello.com/b/vac4k8Po/prowl-quinton-evans-capstone

## Finished and verified

| List, in board order | Cards | Role |
|---|---:|---|
| Resources | 5 | Approved proposal, GitHub, selected research sources, master/current-week plan, hours log |
| Backlog | 12 | Existing future W02–W10 milestone cards |
| To-Do | 5 | W01-01, W01-04/N4, COURSE-01, COURSE-02, W01-05 awaiting work/input/dependency |
| In-Progress | 0 | Only work actively underway belongs here |
| Done | 11 | Existing current-week completed cards |
| Pre-course Complete | 4 | Existing PRE-01–PRE-04 history, separate from Week 1 |
| Week 1 Complete | 0 | Reserved for the weekly close; current Done cards stay in Done |

Created four lists and renamed the original In Progress list to In-Progress without replacing it.
Moved exactly 21 existing cards: 12 future milestones, five inactive current-week tasks and four
pre-course completions. The original To-Do, In-Progress and Done list identities are retained.
No card was deleted, archived, replaced or newly marked complete. No current assignment submission,
presentation or N4 qualification was claimed.

Readback verified all 32 original card IDs remain, with no changes in returned fields other than
list/position/activity metadata. Titles, descriptions, due dates, completion flags, labels and
returned checklist/member/comment fields matched the pre-cleanup snapshot. Those nested collections
were returned empty by the connector; this is not an independent export of Trello's entire history.
Only move operations were used on existing cards. The five new references were each read back with
their exact descriptions. Total: 37 cards; board order and all list counts verified.

Reference cards:

- [Approved proposal](https://trello.com/c/iPaKeSzL)
- [GitHub repository](https://trello.com/c/0amd68GC)
- [PanTS, nnU-Net and RAG](https://trello.com/c/VoSaLr7k)
- [Master plan and current week](https://trello.com/c/cWuIVLyG)
- [Human working-hours log](https://trello.com/c/gBaviwXG)

The approved proposal is v3.8 and appendix v3.1, following the approved-source catalog. Resource
cards distinguish local repository paths from published content; no Git publication occurred.

## Remaining browser dependency

N4 is in To-Do with its existing blocked title, dependency, owner and restart condition intact.
Creating a new named Blocked label is not exposed by the connected Trello tools. The Codex browser
is signed out; Quinton has been asked to sign in. Do not report that the label exists before readback.
The retrieval owner retains N4 execution; moving the card grants no execution authority.

Exact restart: after Trello browser sign-in, create a new label named **Blocked**, attach it only to
[W01-04/N4](https://trello.com/c/XcloMmhR), retain its existing purple label, and verify the card remains
in To-Do with all other fields preserved. Then record the completed label readback here. Do not repeat
the moves or create duplicate Resources cards.

## Continuing protocol

The [weekly development protocol](../weeks/WEEK-01-DEVELOPMENT-FOCUS-2026-10-06.md) now reflects
the approved structure. Prepared assignments awaiting Quinton's confirmation sit in To-Do when
inactive. At weekly close, move that week's Done cards to Week N Complete; do not perform the Week 1
close on Tuesday. Keep future milestones in Backlog until concrete current-week work is selected.

Two Trello write attempts were rate-limited. Live readback before resuming confirmed their outcomes;
all required moves and five creations then completed without duplicates. No tests were needed for
this board/documentation change. Human time for this session is unknown and was not added to the
hours total. Existing development T01–T08 remain complete; SUP-02A remains a proposal.
