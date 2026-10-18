# 05 — AI assistant and evidence interactions

> Handoff update: preserve the current written-answer AND source-only search capabilities added during planning. See 08 for integration details; the approved prototype does not establish scan understanding.


## One companion surface, explicit capability

Proposed right-panel tabs: Findings, Ask, Review summary. Research also has an expanded workspace
within the same shell. Returning restores the selected study/view rather than the demo landing.
Assistant presence is available throughout; never automatically initiate a question on each slice change.

| Content type | Source | Required presentation |
|---|---|---|
| Measurement | Validated structured artifact | Value, unit, method, prediction/reference identity |
| Literature answer | Existing retrieval/answer service | Cited claims, source passages, limitations |
| Reviewer note | Human input | Editable and clearly human-authored |
| Static example | Explicit development fixture | Persistent Example—not from this scan label |
| Future scan explanation | Future validated context adapter | Unavailable until context is actually connected |

Current free-text literature requests are available in code; live service response has not been
tested in this audit. They currently do not receive scans. Place a concise scope line above the
composer: Literature only · Scan context not connected. Do not imply the assistant sees pixels.

## Conversation and findings

- Provide a visible composer, suggested questions appropriate to current capabilities, and
  a conversation area. Audit backend conversation support before implying multi-turn memory.
- Current stateless service can display a sequence of independent questions, labeled as such.
  Do not silently prepend scan details or conversation history to the established endpoint.
- Findings cards use validated facts only. Missing dimensions are Unavailable, not zero.
- Width, length, volume, and equivalent spherical diameter are different measurements. Never
  relabel an existing approximate diameter as observed lesion width or pancreas length.
- Model scores are not disease probabilities. Keep raw confidence behind a properly described
  source detail unless its interpretation is established.
- No lesion predicted means that; it does not mean no lesion exists or the patient is healthy.
- Proposed concerns must identify their source/rule and uncertainty; no decorative generated warnings.
- Links from cards to viewer require actual structure/geometry mappings. Cite source passages in a
  drawer that does not navigate away from the CT. Keep provenance accessible without dumping hashes
  into the main conversation.

## Request states

Idle → submitted → pending → completed / insufficient evidence / unavailable / cancelled.
Only show Searching sources, Preparing answer, or Checking support when the API reports that stage.
Otherwise show Working on your question with elapsed time and cancellation; no fake percent or ETA.
Use a subtle animated status indicator, reduced-motion fallback, and accessible live status updates.
Failed generation can retain successfully retrieved sources when supported by the validated response.
Show retry without deleting the question. Do not expose internal chain-of-thought as a progress log.

## Context and race handling

Every case-specific result targets exact study, series, prediction, and request identity.
Changing study cancels/ignores incompatible pending results and removes prior study findings.
History may be retained separately but never displayed as current-study evidence.
General literature answers remain explicitly general; a nearby CT does not make them case-specific.
Assistant failure must not block image inspection or destroy an edited summary.

## Development examples

Allow a dedicated Example mode with synthetic study/facts, fixed source fixtures, and deterministic
response states. Keep its banner visible in cards, chat, and generated summary. Do not mix invented
measurements into a real study. Do not silently switch to canned success when a real request fails.
No fixture text should imply actual medical evidence unless it is backed by the fixture's cited source.
The UI redesign can implement these visual states before future scan-aware backend support arrives.
