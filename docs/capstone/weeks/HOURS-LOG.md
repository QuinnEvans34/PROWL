# Capstone working-hours log

Quinton requested weekly human working-hour tracking on October 6, 2026.
Weeks run Monday through Sunday in America/Denver. Week 1 is October 5–11.
Pre-course work before October 5 belongs in a separate retrospective, not the Week 1 total.

## Recording rules

- Count Quinton's focused project planning, reading, coding, result review,
  testing supervision and active remote check-ins. Combine short phone sessions when useful.
- Exclude the Capstone Setup submission, Resources assignment and short What/Why/How pitch
  preparation from project hours, following the agreed October 7 reporting scope.
- Record class/meeting time separately so the instructor's counting rule can be applied explicitly.
- Exclude unattended agent execution, training, downloads and waiting. Record machine duration
  separately when it matters for resource planning; it is not human study time.
- Count simultaneous activities once. Do not sum several chats' overlapping wall-clock spans.
- Label entries as timed, Quinton-estimated or provisional reconstruction. Round estimates to
  quarter-hours, preserve corrections and avoid claiming minute-level precision.
- At each session handback, record the task, evidence and human time supplied by Quinton. When time
  is unknown, say so. At the weekly review, confirm the total and retain the estimation basis.
- Starting October 7, record a user-supplied clock-in at the start of a work session and a
  clock-out when Quinton finishes. Record pauses/resumptions for breaks, schoolwork and other
  activities. At close, subtract excluded time before recording active project hours. An open
  clock interval is not proof of continuous participation; missing exclusions keep the total pending.
- Agent execution and scheduled wake-ups never clock Quinton in or out. A session does not
  automatically end at the automation cutoff; use Quinton's actual finish time.

## Project goals

### G1 — Develop and test the pancreas and lesion segmentation training workflow

Implement and test input preparation, model initialization, training, prediction export and
checkpoint recovery. Document failures and resolve issues needed for reproducible training.

Completion means the coordinated workflow passes its bounded checks and demonstrates independent
checkpoint recovery. This goal remains partly done: the invented-data producer completed, but
its independent next-update recovery failed. Work on that unresolved issue still contributes
to the goal; the rehearsal does not establish actual-data model quality.

### G2 — Review experiment results and plan the next model improvements

Analyze previous training results, identify data and annotation gaps, and define controlled
experiments with clear evaluation criteria and resource limits.

Completion means the experiment review and next training/data-validation plan are documented
with explicit overlap, coverage, excess-foreground and resource criteria. Planning hours count
without implying that the proposed experiments or dataset expansion have been executed.

### G3 — Complete the Week 1 training architecture and launch long experiments

Finish the new training pipeline so it can support long runs and checkpoint recovery.

**October 8 work summary:** Worked on the new training pipeline, resumed the long SuPreM run,
and prepared the Lenovo training handoff, including dataset and checkpoint transfer requirements.
Reviewed remaining Week 1 work and planned the next development steps.

This goal records the implementation and launch focus, not a claim that every Week 1 item is
complete. Its hours overlap G1/G2 and must be counted once. October 8 active time remains pending
an end time and exclusions; no training runtime is credited.

## Week 1 — October 5–11, 2026

### Current project-hour entries

Quinton supplied these estimates on October 7 and approved the daily work descriptions below.
They are personal estimates of active project time, not timer measurements or agent runtime.
The same hours support both goals; they are counted once rather than allocated twice.

| Date | Goals | Work completed / reviewed | Human hours | Basis |
|---|---|---|---:|---|
| Monday, Oct 5 | G1, G2 | Reviewed project progress and technical requirements, organized development priorities, and planned the segmentation training workflow. | 4 | Quinton estimate |
| Tuesday, Oct 6 | G1, G2 | Reviewed segmentation experiments, worked through training-readiness issues, evaluated input-adapter and checkpoint tests, and investigated dataset qualification gaps. | 5–6 | Quinton estimate; precise portal value not selected |

**Monday–Tuesday estimated subtotal: 9–10 hours.** Wednesday is clocked out; its net active
hours remain pending reconciliation of other excluded time. Thursday has an open session below.
Class/instructor meetings remain separate and unmeasured. These entries have not been submitted
to Project Peek by this chat.

### Closed clock interval — Wednesday, October 7

Quinton supplied a retrospective clock-in of **9:00 a.m. America/Denver** and, on October 8,
reported finishing at approximately **8:15 p.m. on October 7**. These are user-reported times;
they do not credit the entire school-day background interval as active work or confirm the earlier
provisional 3–4-hour estimate.

