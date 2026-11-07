# Stakeholder validation

**Status:** Fallback selected; preliminary walkthrough moved to November14; session not yet conducted
**Owner:** Quinton Evans (outreach, scheduling, participant confirmation, and change approval)  
**Target weeks:** 1 and 7  
**Depends on:** Plan 08 wireflow and representative fixtures for the session, not for outreach  
**Last reviewed:** 2026-11-07; Quinton deferred this weekend's showcase to Saturday, November14

## Outcome

A structured stakeholder session will test whether PROWL's review workflow, measurements, evidence,
warnings, and accept/edit/reject states make sense to the intended role. Findings will be captured as
evidence, prioritized against the approved scope and remaining schedule, and translated into bounded
changes rather than informal feature requests.

## November 7 schedule change

Quinton cannot showcase the application this week and moved the preliminary
walkthrough to **Saturday, November 14, 2026 (America/Denver)**. SV-P01 remains
his industry-experienced aunt/fallback. Exact time and specific role are still
unconfirmed. This supersedes the tentative November7 date in the historical
preparation entries below; the existing script and fixtures remain useful.
No session, participant feedback, outreach message or clinical validation has
occurred. The main Week7 acceptance requirement stays open.

Before November14, finish the saved scan/reviewer and conversation regression
checks, verify the presentation against the current build, and record any actual
limitations. Quinton still owns scheduling and participant permissions.

The [November7 engineering check](../testing/REVIEWER-FLOW-20261107.md) now verifies
actual isolated browser save/reopen/revise across a backend restart, exact receipt
content/identity and unchanged original package bytes.164UI and38backend tests
pass. Repaired acknowledgment/history validation and the direct Node loader;
no participant feedback, new model generation or live contour assessment occurred.
Before the session, current viewer presentation and any live answer behavior still
need a role-appropriate check; this engineering result does not close G7.

## Approved operating approach

**September 20 update:** Quinton has contacted a radiologist and has not received a reply.
He owns outreach and does not need agent assistance finding a stakeholder. Defer further session
preparation until he confirms a participant or requests help. At that point, tailor specific
questions, things to demonstrate, and feedback priorities to the participant's expertise and the
then-current prototype. The questions/tasks below are provisional reference material, not a frozen
meeting agenda; preserve them without expanding them now. Actual feedback may lead to approved
plan or implementation changes. This deferral does not block other development or mark stakeholder
validation complete; the existing Week 5 fallback checkpoint and Week 7 review target remain.

Keep the outreach status, session script, observation record, and change decisions in this one living
document. No separate stakeholder software or expanded documentation package is needed. Quinton
continues outreach while data, model, retrieval, and initial UI development proceed under their own
plans. A scheduled radiologist meeting is not their startup prerequisite.

Feedback can affect terminology, displayed context, and interaction code later; only the bounded
Quinton-approved revision list enters Plan 08. The actual session or documented role-appropriate
fallback remains a later G7 deliverable. Approval of this plan does not mean that review occurred.

## Current outreach status

| Item | Current state | Next action / owner |
|---|---|---|
| Available expert | Quinton reports an expert he can talk to; actual role/experience and participation not yet recorded | Quinton confirms role, relevant experience, and availability |
| Preferred radiologist | Contacted by Quinton; no reply or confirmed appointment as of September 20 | Quinton owns follow-up; agent preparation deferred until participant confirmation or request |
| Scheduling checkpoint | Confirm participant/session by Week 5, or activate a suitable fallback | Quinton records the outcome here |
| Main walkthrough | Target Week 7, proposed duration 30–45 minutes | Confirm date and session format when available |
| Early conversation | Optional, if useful and convenient | Log preliminary feedback separately from the working-prototype session |
| Session findings | None recorded yet | Append observations after the session |

Use role labels or participant codes in committed notes. Keep contact details, scheduling messages,
recordings, and sensitive raw notes outside Git under the approved local storage boundary. This plan
does not authorize contacting participants, sending files, or making recordings on Quinton's behalf.

## Scope

- Participant/fallback selection, protocol, representative tasks, structured observation, finding
  prioritization, and bounded Week 7 revisions.

## Non-goals

- Clinical validation, diagnostic accuracy adjudication, or formal human-subjects research.
- Treating one proxy participant as proof of broad clinical usability.
- Automatically implementing every requested feature.

## Intended participants

