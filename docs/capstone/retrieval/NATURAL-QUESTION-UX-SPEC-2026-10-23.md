# Natural questions and answer UX

Approved work direction: Quinton requested this spec and autonomous implementation, followed by his
hands-on feedback. Build on the existing assistant; no new application, corpus, model or training.

## Deliverable and sequence

1. Simplify the current panel: clear general-literature versus saved-case context, one primary Ask
   action, secondary source search, concise answer-first presentation with exact citation links.
   Move implementation details into expandable details. Keep material evidence/measurement limits
   visible. Show elapsed time and Cancel; do not invent progress stages without backend events.
2. Add a bounded local question-interpretation preview using the installed8B model and existing
   reformulation machinery. It proposes technical search wording, or asks one clarification. It
   cannot answer, inspect images, invent measurements or bypass the original scope checks.
   Initial release is explicitly user-reviewed: the user can use, edit or discard proposed wording.
   Never silently replace the user's question. Keep the original visible after applying a suggestion.
   This is a conservative refinement of automatic interpretation proposed in discussion: earlier
   semantic-routing/composition failures do not justify trusting rewrites without review yet.
3. Verify a fixed public set of ordinary wording, ambiguity, negation, scan requests and injection
   boundaries. Review meaning and downstream evidence separately. Keep the existing answer policy;
   interpretation does not qualify unsupported composition. Exercise browser flow and cancellation,
   stale requests, Sources, local measurement limitations and service failure.

## Acceptance and stopping conditions

- Existing supported questions and measurement protections stay intact; no fabricated scan access.
- Query suggestions preserve anatomy, modality, negation, numbers, comparison and uncertainty.
  Unsupported/ambiguous requests get a useful clarification or retain their original wording.
- The preview makes no retrieval/generation calls beyond one bounded interpretation call and never
  sends expected answers or evaluation labels. User acceptance triggers the existing answer path.
- A valid preview is not evidence. Every answer still follows the existing source/citation checks.
- Existing citation tabs remain keyboard accessible; final answer is prose, technical metadata folded.
- Interpretation unavailable/timeout leaves the typed question usable, with retry or ordinary Ask.
- Tests cover interrupted/stale interpretation and source/answer identity. Fixed live probes record
  failures and latency; no hidden retry or tuning to claim independent accuracy.
- If the model alters meaning in a material way, do not enable automatic rewrites. Deliver the reviewed
  preview only if it is useful with explicit editing; otherwise keep the feature off and report why.
- Finish with a small user walkthrough packet and honest limitations. Quinton's acceptance is pending.

No conversational memory in this block. Independent evaluation, broader faithful composition,
qualified scan measurements, reference comparisons and reviewed training feedback remain commitments.
Do not reopen larger-model startup experiments during this UX block. Use the approved50GB internal
literature reserve and preserve all previous experimental evidence.


User feedback amendment: general whole-pancreas size questions should answer directly using the
supported whole-organ volume study result, with its population and limitations. Do not require a
volume-versus-length clarification for that general wording. Explicit dimensions and scan requests
remain distinct; do not invent length evidence or call a selected study mean a universal average.
