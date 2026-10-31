# Single-call cited answer candidate

## Status

October31: live-tested, still unpromoted pending the revision below. Original
October28 preparation: not promoted or evaluated with a live model. User chose to
keep the teacher running on October 28; no GPU/model calls or teacher pause were
performed. This replaces the proposed selection-speed experiment as the next
candidate to evaluate, without erasing its measurements or earlier failures.

The candidate supplies the user's question, passage titles, ranks and full text
in one nonthinking Qwen3:8b call. It requests up to three concise paragraphs with
exact supporting quotations, preserving units, populations, uncertainty and
exceptions. It can answer partially or report insufficient evidence. Existing
retrieval, scan boundaries and clarification decisions remain upstream. No
per-question canned answers are introduced.

The response contract distinguishes model-written prose from copied quotations.
Server and browser check schema, pinned model/prompt, coverage consistency, valid
citation ranks and verbatim supporting excerpts. These checks **do not establish
semantic support or completeness**. They must not be labeled an evidence audit.
A failed generation leaves the original passages available; no automatic repair
or second model call occurs. One request at a time, 60-second generation deadline,
5 passages / 16,000 characters, 1,536 generated tokens, 8,192 context tokens.
Oversized evidence fails closed rather than silently truncating qualifications.

## Interface

The shared Research/Workbench literature panel displays plain answer paragraphs
and citation buttons, with Sources and Read passages separately accessible.
Candidate label: “AI summary · Preview · Check the linked sources for details.”
The old answer route remains the active backend. No production service was
restarted or switched; the prepared UI accepts both response contracts.

Checks: nine synthetic backend tests; 79 UI tests covering the candidate, old
extract answers, literature requests/cancellation and scan answers. Headless
browser check rendered an explicitly synthetic answer on Research and opened its
source excerpt. Screenshots are under outputs/prowl/single-summary-20261028/.
This is interface evidence, not a generated-answer quality result.

## Next test window

After an authorized teacher pause, verified cleanup and GPU release:

1. Run `PYTHONPATH=. .venv-retrieval/bin/python scripts/retrieval/check_single_summary_candidate.py --output NEW_DIRECTORY`.
   It uses five existing public development packets (function, paraphrase,
   methods, focal fat, evidence gap), preserves outputs/failures and uses the
   exclusive GPU lock and AC check. Five calls, each bounded to 60 seconds.
2. Manually inspect relevance, factual support, completeness, qualifications,
   citation accuracy and refusal behavior separately. Compare latency with the
   same saved evidence and existing baseline; no independent-accuracy claim.
3. Resolve the literature database mount or qualify the prepared internal copy.
   Run `PYTHONPATH=. .venv-retrieval/bin/python scripts/serve_single_summary_candidate.py --config CONFIG_PATH`
   for API testing on loopback 8021. It holds the exclusive GPU lock while running.
4. For an authorized UI test, stop the verified old literature service and start
   the candidate with `--port 8016` so the existing UI proxy uses it. Do not launch
   two services on that port. Test both Research and Workbench, citations, partial
   answers, cancellation and a new question. Keep the existing startup command
   available for rollback; do not change readiness defaults before promotion.
5. Stop the candidate, verify model unloading/GPU cleanup, then resume the teacher
   under its existing rules. Promote only after quality and latency review.

If the single call changes qualifications or produces unsupported synthesis,
retain that failure. Do not treat a valid citation ID or exact quote as a pass for
its associated paraphrase, and do not add unbounded retries to conceal it.

## Additional CPU interface checks, October 28

Research and Workbench variants now have explicit synthetic tests for partial
answers, evidence gaps and failed summaries. Limitations remain visible, an old
answer does not survive a replacement gap response, and retrieved passages remain
accessible after failure. Loading copy says “an answer” rather than promising a
“checked answer” before review. Candidate, cancellation/stale-response and scan
answer suites: 75 passed in 2.67 seconds. These are interface checks, not model
quality or latency results; the candidate remains unpromoted while the teacher runs.

The internal literature service is now qualified separately; see
INTERNAL-LITERATURE-SERVICE-2026-10-28.md. This resolves step 3's storage dependency,
but does not authorize a competing GPU call.

## Candidate GPU ownership and UI admission

CPU review found that the candidate's lifetime exclusive GPU lock would be
misidentified by the UI proxy as teacher activity, blocking all candidate answers.
The candidate now advertises its answer reservation in health only inside the
exclusive-lock lifetime. Its server closes before that reservation is cleared and
the lock is released. Ordinary services advertise no reservation.

The UI admission helper allows a busy lock only when the loopback8016 backend is
healthy, matches the active storage identity, has the single-pass candidate policy
and explicitly reports its answer reservation. Any missing/mismatched/failed
health response blocks answers. The raw GPU-lock check remains unchanged for
preparation, so Prepare cannot load another model during that reservation.
On test port8021 the candidate can be called directly; UI admission applies only
after the separately authorized8016 test-window switch.

69 CPU tests pass across candidate ownership, summary generation contracts,
development search and readiness. Synthetic checks cover real file-lock exclusion,
teacher-owned startup rejection and cleanup after a server exception. Live helper
still reports gpu_busy=true for the running teacher. No candidate was launched,
no real model answer was generated, and no quality/promotion claim follows.

