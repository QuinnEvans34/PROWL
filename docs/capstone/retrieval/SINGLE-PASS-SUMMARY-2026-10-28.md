# Single-call cited answer candidate

## Status

Prepared, not promoted or evaluated with a live model. User explicitly chose to
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