- Preferred: radiologist or radiology clinician familiar with CT review.
- Fallback: the available expert if their role/experience fits the tasks, or a coordinator/annotator
  or other appropriate proxy; confirm the actual role rather than assuming a clinical credential.
- Optional supplementary participant: imaging annotator or technically informed clinician.

Feedback is interpreted in light of the participant's actual role; proxy feedback is not presented
as radiologist validation. The earlier draft named a diagnostic care coordinator as confirmed; the
September 18 update supersedes that assumption with Quinton's current report of an available expert
whose role is still to be recorded.

## Session questions

- Can the reviewer distinguish model prediction, reference annotation, and literature evidence?
- Is the ordering score understandable and appropriately uncertain?
- Are volume, diameter, location, and source/version details useful or distracting?
- What does accept/edit/reject mean in a realistic workflow?
- Is `edit requested` sufficient without an in-browser contour editor for this prototype?
- Can the reviewer find the evidence source and recognize insufficient evidence?
- Which false-positive/false-negative presentation best supports review?
- Does any wording imply diagnosis or more certainty than the system has?
- What single change would most reduce review burden?

## Representative task set

1. Review a strong positive case and record a decision.
2. Review a false-positive case and explain what signals helped reject it.
3. Review a small/subtle lesion or localization failure.
4. Ask a question with relevant literature and inspect citations.
5. Ask an unanswerable or out-of-scope question and interpret the refusal.
6. Reopen the case and verify the prior review decision/version.

## Lightweight session script

Before the meeting, select permitted de-identified or synthetic representative packages. Record
case-package, prediction, evidence, UI/code, and review-schema versions. Use development/demo cases,
not protected held-out cases/questions for design feedback. Label simulated outputs explicitly and
do not use them to claim that real inference or persistence works.

1. **Opening, about 5 minutes:** explain research/annotation-assist scope, known limitations, and
   that this evaluates the interface/workflow rather than clinical accuracy. Confirm willingness to
   participate and the note-taking/quotation approach. Do not record audio/video without explicit
   permission. Let the participant decline a question or stop.
2. **Tasks, about 20–30 minutes:** ask the participant to work through the representative task set
   and explain what they think is happening. Observe first rather than coaching toward a positive
   response. Record whether each task was completed unaided, with assistance, failed, or not tried.
   If the role is not qualified for contour assessment, ask about workflow/comprehension instead;
   do not ask them to certify medical correctness.
3. **Debrief, about 5–10 minutes:** ask what was confusing, what seemed overstated, which missing
   context mattered, and the one change that would help most. Recap the main findings and confirm
   that the summary reflects their intended meaning.

## Living session and findings record

Append a new dated section for each conversation/session; preserve earlier notes and add corrections
with dates rather than rewriting the original observation. Update outreach when its state changes.

```markdown
### Session SV-001 — date / planned or completed
- Participant code, actual role, relevant experience, and role limitations:
- Format, permission for notes/quotes/recording, and local raw-note reference if applicable:
- Session type: preliminary conversation / working-prototype walkthrough / asynchronous fallback:
- UI/code and exact case-package/prediction/evidence/review versions; simulated boundaries:
- Tasks attempted, unaided/assisted/failed/not-tried outcomes, and assistance provided:
- Observed behavior and participant feedback (distinguish quotes, paraphrases, and interpretation):
- What was not evaluated; role/scope limitations:
- Finding IDs and next actions:
```

For each finding, record `SVF-NNN`, source session/task, observed issue, severity, proposed response,
scope/test/schedule impact, Quinton's disposition (`implement`, `investigate`, or `defer`), owner,
and verification evidence if implemented. A compliment or feature suggestion is not evidence that
a task passed. Missing tasks remain visible. Exact quotes require permission.

## Data collection

- Task completion and notable hesitation/errors.
- Participant role and relevant experience.
- Structured ratings only where useful; qualitative reasoning is primary.
- Exact high-priority quotes only with permission.
- Findings categorized as blocker, important, useful, or future.
- Each proposed change receives scope, risk, test, and schedule impact.

## Invariants

- No participant sees identifiable patient data.
- Session is usability/workflow feedback, not clinical validation.
- Prototype limitations are disclosed before interpretation.
- Feedback does not override scientific correctness or non-diagnostic boundaries.
- Week 7 changes cannot consume Weeks 9–10 as feature work.

## Test matrix

