# Week 6 Trello rollover — November 9

Quinton explicitly requested that Week5 retain only Done, with current work in
Week6. Updated and read back the [board](https://trello.com/b/vac4k8Po/prowl-quinton-evans-capstone).

| List | Verified cards | Meaning |
| --- | ---: | --- |
| Week 6 — To Do | 12 | Proposal work, dependencies and explicit carryovers |
| Week 6 — In Progress | 2 | Existing STU-Net continuation and current reviewer regressions |
| Week 6 Done — Nov 9–15 | 1 | Today's verified reporting/demo preparation |
| Week 5 Done — Nov 2–8 | 7 | Original completed card IDs/statuses preserved |

The old Week5 To Do/In Progress lists were **renamed and reused** as Week6 lists,
so no cards or history were deleted. Their ten unfinished cards were renamed and
re-scoped on the same card IDs; all remain incomplete. W06-01/02 were reused from
Backlog. Three new, distinct cards cover model postprocessing, this week's
closeout and today's delivered work. Week5 Done was renamed for consistency;
its seven cards were not moved or newly completed. Older completed lists and
future Week7–10 Backlog commitments are preserved.

Original titles, full descriptions, list identities and due dates are retained in
the [adjacent JSON](WEEK-06-TRELLO-ROLLOVER-20261109.json), alongside the new mapping
and verified counts. Earlier comments/checklists remain on their original cards.
Revised due dates are **planning targets** in America/Denver, not changes to a
scientific wall-time cap, safety gate or promised meeting appointment.

## Current cards

| Card | Work | Status |
| --- | --- | --- |
| [W06-01](https://trello.com/c/p99kSjSv) | Controlled model comparison; G4 dependency retained | To Do |
| [W06-02](https://trello.com/c/zDFlThwi) | Retrieval and grounded-answer quality | To Do |
| [W06-03](https://trello.com/c/AypxMvB4) | Autonomous baseline; previously W05-01 | To Do |
| [W06-04](https://trello.com/c/Z9QSh78P) | Production-stage integration/recovery; previously W05-06/W04-01 | To Do |
| [W06-05](https://trello.com/c/jXIcbELc) | Source units/localizer/model bindings; previously W05-05 | To Do |
| [W06-06](https://trello.com/c/nI7oktAT) | Portable numerical qualification; previously W05-09 | To Do |
| [W06-07](https://trello.com/c/natlITz0) | Remaining matched-KD spatial assessment; compute already complete | To Do |
| [W06-08](https://trello.com/c/KPvynqav) | Reviewer flow and assistant regressions | In Progress |
| [W06-09](https://trello.com/c/WD6xJcnB) | Confirm/preliminary aunt walkthrough on November14 | To Do |
| [W06-10](https://trello.com/c/uPkdgBxK) | Pretrained provenance/evaluation eligibility | To Do |
| [W06-11](https://trello.com/c/uQpn9fze) | Existing corrected STU-Net continuation/final closeout | In Progress |
| [W06-12](https://trello.com/c/nl7XeVHH) | Week5 active-hours/submission confirmation carryover | To Do |
| [W06-13](https://trello.com/c/OecOcqRQ) | Fixed5mm paired evaluation on the completed selected model | To Do |
| [W06-14](https://trello.com/c/QxycSJlp) | Week6 evidence/hours/Week7 handoff | To Do |
| [W06-15](https://trello.com/c/N6RbR7lm) | Verified Training refresh and degree-chair preparation | Done |

The resource dashboard card now points to the [Week6 plan](WEEK-06-WORK-PLAN.md).
To Do is ordered with baseline and production integration first, alongside the
independent retrieval-quality work while Lenovo trains. Twelve tasks are not
twelve newly authorized experiments: several are existing baseline dependencies
or administrative closure, and the GPU tasks retain their admission conditions.

## Verification and boundaries

Read back every open board card and all lists after the mutations. Checked:

- Only one Week5 list exists, and it is Done; no Week5 To Do/In Progress remains.
- All ten carryover IDs remain open in the intended Week6 list with current scope
  and planning date. No Week6-numbered card remains in Backlog.
- W06-01/02 retain their original card IDs and November15 deadlines/dependencies.
- The three new cards exist once; only delivered W06-15 is marked complete.
- Week5's seven completed IDs and completion flags exactly match the pre-rollover
  read. No incomplete scientific/quality gate was marked complete for appearance.

Trello returned one rate-limit response; waited for the stated retry window and
continued from the recorded successful mutations, without duplicating cards.
The original failed call did not imply training failure or justify any restart.

No training, inference, source-pin edit, monitor change, external outreach or new
scientific authorization occurred. The G3/G4/G5/G6/G7 acceptance requirements,
unknown provenance, seven baseline failures and human-hour confirmation remain
visible. Code tests are not needed for this planning-only change; board readback
and repository record verification are the relevant checks.