| Date | Goals | Clock-in | Clock-out | Breaks / excluded time | Net active hours | Status |
|---|---|---|---|---|---|---|
| Wednesday, Oct 7, 2026 | G1, G2 | 9:00 a.m. MDT (UTC−06:00) | Approximately 8:15 p.m. MDT | Confirmed pause 3:15–approximately 4:27 p.m.; other schoolwork, breaks, assignments, unattended intervals and overlap pending | Pending other exclusions | Clocked out; finish reported October 8 |

Session events (finish supplied retrospectively on October 8):

| Event | America/Denver time | Basis |
|---|---|---|
| Initial clock-in | 9:00 a.m. MDT | Quinton's retrospective requested start |
| Pause | 3:15 p.m. MDT | Quinton: “we stopped working at 3:15” |
| Resume | Approximately 4:27 p.m. MDT | Quinton: “are back now”; time read 22:27:06 UTC and recorded to the minute |
| Final clock-out | Approximately 8:15 p.m. MDT | Quinton, October 8: “we finished working around 8:15 last night” |

Exclude the approximately **1 hour 12 minute** pause. The earlier 9:00 a.m.–3:15 p.m. window
is 6 hours 15 minutes of elapsed time, with its schoolwork/background/other exclusions still
unreconciled; it is not 6.25 credited project hours. The full clock span is approximately
11 hours 15 minutes; subtracting the known pause leaves approximately 10 hours 3 minutes
**before other exclusions**, not a credited active total. Wednesday's net hours remain pending.

Project discussion covered training readiness, review of earlier experiments, and refocusing on
long runs through the new architecture. Later agent preparation and training do not extend
Quinton's supplied 8:15 p.m. finish. The Monday–Tuesday subtotal stays unchanged until Wednesday's
net active time is confirmed.

### Open session — Thursday, October 8

| Date | Goals | Clock-in | Clock-out | Breaks / excluded time | Net active hours | Status |
|---|---|---|---|---|---|---|
| Thursday, Oct 8, 2026 — morning | G1, G2 | 8:02 a.m. MDT (UTC−06:00) | 10:00 a.m. MDT | Short-pitch assignment preparation within this interval remains excluded under the existing rule; duration not yet separated | 1h58 elapsed; net project hours pending assignment exclusion | Clocked out |
| Thursday, Oct 8, 2026 — resumed | G1, G2 | 10:57 a.m. MDT | Pending | 10:00–10:57 training-only interval excluded; record further breaks | Pending | Open |

Quinton supplied today's 8:02 a.m. start on October 8. No earlier morning check-in, transport,
overnight training or agent execution is added to this session automatically. He subsequently
reported stopping at10:00a.m. and resuming at10:57a.m. MDT. The57-minute training-only interval
is excluded. The first interval spans1h58; it includes What/Why/How assignment work, which the
existing reporting rule excludes from project hours until its duration is separated. The resumed
session begins with Week1 software-closeout planning; its finish remains open.

| Day | Estimate feedback |
|---|---|
| Monday | Use the 4-hour estimate for active project participation under the exclusions above. |
| Tuesday | Quinton's recollection supersedes the earlier assistant reconstruction. 5.5 hours is a suggested midpoint if he chooses it; it is not currently recorded as the submitted value. |

Relevant technical records: [input-adapter review](../operations/PREDICTED-ROI-ADAPTER-RESULTS-2026-10-06.md),
[training-readiness sequence](../operations/SUPREM-TRAINING-READINESS-QUEUE-2026-10-06.md),
[dataset gap inventory](../operations/VARIED-MULTICLASS-GAP-INVENTORY-2026-10-06.md) and
[controlled duration plan](../operations/SEGMENTER-DURATION-COMPARISON-PROPOSAL-2026-10-06.md).
These records substantiate project activities, not their human duration. Daily notes describe
Quinton's planning/review participation and do not credit unattended implementation as his time.

### Historical October 6 reconstruction — superseded, excluded from current subtotal

**Confirmed weekly total:** not recorded yet. Unknown time is not zero.
**Provisional Tuesday total through the evening review:** approximately **4 active human hours**,
with a **3–5 hour range**. This is a reconstruction, not a timer or Quinton-confirmed amount.
It supersedes the earlier1.25–2.75h subtotal, which covered course preparation/initial planning
only. Monday, work in other chats and class/meeting time remain unmeasured and are not added.