| Scenario | Evidence |
|---|---|
| Participant completes core review | Task notes and outcome |
| False-positive interpretation | Observed reasoning and terminology issues |
| Cited evidence and refusal | Comprehension and trust-boundary notes |
| Saved review reopened | Participant can identify prior action/version |
| Diagnostic overclaim probe | Wording changes or explicit pass |
| Conflicting/optional feedback | Prioritization rationale and deferral record |

## Failure modes and fallback

- Radiologist unavailable: use coordinator/annotator proxy, asynchronous walkthrough, and record the
  validation limitation.
- No suitable participant by the checkpoint: record the outreach limitation and discuss the
  fallback with the instructor; do not mark the stakeholder requirement complete from planning alone.
- Participant requests clinical features outside scope: capture as future work.
- Prototype unstable: run against fixed representative packages and disclose simulated boundaries.
- Feedback conflicts: prioritize safety/scientific clarity, frequency, user role, and approved scope.

## Planning readiness versus session completion

- [x] Quinton approved the lightweight living record, outreach ownership, session approach, and
  non-blocking development boundary on 2026-09-18.
- [x] Core questions, task script, findings fields, and bounded change process are documented.
- [ ] Session-specific participants, permissions, fixture identities, and working prototype are ready.

The first two items let planning move to Plan 12. They are not evidence for the completion gate below.

## Acceptance gate

- [ ] Participant role and session date are confirmed by Week 5 or fallback is activated.
- [ ] Script, consent/recording approach, tasks, and fixtures are prepared.
- [ ] Session covers success, failure, false positive, evidence, refusal, and saved review.
- [ ] Findings and participant-role limitations are documented.
- [ ] Changes are prioritized and mapped to tests/schedule.
- [ ] Quinton approves the Week 7 revision list before implementation.

## Artifacts

- This document: living protocol, outreach state, session summaries, findings, and approved/declined changes.
- Linked permitted test/before-and-after evidence for implemented high-priority changes.
- Private raw notes/recordings only if needed and permitted; never copied into Git or the release.

## Handoff

Plan 08 implements only the approved Week 7 list. Plan 12 cites the session accurately and records
unresolved limitations.


## November 3 fallback selection and tentative weekend walkthrough

Quinton selected his aunt, an industry-experienced contact and previously identified
fallback. Participant code SV-P01; specific job title/clinical credentials have not
been recorded. Tentative timing is Saturday, November7,2026 ("Saturday or something"),
not a confirmed appointment/time. Quinton owns scheduling. This activates preparation
for the fallback and supersedes the September20 preparation deferral; the original
outreach history stays above. No contact or invitation sent by the agent.

Plan a30–45minute preliminary usability/workflow walkthrough using the existing
six tasks. Unless relevant clinical qualifications are established at the session,
ask about comprehension, navigation, trust, source inspection and decision-saving;
do not ask her to certify contour accuracy or interpret a diagnosis. An early
Week5 session can inform the Week7 plan but is not automatically its completed gate.

Before Saturday: select the verified2028 development package plus retained static
miss/false-positive review images; distinguish the interactive package from images.
Freeze code/package/source identities after import checks. The assistant requires
a separately coordinated GPU window; prepare saved answers and clearly label them
if live generation is unavailable. Explain fast-preview answer limitations.

Record participation/note-taking permission, actual role, tasks attempted and
unaided/assisted/failed/not-tried outcomes in the existing living-session template.
Ask which step was hardest to understand, whether mask measurements and limitations
were clear, whether she could inspect a citation and recover a saved decision, and
what one change would improve the workflow most. Preserve feedback as observations;
Quinton chooses any resulting code changes. No session results or acceptance claimed.

## November 5 Saturday preparation and engineering checks

Prepared for the tentative SaturdayNovember7 preliminary session with SV-P01.
Exact time, actual job role and participation/note-taking permission remain for
Quinton to confirm. No invitation, recording or participant feedback was created.
This is a ready task script with bounded engineering evidence, not a completed
live walkthrough or G7 acceptance.

Use the existing application and living findings template above. Start by saying:
"I would like feedback on whether the workflow and explanations make sense.
These are research model outputs, not a diagnosis. Some answers may be replayed
from saved evidence; I will say when that is the case."

