# Original PROWL AI expert — November 18 demo review

The fixes are installed in the original PROWL app at
`/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
The existing database, local model and UI are running. The final live rehearsal
completed all twelve requests through the UI proxy without service errors.
The basic conversation and saved-measurement flows are operational. Broad
medical coverage remains incomplete; this is not a qualified general medical
expert or a guarantee of answer accuracy.

## What was wrong

- The UI displayed history but sent only the latest question. The literature gate
  therefore required a pancreatic subject in each new question.
- Dense retrieval sometimes preferred a related study over a direct answer.
  The insulin question retrieved a diabetes/volume study even though the library
  already contained an explicit beta-cell insulin statement.
- Reviewed topics could return more than five passages, but generation rejected
  them before calling the model.
- Exact citation links did not prove that the generated claim was supported.
  The first live rehearsal included incorrect scope and causal generalizations.
  A second model pass alone also missed these errors.
- The original source service was running while Docker and its database were
  stopped. Preparation previously did not check whether a running answer service
  used the current prompt and context capabilities.

## Current behavior

The candidate expert supplies the application topic and up to three recent
successful literature questions. It retains the original question and request ID
and displays the interpreted question. Earlier answers, scan IDs and measurements
never become literature evidence. New explicit topics do not inherit an older
comparison. Unknown referents and other organs require clarification. Failed,
refused or cancelled questions and study/prediction changes reset context.

Retrieval combines three lexical matches across all 1,179 verified canonical
passages with two complementary dense matches. It retains complete source
passages and their qualifications. Existing reviewed-record matches still take
precedence. No question/answer lookup table, new source download or new model
weights were introduced. The candidate uses the explicit hybrid configuration;
legacy search initialization remains available.

Generation accepts up to twenty passages while retaining the existing
16,000-character and 100-sentence bounds. A draft must bind exact quotations and
preserve numerical values, named biomedical entities and relevant source scope.
A separate local-model check assesses relevance and support, but is not treated
as a truth guarantee. A failed draft gets at most one correction using only its
originally cited source passages. The correction must stay under 65 words and
pass the same checks. All model work shares the existing 60-second deadline.
The maximum is three model calls, with no repeated correction loop.

If a checked summary is unavailable, the app can show exact selected quotations
with their bound article titles, labelled **Source wording** and **partial**.
The browser reconstructs that text from the returned source records and rejects
alterations. Unsafe, irrelevant or oversized fallbacks stay insufficient.
Source excerpts are not presented as complete answers to broad questions.

With a saved prediction open, both “How big is this pancreas?” and “How big is it?”
calculate the loaded outline volume locally. A consecutive lesion measurement
retains its referent. A new literature subject updates the referent; ambiguity
requires naming the structure. Existing affine, units, geometry and boundary
checks remain. Study/prediction changes reset it. These are saved-outline volumes,
not verified whole-organ measurements or clinical normal-range classifications.

Preparation checks the context policy and prompt identity. It refreshes a stale
service only after matching its recorded command, process ID and start identity.
Unknown services are preserved. The original configured database/container was
started; no database was replaced and no configuration or secrets were copied.

## Actual final rehearsal

These are exposed development questions, not an independent evaluation.

| Question | Observed result |
| --- | --- |
| What does the pancreas do? | A short cited statement of enzyme and hormone secretion after one grounded correction. The coverage reviewer remains overly conservative. |
| What does it do? | Resolves the application subject and gives a concise supported role explanation. |
| Does it produce insulin? | Uses the direct beta-cell passage and answers the current follow-up. |
| Where is it located? | Gives the cited anatomical location rather than repeating function. |
| What happens if it loses function? | Limited, labelled source wording; the library does not support a complete general answer. |
| What are clear signs of disease? | Limited autoimmune-pancreatitis source example with article context, not a universal disease-sign checklist. |
| How big is this pancreas? / How big is it? | Both returned 60.33 mL for the displayed saved outline in PanTS 00009005, matching the workbench. Coverage remains unverified. |
| Unattached size / different organ / individual diagnosis | Clarification or refusal; no invented scan measurement or diagnosis. |

The final API rehearsal's generated responses took approximately 5.4–12.0 seconds
for basic function, insulin and location; this is one warm, exposed rehearsal,
not a latency benchmark. Broad questions can remain partial. The source collection
has fourteen papers and strong imaging/aging emphasis; general educational coverage
needs expansion before presenting this as a broad pancreatic knowledge assistant.

## Verification and retained evidence

- 388 targeted Python checks passed against the original source collection.
- 492 UI checks passed; seven existing checks were skipped. A final focused rerun
  of 56 answer/context/measurement checks passed after the last prompt update.
- Production build passed. The existing large-viewer-bundle advisory remains.
- Four synthetic browser scenarios passed during the initial worktree verification.
  The original app was then checked through its real interface, including local
  size questions and the literature conversation/citation flow.
- All twelve final rehearsal requests returned HTTP 200 and the expected routes.
  HTTP success is not an answer-accuracy score. Manual source review records the
  remaining partial coverage and conservative coverage labels.

Local evidence is under `outputs/prowl/expert-demo-20261118/`:
`rehearsal-01` preserves the original live failures and source review;
`rehearsal-02` preserves the failed model-review approach (and predates the final
lexical normalization edit); `rehearsal-03` and `rehearsal-04` preserve guard/fallback
checks; `rehearsal-05/results.json` and `source-review.json` hold the final sequence.
`final-runtime.json` verifies the running prompt, context policy and changed-source
hashes. The frozen canonical corpus was not edited.

Integration compared every original target with the tested baseline. Two diverged
measurement files were merged in three directions, preserving the original app's
measurement implementation. Original before/after snapshots and the integration
manifest are retained at `/private/tmp/prowl-expert-original-5jp2xcef/`.
The separate untracked STU-Net audit work was preserved. The original implementation
was left uncommitted for the subsequent review below.

## Commit review on November 18

Reviewed the request context, retrieval, source support, service ownership and UI
changes before committing them to main. All 186 targeted Python checks passed,
including the source-only HTTP test with local listener access. The full UI suite
passed 492 checks with seven existing skips. All four synthetic browser scenarios
passed, and the production build passed with the existing large-viewer-bundle
advisory. The CPU-only demo checklist matched all twelve routing expectations.
These checks verify the implementation and fixtures. The live response timings
and source-quality observations above remain those of the original rehearsal.

## Demo preparation

Open Research in the original app and select **Prepare AI expert** before the
presentation. Confirm “The local model is loaded and ready for questions.” Start
with function, insulin and location; open a citation. In Workbench, open a saved
prediction before asking size questions. Keep broad disease/function-loss questions
framed as source-limited research examples. A universal explanation of pancreatic
failure and comprehensive disease signs still need broader reviewed references.