## October31 composition revision

User supplied the exact failing question: “Why can pancreas boundaries be hard to
outline on CT?” Live retrieval returned relevant anatomy, manual outlining and
model-limitations passages. The old extracted response also included unrelated
diagnosis claims. This is primarily a relevance/composition defect, not broken UI
paragraph rendering. The five existing exposed packets plus this question are the
fixed six-case revision set; they are not independent evaluation.

f4c9dca replaces model-copied quotations with request-local sentence IDs. Code
resolves selected sentences to exact contiguous source spans, retaining intervening
qualifications and the existing browser citation contract. Full passage content is
retained; unknown IDs, duplicate IDs and over-budget citations fail closed. Citation
binding still does not prove semantic support. Prior prompt/config/source and raw
failures remain under outputs/prowl/summary-revision-20261031-01 and the live runs.

The v2 prompt/8B model (4833c674…a97029) returned faster, well-bound citations, but
manual review rejected overgeneralized MRI methods, unrelated AIP MRI content in
the CT-fat answer, an unsupported citation for a density claim, and a false partial
answer to the absent stiffness range. Evidence: paired-summary-live-20261031-02.
864d3a7 narrows v3 to one focused paragraph and explicit study/coverage scope.
The six-call v3/8B pilot still failed all six response contracts: five emitted
"none" as a nonempty limitation on supported answers; the gap answer emitted a
claim despite none coverage. Its raw answers also omitted relevant details and
retained the unrelated diagnosis claim. Evidence: summary-focused-live-20261031-01.
Neither failure was hidden or promoted; no automatic output repair was applied.

29 focused Python and73 UI tests passed. An initial npm test invocation had no
configured script; the existing test:run command passed without dependency changes.
The user's conditional next step is one official Qwen3 4B Instruct comparison with
the same v3 prompt and evidence, before considering any app switch. Training remains
paused, its verified checkpoint and continuation qualification unchanged.

## October 31 bounded model comparison: not qualified

The closed coverage grammar removed the invalid supported/limitation combinations.
It did not establish factual support or completeness. The v4 non-thinking 8B and
4B comparisons still generalized a single MRI study; 4B also introduced an
unsupported tumor comparison. The v5/v6 bounded-thinking 8B candidates improved
the boundary explanation but retained study-scope errors and inconsistent function
completeness. All raw outputs remain in outputs/prowl/summary-*-20261031-*.

The final v6 prompt has SHA256
c18f71db4abb2b08b5915beb00fccf947420e6d42f9cc5d2f03f3ee0f0044864.
Fourteen focused generation/review-runner tests pass after this prompt revision;
earlier broader checks passed 29 Python and 73 UI tests. These are engineering
checks, not evidence of answer accuracy.

The installed qwen3:30b model was tested with the same six exposed packets and
v6 prompt, using an experimental runtime override only. Initial cold requests
timed out; a separate preload mistakenly used Ollama's default context and was
stopped before evaluation. Both attempts were retained. The corrected preload
explicitly used 8,192 context tokens and completed in 159.49 seconds within its
separate 240-second startup budget. Each answer retained the 60-second deadline
and 1,536-token generation cap. Six preloaded answers took 5.97–10.52 seconds;
these are generation timings, not cold or end-to-end UI latency.

Evidence: outputs/prowl/summary-30b-preloaded-20261031-02, including raw calls,
preload.json, manual-review.json and verified model-cleanup.json. The model was
unloaded and the bounded process exited. The exact boundary question produced a
direct explanation, but the set is NOT qualified: MRI study scope was lost,
PDAC-specific evidence was broadened to tumors, and the function wording blurred
digestive and endocrine roles. No candidate was promoted; the live backend and
scientific-training pause remain unchanged. Downloaded 4B is retained but inactive.

Next useful change is to test explicit claim-to-source scope preservation before
another model comparison. Keep the same failed cases and manual acceptance checks;
do not treat exact citation binding, valid JSON, or a faster answer as semantic
verification. No further download or repeated prompt sweep is justified by these
results alone.

## Readable bounded comparison packet

The existing comparison runner now snapshots all five question/evidence packets
and source-file SHA256 values into inputs.json before generation. It validates
every packet before creating output or calling the model, refuses an existing
output directory, and updates review.md after each result. The readable review
contains answer prose, supporting quotations, full retrieved passages, limitations,
timing and preserved failures. Every manual decision stays Pending; no automatic
acceptance or independent-evaluation claim is made. Timing is saved-evidence
generation time, not end-to-end retrieval/UI latency.

CPU-only preparation command:
`PYTHONPATH=. .venv-retrieval/bin/python scripts/retrieval/check_single_summary_candidate.py --prepare-only --output NEW_DIRECTORY`

Prepared actual exposed inputs at
outputs/prowl/single-summary-review-preparation-20261028/review.md. All five fit
the unchanged evidence budget. Twelve runner/generation tests pass, including
invalid-last-input rejection, no model use during preparation, output preservation
and synthetic failed-answer review. The later live run must use a fresh directory
under the existing exclusive-GPU/AC guard. Teacher10 reached729/1333 during this
CPU work; all341 producing repository pins remain intact.