| Task / approximate time | What to show or ask | Record without coaching |
| --- | --- | --- |
| Orient,3minutes | Ask what she thinks the scan, colored predictions and reference/source labels mean. State the limitations and confirm her role. | Interpretation, unclear labels, assistance provided. |
| Saved scan,5minutes | Open `/saved?review=b671bd4453db6c91d842d948c95eeac351df76902480d54b5389a2a174efd2f5`. This is exposed-development case2028 with a CT-only prediction, not a new inference. Ask her to find provenance and measurement limitations. | Whether prediction vs annotation and mask volume vs validated anatomical measurement are distinguishable. |
| Failure examples,5minutes | Use the private seven-case gallery, especially a missed component and8711spillover/6880false-positive example. Label static images and explain representative-slice limits. | Can she recognize why the output needs review? Do not ask a proxy to certify medical correctness. |
| Conversation,7minutes | Use the boundary/function questions and the evidence-gap stiffness question from the saved packet. Inspect a citation, edit a prior question, cancel one and send a replacement. Explicitly identify saved playback/fixtures; live generation waits for the GPU to be free. | Does the answer address the question? Is the evidence link understandable? Does the cancelled answer stay out of the replacement conversation? |
| Save and reopen,5minutes | On an explicitly designated session review, save a decision with its reason, reopen the exact prediction/revision, then revise it. Keep engineering records separate from participant records. | Whether the saved version, current draft and previous decision are clear; actual task outcome. |
| Debrief,5minutes | Ask which step was most confusing, what appeared too certain, and the single change that would help most. | Quote only with permission; prioritize actual observed problems in the existing SVF template. |

### Frozen fixtures and current check evidence

- Saved native manifest SHA256
  `b671bd4453db6c91d842d948c95eeac351df76902480d54b5389a2a174efd2f5`;
  local package `outputs/prowl/week05-review-transfer-20261103-01/native-view`.
  November5 CPU browser loader verified file hashes/native geometry and released
  its arrays without rendering. Predicted-mask volumes76.360628mL pancreas-including-
  lesion and15.170559mL lesion match the retained check. These are model mask volumes;
  anatomical completeness and measurement accuracy remain unverified.
- Conversation comparison packet remains
  `outputs/prowl/assistant-review-20261102-01/inputs.json`, SHA256
  `fea15059496f2341703134f905c178f03e5492665aab4efabf6cbe6af0411280`, with the same five
  questions and saved evidence. Current baseline snapshots are the three retained
  October31 fast-preview responses. Do not imply that the two older-model failures
  are current answers, or that saved response timings are a new live benchmark.
  Known relevance/jargon/completeness defects remain in the
  [saved-answer review](../retrieval/ASSISTANT-OFFLINE-REVIEW-2026-11-02.md).
- Node24.21.0:124tests across nine focused suites passed November5, including the
  explicit private-package opt-in test. Coverage includes both conversation variants,
  citation links, edit/resend identities, cancellation/late-answer isolation,
  review revisions, incorrect prediction/revision bindings and history reopening.
  Synthetic answers and mocked transport are engineering checks, not model accuracy.
- Fresh actual-package ASGI HTTP exercise retained under
  `outputs/prowl/testing/week05-walkthrough-20261105-01/readiness.json`.
  Engineering-only revision1/idempotent retry/restart/reopen/revision2 passed;
  stale write rejected409; all five retained file hashes equal the originals.
  No network listener, model call, live GPU viewer or production review write.
  The real application package still has no engineering decision added to it.

Repeat the bounded UI check from `ui/` with the verified runtime and explicit
`PROWL_PHYSICAL_PACKAGE` pointing to that private package:

```sh
/Users/quintonevans/.nvm/versions/node/v24.21.0/bin/node node_modules/vitest/vitest.mjs run \
  tests/LiteratureSearchPanel.test.jsx tests/GeneralExtract.test.jsx \
  tests/reviewDecision.test.jsx tests/reviewLiteratureAttachments.test.jsx \
  tests/reviewNavigation.test.jsx tests/savedPrediction.test.jsx \
  tests/savedReviewList.test.jsx tests/reviewState.test.js tests/physicalPackageLocal.test.js
```

The opt-in scan check skips when its environment variable is absent. Normal CI
does not discover private scans. Before a live session, separately confirm GPU
availability, actual viewer presentation, services and live answer behavior if used.
Do not stop KD or start a model automatically for this preparation. During the
session record unaided/assisted/failed/not-tried, actual role and limitations in
SV-001; all feedback/outcome fields remain empty until the participant acts.