Basis: this chat records course/setup participation from08:00 Denver, resources09:58, slide11:54,
planning and phone reviews12:15–16:50, then home training-readiness discussion from17:21 to21:03
October6. These are contact times, not continuously active blocks. The earlier course/planning
subtotal had midpoint2h; approximately another2h is provisionally allowed for active development,
board/result reviews and evening decisions across the many short check-ins. The3–5h total range
reflects uncertain reading/preparation time and possible overlap. Agent turn durations, long gaps,
training/test runtime and heartbeats are excluded. No supplied timer/attendance evidence exists.
Quinton was asked for his active school/home windows and breaks; revise this estimate when supplied.

| Date | Activity | Human hours | Basis | Evidence / status |
|---|---|---:|---|---|
| Oct 5 | Development handoff, course start and any other work | Unknown | Awaiting Quinton's estimate | R4 handoff records an October 5 decision; it does not measure working time. |
| Oct 6 | Setup/Trello review, instructor access and submission | 0.50–1.00 | Provisional task reconstruction | Setup complete and submitted per Quinton; exact active time unmeasured. |
| Oct 6 | Resource selection and summary review | 0.25–0.75 | Provisional task reconstruction | PanTS, nnU-Net and RAG selected; review DOCX prepared. |
| Oct 6 | Slide planning and motivation revision | 0.25–0.50 | Provisional task reconstruction | What/Why/How v4 and rehearsal notes prepared. |
| Oct 6 | Development regrouping and weekly planning | 0.25–0.50 | Provisional task reconstruction | Current checkpoint/board review; weekly focus and coding packet prepared. |
| Oct 6 | Development/board/results review and evening training-readiness decisions | Approximately2.00 additional | Provisional reconstruction; not separately measured | Included in the4h working estimate above; avoid double counting. Agent execution/checking time excluded. |
| Oct 5–6 | Capstone class and instructor meeting | Unknown, separate | Awaiting Quinton | Do not infer attendance or duration from the course schedule. |
| Oct 7–11 | Remaining week | Not yet recorded | Future work | Add actual session entries rather than counting planned budgets. |

### Correction history

October8,10:57MDT: user reported10:00stop and10:57restart. Closed the8:02–10:00interval
(1h58elapsed) and excluded57minutes of unattended training. Opened the10:57session; retained
the existing short-pitch assignment exclusion instead of crediting the entire morning as project
hours. No new weekly total inferred.

October 8: recorded Quinton's approximate October 7 finish at8:15p.m. MDT and October 8 start
at8:02a.m. MDT. Closed Wednesday's clock interval, retained the known1h12pause and pending
other exclusions, and opened Thursday. No unattended runtime or new weekly total credited.

October 7, afternoon pause/resume: recorded Quinton's supplied 3:15 p.m. pause and “back now”
resumption at approximately 4:27 p.m. America/Denver. Added the known pause as excluded time;
kept final finish, other exclusions and net active hours pending. Monday/Tuesday estimates and
their 9–10-hour subtotal remain unchanged. No portal submission or continuous school-day credit.

October 7, session-clock update: at Quinton's request, opened today's session at 9:00 a.m. Denver
time. Finish and exclusions remain pending; no Wednesday hours or new weekly total were inferred.
Adopted clock-in/pause/resume/clock-out recording for future human work sessions.

October 7: Quinton estimated Monday at 4 hours and Tuesday at 5–6 hours and accepted the daily
work descriptions. Added G1/G2 and the current 9–10-hour project subtotal. The older Tuesday
4-hour/range3–5 reconstruction included assignments and is preserved in the historical section,
not added to these entries. Excluded setup, Resources and short-pitch assignment preparation.
No exact Tuesday portal value, Wednesday total or unattended runtime was inferred.

October 6: initialized the log. The provisional Tuesday range is deliberately separate from a
confirmed weekly total. No agent runtime or pre-course hours have been credited to Quinton.

October6 evening: expanded the earlier course-only subtotal to a provisional whole-day working
estimate4h/range3–5h using chat contact times and task participation. This does not confirm a
weekly total or credit uninterrupted wall-clock/agent runtime. Earlier1.25–2.75h preserved here
as the initial subtotal; Quinton may correct both allocation and total.

## Future entry template

| Date / session | Activity / Trello card | Human hours | Basis | Evidence / next step |
|---|---|---:|---|---|
| YYYY-MM-DD | Named packet | Unknown until supplied | Timed / Quinton estimate / provisional | Result or blocker |

Weekly handback: confirmed human total, remaining estimates, separate class/meeting time,
completed tasks, principal blocker and the next bounded packet.
